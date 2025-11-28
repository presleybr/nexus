"""
Módulo de Automação Canopus
Sistema integrado para download automatizado de boletos de consórcio
"""

__version__ = '1.0.0'
__author__ = 'Nexus CRM'
__description__ = 'Automação de download de boletos do sistema Canopus'

# Importar classes principais
from .canopus_config import CanopusConfig, PontoVenda, Consultor, ExcelColumns
from .excel_importer import ExcelImporter, ExcelMonitor, importar_planilha, importar_todas
from .canopus_automation import CanopusAutomation

# Exportar para uso externo
__all__ = [
    # Configuração
    'CanopusConfig',
    'PontoVenda',
    'Consultor',
    'ExcelColumns',

    # Importador Excel
    'ExcelImporter',
    'ExcelMonitor',
    'importar_planilha',
    'importar_todas',

    # Automação
    'CanopusAutomation',
]
