"""
Verifica se os PDFs dos boletos do Canopus existem
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

print("\n" + "="*60)
print("VERIFICAÇÃO DE PDFs DOS BOLETOS DO CANOPUS")
print("="*60 + "\n")

# Buscar primeiros 11 boletos pendentes
boletos = db.execute_query("""
    SELECT
        b.id,
        b.pdf_path,
        b.pdf_filename,
        cf.nome_completo
    FROM boletos b
    JOIN clientes_finais cf ON b.cliente_final_id = cf.id
    WHERE b.status_envio = 'nao_enviado'
    AND b.pdf_path IS NOT NULL
    AND cf.ativo = true
    ORDER BY b.data_vencimento ASC
    LIMIT 11
""")

if not boletos:
    print("[ERRO] Nenhum boleto pendente encontrado!")
    sys.exit(1)

print(f"[INFO] Verificando {len(boletos)} boletos...\n")

existem = 0
nao_existem = 0

for boleto in boletos:
    pdf_path = boleto['pdf_path']
    existe = os.path.exists(pdf_path)

    status = "[OK]" if existe else "[FALTANDO]"
    tamanho = f"{os.path.getsize(pdf_path)/1024:.1f}KB" if existe else "N/A"

    print(f"{status} ID {boleto['id']}: {boleto['nome_completo'][:30]:<30}")
    print(f"     Arquivo: {boleto['pdf_filename']}")
    print(f"     Caminho: {pdf_path}")
    print(f"     Tamanho: {tamanho}")
    print()

    if existe:
        existem += 1
    else:
        nao_existem += 1

print("="*60)
print(f"[RESUMO] {existem} PDFs encontrados, {nao_existem} faltando")
print("="*60 + "\n")

if nao_existem > 0:
    print("[AVISO] Alguns PDFs nao foram encontrados!")
    print("Verifique se a automacao do Canopus esta rodando corretamente.")
else:
    print("[OK] Todos os PDFs foram encontrados!")
    print("O sistema esta pronto para enviar boletos REAIS do Canopus.")
