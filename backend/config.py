"""
Configurações do Sistema CRM Nexus
Gerencia todas as variáveis de ambiente e configurações da aplicação
"""

import os
from dotenv import load_dotenv
from urllib.parse import urlparse

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
        # Render fornece DATABASE_URL completa - usar urlparse para extrair componentes
        # Formato: postgresql://user:pass@host:port/dbname
        try:
            parsed = urlparse(DATABASE_URL)
            DB_HOST = parsed.hostname or 'localhost'
            DB_PORT = parsed.port or 5432
            DB_NAME = parsed.path.lstrip('/') or 'nexus_crm'
            DB_USER = parsed.username or 'postgres'
            DB_PASSWORD = parsed.password or 'postgres'
            print(f"[CONFIG] DATABASE_URL detectada - Host: {DB_HOST}:{DB_PORT} DB: {DB_NAME}")
        except Exception as e:
            # Fallback se parsing falhar
            print(f"[CONFIG] ⚠️ Erro ao fazer parse de DATABASE_URL: {e}")
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
        print(f"[CONFIG] Usando configuração local - Host: {DB_HOST}:{DB_PORT} DB: {DB_NAME}")

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
