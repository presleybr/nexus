"""
Script para deletar clientes importados da planilha do Dener
e permitir reimportação limpa
"""
import sys
sys.path.insert(0, 'D:/Nexus/backend')
sys.path.insert(0, 'D:/Nexus/automation/canopus')

from db_config import get_connection_params
import psycopg

print('=' * 80)
print('LIMPAR CLIENTES DA PLANILHA DO DENER')
print('=' * 80)
print()

# Conectar ao banco
conn = psycopg.connect(**get_connection_params())
cur = conn.cursor()

# Contar antes
cur.execute("SELECT COUNT(*) FROM clientes_finais WHERE origem = 'planilha_dener'")
total_antes = cur.fetchone()[0]

print(f'Clientes encontrados com origem "planilha_dener": {total_antes}')
print()

if total_antes == 0:
    print('[INFO] Nenhum cliente para deletar')
    conn.close()
    sys.exit(0)

# Confirmar
resposta = input(f'Deseja deletar {total_antes} clientes? (S/N): ').strip().upper()

if resposta != 'S':
    print('[CANCELADO] Nenhum cliente foi deletado')
    conn.close()
    sys.exit(0)

# Deletar
print()
print('[*] Deletando clientes...')

cur.execute("DELETE FROM clientes_finais WHERE origem = 'planilha_dener'")
deleted = cur.rowcount
conn.commit()

print(f'[OK] {deleted} clientes deletados com sucesso!')
print()
print('Proximos passos:')
print('  1. Acesse: http://127.0.0.1:5000/crm/automacao-canopus')
print('  2. Clique em "Importar Planilha do Dener"')
print('  3. Deve importar apenas 43 clientes do PV 24627')
print()

conn.close()
