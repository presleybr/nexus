#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica estrutura da tabela download_canopus
"""
import sys
import psycopg
from psycopg.rows import dict_row

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

print("=" * 80)
print("VERIFICAÇÃO DA TABELA download_canopus")
print("=" * 80)

try:
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()

    # Verificar se tabela existe
    print("\n🔍 Verificando se tabela downloads_canopus existe...")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'downloads_canopus'
        )
    """)

    existe = cur.fetchone()['exists']

    if not existe:
        print("❌ Tabela downloads_canopus NÃO EXISTE!")

        # Listar todas as tabelas disponíveis
        print("\n📋 Tabelas disponíveis no banco:")
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tabelas = cur.fetchall()
        for t in tabelas:
            print(f"   - {t['table_name']}")
    else:
        print("✅ Tabela downloads_canopus existe!")

        # Mostrar estrutura
        print("\n📋 Estrutura da tabela:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'downloads_canopus'
            ORDER BY ordinal_position
        """)
        colunas = cur.fetchall()

        for col in colunas:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"   - {col['column_name']}: {col['data_type']} {nullable} {default}")

        # Contar registros
        print("\n📊 Contando registros...")
        cur.execute("SELECT COUNT(*) as total FROM downloads_canopus")
        total = cur.fetchone()['total']
        print(f"✅ Total de registros: {total}")

        if total > 0:
            # Mostrar últimos registros
            print("\n📋 Últimos 5 registros:")
            cur.execute("""
                SELECT *
                FROM downloads_canopus
                ORDER BY id DESC
                LIMIT 5
            """)
            registros = cur.fetchall()

            for i, reg in enumerate(registros, 1):
                print(f"\n{i}. Registro ID: {reg['id']}")
                for key, value in reg.items():
                    if key != 'id':
                        print(f"   {key}: {value}")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ Verificação concluída!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
