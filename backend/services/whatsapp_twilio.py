"""
Serviço de WhatsApp usando Twilio
Integração completa para envio de mensagens e PDFs via WhatsApp
"""

from twilio.rest import Client
import logging
import time
import random
from typing import Dict, Any, Optional

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WhatsAppTwilio:
    """
    Classe para integração com Twilio WhatsApp API
    """

    def __init__(self):
        """Inicializa o serviço Twilio WhatsApp"""
        self.account_sid = 'AC3daccc77955ee03eccdd580bf494bb08'
        self.auth_token = '980d3137ee8bbecba9997d5b36398475'
        self.from_number = 'whatsapp:+14155238886'

        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✅ Twilio WhatsApp Service inicializado com sucesso")
            logger.info(f"📱 Número Twilio: {self.from_number}")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Twilio: {str(e)}")
            raise

    def conectar(self) -> Dict[str, Any]:
        """
        Twilio não precisa conectar - sempre disponível
        Retorna status de sucesso imediatamente
        """
        logger.info("🔌 Conectar chamado - Twilio sempre disponível")
        return {
            "success": True,
            "message": "Twilio WhatsApp está sempre conectado! Pronto para enviar mensagens.",
            "connected": True
        }

    def verificar_status(self) -> Dict[str, Any]:
        """
        Verifica status da conta Twilio
        Testa se as credenciais são válidas
        """
        try:
            logger.info("🔍 Verificando status da conta Twilio...")

            # Buscar informações da conta para validar credenciais
            account = self.client.api.accounts(self.account_sid).fetch()

            logger.info(f"✅ Conta Twilio ativa: {account.friendly_name}")

            return {
                "connected": True,
                "success": True,
                "status": "connected",
                "phone": self.from_number,
                "account_name": account.friendly_name,
                "account_sid": self.account_sid
            }

        except Exception as e:
            logger.error(f"❌ Erro ao verificar status Twilio: {str(e)}")
            return {
                "connected": False,
                "success": False,
                "status": "error",
                "phone": None,
                "error": str(e)
            }

    def esta_conectado(self) -> bool:
        """
        Verifica se está conectado (Twilio sempre está)
        """
        try:
            status = self.verificar_status()
            return status.get('connected', False)
        except Exception:
            return False

    def obter_qr(self) -> Dict[str, Any]:
        """
        Twilio não usa QR Code
        Retorna mensagem informando que não é necessário
        """
        logger.info("📱 QR Code solicitado - Twilio não requer QR Code")
        return {
            "success": True,
            "connected": True,
            "qr": None,
            "message": "Twilio não requer QR Code. Já está conectado e pronto para uso!"
        }

    def formatar_telefone(self, telefone: str) -> str:
        """
        Formata número de telefone para padrão Twilio WhatsApp

        Args:
            telefone: Número em qualquer formato (ex: 67999887766, +5567999887766)

        Returns:
            str: Número formatado no padrão Twilio (whatsapp:+5567999887766)
        """
        # Remover todos os caracteres não numéricos
        telefone_limpo = ''.join(filter(str.isdigit, telefone))

        # Adicionar código do Brasil (+55) se não tiver
        if not telefone_limpo.startswith('55'):
            telefone_limpo = '55' + telefone_limpo

        # Formato Twilio: whatsapp:+5567999887766
        telefone_formatado = f'whatsapp:+{telefone_limpo}'

        logger.debug(f"📞 Telefone formatado: {telefone} → {telefone_formatado}")

        return telefone_formatado

    def enviar_mensagem(self, telefone: str, mensagem: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto via Twilio WhatsApp

        Args:
            telefone: Número do destinatário
            mensagem: Texto da mensagem

        Returns:
            dict: Resultado do envio com status e SID
        """
        try:
            telefone_formatado = self.formatar_telefone(telefone)

            logger.info(f"📤 Enviando mensagem para {telefone_formatado}")
            logger.debug(f"💬 Mensagem: {mensagem[:50]}...")

            # Enviar mensagem via Twilio
            message = self.client.messages.create(
                from_=self.from_number,
                body=mensagem,
                to=telefone_formatado
            )

            logger.info(f"✅ Mensagem enviada! SID: {message.sid}, Status: {message.status}")

            return {
                "success": True,
                "message": "Mensagem enviada com sucesso",
                "message_sid": message.sid,
                "status": message.status,
                "to": telefone_formatado,
                "from": self.from_number
            }

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem para {telefone}: {str(e)}")
            return {
                "success": False,
                "error": f"Erro ao enviar mensagem: {str(e)}"
            }

    def enviar_pdf(self, telefone: str, pdf_url: str, caption: str = "Segue anexo", filename: str = "documento.pdf") -> Dict[str, Any]:
        """
        Envia PDF via WhatsApp usando Twilio

        IMPORTANTE: Twilio precisa de URL pública do PDF.
        Para localhost, use ngrok ou hospede temporariamente.

        Args:
            telefone: Número do destinatário
            pdf_url: URL pública do PDF
            caption: Legenda do arquivo
            filename: Nome do arquivo (não usado pelo Twilio)

        Returns:
            dict: Resultado do envio
        """
        try:
            telefone_formatado = self.formatar_telefone(telefone)

            logger.info(f"📎 Enviando PDF para {telefone_formatado}")
            logger.info(f"🔗 URL: {pdf_url}")

            # Enviar PDF via Twilio
            message = self.client.messages.create(
                from_=self.from_number,
                body=caption,
                media_url=[pdf_url],
                to=telefone_formatado
            )

            logger.info(f"✅ PDF enviado! SID: {message.sid}, Status: {message.status}")

            return {
                "success": True,
                "message": "PDF enviado com sucesso",
                "message_sid": message.sid,
                "status": message.status,
                "to": telefone_formatado
            }

        except Exception as e:
            logger.error(f"❌ Erro ao enviar PDF para {telefone}: {str(e)}")
            return {
                "success": False,
                "error": f"Erro ao enviar PDF: {str(e)}"
            }

    def enviar_imagem(self, telefone: str, imagem_url: str, caption: str = "") -> Dict[str, Any]:
        """
        Envia imagem via WhatsApp

        Args:
            telefone: Número do destinatário
            imagem_url: URL pública da imagem
            caption: Legenda da imagem

        Returns:
            dict: Resultado do envio
        """
        try:
            telefone_formatado = self.formatar_telefone(telefone)

            logger.info(f"🖼️ Enviando imagem para {telefone_formatado}")

            message = self.client.messages.create(
                from_=self.from_number,
                body=caption,
                media_url=[imagem_url],
                to=telefone_formatado
            )

            logger.info(f"✅ Imagem enviada! SID: {message.sid}")

            return {
                "success": True,
                "message": "Imagem enviada com sucesso",
                "message_sid": message.sid,
                "status": message.status
            }

        except Exception as e:
            logger.error(f"❌ Erro ao enviar imagem: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def enviar_boleto_completo(self, telefone: str, pdf_url: str, mensagem_antibloqueio: str,
                              delay_min: int = 3, delay_max: int = 7) -> Dict[str, Any]:
        """
        Envia mensagem + PDF com delay anti-spam

        Estratégia:
        1. Envia mensagem de texto personalizada
        2. Aguarda delay aleatório (3-7 segundos)
        3. Envia PDF do boleto

        Args:
            telefone: Número do destinatário
            pdf_url: URL pública do PDF do boleto
            mensagem_antibloqueio: Mensagem personalizada antes do PDF
            delay_min: Delay mínimo em segundos
            delay_max: Delay máximo em segundos

        Returns:
            dict: Resultado do envio completo
        """
        try:
            resultados = {
                'mensagem': None,
                'delay': None,
                'pdf': None
            }

            # 1. Enviar mensagem de texto
            logger.info(f"📤 [BOLETO] Enviando mensagem anti-bloqueio para {telefone}")
            result_msg = self.enviar_mensagem(telefone, mensagem_antibloqueio)
            resultados['mensagem'] = result_msg

            if not result_msg.get('success'):
                return {
                    'success': False,
                    'error': 'Falha ao enviar mensagem de texto',
                    'steps': resultados
                }

            # 2. Delay aleatório
            delay = random.randint(delay_min, delay_max)
            resultados['delay'] = delay
            logger.info(f"⏳ [BOLETO] Aguardando {delay}s antes de enviar PDF...")
            time.sleep(delay)

            # 3. Enviar PDF
            logger.info(f"📎 [BOLETO] Enviando PDF para {telefone}")
            result_pdf = self.enviar_pdf(telefone, pdf_url, "Segue boleto em anexo")
            resultados['pdf'] = result_pdf

            if not result_pdf.get('success'):
                return {
                    'success': False,
                    'error': 'Falha ao enviar PDF',
                    'steps': resultados
                }

            logger.info(f"✅ [BOLETO] Envio completo para {telefone}")

            return {
                'success': True,
                'message': 'Mensagem e PDF enviados com sucesso',
                'steps': resultados
            }

        except Exception as e:
            logger.error(f"❌ [BOLETO] Erro no envio completo: {str(e)}")
            return {
                "success": False,
                "error": f"Erro no envio completo: {str(e)}"
            }

    def desconectar(self) -> Dict[str, Any]:
        """
        Twilio não precisa desconectar - sempre disponível
        """
        logger.info("🔌 Desconectar chamado - Twilio sempre disponível")
        return {
            "success": True,
            "message": "Twilio WhatsApp está sempre disponível. Não é necessário desconectar."
        }


# Instância global do serviço Twilio
whatsapp_service = WhatsAppTwilio()
