"""
Configurações do Sistema CRM Nexus
Gerencia todas as variáveis de ambiente e configurações da aplicação
"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Classe de configuração centralizada"""

    # Configurações do Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'nexus-crm-secret-key-2024')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_PORT = int(os.getenv('PORT', os.getenv('FLASK_PORT', 5000)))  # Render usa PORT

    # Configurações do Banco de Dados PostgreSQL
    # PRIORIZA DATABASE_URL do Render.com, senão usa vars individuais
    DATABASE_URL = os.getenv('DATABASE_URL')

    if DATABASE_URL:
        # Render fornece DATABASE_URL completa - extrair componentes se necessário
        # Formato: postgresql://user:pass@host:port/dbname
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if match:
            DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = match.groups()
            DB_PORT = int(DB_PORT)
        else:
            # Fallback se regex falhar
            DB_HOST = 'localhost'
            DB_PORT = 5432
            DB_NAME = 'nexus_crm'
            DB_USER = 'postgres'
            DB_PASSWORD = 'postgres'
    else:
        # Desenvolvimento local - usar variáveis individuais
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = int(os.getenv('DB_PORT', 5432))
        DB_NAME = os.getenv('DB_NAME', 'nexus_crm')
        DB_USER = os.getenv('DB_USER', 'postgres')
        DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Configurações de Automação
    AUTOMATION_ENABLED = os.getenv('AUTOMATION_ENABLED', 'true').lower() == 'true'
    DISPARO_INTERVAL_SECONDS = int(os.getenv('DISPARO_INTERVAL_SECONDS', 5))
    BOLETO_DIR = os.getenv('BOLETO_DIR', 'boletos')

    # Configurações WhatsApp
    WHATSAPP_SESSION_DIR = os.getenv('WHATSAPP_SESSION_DIR', 'whatsapp_sessions')

    # Diretórios do projeto
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
    TEMPLATES_DIR = os.path.join(FRONTEND_DIR, 'templates')
    STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')
    BOLETO_PATH = os.path.join(BASE_DIR, BOLETO_DIR)
    WHATSAPP_PATH = os.path.join(BASE_DIR, WHATSAPP_SESSION_DIR)

    # Configurações de sessão
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = False  # Desabilitado para evitar erro com bytes/string
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora

    @staticmethod
    def init_directories():
        """Cria os diretórios necessários se não existirem"""
        directories = [
            Config.BOLETO_PATH,
            Config.WHATSAPP_PATH,
            os.path.join(Config.BASE_DIR, 'logs')
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
