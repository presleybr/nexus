"""
Aplicação Principal Flask - Sistema CRM Nexus
Aqui seu tempo vale ouro
"""

from flask import Flask, render_template, session, send_from_directory
from flask_session import Session
from flask_cors import CORS
import os
import sys

# Adiciona o diretório backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import Database, log_sistema
from routes import auth_bp, crm_bp, whatsapp_bp, automation_bp, webhook_bp
from routes.crm_disparo_individual import disparo_individual_bp
from routes.whatsapp_baileys import whatsapp_baileys_bp
from routes.whatsapp_wppconnect import whatsapp_wppconnect_bp
from routes.portal_consorcio import register_portal_routes
from routes.boletos_modelo import register_boletos_modelo_routes
from routes.automation_canopus import automation_canopus_bp


def create_app():
    """Factory function para criar a aplicação Flask"""

    app = Flask(
        __name__,
        template_folder=Config.TEMPLATES_DIR,
        static_folder=Config.STATIC_DIR
    )

    # Configurações
    app.config.from_object(Config)

    # Inicializa extensões
    CORS(app, supports_credentials=True)
    Session(app)

    # Inicializa pool de conexões do banco
    Database.initialize_pool()

    # Cria diretórios necessários
    Config.init_directories()

    # Registra blueprints (rotas)
    app.register_blueprint(auth_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(disparo_individual_bp)  # Disparo individual para teste
    app.register_blueprint(whatsapp_bp)
    app.register_blueprint(whatsapp_baileys_bp)
    app.register_blueprint(whatsapp_wppconnect_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(automation_canopus_bp)  # Automação Canopus
    app.register_blueprint(webhook_bp)

    # Registra rotas do Portal Consórcio
    register_portal_routes(app)

    # Registra rotas de Boletos Modelo
    register_boletos_modelo_routes(app)

    # Inicializa o scheduler de automação
    from services.automation_scheduler import automation_scheduler
    automation_scheduler.iniciar()

    # =====================
    # ROTAS DE PÁGINAS HTML
    # =====================

    @app.route('/')
    def index():
        """Página inicial (landing page)"""
        return render_template('landing.html')

    @app.route('/login-cliente')
    def login_cliente():
        """Página de login do cliente"""
        return render_template('login-cliente.html')

    @app.route('/login-admin')
    def login_admin():
        """Página de login do admin"""
        return render_template('login-admin.html')

    @app.route('/crm/dashboard')
    def crm_dashboard():
        """Dashboard do cliente CRM"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/dashboard.html')

    @app.route('/crm/cadastro-clientes')
    def crm_cadastro():
        """Cadastro de clientes"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/cadastro-clientes.html')

    @app.route('/crm/whatsapp')
    def crm_whatsapp():
        """Conexão WhatsApp"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/whatsapp-wppconnect.html')

    @app.route('/crm/whatsapp-baileys')
    def crm_whatsapp_baileys():
        """Conexão WhatsApp Baileys"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/whatsapp-baileys.html')

    @app.route('/crm/disparos')
    def crm_disparos():
        """Disparos de boletos"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/disparos.html')

    @app.route('/crm/monitoramento')
    def crm_monitoramento():
        """Monitoramento do sistema"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/monitoramento.html')

    @app.route('/crm/graficos')
    def crm_graficos():
        """Gráficos e relatórios"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/graficos.html')

    @app.route('/crm/automacao-canopus')
    def crm_automacao_canopus():
        """Automação Canopus - Download e importação de boletos"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/automacao-canopus.html')

    @app.route('/crm/cliente-debitos')
    def crm_cliente_debitos():
        """Débitos de um cliente específico"""
        if 'usuario_id' not in session:
            return render_template('login-cliente.html')
        return render_template('crm-cliente/cliente-debitos.html')

    @app.route('/admin/dashboard')
    def admin_dashboard():
        """Dashboard administrativo"""
        if 'usuario_id' not in session or session.get('tipo') != 'admin':
            return render_template('login-admin.html')
        return render_template('crm-admin/dashboard-admin.html')

    # =====================
    # ROTAS DE API AUXILIARES
    # =====================

    @app.route('/api/status', methods=['GET'])
    def api_status():
        """Status do sistema"""
        from models import fetch_one

        status = fetch_one("SELECT * FROM status_sistema WHERE id = 1")

        return {
            'status': 'online',
            'versao': Config.FLASK_ENV,
            'sistema': status if status else {}
        }

    @app.route('/api/logs', methods=['GET'])
    def api_logs():
        """Retorna logs recentes do sistema"""
        if 'usuario_id' not in session:
            return {'erro': 'Não autenticado'}, 401

        from models import execute_query

        query = """
            SELECT * FROM logs_sistema
            ORDER BY data_hora DESC
            LIMIT 50
        """

        logs = execute_query(query, fetch=True)

        return {'logs': logs}

    # =====================
    # HANDLERS DE ERRO
    # =====================

    @app.errorhandler(404)
    def not_found(error):
        """Página 404"""
        return render_template('landing.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Erro 500"""
        log_sistema('error', f'Erro 500: {str(error)}', 'sistema')
        return {'erro': 'Erro interno do servidor'}, 500

    # =====================
    # EVENTO DE SHUTDOWN
    # =====================

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Fecha conexões do banco ao encerrar"""
        pass  # O pool gerencia automaticamente

    # Registra shutdown do scheduler
    import atexit
    from services.automation_scheduler import automation_scheduler

    def shutdown_scheduler():
        automation_scheduler.parar()

    atexit.register(shutdown_scheduler)

    print("[OK] Aplicacao Flask inicializada com sucesso")
    print(f"[INFO] Templates: {Config.TEMPLATES_DIR}")
    print(f"[INFO] Static: {Config.STATIC_DIR}")

    return app


# Cria a aplicação
app = create_app()


if __name__ == '__main__':
    print("=" * 60)
    print("NEXUS CRM - SISTEMA DE AUTOMACAO DE BOLETOS")
    print("   Aqui seu tempo vale ouro")
    print("=" * 60)
    print(f"Servidor rodando em: http://localhost:{Config.FLASK_PORT}")
    print(f"Banco de dados: {Config.DB_NAME}")
    print("=" * 60)

    # Inicia o servidor
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=(Config.FLASK_ENV == 'development'),
        use_reloader=False  # Desabilitar auto-reload para não matar threads de automação
    )
