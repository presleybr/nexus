"""
Verificar todos os WhatsApp no banco
Mostra estatísticas e lista números que não seguem o padrão
"""
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("VERIFICAÇÃO DE WHATSAPP NO BANCO")
print("="*80 + "\n")

# Buscar TODOS os clientes com WhatsApp
clientes = db.execute_query("""
    SELECT id, nome_completo, whatsapp, cliente_nexus_id
    FROM clientes_finais
    WHERE whatsapp IS NOT NULL
    AND whatsapp != ''
    AND ativo = TRUE
    ORDER BY cliente_nexus_id, nome_completo
""")

print(f"Total de clientes com WhatsApp: {len(clientes)}\n")

stats = {
    'total': len(clientes),
    'padrao_correto': 0,
    'com_formatacao': 0,
    'sem_codigo_pais': 0,
    'outros_problemas': 0
}

problemas = []

for cliente in clientes:
    whatsapp = cliente['whatsapp']

    # Verificar se tem apenas dígitos
    tem_apenas_digitos = bool(re.match(r'^\d+$', whatsapp))

    # Verificar se começa com 55
    comeca_com_55 = whatsapp.startswith('55') if tem_apenas_digitos else False

    # Verificar tamanho (deve ter 12-13 dígitos com código do país)
    tamanho_ok = len(whatsapp) in [12, 13] if tem_apenas_digitos else False

    if tem_apenas_digitos and comeca_com_55 and tamanho_ok:
        stats['padrao_correto'] += 1
    else:
        # Identificar tipo de problema
        if not tem_apenas_digitos:
            stats['com_formatacao'] += 1
            tipo_problema = "Com formatação (+, -, espaços, etc)"
        elif not comeca_com_55:
            stats['sem_codigo_pais'] += 1
            tipo_problema = "Sem código do país (55)"
        else:
            stats['outros_problemas'] += 1
            tipo_problema = f"Tamanho inválido ({len(whatsapp)} dígitos)"

        problemas.append({
            'id': cliente['id'],
            'nome': cliente['nome_completo'][:50],
            'whatsapp': whatsapp,
            'tipo': tipo_problema
        })

print("="*80)
print("ESTATÍSTICAS:")
print("="*80)
print(f"Total de clientes: {stats['total']}")
print(f"Padrão correto (apenas dígitos, com 55): {stats['padrao_correto']}")
print(f"Com formatação: {stats['com_formatacao']}")
print(f"Sem código do país: {stats['sem_codigo_pais']}")
print(f"Outros problemas: {stats['outros_problemas']}")
print("="*80 + "\n")

if problemas:
    print("="*80)
    print("NÚMEROS COM PROBLEMAS:")
    print("="*80 + "\n")
    for p in problemas:
        print(f"ID {p['id']}: {p['nome']}")
        print(f"  WhatsApp: [{p['whatsapp']}]")
        print(f"  Problema: {p['tipo']}\n")
else:
    print("[OK] TODOS os números estão no padrão correto da automação!")
    print("[OK] Formato: apenas dígitos, sempre com código do país (55)\n")

print("="*80 + "\n")
