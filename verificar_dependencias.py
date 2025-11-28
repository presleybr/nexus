#!/usr/bin/env python3
"""
Verifica se todas as dependências do Nexus CRM estão instaladas
Aqui seu tempo vale ouro
"""

import sys
import subprocess


def verificar_modulo(modulo: str, nome_display: str = None) -> bool:
    """Tenta importar um módulo e retorna se teve sucesso"""
    if nome_display is None:
        nome_display = modulo

    try:
        __import__(modulo)
        print(f"✅ {nome_display}")
        return True
    except ImportError:
        print(f"❌ {nome_display} - NÃO INSTALADO")
        return False


def verificar_playwright_browsers() -> bool:
    """Verifica se os navegadores do Playwright estão instalados"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Tenta lançar chromium em modo headless
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("✅ Playwright Chromium")
        return True
    except Exception as e:
        print(f"❌ Playwright Chromium - NÃO INSTALADO")
        print(f"   Erro: {str(e)}")
        return False


def verificar_postgres() -> bool:
    """Verifica se consegue conectar ao PostgreSQL"""
    try:
        import psycopg
        from psycopg.rows import dict_row

        # Tenta conectar
        conn_params = {
            'host': 'localhost',
            'port': 5434,
            'dbname': 'nexus_crm',
            'user': 'postgres',
            'password': 'postgres'
        }

        with psycopg.connect(**conn_params, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                versao = cur.fetchone()
                print(f"✅ PostgreSQL conectado - {versao['version'][:50]}...")
                return True
    except Exception as e:
        print(f"❌ PostgreSQL - NÃO CONECTADO")
        print(f"   Erro: {str(e)}")
        print(f"   Verifique se o PostgreSQL está rodando na porta 5434")
        return False


def verificar_node_npm() -> bool:
    """Verifica se Node.js e npm estão instalados"""
    try:
        # Verifica node
        result = subprocess.run(['node', '--version'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
            node_ok = True
        else:
            print("❌ Node.js - NÃO INSTALADO")
            node_ok = False

        # Verifica npm
        result = subprocess.run(['npm', '--version'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            print(f"✅ npm {result.stdout.strip()}")
            npm_ok = True
        else:
            print("❌ npm - NÃO INSTALADO")
            npm_ok = False

        return node_ok and npm_ok
    except Exception as e:
        print(f"❌ Node.js/npm - NÃO INSTALADO")
        print(f"   Erro: {str(e)}")
        return False


def verificar_wppconnect() -> bool:
    """Verifica se WPPConnect está instalado"""
    import os

    wpp_path = 'wppconnect-server'
    node_modules = os.path.join(wpp_path, 'node_modules')

    if os.path.exists(node_modules):
        print(f"✅ WPPConnect Server - node_modules encontrado")
        return True
    else:
        print(f"❌ WPPConnect Server - node_modules NÃO ENCONTRADO")
        print(f"   Execute: cd {wpp_path} && npm install")
        return False


def main():
    print("=" * 80)
    print("                    NEXUS CRM - VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("                           Aqui seu tempo vale ouro")
    print("=" * 80)
    print()

    falhas = []

    # =============================
    # MÓDULOS PYTHON ESSENCIAIS
    # =============================
    print("📦 VERIFICANDO MÓDULOS PYTHON ESSENCIAIS...")
    print()

    dependencias_python = [
        ('flask', 'Flask'),
        ('flask_session', 'Flask-Session'),
        ('flask_cors', 'Flask-CORS'),
        ('psycopg', 'psycopg[binary]'),
        ('psycopg_pool', 'psycopg-pool'),
        ('twilio', 'Twilio'),
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv'),
        ('reportlab', 'reportlab'),
        ('dateutil', 'python-dateutil'),
        ('werkzeug', 'werkzeug'),
        ('colorlog', 'colorlog'),
    ]

    for modulo, nome in dependencias_python:
        if not verificar_modulo(modulo, nome):
            falhas.append(nome)

    print()

    # =============================
    # MÓDULOS AUTOMAÇÃO CANOPUS
    # =============================
    print("🤖 VERIFICANDO MÓDULOS AUTOMAÇÃO CANOPUS...")
    print()

    dependencias_automacao = [
        ('playwright', 'Playwright'),
        ('pandas', 'Pandas'),
        ('openpyxl', 'openpyxl'),
        ('xlrd', 'xlrd'),
        ('cryptography', 'cryptography'),
        ('watchdog', 'watchdog'),
        ('bcrypt', 'bcrypt'),
    ]

    for modulo, nome in dependencias_automacao:
        if not verificar_modulo(modulo, nome):
            falhas.append(nome)

    print()

    # =============================
    # PLAYWRIGHT BROWSERS
    # =============================
    print("🌐 VERIFICANDO NAVEGADORES PLAYWRIGHT...")
    print()

    if not verificar_playwright_browsers():
        falhas.append('Playwright Chromium')

    print()

    # =============================
    # POSTGRESQL
    # =============================
    print("🐘 VERIFICANDO POSTGRESQL...")
    print()

    if not verificar_postgres():
        falhas.append('PostgreSQL')

    print()

    # =============================
    # NODE.JS E NPM
    # =============================
    print("📦 VERIFICANDO NODE.JS E NPM...")
    print()

    if not verificar_node_npm():
        falhas.append('Node.js/npm')

    print()

    # =============================
    # WPPCONNECT
    # =============================
    print("💬 VERIFICANDO WPPCONNECT...")
    print()

    if not verificar_wppconnect():
        falhas.append('WPPConnect')

    print()

    # =============================
    # RESULTADO FINAL
    # =============================
    print("=" * 80)

    if falhas:
        print(f"❌ VERIFICAÇÃO FALHOU - {len(falhas)} dependência(s) faltando:")
        print()
        for dep in falhas:
            print(f"   • {dep}")
        print()
        print("AÇÕES RECOMENDADAS:")
        print("   1. Execute: setup_canopus.bat")
        print("   2. Execute: cd wppconnect-server && npm install")
        print("   3. Verifique se PostgreSQL está rodando na porta 5434")
        print()
        print("=" * 80)
        return 1
    else:
        print("✅ TODAS AS DEPENDÊNCIAS INSTALADAS COM SUCESSO!")
        print()
        print("SISTEMA PRONTO PARA USO!")
        print()
        print("PRÓXIMOS PASSOS:")
        print("   1. Configure credenciais Canopus:")
        print("      cd automation\\canopus")
        print("      python gerenciar_credenciais.py --adicionar")
        print()
        print("   2. Coloque planilhas Excel em: D:\\Nexus\\planilhas\\")
        print()
        print("   3. Inicie o sistema:")
        print("      iniciar_menu.bat")
        print()
        print("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())
