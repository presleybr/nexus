"""
Serviço WhatsApp usando Playwright
Conecta diretamente ao WhatsApp Web sem precisar de servidor externo
"""

import asyncio
import base64
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logger = logging.getLogger(__name__)


class WhatsAppPlaywrightService:
    """Serviço de WhatsApp usando Playwright"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.is_connected = False
        self.qr_code = None
        self.phone_number = None

        # Diretório para salvar sessão
        self.session_dir = Path(Config.WHATSAPP_PATH) / "playwright_session"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    async def iniciar(self) -> Dict:
        """
        Inicia o navegador e conecta ao WhatsApp Web

        Returns:
            Dict com status da operação
        """
        try:
            logger.info("🚀 Iniciando WhatsApp via Playwright...")

            # Iniciar Playwright
            self.playwright = await async_playwright().start()

            # Lançar navegador com sessão persistente
            self.context = await self.playwright.chromium.launch_persistent_context(
                str(self.session_dir),
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )

            self.page = await self.context.new_page()

            # Navegar para WhatsApp Web
            await self.page.goto('https://web.whatsapp.com', wait_until='networkidle')

            logger.info("✅ Navegador iniciado, aguardando QR Code ou conexão...")

            return {
                'success': True,
                'message': 'WhatsApp iniciado. Aguarde QR Code ou verificação de sessão...'
            }

        except Exception as e:
            logger.error(f"❌ Erro ao iniciar WhatsApp: {e}")
            return {
                'success': False,
                'error': f'Erro ao iniciar: {str(e)}'
            }

    async def obter_qr_code(self) -> Dict:
        """
        Obtém o QR Code do WhatsApp Web

        Returns:
            Dict com QR Code em base64 ou status de conexão
        """
        try:
            if not self.page:
                logger.error("❌ Página não inicializada")
                return {
                    'success': False,
                    'error': 'WhatsApp não foi iniciado. Chame iniciar() primeiro.'
                }

            logger.info("🔍 Verificando estado do WhatsApp Web...")

            # Verificar se já está conectado
            try:
                await self.page.wait_for_selector('div[data-testid="conversation-panel"]', timeout=2000)
                self.is_connected = True

                logger.info("✅ WhatsApp já está conectado!")

                # Tentar obter número de telefone
                try:
                    phone_elem = await self.page.query_selector('span[data-testid="default-user"]')
                    if phone_elem:
                        self.phone_number = await phone_elem.inner_text()
                except:
                    pass

                return {
                    'success': True,
                    'connected': True,
                    'phone': self.phone_number,
                    'message': 'WhatsApp já está conectado!'
                }
            except:
                logger.info("ℹ️ WhatsApp não conectado ainda, procurando QR Code...")

            # Tentar múltiplos seletores para o QR Code (WhatsApp muda frequentemente)
            qr_selectors = [
                'canvas[aria-label="Scan me!"]',
                'canvas[role="img"]',
                'div[data-ref] canvas',
                'canvas'
            ]

            for selector in qr_selectors:
                try:
                    logger.info(f"🔍 Tentando seletor: {selector}")
                    qr_element = await self.page.wait_for_selector(selector, timeout=3000)

                    if qr_element:
                        logger.info(f"✅ QR Code encontrado com seletor: {selector}")

                        # Capturar screenshot do QR Code
                        qr_bytes = await qr_element.screenshot()
                        qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
                        self.qr_code = f"data:image/png;base64,{qr_base64}"

                        logger.info(f"📱 QR Code capturado! Tamanho: {len(qr_base64)} chars")

                        return {
                            'success': True,
                            'qr': self.qr_code,
                            'connected': False
                        }
                except Exception as e:
                    logger.warning(f"⚠️ Seletor '{selector}' não encontrou QR Code: {e}")
                    continue

            # Se chegou aqui, nenhum seletor funcionou
            logger.warning("⚠️ QR Code ainda não apareceu em nenhum seletor")

            # Tentar capturar screenshot da página inteira para debug
            try:
                page_screenshot = await self.page.screenshot()
                screenshot_base64 = base64.b64encode(page_screenshot).decode('utf-8')
                logger.info("📸 Screenshot da página capturado para debug")
            except:
                pass

            return {
                'success': True,
                'connected': False,
                'message': 'Aguardando QR Code aparecer... (recarregue em alguns segundos)'
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter QR Code: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': f'Erro ao obter QR Code: {str(e)}'
            }

    async def verificar_conexao(self) -> Dict:
        """
        Verifica se o WhatsApp está conectado

        Returns:
            Dict com status da conexão
        """
        try:
            if not self.page:
                return {
                    'connected': False,
                    'error': 'WhatsApp não iniciado'
                }

            # Verificar se o painel de conversas está presente
            try:
                await self.page.wait_for_selector('div[data-testid="conversation-panel"]', timeout=2000)
                self.is_connected = True

                # Tentar obter número
                try:
                    phone_elem = await self.page.query_selector('span[data-testid="default-user"]')
                    if phone_elem:
                        self.phone_number = await phone_elem.inner_text()
                except:
                    pass

                return {
                    'connected': True,
                    'phone': self.phone_number
                }
            except:
                self.is_connected = False
                return {
                    'connected': False
                }

        except Exception as e:
            logger.error(f"❌ Erro ao verificar conexão: {e}")
            return {
                'connected': False,
                'error': str(e)
            }

    async def enviar_mensagem(self, numero: str, mensagem: str) -> Dict:
        """
        Envia mensagem via WhatsApp Web

        Args:
            numero: Número do destinatário (com DDI)
            mensagem: Texto da mensagem

        Returns:
            Dict com status do envio
        """
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'error': 'WhatsApp não está conectado'
                }

            # Formatar número (remover caracteres especiais)
            numero_limpo = ''.join(filter(str.isdigit, numero))

            # Abrir conversa
            url = f'https://web.whatsapp.com/send?phone={numero_limpo}'
            await self.page.goto(url, wait_until='networkidle')

            # Aguardar campo de mensagem
            await self.page.wait_for_selector('div[data-testid="conversation-compose-box-input"]', timeout=10000)

            # Digitar mensagem
            await self.page.fill('div[data-testid="conversation-compose-box-input"]', mensagem)

            # Clicar em enviar
            await self.page.click('button[data-testid="compose-btn-send"]')

            logger.info(f"✅ Mensagem enviada para {numero}")

            return {
                'success': True,
                'message': f'Mensagem enviada para {numero}'
            }

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return {
                'success': False,
                'error': f'Erro ao enviar: {str(e)}'
            }

    async def desconectar(self) -> Dict:
        """
        Desconecta e limpa sessão

        Returns:
            Dict com status da operação
        """
        try:
            if self.context:
                await self.context.close()

            if self.playwright:
                await self.playwright.stop()

            self.browser = None
            self.context = None
            self.page = None
            self.is_connected = False
            self.qr_code = None
            self.phone_number = None

            logger.info("🔒 WhatsApp desconectado")

            return {
                'success': True,
                'message': 'Desconectado com sucesso'
            }

        except Exception as e:
            logger.error(f"❌ Erro ao desconectar: {e}")
            return {
                'success': False,
                'error': f'Erro ao desconectar: {str(e)}'
            }


# Instância global
whatsapp_playwright_service = WhatsAppPlaywrightService()
