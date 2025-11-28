import sys
sys.path.insert(0, r'D:\Nexus')

from backend.models.database import Database, execute_query

Database.initialize_pool()

# Verificar se existe consultor Danner
consultor = execute_query("SELECT id, nome FROM consultores WHERE nome = 'Danner' LIMIT 1", fetch=True)

print("Consultor 'Danner':")
if consultor:
    print(f"  ID: {consultor[0]['id']}")
    print(f"  Nome: {consultor[0]['nome']}")
else:
    print("  NAO ENCONTRADO!")

# Listar todos os consultores
todos = execute_query("SELECT id, nome FROM consultores ORDER BY nome", fetch=True)
print(f"\nTotal de consultores: {len(todos) if todos else 0}")
if todos:
    print("\nTodos os consultores:")
    for c in todos:
        print(f"  {c['id']:3d} | {c['nome']}")
