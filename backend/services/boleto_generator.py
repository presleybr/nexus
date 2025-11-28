"""
Gerador de Boletos Bancários em PDF
Sistema Nexus CRM - Portal Consórcio
"""

import os
import random
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class BoletoGenerator:
    """Gerador de boletos bancários em PDF"""

    def __init__(self):
        self.boletos_dir = 'boletos'
        os.makedirs(self.boletos_dir, exist_ok=True)

    def gerar_linha_digitavel(self):
        """Gera linha digitável fake mas realista"""
        partes = []
        for _ in range(9):
            partes.append(f"{random.randint(10000, 99999)}")

        return f"{partes[0]}.{partes[1]} {partes[2]}.{partes[3]} {partes[4]}.{partes[5]} {partes[6]} {partes[7]}{partes[8]}"

    def gerar_nosso_numero(self):
        """Gera nosso número do banco"""
        return f"{random.randint(10000000, 99999999)}-{random.randint(0, 9)}"

    def gerar_codigo_barras_imagem(self, numero):
        """Gera imagem do código de barras"""
        try:
            # Limitar a 44 caracteres para Code128
            numero_str = str(numero)[:44]
            code = barcode.get('code128', numero_str, writer=ImageWriter())
            buffer = BytesIO()
            code.write(buffer, {'write_text': False, 'module_height': 8, 'module_width': 0.3})
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(f"Erro ao gerar código de barras: {e}")
            return None

    def gerar_boleto_pdf(self, cliente_final, valor, data_vencimento, numero_parcela):
        """Gera PDF do boleto completo"""
        try:
            # Nome do arquivo
            cpf_limpo = cliente_final['cpf'].replace('.', '').replace('-', '')
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"boleto_{cpf_limpo}_parcela{numero_parcela:02d}_{timestamp}.pdf"
            filepath = os.path.join(self.boletos_dir, filename)

            # Gerar dados do boleto
            linha_digitavel = self.gerar_linha_digitavel()
            nosso_numero = self.gerar_nosso_numero()
            codigo_barras = linha_digitavel.replace('.', '').replace(' ', '')

            # Criar PDF
            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4

            # ========== CABEÇALHO ==========
            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, height - 50, "BANCO CONSORCIO NACIONAL")

            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, "001-9  |  Banco Consórcio S/A")

            # Linha divisória verde neon
            c.setStrokeColor(colors.HexColor("#39FF14"))
            c.setLineWidth(2)
            c.line(50, height - 80, width - 50, height - 80)

            # ========== DADOS DO BENEFICIÁRIO ==========
            y = height - 110
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.HexColor("#39FF14"))
            c.drawString(50, y, "BENEFICIARIO")

            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(50, y - 18, "CONSORCIO NACIONAL S/A")
            c.drawString(50, y - 33, "CNPJ: 12.345.678/0001-90")
            c.drawString(50, y - 48, "Rua das Financas, 1000 - Centro - Sao Paulo/SP")

            # ========== DADOS DO PAGADOR ==========
            y = y - 90
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.HexColor("#39FF14"))
            c.drawString(50, y, "PAGADOR")

            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(50, y - 18, cliente_final['nome_completo'].upper())
            c.drawString(50, y - 33, f"CPF: {cliente_final['cpf']}")
            c.drawString(50, y - 48, f"Contrato: {cliente_final['numero_contrato']}")
            c.drawString(50, y - 63, f"Grupo: {cliente_final['grupo_consorcio']}  |  Cota: {cliente_final['cota_consorcio']}")

            if cliente_final.get('logradouro'):
                endereco = f"{cliente_final.get('logradouro', '')}, {cliente_final.get('numero', '')}"
                if cliente_final.get('complemento'):
                    endereco += f" - {cliente_final['complemento']}"
                c.drawString(50, y - 78, endereco)
                c.drawString(50, y - 93, f"{cliente_final.get('cidade', '')} - {cliente_final.get('estado', '')} - CEP: {cliente_final.get('cep', '')}")

            # ========== INFORMAÇÕES DO BOLETO ==========
            y = y - 130
            c.setStrokeColor(colors.HexColor("#39FF14"))
            c.setLineWidth(1)
            c.line(50, y, width - 50, y)

            y = y - 25
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.HexColor("#39FF14"))
            c.drawString(50, y, "INFORMACOES DO BOLETO")

            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(50, y - 20, "Nosso Numero:")
            c.setFont("Helvetica-Bold", 9)
            c.drawString(150, y - 20, nosso_numero)

            c.setFont("Helvetica", 9)
            c.drawString(50, y - 35, "Parcela:")
            c.setFont("Helvetica-Bold", 9)
            c.drawString(150, y - 35, f"{numero_parcela}/{cliente_final['prazo_meses']}")

            c.setFont("Helvetica", 9)
            c.drawString(50, y - 50, "Vencimento:")
            c.setFont("Helvetica-Bold", 11)
            c.setFillColor(colors.HexColor("#39FF14"))
            c.drawString(150, y - 50, data_vencimento.strftime('%d/%m/%Y'))

            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawString(50, y - 65, "Valor:")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(150, y - 65, f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

            c.setFont("Helvetica", 8)
            c.drawString(50, y - 85, f"Documento: {random.randint(100000, 999999)}")
            c.drawString(50, y - 100, f"Data Emissao: {datetime.now().strftime('%d/%m/%Y')}")

            # ========== LINHA DIGITÁVEL ==========
            y = y - 130
            c.setStrokeColor(colors.HexColor("#39FF14"))
            c.setLineWidth(1)
            c.rect(45, y - 35, width - 90, 40, stroke=1, fill=0)

            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.HexColor("#39FF14"))
            c.drawString(50, y - 10, "LINHA DIGITAVEL")

            c.setFont("Courier-Bold", 12)
            c.setFillColor(colors.black)
            c.drawString(50, y - 28, linha_digitavel)

            # ========== CÓDIGO DE BARRAS ==========
            y = y - 85
            barcode_img = self.gerar_codigo_barras_imagem(codigo_barras[:44])

            if barcode_img:
                # Usar ImageReader para ler BytesIO
                img_reader = ImageReader(barcode_img)
                c.drawImage(img_reader, 50, y - 50, width=450, height=45,
                           preserveAspectRatio=True, mask='auto')

            # ========== INSTRUÇÕES ==========
            y = y - 110
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor("#39FF14"))
            c.drawString(50, y, "INSTRUCOES")

            c.setFillColor(colors.black)
            c.setFont("Helvetica", 8)
            instrucoes = [
                "• Pagamento via PIX, boleto bancario ou debito automatico",
                "• Multa de 2% apos o vencimento",
                "• Juros de mora de 1% ao mes",
                "• Apos o vencimento, pagar somente nas agencias do Banco Consorcio",
                "• Nao receber apos 30 dias do vencimento"
            ]

            y_inst = y - 18
            for inst in instrucoes:
                c.drawString(50, y_inst, inst)
                y_inst -= 15

            # ========== RODAPÉ ==========
            c.setStrokeColor(colors.HexColor("#39FF14"))
            c.setLineWidth(1)
            c.line(50, 80, width - 50, 80)

            c.setFont("Helvetica", 7)
            c.setFillColor(colors.gray)
            c.drawString(50, 60, f"Documento gerado automaticamente pelo Sistema Nexus CRM em {datetime.now().strftime('%d/%m/%Y as %H:%M')}")
            c.drawString(50, 48, "Este boleto e valido apenas para pagamento do consorcio especificado. Autenticacao mecanica.")
            c.drawString(50, 36, "Em caso de duvidas, entre em contato com a Central de Atendimento: 0800 123 4567")

            # Finalizar PDF
            c.save()

            file_size = os.path.getsize(filepath)

            logger.info(f"[OK] Boleto gerado: {filename} ({file_size} bytes)")

            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'file_size': file_size,
                'linha_digitavel': linha_digitavel,
                'codigo_barras': codigo_barras,
                'nosso_numero': nosso_numero
            }

        except Exception as e:
            logger.error(f"[ERROR] Erro ao gerar boleto: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


# Instância global
boleto_generator = BoletoGenerator()
