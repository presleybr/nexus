"""
Rotas do Portal Consórcio
Sistema Nexus CRM - Gestão de Consórcios
"""

from flask import Blueprint, request, jsonify, session, render_template, send_file
from functools import wraps
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import bcrypt
import logging
import os

from models.database import db
from services.boleto_generator import boleto_generator

logger = logging.getLogger(__name__)

# Blueprint
portal_bp = Blueprint('portal', __name__, url_prefix='/portal-consorcio')


# ============================================
# DECORADORES
# ============================================

def login_required_portal(f):
    """Decorator para verificar login no Portal"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'portal_user_id' not in session:
            return jsonify({'error': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@portal_bp.route('/login', methods=['GET'])
def login_page():
    """Página de login do Portal"""
    return render_template('portal-consorcio/login.html')


@portal_bp.route('/api/login', methods=['POST'])
def login():
    """Login no Portal Consórcio"""
    try:
        data = request.get_json()
        email = data.get('email')
        senha = data.get('senha')

        if not email or not senha:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400

        # Buscar usuário
        usuario = db.execute_query(
            "SELECT * FROM usuarios_portal WHERE email = %s AND ativo = true",
            (email,)
        )

        if not usuario:
            return jsonify({'error': 'Credenciais inválidas'}), 401

        usuario = usuario[0]

        # Verificar senha
        if not bcrypt.checkpw(senha.encode('utf-8'), usuario['senha'].encode('utf-8')):
            return jsonify({'error': 'Credenciais inválidas'}), 401

        # Criar sessão
        session['portal_user_id'] = usuario['id']
        session['portal_user_nome'] = usuario['nome_completo']
        session['portal_user_nivel'] = usuario['nivel_acesso']

        # Atualizar último acesso
        db.execute_update(
            "UPDATE usuarios_portal SET ultimo_acesso = %s WHERE id = %s",
            (datetime.now(), usuario['id'])
        )

        logger.info(f"[PORTAL] Login bem-sucedido: {usuario['nome_completo']}")

        return jsonify({
            'success': True,
            'usuario': {
                'id': usuario['id'],
                'nome': usuario['nome_completo'],
                'email': usuario['email'],
                'nivel_acesso': usuario['nivel_acesso']
            }
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro no login: {str(e)}")
        return jsonify({'error': 'Erro ao fazer login'}), 500


@portal_bp.route('/api/logout', methods=['POST'])
def logout():
    """Logout do Portal"""
    session.pop('portal_user_id', None)
    session.pop('portal_user_nome', None)
    session.pop('portal_user_nivel', None)
    return jsonify({'success': True})


# ============================================
# DASHBOARD
# ============================================

@portal_bp.route('/dashboard', methods=['GET'])
@login_required_portal
def dashboard_page():
    """Página do Dashboard"""
    return render_template('portal-consorcio/dashboard.html')


@portal_bp.route('/api/dashboard/stats', methods=['GET'])
@login_required_portal
def dashboard_stats():
    """Estatísticas do Dashboard"""
    try:
        # Total de clientes
        total_clientes = db.execute_query(
            "SELECT COUNT(*) as total FROM clientes_finais WHERE ativo = true"
        )[0]['total']

        # Total de contratos ativos
        contratos_ativos = db.execute_query(
            "SELECT COUNT(*) as total FROM clientes_finais WHERE status_contrato = 'ativo' AND ativo = true"
        )[0]['total']

        # Total de boletos pendentes
        boletos_pendentes = db.execute_query(
            "SELECT COUNT(*) as total FROM boletos WHERE status = 'pendente'"
        )[0]['total']

        # Boletos vencendo nos próximos 7 dias
        data_limite = date.today() + timedelta(days=7)
        boletos_vencendo = db.execute_query(
            "SELECT COUNT(*) as total FROM boletos WHERE status = 'pendente' AND data_vencimento <= %s AND data_vencimento >= %s",
            (data_limite, date.today())
        )[0]['total']

        # Valor total em crédito
        valor_total_credito = db.execute_query(
            "SELECT COALESCE(SUM(valor_credito), 0) as total FROM clientes_finais WHERE status_contrato = 'ativo' AND ativo = true"
        )[0]['total']

        # Últimos clientes cadastrados
        ultimos_clientes = db.execute_query("""
            SELECT id, nome_completo, cpf, numero_contrato, valor_credito, created_at
            FROM clientes_finais
            WHERE ativo = true
            ORDER BY created_at DESC
            LIMIT 5
        """)

        # Próximos boletos a vencer
        proximos_boletos = db.execute_query("""
            SELECT b.id, b.numero_boleto, b.valor_original, b.data_vencimento,
                   cf.nome_completo, cf.numero_contrato
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.status = 'pendente' AND b.data_vencimento >= %s
            ORDER BY b.data_vencimento ASC
            LIMIT 10
        """, (date.today(),))

        return jsonify({
            'success': True,
            'stats': {
                'total_clientes': total_clientes,
                'contratos_ativos': contratos_ativos,
                'boletos_pendentes': boletos_pendentes,
                'boletos_vencendo': boletos_vencendo,
                'valor_total_credito': float(valor_total_credito)
            },
            'ultimos_clientes': ultimos_clientes,
            'proximos_boletos': proximos_boletos
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao buscar stats: {str(e)}")
        return jsonify({'error': 'Erro ao buscar estatísticas'}), 500


# ============================================
# CLIENTES FINAIS
# ============================================

@portal_bp.route('/clientes', methods=['GET'])
@login_required_portal
def clientes_page():
    """Página de Clientes Finais"""
    return render_template('portal-consorcio/clientes.html')


@portal_bp.route('/api/clientes', methods=['GET'])
@login_required_portal
def listar_clientes():
    """Listar todos os clientes finais"""
    try:
        clientes = db.execute_query("""
            SELECT cf.*, cn.nome_fantasia as cliente_nexus_nome
            FROM clientes_finais cf
            LEFT JOIN clientes_nexus cn ON cf.cliente_nexus_id = cn.id
            WHERE cf.ativo = true
            ORDER BY cf.created_at DESC
        """)

        return jsonify({
            'success': True,
            'clientes': clientes
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao listar clientes: {str(e)}")
        return jsonify({'error': 'Erro ao listar clientes'}), 500


@portal_bp.route('/api/clientes/<int:cliente_id>', methods=['GET'])
@login_required_portal
def obter_cliente(cliente_id):
    """Obter dados de um cliente específico"""
    try:
        cliente = db.execute_query(
            "SELECT * FROM clientes_finais WHERE id = %s",
            (cliente_id,)
        )

        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        return jsonify({
            'success': True,
            'cliente': cliente[0]
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao obter cliente: {str(e)}")
        return jsonify({'error': 'Erro ao obter cliente'}), 500


@portal_bp.route('/api/clientes', methods=['POST'])
@login_required_portal
def criar_cliente():
    """Criar novo cliente final"""
    try:
        data = request.get_json()

        # Validar campos obrigatórios
        campos_obrigatorios = [
            'nome_completo', 'cpf', 'telefone_celular', 'whatsapp',
            'numero_contrato', 'grupo_consorcio', 'cota_consorcio',
            'valor_credito', 'valor_parcela', 'prazo_meses', 'data_adesao'
        ]

        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'error': f'Campo {campo} é obrigatório'}), 400

        # Verificar se CPF já existe
        cpf_existente = db.execute_query(
            "SELECT id FROM clientes_finais WHERE cpf = %s",
            (data['cpf'],)
        )

        if cpf_existente:
            return jsonify({'error': 'CPF já cadastrado'}), 400

        # Verificar se número de contrato já existe
        contrato_existente = db.execute_query(
            "SELECT id FROM clientes_finais WHERE numero_contrato = %s",
            (data['numero_contrato'],)
        )

        if contrato_existente:
            return jsonify({'error': 'Número de contrato já cadastrado'}), 400

        # Cliente Nexus padrão (ID 2)
        cliente_nexus_id = data.get('cliente_nexus_id', 2)

        # Calcular parcelas pendentes
        parcelas_pagas = data.get('parcelas_pagas', 0)
        parcelas_pendentes = data['prazo_meses'] - parcelas_pagas

        # Inserir cliente
        resultado = db.execute_query("""
            INSERT INTO clientes_finais (
                cliente_nexus_id, nome_completo, cpf, rg, data_nascimento,
                email, telefone_fixo, telefone_celular, whatsapp,
                cep, logradouro, numero, complemento, bairro, cidade, estado,
                numero_contrato, grupo_consorcio, cota_consorcio,
                valor_credito, valor_parcela, prazo_meses,
                parcelas_pagas, parcelas_pendentes, data_adesao,
                status_contrato, origem, cadastrado_por, observacoes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            cliente_nexus_id,
            data['nome_completo'], data['cpf'], data.get('rg'), data.get('data_nascimento'),
            data.get('email'), data.get('telefone_fixo'), data['telefone_celular'], data['whatsapp'],
            data.get('cep'), data.get('logradouro'), data.get('numero'), data.get('complemento'),
            data.get('bairro'), data.get('cidade'), data.get('estado'),
            data['numero_contrato'], data['grupo_consorcio'], data['cota_consorcio'],
            data['valor_credito'], data['valor_parcela'], data['prazo_meses'],
            parcelas_pagas, parcelas_pendentes, data['data_adesao'],
            data.get('status_contrato', 'ativo'), data.get('origem', 'portal'),
            session.get('portal_user_nome', 'Admin'), data.get('observacoes')
        ))

        cliente_id = resultado[0]['id']

        logger.info(f"[PORTAL] Cliente criado: {data['nome_completo']} (ID: {cliente_id})")

        return jsonify({
            'success': True,
            'cliente_id': cliente_id,
            'message': 'Cliente cadastrado com sucesso'
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao criar cliente: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao cadastrar cliente'}), 500


@portal_bp.route('/api/clientes/<int:cliente_id>', methods=['PUT'])
@login_required_portal
def atualizar_cliente(cliente_id):
    """Atualizar dados de um cliente"""
    try:
        data = request.get_json()

        # Verificar se cliente existe
        cliente = db.execute_query(
            "SELECT id FROM clientes_finais WHERE id = %s",
            (cliente_id,)
        )

        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        # Recalcular parcelas pendentes se prazo_meses ou parcelas_pagas mudou
        if 'prazo_meses' in data or 'parcelas_pagas' in data:
            cliente_atual = db.execute_query(
                "SELECT prazo_meses, parcelas_pagas FROM clientes_finais WHERE id = %s",
                (cliente_id,)
            )[0]

            prazo_meses = data.get('prazo_meses', cliente_atual['prazo_meses'])
            parcelas_pagas = data.get('parcelas_pagas', cliente_atual['parcelas_pagas'])
            data['parcelas_pendentes'] = prazo_meses - parcelas_pagas

        # Construir query dinamicamente
        campos_permitidos = [
            'nome_completo', 'cpf', 'rg', 'data_nascimento', 'email',
            'telefone_fixo', 'telefone_celular', 'whatsapp',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado',
            'valor_credito', 'valor_parcela', 'prazo_meses',
            'parcelas_pagas', 'parcelas_pendentes', 'status_contrato', 'observacoes'
        ]

        campos_update = []
        valores = []

        for campo in campos_permitidos:
            if campo in data:
                campos_update.append(f"{campo} = %s")
                valores.append(data[campo])

        if not campos_update:
            return jsonify({'error': 'Nenhum campo para atualizar'}), 400

        valores.append(cliente_id)
        query = f"UPDATE clientes_finais SET {', '.join(campos_update)} WHERE id = %s"

        db.execute_update(query, tuple(valores))

        logger.info(f"[PORTAL] Cliente atualizado: ID {cliente_id}")

        return jsonify({
            'success': True,
            'message': 'Cliente atualizado com sucesso'
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao atualizar cliente: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar cliente'}), 500


@portal_bp.route('/api/clientes/<int:cliente_id>', methods=['DELETE'])
@login_required_portal
def deletar_cliente(cliente_id):
    """Deletar (desativar) um cliente"""
    try:
        # Soft delete
        db.execute_update(
            "UPDATE clientes_finais SET ativo = false WHERE id = %s",
            (cliente_id,)
        )

        logger.info(f"[PORTAL] Cliente desativado: ID {cliente_id}")

        return jsonify({
            'success': True,
            'message': 'Cliente desativado com sucesso'
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao deletar cliente: {str(e)}")
        return jsonify({'error': 'Erro ao deletar cliente'}), 500


# ============================================
# BOLETOS
# ============================================

@portal_bp.route('/boletos', methods=['GET'])
@login_required_portal
def boletos_page():
    """Página de Boletos"""
    return render_template('portal-consorcio/boletos.html')


@portal_bp.route('/boletos-modelo', methods=['GET'])
@login_required_portal
def boletos_modelo_page():
    """Página de Boletos Modelo"""
    return render_template('portal-consorcio/boletos-modelo.html')


@portal_bp.route('/api/boletos', methods=['GET'])
@login_required_portal
def listar_boletos():
    """Listar todos os boletos"""
    try:
        boletos = db.execute_query("""
            SELECT b.*, cf.nome_completo, cf.cpf, cf.numero_contrato
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            ORDER BY b.data_vencimento DESC
        """)

        return jsonify({
            'success': True,
            'boletos': boletos
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao listar boletos: {str(e)}")
        return jsonify({'error': 'Erro ao listar boletos'}), 500


@portal_bp.route('/api/boletos/gerar', methods=['POST'])
@login_required_portal
def gerar_boleto():
    """Gerar boleto individual"""
    try:
        data = request.get_json()

        cliente_final_id = data.get('cliente_final_id')
        numero_parcela = data.get('numero_parcela')
        data_vencimento_str = data.get('data_vencimento')
        valor = data.get('valor')

        # Validações
        if not all([cliente_final_id, numero_parcela, data_vencimento_str]):
            return jsonify({'error': 'Dados incompletos'}), 400

        # Buscar cliente
        cliente = db.execute_query(
            "SELECT * FROM clientes_finais WHERE id = %s AND ativo = true",
            (cliente_final_id,)
        )

        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        cliente = cliente[0]

        # Usar valor da parcela do cliente se não informado
        if not valor:
            valor = float(cliente['valor_parcela'])

        # Converter data
        data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()

        # Gerar PDF
        resultado_pdf = boleto_generator.gerar_boleto_pdf(
            cliente_final=cliente,
            valor=valor,
            data_vencimento=data_vencimento,
            numero_parcela=numero_parcela
        )

        if not resultado_pdf['success']:
            return jsonify({'error': resultado_pdf.get('error', 'Erro ao gerar PDF')}), 500

        # Calcular mês/ano de referência
        mes_ref = data_vencimento.month
        ano_ref = data_vencimento.year

        # Inserir boleto no banco
        resultado_db = db.execute_query("""
            INSERT INTO boletos (
                cliente_nexus_id, cliente_final_id, numero_boleto,
                linha_digitavel, codigo_barras, nosso_numero,
                valor_original, valor_atualizado, data_vencimento, data_emissao,
                mes_referencia, ano_referencia, numero_parcela,
                descricao, status, status_envio,
                pdf_filename, pdf_path, pdf_size, gerado_por
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            cliente['cliente_nexus_id'], cliente_final_id,
            resultado_pdf['nosso_numero'],
            resultado_pdf['linha_digitavel'], resultado_pdf['codigo_barras'],
            resultado_pdf['nosso_numero'],
            valor, valor, data_vencimento, date.today(),
            mes_ref, ano_ref, numero_parcela,
            f"Parcela {numero_parcela}/{cliente['prazo_meses']}",
            'pendente', 'nao_enviado',
            resultado_pdf['filename'], resultado_pdf['filepath'],
            resultado_pdf['file_size'], 'portal'
        ))

        boleto_id = resultado_db[0]['id']

        logger.info(f"[PORTAL] Boleto gerado: ID {boleto_id} - Cliente {cliente['nome_completo']}")

        return jsonify({
            'success': True,
            'boleto_id': boleto_id,
            'filename': resultado_pdf['filename'],
            'message': 'Boleto gerado com sucesso'
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao gerar boleto: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao gerar boleto'}), 500


@portal_bp.route('/api/boletos/gerar-lote', methods=['POST'])
@login_required_portal
def gerar_boletos_lote():
    """Gerar boletos em lote para um cliente"""
    try:
        data = request.get_json()

        cliente_final_id = data.get('cliente_final_id')
        quantidade_parcelas = data.get('quantidade_parcelas', 12)
        data_primeira_parcela_str = data.get('data_primeira_parcela')
        parcela_inicial = data.get('parcela_inicial', 1)

        # Validações
        if not all([cliente_final_id, data_primeira_parcela_str]):
            return jsonify({'error': 'Dados incompletos'}), 400

        # Buscar cliente
        cliente = db.execute_query(
            "SELECT * FROM clientes_finais WHERE id = %s AND ativo = true",
            (cliente_final_id,)
        )

        if not cliente:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        cliente = cliente[0]
        valor_parcela = float(cliente['valor_parcela'])

        # Converter data
        data_vencimento = datetime.strptime(data_primeira_parcela_str, '%Y-%m-%d').date()

        boletos_gerados = []
        erros = []

        # Gerar boletos
        for i in range(quantidade_parcelas):
            numero_parcela = parcela_inicial + i

            # Verificar se parcela já existe
            boleto_existente = db.execute_query(
                "SELECT id FROM boletos WHERE cliente_final_id = %s AND numero_parcela = %s",
                (cliente_final_id, numero_parcela)
            )

            if boleto_existente:
                erros.append(f"Parcela {numero_parcela} já existe")
                continue

            # Gerar PDF
            resultado_pdf = boleto_generator.gerar_boleto_pdf(
                cliente_final=cliente,
                valor=valor_parcela,
                data_vencimento=data_vencimento,
                numero_parcela=numero_parcela
            )

            if not resultado_pdf['success']:
                erros.append(f"Erro ao gerar PDF parcela {numero_parcela}")
                continue

            # Inserir no banco
            mes_ref = data_vencimento.month
            ano_ref = data_vencimento.year

            resultado_db = db.execute_query("""
                INSERT INTO boletos (
                    cliente_nexus_id, cliente_final_id, numero_boleto,
                    linha_digitavel, codigo_barras, nosso_numero,
                    valor_original, valor_atualizado, data_vencimento, data_emissao,
                    mes_referencia, ano_referencia, numero_parcela,
                    descricao, status, status_envio,
                    pdf_filename, pdf_path, pdf_size, gerado_por
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                cliente['cliente_nexus_id'], cliente_final_id,
                resultado_pdf['nosso_numero'],
                resultado_pdf['linha_digitavel'], resultado_pdf['codigo_barras'],
                resultado_pdf['nosso_numero'],
                valor_parcela, valor_parcela, data_vencimento, date.today(),
                mes_ref, ano_ref, numero_parcela,
                f"Parcela {numero_parcela}/{cliente['prazo_meses']}",
                'pendente', 'nao_enviado',
                resultado_pdf['filename'], resultado_pdf['filepath'],
                resultado_pdf['file_size'], 'portal'
            ))

            boletos_gerados.append({
                'boleto_id': resultado_db[0]['id'],
                'numero_parcela': numero_parcela,
                'data_vencimento': data_vencimento.strftime('%d/%m/%Y'),
                'filename': resultado_pdf['filename']
            })

            # Próximo vencimento (1 mês depois)
            data_vencimento = data_vencimento + relativedelta(months=1)

        logger.info(f"[PORTAL] Lote gerado: {len(boletos_gerados)} boletos - Cliente {cliente['nome_completo']}")

        return jsonify({
            'success': True,
            'boletos_gerados': len(boletos_gerados),
            'boletos': boletos_gerados,
            'erros': erros
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao gerar lote: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao gerar lote de boletos'}), 500


@portal_bp.route('/api/boletos/<int:boleto_id>/download', methods=['GET'])
@login_required_portal
def download_boleto(boleto_id):
    """Download de PDF do boleto"""
    try:
        # Buscar boleto
        boleto = db.execute_query(
            "SELECT * FROM boletos WHERE id = %s",
            (boleto_id,)
        )

        if not boleto:
            return jsonify({'error': 'Boleto não encontrado'}), 404

        boleto = boleto[0]

        # Construir caminho absoluto
        pdf_path = boleto['pdf_path']
        if not os.path.isabs(pdf_path):
            # Se for caminho relativo, construir absoluto a partir do diretório raiz
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_path = os.path.join(base_dir, pdf_path)

        if not os.path.exists(pdf_path):
            logger.error(f"[PORTAL] Arquivo não encontrado: {pdf_path}")
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=boleto['pdf_filename']
        )

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao fazer download: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao fazer download'}), 500


@portal_bp.route('/api/boletos/<int:boleto_id>/visualizar', methods=['GET'])
@login_required_portal
def visualizar_boleto(boleto_id):
    """Visualizar PDF do boleto inline no navegador"""
    try:
        # Buscar boleto
        boleto = db.execute_query(
            "SELECT * FROM boletos WHERE id = %s",
            (boleto_id,)
        )

        if not boleto:
            return jsonify({'error': 'Boleto não encontrado'}), 404

        boleto = boleto[0]

        # Construir caminho absoluto
        pdf_path = boleto['pdf_path']
        if not os.path.isabs(pdf_path):
            # Se for caminho relativo, construir absoluto a partir do diretório raiz
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_path = os.path.join(base_dir, pdf_path)

        if not os.path.exists(pdf_path):
            logger.error(f"[PORTAL] Arquivo não encontrado: {pdf_path}")
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        # Retornar PDF para visualização inline (não download)
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False  # Inline, não download
        )

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao visualizar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao visualizar PDF'}), 500


@portal_bp.route('/api/boletos/<int:boleto_id>/enviar-whatsapp', methods=['POST'])
@login_required_portal
def enviar_boleto_whatsapp(boleto_id):
    """Envia boleto por WhatsApp"""
    try:
        # Buscar boleto com dados do cliente
        boleto = db.execute_query("""
            SELECT b.*, cf.nome_completo, cf.whatsapp, cf.numero_contrato
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.id = %s
        """, (boleto_id,))

        if not boleto:
            return jsonify({'error': 'Boleto não encontrado'}), 404

        boleto = boleto[0]

        # Verificar se tem WhatsApp
        if not boleto['whatsapp']:
            return jsonify({'error': 'Cliente não possui WhatsApp cadastrado'}), 400

        # Verificar se PDF existe
        if not boleto['pdf_path'] or not os.path.exists(boleto['pdf_path']):
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        # Preparar mensagem
        mensagem = f"""Olá *{boleto['nome_completo']}*!

Segue em anexo o boleto referente à parcela {boleto['numero_parcela']} do seu consórcio.

📄 *Contrato:* {boleto['numero_contrato']}
💰 *Valor:* R$ {float(boleto['valor_original']):.2f}
📅 *Vencimento:* {boleto['data_vencimento'].strftime('%d/%m/%Y') if boleto['data_vencimento'] else 'N/A'}

Qualquer dúvida, estamos à disposição!

_Mensagem automática - Nexus CRM_"""

        # Enviar pelo WhatsApp Baileys
        import requests
        whatsapp_numero = boleto['whatsapp'].replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Enviar mensagem
        payload_msg = {
            'number': whatsapp_numero,
            'message': mensagem
        }

        response_msg = requests.post('http://localhost:3001/send-message', json=payload_msg, timeout=10)

        if not response_msg.ok:
            logger.error(f"[PORTAL] Erro ao enviar mensagem WhatsApp: {response_msg.text}")
            return jsonify({'error': 'Erro ao enviar mensagem WhatsApp'}), 500

        # Enviar PDF
        with open(boleto['pdf_path'], 'rb') as pdf_file:
            pdf_base64 = __import__('base64').b64encode(pdf_file.read()).decode('utf-8')

        payload_doc = {
            'number': whatsapp_numero,
            'document': pdf_base64,
            'filename': boleto['pdf_filename'],
            'caption': f"Boleto - Parcela {boleto['numero_parcela']}"
        }

        response_doc = requests.post('http://localhost:3001/send-document', json=payload_doc, timeout=30)

        if not response_doc.ok:
            logger.error(f"[PORTAL] Erro ao enviar documento WhatsApp: {response_doc.text}")
            return jsonify({'error': 'Erro ao enviar documento WhatsApp'}), 500

        # Atualizar status do boleto
        db.execute_update("""
            UPDATE boletos
            SET status_envio = 'enviado', data_envio = %s, enviado_por = %s
            WHERE id = %s
        """, (datetime.now(), session.get('portal_user_nome', 'Portal'), boleto_id))

        logger.info(f"[PORTAL] Boleto {boleto_id} enviado via WhatsApp para {whatsapp_numero}")

        return jsonify({
            'success': True,
            'message': 'Boleto enviado com sucesso via WhatsApp'
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao enviar boleto via WhatsApp: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao enviar boleto via WhatsApp'}), 500


@portal_bp.route('/api/boletos/enviar-modelo-massa', methods=['POST'])
@login_required_portal
def enviar_boleto_modelo_massa():
    """Envia boleto modelo para todos os clientes ativos via WhatsApp"""
    try:
        data = request.get_json()
        cliente_nexus_id = data.get('cliente_nexus_id')
        mensagem_personalizada = data.get('mensagem')

        if not cliente_nexus_id:
            return jsonify({'error': 'Cliente Nexus ID é obrigatório'}), 400

        # Importar serviço
        from services.boleto_modelo_service import boleto_modelo_service

        # Enviar para todos os clientes
        resultado = boleto_modelo_service.enviar_modelo_para_todos_clientes(
            cliente_nexus_id=cliente_nexus_id,
            mensagem_personalizada=mensagem_personalizada
        )

        if not resultado['success']:
            return jsonify({'error': resultado.get('error', 'Erro ao enviar boletos')}), 500

        logger.info(f"[PORTAL] Boleto modelo enviado para {resultado['total_enviados']} clientes")

        return jsonify({
            'success': True,
            'total_clientes': resultado['total_clientes'],
            'total_enviados': resultado['total_enviados'],
            'total_erros': resultado['total_erros'],
            'resultados': resultado['resultados']
        })

    except Exception as e:
        logger.error(f"[PORTAL] Erro ao enviar boleto modelo em massa: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao enviar boleto modelo'}), 500


# ============================================
# FUNÇÃO DE REGISTRO
# ============================================

def register_portal_routes(app):
    """Registrar blueprint do Portal Consórcio"""
    app.register_blueprint(portal_bp)
    logger.info("[PORTAL] Rotas do Portal Consórcio registradas")
