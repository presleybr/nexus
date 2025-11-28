"""
Remove o 5º dígito de TODOS os números com 13 dígitos
Independente de qual dígito seja
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("AJUSTANDO NÚMEROS COM 13 DÍGITOS")
print("="*80 + "\n")

# Buscar clientes com WhatsApp de 13 dígitos
clientes = db.execute_query("""
    SELECT id, nome_completo, whatsapp
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND LENGTH(whatsapp) = 13
    AND ativo = TRUE
    ORDER BY id
""")

print(f"Total de clientes com 13 dígitos: {len(clientes)}\n")

if len(clientes) == 0:
    print("[OK] Nenhum número com 13 dígitos encontrado.\n")
    print("="*80 + "\n")
    sys.exit(0)

stats = {'ajustados': 0, 'erros': 0}

for cliente in clientes:
    whatsapp_atual = cliente['whatsapp']

    # Remove o 5º dígito (posição 4 no índice)
    # 55 67 X XXXXXXXX -> 55 67 XXXXXXXX
    whatsapp_ajustado = whatsapp_atual[:4] + whatsapp_atual[5:]

    print(f"ID {cliente['id']}: {cliente['nome_completo'][:50]}")
    print(f"  ANTES:  [{whatsapp_atual}] (13 dígitos)")
    print(f"  DEPOIS: [{whatsapp_ajustado}] (12 dígitos)")
    print(f"  Removido: {whatsapp_atual[4]}")

    try:
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (whatsapp_ajustado, cliente['id']))

        print(f"  [OK] Ajustado!\n")
        stats['ajustados'] += 1
    except Exception as e:
        print(f"  [ERRO] {e}\n")
        stats['erros'] += 1

print("="*80)
print(f"Ajustados: {stats['ajustados']}")
print(f"Erros: {stats['erros']}")
print("="*80 + "\n")
