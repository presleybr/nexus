import sys
sys.path.insert(0, r'D:\Nexus')

from backend.models.database import Database, execute_query

Database.initialize_pool()

# Verificar se a atualização foi feita
null_count = execute_query("""
    SELECT COUNT(*) as total
    FROM clientes_finais
    WHERE cliente_nexus_id IS NULL
""", fetch=True)

print(f"Clientes com cliente_nexus_id NULL: {null_count[0]['total']}")

# Ver distribuição
for cliente_nexus_id in [2, 3, 4]:
    count = execute_query("""
        SELECT COUNT(*) as total
        FROM clientes_finais
        WHERE cliente_nexus_id = %s
    """, (cliente_nexus_id,), fetch=True)
    print(f"Clientes com cliente_nexus_id {cliente_nexus_id}: {count[0]['total']}")
