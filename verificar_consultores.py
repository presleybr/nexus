#!/usr/bin/env python3
import psycopg

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

print("Colunas da tabela 'consultores':")
print("="*60)
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'consultores'
    ORDER BY ordinal_position
""")

for col in cur.fetchall():
    print(f"  {col[0]:<35} {col[1]:<25} NULL={col[2]}")

print("\n" + "="*60)
print("Verificando se link_planilha_drive existe:")
cur.execute("""
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_name = 'consultores'
    AND column_name = 'link_planilha_drive'
""")
existe = cur.fetchone()[0]
print(f"  Resultado: {'SIM' if existe > 0 else 'NAO'}")

cur.close()
conn.close()
