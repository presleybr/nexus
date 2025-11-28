"""
Testa conexão com PostgreSQL usando as credenciais corretas
Uso: python testar_conexao_db.py
"""

import sys
from pathlib import Path

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    print("[ERRO] psycopg nao instalado!")
    print("Execute: pip install psycopg psycopg-binary")
    sys.exit(1)

from db_config import get_connection_params, get_connection_info, DB_HOST, DB_PORT, DB_NAME, DB_USER


def main():
    print()
    print("=" * 80)
    print("TESTE DE CONEXAO - POSTGRESQL")
    print("=" * 80)
    print()

    print("Configuracoes do banco:")
    print(get_connection_info())

    print("[*] Tentando conectar...")

    conn_params = get_connection_params()

    try:
        conn = psycopg.connect(**conn_params, row_factory=dict_row)
        print("[OK] Conectado com sucesso!")
        print()

        # Testar query
        print("[*] Testando query...")
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()
            print(f"[OK] PostgreSQL versao: {version['version'][:60]}...")

        # Listar tabelas
        print()
        print("[*] Listando tabelas do banco...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tabelas = cur.fetchall()

            if tabelas:
                print(f"[OK] Encontradas {len(tabelas)} tabelas:")
                for t in tabelas:
                    print(f"  - {t['table_name']}")
            else:
                print("[INFO] Nenhuma tabela encontrada (banco vazio)")

        conn.close()

        print()
        print("=" * 80)
        print("TESTE CONCLUIDO COM SUCESSO!")
        print("=" * 80)
        print()
        print("A conexao esta funcionando corretamente.")
        print("Voce pode executar agora: python executar_sql.py")
        print()

        return 0

    except psycopg.OperationalError as e:
        print(f"[ERRO] Falha ao conectar: {e}")
        print()
        print("Verifique:")
        print("  1. PostgreSQL esta rodando?")
        print(f"  2. Porta {DB_PORT} esta correta?")
        print(f"  3. Banco '{DB_NAME}' existe?")
        print(f"  4. Usuario '{DB_USER}' tem permissao?")
        print("  5. Senha em db_config.py esta correta?")
        print()
        return 1

    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
