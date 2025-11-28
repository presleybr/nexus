"""
Rotas WhatsApp - Conexão, envio de mensagens e PDFs
Integrado com Evolution API (http://localhost:8080)
"""

from flask import Blueprint, request, jsonify, session
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whatsapp_evolution import whatsapp_service
from routes.auth import login_required

# Configura logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')


@whatsapp_bp.route('/conectar', methods=['POST'])
@login_required
def conectar():
    """Inicia conexão WhatsApp e gera QR Code"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        logger.info(f"[WHATSAPP] Cliente {cliente_nexus_id} iniciando conexão")

        # Chama servidor Baileys para conectar
        result = whatsapp_service.conectar()

        logger.info(f"[WHATSAPP] Resposta do Baileys: {result}")

        if result.get('success'):
            return jsonify({
                "success": True,
                "message": result.get('message', 'Conexão iniciada. Aguarde QR Code...')
            }), 200
        else:
            error_msg = result.get('error', 'Erro desconhecido ao conectar')
            logger.error(f"[WHATSAPP] Erro ao conectar: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500

    except Exception as e:
        logger.error(f"[WHATSAPP] Exceção ao conectar: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Erro ao conectar: {str(e)}"
        }), 500


@whatsapp_bp.route('/qr', methods=['GET'])
@login_required
def obter_qr():
    """Obtém QR Code para conexão"""
    try:
        logger.info("[WHATSAPP] Solicitando QR Code")

        result = whatsapp_service.obter_qr()

        logger.info(f"[WHATSAPP] Resposta QR: connected={result.get('connected')}, has_qr={bool(result.get('qr'))}")

        if result.get('connected'):
            return jsonify({
                "success": True,
                "connected": True,
                "qr": None
            }), 200
        elif result.get('qr'):
            return jsonify({
                "success": True,
                "connected": False,
                "qr": result['qr']
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": result.get('message', 'QR Code não disponível')
            }), 200

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro ao obter QR: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@whatsapp_bp.route('/status', methods=['GET'])
@login_required
def verificar_status():
    """Verifica status da conexão WhatsApp"""
    try:
        logger.info("[WHATSAPP] Verificando status")

        result = whatsapp_service.verificar_status()

        logger.info(f"[WHATSAPP] Status: {result}")

        return jsonify({
            "success": True,
            "connected": result.get('connected', False),
            "status": result.get('status', 'disconnected'),
            "phone": result.get('phone')
        }), 200

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro ao verificar status: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "connected": False,
            "error": str(e)
        }), 500


@whatsapp_bp.route('/enviar-mensagem', methods=['POST'])
@login_required
def enviar_mensagem():
    """Envia uma mensagem de texto"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        data = request.get_json()

        telefone = data.get('telefone') or data.get('numero')
        mensagem = data.get('mensagem') or data.get('message')

        if not telefone or not mensagem:
            logger.warning("[WHATSAPP] Telefone ou mensagem não fornecidos")
            return jsonify({
                'success': False,
                'error': 'Telefone e mensagem são obrigatórios'
            }), 400

        logger.info(f"[WHATSAPP] Enviando mensagem para {telefone}")

        result = whatsapp_service.enviar_mensagem(telefone, mensagem)

        if result.get('success'):
            logger.info(f"[WHATSAPP] Mensagem enviada com sucesso para {telefone}")
            return jsonify(result), 200
        else:
            logger.error(f"[WHATSAPP] Falha ao enviar mensagem: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro ao enviar mensagem: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@whatsapp_bp.route('/enviar-pdf', methods=['POST'])
@login_required
def enviar_pdf():
    """Envia um PDF para um número"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        data = request.get_json()

        telefone = data.get('telefone') or data.get('numero')
        pdf_path = data.get('pdf_path') or data.get('filePath')
        caption = data.get('caption') or data.get('legenda', '')
        filename = data.get('filename', 'documento.pdf')

        if not telefone or not pdf_path:
            logger.warning("[WHATSAPP] Telefone ou PDF path não fornecidos")
            return jsonify({
                'success': False,
                'error': 'Telefone e PDF são obrigatórios'
            }), 400

        logger.info(f"[WHATSAPP] Enviando PDF para {telefone}: {pdf_path}")

        result = whatsapp_service.enviar_pdf(telefone, pdf_path, caption, filename)

        if result.get('success'):
            logger.info(f"[WHATSAPP] PDF enviado com sucesso para {telefone}")
            return jsonify(result), 200
        else:
            logger.error(f"[WHATSAPP] Falha ao enviar PDF: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro ao enviar PDF: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@whatsapp_bp.route('/enviar-boleto', methods=['POST'])
@login_required
def enviar_boleto():
    """Envia mensagem + PDF do boleto com delay anti-bloqueio"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        data = request.get_json()

        telefone = data.get('telefone') or data.get('numero')
        pdf_path = data.get('pdf_path')
        mensagem = data.get('mensagem') or data.get('mensagem_antibloqueio')
        delay_min = data.get('delay_min', 3)
        delay_max = data.get('delay_max', 7)

        if not telefone or not pdf_path or not mensagem:
            logger.warning("[WHATSAPP] Dados incompletos para envio de boleto")
            return jsonify({
                'success': False,
                'error': 'Telefone, PDF e mensagem são obrigatórios'
            }), 400

        logger.info(f"[WHATSAPP] Enviando boleto completo para {telefone}")

        result = whatsapp_service.enviar_boleto_completo(
            telefone, pdf_path, mensagem, delay_min, delay_max
        )

        if result.get('success'):
            logger.info(f"[WHATSAPP] Boleto enviado com sucesso para {telefone}")
            return jsonify(result), 200
        else:
            logger.error(f"[WHATSAPP] Falha ao enviar boleto: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro ao enviar boleto: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@whatsapp_bp.route('/desconectar', methods=['POST'])
@login_required
def desconectar():
    """Desconecta do WhatsApp"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        logger.info(f"[WHATSAPP] Cliente {cliente_nexus_id} desconectando")

        result = whatsapp_service.desconectar()

        if result.get('success'):
            logger.info("[WHATSAPP] Desconectado com sucesso")
            return jsonify({
                'success': True,
                'message': 'WhatsApp desconectado com sucesso'
            }), 200
        else:
            logger.error(f"[WHATSAPP] Erro ao desconectar: {result.get('error')}")
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro ao desconectar: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@whatsapp_bp.route('/teste', methods=['POST'])
@login_required
def testar_envio():
    """
    Endpoint de teste para enviar mensagem rápida
    """
    try:
        data = request.get_json()
        telefone = data.get('telefone')

        if not telefone:
            return jsonify({
                'success': False,
                'error': 'Telefone é obrigatório'
            }), 400

        # Verifica se está conectado
        status = whatsapp_service.verificar_status()
        if not status.get('connected'):
            return jsonify({
                'success': False,
                'error': 'WhatsApp não está conectado. Conecte-se primeiro.'
            }), 400

        mensagem_teste = "🤖 Teste de envio - Nexus CRM\n\nSe você recebeu esta mensagem, o WhatsApp está funcionando corretamente!"

        result = whatsapp_service.enviar_mensagem(telefone, mensagem_teste)
        return jsonify(result)

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro ao enviar teste: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Rotas antigas mantidas para compatibilidade
@whatsapp_bp.route('/qr-code', methods=['GET'])
@login_required
def get_qr_code():
    """Alias para /qr (compatibilidade)"""
    return obter_qr()


@whatsapp_bp.route('/disparo-massa', methods=['POST'])
@login_required
def disparo_massa():
    """Envia mensagens em massa (TODO: implementar com Baileys)"""
    try:
        cliente_nexus_id = session.get('cliente_nexus_id')
        data = request.get_json()

        destinatarios = data.get('destinatarios', [])

        if not destinatarios:
            return jsonify({'success': False, 'error': 'Lista de destinatários vazia'}), 400

        logger.info(f"[WHATSAPP] Iniciando disparo em massa para {len(destinatarios)} destinatários")

        # TODO: Implementar com Baileys
        return jsonify({
            'success': False,
            'error': 'Disparo em massa ainda não implementado com Baileys'
        }), 501

    except Exception as e:
        logger.error(f"[WHATSAPP] Erro no disparo em massa: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
