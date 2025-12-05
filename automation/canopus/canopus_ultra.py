"""
Canopus ULTRA - Velocidade Máxima com Stealth Mode
===================================================
Método otimizado para download de boletos Canopus.

Versão: 2.0.0 (2025-12-04)
Build: Force redeploy

Características:
- Login único compartilhado entre processamentos
- Stealth mode completo (anti-detecção de bot)
- Timeouts curtos para clientes não encontrados (~3s)
- Delays mínimos otimizados
- Tempo médio: ~8-10s por cliente com sucesso

Uso:
    from canopus_ultra import processar_boletos_ultra_sync

    resultado = processar_boletos_ultra_sync(
        usuario='17308',
        senha='Senha123',
        clientes=[{'cpf': '12345678901', 'nome': 'FULANO'}],
        mes='JANEIRO',
        headless=True
    )
"""

import asyncio
import logging
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from playwright.async_api import async_playwright, Page, BrowserContext, Browser

# Configurar logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Tentar importar stealth
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
    logger.info("✅ playwright-stealth disponível")
except ImportError:
    STEALTH_AVAILABLE = False
    logger.warning("⚠️ playwright-stealth não disponível")


class CanopusUltra:
    """
    Automação ULTRA para download de boletos Canopus.
    Otimizado para velocidade máxima com stealth mode.
    """

    BASE_URL = 'https://cnp3.consorciocanopus.com.br'

    # Timeouts otimizados (em ms)
    TIMEOUT_RAPIDO = 3000      # 3s para verificações rápidas
    TIMEOUT_NORMAL = 5000      # 5s para operações normais
    TIMEOUT_LONGO = 10000      # 10s para operações longas

    def __init__(
        self,
        usuario: str,
        senha: str,
        headless: bool = True,
        callback_status: Callable = None
    ):
        self.usuario = str(usuario).strip().zfill(10)
        self.senha = senha
        self.headless = headless
        self.callback_status = callback_status

        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.logado = False
        self.pasta_downloads = None

        # Estatísticas
        self.stats = {
            'sucessos': 0,
            'erros': 0,
            'cpf_nao_encontrado': 0,
            'sem_boleto': 0,
            'total': 0,
            'processados': 0
        }

    def _atualizar_status(self, etapa: str, progresso: int = None, erro: str = None):
        """Atualiza status via callback se disponível"""
        if self.callback_status:
            self.callback_status(etapa=etapa, progresso=progresso, erro=erro)
        logger.info(f"📊 {etapa}")
        sys.stdout.flush()

    async def iniciar(self, pasta_downloads: str = None):
        """Inicia o navegador com stealth mode completo."""
        self.pasta_downloads = pasta_downloads or f"/tmp/boletos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.pasta_downloads, exist_ok=True)

        self._atualizar_status('Iniciando navegador...')

        self.playwright = await async_playwright().start()

        # Args stealth completos
        stealth_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-web-security',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--hide-scrollbars',
            '--mute-audio',
        ]

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=stealth_args,
            chromium_sandbox=False
        )

        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            ignore_https_errors=True,
        )

        # Script anti-detecção
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin'},
                    {name: 'Chrome PDF Viewer'},
                    {name: 'Native Client'}
                ]
            });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)

        self.page = await self.context.new_page()

        # Aplicar stealth se disponível
        if STEALTH_AVAILABLE:
            await stealth_async(self.page)
            logger.info("🥷 Stealth mode aplicado")

        # Login
        self._atualizar_status('Fazendo login...')
        logou = await self._fazer_login()

        if not logou:
            raise Exception("Falha no login do Canopus")

        self.logado = True
        logger.info("✅ Login realizado com sucesso!")
        return True

    async def _fazer_login(self) -> bool:
        """Faz login no Canopus."""
        try:
            await self.page.goto(f'{self.BASE_URL}/WWW/frmCorCCCnsLogin.aspx')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(0.5)

            await self.page.fill('#edtUsuario', self.usuario)
            await self.page.fill('#edtSenha', self.senha)
            await self.page.click('#btnLogin')
            await asyncio.sleep(2)

            return 'frmMain.aspx' in self.page.url

        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False

    async def _processar_cliente_ultra(
        self,
        cpf: str,
        nome: str,
        mes: str,
        idx: int,
        total: int
    ) -> dict:
        """
        Processa cliente com velocidade máxima.
        Timeouts curtos para operações que falham.
        """
        # Formatar CPF para exibição
        cpf_fmt = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf
        logger.info(f"⚡ [ULTRA] Processando cliente: {cpf_fmt} ({idx}/{total})")

        inicio = datetime.now()
        resultado = {
            'cpf': cpf,
            'nome': nome,
            'ok': False,
            'status': 'erro',
            'erro': None
        }

        try:
            # PASSO 1: Ir para Atendimento
            await self.page.goto(f'{self.BASE_URL}/WWW/frmMain.aspx')
            await self.page.wait_for_load_state('domcontentloaded')

            await self.page.click('#ctl00_img_Atendimento', timeout=self.TIMEOUT_RAPIDO)
            await self.page.wait_for_load_state('domcontentloaded')

            # PASSO 2: Busca Avançada (timeout curto)
            try:
                await self.page.click('text="Busca avançada..."', timeout=self.TIMEOUT_RAPIDO)
            except:
                # Tentar seletor alternativo
                await self.page.click('input[value*="Busca"]', timeout=self.TIMEOUT_RAPIDO)

            # Esperar dropdown aparecer (timeout curto)
            try:
                await self.page.wait_for_selector(
                    'select[id*="cbxCriterioBusca"]',
                    timeout=self.TIMEOUT_RAPIDO
                )
            except:
                resultado['erro'] = 'Página de busca não carregou'
                resultado['status'] = 'erro'
                return resultado

            # Selecionar CPF
            await self.page.select_option('select[id*="cbxCriterioBusca"]', 'F')

            # Formatar e preencher CPF
            cpf_limpo = re.sub(r'\D', '', cpf)
            cpf_fmt = f'{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}'

            await self.page.fill('input[id*="edtContextoBusca"]', cpf_fmt)

            # Buscar
            await self.page.click('input[value="Buscar"]')

            # TIMEOUT CURTO para resultado da busca (~1.5s)
            await asyncio.sleep(1.5)

            # Verificar resultado RAPIDAMENTE
            html = await self.page.content()
            if 'Nenhum registro' in html or 'não encontrado' in html.lower():
                resultado['erro'] = 'Cliente não encontrado no Canopus'
                resultado['status'] = 'cpf_nao_encontrado'
                self.stats['cpf_nao_encontrado'] += 1
                duracao = (datetime.now() - inicio).total_seconds()
                resultado['duracao'] = duracao
                logger.info(f"⚠️ [{idx}/{total}] NÃO ENCONTRADO - CPF: {cpf_fmt} | {nome[:25]} | ⏱️ {duracao:.1f}s")
                return resultado

            # PASSO 3: Selecionar cliente (timeout curto)
            try:
                link = await self.page.wait_for_selector('td a', timeout=self.TIMEOUT_RAPIDO)
                if link:
                    await link.click()
                    await asyncio.sleep(0.3)
            except:
                resultado['erro'] = 'Link do cliente não encontrado'
                resultado['status'] = 'cpf_nao_encontrado'
                self.stats['cpf_nao_encontrado'] += 1
                return resultado

            # Confirmar busca
            try:
                btn_confirmar = await self.page.wait_for_selector(
                    'input[value="Confirmar Busca"]',
                    timeout=self.TIMEOUT_RAPIDO
                )
                if btn_confirmar:
                    await btn_confirmar.click()
                    await self.page.wait_for_load_state('domcontentloaded')
            except:
                pass  # Continuar mesmo sem confirmar

            # PASSO 4: Emissão de boleto (navegação direta)
            await self.page.goto(f'{self.BASE_URL}/WWW/CONCO/frmConCoRelBoletoAvulso.aspx')
            await self.page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(0.5)

            # Verificar se há boletos disponíveis (timeout curto)
            try:
                img_cbs = await self.page.query_selector_all(
                    'input[type="image"][id*="imgEmite_Boleto"]'
                )
            except:
                img_cbs = []

            if not img_cbs:
                resultado['erro'] = 'Nenhum boleto disponível'
                resultado['status'] = 'sem_boleto'
                self.stats['sem_boleto'] += 1
                duracao = (datetime.now() - inicio).total_seconds()
                resultado['duracao'] = duracao
                logger.info(f"📄 [{idx}/{total}] SEM BOLETO - CPF: {cpf_fmt} | {nome[:25]} | ⏱️ {duracao:.1f}s")
                return resultado

            # Marcar último boleto
            await img_cbs[-1].click()
            await asyncio.sleep(0.5)

            # Emitir - usar expect_popup para capturar o popup corretamente
            logger.info(f"  [{idx}/{total}] Clicando em Emitir Cobrança...")

            popup = None
            try:
                # Método 1: Usar expect_popup (mais confiável)
                async with self.page.expect_popup(timeout=15000) as popup_info:
                    await self.page.click('input[value="Emitir Cobrança"]')
                popup = await popup_info.value
                logger.info(f"  [{idx}/{total}] Popup capturado: {popup.url[:50]}...")

                # IMPORTANTE: Aguardar o popup sair de about:blank e carregar conteúdo real
                if popup.url == 'about:blank':
                    logger.info(f"  [{idx}/{total}] Aguardando popup carregar...")
                    # Aguardar navegação para URL real
                    try:
                        await popup.wait_for_url(lambda url: url != 'about:blank', timeout=10000)
                        logger.info(f"  [{idx}/{total}] Popup navegou para: {popup.url[:50]}...")
                    except:
                        # Se não navegou, aguardar um pouco e verificar se tem conteúdo
                        await asyncio.sleep(2)

                # Aguardar carregamento completo
                await popup.wait_for_load_state('networkidle', timeout=self.TIMEOUT_LONGO)

            except Exception as e_popup:
                logger.warning(f"  [{idx}/{total}] expect_popup falhou: {e_popup}")
                # Método 2: Fallback - aguardar popup manualmente
                popup = None
                for attempt in range(30):  # 15 segundos máximo
                    await asyncio.sleep(0.5)
                    for p in self.context.pages:
                        if p != self.page and p.url != 'about:blank':
                            popup = p
                            logger.info(f"  [{idx}/{total}] Popup encontrado (tentativa {attempt+1}): {p.url[:50]}...")
                            break
                    if popup:
                        break

            if popup and popup.url != 'about:blank':
                # Aguardar mais tempo para garantir que o PDF carregou
                logger.info(f"  [{idx}/{total}] Aguardando PDF carregar completamente...")
                await asyncio.sleep(3)  # Dar tempo para o PDF renderizar

                # Verificar se a página tem conteúdo (não está vazia)
                try:
                    await popup.wait_for_load_state('networkidle', timeout=10000)
                except:
                    pass

                # Salvar PDF
                nome_arquivo = self._formatar_nome(nome, mes)
                caminho = os.path.join(self.pasta_downloads, nome_arquivo)

                await popup.pdf(path=caminho)
                tamanho = os.path.getsize(caminho)

                # Verificar se o arquivo é válido (> 10KB indica PDF real)
                if tamanho < 10000:  # Menos de 10KB = provavelmente página em branco
                    logger.warning(f"  [{idx}/{total}] PDF muito pequeno ({tamanho} bytes), tentando novamente...")
                    await asyncio.sleep(3)  # Aguardar mais
                    await popup.pdf(path=caminho)
                    tamanho = os.path.getsize(caminho)

                await popup.close()

                # Verificar tamanho final
                if tamanho < 10000:
                    duracao = (datetime.now() - inicio).total_seconds()
                    resultado['erro'] = f'PDF inválido ({tamanho} bytes)'
                    resultado['status'] = 'erro'
                    resultado['duracao'] = duracao
                    self.stats['erros'] += 1
                    logger.error(f"❌ [{idx}/{total}] ERRO - CPF: {cpf_fmt} | PDF inválido ({tamanho} bytes) | ⏱️ {duracao:.1f}s")
                    # Remover arquivo inválido
                    try:
                        os.remove(caminho)
                    except:
                        pass
                else:
                    duracao = (datetime.now() - inicio).total_seconds()
                    resultado['ok'] = True
                    resultado['status'] = 'sucesso'
                    resultado['arquivo'] = nome_arquivo
                    resultado['caminho'] = caminho
                    resultado['tamanho'] = tamanho
                    resultado['duracao'] = duracao
                    self.stats['sucessos'] += 1

                    # Log de sucesso com tempo total e tamanho
                    tamanho_kb = tamanho / 1024
                    logger.info(f"✅ [{idx}/{total}] SUCESSO - CPF: {cpf_fmt} | {nome[:25]} | {tamanho_kb:.0f}KB | ⏱️ {duracao:.1f}s")
            else:
                duracao = (datetime.now() - inicio).total_seconds()
                erro_msg = 'Popup ficou em about:blank' if popup else 'Popup do PDF não abriu'
                resultado['erro'] = erro_msg
                resultado['status'] = 'erro'
                resultado['duracao'] = duracao
                self.stats['erros'] += 1

                # Log de erro com tempo total
                logger.error(f"❌ [{idx}/{total}] ERRO - CPF: {cpf_fmt} | {erro_msg} | ⏱️ {duracao:.1f}s")

        except Exception as e:
            duracao = (datetime.now() - inicio).total_seconds()
            resultado['erro'] = str(e)[:100]
            resultado['status'] = 'erro'
            resultado['duracao'] = duracao
            self.stats['erros'] += 1

            # Log de exceção com tempo total
            logger.error(f"❌ [{idx}/{total}] ERRO - CPF: {cpf_fmt} | {str(e)[:50]} | ⏱️ {duracao:.1f}s")

        finally:
            # Fechar popups extras
            try:
                for p in self.context.pages[1:]:
                    await p.close()
            except:
                pass

        return resultado

    def _formatar_nome(self, nome: str, mes: str) -> str:
        """Formata nome do arquivo PDF."""
        import unicodedata
        nome_limpo = unicodedata.normalize('NFD', nome)
        nome_limpo = nome_limpo.encode('ascii', 'ignore').decode('utf-8')
        nome_limpo = re.sub(r'[^A-Za-z0-9\s]', '', nome_limpo)
        nome_limpo = nome_limpo.upper().strip().replace(' ', '_')
        return f"{nome_limpo}_{mes.upper()}.pdf"

    async def processar_lote(
        self,
        clientes: List[Dict],
        mes: str = 'JANEIRO',
        verificar_pausa: Callable = None
    ) -> dict:
        """
        Processa lote de clientes com velocidade máxima.

        Args:
            clientes: Lista de dicts com 'cpf' e 'nome'
            mes: Mês do boleto
            verificar_pausa: Callback para verificar se deve pausar

        Returns:
            Dict com estatísticas e resultados
        """
        if not self.logado:
            raise Exception("Não está logado. Chame iniciar() primeiro.")

        total = len(clientes)
        self.stats['total'] = total

        logger.info(f"\n{'='*50}")
        logger.info(f"MODO ULTRA: {total} cliente(s)")
        logger.info(f"{'='*50}\n")

        self._atualizar_status(f'Processando {total} clientes...', progresso=0)

        inicio = datetime.now()
        resultados = []

        for i, cliente in enumerate(clientes):
            # Verificar pausa
            if verificar_pausa and verificar_pausa():
                logger.info("⏸️ Execução pausada pelo usuário")
                break

            cpf = re.sub(r'\D', '', str(cliente.get('cpf', '')))
            nome = cliente.get('nome', 'CLIENTE')

            r = await self._processar_cliente_ultra(cpf, nome, mes, i+1, total)
            resultados.append(r)

            self.stats['processados'] = i + 1
            self._atualizar_status(
                f'Processando cliente {i+1}/{total}...',
                progresso=i+1
            )

        duracao = (datetime.now() - inicio).total_seconds()

        logger.info(f"\n{'='*50}")
        logger.info(f"RESULTADO: {self.stats['sucessos']}/{total} em {duracao:.1f}s")
        if total > 0:
            logger.info(f"Média: {duracao/total:.1f}s por cliente")
        logger.info(f"{'='*50}")

        return {
            'total': total,
            'sucesso': self.stats['sucessos'],
            'erros': self.stats['erros'],
            'cpf_nao_encontrado': self.stats['cpf_nao_encontrado'],
            'sem_boleto': self.stats['sem_boleto'],
            'duracao': duracao,
            'media': duracao/total if total > 0 else 0,
            'resultados': resultados,
            'pasta': self.pasta_downloads
        }

    async def fechar(self):
        """Fecha o navegador."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("🔒 Navegador fechado")


async def processar_boletos_ultra(
    usuario: str,
    senha: str,
    clientes: List[Dict],
    mes: str = 'JANEIRO',
    pasta_downloads: str = None,
    headless: bool = True,
    callback_status: Callable = None,
    verificar_pausa: Callable = None
) -> dict:
    """
    Função principal para processamento ultra-rápido.

    Args:
        usuario: Usuário/PV do Canopus
        senha: Senha
        clientes: Lista de dicts com 'cpf' e 'nome'
        mes: Mês do boleto
        pasta_downloads: Pasta para salvar PDFs
        headless: Se True, roda sem interface gráfica
        callback_status: Callback para atualizar status
        verificar_pausa: Callback para verificar pausa

    Returns:
        Dict com estatísticas e resultados
    """
    canopus = CanopusUltra(usuario, senha, headless, callback_status)

    try:
        await canopus.iniciar(pasta_downloads)
        return await canopus.processar_lote(clientes, mes, verificar_pausa)
    finally:
        await canopus.fechar()


def processar_boletos_ultra_sync(
    usuario: str,
    senha: str,
    clientes: List[Dict],
    mes: str = 'JANEIRO',
    pasta_downloads: str = None,
    headless: bool = True,
    callback_status: Callable = None,
    verificar_pausa: Callable = None
) -> dict:
    """Wrapper síncrono para uso com Flask."""
    return asyncio.run(processar_boletos_ultra(
        usuario=usuario,
        senha=senha,
        clientes=clientes,
        mes=mes,
        pasta_downloads=pasta_downloads,
        headless=headless,
        callback_status=callback_status,
        verificar_pausa=verificar_pausa
    ))


if __name__ == '__main__':
    async def teste():
        clientes = [
            {'cpf': '50516798898', 'nome': 'ADAO JUNIOR PEREIRA DE BRITO'},
        ]

        print("\n" + "="*60)
        print("TESTE MODO ULTRA - PV 17308")
        print("="*60)

        resultado = await processar_boletos_ultra(
            usuario='17308',
            senha='Sonhorealizado2@',
            clientes=clientes,
            mes='JANEIRO',
            headless=False
        )

        print(f"\n🚀 Tempo: {resultado['duracao']:.1f}s")
        print(f"📊 Sucesso: {resultado['sucesso']}/{resultado['total']}")

    asyncio.run(teste())
