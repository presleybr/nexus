"""
Rotas de Automação Canopus
API REST para gerenciar automação de download de boletos
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import sys

# Configurar logger PRIMEIRO
logger = logging.getLogger(__name__)

# ESTRATÉGIA DE PATHS: Adicionar backend PRIMEIRO, depois canopus
# Isso garante que models.database funcione, e depois o orquestrador adiciona canopus em primeiro
backend_path = Path(__file__).resolve().parent.parent
automation_path = Path(__file__).resolve().parent.parent.parent / "automation" / "canopus"

# Backend primeiro (para Database funcionar)
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Canopus path (mas o orquestrador.py vai reorganizar internamente)
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
    """Retorna conexão com banco de dados"""
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(
        host='localhost',
        port=5434,
        dbname='nexus_crm',
        user='postgres',
        password='nexus2025',
        row_factory=dict_row
    )


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

        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'database': True,
                'canopus_disponivel': CANOPUS_DISPONIVEL,
                'diretorios': diretorios_ok if CANOPUS_DISPONIVEL else 'N/A'
            }
        })

    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
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
        cpfs = [c['cpf'] for c in clientes]

        logger.info(f"🎯 Iniciando downloads para {len(cpfs)} CPFs do PV {ponto_venda}")

        # Estatísticas compartilhadas
        stats = {
            'sucessos': 0,
            'erros': 0,
            'cpf_nao_encontrado': 0,
            'sem_boleto': 0,
            'total': len(cpfs),
            'processados': 0
        }

        # Função para processar em background
        def processar_downloads_background():
            logger.info("=" * 80)
            logger.info("🚀 THREAD DE DOWNLOAD INICIADA")
            logger.info(f"📊 Total de CPFs a processar: {len(cpfs)}")
            logger.info("=" * 80)

            async def processar_todos():
                logger.info("🔄 Função processar_todos() iniciada")
                from automation.canopus.canopus_automation import CanopusAutomation
                from pathlib import Path

                pasta_destino = Path(r'D:\Nexus\automation\canopus\downloads\Danner')
                pasta_destino.mkdir(parents=True, exist_ok=True)

                # Buscar credenciais do banco
                try:
                    logger.info("🔑 Buscando credenciais do PV 24627...")
                    from automation.canopus.orquestrador import DatabaseManager

                    with DatabaseManager() as db_manager:
                        logger.info("✅ DatabaseManager conectado")
                        credenciais = db_manager.obter_credenciais('24627')

                        if not credenciais:
                            logger.error("❌ Credenciais não encontradas para PV 24627")
                            logger.error("Execute: python automation/canopus/cadastrar_credencial.py")
                            return

                        usuario = credenciais['usuario']
                        senha = credenciais['senha']
                        codigo_empresa = credenciais.get('codigo_empresa', '0101')

                        logger.info(f"✅ Credenciais obtidas - Usuário: {usuario}, Código Empresa: {codigo_empresa}")
                        logger.info(f"🔐 Senha descriptografada: {'*' * len(senha)}")

                except Exception as e:
                    logger.error(f"❌ Erro ao buscar credenciais: {e}")
                    logger.exception("Traceback completo:")
                    return

                # Abrir navegador UMA VEZ
                logger.info("🌐 Abrindo Chromium...")
                async with CanopusAutomation(headless=False) as bot:
                    logger.info("✅ Chromium aberto!")

                    # Fazer login
                    logger.info("=" * 80)
                    logger.info("🔐 FAZENDO LOGIN NO PONTO 24627")
                    logger.info(f"👤 Usuário: {usuario}")
                    logger.info(f"🏢 Código Empresa: {codigo_empresa}")
                    logger.info("=" * 80)

                    login_ok = await bot.login(
                        usuario=usuario,
                        senha=senha,
                        codigo_empresa=codigo_empresa,
                        ponto_venda='24627'
                    )

                    if not login_ok:
                        logger.error("=" * 80)
                        logger.error("❌ FALHA NO LOGIN")
                        logger.error("=" * 80)
                        return

                    logger.info("=" * 80)
                    logger.info("✅ LOGIN REALIZADO COM SUCESSO!")
                    logger.info("=" * 80)

                    # Processar cada CPF na mesma sessão
                    for idx, cpf in enumerate(cpfs, 1):
                        logger.info(f"📄 Processando {idx}/{len(cpfs)}: CPF {cpf}")

                        try:
                            from automation.canopus.canopus_config import CanopusConfig

                            # VERIFICAR SE BOLETO JÁ EXISTE
                            # Buscar nome do cliente na planilha para gerar nome do arquivo esperado
                            import pandas as pd
                            planilha_path = Path("D:/Nexus/automation/canopus/excel_files")
                            planilhas = list(planilha_path.glob("*__PLANILHA_GERAL.xlsx"))
                            planilha_path = planilhas[0] if planilhas else None

                            nome_cliente = None
                            if planilha_path and planilha_path.exists():
                                try:
                                    df = pd.read_excel(planilha_path, sheet_name=0, header=11)
                                    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
                                    linha = df[df['Unnamed: 1'].astype(str).str.replace(r'\D', '', regex=True) == cpf_limpo]
                                    if not linha.empty:
                                        nome_cliente = linha.iloc[0]['Unnamed: 0']
                                        if pd.notna(nome_cliente):
                                            nome_cliente = str(nome_cliente).strip().upper().replace(' ', '_')
                                except Exception as e:
                                    logger.warning(f"Erro ao buscar cliente na planilha: {e}")

                            # Se encontrou o nome, verificar se arquivo já existe
                            if nome_cliente:
                                arquivo_esperado = pasta_destino / f"{nome_cliente}_{mes}.pdf"
                                if arquivo_esperado.exists():
                                    logger.info(f"⏭️ PULANDO: Boleto já existe - {arquivo_esperado.name}")
                                    stats['sucessos'] += 1  # Contar como sucesso (já tem o boleto)
                                    stats['processados'] += 1
                                    continue

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

                    logger.info("=" * 80)
                    logger.info("🎉 DOWNLOADS CONCLUÍDOS!")
                    logger.info("=" * 80)
                    logger.info(f"✅ Sucessos: {stats['sucessos']}")
                    logger.info(f"❌ Erros: {stats['erros']}")
                    logger.info(f"⚠️ CPF não encontrado: {stats['cpf_nao_encontrado']}")
                    logger.info(f"📄 Sem boleto: {stats['sem_boleto']}")
                    logger.info(f"📊 Total processados: {stats['processados']}/{stats['total']}")
                    logger.info("=" * 80)
                    logger.info("💾 Os boletos estão em: D:\\Nexus\\automation\\canopus\\downloads\\Danner")
                    logger.info("🔄 Use o botão 'Importar Boletos' no frontend para importar ao banco")
                    logger.info("=" * 80)

            # Rodar o loop assíncrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(processar_todos())
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
        return jsonify({
            'success': True,
            'message': f'Download iniciado em background para {len(clientes)} clientes do PV {ponto_venda}. O Chromium abrirá em alguns segundos.',
            'data': {
                'ponto_venda': ponto_venda,
                'total_clientes': len(clientes),
                'status': 'iniciado',
                'info': 'Acompanhe o progresso nos logs do terminal'
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
    Importa todos os PDFs da pasta Canopus para o banco de dados
    Lê cada PDF, extrai dados e cria clientes + boletos
    """
    import os
    from pathlib import Path
    from datetime import datetime

    logger.info("📥 Iniciando importação de boletos da pasta Canopus...")

    # Importar a função de extração de PDF
    sys.path.insert(0, str(backend_path))
    from services.pdf_extractor import extrair_dados_boleto

    pasta_canopus = Path(r'D:\Nexus\automation\canopus\downloads\Danner')
    cliente_nexus_id = 2  # ID da empresa Cred MS Consorcios

    if not pasta_canopus.exists():
        return jsonify({
            'success': False,
            'error': f'Pasta não encontrada: {pasta_canopus}'
        }), 404

    # Buscar todos os PDFs
    pdfs = [f for f in os.listdir(pasta_canopus) if f.endswith('.pdf')]

    if not pdfs:
        return jsonify({
            'success': False,
            'error': f'Nenhum PDF encontrado em: {pasta_canopus}'
        }), 404

    logger.info(f"📄 Encontrados {len(pdfs)} PDFs para processar")

    stats = {
        'total_pdfs': len(pdfs),
        'clientes_criados': 0,
        'clientes_existentes': 0,
        'boletos_criados': 0,
        'erros': 0,
        'pdfs_sem_dados': 0
    }

    # Processar cada PDF
    for idx, pdf_filename in enumerate(pdfs, 1):
        pdf_path = os.path.join(pasta_canopus, pdf_filename)
        conn = None

        logger.info(f"[{idx}/{len(pdfs)}] Processando: {pdf_filename[:50]}")

        try:
            # Extrair dados do PDF
            dados_pdf = extrair_dados_boleto(pdf_path)

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

                cur.execute("""
                    SELECT id FROM boletos
                    WHERE cliente_final_id = %s
                    AND mes_referencia = %s
                    AND ano_referencia = %s
                """, (cliente_id, mes_ref, ano_ref))

                boleto_existente = cur.fetchone()

                if boleto_existente:
                    logger.info(f"   ℹ️  Boleto já existe para este cliente/mês")
                    conn.commit()
                    conn.close()
                    continue

                # Criar boleto
                logger.info(f"   ➕ Criando boleto...")

                numero_boleto = contrato or f"CANOPUS-{cpf}-{mes_ref:02d}{ano_ref}"

                cur.execute("""
                    INSERT INTO boletos
                    (cliente_nexus_id, cliente_final_id, numero_boleto, valor_original,
                     data_vencimento, data_emissao, mes_referencia, ano_referencia,
                     numero_parcela, pdf_path, pdf_filename, status, status_envio, gerado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    pdf_path,
                    pdf_filename,
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
    Lista todos os boletos que já foram baixados (da pasta de downloads)
    AGORA com dados REAIS extraídos do PDF usando o extrator
    """
    import os
    from pathlib import Path
    from services.pdf_extractor import extrair_dados_boleto

    # Pasta de downloads (mesma usada na automação)
    downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

    if not downloads_dir.exists():
        return jsonify({
            'success': True,
            'data': [],
            'message': 'Pasta de downloads não encontrada'
        })

    boletos = []

    # Listar todos os PDFs
    for pdf_file in downloads_dir.glob("**/*.pdf"):
        try:
            stat = pdf_file.stat()

            # Extrair informações do nome do arquivo (fallback)
            nome_arquivo = pdf_file.stem
            partes = nome_arquivo.split('_')
            mes_nome_arquivo = partes[-1] if partes else 'DESCONHECIDO'
            cliente_nome_arquivo = '_'.join(partes[:-1]) if len(partes) > 1 else nome_arquivo

            # Tentar extrair dados REAIS do PDF usando o extrator
            dados_pdf = None
            try:
                dados_pdf = extrair_dados_boleto(str(pdf_file))
                logger.debug(f"✅ Dados extraídos do PDF: {pdf_file.name}")
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível extrair dados do PDF {pdf_file.name}: {e}")
                dados_pdf = None

            # Se conseguiu extrair dados, usa eles; senão usa fallback do nome
            if dados_pdf and dados_pdf.get('sucesso'):
                boleto_info = {
                    'arquivo_nome': pdf_file.name,
                    'caminho': str(pdf_file),
                    'cliente_nome': dados_pdf.get('nome_pagador', cliente_nome_arquivo.replace('_', ' ').title()),
                    'cpf': dados_pdf.get('cpf', 'N/A'),
                    'valor': dados_pdf.get('valor', 0),
                    'valor_str': dados_pdf.get('valor_str', 'R$ 0,00'),
                    'vencimento': dados_pdf.get('vencimento_str', 'N/A'),
                    'grupo_cota': dados_pdf.get('grupo_cota', 'N/A'),
                    'nosso_numero': dados_pdf.get('nosso_numero', 'N/A'),
                    'mes': dados_pdf.get('vencimento_str', mes_nome_arquivo.capitalize()).split('/')[1] if dados_pdf.get('vencimento_str') else mes_nome_arquivo.capitalize(),
                    'tamanho': stat.st_size,
                    'data_download': stat.st_mtime,
                    'status': 'processado',
                    'dados_extraidos': True
                }
            else:
                # Fallback: usa dados do nome do arquivo
                boleto_info = {
                    'arquivo_nome': pdf_file.name,
                    'caminho': str(pdf_file),
                    'cliente_nome': cliente_nome_arquivo.replace('_', ' ').title(),
                    'cpf': 'N/A',
                    'valor': 0,
                    'valor_str': 'N/A',
                    'vencimento': 'N/A',
                    'grupo_cota': 'N/A',
                    'nosso_numero': 'N/A',
                    'mes': mes_nome_arquivo.capitalize(),
                    'tamanho': stat.st_size,
                    'data_download': stat.st_mtime,
                    'status': 'baixado',
                    'dados_extraidos': False
                }

            boletos.append(boleto_info)

        except Exception as e:
            logger.error(f"Erro ao processar {pdf_file}: {e}")
            continue

    # Ordenar por data de download (mais recente primeiro)
    boletos.sort(key=lambda x: x['data_download'], reverse=True)

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
    Faz download de um boleto específico
    """
    # Pode receber nome do arquivo OU caminho completo
    nome_arquivo = request.args.get('nome')
    caminho = request.args.get('caminho')

    from pathlib import Path
    from flask import send_file

    # Pasta de downloads
    downloads_dir = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

    # Se veio nome do arquivo, construir caminho
    if nome_arquivo:
        arquivo = downloads_dir / nome_arquivo
    # Se veio caminho, usar diretamente
    elif caminho:
        arquivo = Path(caminho)
    else:
        return jsonify({'error': 'Nome do arquivo ou caminho não fornecido'}), 400

    # Verificar se arquivo existe
    if not arquivo.exists():
        logger.error(f"Arquivo não encontrado: {arquivo}")
        return jsonify({'error': f'Arquivo não encontrado: {arquivo.name}'}), 404

    # Verificar se arquivo está dentro da pasta permitida (segurança)
    try:
        arquivo.resolve().relative_to(downloads_dir.resolve())
    except ValueError:
        # Arquivo está fora da pasta permitida
        return jsonify({'error': 'Acesso negado'}), 403

    return send_file(
        arquivo,
        as_attachment=True,
        download_name=arquivo.name,
        mimetype='application/pdf'
    )


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

                # Verificar se boleto já existe
                cur.execute("""
                    SELECT id FROM boletos
                    WHERE cliente_final_id = %s AND mes_referencia = %s
                      AND ano_referencia = %s AND pdf_filename = %s
                """, (cliente_id, mes_num, ano, pdf_file.name))

                if cur.fetchone():
                    logger.debug(f"   ⏭️  Boleto já existe: {pdf_file.name}")
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
