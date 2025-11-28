"""
Rotas Flask para WPPConnect - Conexão e envio de mensagens WhatsApp
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.wppconnect_service import wppconnect_service
from services.whatsapp_service import whatsapp_service
from routes.auth import login_required
from models import log_sistema

whatsapp_wppconnect_bp = Blueprint('whatsapp_wppconnect', __name__, url_prefix='/api/whatsapp/wppconnect')


@whatsapp_wppconnect_bp.route('/status-servidor', methods=['GET'])
@login_required
def verificar_servidor():
    """
    Verifica se o WPPConnect Server está rodando
    """
    try:
        if wppconnect_service.verificar_servidor():
            return jsonify({
                'sucesso': True,
                'rodando': True,
                'mensagem': 'WPPConnect Server está rodando'
            }), 200
        else:
            return jsonify({
                'sucesso': False,
                'rodando': False,
                'mensagem': 'WPPConnect Server não está rodando',
                'instrucoes': 'Execute: wppconnect-server/start.bat'
            }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/iniciar', methods=['POST'])
@login_required
def iniciar_conexao():
    """
    Inicia a conexão com WhatsApp
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        # Verifica se o servidor está rodando
        if not wppconnect_service.verificar_servidor():
            return jsonify({
                'sucesso': False,
                'erro': 'WPPConnect Server não está rodando',
                'instrucoes': 'Execute: wppconnect-server/start.bat'
            }), 400

        # Inicia a conexão
        resultado = wppconnect_service.iniciar_conexao()

        if resultado.get('success'):
            log_sistema('info', 'Conexão WPPConnect iniciada',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})

        return jsonify(resultado), 200

    except Exception as e:
        log_sistema('error', f'Erro ao iniciar conexão: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/qr', methods=['GET'])
@login_required
def obter_qr_code():
    """
    Obtém o QR Code para conexão
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        resultado = wppconnect_service.obter_qr_code()

        return jsonify(resultado), 200

    except Exception as e:
        log_sistema('error', f'Erro ao obter QR Code: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/status', methods=['GET'])
@login_required
def verificar_status():
    """
    Verifica o status da conexão WhatsApp
    """
    try:
        resultado = wppconnect_service.verificar_status()
        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/enviar-mensagem', methods=['POST'])
@login_required
def enviar_mensagem():
    """
    Envia mensagem de texto via WhatsApp
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        data = request.get_json()
        numero = data.get('numero')
        mensagem = data.get('mensagem')

        if not numero or not mensagem:
            return jsonify({'erro': 'Número e mensagem são obrigatórios'}), 400

        resultado = whatsapp_service.enviar_mensagem(
            numero_destino=numero,
            mensagem=mensagem,
            cliente_nexus_id=cliente_nexus_id
        )

        if resultado.get('sucesso'):
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400

    except Exception as e:
        log_sistema('error', f'Erro ao enviar mensagem: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/enviar-pdf', methods=['POST'])
@login_required
def enviar_pdf():
    """
    Envia arquivo PDF via WhatsApp
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        data = request.get_json()
        numero = data.get('numero')
        pdf_path = data.get('pdf_path')
        legenda = data.get('legenda', 'Segue seu boleto em anexo')

        if not numero or not pdf_path:
            return jsonify({'erro': 'Número e caminho do PDF são obrigatórios'}), 400

        resultado = whatsapp_service.enviar_pdf(
            numero_destino=numero,
            pdf_path=pdf_path,
            legenda=legenda,
            cliente_nexus_id=cliente_nexus_id
        )

        if resultado.get('sucesso'):
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400

    except Exception as e:
        log_sistema('error', f'Erro ao enviar PDF: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/enviar-com-antibloqueio', methods=['POST'])
@login_required
def enviar_com_antibloqueio():
    """
    Envia mensagem anti-bloqueio seguida do PDF
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        data = request.get_json()
        numero = data.get('numero')
        pdf_path = data.get('pdf_path')
        mensagem_antibloqueio = data.get('mensagem_antibloqueio',
                                         'Olá! Você receberá seu boleto em instantes.')
        intervalo = data.get('intervalo', 5)

        if not numero or not pdf_path:
            return jsonify({'erro': 'Número e caminho do PDF são obrigatórios'}), 400

        resultado = whatsapp_service.enviar_com_antibloqueio(
            numero_destino=numero,
            pdf_path=pdf_path,
            mensagem_antibloqueio=mensagem_antibloqueio,
            intervalo_segundos=intervalo,
            cliente_nexus_id=cliente_nexus_id
        )

        if resultado.get('sucesso_total'):
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400

    except Exception as e:
        log_sistema('error', f'Erro no envio com anti-bloqueio: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/enviar-em-massa', methods=['POST'])
@login_required
def enviar_em_massa():
    """
    Envia mensagens em massa
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        data = request.get_json()
        destinatarios = data.get('destinatarios', [])

        if not destinatarios:
            return jsonify({'erro': 'Lista de destinatários vazia'}), 400

        resultado = whatsapp_service.enviar_em_massa(
            destinatarios=destinatarios,
            cliente_nexus_id=cliente_nexus_id
        )

        return jsonify(resultado), 200

    except Exception as e:
        log_sistema('error', f'Erro no envio em massa: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/teste', methods=['POST'])
@login_required
def enviar_teste():
    """
    Envia mensagem de teste via WhatsApp
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        data = request.get_json()
        telefone = data.get('telefone')

        if not telefone:
            return jsonify({'error': 'Telefone é obrigatório'}), 400

        # Verifica se está conectado
        status = wppconnect_service.verificar_status()
        if not status.get('connected'):
            return jsonify({'error': 'WhatsApp não está conectado. Conecte-se primeiro.'}), 400

        # Mensagem de teste
        mensagem = f"""✅ *Teste de Conexão - Nexus CRM*

Olá! Esta é uma mensagem de teste do sistema Nexus CRM.

Sua conexão WhatsApp está funcionando perfeitamente! 🚀

_Mensagem enviada em {datetime.now().strftime('%d/%m/%Y às %H:%M')}_"""

        # Envia mensagem
        resultado = wppconnect_service.enviar_mensagem(
            numero=telefone,
            mensagem=mensagem,
            cliente_nexus_id=cliente_nexus_id
        )

        if resultado.get('success'):
            log_sistema('success', f'Mensagem de teste enviada para {telefone}',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})
            return jsonify({'success': True, 'message': 'Mensagem enviada com sucesso!'}), 200
        else:
            return jsonify({'error': resultado.get('error', 'Erro ao enviar mensagem')}), 400

    except Exception as e:
        log_sistema('error', f'Erro no teste: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'error': str(e)}), 500


@whatsapp_wppconnect_bp.route('/desconectar', methods=['POST'])
@login_required
def desconectar():
    """
    Desconecta do WhatsApp
    """
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')

        if not cliente_nexus_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404

        resultado = wppconnect_service.desconectar(cliente_nexus_id)

        if resultado.get('success'):
            log_sistema('info', 'WhatsApp desconectado',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})

        return jsonify(resultado), 200

    except Exception as e:
        log_sistema('error', f'Erro ao desconectar: {str(e)}',
                   'whatsapp', {'cliente_nexus_id': session.get('cliente_nexus_id')})
        return jsonify({'erro': str(e)}), 500


@whatsapp_wppconnect_bp.route('/webhook', methods=['POST'])
def webhook_whatsapp():
    """
    Webhook para receber eventos do WPPConnect Server
    """
    try:
        data = request.get_json()

        log_sistema('info', 'Webhook WhatsApp recebido',
                   'whatsapp', {'data': data})

        # Aqui você pode processar eventos como:
        # - Mensagens recebidas
        # - Status de mensagens
        # - Mudanças de conexão
        # etc.

        return jsonify({'success': True}), 200

    except Exception as e:
        log_sistema('error', f'Erro no webhook: {str(e)}', 'whatsapp')
        return jsonify({'erro': str(e)}), 500
