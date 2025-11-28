#!/usr/bin/env python3
"""Script para executar SQL de criação das tabelas do Portal Consórcio"""

import psycopg2
import sys

# Configurações do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'nexus_crm',
    'user': 'nexus_user',
    'password': 'nexus2025'
}

def executar_sql():
    try:
        # Conectar ao banco
        print("Conectando ao PostgreSQL...")
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            client_encoding='UTF8'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Ler arquivo SQL
        print("Lendo arquivo SQL...")
        with open('backend/sql/criar_tabelas_portal.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Executar SQL
        print("Executando comandos SQL...")
        cursor.execute(sql_script)

        print("\n[OK] Tabelas criadas com sucesso!")
        print("\n[INFO] Verificando tabelas criadas:")

        # Verificar tabelas
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('clientes_finais', 'boletos', 'usuarios_portal', 'pastas_digitais', 'historico_disparos', 'configuracoes_automacao')
            ORDER BY table_name
        """)

        tabelas = cursor.fetchall()
        for tabela in tabelas:
            print(f"  [OK] {tabela[0]}")

        # Verificar dados iniciais
        print("\n[INFO] Dados iniciais:")

        cursor.execute("SELECT COUNT(*) FROM usuarios_portal")
        usuarios = cursor.fetchone()[0]
        print(f"  Usuarios Portal: {usuarios}")

        cursor.execute("SELECT COUNT(*) FROM clientes_finais")
        clientes = cursor.fetchone()[0]
        print(f"  Clientes Finais: {clientes}")

        cursor.execute("SELECT COUNT(*) FROM configuracoes_automacao")
        configs = cursor.fetchone()[0]
        print(f"  Configuracoes: {configs}")

        cursor.close()
        conn.close()

        print("\n[SUCCESS] Script executado com sucesso!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Erro ao executar SQL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = executar_sql()
    sys.exit(0 if success else 1)
