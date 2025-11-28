#!/usr/bin/env python3
"""
Script para criar o cliente_nexus associado ao usuario credms@nexusbrasi.ai
"""
import psycopg

# Conectar ao banco do Render
DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

print("Conectando ao banco do Render...")
conn = psycopg.connect(DATABASE_URL)
cur = conn.cursor()

email = 'credms@nexusbrasi.ai'

# Deletar cliente existente se houver
print(f"\nDeletando cliente existente para {email}...")
cur.execute('DELETE FROM clientes_nexus WHERE email_contato = %s', (email,))
conn.commit()
print(f"Linhas deletadas: {cur.rowcount}")

# Criar cliente_nexus
print("\nCriando cliente_nexus...")
query = """
INSERT INTO clientes_nexus (
    usuario_id,
    nome_empresa,
    cnpj,
    whatsapp_numero,
    email_contato,
    ativo,
    data_cadastro
)
SELECT
    u.id,
    'CredMS - Nexus Brasil',
    '30.767.662/0001-52',
    '556798905585',
    'credms@nexusbrasi.ai',
    true,
    CURRENT_TIMESTAMP
FROM usuarios u
WHERE u.email = %s
RETURNING id, nome_empresa, cnpj, whatsapp_numero
"""

cur.execute(query, (email,))
resultado = cur.fetchone()
conn.commit()

if resultado:
    print("Cliente criado com sucesso!")
    print(f"  ID: {resultado[0]}")
    print(f"  Empresa: {resultado[1]}")
    print(f"  CNPJ: {resultado[2]}")
    print(f"  WhatsApp: {resultado[3]}")
else:
    print("ERRO - Nao foi possivel criar cliente!")

cur.close()
conn.close()
print("\nConexao fechada.")
