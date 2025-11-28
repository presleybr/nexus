#!/usr/bin/env python3
"""
Adiciona coluna ponto_venda na tabela clientes_finais
"""
import psycopg

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

print("Conectando ao banco do Render...")
conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

# Verificar se coluna existe
print("\nVerificando estrutura da tabela clientes_finais...")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'clientes_finais'
    ORDER BY ordinal_position
""")

colunas = cur.fetchall()
print(f"\nColunas atuais ({len(colunas)}):")
for col in colunas:
    print(f"  - {col[0]:<30} {col[1]}")

# Verificar se ponto_venda existe
tem_ponto_venda = any(col[0] == 'ponto_venda' for col in colunas)

if tem_ponto_venda:
    print("\nOK - Coluna ponto_venda ja existe!")
else:
    print("\nERRO - Coluna ponto_venda NAO existe!")
    print("\nAdicionando coluna ponto_venda...")

    try:
        cur.execute("""
            ALTER TABLE clientes_finais
            ADD COLUMN IF NOT EXISTS ponto_venda VARCHAR(20)
        """)
        conn.commit()
        print("OK - Coluna ponto_venda adicionada com sucesso!")
    except Exception as e:
        print(f"ERRO ao adicionar coluna: {e}")
        conn.rollback()

# Verificar novamente
print("\nVerificando novamente...")
cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'clientes_finais'
    AND column_name = 'ponto_venda'
""")

if cur.fetchone():
    print("OK - Coluna ponto_venda confirmada!")
else:
    print("ERRO - Coluna ponto_venda ainda nao existe!")

cur.close()
conn.close()
print("\nConexao fechada.")
