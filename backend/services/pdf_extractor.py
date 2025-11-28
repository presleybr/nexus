"""
Extrator de dados de boletos PDF da Canopus
"""

import re
import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

try:
    import pdfplumber
    PDF_LIB = 'pdfplumber'
except ImportError:
    pdfplumber = None
    try:
        import PyPDF2
        PDF_LIB = 'pypdf2'
    except ImportError:
        PyPDF2 = None
        PDF_LIB = None

logger = logging.getLogger(__name__)


class BoletoExtractor:
    """Extrai dados de boletos PDF da Canopus"""

    def extrair_texto_pdf(self, caminho_pdf: str) -> str:
        """Extrai texto do PDF"""

        if not os.path.exists(caminho_pdf):
            logger.error(f"PDF não encontrado: {caminho_pdf}")
            return ""

        texto = ""

        try:
            if pdfplumber:
                with pdfplumber.open(caminho_pdf) as pdf:
                    for pagina in pdf.pages:
                        texto += (pagina.extract_text() or "") + "\n"
            elif PyPDF2:
                with open(caminho_pdf, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for pagina in reader.pages:
                        texto += (pagina.extract_text() or "") + "\n"
            else:
                logger.error("Nenhuma biblioteca de PDF disponível (pdfplumber ou PyPDF2)")

        except Exception as e:
            logger.error(f"Erro ao ler PDF: {e}")

        return texto

    def extrair_dados(self, caminho_pdf: str) -> Dict:
        """
        Extrai dados do boleto PDF.

        Returns:
            {
                'sucesso': bool,
                'vencimento': datetime ou None,
                'vencimento_str': '15/12/2025',
                'valor': float,
                'valor_str': '931,08',
                'nome_pagador': str,
                'cpf': str,
                'grupo_cota': str,
                'nosso_numero': str,
                'contrato': str
            }
        """

        resultado = {
            'sucesso': False,
            'vencimento': None,
            'vencimento_str': None,
            'valor': 0.0,
            'valor_str': None,
            'nome_pagador': None,
            'cpf': None,
            'grupo_cota': None,
            'nosso_numero': None,
            'contrato': None
        }

        try:
            texto = self.extrair_texto_pdf(caminho_pdf)

            if not texto:
                logger.warning(f"Não foi possível extrair texto do PDF: {caminho_pdf}")
                return resultado

            # VENCIMENTO - padrão: "Vencimento" seguido de data
            # O PDF da Canopus tem várias ocorrências, pegar a primeira válida
            vencimentos = re.findall(r'(\d{2}/\d{2}/\d{4})', texto)
            if vencimentos:
                # Filtrar datas futuras ou recentes (vencimento real)
                hoje = datetime.now()
                for v in vencimentos:
                    try:
                        data = datetime.strptime(v, '%d/%m/%Y')
                        # Vencimento geralmente é futuro ou recente (últimos 60 dias)
                        if data >= hoje - timedelta(days=60):
                            resultado['vencimento_str'] = v
                            resultado['vencimento'] = data
                            break
                    except:
                        continue

                # Se não encontrou futuro, pegar o primeiro
                if not resultado['vencimento_str'] and vencimentos:
                    resultado['vencimento_str'] = vencimentos[0]
                    try:
                        resultado['vencimento'] = datetime.strptime(vencimentos[0], '%d/%m/%Y')
                    except:
                        pass

            # VALOR - padrão: número no formato brasileiro (931,08)
            # Procurar após "Valor do Documento" ou "Valor Cobrado"
            valor_match = re.search(
                r'(?:Valor\s*(?:do\s*)?(?:Documento|Cobrado))\s*[\n\r]*\s*([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})',
                texto,
                re.IGNORECASE
            )
            if valor_match:
                resultado['valor_str'] = valor_match.group(1)
                resultado['valor'] = float(
                    valor_match.group(1).replace('.', '').replace(',', '.')
                )
            else:
                # Buscar padrão de valor brasileiro
                valores = re.findall(r'([\d]{1,3}(?:\.[\d]{3})*,[\d]{2})', texto)
                # Pegar valor mais provável (geralmente aparece várias vezes)
                if valores:
                    from collections import Counter
                    valor_comum = Counter(valores).most_common(1)[0][0]
                    resultado['valor_str'] = valor_comum
                    resultado['valor'] = float(valor_comum.replace('.', '').replace(',', '.'))

            # CPF - padrão: 000.000.000-00
            cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', texto)
            if cpf_match:
                resultado['cpf'] = cpf_match.group(1)
                # Contrato baseado no CPF
                resultado['contrato'] = f"CANOPUS-{cpf_match.group(1).replace('.', '').replace('-', '')}"

            # NOME DO PAGADOR - após "Pagador"
            nome_match = re.search(
                r'Pagador\s*[\n\r]*\s*([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ\s]+?)(?:\s*CPF|\s*\d{3}\.)',
                texto
            )
            if nome_match:
                resultado['nome_pagador'] = nome_match.group(1).strip()

            # GRUPO/COTA - padrão: 006660-3344-00
            grupo_match = re.search(r'Grupo/Cota(?:/Versão)?[:\s]+(\d+-\d+-\d+)', texto)
            if grupo_match:
                resultado['grupo_cota'] = grupo_match.group(1)

            # NOSSO NÚMERO
            nosso_match = re.search(r'Nosso\s*N[úu]mero\s*[\n\r]*\s*(\d+/\d+-\d+)', texto)
            if nosso_match:
                resultado['nosso_numero'] = nosso_match.group(1)

            # Verificar sucesso - pelo menos vencimento e valor devem ser extraídos
            resultado['sucesso'] = bool(resultado['vencimento_str'] and resultado['valor'] > 0)

            if resultado['sucesso']:
                logger.info(
                    f"✅ PDF extraído com sucesso: venc={resultado['vencimento_str']}, "
                    f"valor=R$ {resultado['valor']:.2f}, nome={resultado.get('nome_pagador', 'N/A')}"
                )
            else:
                logger.warning(f"⚠️ Extração parcial do PDF: {caminho_pdf}")

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados do PDF: {e}", exc_info=True)

        return resultado


# Instância global para reuso
_extractor = None

def get_extractor() -> BoletoExtractor:
    """Retorna instância singleton do extrator"""
    global _extractor
    if _extractor is None:
        _extractor = BoletoExtractor()
    return _extractor


def extrair_dados_boleto(caminho_pdf: str) -> Dict:
    """
    Função auxiliar para extrair dados do boleto.

    Args:
        caminho_pdf: Caminho completo do arquivo PDF

    Returns:
        Dict com dados extraídos (vencimento, valor, nome, etc)
    """
    return get_extractor().extrair_dados(caminho_pdf)


# Teste
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = r'D:\Nexus\automation\canopus\downloads\Danner\ZACARIAS_DOS_SANTOS_ARCANJO_IMOVEL_DEZEMBRO.pdf'

    print("=" * 70)
    print("TESTE: EXTRAÇÃO DE DADOS DO PDF")
    print("=" * 70)
    print(f"\n📄 PDF: {os.path.basename(pdf_path)}")

    if os.path.exists(pdf_path):
        dados = extrair_dados_boleto(pdf_path)

        print(f"\n📊 Resultado:")
        print(f"   Sucesso: {dados['sucesso']}")
        print(f"   Vencimento: {dados.get('vencimento_str', 'N/A')}")
        print(f"   Valor: R$ {dados.get('valor', 0):.2f}")
        print(f"   Nome: {dados.get('nome_pagador', 'N/A')}")
        print(f"   CPF: {dados.get('cpf', 'N/A')}")
        print(f"   Contrato: {dados.get('contrato', 'N/A')}")
        print(f"   Grupo/Cota: {dados.get('grupo_cota', 'N/A')}")
        print(f"   Nosso Número: {dados.get('nosso_numero', 'N/A')}")
        print()
    else:
        print(f"\n❌ PDF não encontrado: {pdf_path}")
        print("\nUso: python pdf_extractor.py [caminho_do_pdf]")
