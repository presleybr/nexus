"""
Verificar clientes COM WhatsApp na query
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import ClienteFinal

print("\n" + "="*80)
print("VERIFICANDO CLIENTES COM WHATSAPP")
print("="*80 + "\n")

CLIENTE_NEXUS_ID = 2

print("[1] Buscando TODOS os clientes...")
todos_clientes = ClienteFinal.listar_por_cliente_nexus(CLIENTE_NEXUS_ID, limit=1000)
print(f"Total: {len(todos_clientes)}\n")

print("[2] Filtrando clientes COM WhatsApp...")
com_whatsapp = []
for c in todos_clientes:
    whatsapp = c.get('whatsapp')
    if whatsapp and whatsapp.strip() and whatsapp != '0000000000':
        com_whatsapp.append(c)

print(f"Clientes COM WhatsApp: {len(com_whatsapp)}\n")

if com_whatsapp:
    print("Primeiros 10 clientes COM WhatsApp:\n")
    for i, cliente in enumerate(com_whatsapp[:10], 1):
        print(f"{i}. ID {cliente['id']}: {cliente['nome'][:40]}")
        print(f"   WhatsApp: {cliente['whatsapp']}")
        print()
else:
    print("[ERRO] NENHUM cliente tem WhatsApp na query!\n")
    print("Isso significa que:")
    print("1. Os WhatsApp nao foram salvos no banco, OU")
    print("2. A query nao esta trazendo o campo corretamente\n")

print("="*80 + "\n")
