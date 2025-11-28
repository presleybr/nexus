"""
Verificar se a query listar_por_cliente_nexus traz o WhatsApp
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import ClienteFinal

print("\n" + "="*80)
print("TESTE: Query listar_por_cliente_nexus")
print("="*80 + "\n")

CLIENTE_NEXUS_ID = 2

print("[1] Buscando clientes com a query do sistema...")
clientes = ClienteFinal.listar_por_cliente_nexus(CLIENTE_NEXUS_ID, limit=10)

print(f"Total retornado: {len(clientes)}\n")

print("Verificando campos retornados (primeiros 5 clientes):\n")

for i, cliente in enumerate(clientes[:5], 1):
    print(f"{i}. ID: {cliente.get('id')}")
    print(f"   Nome: {cliente.get('nome_completo', 'N/A')[:40]}")
    print(f"   Campo 'nome': {cliente.get('nome', 'N/A')[:40]}")
    print(f"   WhatsApp: {cliente.get('whatsapp', '[CAMPO NAO EXISTE]')}")
    print(f"   CPF: {cliente.get('cpf', 'N/A')}")
    print(f"   Ativo: {cliente.get('ativo', 'N/A')}")
    print(f"   Total de campos: {len(cliente.keys())}")
    print()

print("="*80)
print("\nCAMPOS DISPONIVEIS no primeiro cliente:")
print("="*80)
if clientes:
    for campo in sorted(clientes[0].keys()):
        valor = clientes[0][campo]
        if isinstance(valor, str) and len(str(valor)) > 50:
            valor = str(valor)[:50] + "..."
        print(f"  - {campo}: {valor}")

print("\n" + "="*80 + "\n")
