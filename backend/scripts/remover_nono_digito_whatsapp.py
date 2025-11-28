"""
Remove o 9º dígito (primeiro 9) de TODOS os números de WhatsApp
Formato esperado: 55 + DDD + 8 dígitos (SEM o 9 inicial)
Exemplo: 5567963911866 → 556763911866
"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def ajustar_numero_whatsapp(numero):
    """
    Remove o 9º dígito se for um 9
    Formato: 55 + DDD (2 dígitos) + número (8 dígitos sem o 9 inicial)
    """
    if not numero or len(numero) < 12:
        return numero

    # Se o número tem 13 dígitos (55 + DDD + 9 dígitos)
    if len(numero) == 13:
        codigo_pais = numero[:2]  # 55
        ddd = numero[2:4]          # 67
        numero_com_9 = numero[4:]  # 963911866 (9 dígitos)

        # Se o primeiro dígito do número for 9, remove
        if numero_com_9.startswith('9'):
            numero_sem_9 = numero_com_9[1:]  # 63911866 (8 dígitos)
            return codigo_pais + ddd + numero_sem_9

    return numero

print("\n" + "="*80)
print("REMOVENDO 9º DÍGITO DE TODOS OS WHATSAPP")
print("="*80 + "\n")

# Buscar TODOS os clientes com WhatsApp de 13 dígitos
clientes = db.execute_query("""
    SELECT id, nome_completo, whatsapp
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND LENGTH(whatsapp) = 13
    AND ativo = TRUE
    ORDER BY id
""")

print(f"Total de clientes com WhatsApp de 13 dígitos: {len(clientes)}\n")

if len(clientes) == 0:
    print("[INFO] Nenhum número com 13 dígitos encontrado.\n")
    print("="*80 + "\n")
    sys.exit(0)

stats = {
    'processados': 0,
    'ajustados': 0,
    'mantidos': 0,
    'erros': 0
}

for cliente in clientes:
    whatsapp_atual = cliente['whatsapp']
    whatsapp_ajustado = ajustar_numero_whatsapp(whatsapp_atual)

    print(f"ID {cliente['id']}: {cliente['nome_completo'][:50]}")
    print(f"  ANTES:  [{whatsapp_atual}] ({len(whatsapp_atual)} dígitos)")
    print(f"  DEPOIS: [{whatsapp_ajustado}] ({len(whatsapp_ajustado)} dígitos)")

    if whatsapp_atual != whatsapp_ajustado:
        # Atualizar no banco
        try:
            db.execute_update("""
                UPDATE clientes_finais
                SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (whatsapp_ajustado, cliente['id']))

            print(f"  [OK] Ajustado com sucesso!\n")
            stats['ajustados'] += 1
        except Exception as e:
            print(f"  [ERRO] Falha ao atualizar: {e}\n")
            stats['erros'] += 1
    else:
        print(f"  [INFO] Número já está no formato correto\n")
        stats['mantidos'] += 1

    stats['processados'] += 1

print("="*80)
print("RESUMO:")
print("="*80)
print(f"Processados: {stats['processados']}")
print(f"Ajustados (9 removido): {stats['ajustados']}")
print(f"Mantidos (já corretos): {stats['mantidos']}")
print(f"Erros: {stats['erros']}")
print("="*80 + "\n")

if stats['ajustados'] > 0:
    print("[OK] Números ajustados para o formato correto:")
    print("[OK] 55 + DDD + 8 dígitos (sem o 9 inicial)")
    print("[OK] Exemplo: 556763911866\n")
