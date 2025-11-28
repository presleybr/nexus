#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atualiza senha do Canopus no banco do Render
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
print("ATUALIZAÇÃO DE SENHA CANOPUS - PV 24627")
print("=" * 80)

conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
cur = conn.cursor()

# Atualizar senha
print("\n🔄 Atualizando senha para PV 24627...")
cur.execute("""
    UPDATE credenciais_canopus
    SET senha = %s, updated_at = CURRENT_TIMESTAMP
    WHERE ponto_venda = '24627'
""", ('Sonhorealizado2!',))

conn.commit()

# Verificar
cur.execute("""
    SELECT ponto_venda, usuario, codigo_empresa, ativo, updated_at
    FROM credenciais_canopus
    WHERE ponto_venda = '24627'
""")

cred = cur.fetchone()
if cred:
    print(f"\n✅ Senha atualizada com sucesso!")
    print(f"  PV: {cred['ponto_venda']}")
    print(f"  Usuário: {cred['usuario']}")
    print(f"  Código Empresa: {cred['codigo_empresa']}")
    print(f"  Ativo: {'SIM' if cred['ativo'] else 'NÃO'}")
    print(f"  Última atualização: {cred['updated_at']}")
else:
    print("❌ PV não encontrado!")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("✅ Concluído!")
print("=" * 80)
