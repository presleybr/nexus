import sys
sys.path.insert(0, r'D:\Nexus')

from backend.models.database import Database, execute_query

# Inicializar pool
Database.initialize_pool()

# Buscar alguns clientes para ver como os nomes estão salvos
clientes = execute_query('''
    SELECT id, nome_completo, cpf
    FROM clientes_finais
    ORDER BY nome_completo
    LIMIT 15
''', fetch=True)

# Contar total primeiro
total = execute_query('SELECT COUNT(*) as total FROM clientes_finais', fetch=True)
print(f'Total de clientes no banco: {total[0]["total"] if total else 0}')

print('\n=== CLIENTES NO BANCO ===')
if clientes:
    for c in clientes:
        print(f'{c["id"]:3d} | {c["nome_completo"]}')
else:
    print('Nenhum cliente encontrado!')

print('\n=== BUSCA POR NOME (como codigo faz) ===')
# Testar busca como o codigo faz
test_names = [
    'Adilson Barros Correa Junio',
    'Luis Eduardo Ferreira Caceres',
    'Marcelo Candido De Araujo'
]

for nome in test_names:
    result = execute_query('''
        SELECT id, nome_completo
        FROM clientes_finais
        WHERE UPPER(REPLACE(nome_completo, ' ', '')) = UPPER(REPLACE(%s, ' ', ''))
        LIMIT 1
    ''', (nome,), fetch=True)

    if result:
        print(f'[OK] Encontrado: "{nome}" -> "{result[0]["nome_completo"]}"')
    else:
        print(f'[ERRO] NAO encontrado: "{nome}"')

        # Buscar similar
        similar = execute_query('''
            SELECT nome_completo
            FROM clientes_finais
            WHERE nome_completo ILIKE %s
            LIMIT 3
        ''', (f'%{nome.split()[0]}%',), fetch=True)

        if similar:
            print(f'  Similares: {[s["nome_completo"] for s in similar]}')
