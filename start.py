"""
Script Principal de Inicialização do Sistema CRM Nexus
Verifica banco, inicializa tabelas, popula dados e inicia o Flask
"""

import sys
import os
import subprocess

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adiciona o backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))


def verificar_postgres():
    """Verifica se o PostgreSQL está rodando"""
    print("🔍 Verificando PostgreSQL...")

    try:
        import psycopg
        from backend.config import Config

        conninfo = f"host={Config.DB_HOST} port={Config.DB_PORT} dbname=postgres user={Config.DB_USER} password={Config.DB_PASSWORD}"

        with psycopg.connect(conninfo, autocommit=True) as conn:
            print("✅ PostgreSQL está rodando")
            return True

    except Exception as e:
        print(f"❌ PostgreSQL não está acessível: {e}")
        print("\n💡 Certifique-se de que:")
        print(f"   1. PostgreSQL está instalado")
        print(f"   2. PostgreSQL está rodando na porta {os.getenv('DB_PORT', '5434')}")
        print(f"   3. As credenciais no arquivo .env estão corretas")
        return False


def inicializar_banco_e_dados():
    """Inicializa o banco de dados e dados fake"""

    from backend.models.database import check_database_exists, check_tables_exist, Database

    print("\n🗄️  Verificando banco de dados...")

    # 1. Verifica e cria o banco se necessário
    if not check_database_exists():
        print("❌ Banco de dados não encontrado")
        print("📝 Executando init_db.py...")

        result = subprocess.run(
            [sys.executable, 'database/init_db.py'],
            cwd=os.path.dirname(__file__)
        )

        if result.returncode != 0:
            print("❌ Erro ao inicializar banco de dados")
            return False
    else:
        print("✅ Banco de dados existe")

    # 2. Inicializa pool
    try:
        Database.initialize_pool()
    except Exception as e:
        print(f"⚠️  Aviso ao inicializar pool: {e}")

    # 3. Verifica e cria tabelas se necessário
    if not check_tables_exist():
        print("❌ Tabelas não encontradas")
        print("📝 Criando tabelas...")

        from backend.models.database import init_schema

        try:
            init_schema()
            print("✅ Tabelas criadas com sucesso")

            # Popular automaticamente com dados fake na primeira inicialização
            print("\n" + "=" * 60)
            print("🌱 Populando com dados fake para testes...")
            result = subprocess.run(
                [sys.executable, 'database/seed_data.py'],
                cwd=os.path.dirname(__file__)
            )

            if result.returncode != 0:
                print("⚠️  Erro ao popular dados, mas o sistema pode continuar")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            return False
    else:
        print("✅ Tabelas existem")

    return True


def verificar_wppconnect():
    """Verifica se WPPConnect Server está rodando"""
    print("\n📱 Verificando WPPConnect Server...")

    try:
        import requests
        response = requests.get('http://localhost:3001', timeout=3)
        data = response.json()
        if data.get('status') == 'running':
            print("✅ WPPConnect Server está rodando em http://localhost:3001")
            if data.get('connected'):
                print(f"   📱 WhatsApp conectado: {data.get('phone')}")
            else:
                print("   ⚠️  WhatsApp ainda não conectado (conecte via interface web)")
            return True
    except Exception as e:
        print("⚠️  WPPConnect Server não está rodando")
        print("\n💡 Para iniciar o WPPConnect Server:")
        print("   1. Abra um novo terminal")
        print("   2. Execute: cd D:\\Nexus\\wppconnect-server")
        print("   3. Execute: start.bat")
        print("\n   Ou use o script: iniciar.bat (inicia tudo junto)")
        print("\n⚠️  Funcionalidades WhatsApp estarão desabilitadas")
        return False


def iniciar_flask():
    """Inicia o servidor Flask"""
    print("\n" + "=" * 60)
    print("🚀 INICIANDO SERVIDOR FLASK")
    print("=" * 60)

    from backend.app import app
    from backend.config import Config

    print(f"\n🌐 Servidor disponível em: http://localhost:{Config.FLASK_PORT}")
    print(f"🗄️  Banco de dados: {Config.DB_NAME} (porta {Config.DB_PORT})")
    print(f"📱 WPPConnect Server: http://localhost:3001")
    print("📝 Pressione CTRL+C para parar o servidor\n")

    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=(Config.FLASK_ENV == 'development'),
        use_reloader=False  # Desabilitar auto-reload para não matar threads de automação
    )


def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 NEXUS CRM - SISTEMA DE AUTOMAÇÃO DE BOLETOS")
    print("   Aqui seu tempo vale ouro")
    print("=" * 60)

    # Passo 1: Verificar PostgreSQL
    if not verificar_postgres():
        print("\n❌ ERRO: PostgreSQL não está acessível")
        print("   Configure o PostgreSQL e tente novamente")
        sys.exit(1)

    # Passo 2: Inicializar banco e dados
    if not inicializar_banco_e_dados():
        print("\n❌ ERRO: Falha ao inicializar banco de dados")
        sys.exit(1)

    # Passo 3: Verificar WPPConnect Server
    verificar_wppconnect()
    # Continua mesmo que WPPConnect não esteja rodando

    # Passo 4: Iniciar Flask
    try:
        iniciar_flask()
    except KeyboardInterrupt:
        print("\n\n👋 Servidor encerrado pelo usuário")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRO ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
