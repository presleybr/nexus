"""
Rotas do CRM - Gerenciamento de clientes, boletos e dashboard
"""

from flask import Blueprint, request, jsonify, session, send_file
import sys
import os
from pathlib import Path
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ClienteNexus, ClienteFinal, Boleto, Configuracao, validar_cpf, validar_cnpj, log_sistema
from models.database import db
from routes.auth import login_required

crm_bp = Blueprint('crm', __name__, url_prefix='/api/crm')


# ============================================================================
# FUNÇÕES AUXILIARES PARA BUSCAR PDFS REAIS DA PASTA
# ============================================================================

def limpar_nome_para_busca(nome):
    """Remove caracteres especiais e normaliza nome para busca"""
    if not nome:
        return ""

    # Remover acentos
    replacements = {
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C',
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c'
    }

    nome_limpo = nome.upper()
    for old, new in replacements.items():
        nome_limpo = nome_limpo.replace(old, new)

    # Remover caracteres especiais, manter apenas letras, números e espaços
    nome_limpo = re.sub(r'[^A-Z0-9\s]', '', nome_limpo)

    return nome_limpo.strip()


def buscar_pdfs_cliente(nome_cliente):
    """Busca PDFs do cliente na pasta de downloads do Canopus"""

    # Caminho da pasta onde ficam os PDFs
    pasta_downloads = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

    if not pasta_downloads.exists():
        print(f"[AVISO] Pasta não encontrada: {pasta_downloads}")
        return []

    # Normalizar nome do cliente para busca
    nome_normalizado = limpar_nome_para_busca(nome_cliente)

    if not nome_normalizado:
        return []

    # Dividir nome em palavras
    palavras_cliente = nome_normalizado.split()

    # Buscar todos os PDFs
    pdfs_encontrados = []

    try:
        for arquivo in pasta_downloads.glob("*.pdf"):
            nome_arquivo = arquivo.stem  # Nome sem extensão
            nome_arquivo_normalizado = limpar_nome_para_busca(nome_arquivo)

            # Verificar se o nome do arquivo contém palavras significativas do nome do cliente
            # Ignora palavras muito curtas (como "DA", "DE", "DOS")
            palavras_significativas = [p for p in palavras_cliente if len(p) > 2]

            if not palavras_significativas:
                continue

            # Match se pelo menos 60% das palavras significativas estão no nome do arquivo
            matches = sum(1 for palavra in palavras_significativas if palavra in nome_arquivo_normalizado)
            percentual_match = matches / len(palavras_significativas)

            if percentual_match >= 0.6:  # 60% de match
                # Extrair mês/ano do nome do arquivo (geralmente última parte antes da extensão)
                partes = nome_arquivo.split('_')
                mes_ref = partes[-1] if partes else "Desconhecido"

                pdfs_encontrados.append({
                    'arquivo': arquivo.name,
                    'caminho_completo': str(arquivo),
                    'mes_referencia': mes_ref,
                    'tamanho': arquivo.stat().st_size,
                    'data_modificacao': arquivo.stat().st_mtime
                })

    except Exception as e:
        print(f"[ERRO] Erro ao buscar PDFs: {e}")
        return []

    # Ordenar por data de modificação (mais recente primeiro)
    pdfs_encontrados.sort(key=lambda x: x['data_modificacao'], reverse=True)

    return pdfs_encontrados


@crm_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """Retorna dados do dashboard do cliente - BUSCA DO PORTAL CONSÓRCIO"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Buscar estatísticas das tabelas do Portal Consórcio
        dashboard_data = db.execute_query("""
            SELECT
                %s as cliente_nexus_id,
                -- Clientes finais
                (SELECT COUNT(*) FROM clientes_finais
                 WHERE cliente_nexus_id = %s AND ativo = true) as total_clientes_finais,

                -- Boletos
                (SELECT COUNT(*) FROM boletos
                 WHERE cliente_nexus_id = %s) as total_boletos,

                (SELECT COUNT(*) FROM boletos
                 WHERE cliente_nexus_id = %s AND status_envio = 'enviado') as boletos_enviados,

                (SELECT COUNT(*) FROM boletos
                 WHERE cliente_nexus_id = %s AND status_envio = 'nao_enviado') as boletos_pendentes,

                (SELECT COUNT(*) FROM boletos
                 WHERE cliente_nexus_id = %s AND status = 'pago') as boletos_pagos,

                (SELECT COUNT(*) FROM boletos
                 WHERE cliente_nexus_id = %s AND status = 'pendente'
                 AND data_vencimento < CURRENT_DATE) as boletos_vencidos,

                -- Valores
                (SELECT COALESCE(SUM(valor_credito), 0) FROM clientes_finais
                 WHERE cliente_nexus_id = %s AND ativo = true) as valor_total_credito,

                (SELECT COALESCE(SUM(valor_original), 0) FROM boletos
                 WHERE cliente_nexus_id = %s AND status = 'pendente') as valor_total_pendente
        """, (cliente_nexus_id, cliente_nexus_id, cliente_nexus_id,
              cliente_nexus_id, cliente_nexus_id, cliente_nexus_id,
              cliente_nexus_id, cliente_nexus_id, cliente_nexus_id))

        if dashboard_data:
            dashboard_info = dashboard_data[0]
        else:
            # Dados vazios se não houver registros
            dashboard_info = {
                'cliente_nexus_id': cliente_nexus_id,
                'total_clientes_finais': 0,
                'total_boletos': 0,
                'boletos_enviados': 0,
                'boletos_pendentes': 0,
                'boletos_pagos': 0,
                'boletos_vencidos': 0,
                'valor_total_credito': 0,
                'valor_total_pendente': 0
            }

        return jsonify({
            'success': True,
            'dashboard': dashboard_info
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/clientes', methods=['GET'])
@login_required
def listar_clientes():
    """Lista clientes finais do cliente Nexus logado"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Parâmetros de paginação
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        filtro = request.args.get('filtro', '')

        if filtro:
            clientes = ClienteFinal.buscar_com_filtro(cliente_nexus_id, filtro)
        else:
            clientes = ClienteFinal.listar_por_cliente_nexus(cliente_nexus_id, limit, offset)

        total = ClienteFinal.contar_por_cliente_nexus(cliente_nexus_id)

        return jsonify({
            'clientes': clientes,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
@login_required
def get_cliente(cliente_id):
    """Retorna dados de um cliente específico"""
    try:
        cliente = ClienteFinal.buscar_por_id(cliente_id)

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Verifica se pertence ao cliente_nexus logado
        if cliente['cliente_nexus_id'] != session.get('cliente_nexus_id'):
            return jsonify({'erro': 'Acesso negado'}), 403

        return jsonify(cliente), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/clientes', methods=['POST'])
@login_required
def criar_cliente():
    """Cria um novo cliente final"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente Nexus não encontrado'}), 404

        data = request.get_json()

        # Validações
        if not data.get('nome') or not data.get('cpf'):
            return jsonify({'erro': 'Nome e CPF são obrigatórios'}), 400

        # Valida CPF
        if not validar_cpf(data['cpf']):
            return jsonify({'erro': 'CPF inválido'}), 400

        # Verifica se CPF já existe
        cliente_existente = ClienteFinal.buscar_por_cpf(data['cpf'])
        if cliente_existente:
            return jsonify({'erro': 'CPF já cadastrado'}), 400

        # Normalizar WhatsApp se presente (padrão da automação: apenas dígitos)
        whatsapp_normalizado = None
        if data.get('whatsapp'):
            import re
            whatsapp_limpo = re.sub(r'[^\d]', '', str(data['whatsapp']))

            # Adicionar código do país se não tiver
            if whatsapp_limpo and not whatsapp_limpo.startswith('55'):
                whatsapp_limpo = '55' + whatsapp_limpo

            whatsapp_normalizado = whatsapp_limpo if whatsapp_limpo else None

        # Cria o cliente
        cliente_id = ClienteFinal.criar(
            cliente_nexus_id=cliente_nexus_id,
            nome=data['nome'],
            cpf=data['cpf'],
            telefone=data.get('telefone'),
            whatsapp=whatsapp_normalizado,
            email=data.get('email'),
            endereco=data.get('endereco'),
            observacoes=data.get('observacoes')
        )

        return jsonify({
            'sucesso': True,
            'mensagem': 'Cliente criado com sucesso',
            'cliente_id': cliente_id
        }), 201

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
@login_required
def atualizar_cliente(cliente_id):
    """Atualiza dados de um cliente"""
    try:
        # Verifica se o cliente pertence ao usuário logado
        cliente = ClienteFinal.buscar_por_id(cliente_id)

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        if cliente['cliente_nexus_id'] != session.get('cliente_nexus_id'):
            return jsonify({'erro': 'Acesso negado'}), 403

        data = request.get_json()

        # Normalizar WhatsApp se presente (padrão da automação: apenas dígitos)
        if 'whatsapp' in data and data['whatsapp']:
            import re
            whatsapp_limpo = re.sub(r'[^\d]', '', str(data['whatsapp']))

            # Adicionar código do país se não tiver
            if whatsapp_limpo and not whatsapp_limpo.startswith('55'):
                whatsapp_limpo = '55' + whatsapp_limpo

            data['whatsapp'] = whatsapp_limpo

        # Atualiza
        sucesso = ClienteFinal.atualizar(cliente_id, **data)

        if sucesso:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Cliente atualizado com sucesso'
            }), 200
        else:
            return jsonify({'erro': 'Nenhum campo para atualizar'}), 400

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
@login_required
def deletar_cliente(cliente_id):
    """Deleta um cliente"""
    try:
        # Verifica se o cliente pertence ao usuário logado
        cliente = ClienteFinal.buscar_por_id(cliente_id)

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        if cliente['cliente_nexus_id'] != session.get('cliente_nexus_id'):
            return jsonify({'erro': 'Acesso negado'}), 403

        # Deleta
        sucesso = ClienteFinal.deletar(cliente_id)

        if sucesso:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Cliente deletado com sucesso'
            }), 200
        else:
            return jsonify({'erro': 'Erro ao deletar cliente'}), 500

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos', methods=['GET'])
@login_required
def listar_boletos():
    """Lista boletos do cliente"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        mes_referencia = request.args.get('mes_referencia')
        status_envio = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)

        boletos = Boleto.listar_por_cliente_nexus(
            cliente_nexus_id,
            mes_referencia,
            status_envio,
            limit
        )

        return jsonify({'boletos': boletos}), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos/pendentes', methods=['GET'])
@login_required
def listar_boletos_pendentes():
    """Lista boletos pendentes de envio"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        boletos = Boleto.listar_pendentes(cliente_nexus_id)

        return jsonify({'boletos': boletos}), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/configuracoes', methods=['GET'])
@login_required
def get_configuracoes():
    """Retorna configurações do cliente"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        config = Configuracao.buscar(cliente_nexus_id)

        return jsonify(config if config else {}), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/configuracoes', methods=['PUT'])
@login_required
def atualizar_configuracoes():
    """Atualiza configurações do cliente"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        data = request.get_json()

        sucesso = Configuracao.atualizar(cliente_nexus_id, **data)

        if sucesso:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Configurações atualizadas'
            }), 200
        else:
            return jsonify({'erro': 'Erro ao atualizar'}), 500

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ============================================
# ROTAS PARA CONSUMIR DADOS DO PORTAL CONSÓRCIO
# ============================================

@crm_bp.route('/clientes-finais', methods=['GET'])
@login_required
def listar_clientes_finais_portal():
    """Lista clientes finais do Portal Consórcio"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Buscar clientes finais da tabela clientes_finais (Portal)
        clientes = db.execute_query("""
            SELECT * FROM clientes_finais
            WHERE cliente_nexus_id = %s AND ativo = true
            ORDER BY created_at DESC
        """, (cliente_nexus_id,))

        return jsonify({
            'success': True,
            'clientes': clientes
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/clientes-finais/<int:cliente_id>', methods=['GET'])
@login_required
def get_cliente_final_portal(cliente_id):
    """Retorna dados de um cliente final específico do Portal"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        cliente = db.execute_query("""
            SELECT * FROM clientes_finais
            WHERE id = %s AND cliente_nexus_id = %s AND ativo = true
        """, (cliente_id, cliente_nexus_id))

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        return jsonify({
            'success': True,
            'cliente': cliente[0]
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos-portal', methods=['GET'])
@login_required
def listar_boletos_portal():
    """Lista boletos do Portal Consórcio"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Parâmetro limit opcional
        limit = request.args.get('limit', type=int)

        # Buscar boletos da tabela boletos (Portal)
        query = """
            SELECT b.*, cf.nome_completo, cf.cpf, cf.numero_contrato,
                   cf.whatsapp, cf.telefone_celular
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.cliente_nexus_id = %s
            ORDER BY b.created_at DESC, b.data_vencimento DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        boletos = db.execute_query(query, (cliente_nexus_id,))

        return jsonify({
            'success': True,
            'boletos': boletos or []
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos-portal/pendentes-envio', methods=['GET'])
@login_required
def listar_boletos_portal_pendentes():
    """Lista boletos pendentes de envio do Portal"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        boletos = db.execute_query("""
            SELECT b.*, cf.nome_completo, cf.cpf, cf.numero_contrato,
                   cf.whatsapp, cf.telefone_celular
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.cliente_nexus_id = %s
            AND b.status_envio = 'nao_enviado'
            AND b.status = 'pendente'
            ORDER BY b.data_vencimento ASC
        """, (cliente_nexus_id,))

        return jsonify({
            'success': True,
            'boletos': boletos
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos-portal/<int:boleto_id>/marcar-enviado', methods=['PUT'])
@login_required
def marcar_boleto_enviado(boleto_id):
    """Marca um boleto como enviado"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        # Verificar se boleto pertence ao cliente
        boleto = db.execute_query("""
            SELECT id FROM boletos
            WHERE id = %s AND cliente_nexus_id = %s
        """, (boleto_id, cliente_nexus_id))

        if not boleto:
            return jsonify({'erro': 'Boleto não encontrado'}), 404

        # Atualizar status
        from datetime import datetime
        db.execute_update("""
            UPDATE boletos
            SET status_envio = 'enviado',
                data_envio = %s,
                enviado_por = %s
            WHERE id = %s
        """, (datetime.now(), session.get('usuario_nome', 'CRM'), boleto_id))

        return jsonify({
            'success': True,
            'message': 'Boleto marcado como enviado'
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos-portal/<int:boleto_id>/enviar-whatsapp', methods=['POST'])
@login_required
def enviar_boleto_whatsapp_crm(boleto_id):
    """Envia boleto por WhatsApp via CRM"""
    try:
        import requests
        import base64
        from datetime import datetime
        from services.mensagens_personalizadas import mensagens_service

        print(f"\n[DEBUG] ===== INÍCIO ENVIO BOLETO PORTAL {boleto_id} =====")

        cliente_nexus_id = session.get('cliente_nexus_id')
        print(f"[DEBUG] Cliente Nexus ID: {cliente_nexus_id}")

        # Buscar boleto com dados do cliente
        print(f"[DEBUG] Buscando boleto no banco...")
        boleto = db.execute_query("""
            SELECT b.*, cf.nome_completo, cf.whatsapp, cf.numero_contrato
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.id = %s AND b.cliente_nexus_id = %s
        """, (boleto_id, cliente_nexus_id))

        print(f"[DEBUG] Boleto encontrado: {boleto is not None and len(boleto) > 0}")

        if not boleto:
            return jsonify({'erro': 'Boleto não encontrado'}), 404

        boleto = boleto[0]
        print(f"[DEBUG] Nome: {boleto.get('nome_completo')}")
        print(f"[DEBUG] WhatsApp: {boleto.get('whatsapp')}")
        print(f"[DEBUG] PDF Path: {boleto.get('pdf_path')}")

        # Verificar se tem WhatsApp
        if not boleto['whatsapp']:
            return jsonify({'erro': 'Cliente não possui WhatsApp cadastrado'}), 400

        # Verificar se PDF existe
        if not boleto['pdf_path'] or not os.path.exists(boleto['pdf_path']):
            return jsonify({'erro': 'Arquivo PDF não encontrado'}), 404

        # Buscar nome da empresa
        cliente_nexus_data = db.execute_query(
            "SELECT nome_empresa FROM clientes_nexus WHERE id = %s",
            (cliente_nexus_id,)
        )
        nome_empresa = cliente_nexus_data[0]['nome_empresa'] if cliente_nexus_data else 'Cred MS'

        # Gerar mensagem personalizada aleatória (usa uma das 10 mensagens)
        mensagem = mensagens_service.gerar_mensagem_boleto(
            dados_cliente={'nome_completo': boleto['nome_completo'], 'numero_contrato': boleto['numero_contrato']},
            dados_boleto=boleto,
            nome_empresa=nome_empresa
        )

        print(f"[DEBUG] Mensagem gerada (aleatória): {mensagem[:100]}...")

        # Limpar número WhatsApp
        whatsapp_numero = boleto['whatsapp'].replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Enviar mensagem de texto
        payload_msg = {
            'phone': whatsapp_numero,
            'message': mensagem
        }

        print(f"[DEBUG] Enviando mensagem para: {whatsapp_numero}")
        print(f"[DEBUG] Payload: {payload_msg}")

        try:
            response_msg = requests.post('http://localhost:3001/send-text', json=payload_msg, timeout=10)
            print(f"[DEBUG] Status: {response_msg.status_code}")
            print(f"[DEBUG] Response: {response_msg.text}")

            if not response_msg.ok:
                return jsonify({'erro': f'Erro ao enviar mensagem: {response_msg.text}'}), 500
        except Exception as e:
            print(f"[DEBUG] Exception: {str(e)}")
            return jsonify({'erro': f'Erro ao enviar mensagem de texto: {str(e)}'}), 500

        # Enviar PDF
        print(f"[DEBUG] Caminho do PDF: {boleto['pdf_path']}")
        print(f"[DEBUG] Arquivo existe: {os.path.exists(boleto['pdf_path'])}")

        with open(boleto['pdf_path'], 'rb') as pdf_file:
            pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

        payload_doc = {
            'phone': whatsapp_numero,
            'filePath': boleto['pdf_path'],
            'caption': f"📄 *Boleto Cred MS* - Vencimento: {boleto['data_vencimento'].strftime('%d/%m/%Y') if boleto['data_vencimento'] else 'N/A'}\n\n💚 Cred MS - Seu parceiro de confiança!",
            'filename': boleto['pdf_filename'] or 'boleto.pdf'
        }

        print(f"[DEBUG] Enviando arquivo...")

        try:
            response_doc = requests.post('http://localhost:3001/send-file', json=payload_doc, timeout=30)
            print(f"[DEBUG] Status arquivo: {response_doc.status_code}")
            print(f"[DEBUG] Response arquivo: {response_doc.text}")

            if not response_doc.ok:
                return jsonify({'erro': f'Erro ao enviar documento: {response_doc.text}'}), 500
        except Exception as e:
            print(f"[DEBUG] Exception arquivo: {str(e)}")
            return jsonify({'erro': f'Erro ao enviar PDF: {str(e)}'}), 500

        # Atualizar status do boleto
        print(f"[DEBUG] Atualizando status do boleto...")
        db.execute_update("""
            UPDATE boletos
            SET status_envio = 'enviado', data_envio = %s, enviado_por = %s
            WHERE id = %s
        """, (datetime.now(), session.get('usuario_nome', 'CRM'), boleto_id))

        print(f"[DEBUG] ===== BOLETO ENVIADO COM SUCESSO =====\n")

        return jsonify({
            'success': True,
            'message': 'Boleto enviado com sucesso via WhatsApp!'
        }), 200

    except Exception as e:
        print(f"\n[ERROR] ===== ERRO NO ENVIO DO BOLETO PORTAL =====")
        print(f"[ERROR] Tipo: {type(e).__name__}")
        print(f"[ERROR] Mensagem: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback completo:")
        traceback.print_exc()
        print(f"[ERROR] ========================================\n")
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos/<int:boleto_id>/download', methods=['GET'])
@login_required
def download_boleto_crm(boleto_id):
    """Download de PDF do boleto via CRM"""
    try:
        from flask import send_file
        cliente_nexus_id = session.get('cliente_nexus_id')

        # Buscar boleto
        boleto = db.execute_query(
            "SELECT * FROM boletos WHERE id = %s AND cliente_nexus_id = %s",
            (boleto_id, cliente_nexus_id)
        )

        if not boleto:
            return jsonify({'error': 'Boleto não encontrado'}), 404

        boleto = boleto[0]

        # Construir caminho absoluto
        pdf_path = boleto['pdf_path']
        if not os.path.isabs(pdf_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_path = os.path.join(base_dir, pdf_path)

        if not os.path.exists(pdf_path):
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=boleto['pdf_filename']
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao fazer download'}), 500


@crm_bp.route('/boletos/<int:boleto_id>/visualizar', methods=['GET'])
@login_required
def visualizar_boleto_crm(boleto_id):
    """Visualizar PDF do boleto inline via CRM"""
    try:
        from flask import send_file
        cliente_nexus_id = session.get('cliente_nexus_id')

        # Buscar boleto
        boleto = db.execute_query(
            "SELECT * FROM boletos WHERE id = %s AND cliente_nexus_id = %s",
            (boleto_id, cliente_nexus_id)
        )

        if not boleto:
            return jsonify({'error': 'Boleto não encontrado'}), 404

        boleto = boleto[0]

        # Construir caminho absoluto
        pdf_path = boleto['pdf_path']
        if not os.path.isabs(pdf_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_path = os.path.join(base_dir, pdf_path)

        if not os.path.exists(pdf_path):
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro ao visualizar PDF'}), 500


@crm_bp.route('/boletos/<int:boleto_id>/enviar-whatsapp', methods=['POST'])
@login_required
def enviar_boleto_whatsapp_api_crm(boleto_id):
    """Envia boleto por WhatsApp via API do CRM"""
    try:
        import requests
        import base64
        from datetime import datetime
        from services.mensagens_personalizadas import mensagens_service

        print(f"\n[DEBUG] ===== INÍCIO ENVIO BOLETO CRM {boleto_id} =====")

        cliente_nexus_id = session.get('cliente_nexus_id')
        print(f"[DEBUG] Cliente Nexus ID: {cliente_nexus_id}")

        # Buscar boleto - MESMA QUERY DO DOWNLOAD/VISUALIZAR
        print(f"[DEBUG] Buscando boleto no banco...")
        boleto_data = db.execute_query(
            "SELECT * FROM boletos WHERE id = %s AND cliente_nexus_id = %s",
            (boleto_id, cliente_nexus_id)
        )

        print(f"[DEBUG] Boleto encontrado: {boleto_data is not None and len(boleto_data) > 0}")

        if not boleto_data:
            return jsonify({'error': 'Boleto não encontrado'}), 404

        boleto = boleto_data[0]
        print(f"[DEBUG] PDF Path do banco: {boleto.get('pdf_path')}")
        print(f"[DEBUG] PDF Filename: {boleto.get('pdf_filename')}")

        # Buscar dados do cliente final
        cliente_final = db.execute_query(
            "SELECT nome_completo, whatsapp, numero_contrato FROM clientes_finais WHERE id = %s",
            (boleto['cliente_final_id'],)
        )

        if not cliente_final:
            return jsonify({'error': 'Cliente final não encontrado'}), 404

        cliente_final = cliente_final[0]
        print(f"[DEBUG] Nome: {cliente_final.get('nome_completo')}")
        print(f"[DEBUG] WhatsApp: {cliente_final.get('whatsapp')}")

        # Verificar se tem WhatsApp
        if not cliente_final['whatsapp']:
            return jsonify({'error': 'Cliente não possui WhatsApp cadastrado'}), 400

        # Construir caminho absoluto do PDF - MESMA LÓGICA DO DOWNLOAD/VISUALIZAR
        pdf_path = boleto['pdf_path']
        if not os.path.isabs(pdf_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            pdf_path = os.path.join(base_dir, pdf_path)

        print(f"[DEBUG] Caminho absoluto do PDF: {pdf_path}")
        print(f"[DEBUG] Arquivo existe: {os.path.exists(pdf_path)}")

        if not os.path.exists(pdf_path):
            return jsonify({'error': 'Arquivo PDF não encontrado'}), 404

        # Buscar nome da empresa
        cliente_nexus_data = db.execute_query(
            "SELECT nome_empresa FROM clientes_nexus WHERE id = %s",
            (cliente_nexus_id,)
        )
        nome_empresa = cliente_nexus_data[0]['nome_empresa'] if cliente_nexus_data else 'Cred MS'

        # Gerar mensagem personalizada aleatória (usa uma das 10 mensagens)
        mensagem = mensagens_service.gerar_mensagem_boleto(
            dados_cliente=cliente_final,
            dados_boleto=boleto,
            nome_empresa=nome_empresa
        )

        print(f"[DEBUG] Mensagem gerada (aleatória): {mensagem[:100]}...")

        # Limpar número WhatsApp
        whatsapp_numero = cliente_final['whatsapp'].replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Enviar mensagem de texto
        payload_msg = {
            'phone': whatsapp_numero,
            'message': mensagem
        }

        print(f"[DEBUG] Enviando mensagem para: {whatsapp_numero}")
        print(f"[DEBUG] Payload mensagem: {payload_msg}")

        try:
            response = requests.post('http://localhost:3001/send-text', json=payload_msg, timeout=10)
            print(f"[DEBUG] Status mensagem: {response.status_code}")
            print(f"[DEBUG] Response mensagem: {response.text}")

            if response.status_code != 200:
                return jsonify({'error': f'Erro ao enviar mensagem de texto: {response.text}'}), 500
        except Exception as e:
            print(f"[DEBUG] Exception ao enviar mensagem: {str(e)}")
            return jsonify({'error': f'Erro ao enviar mensagem de texto: {str(e)}'}), 500

        # Pequeno delay antes de enviar o arquivo
        import time
        time.sleep(2)

        # Enviar PDF usando filePath
        payload_pdf = {
            'phone': whatsapp_numero,
            'filePath': pdf_path,
            'caption': f"📄 *Boleto Cred MS* - Vencimento: {boleto['data_vencimento'].strftime('%d/%m/%Y') if boleto['data_vencimento'] else 'N/A'}\n\n💚 Cred MS - Seu parceiro de confiança!",
            'filename': boleto['pdf_filename'] or 'boleto.pdf'
        }

        print(f"[DEBUG] Enviando arquivo...")
        print(f"[DEBUG] Payload arquivo: {payload_pdf}")

        try:
            response = requests.post('http://localhost:3001/send-file', json=payload_pdf, timeout=30)
            print(f"[DEBUG] Status arquivo: {response.status_code}")
            print(f"[DEBUG] Response arquivo: {response.text}")

            if response.status_code != 200:
                return jsonify({'error': f'Erro ao enviar arquivo PDF: {response.text}'}), 500
        except Exception as e:
            print(f"[DEBUG] Exception ao enviar arquivo: {str(e)}")
            return jsonify({'error': f'Erro ao enviar PDF: {str(e)}'}), 500

        # Atualizar status do boleto
        print(f"[DEBUG] Atualizando status do boleto...")
        db.execute_update("""
            UPDATE boletos
            SET status_envio = 'enviado', data_envio = %s, enviado_por = %s
            WHERE id = %s
        """, (datetime.now(), session.get('usuario_nome', 'CRM'), boleto_id))

        print(f"[DEBUG] ===== BOLETO ENVIADO COM SUCESSO =====\n")

        return jsonify({
            'success': True,
            'message': 'Boleto enviado com sucesso via WhatsApp!'
        }), 200

    except Exception as e:
        print(f"\n[ERROR] ===== ERRO NO ENVIO DO BOLETO CRM =====")
        print(f"[ERROR] Tipo: {type(e).__name__}")
        print(f"[ERROR] Mensagem: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback completo:")
        traceback.print_exc()
        print(f"[ERROR] ========================================\n")
        return jsonify({'error': str(e)}), 500


@crm_bp.route('/boletos-modelo/enviar-massa', methods=['POST'])
@login_required
def enviar_boleto_modelo_massa_crm():
    """Envia boleto modelo para todos os clientes ativos via WhatsApp"""
    try:
        from datetime import datetime

        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        data = request.get_json()
        mensagem_personalizada = data.get('mensagem')

        # Importar serviço
        from services.boleto_modelo_service import boleto_modelo_service

        # Enviar para todos os clientes
        resultado = boleto_modelo_service.enviar_modelo_para_todos_clientes(
            cliente_nexus_id=cliente_nexus_id,
            mensagem_personalizada=mensagem_personalizada
        )

        if not resultado['success']:
            return jsonify({'erro': resultado.get('error', 'Erro ao enviar boletos')}), 500

        return jsonify({
            'success': True,
            'total_clientes': resultado['total_clientes'],
            'total_enviados': resultado['total_enviados'],
            'total_erros': resultado['total_erros'],
            'resultados': resultado['resultados'],
            'message': f'Boleto modelo enviado para {resultado["total_enviados"]} clientes!'
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/pastas-digitais', methods=['GET'])
@login_required
def listar_pastas_digitais():
    """Lista pastas digitais organizadas"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Buscar pastas digitais
        pastas = db.execute_query("""
            SELECT pd.*, cf.nome_completo, b.numero_boleto, b.pdf_filename, b.pdf_path
            FROM pastas_digitais pd
            LEFT JOIN clientes_finais cf ON pd.cliente_final_id = cf.id
            LEFT JOIN boletos b ON pd.boleto_id = b.id
            WHERE pd.cliente_nexus_id = %s
            ORDER BY pd.ordem ASC, pd.created_at DESC
        """, (cliente_nexus_id,))

        return jsonify({
            'success': True,
            'pastas': pastas
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/configuracoes-automacao', methods=['GET'])
@login_required
def get_configuracoes_automacao():
    """Retorna configurações de automação"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado na sessão'}), 404

        config = db.execute_query("""
            SELECT * FROM configuracoes_automacao
            WHERE cliente_nexus_id = %s
        """, (cliente_nexus_id,))

        if not config:
            # Criar configuração padrão com todos os campos
            db.execute_update("""
                INSERT INTO configuracoes_automacao (
                    cliente_nexus_id,
                    disparo_automatico_habilitado,
                    dia_do_mes,
                    dias_antes_vencimento,
                    horario_disparo,
                    mensagem_antibloqueio,
                    intervalo_min_segundos,
                    intervalo_max_segundos,
                    pausa_apos_disparos,
                    tempo_pausa_segundos
                ) VALUES (%s, false, 1, 3, '09:00:00', 'Olá! Tudo bem? Segue em anexo seu boleto. Qualquer dúvida, estamos à disposição!', 3, 7, 20, 60)
                ON CONFLICT (cliente_nexus_id) DO NOTHING
            """, (cliente_nexus_id,))

            # Busca novamente
            config = db.execute_query("""
                SELECT * FROM configuracoes_automacao
                WHERE cliente_nexus_id = %s
            """, (cliente_nexus_id,))

        # Serializar campos não-JSON (time, datetime, etc)
        if config and config[0]:
            config_serializada = dict(config[0])

            # Converte time para string
            if 'horario_disparo' in config_serializada and config_serializada['horario_disparo']:
                config_serializada['horario_disparo'] = str(config_serializada['horario_disparo'])

            # Converte datetime para string
            if 'created_at' in config_serializada and config_serializada['created_at']:
                config_serializada['created_at'] = config_serializada['created_at'].isoformat()

            if 'updated_at' in config_serializada and config_serializada['updated_at']:
                config_serializada['updated_at'] = config_serializada['updated_at'].isoformat()
        else:
            config_serializada = {}

        return jsonify({
            'success': True,
            'configuracao': config_serializada
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/configuracoes-automacao', methods=['PUT'])
@login_required
def atualizar_configuracoes_automacao():
    """Atualiza configurações de automação"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        data = request.get_json()

        # Campos permitidos
        campos_update = []
        valores = []

        campos_permitidos = [
            'disparo_automatico_habilitado', 'dias_antes_vencimento',
            'horario_disparo', 'mensagem_antibloqueio', 'mensagem_personalizada',
            'intervalo_min_segundos', 'intervalo_max_segundos',
            'pausa_apos_disparos', 'tempo_pausa_segundos', 'dia_do_mes'
        ]

        for campo in campos_permitidos:
            if campo in data:
                # Validação especial para dia_do_mes
                if campo == 'dia_do_mes':
                    dia = int(data[campo])
                    if dia < 1 or dia > 31:
                        return jsonify({'erro': 'O dia do mês deve estar entre 1 e 31'}), 400

                campos_update.append(f"{campo} = %s")
                valores.append(data[campo])

        if not campos_update:
            return jsonify({'erro': 'Nenhum campo para atualizar'}), 400

        valores.append(cliente_nexus_id)

        query = f"""
            UPDATE configuracoes_automacao
            SET {', '.join(campos_update)}
            WHERE cliente_nexus_id = %s
        """

        db.execute_update(query, tuple(valores))

        return jsonify({
            'success': True,
            'message': 'Configurações atualizadas com sucesso'
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/dashboard-stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Retorna estatísticas do dashboard com dados reais de boletos"""
    try:
        # Total de clientes finais (TODOS, não filtrar por cliente_nexus_id)
        total_clientes = db.execute_query("""
            SELECT COUNT(*) as total
            FROM clientes_finais
            WHERE ativo = TRUE
        """)

        # Total de boletos (TODOS)
        total_boletos = db.execute_query("""
            SELECT COUNT(*) as total
            FROM boletos b
        """)

        # Boletos enviados (status_envio = 'enviado')
        boletos_enviados = db.execute_query("""
            SELECT COUNT(*) as total
            FROM boletos b
            WHERE b.status_envio = 'enviado'
        """)

        # Boletos pendentes (status_envio = 'nao_enviado' ou NULL)
        boletos_pendentes = db.execute_query("""
            SELECT COUNT(*) as total
            FROM boletos b
            WHERE (b.status_envio = 'nao_enviado' OR b.status_envio IS NULL OR b.status_envio = 'pendente')
        """)

        # Últimos 10 boletos (TODOS, não filtrar)
        ultimos_boletos = db.execute_query("""
            SELECT
                b.id,
                b.numero_boleto,
                cf.nome_completo as cliente_nome,
                cf.cpf as cliente_cpf,
                b.valor_original,
                b.data_vencimento,
                b.data_emissao,
                b.mes_referencia,
                b.ano_referencia,
                b.status,
                b.status_envio,
                b.pdf_filename,
                b.pdf_size,
                b.created_at
            FROM boletos b
            LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            ORDER BY b.created_at DESC
            LIMIT 10
        """)

        # Serializar os últimos boletos (converter datetime para string)
        ultimos_boletos_serializado = []
        if ultimos_boletos:
            for boleto in ultimos_boletos:
                boleto_dict = dict(boleto)

                # Converter datetime para string
                if 'data_vencimento' in boleto_dict and boleto_dict['data_vencimento']:
                    boleto_dict['data_vencimento'] = boleto_dict['data_vencimento'].isoformat()
                if 'data_emissao' in boleto_dict and boleto_dict['data_emissao']:
                    boleto_dict['data_emissao'] = boleto_dict['data_emissao'].isoformat()
                if 'created_at' in boleto_dict and boleto_dict['created_at']:
                    boleto_dict['created_at'] = boleto_dict['created_at'].isoformat()

                ultimos_boletos_serializado.append(boleto_dict)

        return jsonify({
            'success': True,
            'stats': {
                'total_clientes': total_clientes[0]['total'] if total_clientes else 0,
                'total_boletos': total_boletos[0]['total'] if total_boletos else 0,
                'boletos_enviados': boletos_enviados[0]['total'] if boletos_enviados else 0,
                'boletos_pendentes': boletos_pendentes[0]['total'] if boletos_pendentes else 0
            },
            'ultimos_boletos': ultimos_boletos_serializado
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/scheduler/status', methods=['GET'])
@login_required
def get_scheduler_status():
    """Retorna o status do scheduler de automação"""
    try:
        from services.automation_scheduler import automation_scheduler

        status = automation_scheduler.status()

        return jsonify({
            'success': True,
            'scheduler': status
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/scheduler/ativar-disparo-completo', methods=['POST'])
@login_required
def ativar_disparo_completo():
    """Ativa disparo COMPLETO com mensagens personalizadas e fluxo sequencial"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        # Buscar boletos REAIS do banco (importados do Canopus)
        # FILTRA PLACEHOLDERS: só envia para números REAIS (não 55679999999999)
        boletos_reais = db.execute_query("""
            SELECT
                b.id as boleto_id,
                b.pdf_path,
                b.numero_boleto,
                b.data_vencimento,
                b.valor_original,
                b.cliente_final_id,
                cf.nome_completo as cliente_final_nome,
                cf.cpf as cliente_final_cpf,
                cf.whatsapp,
                cf.nome_completo,
                cf.numero_contrato
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.cliente_nexus_id = %s
            AND b.status_envio = 'nao_enviado'
            AND cf.whatsapp IS NOT NULL
            AND cf.whatsapp != ''
            AND cf.whatsapp != '55679999999999'
            AND cf.whatsapp != '0000000000'
            AND cf.ativo = true
            ORDER BY b.data_vencimento ASC
        """, (cliente_nexus_id,))

        if not boletos_reais:
            return jsonify({
                'success': False,
                'message': 'Nenhum boleto pendente com WhatsApp encontrado'
            }), 400

        # Buscar configurações
        config = db.execute_query("""
            SELECT intervalo_min_segundos, intervalo_max_segundos
            FROM configuracoes_automacao
            WHERE cliente_nexus_id = %s
        """, (cliente_nexus_id,))

        intervalo_min = config[0].get('intervalo_min_segundos', 3) if config else 3
        intervalo_max = config[0].get('intervalo_max_segundos', 7) if config else 7

        # Buscar nome da empresa
        cliente_nexus = db.execute_query(
            "SELECT nome_empresa FROM clientes_nexus WHERE id = %s",
            (cliente_nexus_id,)
        )
        nome_empresa = cliente_nexus[0]['nome_empresa'] if cliente_nexus else 'Nexus'

        # Enviar notificação de INÍCIO para Nexus
        from services.whatsapp_evolution import whatsapp_service
        from routes.crm_disparo_individual import buscar_numeros_notificacao
        numeros_notificacao = buscar_numeros_notificacao(cliente_nexus_id)

        mensagem_inicio = f"""🚀 DISPARO COMPLETO INICIADO!

📊 Total de boletos: {len(boletos_reais)}
⏰ Iniciando envio automático com mensagens personalizadas...

Sistema Nexus - Aqui seu tempo vale ouro"""

        for numero in numeros_notificacao:
            try:
                whatsapp_service.enviar_mensagem(
                    numero,
                    mensagem_inicio,
                    cliente_nexus_id
                )
            except Exception as e:
                log_sistema('warning', f'Erro ao enviar notificação inicial para {numero}: {str(e)}', 'disparo')

        # Disparar cada boleto com mensagem personalizada
        import random
        import time
        from datetime import datetime
        from pathlib import Path
        from services.mensagens_personalizadas import mensagens_service

        stats = {
            'total': len(boletos_reais),
            'enviados': 0,
            'erros': 0,
            'inicio': time.time()
        }

        for idx, boleto in enumerate(boletos_reais):
            try:
                whatsapp = boleto['whatsapp']
                nome_cliente = boleto['nome_completo']
                cpf_cliente = boleto['cliente_final_cpf']

                log_sistema('info', f"[{idx+1}/{len(boletos_reais)}] Processando cliente: {nome_cliente}", 'disparo')

                # Obter caminho do PDF do banco de dados
                pdf_path = boleto.get('pdf_path')
                pdf_temp_criado = False  # Flag para deletar depois

                # Se não tiver pdf_path válido, buscar de downloads_canopus
                if not pdf_path or not Path(pdf_path).exists():
                    log_sistema('info', f"PDF não encontrado em pdf_path, buscando em downloads_canopus para {nome_cliente}", 'disparo')

                    # Buscar PDF mais recente deste CPF em downloads_canopus
                    pdf_canopus = db.execute_query("""
                        SELECT caminho_arquivo, nome_arquivo
                        FROM downloads_canopus
                        WHERE cpf = %s
                        AND status = 'sucesso'
                        AND caminho_arquivo IS NOT NULL
                        AND caminho_arquivo != ''
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, (cpf_cliente,))

                    if not pdf_canopus or not pdf_canopus[0].get('caminho_arquivo'):
                        log_sistema('warning', f"PDF não encontrado em downloads_canopus para {nome_cliente} (CPF: {cpf_cliente})", 'disparo')
                        stats['erros'] += 1
                        continue

                    # Decodificar base64 e criar arquivo temporário
                    import base64
                    import tempfile
                    import os

                    try:
                        pdf_base64 = pdf_canopus[0]['caminho_arquivo']
                        pdf_bytes = base64.b64decode(pdf_base64)

                        # Criar arquivo temporário
                        temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix='boleto_')
                        os.write(temp_fd, pdf_bytes)
                        os.close(temp_fd)

                        pdf_temp_criado = True
                        log_sistema('success', f"✅ PDF temporário criado para {nome_cliente}: {pdf_path}", 'disparo')
                    except Exception as e:
                        log_sistema('error', f"Erro ao decodificar PDF de downloads_canopus para {nome_cliente}: {str(e)}", 'disparo')
                        stats['erros'] += 1
                        continue

                # EXTRAIR DADOS REAIS DO PDF usando nosso extrator
                from services.pdf_extractor import extrair_dados_boleto

                log_sistema('info', f"Extraindo dados do PDF: {pdf_path}", 'disparo')
                dados_pdf = extrair_dados_boleto(pdf_path)

                if not dados_pdf.get('sucesso'):
                    log_sistema('warning', f"Não foi possível extrair dados do PDF para {nome_cliente}", 'disparo')
                    # Continua com dados do banco como fallback
                    dados_pdf = {}
                else:
                    # Log dos dados extraídos com sucesso
                    log_sistema('success', f"✅ Dados extraídos do PDF - Venc: {dados_pdf.get('vencimento_str')}, Valor: R$ {dados_pdf.get('valor', 0):.2f}", 'disparo')

                # 1. GERAR MENSAGEM PERSONALIZADA COM DADOS DO PDF
                log_sistema('info', f"📝 Gerando mensagem personalizada para {nome_cliente}", 'disparo')

                mensagem_personalizada = mensagens_service.gerar_mensagem_boleto(
                    dados_cliente={
                        'nome_completo': nome_cliente,
                        'numero_contrato': boleto.get('numero_contrato', 'N/A')
                    },
                    dados_boleto={
                        'valor_original': dados_pdf.get('valor') if dados_pdf.get('sucesso') else boleto['valor_original'],
                        'data_vencimento': dados_pdf.get('vencimento_str') if dados_pdf.get('sucesso') else boleto['data_vencimento'].strftime('%d/%m/%Y')
                    },
                    nome_empresa='Cred MS Consorcios'
                )

                log_sistema('success', f"✅ Mensagem gerada. Tamanho: {len(mensagem_personalizada)} caracteres", 'disparo')
                log_sistema('info', f"📱 Enviando mensagem de texto para {whatsapp}", 'disparo')

                # 2. ENVIAR MENSAGEM PERSONALIZADA
                resultado_msg = whatsapp_service.enviar_mensagem(
                    whatsapp,
                    mensagem_personalizada,
                    cliente_nexus_id
                )

                log_sistema('info', f"📋 Resultado envio mensagem: {resultado_msg}", 'disparo')

                if not resultado_msg.get('sucesso'):
                    log_sistema('error', f"❌ FALHA ao enviar mensagem para {nome_cliente}: {resultado_msg.get('error', 'Erro desconhecido')}", 'disparo')
                    stats['erros'] += 1
                    continue

                log_sistema('success', f"✅ Mensagem de texto enviada com sucesso!", 'disparo')

                # 3. AGUARDAR 2-3 SEGUNDOS ANTES DE ENVIAR O BOLETO
                intervalo_msg_pdf = random.randint(2, 3)
                log_sistema('info', f"⏳ Aguardando {intervalo_msg_pdf}s antes de enviar PDF...", 'disparo')
                time.sleep(intervalo_msg_pdf)

                # 4. ENVIAR PDF DO BOLETO COM DADOS REAIS DO PDF
                log_sistema('info', f"🔄 INICIANDO ENVIO DE PDF para {nome_cliente}", 'disparo')

                vencimento_str = dados_pdf.get('vencimento_str') if dados_pdf.get('sucesso') else boleto['data_vencimento'].strftime('%d/%m/%Y')
                valor_str = f"R$ {dados_pdf.get('valor', 0):.2f}" if dados_pdf.get('sucesso') else f"R$ {boleto['valor_original']:.2f}"

                legenda = f"📄 *Boleto {nome_empresa}*\nVencimento: {vencimento_str}\nValor: {valor_str}\n\n💚 {nome_empresa} - Seu parceiro de confiança!"

                log_sistema('info', f"📄 Preparando envio de PDF:", 'disparo')
                log_sistema('info', f"  ├─ Cliente: {nome_cliente}", 'disparo')
                log_sistema('info', f"  ├─ WhatsApp: {whatsapp}", 'disparo')
                log_sistema('info', f"  ├─ Arquivo: {pdf_path}", 'disparo')
                log_sistema('info', f"  ├─ Temporário: {pdf_temp_criado}", 'disparo')
                log_sistema('info', f"  └─ Legenda: {legenda[:50]}...", 'disparo')

                # Verificar se arquivo existe antes de tentar enviar
                import os
                if not os.path.exists(pdf_path):
                    log_sistema('error', f"❌ ARQUIVO PDF NÃO EXISTE: {pdf_path}", 'disparo')
                    stats['erros'] += 1
                    continue

                tamanho_pdf = os.path.getsize(pdf_path)
                log_sistema('info', f"✅ Arquivo PDF existe. Tamanho: {tamanho_pdf} bytes", 'disparo')

                log_sistema('info', f"📤 Chamando whatsapp_service.enviar_pdf()...", 'disparo')

                resultado_pdf = whatsapp_service.enviar_pdf(
                    whatsapp,
                    pdf_path,
                    legenda,
                    cliente_nexus_id
                )

                log_sistema('info', f"📋 Resultado PDF recebido: {resultado_pdf}", 'disparo')

                # Verificar tanto 'sucesso' quanto 'success' (compatibilidade)
                pdf_enviado = resultado_pdf.get('sucesso') or resultado_pdf.get('success')

                if pdf_enviado:
                    # 5. ATUALIZAR STATUS DO BOLETO
                    db.execute_update("""
                        UPDATE boletos
                        SET status_envio = 'enviado', data_envio = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (boleto['boleto_id'],))

                    stats['enviados'] += 1
                    log_sistema('success', f"✅ Boleto enviado com sucesso para {nome_cliente}", 'disparo')
                else:
                    erro_msg = resultado_pdf.get('error') or resultado_pdf.get('mensagem') or 'Erro desconhecido'
                    log_sistema('error', f"❌ Erro ao enviar PDF para {nome_cliente}: {erro_msg}", 'disparo')
                    log_sistema('error', f"📋 Detalhes do erro: {resultado_pdf}", 'disparo')
                    stats['erros'] += 1

                # 6. INTERVALO ENTRE CLIENTES (segurança anti-bloqueio)
                if idx < len(boletos_reais) - 1:
                    intervalo = random.randint(intervalo_min, intervalo_max)
                    log_sistema('info', f"Aguardando {intervalo}s antes do próximo disparo...", 'disparo')
                    time.sleep(intervalo)

            except Exception as e:
                log_sistema('error', f"Erro ao processar {nome_cliente}: {str(e)}", 'disparo')
                stats['erros'] += 1
            finally:
                # Limpar arquivo temporário se foi criado
                if pdf_temp_criado and pdf_path and os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                        log_sistema('info', f"Arquivo temporário removido: {pdf_path}", 'disparo')
                    except Exception as e:
                        log_sistema('warning', f"Erro ao remover arquivo temporário {pdf_path}: {str(e)}", 'disparo')

        # Calcular tempo total
        tempo_total = time.time() - stats['inicio']
        tempo_minutos = tempo_total / 60
        taxa_sucesso = (stats['enviados'] / stats['total']) * 100 if stats['total'] > 0 else 0

        # Enviar notificação de FIM
        try:
            from datetime import timedelta
            proxima_data = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

            mensagem_final = f"""✅ *DISPARO COMPLETO FINALIZADO!*

🕐 *Finalizado em:* {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
⏱️ *Tempo total:* {tempo_minutos:.1f} minutos

📊 *Estatísticas do Disparo:*
• Total processado: {stats['total']} clientes
• Boletos enviados: {stats['enviados']}
• Taxa de sucesso: {taxa_sucesso:.1f}%
• Erros: {stats['erros']}

📅 *Próximo disparo automático:*
• Data: {proxima_data}

✨ *Nexus - Aqui seu tempo vale ouro!*
Obrigado por confiar em nossos serviços."""

            for numero in numeros_notificacao:
                try:
                    whatsapp_service.enviar_mensagem(
                        numero,
                        mensagem_final,
                        cliente_nexus_id
                    )
                except Exception as e:
                    log_sistema('warning', f'Erro ao enviar notificação final para {numero}: {str(e)}', 'disparo')
        except:
            pass

        return jsonify({
            'success': True,
            'message': f'Disparo completo finalizado: {stats["enviados"]} enviados, {stats["erros"]} erros',
            'stats': stats,
            'tempo_execucao': tempo_total
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/scheduler/executar-agora', methods=['POST'])
@login_required
def executar_scheduler_agora():
    """Executa disparo usando boletos REAIS do Canopus"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        # Buscar boletos REAIS do banco (importados do Canopus)
        # FILTRA PLACEHOLDERS: só envia para números REAIS (não 55679999999999)
        boletos_reais = db.execute_query("""
            SELECT
                b.id as boleto_id,
                b.pdf_path,
                b.numero_boleto,
                b.data_vencimento,
                b.valor_original,
                b.cliente_final_id,
                cf.nome_completo as cliente_final_nome,
                cf.cpf as cliente_final_cpf,
                cf.whatsapp,
                cf.nome_completo,
                cf.numero_contrato
            FROM boletos b
            JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE b.cliente_nexus_id = %s
            AND b.status_envio = 'nao_enviado'
            AND cf.whatsapp IS NOT NULL
            AND cf.whatsapp != ''
            AND cf.whatsapp != '55679999999999'
            AND cf.whatsapp != '0000000000'
            AND cf.ativo = true
            ORDER BY b.data_vencimento ASC
        """, (cliente_nexus_id,))

        if not boletos_reais:
            return jsonify({
                'success': False,
                'message': 'Nenhum boleto pendente com WhatsApp encontrado'
            }), 400

        # Buscar configurações
        config = db.execute_query("""
            SELECT mensagem_antibloqueio, intervalo_min_segundos, intervalo_max_segundos
            FROM configuracoes_automacao
            WHERE cliente_nexus_id = %s
        """, (cliente_nexus_id,))

        mensagem_antibloqueio = config[0].get('mensagem_antibloqueio', 'Olá! Segue seu boleto.') if config else 'Olá! Segue seu boleto.'
        intervalo_min = config[0].get('intervalo_min_segundos', 3) if config else 3
        intervalo_max = config[0].get('intervalo_max_segundos', 7) if config else 7

        # Buscar nome da empresa
        cliente_nexus = db.execute_query(
            "SELECT nome_empresa FROM clientes_nexus WHERE id = %s",
            (cliente_nexus_id,)
        )
        nome_empresa = cliente_nexus[0]['nome_empresa'] if cliente_nexus else 'Nexus'

        # Enviar notificação de INÍCIO para Nexus (ambos os números)
        from services.whatsapp_service import whatsapp_service
        from routes.crm_disparo_individual import buscar_numeros_notificacao
        numeros_notificacao = buscar_numeros_notificacao(cliente_nexus_id)

        mensagem_inicio = f"""Olá! Seus boletos foram gerados com sucesso.

📊 Total de boletos: {len(boletos_reais)}
⏰ Iniciando disparo automático...

Sistema Nexus - Aqui seu tempo vale ouro"""

        for numero in numeros_notificacao:
            try:
                whatsapp_service.enviar_mensagem(
                    numero,
                    mensagem_inicio,
                    cliente_nexus_id
                )
            except Exception as e:
                log_sistema('warning', f'Erro ao enviar notificação inicial para {numero}: {str(e)}', 'disparo')

        # Disparar cada boleto
        import random
        import time
        from datetime import datetime
        from pathlib import Path

        stats = {
            'total': len(boletos_reais),
            'enviados': 0,
            'erros': 0,
            'inicio': time.time()
        }

        for idx, boleto in enumerate(boletos_reais):
            try:
                whatsapp = boleto['whatsapp']
                nome_cliente = boleto['nome_completo']

                # Buscar PDF REAL do cliente na pasta do Canopus
                pdfs_cliente = buscar_pdfs_cliente(nome_cliente)

                if not pdfs_cliente:
                    log_sistema('warning', f"PDF não encontrado para {nome_cliente}", 'disparo')
                    stats['erros'] += 1
                    continue

                # Usar o PDF mais recente (primeiro da lista)
                pdf_path = pdfs_cliente[0]['caminho_completo']

                if not Path(pdf_path).exists():
                    log_sistema('warning', f"PDF não encontrado: {pdf_path}", 'disparo')
                    stats['erros'] += 1
                    continue

                # Enviar mensagem antibloqueio
                resultado_msg = whatsapp_service.enviar_mensagem(
                    whatsapp,
                    mensagem_antibloqueio,
                    cliente_nexus_id
                )

                if not resultado_msg.get('sucesso'):
                    stats['erros'] += 1
                    continue

                # Aguardar 2 segundos
                time.sleep(2)

                # Enviar PDF
                legenda = f"📄 *Boleto {nome_empresa}*\nVencimento: {boleto['data_vencimento'].strftime('%d/%m/%Y')}\n\n💚 {nome_empresa}"

                resultado_pdf = whatsapp_service.enviar_pdf(
                    whatsapp,
                    pdf_path,
                    legenda,
                    cliente_nexus_id
                )

                if resultado_pdf.get('sucesso'):
                    # Atualizar status do boleto
                    db.execute_update("""
                        UPDATE boletos
                        SET status_envio = 'enviado', data_envio = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (boleto['boleto_id'],))

                    stats['enviados'] += 1
                    log_sistema('success', f"Boleto enviado para {boleto['nome_completo']}", 'disparo')
                else:
                    stats['erros'] += 1

                # Intervalo entre disparos
                if idx < len(boletos_reais) - 1:
                    intervalo = random.randint(intervalo_min, intervalo_max)
                    time.sleep(intervalo)

            except Exception as e:
                log_sistema('error', f"Erro ao enviar boleto: {str(e)}", 'disparo')
                stats['erros'] += 1

        # Calcular tempo total
        tempo_total = time.time() - stats['inicio']
        tempo_minutos = tempo_total / 60
        taxa_sucesso = (stats['enviados'] / stats['total']) * 100 if stats['total'] > 0 else 0

        # Enviar notificação de FIM para Nexus (ambos os números)
        try:
            from datetime import timedelta
            proxima_data = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

            mensagem_final = f"""✅ *DISPAROS FINALIZADOS COM SUCESSO!*

🕐 *Finalizado em:* {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
⏱️ *Tempo total:* {tempo_minutos:.1f} minutos

📊 *Estatísticas do Disparo:*
• Total processado: {stats['total']} clientes
• Boletos enviados: {stats['enviados']}
• Taxa de sucesso: {taxa_sucesso:.1f}%
• Erros: {stats['erros']}

📅 *Próximo disparo automático:*
• Data: {proxima_data}

✨ *Nexus - Aqui seu tempo vale ouro!*
Obrigado por confiar em nossos serviços."""

            for numero in numeros_notificacao:
                try:
                    whatsapp_service.enviar_mensagem(
                        numero,
                        mensagem_final,
                        cliente_nexus_id
                    )
                except Exception as e:
                    log_sistema('warning', f'Erro ao enviar notificação final para {numero}: {str(e)}', 'disparo')
        except:
            pass

        return jsonify({
            'success': True,
            'message': f'Disparos concluídos: {stats["enviados"]} enviados, {stats["erros"]} erros',
            'stats': stats
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/cliente-debitos/<int:cliente_id>', methods=['GET'])
@login_required
def get_cliente_debitos(cliente_id):
    """Retorna todos os débitos (boletos) de um cliente específico + PDFs REAIS da pasta"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        # 1. Buscar dados do cliente
        cliente = db.execute_query("""
            SELECT id, nome_completo, cpf
            FROM clientes_finais
            WHERE id = %s
            LIMIT 1
        """, (cliente_id,))

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        nome_cliente = cliente[0]['nome_completo']

        # 2. Buscar boletos do banco de dados
        boletos_bd = db.execute_query("""
            SELECT
                b.*,
                cf.nome_completo,
                cf.cpf
            FROM boletos b
            LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            WHERE (b.cliente_final_id = %s OR b.id = %s)
            AND b.cliente_nexus_id = %s
            ORDER BY b.data_vencimento DESC
        """, (cliente_id, cliente_id, cliente_nexus_id))

        # 3. Buscar PDFs REAIS da pasta
        pdfs_reais = buscar_pdfs_cliente(nome_cliente)

        # 4. Combinar boletos do BD com PDFs reais
        # Para cada PDF real encontrado, criar/atualizar entrada de boleto
        boletos_combinados = list(boletos_bd) if boletos_bd else []

        for pdf in pdfs_reais:
            # Adicionar URL de download ao PDF
            pdf['pdf_url'] = f"/api/crm/download-pdf-canopus?arquivo={pdf['arquivo']}"
            pdf['pdf_path'] = pdf['arquivo']
            pdf['tipo_fonte'] = 'pasta_real'  # Indica que veio da pasta
            pdf['status'] = 'pendente'  # Status padrão
            pdf['numero_boleto'] = pdf['arquivo']
            pdf['valor'] = 0  # Valor desconhecido
            pdf['valor_original'] = 0  # Para compatibilidade
            pdf['data_vencimento'] = None
            pdf['ano_referencia'] = None

            # Adicionar à lista de boletos combinados
            boletos_combinados.append(pdf)

        # 5. Calcular estatísticas
        total = len(boletos_combinados)
        pendentes = sum(1 for b in boletos_combinados if b.get('status') == 'pendente')
        pagos = sum(1 for b in boletos_combinados if b.get('status') == 'pago')

        # Vencidos: pendentes com data de vencimento passada
        from datetime import date
        vencidos = sum(1 for b in boletos_combinados
                      if b.get('status') == 'pendente'
                      and b.get('data_vencimento')
                      and b['data_vencimento'] < date.today())

        return jsonify({
            'success': True,
            'total': total,
            'pendentes': pendentes,
            'vencidos': vencidos,
            'pagos': pagos,
            'debitos': boletos_combinados,
            'pdfs_reais_encontrados': len(pdfs_reais)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/download-pdf-canopus', methods=['GET'])
@login_required
def download_pdf_canopus():
    """Serve/baixa PDFs da pasta de downloads do Canopus"""
    try:
        nome_arquivo = request.args.get('arquivo')

        if not nome_arquivo:
            return jsonify({'erro': 'Nome do arquivo não fornecido'}), 400

        # Caminho da pasta
        pasta_downloads = Path(r"D:\Nexus\automation\canopus\downloads\Danner")
        caminho_arquivo = pasta_downloads / nome_arquivo

        # Segurança: verificar se o arquivo está realmente na pasta permitida
        if not caminho_arquivo.resolve().is_relative_to(pasta_downloads.resolve()):
            return jsonify({'erro': 'Acesso negado'}), 403

        if not caminho_arquivo.exists():
            return jsonify({'erro': 'Arquivo não encontrado'}), 404

        # Servir o arquivo
        return send_file(
            str(caminho_arquivo),
            mimetype='application/pdf',
            as_attachment=False,  # False = visualizar no navegador, True = forçar download
            download_name=nome_arquivo
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/monitoramento', methods=['GET'])
@login_required
def get_monitoramento():
    """Retorna dados de monitoramento em tempo real - disparos, taxa de sucesso, atividades"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # 1. DISPAROS HOJE
        disparos_hoje_result = db.execute_query("""
            SELECT COUNT(*) as total
            FROM disparos
            WHERE cliente_nexus_id = %s
            AND DATE(data_disparo) = CURRENT_DATE
            AND status = 'enviado'
        """, (cliente_nexus_id,))

        disparos_hoje = disparos_hoje_result[0]['total'] if disparos_hoje_result else 0

        # 2. TAXA DE SUCESSO (últimos 30 dias)
        taxa_sucesso_result = db.execute_query("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'enviado') as enviados,
                COUNT(*) as total
            FROM disparos
            WHERE cliente_nexus_id = %s
            AND data_disparo >= CURRENT_DATE - INTERVAL '30 days'
        """, (cliente_nexus_id,))

        if taxa_sucesso_result and taxa_sucesso_result[0]['total'] > 0:
            enviados = taxa_sucesso_result[0]['enviados']
            total = taxa_sucesso_result[0]['total']
            taxa_sucesso = round((enviados / total) * 100, 1)
        else:
            taxa_sucesso = 0

        # 3. STATUS WHATSAPP
        whatsapp_status = db.execute_query("""
            SELECT status, phone_number
            FROM whatsapp_sessions
            WHERE cliente_nexus_id = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """, (cliente_nexus_id,))

        whatsapp_conectado = False
        if whatsapp_status and whatsapp_status[0]['status'] == 'connected':
            whatsapp_conectado = True

        # 4. GRÁFICO DE DISPAROS (últimos 7 dias)
        chart_disparos_result = db.execute_query("""
            SELECT
                DATE(data_disparo) as dia,
                COUNT(*) as total
            FROM disparos
            WHERE cliente_nexus_id = %s
            AND data_disparo >= CURRENT_DATE - INTERVAL '6 days'
            AND status = 'enviado'
            GROUP BY DATE(data_disparo)
            ORDER BY dia ASC
        """, (cliente_nexus_id,))

        # Preencher array com 7 dias (pode ter dias sem disparos)
        chart_disparos = []
        for i in range(6, -1, -1):
            from datetime import datetime, timedelta
            dia_atual = (datetime.now() - timedelta(days=i)).date()

            # Buscar valor do dia
            valor_dia = 0
            for row in chart_disparos_result:
                if row['dia'] == dia_atual:
                    valor_dia = row['total']
                    break

            chart_disparos.append(valor_dia)

        # 5. GRÁFICO DE TAXA DE SUCESSO (últimos 7 dias)
        chart_sucesso_result = db.execute_query("""
            SELECT
                DATE(data_disparo) as dia,
                COUNT(*) FILTER (WHERE status = 'enviado') as enviados,
                COUNT(*) as total
            FROM disparos
            WHERE cliente_nexus_id = %s
            AND data_disparo >= CURRENT_DATE - INTERVAL '6 days'
            GROUP BY DATE(data_disparo)
            ORDER BY dia ASC
        """, (cliente_nexus_id,))

        chart_sucesso = []
        for i in range(6, -1, -1):
            from datetime import datetime, timedelta
            dia_atual = (datetime.now() - timedelta(days=i)).date()

            # Buscar taxa do dia
            taxa_dia = 0
            for row in chart_sucesso_result:
                if row['dia'] == dia_atual and row['total'] > 0:
                    taxa_dia = round((row['enviados'] / row['total']) * 100, 1)
                    break

            chart_sucesso.append(taxa_dia)

        # 6. ATIVIDADES RECENTES (últimas 10)
        atividades_result = db.execute_query("""
            SELECT
                d.id,
                d.telefone_destino,
                d.status,
                d.data_disparo,
                d.mensagem_enviada,
                d.erro,
                COALESCE(b.cliente_final_nome, 'Cliente') as nome_cliente
            FROM disparos d
            LEFT JOIN boletos b ON d.boleto_id = b.id
            WHERE d.cliente_nexus_id = %s
            ORDER BY d.data_disparo DESC
            LIMIT 10
        """, (cliente_nexus_id,))

        atividades = []
        for row in atividades_result:
            # Formatar tempo relativo
            from datetime import datetime
            if row['data_disparo']:
                tempo_diff = datetime.now() - row['data_disparo']

                if tempo_diff.seconds < 60:
                    tempo_str = "agora mesmo"
                elif tempo_diff.seconds < 3600:
                    minutos = tempo_diff.seconds // 60
                    tempo_str = f"há {minutos} min"
                elif tempo_diff.days == 0:
                    horas = tempo_diff.seconds // 3600
                    tempo_str = f"há {horas}h"
                else:
                    tempo_str = f"há {tempo_diff.days} dias"
            else:
                tempo_str = "Desconhecido"

            atividades.append({
                'id': row['id'],
                'tipo': 'WhatsApp',
                'descricao': f"Disparo para {row['nome_cliente']}",
                'telefone': row['telefone_destino'],
                'status': row['status'],
                'tempo': tempo_str,
                'erro': row['erro']
            })

        return jsonify({
            'success': True,
            'disparos_hoje': disparos_hoje,
            'taxa_sucesso': taxa_sucesso,
            'whatsapp_conectado': whatsapp_conectado,
            'chart_disparos': chart_disparos,
            'chart_sucesso': chart_sucesso,
            'atividades': atividades
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/clientes-finais/<int:cliente_id>/whatsapp', methods=['PUT'])
@login_required
def atualizar_whatsapp_cliente(cliente_id):
    """Atualiza o WhatsApp de um cliente final"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado na sessão'}), 404

        # Verificar se o cliente pertence ao cliente_nexus logado
        cliente = db.execute_query("""
            SELECT id FROM clientes_finais
            WHERE id = %s AND cliente_nexus_id = %s
        """, (cliente_id, cliente_nexus_id))

        if not cliente:
            return jsonify({'erro': 'Cliente não encontrado ou não pertence a você'}), 404

        data = request.get_json()
        novo_whatsapp = data.get('whatsapp', '').strip()

        if not novo_whatsapp:
            return jsonify({'erro': 'WhatsApp não pode ser vazio'}), 400

        # Limpar o número (remover caracteres especiais)
        import re
        whatsapp_limpo = re.sub(r'[^\d]', '', novo_whatsapp)

        # Validar formato básico (deve ter pelo menos 10 dígitos)
        if len(whatsapp_limpo) < 10:
            return jsonify({'erro': 'Número de WhatsApp inválido (mínimo 10 dígitos)'}), 400

        # Adicionar código do país se não tiver
        if not whatsapp_limpo.startswith('55'):
            whatsapp_limpo = '55' + whatsapp_limpo

        # Atualizar no banco
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s
            WHERE id = %s
        """, (whatsapp_limpo, cliente_id))

        return jsonify({
            'success': True,
            'message': 'WhatsApp atualizado com sucesso',
            'whatsapp': whatsapp_limpo
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/graficos', methods=['GET'])
@login_required
def get_graficos():
    """Retorna dados para gráficos e relatórios analíticos"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # 1. DISPAROS POR MÊS (últimos 6 meses)
        disparos_mes_result = db.execute_query("""
            SELECT
                TO_CHAR(data_disparo, 'YYYY-MM') as mes,
                TO_CHAR(data_disparo, 'Mon/YY') as mes_label,
                COUNT(*) as total
            FROM disparos
            WHERE cliente_nexus_id = %s
            AND data_disparo >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(data_disparo, 'YYYY-MM'), TO_CHAR(data_disparo, 'Mon/YY')
            ORDER BY mes ASC
        """, (cliente_nexus_id,))

        disparos_mes_labels = [row['mes_label'] for row in disparos_mes_result]
        disparos_mes_data = [row['total'] for row in disparos_mes_result]

        # 2. STATUS DOS DISPAROS (total geral)
        status_result = db.execute_query("""
            SELECT
                status,
                COUNT(*) as total
            FROM disparos
            WHERE cliente_nexus_id = %s
            GROUP BY status
        """, (cliente_nexus_id,))

        status_labels = []
        status_data = []
        status_colors = {
            'enviado': '#10b981',
            'erro': '#ef4444',
            'pendente': '#f59e0b',
            'cancelado': '#6b7280'
        }
        status_background = []

        for row in status_result:
            status_labels.append(row['status'].capitalize())
            status_data.append(row['total'])
            status_background.append(status_colors.get(row['status'], '#6b7280'))

        # 3. BOLETOS POR STATUS (últimos 30 dias)
        boletos_status_result = db.execute_query("""
            SELECT
                status,
                COUNT(*) as total
            FROM boletos
            WHERE cliente_nexus_id = %s
            AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY status
        """, (cliente_nexus_id,))

        boletos_labels = []
        boletos_data = []
        boletos_colors = {
            'pendente': '#f59e0b',
            'pago': '#10b981',
            'vencido': '#ef4444',
            'cancelado': '#6b7280'
        }
        boletos_background = []

        for row in boletos_status_result:
            boletos_labels.append(row['status'].capitalize())
            boletos_data.append(row['total'])
            boletos_background.append(boletos_colors.get(row['status'], '#6b7280'))

        # 4. TAXA DE CONVERSÃO (últimos 30 dias) - Disparos x Pagamentos
        conversao_result = db.execute_query("""
            SELECT
                DATE(d.data_disparo) as data,
                COUNT(DISTINCT d.id) as disparos,
                COUNT(DISTINCT CASE WHEN b.status = 'pago' THEN b.id END) as pagamentos
            FROM disparos d
            LEFT JOIN boletos b ON d.boleto_id = b.id
                AND b.cliente_nexus_id = %s
            WHERE d.cliente_nexus_id = %s
            AND d.data_disparo >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(d.data_disparo)
            ORDER BY data ASC
        """, (cliente_nexus_id, cliente_nexus_id))

        conversao_labels = []
        conversao_disparos = []
        conversao_pagamentos = []

        for row in conversao_result:
            conversao_labels.append(row['data'].strftime('%d/%m'))
            conversao_disparos.append(row['disparos'])
            conversao_pagamentos.append(row['pagamentos'])

        # 5. VALORES FINANCEIROS (últimos 6 meses)
        valores_result = db.execute_query("""
            SELECT
                TO_CHAR(data_vencimento, 'YYYY-MM') as mes,
                TO_CHAR(data_vencimento, 'Mon/YY') as mes_label,
                SUM(CASE WHEN status = 'pago' THEN valor_original ELSE 0 END) as valor_pago,
                SUM(CASE WHEN status = 'pendente' THEN valor_original ELSE 0 END) as valor_pendente
            FROM boletos
            WHERE cliente_nexus_id = %s
            AND data_vencimento >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(data_vencimento, 'YYYY-MM'), TO_CHAR(data_vencimento, 'Mon/YY')
            ORDER BY mes ASC
        """, (cliente_nexus_id,))

        valores_labels = [row['mes_label'] for row in valores_result]
        valores_pago = [float(row['valor_pago']) for row in valores_result]
        valores_pendente = [float(row['valor_pendente']) for row in valores_result]

        # 6. RESUMO GERAL
        resumo_result = db.execute_query("""
            SELECT
                (SELECT COUNT(*) FROM disparos WHERE cliente_nexus_id = %s) as total_disparos,
                (SELECT COUNT(*) FROM boletos WHERE cliente_nexus_id = %s) as total_boletos,
                (SELECT COUNT(*) FROM clientes_finais WHERE cliente_nexus_id = %s AND ativo = true) as total_clientes,
                (SELECT COALESCE(SUM(valor_original), 0) FROM boletos
                 WHERE cliente_nexus_id = %s AND status = 'pago') as total_recebido,
                (SELECT COALESCE(SUM(valor_original), 0) FROM boletos
                 WHERE cliente_nexus_id = %s AND status = 'pendente') as total_pendente
        """, (cliente_nexus_id, cliente_nexus_id, cliente_nexus_id,
              cliente_nexus_id, cliente_nexus_id))

        resumo = {}
        if resumo_result:
            row = resumo_result[0]
            resumo = {
                'total_disparos': row['total_disparos'],
                'total_boletos': row['total_boletos'],
                'total_clientes': row['total_clientes'],
                'total_recebido': float(row['total_recebido']),
                'total_pendente': float(row['total_pendente'])
            }

        return jsonify({
            'success': True,
            'disparos_mes': {
                'labels': disparos_mes_labels,
                'data': disparos_mes_data
            },
            'status_disparos': {
                'labels': status_labels,
                'data': status_data,
                'background': status_background
            },
            'boletos_status': {
                'labels': boletos_labels,
                'data': boletos_data,
                'background': boletos_background
            },
            'conversao': {
                'labels': conversao_labels,
                'disparos': conversao_disparos,
                'pagamentos': conversao_pagamentos
            },
            'valores': {
                'labels': valores_labels,
                'pago': valores_pago,
                'pendente': valores_pendente
            },
            'resumo': resumo
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


# ============================================================================
# DEBUG: ENDPOINTS PARA VISUALIZAR BOLETOS
# ============================================================================

@crm_bp.route('/boletos-debug/todos', methods=['GET'])
def listar_todos_boletos_debug():
    """Lista TODOS os boletos (sem filtrar por cliente) - Para debug"""
    try:
        limit = request.args.get('limit', 50, type=int)

        query = """
            SELECT
                b.id,
                b.cliente_nexus_id,
                b.cliente_final_id,
                b.numero_boleto,
                b.valor_original,
                b.data_vencimento,
                b.data_emissao,
                b.mes_referencia,
                b.ano_referencia,
                b.status,
                b.status_envio,
                b.pdf_filename,
                b.pdf_path,
                b.pdf_size,
                b.created_at,
                cf.nome_completo,
                cf.cpf,
                cf.whatsapp
            FROM boletos b
            LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            ORDER BY b.created_at DESC
            LIMIT %s
        """

        boletos = db.execute_query(query, (limit,))

        return jsonify({
            'success': True,
            'count': len(boletos) if boletos else 0,
            'boletos': boletos or []
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos/<int:boleto_id>/visualizar', methods=['GET'])
def visualizar_boleto_pdf(boleto_id):
    """Retorna o PDF do boleto para visualização"""
    try:
        from io import BytesIO
        import base64

        # Buscar boleto no banco
        query = """
            SELECT
                b.id,
                b.pdf_filename,
                b.pdf_path,
                b.pdf_size,
                b.pdf_data
            FROM boletos b
            WHERE b.id = %s
        """

        boleto = db.execute_query(query, (boleto_id,))

        if not boleto or len(boleto) == 0:
            return jsonify({'erro': 'Boleto não encontrado'}), 404

        boleto = boleto[0]

        # Verificar se tem PDF armazenado no banco
        if boleto.get('pdf_data'):
            # PDF está no banco (bytea)
            pdf_bytes = boleto['pdf_data']
            if isinstance(pdf_bytes, str):
                # Se vier como base64 string
                pdf_bytes = base64.b64decode(pdf_bytes)

            return send_file(
                BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=False,
                download_name=boleto['pdf_filename'] or f'boleto_{boleto_id}.pdf'
            )

        # Se não tem no banco, tentar ler do arquivo
        elif boleto.get('pdf_path'):
            pdf_path = Path(boleto['pdf_path'])

            if pdf_path.exists():
                return send_file(
                    pdf_path,
                    mimetype='application/pdf',
                    as_attachment=False,
                    download_name=boleto['pdf_filename'] or f'boleto_{boleto_id}.pdf'
                )
            else:
                return jsonify({
                    'erro': 'Arquivo PDF não encontrado no sistema',
                    'pdf_path': str(pdf_path),
                    'pdf_size': boleto.get('pdf_size'),
                    'mensagem': 'O arquivo pode ter sido removido ou não está acessível no Render'
                }), 404

        else:
            return jsonify({'erro': 'Boleto não possui PDF associado'}), 404

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


@crm_bp.route('/boletos/<int:boleto_id>/download', methods=['GET'])
def download_boleto_pdf(boleto_id):
    """Download do PDF do boleto"""
    try:
        from io import BytesIO
        import base64

        # Buscar boleto no banco
        query = """
            SELECT
                b.id,
                b.pdf_filename,
                b.pdf_path,
                b.pdf_data
            FROM boletos b
            WHERE b.id = %s
        """

        boleto = db.execute_query(query, (boleto_id,))

        if not boleto or len(boleto) == 0:
            return jsonify({'erro': 'Boleto não encontrado'}), 404

        boleto = boleto[0]

        # Verificar se tem PDF armazenado no banco
        if boleto.get('pdf_data'):
            pdf_bytes = boleto['pdf_data']
            if isinstance(pdf_bytes, str):
                pdf_bytes = base64.b64decode(pdf_bytes)

            return send_file(
                BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=boleto['pdf_filename'] or f'boleto_{boleto_id}.pdf'
            )

        # Se não tem no banco, tentar ler do arquivo
        elif boleto.get('pdf_path'):
            pdf_path = Path(boleto['pdf_path'])

            if pdf_path.exists():
                return send_file(
                    pdf_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=boleto['pdf_filename'] or f'boleto_{boleto_id}.pdf'
                )
            else:
                return jsonify({'erro': 'Arquivo PDF não encontrado'}), 404

        else:
            return jsonify({'erro': 'Boleto não possui PDF associado'}), 404

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500
