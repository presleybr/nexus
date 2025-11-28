"""
Simula EXATAMENTE o que acontecerá no disparo
Mostra os números que serão usados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import ClienteFinal, ClienteNexus

print("\n" + "="*80)
print("SIMULACAO DE DISPARO - NUMEROS REAIS QUE SERAO USADOS")
print("="*80 + "\n")

CLIENTE_NEXUS_ID = 2

# 1. Buscar clientes EXATAMENTE como a automação faz
print("[1] Buscando clientes (mesma query da automação)...")
clientes = ClienteFinal.listar_por_cliente_nexus(CLIENTE_NEXUS_ID, limit=1000)
print(f"Total: {len(clientes)}\n")

# 2. Filtrar quem tem WhatsApp
print("[2] Filtrando quem receberá disparo...")
clientes_disparo = []
for cliente in clientes:
    whatsapp = cliente.get('whatsapp')
    if whatsapp and whatsapp.strip() and whatsapp != '0000000000':
        clientes_disparo.append(cliente)

print(f"Total que RECEBERÁ disparo: {len(clientes_disparo)}\n")

# 3. Mostrar EXATAMENTE quem receberá e qual número
print("="*80)
print("LISTA DE DISPAROS - ESSES SAO OS NUMEROS QUE SERAO USADOS:")
print("="*80 + "\n")

for i, cliente in enumerate(clientes_disparo[:20], 1):  # Primeiros 20
    print(f"{i:2}. {cliente['nome'][:45]:<45} | WhatsApp: {cliente['whatsapp']}")

if len(clientes_disparo) > 20:
    print(f"\n... e mais {len(clientes_disparo) - 20} clientes")

print("\n" + "="*80)
print(f"TOTAL DE DISPAROS: {len(clientes_disparo)}")
print("="*80)
print("\nESSES sao os numeros REAIS do banco de dados.")
print("Se voce ver numeros diferentes durante o disparo,")
print("me avise QUAIS numeros aparecem!\n")
print("="*80 + "\n")
