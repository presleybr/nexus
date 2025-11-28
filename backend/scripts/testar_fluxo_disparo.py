"""
Testa o fluxo completo de disparo SEM enviar mensagens
Valida: clientes, WhatsApp, boletos e PDFs
"""
import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import ClienteFinal
from models.database import db

print("\n" + "="*80)
print("TESTE DE FLUXO DE DISPARO (SEM ENVIAR)")
print("="*80 + "\n")

CLIENTE_NEXUS_ID = 2

# ============================================================================
# 1. BUSCAR CLIENTES
# ============================================================================
print("[1] BUSCANDO CLIENTES...")
clientes = ClienteFinal.listar_por_cliente_nexus(CLIENTE_NEXUS_ID, limit=1000)
print(f"    [OK] Total de clientes: {len(clientes)}\n")

# ============================================================================
# 2. FILTRAR CLIENTES COM WHATSAPP
# ============================================================================
print("[2] FILTRANDO CLIENTES COM WHATSAPP...")
clientes_com_whatsapp = []
clientes_sem_whatsapp = []

for cliente in clientes:
    whatsapp = cliente.get('whatsapp')
    if whatsapp and whatsapp.strip() and whatsapp != '0000000000':
        clientes_com_whatsapp.append(cliente)
    else:
        clientes_sem_whatsapp.append(cliente)

print(f"    [OK] Com WhatsApp: {len(clientes_com_whatsapp)}")
print(f"    [AVISO] Sem WhatsApp: {len(clientes_sem_whatsapp)}\n")

if clientes_sem_whatsapp:
    print("    Clientes SEM WhatsApp (primeiros 5):")
    for c in clientes_sem_whatsapp[:5]:
        print(f"    - ID {c['id']}: {c['nome'][:40]}")
    print()

# ============================================================================
# 3. BUSCAR BOLETOS PARA OS CLIENTES
# ============================================================================
print("[3] VERIFICANDO BOLETOS NO BANCO...")
boletos_stats = {
    'com_boleto': 0,
    'sem_boleto': 0,
    'total_boletos': 0
}

clientes_com_boleto_e_whatsapp = []

for cliente in clientes_com_whatsapp:
    boletos = db.execute_query("""
        SELECT id, numero_boleto, pdf_path, valor_original, data_vencimento, status_envio
        FROM boletos
        WHERE cliente_final_id = %s
        AND cliente_nexus_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (cliente['id'], CLIENTE_NEXUS_ID))

    if boletos:
        boletos_stats['com_boleto'] += 1
        boletos_stats['total_boletos'] += len(boletos)
        cliente['boleto'] = boletos[0]
        clientes_com_boleto_e_whatsapp.append(cliente)
    else:
        boletos_stats['sem_boleto'] += 1

print(f"    [OK] Clientes com boleto: {boletos_stats['com_boleto']}")
print(f"    [AVISO] Clientes sem boleto: {boletos_stats['sem_boleto']}")
print(f"    [OK] Total de boletos: {boletos_stats['total_boletos']}\n")

# ============================================================================
# 4. VALIDAR FORMATO DOS WHATSAPP
# ============================================================================
print("[4] VALIDANDO FORMATO DOS WHATSAPP...")
whatsapp_stats = {
    '12_digitos': 0,
    '13_digitos': 0,
    'outros': 0
}

for cliente in clientes_com_boleto_e_whatsapp:
    whatsapp = cliente['whatsapp']
    tamanho = len(whatsapp)

    if tamanho == 12:
        whatsapp_stats['12_digitos'] += 1
    elif tamanho == 13:
        whatsapp_stats['13_digitos'] += 1
    else:
        whatsapp_stats['outros'] += 1

print(f"    [OK] 12 digitos (55+DDD+8): {whatsapp_stats['12_digitos']}")
print(f"    [AVISO] 13 digitos (55+DDD+9): {whatsapp_stats['13_digitos']}")
print(f"    [ERRO] Outros tamanhos: {whatsapp_stats['outros']}\n")

# ============================================================================
# 5. VERIFICAR SE PDFs EXISTEM
# ============================================================================
print("[5] VERIFICANDO SE PDFs EXISTEM...")
pdf_stats = {
    'existem': 0,
    'nao_existem': 0,
    'sem_caminho': 0
}

pdfs_nao_encontrados = []

for cliente in clientes_com_boleto_e_whatsapp:
    pdf_path = cliente['boleto'].get('pdf_path')

    if not pdf_path:
        pdf_stats['sem_caminho'] += 1
        continue

    if Path(pdf_path).exists():
        pdf_stats['existem'] += 1
    else:
        pdf_stats['nao_existem'] += 1
        pdfs_nao_encontrados.append({
            'cliente': cliente['nome'][:40],
            'path': pdf_path
        })

print(f"    [OK] PDFs encontrados: {pdf_stats['existem']}")
print(f"    [ERRO] PDFs nao encontrados: {pdf_stats['nao_existem']}")
print(f"    [AVISO] Sem caminho: {pdf_stats['sem_caminho']}\n")

if pdfs_nao_encontrados[:3]:
    print("    PDFs nao encontrados (primeiros 3):")
    for p in pdfs_nao_encontrados[:3]:
        print(f"    - {p['cliente']}")
        print(f"      {p['path']}\n")

# ============================================================================
# 6. RESUMO FINAL
# ============================================================================
print("="*80)
print("RESUMO DO TESTE")
print("="*80)
print(f"Total de clientes: {len(clientes)}")
print(f"Clientes com WhatsApp: {len(clientes_com_whatsapp)}")
print(f"Clientes com boleto + WhatsApp: {len(clientes_com_boleto_e_whatsapp)}")
print(f"PDFs prontos: {pdf_stats['existem']}")
print()

disparos_possiveis = min(len(clientes_com_boleto_e_whatsapp), pdf_stats['existem'])
print(f"DISPAROS POSSIVEIS: {disparos_possiveis}")
print("="*80)

if disparos_possiveis > 0:
    print("\n[OK] SISTEMA PRONTO PARA DISPARAR!")
    print(f"    {disparos_possiveis} clientes receberao seus boletos via WhatsApp\n")

    # Mostrar 5 exemplos
    print("    Exemplos de disparos (primeiros 5):")
    for i, cliente in enumerate(clientes_com_boleto_e_whatsapp[:5]):
        if cliente['boleto'].get('pdf_path') and Path(cliente['boleto']['pdf_path']).exists():
            print(f"\n    {i+1}. {cliente['nome'][:40]}")
            print(f"       WhatsApp: {cliente['whatsapp']}")
            print(f"       Boleto: {cliente['boleto']['numero_boleto']}")
            print(f"       Valor: R$ {cliente['boleto']['valor_original']}")
            print(f"       Vencimento: {cliente['boleto']['data_vencimento']}")
            print(f"       Status: {cliente['boleto']['status_envio']}")
else:
    print("\n[ERRO] SISTEMA NAO PODE DISPARAR")
    print("    Verifique os problemas acima\n")

print("="*80 + "\n")
