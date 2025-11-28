"""
Script para verificar se os WhatsApps foram salvos no banco
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("VERIFICANDO WHATSAPPS NO BANCO DE DADOS")
print("="*80 + "\n")

# Buscar clientes com WhatsApp
clientes_com_whatsapp = db.execute_query("""
    SELECT id, nome_completo, cpf, whatsapp, ponto_venda
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND whatsapp != '0000000000'
    AND ativo = TRUE
    ORDER BY nome_completo
    LIMIT 20
""")

if clientes_com_whatsapp:
    print(f"[OK] Encontrados {len(clientes_com_whatsapp)} clientes com WhatsApp (mostrando primeiros 20):\n")

    for cliente in clientes_com_whatsapp:
        print(f"ID: {cliente['id']:<5} | Nome: {cliente['nome_completo'][:35]:<35} | WhatsApp: {cliente['whatsapp']}")
else:
    print("[ERRO] Nenhum cliente com WhatsApp encontrado!")

# Verificar total de clientes
total_clientes = db.execute_query("""
    SELECT COUNT(*) as total
    FROM clientes_finais
    WHERE ativo = TRUE
""")

total = total_clientes[0]['total'] if total_clientes else 0

print(f"\n" + "="*80)
print(f"TOTAL DE CLIENTES ATIVOS: {total}")
print("="*80 + "\n")
