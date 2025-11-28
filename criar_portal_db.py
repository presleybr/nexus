#!/usr/bin/env python3
"""Script direto para criar tabelas Portal usando psycopg2"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'nexus_crm',
    'user': 'nexus_user',
    'password': 'nexus2025'
}

def criar_tabelas():
    conn = None
    try:
        print("[INFO] Conectando ao banco...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print("[INFO] Lendo arquivo SQL...")
        with open('backend/sql/criar_tabelas_portal.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("[INFO] Executando SQL...")

        # Executar todo o script de uma vez
        cursor.execute(sql_script)
        conn.commit()

        print("\n[OK] SQL executado com sucesso!")

        # Verificar tabelas
        print("\n[INFO] Verificando tabelas criadas:")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('clientes_finais', 'boletos', 'usuarios_portal',
                               'pastas_digitais', 'historico_disparos', 'configuracoes_automacao')
            ORDER BY table_name
        """)

        for row in cursor.fetchall():
            print(f"  [OK] {row['table_name']}")

        # Verificar dados
        print("\n[INFO] Dados iniciais:")

        cursor.execute("SELECT COUNT(*) as total FROM usuarios_portal")
        print(f"  Usuarios Portal: {cursor.fetchone()['total']}")

        cursor.execute("SELECT COUNT(*) as total FROM clientes_finais")
        print(f"  Clientes Finais: {cursor.fetchone()['total']}")

        cursor.execute("SELECT COUNT(*) as total FROM configuracoes_automacao")
        print(f"  Configuracoes: {cursor.fetchone()['total']}")

        cursor.close()
        conn.close()

        print("\n[SUCCESS] Portal Consorcio - Tabelas criadas!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys
    success = criar_tabelas()
    sys.exit(0 if success else 1)
