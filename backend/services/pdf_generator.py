"""
Serviço de Geração de PDFs de Boletos
Utiliza ReportLab para gerar boletos profissionais
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
from datetime import datetime, date
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


class BoletoGenerator:
    """Classe para gerar PDFs de boletos"""

    def __init__(self):
        self.page_width, self.page_height = A4

    def gerar_boleto(self, dados_boleto: dict, output_path: str) -> str:
        """
        Gera um boleto em PDF

        Args:
            dados_boleto: Dicionário com dados do boleto
                - beneficiario: nome da empresa
                - cnpj_beneficiario: CNPJ
                - pagador: nome do cliente
                - cpf_pagador: CPF
                - valor: valor do boleto
                - vencimento: data de vencimento
                - mes_referencia: mês de referência
                - numero_documento: número do documento

            output_path: Caminho onde o PDF será salvo

        Returns:
            Caminho do arquivo gerado
        """
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Cria o PDF
        c = canvas.Canvas(output_path, pagesize=A4)

        # Desenha o boleto
        self._desenhar_cabecalho(c, dados_boleto)
        self._desenhar_dados_beneficiario(c, dados_boleto)
        self._desenhar_dados_pagador(c, dados_boleto)
        self._desenhar_valores(c, dados_boleto)
        self._desenhar_rodape(c, dados_boleto)

        # Finaliza o PDF
        c.save()

        return output_path

    def _desenhar_cabecalho(self, c: canvas.Canvas, dados: dict):
        """Desenha o cabeçalho do boleto"""
        # Cor da marca Nexus
        cor_nexus = HexColor('#00d4ff')

        # Retângulo superior azul
        c.setFillColor(cor_nexus)
        c.rect(0, self.page_height - 60*mm, self.page_width, 60*mm, fill=True, stroke=False)

        # Título
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(self.page_width/2, self.page_height - 30*mm, "BOLETO DE PAGAMENTO")

        # Subtítulo
        c.setFont("Helvetica", 12)
        c.drawCentredString(self.page_width/2, self.page_height - 40*mm,
                           f"Referência: {dados.get('mes_referencia', 'N/A')}")

        # Data de emissão
        c.setFont("Helvetica", 10)
        data_emissao = datetime.now().strftime("%d/%m/%Y")
        c.drawCentredString(self.page_width/2, self.page_height - 50*mm,
                           f"Emitido em: {data_emissao}")

    def _desenhar_dados_beneficiario(self, c: canvas.Canvas, dados: dict):
        """Desenha os dados do beneficiário"""
        y_start = self.page_height - 80*mm

        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30*mm, y_start, "BENEFICIÁRIO")

        c.setFont("Helvetica", 10)
        y = y_start - 8*mm

        # Nome da empresa
        c.drawString(30*mm, y, f"Nome: {dados.get('beneficiario', 'N/A')}")
        y -= 6*mm

        # CNPJ
        c.drawString(30*mm, y, f"CNPJ: {dados.get('cnpj_beneficiario', 'N/A')}")
        y -= 6*mm

        # Linha separadora
        c.setStrokeColor(HexColor('#cccccc'))
        c.line(20*mm, y - 2*mm, self.page_width - 20*mm, y - 2*mm)

    def _desenhar_dados_pagador(self, c: canvas.Canvas, dados: dict):
        """Desenha os dados do pagador"""
        y_start = self.page_height - 115*mm

        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30*mm, y_start, "PAGADOR")

        c.setFont("Helvetica", 10)
        y = y_start - 8*mm

        # Nome
        c.drawString(30*mm, y, f"Nome: {dados.get('pagador', 'N/A')}")
        y -= 6*mm

        # CPF
        c.drawString(30*mm, y, f"CPF: {dados.get('cpf_pagador', 'N/A')}")
        y -= 6*mm

        # Endereço (se fornecido)
        if dados.get('endereco_pagador'):
            c.drawString(30*mm, y, f"Endereço: {dados['endereco_pagador']}")
            y -= 6*mm

        # Linha separadora
        c.setStrokeColor(HexColor('#cccccc'))
        c.line(20*mm, y - 2*mm, self.page_width - 20*mm, y - 2*mm)

    def _desenhar_valores(self, c: canvas.Canvas, dados: dict):
        """Desenha os valores e datas do boleto"""
        y_start = self.page_height - 155*mm

        # Caixa de destaque para o valor
        cor_caixa = HexColor('#f0f0f0')
        c.setFillColor(cor_caixa)
        c.rect(20*mm, y_start - 25*mm, self.page_width - 40*mm, 30*mm,
               fill=True, stroke=True)

        # Valor
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(30*mm, y_start - 8*mm, "VALOR DO DOCUMENTO")

        valor = dados.get('valor', 0)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(30*mm, y_start - 18*mm, f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # Vencimento
        c.setFont("Helvetica-Bold", 11)
        c.drawString(120*mm, y_start - 8*mm, "VENCIMENTO")

        vencimento = dados.get('vencimento')
        if isinstance(vencimento, date):
            vencimento_str = vencimento.strftime("%d/%m/%Y")
        else:
            vencimento_str = str(vencimento)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(120*mm, y_start - 18*mm, vencimento_str)

        # Número do documento
        y = y_start - 35*mm
        c.setFont("Helvetica", 10)
        c.drawString(30*mm, y, f"Número do documento: {dados.get('numero_documento', 'N/A')}")

        # Linha separadora
        c.setStrokeColor(HexColor('#cccccc'))
        c.line(20*mm, y - 4*mm, self.page_width - 20*mm, y - 4*mm)

    def _desenhar_rodape(self, c: canvas.Canvas, dados: dict):
        """Desenha o rodapé do boleto"""
        y_rodape = 40*mm

        # Instruções
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30*mm, y_rodape + 15*mm, "INSTRUÇÕES")

        c.setFont("Helvetica", 9)
        c.drawString(30*mm, y_rodape + 9*mm, "• Pagar preferencialmente até a data de vencimento")
        c.drawString(30*mm, y_rodape + 5*mm, "• Em caso de dúvidas, entre em contato com o beneficiário")
        c.drawString(30*mm, y_rodape + 1*mm, "• Boleto gerado automaticamente pelo Sistema CRM Nexus")

        # Linha final
        c.setStrokeColor(HexColor('#00d4ff'))
        c.setLineWidth(2)
        c.line(20*mm, 30*mm, self.page_width - 20*mm, 30*mm)

        # Logo/Texto Nexus
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(HexColor('#00d4ff'))
        c.drawCentredString(self.page_width/2, 20*mm, "NEXUS CRM")

        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor('#666666'))
        c.drawCentredString(self.page_width/2, 15*mm,
                           "Aqui seu tempo vale ouro - Sistema de automação de boletos")

    def gerar_boletos_em_lote(self, lista_boletos: list, diretorio_base: str) -> list:
        """
        Gera múltiplos boletos de uma vez

        Args:
            lista_boletos: Lista de dicionários com dados dos boletos
            diretorio_base: Diretório base para salvar os PDFs

        Returns:
            Lista de caminhos dos arquivos gerados
        """
        arquivos_gerados = []

        for i, boleto_data in enumerate(lista_boletos):
            try:
                # Define o nome do arquivo
                cliente_nome = boleto_data.get('pagador', 'cliente').replace(' ', '_')
                mes_ref = boleto_data.get('mes_referencia', 'mes').replace('/', '_')
                filename = f"boleto_{cliente_nome}_{mes_ref}_{i+1}.pdf"

                output_path = os.path.join(diretorio_base, filename)

                # Gera o boleto
                caminho = self.gerar_boleto(boleto_data, output_path)
                arquivos_gerados.append(caminho)

            except Exception as e:
                print(f"❌ Erro ao gerar boleto {i+1}: {e}")
                continue

        return arquivos_gerados


def criar_boleto_exemplo():
    """Cria um boleto de exemplo para testes"""
    generator = BoletoGenerator()

    dados_exemplo = {
        'beneficiario': 'EMPRESA EXEMPLO LTDA',
        'cnpj_beneficiario': '12.345.678/0001-90',
        'pagador': 'João da Silva',
        'cpf_pagador': '123.456.789-00',
        'endereco_pagador': 'Rua Exemplo, 123 - São Paulo/SP',
        'valor': 1500.00,
        'vencimento': date(2024, 12, 31),
        'mes_referencia': 'Dezembro/2024',
        'numero_documento': '000001'
    }

    output_dir = os.path.join(Config.BASE_DIR, 'boletos', 'exemplos')
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'boleto_exemplo.pdf')

    caminho = generator.gerar_boleto(dados_exemplo, output_path)
    print(f"✅ Boleto de exemplo criado: {caminho}")

    return caminho


if __name__ == '__main__':
    # Testa a geração de boleto
    criar_boleto_exemplo()
