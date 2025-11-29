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

        # Logs detalhados de inicialização (mascarando API Key)
        api_key_masked = self.api_key[:4] + '***' + self.api_key[-4:] if len(self.api_key) > 8 else '***'
        logger.info(f"✅ WhatsApp Evolution Service inicializado")
        logger.info(f"   📍 URL: {self.base_url}")
        logger.info(f"   🔑 API Key: {api_key_masked}")
        logger.info(f"   📱 Instance: {self.instance_name}")

    def _make_request(self, method, endpoint, data=None):
        """Faz requisição HTTP para Evolution API"""
        try:
            url = f"{self.base_url}{endpoint}"

            logger.info(f"🌐 Requisição: {method} {url}")
            if data:
                logger.info(f"📦 Payload: {data}")

            if method == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=10)

            logger.info(f"📊 Status HTTP: {response.status_code}")

            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Resposta: {result}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro na requisição para Evolution API: {str(e)}")
            # Tentar logar resposta mesmo em caso de erro
            try:
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"📄 Resposta de erro: {e.response.text}")
            except:
                pass
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
            logger.info(f"🔍 Obtendo QR Code da instância: {self.instance_name}")
            endpoint = f'/instance/connect/{self.instance_name}'
            result = self._make_request('GET', endpoint)

            logger.info(f"📥 Resposta /instance/connect: {result}")

            if 'error' in result:
                logger.error(f"❌ Erro ao obter QR: {result['error']}")
                return {'success': False, 'error': result['error']}

            # Evolution API v2 pode retornar QR Code de várias formas
            # Vamos logar a estrutura completa para debug
            logger.info(f"🔑 Chaves da resposta: {list(result.keys())}")

            # Tentar obter QR Code (várias possibilidades)
            qr_base64 = None

            if result.get('qrcode'):
                logger.info(f"📱 Campo 'qrcode' encontrado")
                if isinstance(result['qrcode'], dict) and result['qrcode'].get('base64'):
                    qr_base64 = result['qrcode']['base64']
                elif isinstance(result['qrcode'], str):
                    qr_base64 = result['qrcode']

            elif result.get('base64'):
                logger.info(f"📱 Campo 'base64' encontrado")
                qr_base64 = result['base64']

            elif result.get('code'):
                logger.info(f"📱 Campo 'code' encontrado")
                qr_base64 = result['code']

            if qr_base64:
                logger.info(f"✅ QR Code obtido com sucesso (tamanho: {len(qr_base64)} chars)")
                return {
                    'success': True,
                    'connected': False,
                    'qr': qr_base64 if qr_base64.startswith('data:image') else f'data:image/png;base64,{qr_base64}'
                }

            # Se não tem QR, verificar se já está conectado
            logger.info(f"⚠️ QR Code não encontrado, verificando status...")
            status = self.verificar_status()
            if status.get('connected'):
                logger.info(f"✅ Já está conectado")
                return {'success': True, 'connected': True, 'qr': None}

            logger.warning(f"⚠️ QR Code não disponível e não está conectado")
            return {'success': False, 'message': 'QR Code não disponível'}

        except Exception as e:
            logger.error(f"❌ Erro ao obter QR: {str(e)}")
            return {'success': False, 'error': str(e)}

    def verificar_status(self):
        """Verifica status da conexão"""
        try:
            logger.info(f"🔍 Verificando status da instância: {self.instance_name}")
            endpoint = f'/instance/connectionState/{self.instance_name}'
            result = self._make_request('GET', endpoint)

            logger.info(f"📥 Resposta /instance/connectionState: {result}")

            if 'error' in result:
                logger.error(f"❌ Erro ao verificar status: {result['error']}")
                return {
                    'connected': False,
                    'status': 'disconnected',
                    'phone': None
                }

            # Logar estrutura da resposta para debug
            logger.info(f"🔑 Chaves da resposta status: {list(result.keys())}")

            # Evolution API v2 pode retornar state de várias formas
            state_direto = result.get('state')
            state_instance = result.get('instance', {}).get('state') if result.get('instance') else None
            state = state_direto or state_instance or 'close'

            logger.info(f"📊 state_direto: {state_direto}")
            logger.info(f"📊 state_instance: {state_instance}")
            logger.info(f"📊 Estado final: {state}")

            # Estados possíveis: open, connecting, close
            is_connected = state == 'open'

            status_map = {
                'open': 'connected',
                'connecting': 'connecting',
                'close': 'disconnected'
            }

            # Tentar obter telefone de várias formas possíveis
            phone = None
            if is_connected:
                phone = (
                    result.get('instance', {}).get('owner') or
                    result.get('instance', {}).get('wuid') or
                    result.get('owner') or
                    result.get('wuid')
                )
                logger.info(f"📞 Telefone detectado: {phone}")

            status_result = {
                'connected': is_connected,
                'status': status_map.get(state, 'disconnected'),
                'phone': phone
            }

            logger.info(f"✅ Status final: {status_result}")
            return status_result

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
