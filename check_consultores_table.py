"""
Script para verificar a estrutura da tabela consultores
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

def check_table():
    """Verifica a estrutura da tabela consultores"""
    try:
        conn_string = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} password={DB_CONFIG['password']}"

        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Verificar estrutura da tabela
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'consultores'
                    ORDER BY ordinal_position
                """)
                columns = cur.fetchall()

                print("=" * 80)
                print("ESTRUTURA DA TABELA CONSULTORES")
                print("=" * 80)
                for col in columns:
                    print(f"{col[0]:20} | {col[1]:20} | NULL: {col[2]:3} | Default: {col[3]}")

                print("\n" + "=" * 80)
                print("CONSTRAINTS")
                print("=" * 80)
                cur.execute("""
                    SELECT conname, pg_get_constraintdef(oid)
                    FROM pg_constraint
                    WHERE conrelid = 'consultores'::regclass
                """)
                constraints = cur.fetchall()
                for c in constraints:
                    print(f"{c[0]}: {c[1]}")

    except Exception as e:
        print(f"[ERRO] {e}")

if __name__ == '__main__':
    check_table()
