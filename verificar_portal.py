#!/usr/bin/env python3
"""Script para verificar tabelas do Portal"""

import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import execute_query, fetch_one, Database

def verificar():
    try:
        # Inicializar pool de conexões
        print("[INFO] Inicializando conexão com banco...")
        Database.initialize_pool()

        # Verificar tabelas
        print("\n[INFO] Verificando tabelas Portal:")

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

        # Verificar dados
        print("\n[INFO] Dados:")

        usuarios_result = fetch_one("SELECT COUNT(*) as total FROM usuarios_portal")
        print(f"\n  Usuarios Portal: {usuarios_result['total']}")

        usuarios = execute_query("SELECT id, email, nome_completo, nivel_acesso FROM usuarios_portal", fetch=True)
        for user in usuarios:
            print(f"    ID: {user['id']}, Email: {user['email']}, Nome: {user['nome_completo']}, Nivel: {user['nivel_acesso']}")

        clientes_result = fetch_one("SELECT COUNT(*) as total FROM clientes_finais")
        print(f"\n  Clientes Finais: {clientes_result['total']}")

        boletos_result = fetch_one("SELECT COUNT(*) as total FROM boletos")
        print(f"  Boletos: {boletos_result['total']}")

        print("\n[SUCCESS] Verificação completa!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        Database.close_all_connections()

if __name__ == '__main__':
    success = verificar()
    sys.exit(0 if success else 1)
