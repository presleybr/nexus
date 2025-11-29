"""
Rotas de Automação Canopus
API REST para gerenciar automação de download de boletos
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from functools import wraps
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import os

# Configurar logger PRIMEIRO
logger = logging.getLogger(__name__)

# ESTRATÉGIA DE PATHS: Adicionar backend PRIMEIRO, depois root (para automation)
# Isso garante que models.database funcione, e também que automation.canopus seja importável
backend_path = Path(__file__).resolve().parent.parent
root_path = backend_path.parent  # Diretório raiz que contém 'automation' e 'backend'
automation_path = root_path / "automation" / "canopus"

# Backend primeiro (para Database funcionar)
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Root path (para poder importar automation.canopus.*)
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Canopus path direto (para imports legados do orquestrador)
if str(automation_path) not in sys.path:
    sys.path.append(str(automation_path))  # Append, não insert(0)

# Importar do backend
from models.database import Database

# Importar do Canopus (com tratamento de erro)
try:
    from orquestrador import CanopusOrquestrador, DatabaseManager
    CANOPUS_DISPONIVEL = True
    logger.info("✅ Automação Canopus carregada com sucesso")
except ImportError as e:
    logger.warning(f"⚠️ Automação Canopus não disponível: {e}")
    CANOPUS_DISPONIVEL = False
    CanopusOrquestrador = None
    DatabaseManager = None

# Blueprint
automation_canopus_bp = Blueprint('automation_canopus', __name__, url_prefix='/api/automation')


# ============================================================================
# CONTROLE DE STATUS DE EXECUÇÃO
# ============================================================================

# Status global da execução de downloads
execution_status = {
    'ativo': False,
    'ponto_venda': None,
    'total_clientes': 0,
    'clientes_processados': 0,
    'etapa_atual': 'Aguardando início...',
    'porcentagem': 0,
    'inicio': None,
    'ultimo_update': None,
    'erros': []
}

def atualizar_status(etapa: str = None, progresso: int = None, total: int = None, erro: str = None):
    """Atualiza o status da execução"""
    global execution_status

    if etapa:
        execution_status['etapa_atual'] = etapa

    if progresso is not None:
        execution_status['clientes_processados'] = progresso

    if total is not None:
        execution_status['total_clientes'] = total

    if erro:
        execution_status['erros'].append({
            'timestamp': datetime.now().isoformat(),
            'mensagem': erro
        })

    # Calcular porcentagem
    if execution_status['total_clientes'] > 0:
        execution_status['porcentagem'] = int(
            (execution_status['clientes_processados'] / execution_status['total_clientes']) * 100
        )

    execution_status['ultimo_update'] = datetime.now().isoformat()
    logger.info(f"📊 Status: {execution_status['etapa_atual']} ({execution_status['porcentagem']}%)")

def iniciar_execucao(ponto_venda: str, total_clientes: int):
    """Marca início da execução"""
    global execution_status
    execution_status.update({
        'ativo': True,
        'ponto_venda': ponto_venda,
        'total_clientes': total_clientes,
        'clientes_processados': 0,
        'etapa_atual': 'Iniciando automação...',
        'porcentagem': 0,
        'inicio': datetime.now().isoformat(),
        'ultimo_update': datetime.now().isoformat(),
        'erros': []
    })

def finalizar_execucao(sucesso: bool = True):
    """Marca fim da execução"""
    global execution_status
    execution_status['ativo'] = False
    execution_status['etapa_atual'] = 'Concluído!' if sucesso else 'Erro na execução'
    execution_status['porcentagem'] = 100 if sucesso else execution_status['porcentagem']
    execution_status['ultimo_update'] = datetime.now().isoformat()


# ============================================================================
# DECORADORES E HELPERS
# ============================================================================

def handle_errors(f):
    """Decorator para tratamento de erros"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Erro de validação: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Erro interno: {e}", exc_info=True)
            return jsonify({'error': 'Erro interno do servidor'}), 500
    return decorated_function


def get_db_connection():
    """Retorna conexão com banco de dados usando configuração centralizada"""
    import psycopg
    from psycopg.rows import dict_row
    from config import Config

    # Usar DATABASE_URL do Config (já configurado para Render ou local)
    return psycopg.connect(
        Config.DATABASE_URL,
        row_factory=dict_row
    )


# ============================================================================
# UPLOAD E PROCESSAMENTO DE PLANILHAS
# ============================================================================

@automation_canopus_bp.route('/upload-planilha', methods=['POST'])
@handle_errors
def upload_planilha():
    """
    Endpoint para upload de planilha Excel e importação de clientes
    Aceita arquivo .xlsx ou .xls e processa automaticamente
    """
    logger.info("📤 Recebendo upload de planilha...")

    # Verificar se arquivo foi enviado
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Nenhum arquivo enviado'
        }), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Nenhum arquivo selecionado'
        }), 400

    # Validar extensão
    allowed_extensions = {'.xlsx', '.xls', '.xlsm'}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        return jsonify({
            'success': False,
            'error': f'Tipo de arquivo inválido. Use: {", ".join(allowed_extensions)}'
        }), 400

    # Obter parâmetros
    pontos_venda_param = request.form.get('pontos_venda', '24627')

    # Determinar quais PVs processar
    if pontos_venda_param == 'ambos':
        filtro_pv = ['17308', '24627']
    elif pontos_venda_param == '17308':
        filtro_pv = ['17308']
    else:
        filtro_pv = ['24627']

    logger.info(f"📊 Arquivo: {file.filename}")
    logger.info(f"📍 Pontos de venda: {pontos_venda_param}")

    # Salvar arquivo temporariamente
    temp_file = None
    try:
        # Criar arquivo temporário
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)
        temp_file = temp_path

        # Salvar upload
        file.save(temp_path)
        logger.info(f"💾 Arquivo salvo temporariamente: {temp_path}")

        # Importar extrator
        from services.excel_extractor import extrair_clientes_planilha

        # ====================================================================
        # ETAPA 1: EXTRAIR DADOS DA PLANILHA
        # ====================================================================
        logger.info("🔍 Extraindo dados da planilha...")

        resultado_extracao = extrair_clientes_planilha(
            arquivo_excel=temp_path,
            pontos_venda=filtro_pv
        )

        if not resultado_extracao['sucesso']:
            return jsonify({
                'success': False,
                'error': f"Erro ao processar planilha: {resultado_extracao.get('erro', 'Erro desconhecido')}"
            }), 500

        clientes = resultado_extracao['clientes']
        logger.info(f"✅ {len(clientes)} clientes extraídos")
        logger.info(f"📊 Por PV: {resultado_extracao['estatisticas_pv']}")

        if len(clientes) == 0:
            return jsonify({
                'success': False,
                'error': 'Nenhum cliente válido encontrado na planilha para os PVs selecionados'
            }), 400

        # ====================================================================
        # ETAPA 2: IMPORTAR PARA O BANCO DE DADOS
        # ====================================================================
        logger.info(f"💾 Importando {len(clientes)} clientes para o banco...")

        importados = 0
        atualizados = 0
        erros = 0
        erros_detalhes = []

        with get_db_connection() as conn:
            cur = conn.cursor()

            for idx, cliente in enumerate(clientes, 1):
                try:
                    cpf = cliente['cpf']
                    nome = cliente['nome']
                    pv = cliente['ponto_venda']

                    # Verificar se cliente já existe
                    cur.execute("""
                        SELECT id FROM clientes_finais
                        WHERE cpf = %s AND ponto_venda = %s
                    """, (cpf, pv))

                    existing = cur.fetchone()

                    if existing:
                        # Atualizar
                        cur.execute("""
                            UPDATE clientes_finais
                            SET nome_completo = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (nome, existing['id']))
                        atualizados += 1
                    else:
                        # Buscar cliente_nexus
                        cur.execute("SELECT id FROM clientes_nexus ORDER BY id LIMIT 1")
                        cliente_nexus_row = cur.fetchone()
                        cliente_nexus_id = cliente_nexus_row['id'] if cliente_nexus_row else None

                        # Inserir novo
                        numero_contrato = f"CANOPUS-{pv}-{cpf}"
                        whatsapp = '5567999999999'  # Placeholder

                        cur.execute("""
                            INSERT INTO clientes_finais (
                                cliente_nexus_id,
                                nome_completo,
                                cpf,
                                telefone_celular,
                                whatsapp,
                                ponto_venda,
                                numero_contrato,
                                ativo,
                                created_at,
                                updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (cliente_nexus_id, nome, cpf, whatsapp, whatsapp, pv, numero_contrato))

                        importados += 1

                    # Commit a cada 100
                    if idx % 100 == 0:
                        conn.commit()
                        logger.info(f"   Checkpoint: {idx}/{len(clientes)} processados")

                except Exception as e:
                    erros += 1
                    erro_msg = f"Erro ao processar {nome} (CPF: {cpf}): {str(e)}"
                    erros_detalhes.append(erro_msg)
                    logger.error(erro_msg)
                    continue

            # Commit final
            conn.commit()
            cur.close()

        logger.info(f"✅ Importação concluída!")
        logger.info(f"   Novos: {importados}, Atualizados: {atualizados}, Erros: {erros}")

        return jsonify({
            'success': True,
            'message': f'Planilha processada com sucesso',
            'data': {
                'arquivo': file.filename,
                'total_extraidos': len(clientes),
                'importados': importados,
                'atualizados': atualizados,
                'erros': erros,
                'total_processados': importados + atualizados,
                'pontos_venda': filtro_pv,
                'estatisticas_pv': resultado_extracao['estatisticas_pv'],
                'erros_detalhes': erros_detalhes[:10]  # Primeiros 10 erros
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro ao processar upload: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erro ao processar arquivo: {str(e)}'
        }), 500

    finally:
        # Limpar arquivo temporário
        if temp_file and os.path.exists(temp_file):
            try:
                os.close(temp_fd)
                os.unlink(temp_file)
                logger.info(f"🗑️ Arquivo temporário removido")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")


# ============================================================================
# ROTAS DE CONSULTORES
# ============================================================================

@automation_canopus_bp.route('/consultores', methods=['GET'])
@handle_errors
def listar_consultores():
    """Lista todos os consultores"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.id,
                    c.nome,
                    c.email,
                    c.telefone,
                    c.whatsapp,
                    c.empresa,
                    c.ponto_venda,
                    c.pasta_boletos,
                    c.cor_identificacao,
                    c.ativo,
                    c.created_at,
                    c.updated_at,
                    COUNT(DISTINCT cf.id) as total_clientes,
                    COUNT(DISTINCT l.id) as total_downloads
                FROM consultores c
                LEFT JOIN clientes_finais cf ON cf.consultor_id = c.id
                LEFT JOIN log_downloads_boletos l ON l.consultor_id = c.id
                GROUP BY c.id
                ORDER BY c.nome
            """)

            consultores = cur.fetchall()

    return jsonify({
        'success': True,
        'data': consultores,
        'total': len(consultores)
    })


@automation_canopus_bp.route('/consultores', methods=['POST'])
@handle_errors
def criar_consultor():
    """Cria um novo consultor"""
    data = request.get_json()

    # Validações
    if not data.get('nome'):
        return jsonify({'error': 'Nome é obrigatório'}), 400

    if not data.get('empresa') or data['empresa'] not in ['credms', 'semicredito']:
        return jsonify({'error': 'Empresa inválida (credms ou semicredito)'}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO consultores (
                    nome,
                    email,
                    telefone,
                    whatsapp,
                    empresa,
                    ponto_venda,
                    pasta_boletos,
                    cor_identificacao,
                    ativo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, nome, empresa, ponto_venda
            """, (
                data['nome'],
                data.get('email'),
                data.get('telefone'),
                data.get('whatsapp'),
                data['empresa'],
                data.get('ponto_venda'),
                data.get('pasta_boletos', data['nome']),  # Usa nome como padrão
                data.get('cor_identificacao'),
                data.get('ativo', True)
            ))

            consultor = cur.fetchone()
            conn.commit()

    logger.info(f"✅ Consultor criado: {consultor['nome']}")

    return jsonify({
        'success': True,
        'message': 'Consultor criado com sucesso',
        'data': consultor
    }), 201


@automation_canopus_bp.route('/consultores/<int:id>', methods=['PUT'])
@handle_errors
def atualizar_consultor(id):
    """Atualiza um consultor"""
    data = request.get_json()

    updates = []
    params = []

    # Campos permitidos para atualização
    campos_permitidos = [
        'nome', 'email', 'telefone', 'whatsapp', 'empresa',
        'ponto_venda', 'pasta_boletos', 'cor_identificacao', 'ativo'
    ]

    for campo in campos_permitidos:
        if campo in data:
            updates.append(f"{campo} = %s")
            params.append(data[campo])

    if not updates:
        return jsonify({'error': 'Nenhum campo para atualizar'}), 400

    params.append(id)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE consultores
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, nome, empresa
            """, params)

            consultor = cur.fetchone()

            if not consultor:
                return jsonify({'error': 'Consultor não encontrado'}), 404

            conn.commit()

    logger.info(f"✅ Consultor atualizado: {consultor['nome']}")

    return jsonify({
        'success': True,
        'message': 'Consultor atualizado com sucesso',
        'data': consultor
    })


@automation_canopus_bp.route('/consultores/<int:id>', methods=['DELETE'])
@handle_errors
def desativar_consultor(id):
    """Desativa um consultor (soft delete)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE consultores
                SET ativo = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, nome
            """, (id,))

            consultor = cur.fetchone()

            if not consultor:
                return jsonify({'error': 'Consultor não encontrado'}), 404

            conn.commit()

    logger.info(f"✅ Consultor desativado: {consultor['nome']}")

    return jsonify({
        'success': True,
        'message': 'Consultor desativado com sucesso',
        'data': consultor
    })


# ============================================================================
# ROTAS DE IMPORTAÇÃO
# ============================================================================

@automation_canopus_bp.route('/importar-planilhas', methods=['POST'])
@handle_errors
def importar_planilhas():
    """Importa planilhas Excel para staging"""
    if not CANOPUS_DISPONIVEL:
        return jsonify({
            'success': False,
            'error': 'Automação Canopus não disponível. Execute: instalar_canopus.bat'
        }), 503

    data = request.get_json() or {}
    diretorio = data.get('diretorio')

    logger.info(f"📊 Iniciando importação de planilhas...")

    # Executar importação
    orquestrador = CanopusOrquestrador()

    dir_path = Path(diretorio) if diretorio else None
    stats = orquestrador.importar_planilhas(dir_path)

    return jsonify({
        'success': True,
        'message': 'Importação concluída',
        'data': {
            'total_planilhas': stats['total_planilhas'],
            'total_clientes': stats['total_clientes'],
            'clientes_salvos': stats['clientes_salvos'],
            'erros': stats['erros'],
            'planilhas_processadas': stats['planilhas_processadas'],
            'automacao_id': orquestrador.automacao_id
        }
    })


@automation_canopus_bp.route('/clientes-staging', methods=['GET'])
@handle_errors
def listar_clientes_staging():
    """Lista clientes no staging"""
    # Parâmetros de query
    status = request.args.get('status', 'pendente')
    consultor = request.args.get('consultor')
    limite = request.args.get('limite', type=int)

    query = """
        SELECT
            s.*,
            c.id as consultor_id,
            c.nome as consultor_nome_db
        FROM clientes_planilha_staging s
        LEFT JOIN consultores c ON c.nome = s.consultor_nome
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND s.status = %s"
        params.append(status)

    if consultor:
        query += " AND s.consultor_nome = %s"
        params.append(consultor)

    query += " ORDER BY s.importado_em DESC"

    if limite:
        query += " LIMIT %s"
        params.append(limite)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            clientes = cur.fetchall()

    return jsonify({
        'success': True,
        'data': clientes,
        'total': len(clientes),
        'filtros': {
            'status': status,
            'consultor': consultor,
            'limite': limite
        }
    })


@automation_canopus_bp.route('/sincronizar-clientes', methods=['POST'])
@handle_errors
def sincronizar_clientes():
    """Sincroniza clientes do staging para clientes_finais"""
    if not CANOPUS_DISPONIVEL:
        return jsonify({
            'success': False,
            'error': 'Automação Canopus não disponível. Execute: instalar_canopus.bat'
        }), 503

    logger.info("🔄 Iniciando sincronização de clientes...")

    orquestrador = CanopusOrquestrador()
    stats = orquestrador.sincronizar_clientes()

    return jsonify({
        'success': True,
        'message': 'Sincronização concluída',
        'data': {
            'total_pendentes': stats['total_pendentes'],
            'sincronizados': stats['sincronizados'],
            'erros': stats['erros']
        }
    })


# ============================================================================
# ROTAS DE DOWNLOAD
# ============================================================================

@automation_canopus_bp.route('/processar-downloads', methods=['POST'])
@handle_errors
def processar_downloads():
    """Processa downloads de boletos"""
    if not CANOPUS_DISPONIVEL:
        return jsonify({
            'success': False,
            'error': 'Automação Canopus não disponível. Execute: instalar_canopus.bat'
        }), 503

    data = request.get_json() or {}

    consultor = data.get('consultor')
    mes = data.get('mes', 'DEZEMBRO')
    ano = data.get('ano', datetime.now().year)
    limite = data.get('limite')

    if not consultor:
        return jsonify({'error': 'Consultor é obrigatório'}), 400

    logger.info(f"📥 Iniciando downloads - Consultor: {consultor}, Mês: {mes}/{ano}")

    # Executar downloads de forma assíncrona
    orquestrador = CanopusOrquestrador()

    # Como Flask não suporta async nativamente, rodar em thread separada
    # Ou retornar task ID para consulta posterior
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        stats = loop.run_until_complete(
            orquestrador.processar_downloads(
                consultor_nome=consultor,
                mes=mes,
                ano=ano,
                limite=limite
            )
        )
    finally:
        loop.close()

    return jsonify({
        'success': True,
        'message': 'Downloads processados',
        'data': {
            'automacao_id': orquestrador.automacao_id,
            'total_clientes': stats['total_clientes'],
            'sucessos': stats['sucessos'],
            'erros': stats['erros'],
            'cpf_nao_encontrado': stats['cpf_nao_encontrado'],
            'sem_boleto': stats['sem_boleto']
        }
    })


@automation_canopus_bp.route('/processar-downloads-ponto-venda', methods=['POST'])
@handle_errors
def processar_downloads_ponto_venda():
    """
    Processa downloads de boletos para TODOS os clientes de um ponto de venda

    Body JSON:
    {
        "ponto_venda": "17.308",
        "mes": "DEZEMBRO",  // opcional
        "ano": 2024,        // opcional
        "limite": 100       // opcional
    }
    """
    if not CANOPUS_DISPONIVEL:
        return jsonify({
            'success': False,
            'error': 'Automação Canopus não disponível. Execute: instalar_canopus.bat'
        }), 503

    data = request.get_json() or {}

    ponto_venda = data.get('ponto_venda')
    mes = data.get('mes')  # Opcional - será extraído da página
    ano = data.get('ano', datetime.now().year)
    limite = data.get('limite')

    if not ponto_venda:
        return jsonify({'error': 'Ponto de venda é obrigatório'}), 400

    logger.info(f"📥 Iniciando downloads em massa - PV: {ponto_venda}, Ano: {ano}")

    # Buscar todos os CPFs cadastrados para este ponto de venda
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT DISTINCT cf.cpf, cf.nome, c.nome as consultor_nome
                FROM clientes_finais cf
                JOIN consultores c ON c.id = cf.consultor_id
                JOIN pontos_venda pv ON pv.id = c.ponto_venda_id
                WHERE pv.codigo = %s
                  AND cf.ativo = TRUE
                  AND c.ativo = TRUE
            """
            params = [ponto_venda]

            if limite:
                query += " LIMIT %s"
                params.append(limite)

            cur.execute(query, params)
            clientes = cur.fetchall()

    if not clientes:
        return jsonify({
            'success': False,
            'error': f'Nenhum cliente encontrado para o ponto de venda {ponto_venda}'
        }), 404

    total_clientes = len(clientes)
    logger.info(f"📊 Encontrados {total_clientes} clientes para processar")

    # Executar downloads de forma assíncrona
    orquestrador = CanopusOrquestrador()

    # Rodar em thread separada
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Usar o primeiro consultor encontrado para login
        consultor_nome = clientes[0]['consultor_nome']

        stats = loop.run_until_complete(
            orquestrador.processar_downloads(
                consultor_nome=consultor_nome,
                mes=mes,
                ano=ano,
                limite=limite
            )
        )
    finally:
        loop.close()

    return jsonify({
        'success': True,
        'message': f'Downloads processados para {total_clientes} clientes',
        'data': {
            'automacao_id': orquestrador.automacao_id,
            'ponto_venda': ponto_venda,
            'total_clientes': stats['total_clientes'],
            'sucessos': stats['sucessos'],
            'erros': stats['erros'],
            'cpf_nao_encontrado': stats['cpf_nao_encontrado'],
            'sem_boleto': stats['sem_boleto']
        }
    })


@automation_canopus_bp.route('/importar-boletos-crm', methods=['POST'])
@handle_errors
def importar_boletos_crm():
    """Importa boletos baixados para tabela de boletos do CRM"""
    if not CANOPUS_DISPONIVEL:
        return jsonify({
            'success': False,
            'error': 'Automação Canopus não disponível. Execute: instalar_canopus.bat'
        }), 503

    logger.info("📄 Iniciando importação de boletos para CRM...")

    orquestrador = CanopusOrquestrador()
    stats = orquestrador.importar_boletos_para_crm()

    return jsonify({
        'success': True,
        'message': 'Boletos importados para CRM',
        'data': {
            'total_logs': stats['total_logs'],
            'importados': stats['importados'],
            'ja_existentes': stats['ja_existentes'],
            'erros': stats['erros']
        }
    })


# ============================================================================
# ROTAS DE EXECUÇÕES
# ============================================================================

@automation_canopus_bp.route('/execucoes', methods=['GET'])
@handle_errors
def listar_execucoes():
    """Lista execuções de automação"""
    # Parâmetros
    limite = request.args.get('limite', 50, type=int)
    status = request.args.get('status')
    tipo = request.args.get('tipo')
    consultor_id = request.args.get('consultor_id', type=int)

    query = """
        SELECT
            e.*,
            c.nome as consultor_nome
        FROM execucoes_automacao e
        LEFT JOIN consultores c ON c.id = e.consultor_id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND e.status = %s"
        params.append(status)

    if tipo:
        query += " AND e.tipo = %s"
        params.append(tipo)

    if consultor_id:
        query += " AND e.consultor_id = %s"
        params.append(consultor_id)

    query += " ORDER BY e.iniciado_em DESC LIMIT %s"
    params.append(limite)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            execucoes = cur.fetchall()

    return jsonify({
        'success': True,
        'data': execucoes,
        'total': len(execucoes),
        'filtros': {
            'status': status,
            'tipo': tipo,
            'consultor_id': consultor_id,
            'limite': limite
        }
    })


@automation_canopus_bp.route('/execucoes/<automacao_id>', methods=['GET'])
@handle_errors
def obter_execucao(automacao_id):
    """Obtém detalhes de uma execução específica"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Buscar execução
            cur.execute("""
                SELECT
                    e.*,
                    c.nome as consultor_nome
                FROM execucoes_automacao e
                LEFT JOIN consultores c ON c.id = e.consultor_id
                WHERE e.automacao_id = %s
            """, (automacao_id,))

            execucao = cur.fetchone()

            if not execucao:
                return jsonify({'error': 'Execução não encontrada'}), 404

            # Buscar logs relacionados
            cur.execute("""
                SELECT
                    status,
                    COUNT(*) as quantidade
                FROM log_downloads_boletos
                WHERE automacao_id = %s
                GROUP BY status
            """, (automacao_id,))

            logs_stats = cur.fetchall()

    return jsonify({
        'success': True,
        'data': {
            'execucao': execucao,
            'logs_stats': logs_stats
        }
    })


# ============================================================================
# ROTAS DE ESTATÍSTICAS
# ============================================================================

@automation_canopus_bp.route('/estatisticas', methods=['GET'])
@handle_errors
def obter_estatisticas():
    """Retorna estatísticas gerais da automação"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Estatísticas de consultores
            cur.execute("""
                SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE ativo = TRUE) as ativos
                FROM consultores
            """)
            stats_consultores = cur.fetchone()

            # Estatísticas de staging
            cur.execute("""
                SELECT
                    status,
                    COUNT(*) as quantidade
                FROM clientes_planilha_staging
                GROUP BY status
            """)
            stats_staging = cur.fetchall()

            # Estatísticas de downloads
            cur.execute("""
                SELECT
                    DATE(baixado_em) as data,
                    status,
                    COUNT(*) as quantidade
                FROM log_downloads_boletos
                WHERE baixado_em >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(baixado_em), status
                ORDER BY data DESC
            """)
            stats_downloads = cur.fetchall()

            # Últimas execuções
            cur.execute("""
                SELECT
                    e.automacao_id,
                    e.tipo,
                    e.status,
                    e.iniciado_em,
                    e.finalizado_em,
                    e.total_clientes,
                    e.processados_sucesso,
                    c.nome as consultor_nome
                FROM execucoes_automacao e
                LEFT JOIN consultores c ON c.id = e.consultor_id
                ORDER BY e.iniciado_em DESC
                LIMIT 10
            """)
            ultimas_execucoes = cur.fetchall()

    return jsonify({
        'success': True,
        'data': {
            'consultores': stats_consultores,
            'staging': stats_staging,
            'downloads_ultimos_30_dias': stats_downloads,
            'ultimas_execucoes': ultimas_execucoes
        }
    })


# ============================================================================
# ROTA DE HEALTH CHECK
# ============================================================================

@automation_canopus_bp.route('/health', methods=['GET'])
def health_check():
    """Verifica saúde do serviço de automação"""
    try:
        # Verificar conexão com banco
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

        # Verificar diretórios (se Canopus estiver disponível)
        diretorios_ok = False
        if CANOPUS_DISPONIVEL:
            try:
                from config import CanopusConfig
                diretorios_ok = all([
                    CanopusConfig.DOWNLOADS_DIR.exists(),
                    CanopusConfig.EXCEL_DIR.exists(),
                    CanopusConfig.LOGS_DIR.exists()
                ])
            except:
                diretorios_ok = False

        # Verificar pool de conexões
        from models.database import Database
        pool_info = {
            'available': 'N/A',
            'total_size': 'N/A'
        }
        try:
            if Database._connection_pool:
                # Tentar obter informações do pool
                pool_info['available'] = Database._connection_pool.pool.qsize() if hasattr(Database._connection_pool, 'pool') else 'N/A'
        except:
            pass

        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'database': True,
                'canopus_disponivel': CANOPUS_DISPONIVEL,
                'diretorios': diretorios_ok if CANOPUS_DISPONIVEL else 'N/A',
                'connection_pool': pool_info
            }
        })

    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@automation_canopus_bp.route('/reset-pool', methods=['POST'])
@handle_errors
def reset_connection_pool():
    """
    Reseta o pool de conexões do PostgreSQL
    Use quando o pool estiver esgotado ou com conexões presas
    """
    try:
        from models.database import Database

        logger.warning("⚠️ Resetando pool de conexões do PostgreSQL...")

        # Fechar todas as conexões atuais
        if Database._connection_pool:
            Database.close_all_connections()
            Database._connection_pool = None
            logger.info("🔒 Pool de conexões fechado")

        # Reinicializar pool com novos parâmetros
        Database.initialize_pool(minconn=5, maxconn=50)
        logger.info("✅ Pool de conexões reinicializado (min=5, max=50)")

        return jsonify({
            'success': True,
            'message': 'Pool de conexões resetado com sucesso',
            'pool_config': {
                'min_connections': 5,
                'max_connections': 50,
                'timeout': 10.0
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao resetar pool: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_canopus_bp.route('/status-execucao', methods=['GET'])
def status_execucao():
    """
    Retorna status atual da execução de downloads
    Usado para polling em tempo real no frontend
    """
    global execution_status
    return jsonify({
        'success': True,
        'status': execution_status.copy()
    })


@automation_canopus_bp.route('/verificar-arquivos', methods=['GET'])
def verificar_arquivos():
    """
    Verifica arquivos PDF salvos no servidor
    """
    import os

    # Caminho dos downloads
    base_dir = os.getenv('DOWNLOAD_BASE_DIR', str(Path(__file__).resolve().parent.parent.parent / 'automation' / 'canopus' / 'downloads'))
    pasta_destino = Path(base_dir) / 'Danner'

    resultado = {
        'base_dir': str(base_dir),
        'pasta_destino': str(pasta_destino),
        'pasta_existe': pasta_destino.exists(),
        'arquivos': [],
        'total_arquivos': 0,
        'tamanho_total_mb': 0
    }

    if pasta_destino.exists():
        arquivos = []
        tamanho_total = 0

        for arquivo in pasta_destino.glob('*.pdf'):
            stat = arquivo.stat()
            arquivos.append({
                'nome': arquivo.name,
                'tamanho_kb': round(stat.st_size / 1024, 2),
                'modificado': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
            tamanho_total += stat.st_size

        resultado['arquivos'] = sorted(arquivos, key=lambda x: x['modificado'], reverse=True)[:20]  # Últimos 20
        resultado['total_arquivos'] = len(list(pasta_destino.glob('*.pdf')))
        resultado['tamanho_total_mb'] = round(tamanho_total / (1024 * 1024), 2)

    return jsonify({
        'success': True,
        'data': resultado
    })


@automation_canopus_bp.route('/verificar-boletos-banco', methods=['GET'])
def verificar_boletos_banco():
    """
    Verifica downloads registrados na tabela downloads_canopus
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Total de downloads
                cur.execute("SELECT COUNT(*) as total FROM downloads_canopus")
                total = cur.fetchone()['total']

                # Últimos 10 downloads
                cur.execute("""
                    SELECT
                        d.id,
                        d.cpf,
                        d.nome_arquivo,
                        d.caminho_arquivo,
                        d.tamanho_bytes,
                        d.status,
                        d.data_download,
                        d.created_at,
                        cf.nome_completo as cliente_nome,
                        c.nome as consultor_nome
                    FROM downloads_canopus d
                    LEFT JOIN clientes_finais cf ON cf.cpf = d.cpf
                    LEFT JOIN consultores c ON c.id = d.consultor_id
                    ORDER BY d.created_at DESC
                    LIMIT 10
                """)
                ultimos_downloads = cur.fetchall()

                # Estatísticas por status
                cur.execute("""
                    SELECT
                        status,
                        COUNT(*) as total,
                        SUM(tamanho_bytes) as tamanho_total
                    FROM downloads_canopus
                    GROUP BY status
                    ORDER BY total DESC
                """)
                estatisticas = cur.fetchall()

                # Downloads por consultor
                cur.execute("""
                    SELECT
                        c.nome as consultor_nome,
                        COUNT(d.id) as total_downloads
                    FROM downloads_canopus d
                    LEFT JOIN consultores c ON c.id = d.consultor_id
                    GROUP BY c.nome
                    ORDER BY total_downloads DESC
                """)
                por_consultor = cur.fetchall()

                return jsonify({
                    'success': True,
                    'data': {
                        'total_downloads': total,
                        'ultimos_downloads': ultimos_downloads,
                        'estatisticas_por_status': estatisticas,
                        'downloads_por_consultor': por_consultor
                    }
                })

    except Exception as e:
        logger.error(f"Erro ao verificar downloads: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ROTAS PARA O FRONTEND DO CLIENTE
# ============================================================================

@automation_canopus_bp.route('/baixar-boletos-ponto-venda', methods=['POST'])
@handle_errors
def baixar_boletos_ponto_venda():
    """
    Inicia download de boletos para todos os CPFs de um ponto de venda
    Retorna execução_id para acompanhamento via polling
    """
    logger.info("=" * 80)
    logger.info("📥 REQUISIÇÃO RECEBIDA: /baixar-boletos-ponto-venda")
    logger.info("=" * 80)

    if not CANOPUS_DISPONIVEL:
        logger.error("❌ Automação Canopus não disponível")
        return jsonify({
            'success': False,
            'error': 'Automação Canopus não disponível. Execute: instalar_canopus.bat'
        }), 503

    # Verificar se já há execução ativa
    global execution_status
    if execution_status['ativo']:
        logger.warning("⚠️ Já existe uma execução em andamento")
        return jsonify({
            'success': False,
            'error': 'Já existe uma execução em andamento. Aguarde a conclusão.',
            'status_atual': execution_status.copy()
        }), 409  # 409 Conflict

    data = request.get_json() or {}
    ponto_venda = data.get('ponto_venda', '24627')
    mes = data.get('mes')
    ano = data.get('ano')

    logger.info(f"🚀 Iniciando download de boletos - PV: {ponto_venda}, Mês: {mes}, Ano: {ano}")
    logger.info(f"📋 Dados recebidos: {data}")

    # Criar orquestrador
    logger.info("🔧 Criando orquestrador...")
    orquestrador = CanopusOrquestrador()

    # Buscar todos os CPFs dos clientes do ponto de venda no banco
    logger.info(f"🔍 Buscando clientes do PV {ponto_venda}...")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT c.cpf, c.nome_completo as nome
                    FROM clientes_finais c
                    WHERE c.ponto_venda = %s AND c.ativo = TRUE
                    ORDER BY c.nome_completo
                """, (ponto_venda,))

                clientes = cur.fetchall()
                logger.info(f"✅ Query executada. Resultados: {len(clientes)}")

    except Exception as e:
        logger.error(f"❌ Erro ao buscar clientes: {e}")
        logger.exception("Traceback completo:")
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar clientes: {str(e)}'
        }), 500

    if not clientes:
        logger.warning(f"⚠️ Nenhum cliente encontrado no PV {ponto_venda}")
        return jsonify({
            'success': False,
            'error': f'Nenhum cliente encontrado no ponto de venda {ponto_venda}'
        }), 404

    logger.info(f"📋 Encontrados {len(clientes)} clientes para processar")
    logger.info(f"📄 Primeiros 5 CPFs: {[c['cpf'] for c in clientes[:5]]}")

    # Executar downloads para cada cliente em BACKGROUND
    try:
        import asyncio
        import threading

        # Criar lista de CPFs
        cpfs_todos = [c['cpf'] for c in clientes]

        logger.info(f"📋 Total de clientes no PV: {len(cpfs_todos)}")
        sys.stdout.flush()

        # ========================================================================
        # ENCONTRAR ÚLTIMO BOLETO BAIXADO E CONTINUAR SEQUENCIALMENTE
        # ========================================================================
        indice_inicio = 0
        ultimo_cpf_baixado = None
        total_ja_baixados = 0

        try:
            with get_db_connection() as conn_check:
                with conn_check.cursor() as cur_check:
                    # Buscar o ÚLTIMO CPF baixado (mais recente) para este mês/ano
                    # que também está na lista de CPFs do PV
                    cur_check.execute("""
                        SELECT cpf, data_download, nome_arquivo
                        FROM downloads_canopus
                        WHERE status = 'sucesso'
                        AND EXTRACT(MONTH FROM data_download) = %s
                        AND EXTRACT(YEAR FROM data_download) = %s
                        AND cpf = ANY(%s)
                        ORDER BY data_download DESC
                        LIMIT 1
                    """, (mes, ano if ano else 2025, cpfs_todos))

                    ultimo_download = cur_check.fetchone()

                    if ultimo_download:
                        ultimo_cpf_baixado = ultimo_download['cpf']
                        data_ultimo = ultimo_download['data_download']
                        nome_arquivo = ultimo_download['nome_arquivo']

                        # Encontrar posição deste CPF na lista ordenada
                        try:
                            indice_ultimo = cpfs_todos.index(ultimo_cpf_baixado)
                            indice_inicio = indice_ultimo + 1  # Começar do próximo
                            total_ja_baixados = indice_inicio

                            logger.info("=" * 80)
                            logger.info(f"📊 RETOMANDO DOWNLOAD A PARTIR DO ÚLTIMO BOLETO")
                            logger.info(f"   Total de clientes no PV: {len(cpfs_todos)}")
                            logger.info(f"   Último baixado: {ultimo_cpf_baixado}")
                            logger.info(f"   Arquivo: {nome_arquivo}")
                            logger.info(f"   Data: {data_ultimo}")
                            logger.info(f"   Posição: {indice_ultimo + 1}/{len(cpfs_todos)}")
                            logger.info(f"   Já processados: {total_ja_baixados}")
                            logger.info(f"   Faltam processar: {len(cpfs_todos) - indice_inicio}")
                            logger.info("=" * 80)
                            sys.stdout.flush()

                        except ValueError:
                            # CPF não encontrado na lista (caso raro)
                            logger.warning(f"⚠️ Último CPF baixado ({ultimo_cpf_baixado}) não está na lista atual")
                            logger.info("   Iniciando do começo...")
                            sys.stdout.flush()
                            indice_inicio = 0
                    else:
                        logger.info("=" * 80)
                        logger.info(f"📊 INICIANDO DOWNLOAD PELA PRIMEIRA VEZ")
                        logger.info(f"   Total de clientes no PV: {len(cpfs_todos)}")
                        logger.info(f"   Nenhum download anterior encontrado")
                        logger.info("=" * 80)
                        sys.stdout.flush()

        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar último download: {e}")
            logger.exception("Traceback:")
            logger.info("   Continuando do início...")
            sys.stdout.flush()
            indice_inicio = 0

        # Pegar apenas os CPFs a partir do índice de início (continuar sequencialmente)
        cpfs = cpfs_todos[indice_inicio:]

        logger.info("=" * 80)
        logger.info(f"🎯 INICIANDO DOWNLOADS SEQUENCIAIS")
        logger.info(f"   Índice de início: {indice_inicio + 1}/{len(cpfs_todos)}")
        logger.info(f"   CPFs a processar: {len(cpfs)}")
        if len(cpfs) > 0:
            logger.info(f"   Primeiro CPF: {cpfs[0]} (posição {indice_inicio + 1})")
            logger.info(f"   Último CPF: {cpfs[-1]} (posição {len(cpfs_todos)})")
        logger.info("=" * 80)
        sys.stdout.flush()

        # Se não há CPFs para processar, retornar sucesso
        if len(cpfs) == 0:
            logger.info("✅ TODOS OS BOLETOS JÁ FORAM BAIXADOS!")
            logger.info(f"   Total de {len(cpfs_todos)} boletos já registrados no banco.")
            sys.stdout.flush()
            return jsonify({
                'success': True,
                'message': 'Todos os boletos já foram baixados',
                'total_clientes': len(cpfs_todos),
                'ja_baixados': len(cpfs_todos),
                'faltam': 0
            })

        # Estatísticas compartilhadas
        stats = {
            'sucessos': 0,
            'erros': 0,
            'cpf_nao_encontrado': 0,
            'sem_boleto': 0,
            'total': len(cpfs),
            'processados': 0,
            'ja_baixados': total_ja_baixados,  # Quantos já foram processados anteriormente
            'indice_inicio': indice_inicio  # Posição de onde começou
        }

        # Função para processar em background
        def processar_downloads_background():
            logger.info("=" * 80)
            logger.info("🚀 THREAD DE DOWNLOAD INICIADA")
            logger.info(f"📊 Total de CPFs a processar: {len(cpfs)}")
            logger.info("=" * 80)

            async def processar_todos():
                logger.info("🔄 Função processar_todos() iniciada")

                # Iniciar rastreamento de execução
                iniciar_execucao(ponto_venda, len(cpfs))
                atualizar_status(etapa='Configurando ambiente...', progresso=0)

                # IMPORTANTE: Configurar sys.path dentro da thread
                import sys
                from pathlib import Path
                import os

                # Adicionar paths necessários
                backend_path = Path(__file__).resolve().parent.parent
                root_path = backend_path.parent  # Diretório raiz que contém 'automation' e 'backend'

                if str(backend_path) not in sys.path:
                    sys.path.insert(0, str(backend_path))
                    logger.info(f"📂 Path adicionado ao sys.path: {backend_path}")

                if str(root_path) not in sys.path:
                    sys.path.insert(0, str(root_path))
                    logger.info(f"📂 Path adicionado ao sys.path: {root_path}")

                # Agora sim importar
                from automation.canopus.canopus_automation import CanopusAutomation

                atualizar_status(etapa='Configurando diretórios...')

                # Usar path relativo ou variável de ambiente para Render
                base_dir = os.getenv('DOWNLOAD_BASE_DIR', str(Path(__file__).resolve().parent.parent.parent / 'automation' / 'canopus' / 'downloads'))
                pasta_destino = Path(base_dir) / 'Danner'
                pasta_destino.mkdir(parents=True, exist_ok=True)

                logger.info(f"📁 Pasta de destino dos boletos: {pasta_destino}")

                # Buscar credenciais do banco usando conexão centralizada
                try:
                    atualizar_status(etapa='Buscando credenciais no banco...')
                    logger.info(f"🔑 Buscando credenciais do PV {ponto_venda}...")

                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT usuario, senha, codigo_empresa, ponto_venda
                                FROM credenciais_canopus
                                WHERE ponto_venda = %s AND ativo = TRUE
                                LIMIT 1
                            """, (ponto_venda,))

                            credencial_row = cur.fetchone()

                            if not credencial_row:
                                logger.error(f"❌ Credenciais não encontradas para PV {ponto_venda}")
                                logger.error("Configure as credenciais na tabela credenciais_canopus")
                                return

                            usuario = credencial_row['usuario']
                            senha = credencial_row['senha']
                            codigo_empresa = credencial_row.get('codigo_empresa', '0101')

                            # IMPORTANTE: No Canopus, o login precisa do código do PV com zeros à esquerda
                            # Exemplo: 24627 -> 0000024627 (total de 10 dígitos)
                            usuario_login = ponto_venda.zfill(10)  # Preenche com zeros à esquerda até 10 dígitos

                            logger.info(f"✅ Credenciais obtidas")
                            logger.info(f"   Usuário (original): {usuario}")
                            logger.info(f"   Usuário (login): {usuario_login} (PV com zeros)")
                            logger.info(f"   Código Empresa: {codigo_empresa}")
                            logger.info(f"🔐 Senha: {'*' * len(senha)}")

                except Exception as e:
                    logger.error(f"❌ Erro ao buscar credenciais: {e}")
                    logger.exception("Traceback completo:")
                    return

                # Abrir navegador UMA VEZ
                # Detectar se está no Render (sem interface gráfica)
                # Render define RENDER=true ou verifica se DATABASE_URL começa com postgresql://
                is_render = (
                    os.getenv('RENDER') is not None or
                    os.getenv('IS_RENDER') == 'true' or
                    'render.com' in os.getenv('DATABASE_URL', '')
                )
                headless_mode = is_render  # True no Render, False localmente

                logger.info(f"🌐 Ambiente: {'Render (servidor)' if is_render else 'Local'}")
                logger.info(f"🌐 Abrindo Chromium (headless={headless_mode})...")
                sys.stdout.flush()

                atualizar_status(etapa='Abrindo navegador Chromium...')

                async with CanopusAutomation(headless=headless_mode) as bot:
                    logger.info("✅ Chromium aberto!")
                    sys.stdout.flush()

                    # Fazer login
                    atualizar_status(etapa=f'Fazendo login no sistema (PV: {usuario_login})...')

                    logger.info("=" * 80)
                    logger.info("🔐 FAZENDO LOGIN NO PONTO 24627")
                    logger.info(f"👤 Usuário (login): {usuario_login}")
                    logger.info(f"🏢 Código Empresa: {codigo_empresa}")
                    logger.info(f"🔐 Senha: {'*' * len(senha)}")
                    logger.info("=" * 80)
                    sys.stdout.flush()

                    try:
                        login_ok = await bot.login(
                            usuario=usuario_login,  # Usar PV com zeros à esquerda
                            senha=senha,
                            codigo_empresa=codigo_empresa,
                            ponto_venda=ponto_venda
                        )
                    except Exception as e_login:
                        logger.error(f"❌ EXCEPTION durante login: {e_login}")
                        logger.exception("Traceback completo:")
                        sys.stdout.flush()
                        atualizar_status(etapa=f'Erro no login: {str(e_login)}', erro=str(e_login))
                        finalizar_execucao(sucesso=False)
                        return

                    if not login_ok:
                        logger.error("=" * 80)
                        logger.error("❌ FALHA NO LOGIN")
                        logger.error("Possíveis causas:")
                        logger.error("  1. Senha incorreta")
                        logger.error("  2. Usuário bloqueado")
                        logger.error("  3. Sistema Canopus indisponível")
                        logger.error("  4. Seletores CSS mudaram")
                        logger.error("=" * 80)
                        sys.stdout.flush()
                        atualizar_status(etapa='Falha no login - verifique credenciais', erro='Login falhou')
                        finalizar_execucao(sucesso=False)
                        return

                    logger.info("=" * 80)
                    logger.info("✅ LOGIN REALIZADO COM SUCESSO!")
                    logger.info("=" * 80)
                    sys.stdout.flush()

                    atualizar_status(etapa='Login realizado! Iniciando processamento de clientes...')

                    # Monitorar uso de memória
                    import psutil
                    import gc
                    process = psutil.Process()

                    # Processar cada CPF na mesma sessão
                    for idx, cpf in enumerate(cpfs, 1):
                        # Monitorar memória a cada 5 clientes
                        if idx % 5 == 0:
                            mem_info = process.memory_info()
                            mem_mb = mem_info.rss / 1024 / 1024
                            logger.info("=" * 80)
                            logger.info(f"📊 MONITORAMENTO DE RECURSOS (Cliente {idx}/{len(cpfs)})")
                            logger.info(f"   Memória RAM: {mem_mb:.1f} MB")
                            sys.stdout.flush()
                            if mem_mb > 400:  # Alerta se > 400MB (próximo do limite de 512MB)
                                logger.warning(f"⚠️ MEMÓRIA ALTA! {mem_mb:.1f} MB / 512 MB limite")
                                logger.info("   Executando garbage collection...")
                                sys.stdout.flush()
                                gc.collect()  # Forçar limpeza de memória Python
                                mem_after = process.memory_info().rss / 1024 / 1024
                                logger.info(f"   Memória após GC: {mem_after:.1f} MB")
                                sys.stdout.flush()
                            logger.info("=" * 80)
                            sys.stdout.flush()

                        logger.info(f"📄 Processando {idx}/{len(cpfs)}: CPF {cpf}")
                        sys.stdout.flush()

                        # Atualizar status com cliente atual
                        atualizar_status(
                            etapa=f'Processando cliente {idx}/{len(cpfs)} - CPF: {cpf}',
                            progresso=idx - 1
                        )

                        try:
                            from automation.canopus.canopus_config import CanopusConfig

                            # BUSCAR NOME DO CLIENTE NO BANCO DE DADOS (não mais na planilha local)
                            nome_cliente = None
                            try:
                                # Buscar cliente correspondente ao CPF no banco
                                cliente_info = next((c for c in clientes if c['cpf'] == cpf), None)
                                if cliente_info and cliente_info.get('nome'):
                                    nome_cliente = str(cliente_info['nome']).strip().upper().replace(' ', '_')
                                    logger.info(f"✅ Nome do cliente encontrado no banco: {nome_cliente}")
                                    sys.stdout.flush()
                            except Exception as e:
                                logger.warning(f"⚠️ Erro ao buscar nome do cliente no banco: {e}")
                                sys.stdout.flush()

                            # NÃO passar nome_arquivo - deixar gerar automaticamente com nome do cliente
                            # Processar cliente
                            resultado = await bot.processar_cliente_completo(
                                cpf=cpf,
                                mes=mes,
                                ano=int(ano) if ano else 2025,
                                destino=pasta_destino,
                                nome_arquivo=None  # None = gera automaticamente com nome do cliente
                            )

                            # Verificar resultado e atualizar estatísticas
                            if resultado.get('status') == CanopusConfig.Status.SUCESSO:
                                stats['sucessos'] += 1
                                stats['processados'] += 1
                                logger.info("=" * 80)
                                logger.info(f"✅ SUCESSO! Boleto {idx}/{len(cpfs)} baixado: {cpf}")
                                logger.info(f"📁 Arquivo: {resultado.get('dados_boleto', {}).get('arquivo_nome', 'N/A')}")
                                logger.info("=" * 80)
                                sys.stdout.flush()

                                # REGISTRAR DOWNLOAD NA TABELA downloads_canopus
                                try:
                                    logger.info("🔍 DEBUG: Iniciando processo de registro no banco...")
                                    sys.stdout.flush()

                                    arquivo_caminho = resultado.get('dados_boleto', {}).get('arquivo_caminho')
                                    arquivo_nome = resultado.get('dados_boleto', {}).get('arquivo_nome')
                                    arquivo_tamanho = resultado.get('dados_boleto', {}).get('arquivo_tamanho', 0)

                                    logger.info(f"🔍 DEBUG: arquivo_caminho={arquivo_caminho}")
                                    logger.info(f"🔍 DEBUG: arquivo_nome={arquivo_nome}")
                                    logger.info(f"🔍 DEBUG: arquivo_tamanho={arquivo_tamanho}")
                                    sys.stdout.flush()

                                    if not arquivo_caminho:
                                        logger.error("❌ DEBUG: arquivo_caminho está None!")
                                        sys.stdout.flush()
                                    elif not Path(arquivo_caminho).exists():
                                        logger.error(f"❌ DEBUG: Arquivo não existe: {arquivo_caminho}")
                                        sys.stdout.flush()
                                    else:
                                        logger.info(f"✅ DEBUG: Arquivo existe: {arquivo_caminho}")
                                        sys.stdout.flush()

                                        atualizar_status(etapa=f'Convertendo PDF para base64... ({idx}/{len(cpfs)})')

                                        # CONVERTER PDF PARA BASE64
                                        import base64
                                        try:
                                            with open(arquivo_caminho, 'rb') as pdf_file:
                                                pdf_bytes = pdf_file.read()
                                                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

                                            logger.info(f"✅ PDF convertido para base64: {len(pdf_base64)} caracteres")
                                            sys.stdout.flush()
                                        except Exception as e_base64:
                                            logger.error(f"❌ Erro ao converter PDF para base64: {e_base64}")
                                            sys.stdout.flush()
                                            continue

                                        atualizar_status(etapa=f'Registrando download no banco... ({idx}/{len(cpfs)})')

                                        logger.info("🔍 DEBUG: Conectando ao banco...")
                                        sys.stdout.flush()

                                        with get_db_connection() as conn_import:
                                            with conn_import.cursor() as cur_import:
                                                logger.info(f"🔍 DEBUG: Buscando consultor_id para CPF {cpf}...")
                                                sys.stdout.flush()

                                                # Buscar consultor_id pelo CPF do cliente
                                                cur_import.execute("""
                                                    SELECT consultor_id FROM clientes_finais
                                                    WHERE cpf = %s AND ativo = TRUE
                                                    LIMIT 1
                                                """, (cpf,))

                                                consultor_row = cur_import.fetchone()
                                                consultor_id = consultor_row['consultor_id'] if consultor_row else None

                                                logger.info(f"🔍 DEBUG: consultor_id encontrado: {consultor_id}")
                                                sys.stdout.flush()

                                                # Verificar se download já existe
                                                logger.info(f"🔍 DEBUG: Verificando se download já existe...")
                                                sys.stdout.flush()

                                                cur_import.execute("""
                                                    SELECT id FROM downloads_canopus
                                                    WHERE cpf = %s AND nome_arquivo = %s
                                                """, (cpf, arquivo_nome))

                                                existe = cur_import.fetchone()
                                                logger.info(f"🔍 DEBUG: Download existe? {existe is not None}")
                                                sys.stdout.flush()

                                                if not existe:
                                                    logger.info(f"🔍 DEBUG: Inserindo registro no banco...")
                                                    logger.info(f"   CPF: {cpf}")
                                                    logger.info(f"   Consultor ID: {consultor_id}")
                                                    logger.info(f"   Nome arquivo: {arquivo_nome}")
                                                    logger.info(f"   Tamanho base64: {len(pdf_base64)} caracteres")
                                                    logger.info(f"   Tamanho bytes: {arquivo_tamanho}")
                                                    sys.stdout.flush()

                                                    # Inserir registro de download COM BASE64
                                                    cur_import.execute("""
                                                        INSERT INTO downloads_canopus (
                                                            consultor_id,
                                                            cpf,
                                                            nome_arquivo,
                                                            caminho_arquivo,
                                                            tamanho_bytes,
                                                            status,
                                                            data_download,
                                                            created_at
                                                        ) VALUES (
                                                            %s, %s, %s, %s, %s, 'sucesso', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                                                        )
                                                    """, (
                                                        consultor_id,
                                                        cpf,
                                                        arquivo_nome,
                                                        pdf_base64,  # SALVANDO BASE64 ao invés do caminho
                                                        arquivo_tamanho
                                                    ))

                                                    logger.info("🔍 DEBUG: Fazendo commit...")
                                                    sys.stdout.flush()

                                                    conn_import.commit()

                                                    logger.info(f"💾 ✅ Download registrado no banco: {arquivo_nome}")
                                                    sys.stdout.flush()

                                                    # EXTRAIR DADOS DO PDF E SALVAR NA TABELA BOLETOS
                                                    try:
                                                        logger.info("📄 Extraindo dados do PDF para tabela boletos...")
                                                        sys.stdout.flush()

                                                        from services.pdf_extractor import extrair_dados_boleto

                                                        dados_pdf = extrair_dados_boleto(arquivo_caminho)

                                                        if dados_pdf.get('sucesso'):
                                                            logger.info(f"✅ Dados extraídos: venc={dados_pdf.get('vencimento_str')}, valor=R$ {dados_pdf.get('valor', 0):.2f}")
                                                            sys.stdout.flush()

                                                            # Buscar cliente_final_id pelo CPF
                                                            cur_import.execute("""
                                                                SELECT id, consultor_id FROM clientes_finais
                                                                WHERE cpf = %s AND ativo = TRUE
                                                                LIMIT 1
                                                            """, (cpf,))

                                                            cliente_row = cur_import.fetchone()

                                                            if cliente_row:
                                                                cliente_final_id = cliente_row['id']
                                                                consultor_id_boleto = cliente_row['consultor_id']

                                                                # Buscar cliente_nexus_id do consultor
                                                                cur_import.execute("""
                                                                    SELECT cliente_nexus_id FROM consultores
                                                                    WHERE id = %s
                                                                    LIMIT 1
                                                                """, (consultor_id_boleto,))

                                                                consultor_nexus = cur_import.fetchone()
                                                                cliente_nexus_id = consultor_nexus['cliente_nexus_id'] if consultor_nexus else 1

                                                                # Verificar se boleto já existe
                                                                numero_boleto = dados_pdf.get('nosso_numero') or dados_pdf.get('grupo_cota') or f"CANOPUS-{cpf}"

                                                                cur_import.execute("""
                                                                    SELECT id FROM boletos
                                                                    WHERE cliente_final_id = %s
                                                                    AND data_vencimento = %s
                                                                    AND valor_original = %s
                                                                    LIMIT 1
                                                                """, (
                                                                    cliente_final_id,
                                                                    dados_pdf.get('vencimento'),
                                                                    dados_pdf.get('valor', 0)
                                                                ))

                                                                boleto_existe = cur_import.fetchone()

                                                                if not boleto_existe:
                                                                    # Extrair mês e ano do vencimento
                                                                    vencimento = dados_pdf.get('vencimento')
                                                                    mes_ref = vencimento.month if vencimento else mes
                                                                    ano_ref = vencimento.year if vencimento else (int(ano) if ano else 2025)

                                                                    # Inserir boleto
                                                                    cur_import.execute("""
                                                                        INSERT INTO boletos (
                                                                            cliente_final_id,
                                                                            cliente_nexus_id,
                                                                            numero_boleto,
                                                                            valor_original,
                                                                            data_vencimento,
                                                                            data_emissao,
                                                                            mes_referencia,
                                                                            ano_referencia,
                                                                            numero_parcela,
                                                                            descricao,
                                                                            status,
                                                                            status_envio,
                                                                            pdf_filename,
                                                                            pdf_path,
                                                                            pdf_size,
                                                                            gerado_por,
                                                                            created_at,
                                                                            updated_at
                                                                        ) VALUES (
                                                                            %s, %s, %s, %s, %s, CURRENT_DATE, %s, %s,
                                                                            1, %s, 'pendente', 'nao_enviado',
                                                                            %s, %s, %s, 'automacao_canopus',
                                                                            NOW(), NOW()
                                                                        ) RETURNING id
                                                                    """, (
                                                                        cliente_final_id,
                                                                        cliente_nexus_id,
                                                                        numero_boleto,
                                                                        dados_pdf.get('valor', 0),
                                                                        dados_pdf.get('vencimento'),
                                                                        mes_ref,
                                                                        ano_ref,
                                                                        f"Boleto {dados_pdf.get('grupo_cota', '')}",
                                                                        arquivo_nome,
                                                                        arquivo_caminho,
                                                                        arquivo_tamanho
                                                                    ))

                                                                    boleto_id = cur_import.fetchone()['id']
                                                                    conn_import.commit()

                                                                    logger.info(f"💾 ✅ Boleto #{boleto_id} salvo na tabela boletos!")
                                                                    sys.stdout.flush()
                                                                else:
                                                                    logger.info(f"⏭️ Boleto já existe na tabela boletos")
                                                                    sys.stdout.flush()
                                                            else:
                                                                logger.warning(f"⚠️ Cliente não encontrado para CPF {cpf}")
                                                                sys.stdout.flush()
                                                        else:
                                                            logger.warning(f"⚠️ Falha ao extrair dados do PDF")
                                                            sys.stdout.flush()

                                                    except Exception as e_boleto:
                                                        logger.error(f"❌ Erro ao salvar boleto na tabela boletos: {e_boleto}")
                                                        logger.exception("Traceback:")
                                                        sys.stdout.flush()

                                                else:
                                                    logger.info(f"⏭️ Download já registrado: {arquivo_nome}")
                                                    sys.stdout.flush()

                                except Exception as e_import:
                                    logger.error(f"❌ Erro ao registrar download no banco: {e_import}")
                                    logger.exception("Traceback:")
                                    sys.stdout.flush()

                                # Atualizar status com sucesso
                                atualizar_status(
                                    etapa=f'Boleto baixado e importado! ({idx}/{len(cpfs)})',
                                    progresso=idx
                                )

                                # Aguardar 3 segundos antes do próximo (para você ver o sucesso)
                                await asyncio.sleep(3)

                            elif resultado.get('status') == CanopusConfig.Status.CPF_NAO_ENCONTRADO:
                                stats['cpf_nao_encontrado'] += 1
                                stats['processados'] += 1
                                logger.warning("=" * 80)
                                logger.warning(f"⚠️ CPF {idx}/{len(cpfs)} NÃO ENCONTRADO: {cpf}")
                                logger.warning("Aguardando 5 segundos antes de continuar...")
                                logger.warning("=" * 80)
                                await asyncio.sleep(5)

                            elif resultado.get('status') == CanopusConfig.Status.SEM_BOLETO:
                                stats['sem_boleto'] += 1
                                stats['processados'] += 1
                                logger.warning("=" * 80)
                                logger.warning(f"📄 SEM BOLETO: {cpf} - {resultado.get('mensagem')}")
                                logger.warning("Aguardando 5 segundos antes de continuar...")
                                logger.warning("=" * 80)
                                await asyncio.sleep(5)

                            else:
                                stats['erros'] += 1
                                stats['processados'] += 1
                                logger.error("=" * 80)
                                logger.error(f"❌ ERRO no CPF {idx}/{len(cpfs)}: {cpf}")
                                logger.error(f"Mensagem: {resultado.get('mensagem')}")
                                logger.error("Aguardando 5 segundos antes de continuar...")
                                logger.error("=" * 80)
                                await asyncio.sleep(5)

                        except Exception as e:
                            stats['erros'] += 1
                            stats['processados'] += 1
                            logger.error("=" * 80)
                            logger.error(f"❌ EXCEÇÃO no CPF {idx}/{len(cpfs)}: {cpf}")
                            logger.error(f"Erro: {str(e)}")
                            logger.error("Aguardando 5 segundos antes de continuar...")
                            logger.error("=" * 80)
                            await asyncio.sleep(5)

                    # Monitoramento final de memória
                    mem_final = process.memory_info().rss / 1024 / 1024
                    logger.info("=" * 80)
                    logger.info("🎉 DOWNLOADS CONCLUÍDOS!")
                    logger.info("=" * 80)
                    logger.info(f"✅ Sucessos: {stats['sucessos']}")
                    logger.info(f"❌ Erros: {stats['erros']}")
                    logger.info(f"⚠️ CPF não encontrado: {stats['cpf_nao_encontrado']}")
                    logger.info(f"📄 Sem boleto: {stats['sem_boleto']}")
                    logger.info(f"📊 Total processados: {stats['processados']}/{stats['total']}")
                    logger.info(f"⏭️ Já baixados anteriormente: {stats['ja_baixados']}")
                    logger.info(f"📈 Total geral: {stats['processados'] + stats['ja_baixados']}")
                    logger.info("=" * 80)
                    logger.info(f"💾 Os boletos estão em: {pasta_destino}")
                    logger.info("💾 Registros salvos na tabela: downloads_canopus")
                    logger.info(f"📊 Memória final: {mem_final:.1f} MB")
                    logger.info("=" * 80)
                    logger.info("✅ EXECUÇÃO FINALIZADA NORMALMENTE (SEM CRASH)")
                    logger.info("=" * 80)
                    sys.stdout.flush()

                    # Finalizar execução com sucesso
                    finalizar_execucao(sucesso=True)

            # Rodar o loop assíncrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(processar_todos())
            except Exception as e:
                logger.error(f"❌ Erro na execução: {e}")
                finalizar_execucao(sucesso=False)
                atualizar_status(erro=str(e))
            finally:
                loop.close()

        # Iniciar thread em background
        logger.info("🔧 Criando thread em background...")
        thread = threading.Thread(target=processar_downloads_background, daemon=True, name="DownloadBoletosThread")
        logger.info("🚀 Iniciando thread...")
        thread.start()
        logger.info(f"✅ Thread iniciada! Ativa: {thread.is_alive()}, Nome: {thread.name}")

        # Retornar imediatamente
        logger.info("📤 Retornando resposta ao cliente...")
        if total_ja_baixados > 0:
            mensagem = f'Retomando download: {len(cpfs)} clientes restantes (de {len(cpfs_todos)} total). Já processados: {total_ja_baixados}.'
        else:
            mensagem = f'Download iniciado para {len(cpfs)} clientes.'

        return jsonify({
            'success': True,
            'message': mensagem,
            'data': {
                'ponto_venda': ponto_venda,
                'total_clientes': len(cpfs_todos),
                'ja_baixados': total_ja_baixados,
                'a_processar': len(cpfs),
                'indice_inicio': indice_inicio + 1,
                'status': 'iniciado',
                'info': 'Acompanhe o progresso em tempo real no monitoramento'
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro ao processar downloads: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': f'Erro ao processar downloads: {str(e)}'
        }), 500


@automation_canopus_bp.route('/importar-planilha-dener', methods=['POST'])
@handle_errors
def importar_planilha_dener():
    """
    Importa a planilha do Dener para o banco de dados usando EXTRATOR ROBUSTO
    Suporta seleção de pontos de venda (17308, 24627 ou ambos)
    À prova de erros com validações completas
    """
    from pathlib import Path

    logger.info("📊 Iniciando importação da planilha do Dener com extrator robusto...")

    try:
        # Importar extrator
        sys.path.insert(0, str(backend_path))
        from services.excel_extractor import extrair_clientes_planilha

        # Obter configuração de pontos de venda
        data = request.get_json() or {}
        pontos_venda_selecionados = data.get('pontos_venda', '24627')  # Padrão: apenas 24627

        logger.info(f"📍 Pontos de venda selecionados: {pontos_venda_selecionados}")

        # Buscar qualquer planilha geral na pasta (DENER, DANNER, etc)
        pasta_excel = Path("D:/Nexus/automation/canopus/excel_files")
        planilhas_disponiveis = list(pasta_excel.glob("*__PLANILHA_GERAL.xlsx"))

        if not planilhas_disponiveis:
            logger.info(f"📂 Nenhuma planilha encontrada em: {pasta_excel}")
            return jsonify({
                'success': False,
                'error': f'Nenhuma planilha encontrada em {pasta_excel}. Por favor, baixe a planilha do Google Drive primeiro.'
            }), 404

        # Usar a primeira planilha encontrada
        planilha_path = planilhas_disponiveis[0]
        logger.info(f"📂 Planilha encontrada: {planilha_path.name}")

        # Determinar quais PVs extrair
        if pontos_venda_selecionados == 'ambos':
            filtro_pv = ['17308', '24627']
            logger.info(f"📋 Importando de AMBOS os PVs (17308 + 24627)")
        elif pontos_venda_selecionados == '17308':
            filtro_pv = ['17308']
            logger.info(f"📋 Importando apenas PV 17308")
        else:  # '24627' ou padrão
            filtro_pv = ['24627']
            logger.info(f"📋 Importando apenas PV 24627")

        # ====================================================================
        # ETAPA 1: EXTRAÇÃO DOS DADOS (usando extrator robusto)
        # ====================================================================
        logger.info(f"🔍 ETAPA 1: Extraindo dados da planilha...")

        resultado_extracao = extrair_clientes_planilha(
            arquivo_excel=str(planilha_path),
            pontos_venda=filtro_pv
        )

        if not resultado_extracao['sucesso']:
            return jsonify({
                'success': False,
                'error': f"Erro ao extrair planilha: {resultado_extracao.get('erro', 'Erro desconhecido')}"
            }), 500

        clientes = resultado_extracao['clientes']
        logger.info(f"✅ {len(clientes)} clientes válidos extraídos")
        logger.info(f"📊 Distribuição por PV: {resultado_extracao['estatisticas_pv']}")

        if len(clientes) == 0:
            return jsonify({
                'success': False,
                'error': 'Nenhum cliente válido encontrado na planilha para os PVs selecionados'
            }), 400

        # ====================================================================
        # ETAPA 2: IMPORTAÇÃO PARA O BANCO DE DADOS
        # ====================================================================
        logger.info(f"💾 ETAPA 2: Importando {len(clientes)} clientes para o banco...")

        importados = 0
        atualizados = 0
        erros = 0
        erros_detalhes = []

        for idx, cliente in enumerate(clientes, 1):
            conn = None
            try:
                cpf = cliente['cpf']
                cpf_formatado = cliente['cpf_formatado']
                nome = cliente['nome']
                ponto_venda = cliente['ponto_venda']

                logger.debug(f"[{idx}/{len(clientes)}] Processando: {nome} (CPF: {cpf_formatado}, PV: {ponto_venda})")

                conn = get_db_connection()
                with conn.cursor() as cur:
                    # Verificar se cliente já existe (buscar por CPF + PV)
                    cur.execute("""
                        SELECT id, nome_completo FROM clientes_finais
                        WHERE cpf = %s AND ponto_venda = %s
                    """, (cpf, ponto_venda))

                    existing = cur.fetchone()

                    # Gerar número de contrato único
                    numero_contrato = f"CANOPUS-{ponto_venda}-{cpf}"

                    # Buscar ID do consultor (Dener/Danner)
                    cur.execute("""
                        SELECT id FROM consultores
                        WHERE nome ILIKE '%dener%' OR nome ILIKE '%danner%' OR nome ILIKE '%den%'
                        LIMIT 1
                    """)
                    consultor_row = cur.fetchone()
                    consultor_id = consultor_row['id'] if consultor_row else None

                    # Buscar primeiro cliente_nexus disponível
                    cur.execute("SELECT id FROM clientes_nexus ORDER BY id LIMIT 1")
                    cliente_nexus_row = cur.fetchone()
                    cliente_nexus_id = cliente_nexus_row['id'] if cliente_nexus_row else None

                    if existing:
                        # ========== ATUALIZAR CLIENTE EXISTENTE ==========
                        cliente_id = existing['id']
                        logger.info(f"   🔄 Atualizando cliente existente (ID: {cliente_id}): {nome}")

                        cur.execute("""
                            UPDATE clientes_finais
                            SET nome_completo = %s,
                                ponto_venda = %s,
                                numero_contrato = %s,
                                consultor_id = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (nome, ponto_venda, numero_contrato, consultor_id, cliente_id))

                        atualizados += 1
                        logger.debug(f"   ✅ Cliente atualizado!")

                    else:
                        # ========== INSERIR NOVO CLIENTE ==========
                        logger.info(f"   ➕ Criando novo cliente: {nome} (CPF: {cpf_formatado}, PV: {ponto_venda})")

                        # Dados básicos obrigatórios
                        whatsapp = '5567999999999'  # Placeholder
                        telefone_celular = whatsapp

                        cur.execute("""
                            INSERT INTO clientes_finais (
                                cliente_nexus_id,
                                nome_completo,
                                cpf,
                                telefone_celular,
                                whatsapp,
                                numero_contrato,
                                grupo_consorcio,
                                cota_consorcio,
                                valor_credito,
                                valor_parcela,
                                prazo_meses,
                                data_adesao,
                                status_contrato,
                                origem,
                                ativo,
                                created_at,
                                updated_at,
                                consultor_id,
                                ponto_venda
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s
                            )
                        """, (
                            cliente_nexus_id,  # 1. cliente_nexus_id
                            nome,  # 2. nome_completo
                            cpf,  # 3. cpf
                            telefone_celular,  # 4. telefone_celular
                            whatsapp,  # 5. whatsapp
                            numero_contrato,  # 6. numero_contrato
                            '0000',  # 7. grupo_consorcio (padrão)
                            '001',  # 8. cota_consorcio (padrão)
                            0.00,  # 9. valor_credito
                            0.00,  # 10. valor_parcela
                            80,  # 11. prazo_meses (padrão)
                            datetime.now().date(),  # 12. data_adesao
                            'ATIVO',  # 13. status_contrato
                            f'PLANILHA_DENER_PV{ponto_venda}',  # 14. origem
                            True,  # 15. ativo
                            consultor_id,  # 16. consultor_id
                            ponto_venda  # 17. ponto_venda
                        ))

                        importados += 1
                        logger.debug(f"   ✅ Cliente criado!")

                    conn.commit()

                conn.close()

            except Exception as e:
                erros += 1
                erro_msg = f"CPF {cliente.get('cpf_formatado', '?')}: {str(e)}"
                erros_detalhes.append(erro_msg)
                logger.error(f"   ❌ ERRO: {erro_msg}")

                if conn:
                    try:
                        conn.rollback()
                        conn.close()
                    except:
                        pass

        # ====================================================================
        # RESULTADO FINAL
        # ====================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ IMPORTAÇÃO CONCLUÍDA!")
        logger.info(f"   Total processado: {len(clientes)}")
        logger.info(f"   ➕ Novos clientes: {importados}")
        logger.info(f"   🔄 Atualizados: {atualizados}")
        logger.info(f"   ❌ Erros: {erros}")
        logger.info(f"{'='*70}\n")

        return jsonify({
            'success': True,
            'message': f'Importação concluída com sucesso!',
            'data': {
                'total_processados': len(clientes),
                'importados': importados,
                'atualizados': atualizados,
                'erros': erros,
                'erros_detalhes': erros_detalhes[:5],  # Primeiros 5 erros
                'distribuicao_pv': resultado_extracao['estatisticas_pv']
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro fatal na importação: {e}")
        import traceback
        logger.error(traceback.format_exc())

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@automation_canopus_bp.route('/importar-boletos', methods=['POST'])
@handle_errors
def importar_boletos():
    """
    Importa todos os PDFs da tabela downloads_canopus para o banco de dados
    Lê cada PDF (base64), extrai dados e cria clientes + boletos
    """
    import base64
    import tempfile
    import os
    from datetime import datetime
    from psycopg.rows import dict_row

    logger.info("📥 Iniciando importação de boletos da tabela downloads_canopus...")

    # Importar a função de extração de PDF
    sys.path.insert(0, str(backend_path))
    from services.pdf_extractor import extrair_dados_boleto

    # Buscar cliente_nexus_id do usuário logado (não mais hardcoded)
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Buscar o primeiro (e único) cliente_nexus ativo
                cur.execute("""
                    SELECT id FROM clientes_nexus
                    WHERE ativo = TRUE
                    ORDER BY id
                    LIMIT 1
                """)
                cliente_nexus_row = cur.fetchone()

                if not cliente_nexus_row:
                    logger.error("❌ Nenhum cliente_nexus encontrado na tabela!")
                    return jsonify({
                        'success': False,
                        'error': 'Nenhum cliente Nexus cadastrado no sistema'
                    }), 404

                cliente_nexus_id = cliente_nexus_row['id']
                logger.info(f"✅ Usando cliente_nexus_id: {cliente_nexus_id}")
    except Exception as e:
        logger.error(f"❌ Erro ao buscar cliente_nexus_id: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar cliente Nexus: {str(e)}'
        }), 500

    # Buscar PDFs da tabela downloads_canopus que ainda não foram importados
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT
                        dc.id,
                        dc.cpf,
                        dc.nome_arquivo,
                        dc.caminho_arquivo,
                        dc.tamanho_bytes
                    FROM downloads_canopus dc
                    WHERE dc.status = 'sucesso'
                    AND NOT EXISTS (
                        SELECT 1 FROM boletos b
                        WHERE b.pdf_filename = dc.nome_arquivo
                    )
                    ORDER BY dc.created_at DESC
                """)
                pdfs_db = cur.fetchall()
    except Exception as e:
        logger.error(f"❌ Erro ao buscar PDFs do banco: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro ao buscar PDFs: {str(e)}'
        }), 500

    if not pdfs_db:
        logger.info("ℹ️  Nenhum PDF novo para importar")
        return jsonify({
            'success': True,
            'message': 'Nenhum PDF novo para importar',
            'data': {
                'total_pdfs': 0,
                'importados': 0,
                'clientes_criados': 0,
                'clientes_existentes': 0,
                'ja_existentes': 0,
                'sem_cliente': 0,
                'erros': 0,
                'pdfs_sem_dados': 0
            }
        })

    logger.info(f"📄 Encontrados {len(pdfs_db)} PDFs para processar")

    stats = {
        'total_pdfs': len(pdfs_db),
        'clientes_criados': 0,
        'clientes_existentes': 0,
        'boletos_criados': 0,
        'erros': 0,
        'pdfs_sem_dados': 0
    }

    # Processar cada PDF
    for idx, pdf_row in enumerate(pdfs_db, 1):
        pdf_filename = pdf_row['nome_arquivo']
        pdf_base64 = pdf_row['caminho_arquivo']
        cpf_original = pdf_row['cpf']
        conn = None
        temp_pdf_path = None

        logger.info(f"[{idx}/{len(pdfs_db)}] Processando: {pdf_filename[:50]}")

        try:
            # Decodificar PDF base64 e salvar em arquivo temporário
            try:
                pdf_bytes = base64.b64decode(pdf_base64)

                # Criar arquivo temporário
                temp_fd, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
                os.close(temp_fd)  # Fechar file descriptor

                with open(temp_pdf_path, 'wb') as f:
                    f.write(pdf_bytes)

                logger.info(f"   📄 PDF decodificado e salvo temporariamente")
            except Exception as e:
                logger.error(f"   ❌ Erro ao decodificar PDF base64: {e}")
                stats['erros'] += 1
                continue

            # Extrair dados do PDF
            dados_pdf = extrair_dados_boleto(temp_pdf_path)

            if not dados_pdf.get('sucesso'):
                logger.warning(f"   ⚠️  Não foi possível extrair dados do PDF")
                stats['pdfs_sem_dados'] += 1
                continue

            # Dados extraídos
            nome = dados_pdf.get('nome_pagador')
            cpf = dados_pdf.get('cpf', '').replace('.', '').replace('-', '').strip()
            vencimento = dados_pdf.get('vencimento')
            valor = dados_pdf.get('valor', 0)
            contrato = dados_pdf.get('contrato')

            # ====== VALIDAÇÕES RIGOROSAS PARA GARANTIR 100% DE EXATIDÃO ======

            # 1. Validar Nome
            if not nome or len(nome.strip()) < 3:
                logger.error(f"   ❌ VALIDAÇÃO FALHOU: Nome inválido ou muito curto: '{nome}'")
                stats['erros'] += 1
                continue

            # 2. Validar CPF
            if not cpf or len(cpf) != 11 or not cpf.isdigit():
                logger.error(f"   ❌ VALIDAÇÃO FALHOU: CPF inválido: '{cpf}' (tamanho: {len(cpf)})")
                stats['erros'] += 1
                continue

            # 3. Validar Vencimento
            if not vencimento:
                logger.error(f"   ❌ VALIDAÇÃO FALHOU: Vencimento não encontrado no PDF")
                stats['erros'] += 1
                continue

            # 4. Validar Valor
            if not valor or valor <= 0:
                logger.error(f"   ❌ VALIDAÇÃO FALHOU: Valor inválido: R$ {valor}")
                stats['erros'] += 1
                continue

            # 5. Validar Grupo/Cota
            grupo_cota_completo = dados_pdf.get('grupo_cota', '')
            if not grupo_cota_completo or grupo_cota_completo == 'N/A':
                logger.warning(f"   ⚠️  Grupo/Cota não encontrado - usando valores padrão")

            logger.info(f"   ✅ VALIDAÇÕES OK: Nome: {nome}, CPF: {cpf}, Valor: R$ {valor:.2f}, Venc: {vencimento.strftime('%d/%m/%Y') if vencimento else 'N/A'}")

            conn = get_db_connection()
            with conn.cursor() as cur:
                # Verificar se cliente já existe (por CPF)
                cur.execute("""
                    SELECT id, nome_completo, whatsapp
                    FROM clientes_finais
                    WHERE cpf = %s AND cliente_nexus_id = %s
                """, (cpf, cliente_nexus_id))

                cliente_existente = cur.fetchone()

                if cliente_existente:
                    cliente_id = cliente_existente['id']
                    logger.info(f"   ℹ️  Cliente já existe (ID: {cliente_id})")
                    stats['clientes_existentes'] += 1
                else:
                    # Criar novo cliente
                    logger.info(f"   ➕ Criando novo cliente...")

                    whatsapp = '55679999999999'  # Placeholder
                    telefone_celular = whatsapp
                    numero_contrato = f"TEMP-{cpf}"

                    # Separar grupo e cota do PDF
                    grupo_cota_completo = dados_pdf.get('grupo_cota', '')
                    if grupo_cota_completo and '-' in grupo_cota_completo:
                        partes = grupo_cota_completo.split('-')
                        grupo_consorcio = partes[0] if len(partes) > 0 else 'N/A'
                        cota_consorcio = partes[1] if len(partes) > 1 else 'N/A'
                    else:
                        grupo_consorcio = 'N/A'
                        cota_consorcio = 'N/A'

                    valor_parcela = valor
                    prazo_meses = 60
                    data_adesao = datetime.now().date()

                    cur.execute("""
                        INSERT INTO clientes_finais
                        (cliente_nexus_id, nome_completo, cpf, whatsapp, telefone_celular, numero_contrato,
                         grupo_consorcio, cota_consorcio, valor_credito, valor_parcela, prazo_meses,
                         data_adesao, ativo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (cliente_nexus_id, nome, cpf, whatsapp, telefone_celular, numero_contrato,
                          grupo_consorcio, cota_consorcio, 0.0, valor_parcela, prazo_meses,
                          data_adesao, True))

                    novo_cliente = cur.fetchone()
                    cliente_id = novo_cliente['id']
                    logger.info(f"   ✅ Cliente criado (ID: {cliente_id})")
                    stats['clientes_criados'] += 1

                # Verificar se boleto já existe para este cliente e mês
                mes_ref = vencimento.month if vencimento else datetime.now().month
                ano_ref = vencimento.year if vencimento else datetime.now().year

                boleto_existente = cur.execute("""
                    SELECT id FROM boletos
                    WHERE cliente_final_id = %s
                    AND mes_referencia = %s
                    AND ano_referencia = %s
                """, (cliente_id, mes_ref, ano_ref))

                if cur.fetchone():
                    logger.info(f"   ℹ️  Boleto já existe para este cliente/mês - pulando")
                    stats['boletos_ja_existentes'] = stats.get('boletos_ja_existentes', 0) + 1
                    continue

                # Criar boleto
                logger.info(f"   ➕ Criando boleto...")

                numero_boleto = contrato or f"CANOPUS-{cpf}-{mes_ref:02d}{ano_ref}"

                # Usar base64 ou temp path (preferir não salvar path temporário)
                pdf_path_salvar = None  # Não salvar path temporário, usar base64 de downloads_canopus

                cur.execute("""
                    INSERT INTO boletos
                    (cliente_nexus_id, cliente_final_id, numero_boleto, valor_original,
                     data_vencimento, data_emissao, mes_referencia, ano_referencia,
                     numero_parcela, pdf_path, pdf_filename, pdf_size, status, status_envio, gerado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    cliente_nexus_id,
                    cliente_id,
                    numero_boleto,
                    valor,
                    vencimento,
                    datetime.now().date(),
                    mes_ref,
                    ano_ref,
                    1,
                    pdf_path_salvar,
                    pdf_filename,
                    pdf_row['tamanho_bytes'],
                    'pendente',
                    'nao_enviado',
                    'importacao_canopus'
                ))

                novo_boleto = cur.fetchone()
                boleto_id = novo_boleto['id']
                logger.info(f"   ✅ Boleto criado (ID: {boleto_id})")
                stats['boletos_criados'] += 1

                # Commit apenas se tudo deu certo
                conn.commit()
                logger.info(f"   💾 Transação confirmada com sucesso!")

        except Exception as e:
            # Rollback em caso de erro
            if conn:
                try:
                    conn.rollback()
                    logger.error(f"   ↩️  Rollback realizado devido ao erro")
                except:
                    pass

            logger.error(f"   ❌ ERRO ao processar PDF: {str(e)}")
            import traceback
            logger.error(f"   📋 Stack trace: {traceback.format_exc()}")
            stats['erros'] += 1

        finally:
            # Limpar arquivo temporário
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.remove(temp_pdf_path)
                    logger.debug(f"   🗑️  Arquivo temporário removido")
                except:
                    pass

            # Garantir fechamento da conexão
            if conn:
                try:
                    conn.close()
                except:
                    pass

    logger.info(f"✅ Importação concluída: {stats['boletos_criados']} boletos criados")

    return jsonify({
        'success': True,
        'message': 'Boletos importados com sucesso',
        'data': {
            'total_pdfs': stats['total_pdfs'],
            'importados': stats['boletos_criados'],
            'clientes_criados': stats['clientes_criados'],
            'clientes_existentes': stats['clientes_existentes'],
            'ja_existentes': 0,  # Compatibilidade com frontend
            'sem_cliente': 0,  # Não se aplica - criamos clientes automaticamente
            'erros': stats['erros'],
            'pdfs_sem_dados': stats['pdfs_sem_dados']
        }
    })


@automation_canopus_bp.route('/boletos-baixados', methods=['GET'])
@handle_errors
def listar_boletos_baixados():
    """
    Lista todos os boletos baixados DO BANCO DE DADOS (PostgreSQL)
    Agora funciona no Render! Busca de downloads_canopus E boletos
    """
    from models.database import get_db_connection
    from psycopg.rows import dict_row
    import logging

    logger = logging.getLogger(__name__)
    boletos = []

    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # BUSCAR DA TABELA downloads_canopus (que registra os downloads)
                # JOIN com clientes_finais para pegar dados completos
                # Usar DISTINCT ON para evitar duplicação do MESMO boleto (CPF + arquivo)
                # Isso garante que cada boleto único apareça apenas uma vez, pegando o download mais recente
                cur.execute("""
                    SELECT DISTINCT ON (dc.cpf, dc.nome_arquivo)
                        dc.id,
                        dc.cpf,
                        dc.nome_arquivo,
                        dc.caminho_arquivo,
                        dc.tamanho_bytes,
                        dc.status,
                        dc.data_download,
                        dc.created_at,
                        cf.nome_completo as cliente_nome,
                        cf.whatsapp,
                        b.valor_original,
                        b.data_vencimento,
                        b.numero_boleto as grupo_cota,
                        b.status as status_boleto
                    FROM downloads_canopus dc
                    LEFT JOIN clientes_finais cf ON dc.cpf = cf.cpf
                    LEFT JOIN LATERAL (
                        SELECT valor_original, data_vencimento, numero_boleto, status
                        FROM boletos
                        WHERE boletos.cliente_final_id = cf.id
                        ORDER BY created_at DESC
                        LIMIT 1
                    ) b ON true
                    WHERE dc.status = 'sucesso'
                    ORDER BY dc.cpf, dc.nome_arquivo, dc.created_at DESC
                    LIMIT 200
                """)

                rows = cur.fetchall()

                for row in rows:
                    try:
                        # Formatar valor
                        valor_original = row.get('valor_original', 0) or 0
                        valor_str = f"R$ {valor_original:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

                        # Formatar vencimento
                        vencimento_obj = row.get('data_vencimento')
                        vencimento_str = vencimento_obj.strftime('%d/%m/%Y') if vencimento_obj else 'N/A'

                        # Data de download
                        data_download_obj = row.get('data_download') or row.get('created_at')
                        data_download_timestamp = data_download_obj.timestamp() if data_download_obj else 0

                        boleto_info = {
                            'arquivo_nome': row.get('nome_arquivo', 'N/A'),
                            'caminho': row.get('caminho_arquivo', 'N/A'),
                            'cliente_nome': row.get('cliente_nome', 'N/A'),
                            'cpf': row.get('cpf', 'N/A'),
                            'valor': valor_original,
                            'valor_str': valor_str,
                            'vencimento': vencimento_str,
                            'grupo_cota': row.get('grupo_cota', 'N/A'),
                            'nosso_numero': row.get('grupo_cota', 'N/A'),
                            'mes': vencimento_str.split('/')[1] if vencimento_str != 'N/A' else 'N/A',
                            'tamanho': row.get('tamanho_bytes', 0),
                            'data_download': data_download_timestamp,
                            'status': row.get('status_boleto', 'processado'),
                            'dados_extraidos': True,
                            'whatsapp': row.get('whatsapp', 'N/A')
                        }

                        boletos.append(boleto_info)

                    except Exception as e:
                        logger.error(f"Erro ao processar row do banco: {e}")
                        continue

    except Exception as e:
        logger.error(f"Erro ao buscar boletos do banco: {e}")
        return jsonify({
            'success': False,
            'data': [],
            'error': str(e)
        })

    # Já vem ordenado do banco (ORDER BY created_at DESC)

    response = jsonify({
        'success': True,
        'data': boletos,
        'total': len(boletos)
    })

    # Adicionar headers no-cache para evitar cache do navegador
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response


@automation_canopus_bp.route('/download-boleto', methods=['GET'])
@handle_errors
def download_boleto():
    """
    Faz download de um boleto específico DO BANCO DE DADOS (base64)
    Compatível com Render - não depende de filesystem
    """
    import base64
    from io import BytesIO
    from flask import send_file
    from psycopg.rows import dict_row

    nome_arquivo = request.args.get('nome')

    if not nome_arquivo:
        return jsonify({'error': 'Nome do arquivo não fornecido'}), 400

    logger.info(f"📥 Buscando PDF no banco: {nome_arquivo}")

    try:
        # Buscar PDF da tabela downloads_canopus
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("""
                    SELECT
                        nome_arquivo,
                        caminho_arquivo,
                        tamanho_bytes
                    FROM downloads_canopus
                    WHERE nome_arquivo = %s
                    LIMIT 1
                """, (nome_arquivo,))

                row = cur.fetchone()

                if not row:
                    logger.error(f"❌ PDF não encontrado no banco: {nome_arquivo}")
                    return jsonify({'error': f'Arquivo não encontrado: {nome_arquivo}'}), 404

                # Decodificar base64
                pdf_base64 = row['caminho_arquivo']

                try:
                    pdf_bytes = base64.b64decode(pdf_base64)
                    logger.info(f"✅ PDF decodificado: {len(pdf_bytes)} bytes")
                except Exception as e:
                    logger.error(f"❌ Erro ao decodificar base64: {e}")
                    return jsonify({'error': 'Erro ao decodificar PDF'}), 500

                # Criar BytesIO para enviar
                pdf_io = BytesIO(pdf_bytes)
                pdf_io.seek(0)

                logger.info(f"📤 Enviando PDF: {nome_arquivo}")

                return send_file(
                    pdf_io,
                    as_attachment=True,
                    download_name=nome_arquivo,
                    mimetype='application/pdf'
                )

    except Exception as e:
        logger.error(f"❌ Erro ao buscar PDF: {e}")
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500


@automation_canopus_bp.route('/limpar-downloads-antigos', methods=['POST'])
@handle_errors
def limpar_downloads_antigos():
    """
    Remove downloads com caminho de arquivo (formato antigo)
    Mantém apenas downloads com base64 (formato novo)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Contar quantos registros serão removidos
                cur.execute("""
                    SELECT COUNT(*) as total FROM downloads_canopus
                    WHERE caminho_arquivo NOT LIKE 'JVBERi0%'
                    AND caminho_arquivo NOT LIKE 'JVBER%'
                """)
                total_antigos = cur.fetchone()['total']

                logger.info(f"🗑️ Removendo {total_antigos} downloads com formato antigo...")

                # Deletar registros antigos (que têm caminho ao invés de base64)
                # Base64 de PDF sempre começa com "JVBERi0" (%PDF em base64)
                cur.execute("""
                    DELETE FROM downloads_canopus
                    WHERE caminho_arquivo NOT LIKE 'JVBERi0%'
                    AND caminho_arquivo NOT LIKE 'JVBER%'
                """)

                conn.commit()

                logger.info(f"✅ {total_antigos} registros antigos removidos com sucesso")

                return jsonify({
                    'success': True,
                    'message': f'{total_antigos} downloads antigos removidos',
                    'data': {
                        'removidos': total_antigos
                    }
                })

    except Exception as e:
        logger.error(f"❌ Erro ao limpar downloads antigos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# EXEMPLO DE USO (TESTE)
# ============================================================================
# NOVA ROTA PARA ADICIONAR EM automation_canopus.py
# Adicionar ANTES do bloco "if __name__ == '__main__':"

@automation_canopus_bp.route('/resetar-dados', methods=['POST'])
@handle_errors
def resetar_dados():
    """
    LIMPA TODOS OS DADOS (APENAS RESET, SEM REIMPORTAR)
    - Deleta todos os registros de clientes_finais
    - Deleta todos os registros de boletos
    - Opcionalmente deleta arquivos físicos de boletos
    - NÃO faz reimportação (diferente do resetar-e-reimportar)
    """
    logger.info("🗑️ Iniciando reset completo de dados...")

    try:
        data = request.get_json() if request.is_json else {}
        deletar_arquivos = data.get('deletar_arquivos', False)

        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()

        # Deletar boletos primeiro (por causa da FK)
        logger.info("   Deletando boletos do banco...")
        cur.execute("DELETE FROM boletos")
        boletos_deletados = cur.rowcount

        # Deletar clientes
        logger.info("   Deletando clientes_finais do banco...")
        cur.execute("DELETE FROM clientes_finais")
        clientes_deletados = cur.rowcount

        # Commit
        conn.commit()

        cur.close()
        db.return_connection(conn)

        arquivos_deletados = 0

        # Se solicitado, deletar arquivos físicos também
        if deletar_arquivos:
            from pathlib import Path
            import os

            logger.info("   🗑️ Deletando arquivos físicos de boletos...")
            downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

            if downloads_dir.exists():
                for pdf_file in downloads_dir.glob("**/*.pdf"):
                    try:
                        pdf_file.unlink()
                        arquivos_deletados += 1
                    except Exception as e:
                        logger.warning(f"   ⚠️ Erro ao deletar {pdf_file}: {e}")

                logger.info(f"   ✅ {arquivos_deletados} arquivos PDF deletados")

        logger.info(f"✅ Reset concluído: {clientes_deletados} clientes e {boletos_deletados} boletos deletados do banco")

        return jsonify({
            'success': True,
            'message': 'Dados resetados com sucesso',
            'clientes_deletados': clientes_deletados,
            'boletos_deletados': boletos_deletados,
            'arquivos_deletados': arquivos_deletados
        })

    except Exception as e:
        logger.error(f"❌ Erro ao resetar dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_canopus_bp.route('/resetar-e-reimportar', methods=['POST'])
@handle_errors
def resetar_e_reimportar():
    """
    LIMPA TODOS OS DADOS ANTIGOS e REIMPORTA DO ZERO
    - Limpa tabelas clientes_finais e boletos
    - Importa clientes do Excel (DENER__PLANILHA_GERAL.xlsx)
    - Importa boletos da pasta D:/Nexus/automation/canopus/downloads/Danner
    """
    import pandas as pd
    from pathlib import Path

    logger.info("🔄 Iniciando reset e reimportação completa...")

    try:
        db = Database()
        conn = db.get_connection()
        cur = conn.cursor()

        # ==================================================
        # 1. LIMPAR DADOS ANTIGOS
        # ==================================================
        logger.info("🗑️ Limpando dados antigos...")

        cur.execute("DELETE FROM boletos")
        boletos_deletados = cur.rowcount
        logger.info(f"   ✓ {boletos_deletados} boletos deletados")

        cur.execute("DELETE FROM clientes_finais")
        clientes_deletados = cur.rowcount
        logger.info(f"   ✓ {clientes_deletados} clientes deletados")

        conn.commit()

        # ==================================================
        # 2. IMPORTAR CLIENTES DO EXCEL
        # ==================================================
        logger.info("📊 Importando clientes do Excel...")

        excel_path = Path(r"D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx")

        if not excel_path.exists():
            return jsonify({
                'success': False,
                'error': f'Arquivo Excel não encontrado: {excel_path}'
            }), 404

        # Ler Excel (header=11 conforme código existente)
        df = pd.read_excel(excel_path, sheet_name=0, header=11)

        # IMPORTANTE: Pular a primeira linha, que contém os cabeçalhos duplicados
        df = df[1:].reset_index(drop=True)

        # Filtrar apenas linhas válidas (tem CPF e Nome)
        # Unnamed: 0 = CPF, Unnamed: 5 = Nome do Cliente
        df = df[df['Unnamed: 0'].notna() & df['Unnamed: 5'].notna()]

        clientes_importados = 0
        clientes_erros = 0

        # Buscar cliente_nexus_id do Danner
        cur.execute("SELECT id FROM consultores WHERE nome = 'Danner' LIMIT 1")
        consultor = cur.fetchone()
        consultor_id = consultor[0] if consultor else None

        for index, row in df.iterrows():
            try:
                # Extrair dados (CORRIGIDO: Unnamed: 0 = CPF, Unnamed: 5 = Nome)
                cpf_raw = str(row['Unnamed: 0']).strip()
                nome_raw = str(row['Unnamed: 5']).strip()

                # Pular linhas vazias ou inválidas
                if cpf_raw.lower() in ['nan', 'none', ''] or nome_raw.lower() in ['nan', 'none', '']:
                    continue

                # Limpar nome (remover sufixos como "- 70%", "70%", etc)
                import re
                nome = re.sub(r'\s*-?\s*\d+%?', '', nome_raw).strip()

                # Limpar CPF (remover pontos, hífens, espaços)
                cpf = ''.join(filter(str.isdigit, cpf_raw))

                # Validar CPF (deve ter exatamente 11 dígitos)
                if not cpf or len(cpf) != 11 or not cpf.isdigit():
                    logger.warning(f"   ⚠️ CPF inválido: {cpf_raw} (linha {index + 13})")
                    clientes_erros += 1
                    continue

                # Formatar CPF para XXX.XXX.XXX-XX
                cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

                # Gerar número de contrato único baseado no CPF
                numero_contrato = f"CANOPUS-{cpf}"

                # Buscar primeiro cliente_nexus disponível (para evitar FK error)
                # NOTA: Idealmente deveria vir da sessão do usuário, mas como é automação,
                # usa o primeiro cliente_nexus disponível
                cur.execute("SELECT id FROM clientes_nexus ORDER BY id LIMIT 1")
                cliente_nexus_row = cur.fetchone()
                cliente_nexus_id_import = cliente_nexus_row[0] if cliente_nexus_row else None

                # Inserir cliente
                cur.execute("""
                    INSERT INTO clientes_finais (
                        nome_completo, cpf, telefone_celular, whatsapp,
                        numero_contrato, grupo_consorcio, cota_consorcio,
                        valor_credito, valor_parcela, prazo_meses, data_adesao,
                        consultor_id, cliente_nexus_id, ativo,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, '', '',
                        %s, 'N/A', 'N/A',
                        0.0, 0.0, 0, NOW(),
                        %s, %s, TRUE,
                        NOW(), NOW()
                    )
                    ON CONFLICT (cpf) DO UPDATE SET
                        nome_completo = EXCLUDED.nome_completo,
                        consultor_id = EXCLUDED.consultor_id,
                        updated_at = NOW()
                    RETURNING id
                """, (nome, cpf_formatado, numero_contrato, consultor_id, cliente_nexus_id_import))

                cliente_id = cur.fetchone()[0]
                clientes_importados += 1

            except Exception as e:
                logger.error(f"   ❌ Erro ao importar cliente linha {index + 12}: {e}")
                clientes_erros += 1
                continue

        conn.commit()
        logger.info(f"   ✓ {clientes_importados} clientes importados, {clientes_erros} erros")

        # ==================================================
        # 3. IMPORTAR BOLETOS DA PASTA
        # ==================================================
        logger.info("📄 Importando boletos da pasta...")

        downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

        if not downloads_dir.exists():
            return jsonify({
                'success': False,
                'error': f'Pasta de boletos não encontrada: {downloads_dir}'
            }), 404

        pdfs = list(downloads_dir.glob("*.pdf"))

        meses = {
            'JANEIRO': 1, 'FEVEREIRO': 2, 'MARÇO': 3, 'MARCO': 3,
            'ABRIL': 4, 'MAIO': 5, 'JUNHO': 6,
            'JULHO': 7, 'AGOSTO': 8, 'SETEMBRO': 9,
            'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12
        }

        boletos_importados = 0
        boletos_sem_cliente = 0
        boletos_erros = 0

        for pdf_file in pdfs:
            try:
                # Extrair informações do nome: NOME_CLIENTE_MES.pdf
                nome_arquivo = pdf_file.stem
                partes = nome_arquivo.split('_')

                if len(partes) < 2:
                    logger.warning(f"   ⚠️ Nome de arquivo inválido: {pdf_file.name}")
                    boletos_erros += 1
                    continue

                mes_str = partes[-1].upper()
                nome_cliente = '_'.join(partes[:-1])
                nome_cliente_formatado = nome_cliente.replace('_', ' ').title()

                mes_num = meses.get(mes_str, datetime.now().month)
                ano = datetime.now().year

                # Buscar cliente no banco
                cur.execute("""
                    SELECT id, cpf, nome_completo
                    FROM clientes_finais
                    WHERE UPPER(REPLACE(nome_completo, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
                    LIMIT 1
                """, (nome_cliente_formatado,))

                cliente = cur.fetchone()

                if not cliente:
                    logger.warning(f"   ⚠️ Cliente não encontrado: {nome_cliente_formatado}")
                    boletos_sem_cliente += 1
                    continue

                cliente_id = cliente[0]

                # Verificar se boleto já existe para este cliente e mês
                boleto_existente = cur.execute("""
                    SELECT id FROM boletos
                    WHERE cliente_final_id = %s
                    AND mes_referencia = %s
                    AND ano_referencia = %s
                """, (cliente_id, mes_num, ano))

                if cur.fetchone():
                    logger.info(f"   ℹ️  Boleto já existe para {pdf_file.name} - pulando")
                    boletos_duplicados = boletos_duplicados + 1 if 'boletos_duplicados' in locals() else 1
                    continue

                # Dados do boleto
                data_vencimento = datetime(ano, mes_num, 10).date()  # Dia 10 do mês
                numero_boleto = f"BOL-{cliente_id}-{mes_num:02d}{ano}"

                # Inserir boleto
                cur.execute("""
                    INSERT INTO boletos (
                        cliente_final_id, cliente_nexus_id, numero_boleto, valor_original,
                        data_vencimento, data_emissao, mes_referencia, ano_referencia,
                        numero_parcela, descricao, status, status_envio,
                        pdf_filename, pdf_path, pdf_size, gerado_por,
                        created_at, updated_at
                    ) VALUES (
                        %s, 1, %s, 0.0, %s, %s, %s, %s,
                        1, %s, 'pendente', 'nao_enviado',
                        %s, %s, %s, 'automacao_canopus',
                        NOW(), NOW()
                    )
                    RETURNING id
                """, (
                    cliente_id, numero_boleto, data_vencimento, datetime.now().date(),
                    mes_num, ano, f"Boleto {mes_str}/{ano}",
                    pdf_file.name, str(pdf_file), pdf_file.stat().st_size
                ))

                boleto_id = cur.fetchone()[0]
                boletos_importados += 1

            except Exception as e:
                logger.error(f"   ❌ Erro ao importar boleto {pdf_file.name}: {e}")
                boletos_erros += 1
                continue

        conn.commit()
        logger.info(f"   ✓ {boletos_importados} boletos importados")
        logger.info(f"   ⚠️ {boletos_sem_cliente} boletos sem cliente correspondente")
        logger.info(f"   ❌ {boletos_erros} erros")

        cur.close()
        conn.close()

        # ==================================================
        # 4. RETORNAR RESULTADO
        # ==================================================
        return jsonify({
            'success': True,
            'message': 'Dados reimportados com sucesso!',
            'dados_antigos': {
                'clientes_deletados': clientes_deletados,
                'boletos_deletados': boletos_deletados
            },
            'dados_novos': {
                'clientes_importados': clientes_importados,
                'clientes_erros': clientes_erros,
                'boletos_importados': boletos_importados,
                'boletos_sem_cliente': boletos_sem_cliente,
                'boletos_erros': boletos_erros
            }
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"❌ Erro na reimportação: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# GESTÃO DE PLANILHAS DO GOOGLE DRIVE
# ============================================================================

@automation_canopus_bp.route('/consultores-planilhas', methods=['GET'])
@handle_errors
def listar_consultores_planilhas():
    """Lista todos os consultores com suas configurações de planilhas"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    nome,
                    email,
                    empresa,
                    ponto_venda,
                    link_planilha_drive,
                    ultima_atualizacao_planilha,
                    ativo
                FROM consultores
                ORDER BY nome
            """)

            consultores = cur.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'consultores': consultores
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar consultores: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@automation_canopus_bp.route('/consultor/<int:consultor_id>/configurar-planilha', methods=['POST'])
@handle_errors
def configurar_planilha_consultor(consultor_id):
    """Configura o link do Google Drive para a planilha de um consultor"""
    try:
        data = request.get_json()
        link_drive = data.get('link_drive', '').strip()

        if not link_drive:
            return jsonify({
                'success': False,
                'error': 'Link do Google Drive é obrigatório'
            }), 400

        # Verificar se consultor existe
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT nome FROM consultores WHERE id = %s", (consultor_id,))
            consultor = cur.fetchone()

            if not consultor:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Consultor não encontrado'
                }), 404

            # Atualizar link da planilha
            cur.execute("""
                UPDATE consultores
                SET link_planilha_drive = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (link_drive, consultor_id))

            conn.commit()

        conn.close()

        logger.info(f"✅ Link da planilha configurado para consultor {consultor['nome']}")

        return jsonify({
            'success': True,
            'message': f'Link configurado com sucesso para {consultor["nome"]}'
        })

    except Exception as e:
        logger.error(f"Erro ao configurar planilha: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@automation_canopus_bp.route('/consultor/<int:consultor_id>/atualizar-planilha', methods=['POST'])
@handle_errors
def atualizar_planilha_consultor(consultor_id):
    """Baixa/atualiza a planilha do Google Drive para um consultor"""
    try:
        # Importar serviço de download
        sys.path.insert(0, str(backend_path))
        from services.drive_downloader import baixar_planilha_consultor

        # Buscar dados do consultor
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, nome, link_planilha_drive
                FROM consultores
                WHERE id = %s
            """, (consultor_id,))

            consultor = cur.fetchone()

        if not consultor:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Consultor não encontrado'
            }), 404

        if not consultor['link_planilha_drive']:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Consultor {consultor["nome"]} não tem link do Google Drive configurado'
            }), 400

        logger.info(f"📥 Iniciando atualização da planilha: {consultor['nome']}")

        # Fazer download da planilha
        resultado = baixar_planilha_consultor(
            link_drive=consultor['link_planilha_drive'],
            nome_consultor=consultor['nome'],
            substituir=True  # Sempre substituir a planilha existente
        )

        if not resultado['sucesso']:
            return jsonify({
                'success': False,
                'error': resultado.get('erro', 'Erro desconhecido ao baixar planilha')
            }), 500

        # Atualizar data da última atualização
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE consultores
                SET ultima_atualizacao_planilha = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (consultor_id,))
            conn.commit()

        conn.close()

        logger.info(f"✅ Planilha atualizada com sucesso: {consultor['nome']}")

        return jsonify({
            'success': True,
            'message': 'Planilha atualizada com sucesso!',
            'data': {
                'consultor': consultor['nome'],
                'arquivo': resultado['arquivo_nome'],
                'tamanho': resultado['tamanho'],
                'caminho': resultado['arquivo_path']
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar planilha: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@automation_canopus_bp.route('/atualizar-todas-planilhas', methods=['POST'])
@handle_errors
def atualizar_todas_planilhas():
    """Atualiza as planilhas de todos os consultores que têm link configurado"""
    try:
        # Importar serviço de download
        sys.path.insert(0, str(backend_path))
        from services.drive_downloader import baixar_planilha_consultor

        # Buscar todos os consultores com link configurado
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, nome, link_planilha_drive
                FROM consultores
                WHERE link_planilha_drive IS NOT NULL
                  AND link_planilha_drive != ''
                  AND ativo = TRUE
                ORDER BY nome
            """)

            consultores = cur.fetchall()

        if not consultores:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Nenhum consultor com planilha configurada'
            }), 404

        logger.info(f"📥 Atualizando planilhas de {len(consultores)} consultor(es)...")

        sucessos = 0
        falhas = 0
        resultados = []

        for consultor in consultores:
            try:
                logger.info(f"   Processando: {consultor['nome']}")

                # Fazer download
                resultado = baixar_planilha_consultor(
                    link_drive=consultor['link_planilha_drive'],
                    nome_consultor=consultor['nome'],
                    substituir=True
                )

                if resultado['sucesso']:
                    # Atualizar data
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE consultores
                            SET ultima_atualizacao_planilha = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (consultor['id'],))
                        conn.commit()

                    sucessos += 1
                    resultados.append({
                        'consultor': consultor['nome'],
                        'status': 'sucesso',
                        'arquivo': resultado['arquivo_nome']
                    })
                    logger.info(f"   ✅ {consultor['nome']}: OK")
                else:
                    falhas += 1
                    resultados.append({
                        'consultor': consultor['nome'],
                        'status': 'erro',
                        'erro': resultado.get('erro', 'Erro desconhecido')
                    })
                    logger.error(f"   ❌ {consultor['nome']}: ERRO")

            except Exception as e:
                falhas += 1
                resultados.append({
                    'consultor': consultor['nome'],
                    'status': 'erro',
                    'erro': str(e)
                })
                logger.error(f"   ❌ {consultor['nome']}: EXCEÇÃO - {e}")

        conn.close()

        logger.info(f"✅ Atualização concluída: {sucessos} sucessos, {falhas} falhas")

        return jsonify({
            'success': True,
            'message': f'Atualização concluída: {sucessos} sucessos, {falhas} falhas',
            'data': {
                'total': len(consultores),
                'sucessos': sucessos,
                'falhas': falhas,
                'resultados': resultados
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar planilhas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == "__main__":
    print("=" * 80)
    print("ROTAS DE AUTOMAÇÃO CANOPUS")
    print("=" * 80)
    print("\nRotas disponíveis:")
    print("\nConsultores:")
    print("  GET    /api/automation/consultores")
    print("  POST   /api/automation/consultores")
    print("  PUT    /api/automation/consultores/<id>")
    print("  DELETE /api/automation/consultores/<id>")
    print("\nImportação:")
    print("  POST   /api/automation/importar-planilhas")
    print("  GET    /api/automation/clientes-staging")
    print("  POST   /api/automation/sincronizar-clientes")
    print("\nDownloads:")
    print("  POST   /api/automation/processar-downloads")
    print("  POST   /api/automation/importar-boletos-crm")
    print("\nExecuções:")
    print("  GET    /api/automation/execucoes")
    print("  GET    /api/automation/execucoes/<id>")
    print("\nEstatísticas:")
    print("  GET    /api/automation/estatisticas")
    print("\nHealth:")
    print("  GET    /api/automation/health")
    print("\nReset:")
    print("  POST   /api/automation/resetar-e-reimportar")
    print("\n" + "=" * 80)
