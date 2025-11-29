import requests
import logging
import time
import random
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppEvolution:
    """Serviço WhatsApp usando Evolution API"""

    def __init__(self):
        self.base_url = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
        self.api_key = os.getenv('EVOLUTION_API_KEY', 'nexus-evolution-key-2025-secure')
        self.instance_name = os.getenv('EVOLUTION_INSTANCE_NAME', 'nexus_whatsapp')

        self.headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key
        }

        logger.info(f"✅ WhatsApp Evolution Service inicializado: {self.base_url}")

    def _make_request(self, method, endpoint, data=None):
        """Faz requisição HTTP para Evolution API"""
        try:
            url = f"{self.base_url}{endpoint}"

            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro na requisição para Evolution API: {str(e)}")
            return {'error': str(e)}

    def criar_instancia(self):
        """Cria instância do WhatsApp se não existir"""
        try:
            logger.info(f"📱 Criando instância: {self.instance_name}")

            data = {
                "instanceName": self.instance_name,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }

            result = self._make_request('POST', '/instance/create', data)

            if 'error' in result:
                # Instância pode já existir
                logger.info(f"ℹ️ Instância pode já existir: {result.get('error')}")
                return {'success': True, 'message': 'Instância já existe ou foi criada'}

            logger.info(f"✅ Instância criada: {self.instance_name}")
            return {'success': True, 'data': result}

        except Exception as e:
            logger.error(f"❌ Erro ao criar instância: {str(e)}")
            return {'success': False, 'error': str(e)}

    def conectar(self):
        """Inicia conexão WhatsApp (gera QR Code)"""
        try:
            logger.info(f"📲 Iniciando conexão para instância: {self.instance_name}")

            # Criar instância se não existir
            self.criar_instancia()

            # Conectar
            endpoint = f'/instance/connect/{self.instance_name}'
            result = self._make_request('GET', endpoint)

            if 'error' in result:
                return {'success': False, 'error': result['error']}

            logger.info(f"✅ Conexão iniciada")
            return {'success': True, 'message': 'Conexão iniciada. Aguarde QR Code...'}

        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {str(e)}")
            return {'success': False, 'error': str(e)}

    def obter_qr(self):
        """Obtém QR Code da instância"""
        try:
            endpoint = f'/instance/connect/{self.instance_name}'
            result = self._make_request('GET', endpoint)

            if 'error' in result:
                return {'success': False, 'error': result['error']}

            # Evolution API retorna QR Code em base64
            if result.get('qrcode'):
                qr_base64 = result['qrcode'].get('base64')
                if qr_base64:
                    logger.info(f"📱 QR Code obtido")
                    return {
                        'success': True,
                        'connected': False,
                        'qr': qr_base64 if qr_base64.startswith('data:image') else f'data:image/png;base64,{qr_base64}'
                    }

            # Se não tem QR, verificar se já está conectado
            status = self.verificar_status()
            if status.get('connected'):
                return {'success': True, 'connected': True, 'qr': None}

            return {'success': False, 'message': 'QR Code não disponível'}

        except Exception as e:
            logger.error(f"❌ Erro ao obter QR: {str(e)}")
            return {'success': False, 'error': str(e)}

    def verificar_status(self):
        """Verifica status da conexão"""
        try:
            endpoint = f'/instance/connectionState/{self.instance_name}'
            result = self._make_request('GET', endpoint)

            if 'error' in result:
                return {
                    'connected': False,
                    'status': 'disconnected',
                    'phone': None
                }

            state = result.get('state', 'close')

            # Estados possíveis: open, connecting, close
            is_connected = state == 'open'

            status_map = {
                'open': 'connected',
                'connecting': 'connecting',
                'close': 'disconnected'
            }

            return {
                'connected': is_connected,
                'status': status_map.get(state, 'disconnected'),
                'phone': result.get('instance', {}).get('owner') if is_connected else None
            }

        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {str(e)}")
            return {
                'connected': False,
                'status': 'error',
                'phone': None,
                'error': str(e)
            }

    def formatar_telefone(self, telefone):
        """Formata telefone para padrão Evolution API"""
        # Remover formatação
        telefone_limpo = ''.join(filter(str.isdigit, telefone))

        # Adicionar código do Brasil se não tiver
        if not telefone_limpo.startswith('55'):
            telefone_limpo = '55' + telefone_limpo

        # Evolution API usa formato: 5567999887766@s.whatsapp.net
        if not telefone_limpo.endswith('@s.whatsapp.net'):
            telefone_limpo = f'{telefone_limpo}@s.whatsapp.net'

        return telefone_limpo

    def enviar_mensagem(self, telefone, mensagem):
        """Envia mensagem de texto"""
        try:
            telefone_formatado = self.formatar_telefone(telefone)

            logger.info(f"📤 Enviando mensagem para {telefone_formatado}")

            endpoint = f'/message/sendText/{self.instance_name}'
            data = {
                "number": telefone_formatado,
                "text": mensagem,
                "delay": 1000
            }

            result = self._make_request('POST', endpoint, data)

            if 'error' in result:
                return {'success': False, 'error': result['error']}

            logger.info(f"✅ Mensagem enviada para {telefone}")
            return {
                'success': True,
                'message_id': result.get('key', {}).get('id'),
                'status': 'sent'
            }

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {str(e)}")
            return {'success': False, 'error': str(e)}

    def enviar_pdf(self, telefone, pdf_path, caption="", filename="documento.pdf"):
        """Envia arquivo PDF"""
        try:
            telefone_formatado = self.formatar_telefone(telefone)

            logger.info(f"📎 Enviando PDF para {telefone_formatado}: {pdf_path}")

            # Evolution API aceita base64 ou URL
            import base64
            with open(pdf_path, 'rb') as f:
                pdf_base64 = base64.b64encode(f.read()).decode('utf-8')

            endpoint = f'/message/sendMedia/{self.instance_name}'
            data = {
                "number": telefone_formatado,
                "mediatype": "document",
                "mimetype": "application/pdf",
                "caption": caption,
                "fileName": filename,
                "media": pdf_base64
            }

            result = self._make_request('POST', endpoint, data)

            if 'error' in result:
                return {'success': False, 'error': result['error']}

            logger.info(f"✅ PDF enviado para {telefone}")
            return {
                'success': True,
                'message_id': result.get('key', {}).get('id'),
                'status': 'sent'
            }

        except Exception as e:
            logger.error(f"❌ Erro ao enviar PDF: {str(e)}")
            return {'success': False, 'error': str(e)}

    def enviar_boleto_completo(self, telefone, pdf_path, mensagem_antibloqueio):
        """Envia mensagem + PDF com delay anti-bloqueio"""
        try:
            logger.info(f"📤 Enviando boleto completo para {telefone}")

            # 1. Enviar mensagem de texto
            result_msg = self.enviar_mensagem(telefone, mensagem_antibloqueio)

            if not result_msg.get('success'):
                return result_msg

            # 2. Delay aleatório (3-7 segundos)
            delay = random.randint(3, 7)
            logger.info(f"⏳ Aguardando {delay}s antes de enviar PDF...")
            time.sleep(delay)

            # 3. Enviar PDF
            result_pdf = self.enviar_pdf(telefone, pdf_path, "Segue boleto em anexo")

            return result_pdf

        except Exception as e:
            logger.error(f"❌ Erro no envio completo: {str(e)}")
            return {'success': False, 'error': str(e)}

    def desconectar(self):
        """Desconecta instância do WhatsApp"""
        try:
            logger.info(f"🔌 Desconectando instância: {self.instance_name}")

            endpoint = f'/instance/logout/{self.instance_name}'
            result = self._make_request('DELETE', endpoint)

            logger.info(f"✅ Instância desconectada")
            return {'success': True, 'message': 'Desconectado com sucesso'}

        except Exception as e:
            logger.error(f"❌ Erro ao desconectar: {str(e)}")
            return {'success': False, 'error': str(e)}

    def deletar_instancia(self):
        """Deleta instância completamente"""
        try:
            logger.info(f"🗑️ Deletando instância: {self.instance_name}")

            endpoint = f'/instance/delete/{self.instance_name}'
            result = self._make_request('DELETE', endpoint)

            logger.info(f"✅ Instância deletada")
            return {'success': True, 'message': 'Instância deletada'}

        except Exception as e:
            logger.error(f"❌ Erro ao deletar instância: {str(e)}")
            return {'success': False, 'error': str(e)}

# Instância global
whatsapp_service = WhatsAppEvolution()
