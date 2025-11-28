"""
DEBUG: Mostra EXATAMENTE quais números estão sendo usados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import ClienteFinal
from models.database import db

print("\n" + "="*80)
print("DEBUG: RASTREANDO NUMEROS NO FLUXO DE DISPARO")
print("="*80 + "\n")

CLIENTE_NEXUS_ID = 2

# PASSO 1: Buscar clientes EXATAMENTE como a automação faz
print("[PASSO 1] Buscando clientes (mesma query da automacao)...")
clientes = ClienteFinal.listar_por_cliente_nexus(CLIENTE_NEXUS_ID, limit=1000)
print(f"Total: {len(clientes)}\n")

# Filtrar só quem tem WhatsApp
clientes_com_whatsapp = [c for c in clientes if c.get('whatsapp') and c['whatsapp'].strip()]
print(f"Clientes COM WhatsApp: {len(clientes_com_whatsapp)}\n")

# PASSO 2: Processar cada cliente
print("[PASSO 2] Processando primeiros 5 clientes COM WhatsApp...\n")

for i, cliente_final in enumerate(clientes_com_whatsapp[:5], 1):
    print(f"--- CLIENTE {i} ---")
    print(f"ID: {cliente_final['id']}")
    print(f"Nome: {cliente_final.get('nome', 'N/A')[:40]}")

    # PONTO CRÍTICO: De onde vem o WhatsApp?
    whatsapp_do_dict = cliente_final.get('whatsapp')
    print(f"WhatsApp da query: [{whatsapp_do_dict}]")

    # Buscar DIRETO do banco para comparar
    whatsapp_banco = db.execute_query("""
        SELECT whatsapp FROM clientes_finais WHERE id = %s
    """, (cliente_final['id'],))

    if whatsapp_banco:
        whatsapp_direto = whatsapp_banco[0].get('whatsapp', '')
        print(f"WhatsApp do banco:  [{whatsapp_direto}]")

        if whatsapp_do_dict != whatsapp_direto:
            print("[ERRO] NUMEROS DIFERENTES!")
            print("A query NAO bate com o banco!")
        else:
            print("[OK] Numeros batem")

    # Simular o que _gerar_boleto_para_cliente faz
    boleto_data = {
        'cliente_final_id': cliente_final['id'],
        'cliente_final_nome': cliente_final.get('nome'),
        'whatsapp': cliente_final.get('whatsapp'),  # ← LINHA 199 do código
    }

    print(f"WhatsApp para disparo: [{boleto_data['whatsapp']}]")
    print()

print("="*80)
print("VERIFICACAO COMPLETA")
print("="*80)
print("\nQUAIS sao os numeros ERRADOS que voce esta vendo?")
print("Me diga 2-3 exemplos dos numeros que estao sendo usados!")
print("\nSe esses numeros acima estao CORRETOS mas o disparo usa")
print("outros numeros, entao:")
print("1. Reinicie o backend (pode ter cache)")
print("2. Verifique se tem outra instancia rodando")
print("3. Mostre os logs do disparo real\n")
print("="*80 + "\n")
