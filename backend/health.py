"""
Rota de Health Check para Render.com
Verifica se o serviço está funcionando corretamente
"""

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint para Render.com
    Retorna status 200 se o serviço está funcionando
    """
    return jsonify({
        "status": "healthy",
        "service": "nexus-crm",
        "message": "Service is running"
    }), 200
