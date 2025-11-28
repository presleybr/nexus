"""
Módulo de Services - Exporta todos os serviços do sistema
"""

from .pdf_generator import BoletoGenerator, criar_boleto_exemplo
from .whatsapp_service import WhatsAppService, whatsapp_service
from .webscraping import CampusConsorcioScraper, campus_scraper
from .automation_service import AutomationService, automation_service

__all__ = [
    'BoletoGenerator',
    'criar_boleto_exemplo',
    'WhatsAppService',
    'whatsapp_service',
    'CampusConsorcioScraper',
    'campus_scraper',
    'AutomationService',
    'automation_service',
]
