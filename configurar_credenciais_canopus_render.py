#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configura credenciais do Canopus no banco do Render
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
print("CONFIGURAÇÃO DE CREDENCIAIS CANOPUS NO RENDER")
print("=" * 80)

conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
cur = conn.cursor()

# Verificar se tabela existe
print("\n🔍 Verificando se tabela credenciais_canopus existe...")
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = 'credenciais_canopus'
    )
""")

tabela_existe = cur.fetchone()['exists']

if not tabela_existe:
    print("❌ Tabela credenciais_canopus não existe!")
    print("\n📝 Criando tabela...")

    cur.execute("""
        CREATE TABLE credenciais_canopus (
            id SERIAL PRIMARY KEY,
            ponto_venda VARCHAR(20) NOT NULL,
            usuario VARCHAR(255) NOT NULL,
            senha VARCHAR(255) NOT NULL,
            codigo_empresa VARCHAR(10) DEFAULT '0101',
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ponto_venda)
        )
    """)
    conn.commit()
    print("✅ Tabela criada com sucesso!")
else:
    print("✅ Tabela credenciais_canopus já existe!")

# Verificar credenciais existentes
print("\n📋 Verificando credenciais existentes...")
cur.execute("SELECT ponto_venda, usuario, codigo_empresa, ativo FROM credenciais_canopus")
credenciais = cur.fetchall()

if credenciais:
    print(f"\n✅ {len(credenciais)} credencial(is) encontrada(s):")
    for cred in credenciais:
        status = "ATIVO" if cred['ativo'] else "INATIVO"
        print(f"  PV: {cred['ponto_venda']:<10} | Usuário: {cred['usuario']:<20} | Código Empresa: {cred['codigo_empresa']:<6} | {status}")
else:
    print("\n⚠️ Nenhuma credencial encontrada!")
    print("\n📝 Inserindo credenciais do PV 24627 (Dener - Canopus)...")

    # NOTA: Ajuste esses valores conforme necessário
    cur.execute("""
        INSERT INTO credenciais_canopus (
            ponto_venda,
            usuario,
            senha,
            codigo_empresa,
            ativo,
            created_at,
            updated_at
        ) VALUES (
            '24627',
            'dener',
            'sua_senha_aqui',
            '0101',
            TRUE,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (ponto_venda) DO UPDATE SET
            usuario = EXCLUDED.usuario,
            senha = EXCLUDED.senha,
            codigo_empresa = EXCLUDED.codigo_empresa,
            updated_at = CURRENT_TIMESTAMP
    """)
    conn.commit()

    print("✅ Credenciais inseridas!")
    print("\n⚠️ IMPORTANTE: Edite este script e configure a senha correta antes de executar!")

# Mostrar estrutura da tabela
print("\n📊 Estrutura da tabela credenciais_canopus:")
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'credenciais_canopus'
    ORDER BY ordinal_position
""")

for col in cur.fetchall():
    print(f"  {col['column_name']:<25} {col['data_type']:<25} NULL={col['is_nullable']}")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("✅ Configuração concluída!")
print("=" * 80)
