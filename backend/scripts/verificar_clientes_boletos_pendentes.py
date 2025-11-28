"""
Verificar clientes com boletos pendentes para debug do dropdown
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print('=' * 60)
print('VERIFICANDO CLIENTES COM BOLETOS PENDENTES')
print('=' * 60)

# Verificar todos os cliente_nexus_id
clientes_nexus = db.execute_query('SELECT id, nome_empresa FROM clientes_nexus ORDER BY id')
print('\n[CLIENTES NEXUS] Cadastrados:')
for cn in clientes_nexus:
    print(f'  ID {cn["id"]}: {cn["nome_empresa"]}')

print('\n' + '=' * 60)
print('BOLETOS POR STATUS_ENVIO E CLIENTE_NEXUS_ID')
print('=' * 60)

for cn in clientes_nexus:
    print(f'\n[BOLETOS] Cliente Nexus ID {cn["id"]} ({cn["nome_empresa"]}):')

    # Contar boletos por status
    status_count = db.execute_query('''
        SELECT
            status_envio,
            COUNT(*) as total
        FROM boletos
        WHERE cliente_nexus_id = %s
        GROUP BY status_envio
        ORDER BY status_envio
    ''', (cn['id'],))

    if status_count:
        for s in status_count:
            print(f'  {s["status_envio"]}: {s["total"]} boleto(s)')
    else:
        print('  (Nenhum boleto cadastrado)')

print('\n' + '=' * 60)
print('CLIENTES COM BOLETOS NAO ENVIADOS (Query da API)')
print('=' * 60)

for cn in clientes_nexus:
    print(f'\n[API QUERY] Cliente Nexus ID {cn["id"]} ({cn["nome_empresa"]}):')

    query = '''
        SELECT
            cf.id,
            cf.nome_completo,
            cf.whatsapp,
            COUNT(b.id) as total_boletos
        FROM clientes_finais cf
        INNER JOIN boletos b ON b.cliente_final_id = cf.id
        WHERE cf.cliente_nexus_id = %s
            AND cf.ativo = true
            AND b.status_envio = 'nao_enviado'
        GROUP BY cf.id, cf.nome_completo, cf.whatsapp
        ORDER BY cf.nome_completo
        LIMIT 5
    '''

    clientes = db.execute_query(query, (cn['id'],))

    if clientes:
        print(f'  [OK] {len(clientes)} cliente(s) com boletos pendentes:')
        for c in clientes[:5]:
            print(f'    - {c["nome_completo"]} ({c["total_boletos"]} boleto(s)) - WhatsApp: {c["whatsapp"]}')
    else:
        print('  [X] Nenhum cliente com boletos pendentes')

print('\n' + '=' * 60)
print('VERIFICANDO CAMPO ATIVO DOS CLIENTES')
print('=' * 60)

for cn in clientes_nexus:
    print(f'\n[CAMPO ATIVO] Cliente Nexus ID {cn["id"]} ({cn["nome_empresa"]}):')

    # Total de clientes finais
    total = db.execute_query('''
        SELECT COUNT(*) as total FROM clientes_finais
        WHERE cliente_nexus_id = %s
    ''', (cn['id'],))

    # Clientes ativos
    ativos = db.execute_query('''
        SELECT COUNT(*) as total FROM clientes_finais
        WHERE cliente_nexus_id = %s AND ativo = true
    ''', (cn['id'],))

    # Clientes inativos
    inativos = db.execute_query('''
        SELECT COUNT(*) as total FROM clientes_finais
        WHERE cliente_nexus_id = %s AND ativo = false
    ''', (cn['id'],))

    print(f'  Total: {total[0]["total"]} | Ativos: {ativos[0]["total"]} | Inativos: {inativos[0]["total"]}')

    # Se houver inativos, mostrar quais
    if inativos[0]["total"] > 0:
        inativos_lista = db.execute_query('''
            SELECT id, nome_completo FROM clientes_finais
            WHERE cliente_nexus_id = %s AND ativo = false
            LIMIT 5
        ''', (cn['id'],))
        print(f'  Inativos (primeiros 5):')
        for c in inativos_lista:
            print(f'    - ID {c["id"]}: {c["nome_completo"]}')

print('\n' + '=' * 60)
