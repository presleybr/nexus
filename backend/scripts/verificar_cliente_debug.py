"""
Script de debug para verificar informações de um cliente específico
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db
from pathlib import Path

def verificar_cliente(cliente_id):
    """Verifica informações detalhadas de um cliente"""

    print("\n" + "="*80)
    print(f"DEBUG - CLIENTE ID: {cliente_id}")
    print("="*80 + "\n")

    # 1. Buscar dados do cliente
    print("[1] DADOS DO CLIENTE:")
    cliente = db.execute_query("""
        SELECT id, nome_completo, cpf, whatsapp, ponto_venda, ativo
        FROM clientes_finais
        WHERE id = %s
    """, (cliente_id,))

    if not cliente:
        print(f"[ERRO] Cliente ID {cliente_id} não encontrado no banco!")
        return

    cliente = cliente[0]
    print(f"   Nome: {cliente['nome_completo']}")
    print(f"   CPF: {cliente['cpf']}")
    print(f"   WhatsApp: {cliente['whatsapp']}")
    print(f"   Ponto Venda: {cliente['ponto_venda']}")
    print(f"   Ativo: {cliente['ativo']}")

    # 2. Verificar boletos no banco
    print(f"\n[2] BOLETOS NO BANCO DE DADOS:")
    boletos = db.execute_query("""
        SELECT id, numero_boleto, mes_referencia, ano_referencia,
               data_vencimento, valor_original, status, pdf_path
        FROM boletos
        WHERE cliente_final_id = %s
        ORDER BY data_vencimento DESC
    """, (cliente_id,))

    if boletos:
        print(f"   Total de boletos: {len(boletos)}")
        for boleto in boletos[:5]:  # Mostrar até 5
            print(f"   - {boleto['numero_boleto']} | {boleto['mes_referencia']}/{boleto['ano_referencia']} | Status: {boleto['status']}")
    else:
        print("   [AVISO] Nenhum boleto encontrado no banco de dados!")

    # 3. Buscar PDFs na pasta
    print(f"\n[3] BUSCANDO PDFs NA PASTA:")
    pasta_downloads = Path(r"D:\Nexus\automation\canopus\downloads\Danner")

    if not pasta_downloads.exists():
        print(f"   [ERRO] Pasta não existe: {pasta_downloads}")
        return

    nome_cliente = cliente['nome_completo']
    print(f"   Buscando por: {nome_cliente}")

    # Normalizar nome
    import re
    replacements = {
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C',
    }

    nome_normalizado = nome_cliente.upper()
    for old, new in replacements.items():
        nome_normalizado = nome_normalizado.replace(old, new)

    nome_normalizado = re.sub(r'[^A-Z0-9\s]', '', nome_normalizado).strip()
    palavras_cliente = [p for p in nome_normalizado.split() if len(p) > 2]

    print(f"   Nome normalizado: {nome_normalizado}")
    print(f"   Palavras significativas: {palavras_cliente}")

    # Buscar PDFs
    pdfs_encontrados = []
    todos_pdfs = list(pasta_downloads.glob("*.pdf"))

    print(f"\n   Total de PDFs na pasta: {len(todos_pdfs)}")
    print(f"   Testando match com cada arquivo...\n")

    for arquivo in todos_pdfs:
        nome_arquivo = arquivo.stem
        nome_arquivo_normalizado = nome_arquivo.upper()
        for old, new in replacements.items():
            nome_arquivo_normalizado = nome_arquivo_normalizado.replace(old, new)
        nome_arquivo_normalizado = re.sub(r'[^A-Z0-9\s]', '', nome_arquivo_normalizado)

        # Verificar match
        matches = sum(1 for palavra in palavras_cliente if palavra in nome_arquivo_normalizado)
        percentual_match = matches / len(palavras_cliente) if palavras_cliente else 0

        if percentual_match >= 0.6:
            pdfs_encontrados.append({
                'arquivo': arquivo.name,
                'match': f"{percentual_match*100:.0f}%"
            })
            print(f"   ✓ MATCH {percentual_match*100:.0f}%: {arquivo.name}")

    if not pdfs_encontrados:
        print(f"   [AVISO] Nenhum PDF encontrado para este cliente!")
        print(f"\n   Arquivos similares (primeiros 10):")
        for arquivo in todos_pdfs[:10]:
            print(f"   - {arquivo.name}")

    # 4. Resumo
    print(f"\n" + "="*80)
    print("RESUMO:")
    print(f"   - Cliente: {'ENCONTRADO' if cliente else 'NÃO ENCONTRADO'}")
    print(f"   - Boletos no BD: {len(boletos) if boletos else 0}")
    print(f"   - PDFs na pasta: {len(pdfs_encontrados)}")
    print("="*80 + "\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Debug de cliente')
    parser.add_argument('cliente_id', type=int, help='ID do cliente')

    args = parser.parse_args()

    verificar_cliente(args.cliente_id)
