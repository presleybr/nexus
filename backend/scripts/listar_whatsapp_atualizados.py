"""
Listar números de WhatsApp para verificar formato
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("NÚMEROS DE WHATSAPP ATUALIZADOS")
print("="*80 + "\n")

# Buscar todos os clientes com WhatsApp
clientes = db.execute_query("""
    SELECT id, nome_completo, whatsapp
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND ativo = TRUE
    ORDER BY nome_completo
    LIMIT 30
""")

print(f"Mostrando {len(clientes)} clientes com WhatsApp:\n")
print(f"{'ID':<6} {'Nome':<40} {'WhatsApp':<15} {'Dígitos':<8}")
print("-" * 80)

for c in clientes:
    nome = c['nome_completo'][:38]
    whatsapp = c['whatsapp']
    digitos = len(whatsapp)

    print(f"{c['id']:<6} {nome:<40} {whatsapp:<15} {digitos}")

print("\n" + "="*80)
print("FORMATO CORRETO:")
print("="*80)
print("Código: 55 (Brasil)")
print("DDD: 2 dígitos (ex: 67)")
print("Número: 8 dígitos (SEM o 9 inicial)")
print("Total: 12 dígitos")
print("Exemplo: 556763911866")
print("="*80 + "\n")
