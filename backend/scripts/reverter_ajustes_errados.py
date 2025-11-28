"""
Reverter ajustes errados - números que não tinham 9 após o DDD
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("REVERTENDO AJUSTES ERRADOS")
print("="*80 + "\n")

# Números que foram ajustados incorretamente
REVERTER = [
    (948, "5565841100040", "WESLEY JUNIOR DIDEROT CHERISCAR"),
    (966, "5567848311225", "LUIS FELIPE DA SILVA BEZERRA"),
    (1055, "5567841266146", "GILBERTO FERREIRA DA SILVA"),
    (1063, "5567810620233", "RAQUEL REGINA HORING"),
]

print(f"Revertendo {len(REVERTER)} números:\n")

for cliente_id, numero_original, nome in REVERTER:
    print(f"ID {cliente_id}: {nome}")
    print(f"  Restaurando: {numero_original}")

    try:
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (numero_original, cliente_id))

        print(f"  [OK] Revertido!\n")
    except Exception as e:
        print(f"  [ERRO] {e}\n")

print("="*80)
print("[OK] Números restaurados ao estado anterior")
print("="*80 + "\n")
