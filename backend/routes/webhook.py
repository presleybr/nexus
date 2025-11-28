"""
Rotas de Webhook - Recebe notificações do WPPConnect
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import log_sistema
from models.database import db

webhook_bp = Blueprint('webhook', __name__, url_prefix='/api/webhook')


@webhook_bp.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Recebe notificações do WPPConnect sobre status da conexão,
    mensagens recebidas, etc.
    """
    try:
        data = request.get_json()

        # Log do evento recebido
        event_type = data.get('event', 'unknown')

        # Eventos importantes para logar
        if event_type in ['qrcode', 'connection', 'disconnected', 'message']:
            log_sistema('info', f'Webhook WPPConnect: {event_type}',
                       'webhook', {'data': data})

        # Atualiza status da sessão se for evento de conexão
        if event_type == 'connection' or event_type == 'qrcode':
            session_name = data.get('session')
            phone = data.get('phone')

            if session_name and phone:
                # Atualiza status no banco se necessário
                try:
                    db.execute_update("""
                        UPDATE whatsapp_sessions
                        SET status = %s, phone_number = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE session_name = %s
                    """, ('connected' if event_type == 'connection' else 'waiting',
                          phone, session_name))
                except Exception as e:
                    # Se a tabela não existir, apenas loga
                    log_sistema('warning', f'Erro ao atualizar sessão: {str(e)}',
                               'webhook')

        # Sempre retorna sucesso para o WPPConnect
        return jsonify({
            'success': True,
            'message': 'Webhook recebido'
        }), 200

    except Exception as e:
        # Loga o erro mas retorna sucesso para não bloquear o WPPConnect
        log_sistema('error', f'Erro no webhook: {str(e)}',
                   'webhook', {'error': str(e)})

        return jsonify({
            'success': True,
            'message': 'Webhook recebido com erro'
        }), 200
