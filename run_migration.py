"""
Script para executar migration 004 - Adicionar CPF à tabela consultores
"""
import psycopg
import os

# Configurações do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'dbname': 'nexus_crm',
    'user': 'postgres',
    'password': 'nexus2025'
}

def run_migration():
    """Executa a migration 004"""
    migration_file = r'D:\Nexus\database\migrations\004_add_cpf_to_consultores.sql'

    try:
        # Ler o arquivo SQL
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Conectar ao banco
        conn_string = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} password={DB_CONFIG['password']}"

        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                print("[INFO] Executando migration 004...")
                cur.execute(sql)
                conn.commit()
                print("[OK] Migration 004 executada com sucesso!")

                # Verificar se a coluna foi adicionada
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'consultores'
                    AND column_name = 'cpf'
                """)
                result = cur.fetchone()

                if result:
                    print(f"[OK] Coluna CPF adicionada: {result[0]} ({result[1]})")
                else:
                    print("[!] Atencao: Coluna CPF nao encontrada apos migration")

    except Exception as e:
        print(f"[ERRO] Falha ao executar migration: {e}")
        return False

    return True

if __name__ == '__main__':
    print("=" * 60)
    print("NEXUS CRM - MIGRATION 004")
    print("Adicionando coluna CPF à tabela consultores")
    print("=" * 60)

    success = run_migration()

    if success:
        print("\n[OK] Migration concluída!")
    else:
        print("\n[ERRO] Migration falhou!")
