#!/usr/bin/env python3
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
cur = conn.cursor()

# Contar consultores
cur.execute('SELECT COUNT(*) as total FROM consultores')
total = cur.fetchone()['total']
print(f'Total de consultores no banco: {total}')
print('='*80)

if total == 0:
    print('\nNENHUM CONSULTOR CADASTRADO!')
    print('\nVou criar um consultor padrao (Dener - Canopus)...')

    # Criar consultor padrão
    cur.execute("""
        INSERT INTO consultores (
            nome,
            email,
            empresa,
            ponto_venda,
            ativo,
            created_at,
            updated_at
        ) VALUES (
            'Dener - Canopus',
            'dener@canopus.com',
            'credms',
            '24627',
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        RETURNING id, nome, empresa, ponto_venda
    """)

    novo_consultor = cur.fetchone()
    conn.commit()

    print(f'\nConsultor criado com sucesso!')
    print(f'  ID: {novo_consultor["id"]}')
    print(f'  Nome: {novo_consultor["nome"]}')
    print(f'  Empresa: {novo_consultor["empresa"]}')
    print(f'  PV: {novo_consultor["ponto_venda"]}')

else:
    # Listar consultores
    cur.execute("""
        SELECT id, nome, email, empresa, ponto_venda, ativo
        FROM consultores
        ORDER BY id
    """)

    consultores = cur.fetchall()

    print(f'\nConsultores cadastrados:\n')
    for c in consultores:
        status = 'ATIVO' if c['ativo'] else 'INATIVO'
        print(f'ID: {c["id"]:3} | {c["nome"]:<30} | Empresa: {c["empresa"]:<15} | PV: {c["ponto_venda"]:<10} | {status}')

cur.close()
conn.close()
print('\n' + '='*80)
