"""
Script para normalizar todos os números de WhatsApp formatados
Remove formatação (+, -, espaços, parênteses) para manter padrão da automação
"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def normalizar_numero(numero):
    """Remove tudo exceto dígitos"""
    if not numero:
        return ""
    return re.sub(r'[^\d]', '', str(numero))

print("\n" + "="*80)
print("NORMALIZANDO WHATSAPP COM FORMATAÇÃO")
print("="*80 + "\n")

# Buscar clientes com WhatsApp formatado (contém símbolos)
clientes = db.execute_query("""
    SELECT id, nome_completo, whatsapp
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND (
        whatsapp LIKE '%+%'
        OR whatsapp LIKE '%-%'
        OR whatsapp LIKE '% %'
        OR whatsapp LIKE '%(%'
    )
    AND cliente_nexus_id = 2
    AND ativo = TRUE
    ORDER BY nome_completo
""")

print(f"Total de clientes com WhatsApp formatado: {len(clientes)}\n")

if len(clientes) == 0:
    print("[INFO] Nenhum número formatado encontrado. Todos já estão no padrão da automação.\n")
    print("="*80 + "\n")
    sys.exit(0)

stats = {
    'processados': 0,
    'normalizados': 0,
    'erros': 0
}

for cliente in clientes:
    whatsapp_atual = cliente['whatsapp']
    whatsapp_normalizado = normalizar_numero(whatsapp_atual)

    print(f"ID {cliente['id']}: {cliente['nome_completo'][:50]}")
    print(f"  ANTES:  [{whatsapp_atual}]")
    print(f"  DEPOIS: [{whatsapp_normalizado}]")

    if not whatsapp_normalizado:
        print(f"  [ERRO] Número ficou vazio após normalização!\n")
        stats['erros'] += 1
        continue

    # Atualizar no banco
    try:
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (whatsapp_normalizado, cliente['id']))

        print(f"  [OK] Normalizado com sucesso!\n")
        stats['normalizados'] += 1
    except Exception as e:
        print(f"  [ERRO] Falha ao atualizar: {e}\n")
        stats['erros'] += 1

    stats['processados'] += 1

print("="*80)
print("RESUMO:")
print("="*80)
print(f"Processados: {stats['processados']}")
print(f"Normalizados com sucesso: {stats['normalizados']}")
print(f"Erros: {stats['erros']}")
print("="*80 + "\n")

if stats['normalizados'] > 0:
    print("[OK] Números normalizados para o padrão da automação (apenas dígitos)")
    print("[INFO] Agora todos os números seguem o formato: 5567912345678\n")
