"""
Normalizar TODOS os WhatsApp no banco de dados
Remove formatação de todos os números existentes
"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def normalizar_whatsapp(numero):
    """Remove tudo exceto dígitos"""
    if not numero:
        return ""

    apenas_digitos = re.sub(r'[^\d]', '', str(numero))

    # Se não começar com 55, adicionar
    if apenas_digitos and not apenas_digitos.startswith('55'):
        apenas_digitos = '55' + apenas_digitos

    return apenas_digitos

print("\n" + "="*80)
print("NORMALIZANDO TODOS OS WHATSAPP DO BANCO")
print("="*80 + "\n")

# Buscar TODOS os clientes com WhatsApp
clientes = db.execute_query("""
    SELECT id, nome_completo, whatsapp
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND ativo = TRUE
    ORDER BY id
""")

print(f"Total de clientes com WhatsApp: {len(clientes)}\n")

stats = {
    'processados': 0,
    'normalizados': 0,
    'ja_corretos': 0
}

for cliente in clientes:
    whatsapp_atual = cliente['whatsapp']
    whatsapp_normalizado = normalizar_whatsapp(whatsapp_atual)

    # Verificar se precisa normalizar
    if whatsapp_atual != whatsapp_normalizado:
        print(f"ID {cliente['id']}: {cliente['nome_completo'][:40]}")
        print(f"  ANTES: [{whatsapp_atual}]")
        print(f"  DEPOIS: [{whatsapp_normalizado}]")

        # Atualizar
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (whatsapp_normalizado, cliente['id']))

        print(f"  [OK] Normalizado!\n")
        stats['normalizados'] += 1
    else:
        stats['ja_corretos'] += 1

    stats['processados'] += 1

print("="*80)
print("RESUMO:")
print("="*80)
print(f"Processados: {stats['processados']}")
print(f"Normalizados: {stats['normalizados']}")
print(f"Ja corretos: {stats['ja_corretos']}")
print("="*80 + "\n")
