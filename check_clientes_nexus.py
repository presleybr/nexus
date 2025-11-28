import sys
sys.path.insert(0, r'D:\Nexus')

from backend.models.database import Database, execute_query

Database.initialize_pool()

# Ver estrutura primeiro
cols = execute_query("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'clientes_nexus'
    ORDER BY ordinal_position
""", fetch=True)

print("Colunas da tabela clientes_nexus:")
for col in cols:
    print(f"  - {col['column_name']}")

# Ver quais clientes_nexus existem
result = execute_query("""
    SELECT *
    FROM clientes_nexus
    ORDER BY id
""", fetch=True)

print("\nClientes Nexus na tabela:")
print("=" * 60)
if result:
    for c in result:
        print(f"{c['id']:3d} | {c}")
else:
    print("NENHUM cliente nexus encontrado!")
