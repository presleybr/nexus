"""
Módulo de Routes - Exporta todos os blueprints
"""

from .auth import auth_bp, login_required, admin_required
from .crm import crm_bp
from .whatsapp import whatsapp_bp
from .automation import automation_bp
from .webhook import webhook_bp

__all__ = [
    'auth_bp',
    'crm_bp',
    'whatsapp_bp',
    'automation_bp',
    'webhook_bp',
    'login_required',
    'admin_required',
]
