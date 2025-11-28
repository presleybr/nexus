"""
Reverter TODOS os ajustes de remoção do 9
Restaurar números ao estado anterior
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("REVERTENDO TODOS OS AJUSTES DE REMOÇÃO DO 9")
print("="*80 + "\n")

# Números que foram ajustados (adicionando o 9 de volta na posição 4)
clientes = db.execute_query("""
    SELECT id, nome_completo, whatsapp
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND LENGTH(whatsapp) = 12
    AND ativo = TRUE
    ORDER BY id
""")

print(f"Total de clientes com 12 dígitos: {len(clientes)}\n")
print("Verificando quais precisam ter o 9 restaurado...\n")

# IDs que foram modificados no script anterior (baseado no log)
IDS_MODIFICADOS = [931, 953, 965, 969, 974, 978, 1024, 1032, 1039, 1044, 1045,
                   1050, 1051, 1053, 1054, 1057, 1061, 1064, 1066, 1068, 1071]

stats = {'revertidos': 0, 'mantidos': 0}

for cliente in clientes:
    if cliente['id'] in IDS_MODIFICADOS:
        whatsapp_atual = cliente['whatsapp']

        # Adicionar 9 de volta na posição 4 (após 55 e DDD)
        # 556764433485 → 5567964433485
        whatsapp_revertido = whatsapp_atual[:4] + '9' + whatsapp_atual[4:]

        print(f"ID {cliente['id']}: {cliente['nome_completo'][:50]}")
        print(f"  ATUAL:     [{whatsapp_atual}] (12 dígitos)")
        print(f"  REVERTIDO: [{whatsapp_revertido}] (13 dígitos)")

        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (whatsapp_revertido, cliente['id']))

        print(f"  [OK] Revertido!\n")
        stats['revertidos'] += 1
    else:
        stats['mantidos'] += 1

print("="*80)
print(f"Revertidos: {stats['revertidos']}")
print(f"Mantidos: {stats['mantidos']}")
print("="*80 + "\n")
