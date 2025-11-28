"""
Script para verificar tabelas de clientes
"""
import psycopg

# Configurações do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'dbname': 'nexus_crm',
    'user': 'postgres',
    'password': 'nexus2025'
}

def check_tables():
    """Verifica tabelas relacionadas a clientes"""
    try:
        conn_string = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} password={DB_CONFIG['password']}"

        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Listar todas as tabelas
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                tables = cur.fetchall()

                print("=" * 80)
                print("TABELAS NO BANCO")
                print("=" * 80)
                for t in tables:
                    print(f"- {t[0]}")

                # Verificar se existe tabela de clientes/débitos
                print("\n" + "=" * 80)
                print("PROCURANDO TABELAS DE CLIENTES/DEBITOS")
                print("=" * 80)

                for table_name in ['clientes', 'debitos', 'cliente_debitos', 'boletos']:
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                    columns = cur.fetchall()

                    if columns:
                        print(f"\nTabela: {table_name}")
                        print("-" * 80)
                        for col in columns:
                            print(f"  {col[0]:30} | {col[1]:25} | NULL: {col[2]}")

    except Exception as e:
        print(f"[ERRO] {e}")

if __name__ == '__main__':
    check_tables()
