"""
Verificar boletos prontos para disparo
"""
import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("VERIFICACAO DE BOLETOS PARA DISPARO")
print("="*80 + "\n")

CLIENTE_NEXUS_ID = 2

# Query EXATA que a automação usa
boletos = db.execute_query("""
    SELECT
        b.id as boleto_id,
        b.pdf_path,
        b.numero_boleto,
        b.data_vencimento,
        b.valor_original,
        b.cliente_final_id,
        cf.nome_completo as cliente_final_nome,
        cf.cpf as cliente_final_cpf,
        cf.whatsapp,
        cf.nome_completo,
        cf.numero_contrato
    FROM boletos b
    JOIN clientes_finais cf ON b.cliente_final_id = cf.id
    WHERE b.cliente_nexus_id = %s
    AND b.status_envio = 'nao_enviado'
    AND cf.whatsapp IS NOT NULL
    AND cf.whatsapp != ''
    AND cf.ativo = true
    ORDER BY b.data_vencimento ASC
""", (CLIENTE_NEXUS_ID,))

print(f"[1] Boletos encontrados: {len(boletos)}\n")

if not boletos:
    print("[ERRO] NENHUM boleto encontrado!")
    print("\nPossíveis motivos:")
    print("1. Todos já foram enviados (status_envio != 'nao_enviado')")
    print("2. Clientes não têm WhatsApp")
    print("3. Boletos não foram importados do Canopus\n")

    # Verificar quantos existem no total
    total = db.execute_query("""
        SELECT COUNT(*) as total FROM boletos WHERE cliente_nexus_id = %s
    """, (CLIENTE_NEXUS_ID,))
    print(f"Total de boletos no banco: {total[0]['total'] if total else 0}")

    # Verificar quantos já foram enviados
    enviados = db.execute_query("""
        SELECT COUNT(*) as total FROM boletos
        WHERE cliente_nexus_id = %s AND status_envio = 'enviado'
    """, (CLIENTE_NEXUS_ID,))
    print(f"Boletos já enviados: {enviados[0]['total'] if enviados else 0}")

    # Verificar quantos pendentes
    pendentes = db.execute_query("""
        SELECT COUNT(*) as total FROM boletos
        WHERE cliente_nexus_id = %s AND status_envio = 'nao_enviado'
    """, (CLIENTE_NEXUS_ID,))
    print(f"Boletos pendentes (todos): {pendentes[0]['total'] if pendentes else 0}")

    # Verificar quantos têm WhatsApp
    com_whatsapp = db.execute_query("""
        SELECT COUNT(*) as total FROM boletos b
        JOIN clientes_finais cf ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = %s
        AND b.status_envio = 'nao_enviado'
        AND cf.whatsapp IS NOT NULL
        AND cf.whatsapp != ''
    """, (CLIENTE_NEXUS_ID,))
    print(f"Boletos pendentes COM WhatsApp: {com_whatsapp[0]['total'] if com_whatsapp else 0}\n")

    print("="*80 + "\n")
    sys.exit(0)

print("[2] Verificando cada boleto...\n")

problemas = []
ok_count = 0

for i, boleto in enumerate(boletos[:10], 1):  # Primeiros 10
    print(f"--- BOLETO {i} ---")
    print(f"ID: {boleto['boleto_id']}")
    print(f"Cliente: {boleto['nome_completo']}")
    print(f"WhatsApp: {boleto['whatsapp']}")
    print(f"Numero boleto: {boleto['numero_boleto']}")
    print(f"PDF: {boleto['pdf_path']}")

    # Verificar se PDF existe
    pdf_path = boleto['pdf_path']
    if Path(pdf_path).exists():
        tamanho_kb = Path(pdf_path).stat().st_size / 1024
        print(f"PDF existe: SIM ({tamanho_kb:.1f} KB)")
        ok_count += 1
    else:
        print(f"PDF existe: NAO - [ERRO]")
        problemas.append({
            'boleto_id': boleto['boleto_id'],
            'cliente': boleto['nome_completo'],
            'problema': f"PDF não encontrado: {pdf_path}"
        })

    print()

if len(boletos) > 10:
    print(f"... e mais {len(boletos) - 10} boletos\n")

print("="*80)
print("RESUMO")
print("="*80)
print(f"Total de boletos prontos: {len(boletos)}")
print(f"Boletos OK (PDF existe): {ok_count}")
print(f"Boletos com problema: {len(problemas)}")
print("="*80)

if problemas:
    print("\nPROBLEMAS ENCONTRADOS:\n")
    for p in problemas[:5]:
        print(f"Boleto {p['boleto_id']} - {p['cliente']}")
        print(f"  {p['problema']}\n")

if ok_count > 0:
    print(f"\n[OK] {ok_count} boletos estao prontos para disparo!")
else:
    print("\n[ERRO] Nenhum boleto esta pronto!")

print("="*80 + "\n")
