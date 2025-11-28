"""
Script para executar migrações do banco de dados
"""
import psycopg
from pathlib import Path
import sys
import os

# Adiciona o diretório backend ao path para importar Config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from config import Config

def run_migration(migration_file: str):
    """
    Executa um arquivo de migração SQL

    Args:
        migration_file: Caminho para o arquivo .sql
    """
    try:
        # Conectar ao banco de dados usando Config
        conninfo = f"host={Config.DB_HOST} port={Config.DB_PORT} dbname={Config.DB_NAME} user={Config.DB_USER} password={Config.DB_PASSWORD}"
        conn = psycopg.connect(conninfo)

        # Ler o arquivo SQL
        migration_path = Path(migration_file)
        if not migration_path.exists():
            print(f"[ERRO] Arquivo nao encontrado: {migration_file}")
            return False

        sql_content = migration_path.read_text(encoding='utf-8')

        print(f"[INFO] Executando migracao: {migration_path.name}")
        print(f"{'='*60}")

        # Executar a migração
        with conn.cursor() as cur:
            cur.execute(sql_content)
            conn.commit()

        print(f"[SUCESSO] Migracao executada com sucesso!")

        # Verificar se as colunas foram criadas
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'consultores'
                AND column_name IN ('link_planilha_drive', 'ultima_atualizacao_planilha')
                ORDER BY column_name
            """)
            columns = cur.fetchall()

            if columns:
                print(f"\n[INFO] Colunas adicionadas:")
                for col_name, col_type in columns:
                    print(f"   + {col_name} ({col_type})")
            else:
                print(f"\n[AVISO] Colunas nao encontradas apos migracao")

        conn.close()
        return True

    except Exception as e:
        print(f"[ERRO] Erro ao executar migracao: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python run_migration.py <arquivo_migracao.sql>")
        print("\nExemplo:")
        print("  python run_migration.py migrations/005_add_link_planilha_consultores.sql")
        sys.exit(1)

    migration_file = sys.argv[1]
    success = run_migration(migration_file)
    sys.exit(0 if success else 1)
