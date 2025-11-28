"""
Testa a geração de mensagem com dados extraídos do PDF
"""

import sys
import os
import io

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.pdf_extractor import extrair_dados_boleto
from services.mensagens_personalizadas import gerar_mensagem_boleto


def testar(caminho_pdf: str):
    """
    Testa a extração de dados do PDF e geração de mensagem personalizada

    Args:
        caminho_pdf: Caminho completo do arquivo PDF do boleto
    """
    print("=" * 70)
    print("TESTE: EXTRAÇÃO PDF + GERAÇÃO DE MENSAGEM")
    print("=" * 70)

    if not os.path.exists(caminho_pdf):
        print(f"\n❌ PDF não encontrado: {caminho_pdf}")
        print("\nUso: python testar_mensagem_pdf.py [caminho_do_pdf]")
        return

    print(f"\n📄 PDF: {os.path.basename(caminho_pdf)}")
    print(f"   Caminho: {caminho_pdf}")

    # Extrair dados
    print("\n🔍 Extraindo dados do PDF...")
    dados = extrair_dados_boleto(caminho_pdf)

    print(f"\n📊 Dados extraídos:")
    print(f"   Sucesso: {dados['sucesso']}")
    print(f"   Vencimento: {dados.get('vencimento_str', 'N/A')}")
    print(f"   Valor: R$ {dados.get('valor', 0):.2f}")
    print(f"   Nome: {dados.get('nome_pagador', 'N/A')}")
    print(f"   CPF: {dados.get('cpf', 'N/A')}")
    print(f"   Contrato: {dados.get('contrato', 'N/A')}")
    print(f"   Grupo/Cota: {dados.get('grupo_cota', 'N/A')}")
    print(f"   Nosso Número: {dados.get('nosso_numero', 'N/A')}")

    # Gerar mensagem
    print("\n" + "=" * 70)
    print("📱 MENSAGEM GERADA (COM DADOS DO PDF):")
    print("=" * 70)

    mensagem = gerar_mensagem_boleto(
        nome_cliente=dados.get('nome_pagador', 'Cliente Teste'),
        dados_pdf=dados
    )

    print(mensagem)

    # Comparação: mensagem SEM dados do PDF
    print("\n" + "=" * 70)
    print("📱 MENSAGEM SEM DADOS DO PDF (apenas banco de dados):")
    print("=" * 70)

    mensagem_sem_pdf = gerar_mensagem_boleto(
        nome_cliente="CLIENTE TESTE",
        vencimento="28/12/2025",  # Data errada (exemplo)
        valor=0,                   # Sem valor
        contrato="N/A",
        empresa="Cred MS Consorcios",
        dados_pdf=None  # SEM dados do PDF
    )

    print(mensagem_sem_pdf)

    print("\n" + "=" * 70)
    print("✅ Teste concluído!")
    print("=" * 70)

    # Resumo das diferenças
    print("\n📌 DIFERENÇAS IDENTIFICADAS:")
    print(f"   Com PDF:")
    print(f"      - Vencimento: {dados.get('vencimento_str', 'N/A')}")
    print(f"      - Valor: R$ {dados.get('valor', 0):.2f}")
    print(f"      - Nome: {dados.get('nome_pagador', 'N/A')}")
    print(f"\n   Sem PDF:")
    print(f"      - Vencimento: 28/12/2025 (fixo/errado)")
    print(f"      - Valor: R$ 0,00 (não informado)")
    print(f"      - Nome: CLIENTE TESTE (do banco)")


if __name__ == '__main__':
    # PDF de teste padrão
    pdf_teste = r'D:\Nexus\automation\canopus\downloads\Danner\ZACARIAS_DOS_SANTOS_ARCANJO_IMOVEL_DEZEMBRO.pdf'

    # Aceita PDF customizado via argumento
    if len(sys.argv) > 1:
        pdf_teste = sys.argv[1]

    # Testa com o PDF
    testar(pdf_teste)

    print("\n" + "=" * 70)
    print("💡 DICA:")
    print("   Para testar com outro PDF:")
    print('   python testar_mensagem_pdf.py "D:\\caminho\\para\\seu\\boleto.pdf"')
    print("=" * 70)
