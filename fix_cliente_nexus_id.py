import sys
sys.path.insert(0, r'D:\Nexus')

from backend.models.database import Database, execute_query

Database.initialize_pool()

print("=" * 80)
print("VERIFICANDO E CORRIGINDO cliente_nexus_id")
print("=" * 80)

# 1. Ver quantos clientes tem cliente_nexus_id NULL
clientes_null = execute_query("""
    SELECT COUNT(*) as total
    FROM clientes_finais
    WHERE cliente_nexus_id IS NULL
""", fetch=True)

print(f"\nClientes com cliente_nexus_id NULL: {clientes_null[0]['total']}")

# 2. Ver todos os clientes_nexus disponíveis
clientes_nexus = execute_query("""
    SELECT id, nome_empresa, usuario_id
    FROM clientes_nexus
    ORDER BY id
""", fetch=True)

print(f"\nClientes Nexus disponíveis:")
for cn in clientes_nexus:
    print(f"  ID {cn['id']}: {cn['nome_empresa']} (usuario_id: {cn['usuario_id']})")

# 3. Para cada cliente_nexus, ver quantos clientes_finais ele tem
print(f"\nDistribuição de clientes_finais:")
for cn in clientes_nexus:
    count = execute_query("""
        SELECT COUNT(*) as total
        FROM clientes_finais
        WHERE cliente_nexus_id = %s
    """, (cn['id'],), fetch=True)
    print(f"  Cliente Nexus {cn['id']} ({cn['nome_empresa']}): {count[0]['total']} clientes")

# 4. Atualizar automaticamente
print("\n" + "=" * 80)
print("CORREÇÃO AUTOMÁTICA")
print("=" * 80)

# Vamos usar o primeiro cliente_nexus disponível (ID 2)
cliente_nexus_id_para_usar = clientes_nexus[0]['id']

print(f"\nAtualizando todos os clientes com cliente_nexus_id NULL")
print(f"para cliente_nexus_id = {cliente_nexus_id_para_usar} ({clientes_nexus[0]['nome_empresa']})")

db = Database()
conn = db.get_connection()
cur = conn.cursor()

try:
    cur.execute("""
        UPDATE clientes_finais
        SET cliente_nexus_id = %s
        WHERE cliente_nexus_id IS NULL
    """, (cliente_nexus_id_para_usar,))

    rows_updated = cur.rowcount
    conn.commit()

    print(f"\n✓ {rows_updated} clientes atualizados!")

    # Verificar
    count = execute_query("""
        SELECT COUNT(*) as total
        FROM clientes_finais
        WHERE cliente_nexus_id = %s
    """, (cliente_nexus_id_para_usar,), fetch=True)

    print(f"✓ Total de clientes para cliente_nexus_id {cliente_nexus_id_para_usar}: {count[0]['total']}")

    # Verificar NULL restantes
    null_count = execute_query("""
        SELECT COUNT(*) as total
        FROM clientes_finais
        WHERE cliente_nexus_id IS NULL
    """, fetch=True)

    print(f"✓ Clientes com NULL restantes: {null_count[0]['total']}")

except Exception as e:
    conn.rollback()
    print(f"✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
