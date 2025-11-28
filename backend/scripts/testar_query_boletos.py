"""
Testa a query de boletos para ver quais serão enviados no teste
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*80)
print("QUERY DE TESTE - BOLETOS QUE SERÃO ENVIADOS")
print("="*80 + "\n")

# Simular o cliente_nexus_id (assumindo id 2)
cliente_nexus_id = 2

# Query EXATA do endpoint de teste
boletos = db.execute_query("""
    SELECT
        b.id as boleto_id,
        b.pdf_path,
        b.pdf_filename,
        b.data_vencimento,
        b.valor_original,
        cf.id as cliente_id,
        cf.nome_completo,
        cf.cpf,
        cf.numero_contrato
    FROM boletos b
    JOIN clientes_finais cf ON b.cliente_final_id = cf.id
    WHERE b.cliente_nexus_id = %s
    AND b.status_envio = 'nao_enviado'
    AND b.pdf_path IS NOT NULL
    AND b.pdf_path LIKE '%%canopus%%'
    AND b.pdf_filename IS NOT NULL
    AND cf.ativo = true
    ORDER BY b.data_vencimento ASC
    LIMIT 11
""", (cliente_nexus_id,))

if not boletos:
    print("[ERRO] Nenhum boleto encontrado com os critérios!")
    print("\nVerificando boletos pendentes SEM filtro do Canopus:")

    boletos_todos = db.execute_query("""
        SELECT
            b.id,
            b.pdf_path,
            b.pdf_filename,
            b.status_envio,
            cf.nome_completo
        FROM boletos b
        JOIN clientes_finais cf ON b.cliente_final_id = cf.id
        WHERE b.cliente_nexus_id = %s
        AND b.status_envio = 'nao_enviado'
        LIMIT 20
    """, (cliente_nexus_id,))

    if boletos_todos:
        print(f"\n[INFO] Encontrados {len(boletos_todos)} boletos pendentes (sem filtro Canopus):\n")
        for b in boletos_todos:
            tipo = "[CANOPUS]" if 'canopus' in b['pdf_path'].lower() else "[FAKE/ANTIGO]"
            print(f"{tipo} ID {b['id']}: {b['nome_completo'][:30]:<30}")
            print(f"         Filename: {b['pdf_filename']}")
            print(f"         Path: {b['pdf_path'][:60]}...")
            print()
    sys.exit(1)

print(f"[OK] Encontrados {len(boletos)} boletos do CANOPUS para enviar:\n")

for idx, boleto in enumerate(boletos, 1):
    print(f"{idx}. Cliente: {boleto['nome_completo']}")
    print(f"   Boleto ID: {boleto['boleto_id']}")
    print(f"   Filename: {boleto['pdf_filename']}")
    print(f"   Path: {boleto['pdf_path']}")
    print(f"   Vencimento: {boleto['data_vencimento']}")

    # Verificar se arquivo existe
    if os.path.exists(boleto['pdf_path']):
        tamanho = os.path.getsize(boleto['pdf_path']) / 1024
        print(f"   Status: [OK] {tamanho:.1f}KB")
    else:
        print(f"   Status: [ERRO] Arquivo não encontrado!")
    print()

print("="*80)
print(f"[RESUMO] {len(boletos)} boletos REAIS do Canopus prontos para envio")
print("="*80 + "\n")
