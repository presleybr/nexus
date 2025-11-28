from flask import Blueprint, jsonify, request, session
from functools import wraps
from services.whatsapp_baileys import whatsapp_service
import os

whatsapp_baileys_bp = Blueprint('whatsapp_baileys', __name__)


def login_required(f):
    """Decorator para verificar se usuário está logado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated_function


@whatsapp_baileys_bp.route('/api/whatsapp/conectar', methods=['POST'])
@login_required
def conectar_whatsapp():
    """
    Inicia conexão com WhatsApp via Baileys
    """
    try:
        resultado = whatsapp_service.conectar()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao conectar: {str(e)}'
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/qr', methods=['GET'])
@login_required
def obter_qr_code():
    """
    Obtém QR Code para conectar WhatsApp
    Retorna QR Code em base64 ou status de conexão
    """
    try:
        resultado = whatsapp_service.obter_qr()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter QR Code: {str(e)}'
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/status', methods=['GET'])
@login_required
def verificar_status():
    """
    Verifica status da conexão WhatsApp
    """
    try:
        resultado = whatsapp_service.verificar_status()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'connected': False,
            'status': 'error',
            'error': str(e)
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/enviar-mensagem', methods=['POST'])
@login_required
def enviar_mensagem():
    """
    Envia mensagem de texto via WhatsApp

    Body JSON:
    {
        "telefone": "+55 67 99988-7766",
        "mensagem": "Texto da mensagem"
    }
    """
    try:
        dados = request.get_json()

        telefone = dados.get('telefone')
        mensagem = dados.get('mensagem')

        if not telefone or not mensagem:
            return jsonify({
                'success': False,
                'error': 'Telefone e mensagem são obrigatórios'
            }), 400

        # Verifica se está conectado
        if not whatsapp_service.esta_conectado():
            return jsonify({
                'success': False,
                'error': 'WhatsApp não está conectado. Conecte-se primeiro.'
            }), 400

        resultado = whatsapp_service.enviar_mensagem(telefone, mensagem)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao enviar mensagem: {str(e)}'
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/enviar-pdf', methods=['POST'])
@login_required
def enviar_pdf():
    """
    Envia arquivo PDF via WhatsApp

    Body JSON:
    {
        "telefone": "+55 67 99988-7766",
        "caminho_pdf": "D:/Nexus/boletos/boleto123.pdf",
        "caption": "Seu boleto",
        "filename": "boleto.pdf"
    }
    """
    try:
        dados = request.get_json()

        telefone = dados.get('telefone')
        caminho_pdf = dados.get('caminho_pdf')
        caption = dados.get('caption', '')
        filename = dados.get('filename', 'documento.pdf')

        if not telefone or not caminho_pdf:
            return jsonify({
                'success': False,
                'error': 'Telefone e caminho do PDF são obrigatórios'
            }), 400

        # Verifica se está conectado
        if not whatsapp_service.esta_conectado():
            return jsonify({
                'success': False,
                'error': 'WhatsApp não está conectado. Conecte-se primeiro.'
            }), 400

        resultado = whatsapp_service.enviar_pdf(telefone, caminho_pdf, caption, filename)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao enviar PDF: {str(e)}'
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/enviar-imagem', methods=['POST'])
@login_required
def enviar_imagem():
    """
    Envia imagem via WhatsApp

    Body JSON:
    {
        "telefone": "+55 67 99988-7766",
        "caminho_imagem": "D:/Nexus/imagens/foto.jpg",
        "caption": "Legenda da imagem"
    }
    """
    try:
        dados = request.get_json()

        telefone = dados.get('telefone')
        caminho_imagem = dados.get('caminho_imagem')
        caption = dados.get('caption', '')

        if not telefone or not caminho_imagem:
            return jsonify({
                'success': False,
                'error': 'Telefone e caminho da imagem são obrigatórios'
            }), 400

        # Verifica se está conectado
        if not whatsapp_service.esta_conectado():
            return jsonify({
                'success': False,
                'error': 'WhatsApp não está conectado. Conecte-se primeiro.'
            }), 400

        resultado = whatsapp_service.enviar_imagem(telefone, caminho_imagem, caption)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao enviar imagem: {str(e)}'
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/enviar-boleto', methods=['POST'])
@login_required
def enviar_boleto_completo():
    """
    Envia mensagem + PDF do boleto com delay anti-bloqueio

    Body JSON:
    {
        "telefone": "+55 67 99988-7766",
        "pdf_path": "D:/Nexus/boletos/boleto123.pdf",
        "mensagem": "Olá! Segue seu boleto referente ao pedido #123",
        "delay_min": 3,
        "delay_max": 7
    }
    """
    try:
        dados = request.get_json()

        telefone = dados.get('telefone')
        pdf_path = dados.get('pdf_path')
        mensagem = dados.get('mensagem')
        delay_min = dados.get('delay_min', 3)
        delay_max = dados.get('delay_max', 7)

        if not telefone or not pdf_path or not mensagem:
            return jsonify({
                'success': False,
                'error': 'Telefone, PDF e mensagem são obrigatórios'
            }), 400

        # Verifica se está conectado
        if not whatsapp_service.esta_conectado():
            return jsonify({
                'success': False,
                'error': 'WhatsApp não está conectado. Conecte-se primeiro.'
            }), 400

        resultado = whatsapp_service.enviar_boleto_completo(
            telefone, pdf_path, mensagem, delay_min, delay_max
        )
        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao enviar boleto: {str(e)}'
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/desconectar', methods=['POST'])
@login_required
def desconectar_whatsapp():
    """
    Desconecta do WhatsApp e limpa sessão
    """
    try:
        resultado = whatsapp_service.desconectar()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao desconectar: {str(e)}'
        }), 500


@whatsapp_baileys_bp.route('/api/whatsapp/teste', methods=['POST'])
@login_required
def testar_envio():
    """
    Endpoint de teste para enviar mensagem rápida

    Body JSON:
    {
        "telefone": "+55 67 99988-7766"
    }
    """
    try:
        dados = request.get_json()
        telefone = dados.get('telefone')

        if not telefone:
            return jsonify({
                'success': False,
                'error': 'Telefone é obrigatório'
            }), 400

        # Verifica se está conectado
        if not whatsapp_service.esta_conectado():
            return jsonify({
                'success': False,
                'error': 'WhatsApp não está conectado. Conecte-se primeiro.'
            }), 400

        mensagem_teste = "🤖 Teste de envio - Nexus CRM\n\nSe você recebeu esta mensagem, o WhatsApp está funcionando corretamente!"

        resultado = whatsapp_service.enviar_mensagem(telefone, mensagem_teste)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao enviar teste: {str(e)}'
        }), 500
