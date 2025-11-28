#!/usr/bin/env python3
"""Script para criar tabelas do Portal usando a infraestrutura existente"""

import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import execute_query, fetch_one, Database

def criar_tabelas():
    try:
        # Inicializar pool de conexões
        print("[INFO] Inicializando conexão com banco...")
        Database.initialize_pool()

        # Ler arquivo SQL
        print("[INFO] Lendo arquivo SQL...")
        with open('backend/sql/criar_tabelas_portal.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Executar SQL
        print("[INFO] Executando comandos SQL...")
        execute_query(sql_script)

        print("\n[OK] Tabelas criadas com sucesso!")
        print("\n[INFO] Verificando tabelas criadas:")

        # Verificar tabelas
        tabelas_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('clientes_finais', 'boletos', 'usuarios_portal', 'pastas_digitais', 'historico_disparos', 'configuracoes_automacao')
            ORDER BY table_name
        """
        tabelas = execute_query(tabelas_query, fetch=True)

        for tabela in tabelas:
            print(f"  [OK] {tabela['table_name']}")

        # Verificar dados iniciais
        print("\n[INFO] Dados iniciais:")

        usuarios_result = fetch_one("SELECT COUNT(*) as total FROM usuarios_portal")
        print(f"  Usuarios Portal: {usuarios_result['total']}")

        usuarios_emails = execute_query("SELECT email FROM usuarios_portal", fetch=True)
        for user in usuarios_emails:
            print(f"    - {user['email']}")

        clientes_result = fetch_one("SELECT COUNT(*) as total FROM clientes_finais")
        print(f"  Clientes Finais: {clientes_result['total']}")

        print("\n[SUCCESS] Script executado com sucesso!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Erro ao executar SQL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        Database.close_all_connections()

if __name__ == '__main__':
    success = criar_tabelas()
    sys.exit(0 if success else 1)
