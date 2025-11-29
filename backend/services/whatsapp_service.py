"""
Serviço de WhatsApp - Integração para envio de mensagens e PDFs
INTEGRADO COM WPPCONNECT - Conecta a servidor WPPConnect externo
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, Optional, List
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models import log_sistema, ClienteNexus
from services.wppconnect_service import wppconnect_service


class WhatsAppService:
    """Serviço de integração com WhatsApp via WPPConnect"""

    def __init__(self):
        self.session_dir = Config.WHATSAPP_PATH
        self.wpp = wppconnect_service
        self.session_data = {}

    def conectar(self) -> Dict:
        """
        Inicia conexão com WhatsApp Web via WPPConnect

        Returns:
            Dict com status da operação
        """
        try:
            resultado = self.wpp.iniciar_conexao()

            if resultado.get('success'):
                log_sistema('info', 'WhatsApp iniciado via WPPConnect', 'whatsapp', {})

            return resultado

        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao conectar: {str(e)}'
            }

    def gerar_qr_code(self, cliente_nexus_id: int) -> Dict:
        """
        Gera QR Code para conexão WhatsApp via WPPConnect

        Args:
            cliente_nexus_id: ID do cliente Nexus

        Returns:
            Dicionário com dados do QR Code
        """
        try:
            # Obtém o QR Code
            resultado_qr = self.wpp.obter_qr_code()

            if resultado_qr.get('connected'):
                # Já está conectado
                phone = resultado_qr.get('phone')

                log_sistema('success', f'WhatsApp já conectado: {phone}',
                           'whatsapp', {'cliente_nexus_id': cliente_nexus_id})

                return {
                    'qr_code': None,
                    'timestamp': datetime.now().isoformat(),
                    'cliente_nexus_id': cliente_nexus_id,
                    'status': 'conectado',
                    'phone': phone
                }

            if resultado_qr.get('qr'):
                # QR Code disponível
                log_sistema('info', 'QR Code gerado via WPPConnect',
                           'whatsapp', {'cliente_nexus_id': cliente_nexus_id})

                return {
                    'qr_code': resultado_qr.get('qr'),
                    'timestamp': datetime.now().isoformat(),
                    'cliente_nexus_id': cliente_nexus_id,
                    'status': 'aguardando_conexao'
                }

            # QR Code ainda não disponível
            return {
                'qr_code': None,
                'timestamp': datetime.now().isoformat(),
                'cliente_nexus_id': cliente_nexus_id,
                'status': 'aguardando',
                'mensagem': resultado_qr.get('message', 'Aguarde enquanto o QR Code é gerado...')
            }

        except Exception as e:
            log_sistema('error', f'Erro ao gerar QR Code: {str(e)}',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})
            return {
                'qr_code': None,
                'timestamp': datetime.now().isoformat(),
                'cliente_nexus_id': cliente_nexus_id,
                'status': 'erro',
                'erro': str(e)
            }

    def verificar_conexao(self, cliente_nexus_id: int) -> bool:
        """
        Verifica se o WhatsApp está conectado via WPPConnect

        Args:
            cliente_nexus_id: ID do cliente

        Returns:
            True se conectado, False caso contrário
        """
        status = self.wpp.verificar_status()
        return status.get('connected', False)

    def conectar(self, cliente_nexus_id: int, numero_whatsapp: str = None) -> bool:
        """
        Conecta ao WhatsApp via WPPConnect

        Args:
            cliente_nexus_id: ID do cliente
            numero_whatsapp: Número do WhatsApp (opcional, obtido automaticamente)

        Returns:
            True se conectado com sucesso
        """
        try:
            status = self.wpp.verificar_status()

            if status.get('connected'):
                phone = status.get('phone')

                self.session_data[cliente_nexus_id] = {
                    'numero': phone,
                    'conectado_em': datetime.now().isoformat()
                }

                # Atualiza no banco
                if phone:
                    ClienteNexus.atualizar_whatsapp(cliente_nexus_id, phone, True)

                log_sistema('success', f'WhatsApp conectado via WPPConnect: {phone}',
                           'whatsapp', {'cliente_nexus_id': cliente_nexus_id})

                return True

            return False

        except Exception as e:
            log_sistema('error', f'Erro ao verificar conexão WhatsApp: {str(e)}',
                       'whatsapp', {'cliente_nexus_id': cliente_nexus_id})
            return False

    def enviar_mensagem(self, numero_destino: str, mensagem: str,
                       cliente_nexus_id: int = None) -> Dict:
        """
        Envia uma mensagem de texto via WhatsApp usando WPPConnect

        Args:
            numero_destino: Número do destinatário (formato: 5511999999999)
            mensagem: Texto da mensagem
            cliente_nexus_id: ID do cliente (opcional)

        Returns:
            Dicionário com resultado do envio
        """
        resultado = self.wpp.enviar_mensagem(
            numero=numero_destino,
            mensagem=mensagem,
            cliente_nexus_id=cliente_nexus_id
        )

        # Converte o formato de resposta para manter compatibilidade
        if resultado.get('success'):
            return {
                'sucesso': True,
                'numero': resultado.get('numero', numero_destino),
                'mensagem': mensagem,
                'timestamp': datetime.now().isoformat(),
                'id_mensagem': resultado.get('messageId', f"msg_{int(time.time() * 1000)}")
            }
        else:
            return {
                'sucesso': False,
                'erro': resultado.get('error', 'Erro desconhecido'),
                'timestamp': datetime.now().isoformat()
            }

    def enviar_pdf(self, numero_destino: str, pdf_path: str,
                   legenda: str = None, cliente_nexus_id: int = None) -> Dict:
        """
        Envia um arquivo PDF via WhatsApp usando WPPConnect

        Args:
            numero_destino: Número do destinatário
            pdf_path: Caminho do arquivo PDF
            legenda: Legenda opcional
            cliente_nexus_id: ID do cliente

        Returns:
            Dicionário com resultado do envio
        """
        resultado = self.wpp.enviar_pdf(
            numero=numero_destino,
            pdf_path=pdf_path,
            legenda=legenda or "Segue seu boleto em anexo",
            cliente_nexus_id=cliente_nexus_id
        )

        # Converte o formato de resposta para manter compatibilidade
        if resultado.get('success'):
            return {
                'sucesso': True,
                'numero': resultado.get('numero', numero_destino),
                'arquivo': os.path.basename(pdf_path),
                'tamanho_kb': os.path.getsize(pdf_path) / 1024 if os.path.exists(pdf_path) else 0,
                'legenda': legenda,
                'timestamp': datetime.now().isoformat(),
                'id_mensagem': resultado.get('messageId', f"msg_{int(time.time() * 1000)}")
            }
        else:
            return {
                'sucesso': False,
                'erro': resultado.get('error', 'Erro desconhecido'),
                'timestamp': datetime.now().isoformat()
            }

    def enviar_com_antibloqueio(self, numero_destino: str, pdf_path: str,
                               mensagem_antibloqueio: str,
                               intervalo: int = 5,
                               cliente_nexus_id: int = None) -> Dict:
        """
        Envia mensagem personalizada + PDF do boleto com delay anti-bloqueio

        Args:
            numero_destino: Número do destinatário
            pdf_path: Caminho do PDF
            mensagem_antibloqueio: Mensagem personalizada do boleto
            intervalo: Intervalo entre mensagem e PDF em segundos (padrão: 5s)
            cliente_nexus_id: ID do cliente

        Returns:
            Dicionário com resultados
        """
        import time

        log_sistema('info',
                   f'📤 Iniciando disparo para {numero_destino}',
                   'whatsapp',
                   {'intervalo': intervalo})

        resultados = {
            'mensagem_antibloqueio': None,
            'pdf': None,
            'sucesso_total': False
        }

        try:
            # 1. Enviar mensagem personalizada
            log_sistema('info', '📝 Enviando mensagem personalizada do boleto...', 'whatsapp')

            resultado_msg = self.wpp.enviar_mensagem(
                numero=numero_destino,
                mensagem=mensagem_antibloqueio,
                cliente_nexus_id=cliente_nexus_id
            )
            resultados['mensagem_antibloqueio'] = resultado_msg

            if resultado_msg.get('success'):
                log_sistema('success', '✅ Mensagem enviada com sucesso', 'whatsapp')
            else:
                log_sistema('error', f'❌ Erro ao enviar mensagem: {resultado_msg.get("error")}', 'whatsapp')
                return resultados

            # 2. Aguarda intervalo antes do PDF
            log_sistema('info', f'⏳ Aguardando {intervalo}s antes de enviar PDF...', 'whatsapp')
            time.sleep(intervalo)

            # 3. Enviar PDF
            log_sistema('info', '📎 Enviando PDF do boleto...', 'whatsapp')
            resultado_pdf = self.wpp.enviar_pdf(
                numero=numero_destino,
                pdf_path=pdf_path,
                legenda="Segue seu boleto em anexo",
                cliente_nexus_id=cliente_nexus_id
            )
            resultados['pdf'] = resultado_pdf

            if resultado_pdf.get('success'):
                log_sistema('success', '✅ PDF enviado com sucesso', 'whatsapp')
            else:
                log_sistema('error', f'❌ Erro ao enviar PDF: {resultado_pdf.get("error")}', 'whatsapp')

            # 4. Verifica sucesso total
            resultados['sucesso_total'] = (
                resultado_msg.get('success') and resultado_pdf.get('success')
            )

            if resultados['sucesso_total']:
                log_sistema('success', '🎉 Disparo completo! Mensagem + PDF enviados', 'whatsapp')
            else:
                log_sistema('warning', '⚠️ Disparo incompleto', 'whatsapp', resultados)

            return resultados

        except Exception as e:
            log_sistema('error', f'❌ Erro no disparo: {str(e)}', 'whatsapp')
            resultados['erro'] = str(e)
            return resultados

    def enviar_em_massa(self, destinatarios: List[Dict],
                       cliente_nexus_id: int) -> Dict:
        """
        Envia mensagens em massa via WPPConnect

        Args:
            destinatarios: Lista de dicts com 'numero', 'mensagem' ou 'pdf_path'
            cliente_nexus_id: ID do cliente

        Returns:
            Estatísticas do envio em massa
        """
        return self.wpp.enviar_em_massa(
            destinatarios=destinatarios,
            cliente_nexus_id=cliente_nexus_id
        )

    def desconectar(self, cliente_nexus_id: int):
        """Desconecta do WhatsApp via WPPConnect"""
        resultado = self.wpp.desconectar(cliente_nexus_id=cliente_nexus_id)

        if resultado.get('success'):
            if cliente_nexus_id in self.session_data:
                del self.session_data[cliente_nexus_id]

            ClienteNexus.atualizar_whatsapp(cliente_nexus_id, None, False)

        return resultado


# Instância global do serviço
whatsapp_service = WhatsAppService()
