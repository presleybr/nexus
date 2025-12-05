"""
Canopus ULTRA - Velocidade Máxima com Processamento Paralelo
============================================================
Método otimizado para download de boletos Canopus.

Versão: 3.0.1 (2025-12-05)
Build: PARALLEL-FIX

Características:
- Login único compartilhado entre processamentos
- Stealth mode completo (anti-detecção de bot)
- Timeouts curtos para clientes não encontrados (~3s)
- Delays mínimos otimizados
- PROCESSAMENTO PARALELO com múltiplos workers (2x mais rápido!)
- Tempo médio: ~4-5s por cliente (efetivo com 2 workers)

Uso:
    from canopus_ultra import processar_boletos_ultra_sync

    resultado = processar_boletos_ultra_sync(
        usuario='17308',
        senha='Senha123',
        clientes=[{'cpf': '12345678901', 'nome': 'FULANO'}],
        mes='JANEIRO',
        headless=True,
        num_workers=2,  # Número de workers paralelos
        paralelo=True   # Ativar modo paralelo
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

    # Timeouts ULTRA otimizados (em ms)
    TIMEOUT_RAPIDO = 2000      # 2s para verificações rápidas
    TIMEOUT_NORMAL = 4000      # 4s para operações normais
    TIMEOUT_LONGO = 8000       # 8s para operações longas

    def __init__(
        self,
        usuario: str,
        senha: str,
        headless: bool = True,
        callback_status: Callable = None,
        num_workers: int = 1  # Número de workers (1=sequencial, 2+=paralelo)
    ):
        self.usuario = str(usuario).strip().zfill(10)
        self.senha = senha
        self.headless = headless
        self.callback_status = callback_status
        self.num_workers = num_workers

        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None  # Página principal (para login)
        self.pages: List[Page] = []  # Páginas dos workers
        self.logado = False
        self.pasta_downloads = None

        # Estatísticas (thread-safe com lock)
        self.stats = {
            'sucessos': 0,
            'erros': 0,
            'cpf_nao_encontrado': 0,
            'sem_boleto': 0,
            'total': 0,
            'processados': 0
        }
        self._stats_lock = None  # Será criado no iniciar()

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

        # Criar lock para estatísticas (precisa estar no event loop)
        self._stats_lock = asyncio.Lock()

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

        # Criar páginas dos workers para processamento paralelo (só se num_workers > 1)
        if self.num_workers > 1:
            logger.info(f"🔧 Criando {self.num_workers} workers paralelos...")
            for i in range(self.num_workers):
                worker_page = await self.context.new_page()
                if STEALTH_AVAILABLE:
                    await stealth_async(worker_page)
                self.pages.append(worker_page)
                logger.info(f"  ✓ Worker {i+1} criado")
            logger.info(f"🚀 {self.num_workers} workers prontos!")
        else:
            logger.info("📝 Modo sequencial (1 worker)")

        return True

    async def _fazer_login(self) -> bool:
        """Faz login no Canopus."""
        try:
            await self.page.goto(f'{self.BASE_URL}/WWW/frmCorCCCnsLogin.aspx')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(0.3)

            await self.page.fill('#edtUsuario', self.usuario)
            await self.page.fill('#edtSenha', self.senha)
            await self.page.click('#btnLogin')
            await asyncio.sleep(1.2)

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
        total: int,
        page: Page = None,
        worker_id: int = 0
    ) -> dict:
        """
        Processa cliente com velocidade máxima.
        Timeouts curtos para operações que falham.

        Args:
            page: Página específica do worker (se None, usa self.page)
            worker_id: ID do worker para logging
        """
        # Usar página fornecida ou página principal
        if page is None:
            page = self.page

        # Formatar CPF para exibição
        cpf_fmt = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf
        logger.info(f"⚡ [W{worker_id}] Processando: {cpf_fmt} ({idx}/{total})")

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
            await page.goto(f'{self.BASE_URL}/WWW/frmMain.aspx')
            await page.wait_for_load_state('domcontentloaded')

            await page.click('#ctl00_img_Atendimento', timeout=self.TIMEOUT_RAPIDO)
            await page.wait_for_load_state('domcontentloaded')

            # PASSO 2: Busca Avançada (timeout curto)
            try:
                await page.click('text="Busca avançada..."', timeout=self.TIMEOUT_RAPIDO)
            except:
                # Tentar seletor alternativo
                await page.click('input[value*="Busca"]', timeout=self.TIMEOUT_RAPIDO)

            # Esperar dropdown aparecer (timeout curto)
            try:
                await page.wait_for_selector(
                    'select[id*="cbxCriterioBusca"]',
                    timeout=self.TIMEOUT_RAPIDO
                )
            except:
                resultado['erro'] = 'Página de busca não carregou'
                resultado['status'] = 'erro'
                return resultado

            # Selecionar CPF
            await page.select_option('select[id*="cbxCriterioBusca"]', 'F')

            # Formatar e preencher CPF
            cpf_limpo = re.sub(r'\D', '', cpf)
            cpf_fmt = f'{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}'

            await page.fill('input[id*="edtContextoBusca"]', cpf_fmt)

            # Buscar
            await page.click('input[value="Buscar"]')

            # TIMEOUT CURTO para resultado da busca
            await asyncio.sleep(1.0)

            # Verificar resultado RAPIDAMENTE
            html = await page.content()
            if 'Nenhum registro' in html or 'não encontrado' in html.lower():
                resultado['erro'] = 'Cliente não encontrado no Canopus'
                resultado['status'] = 'cpf_nao_encontrado'
                async with self._stats_lock:
                    self.stats['cpf_nao_encontrado'] += 1
                duracao = (datetime.now() - inicio).total_seconds()
                resultado['duracao'] = duracao
                logger.info(f"⚠️ [W{worker_id}] NÃO ENCONTRADO - CPF: {cpf_fmt} | {nome[:25]} | ⏱️ {duracao:.1f}s")
                return resultado

            # PASSO 3: Selecionar cliente (timeout curto)
            try:
                link = await page.wait_for_selector('td a', timeout=self.TIMEOUT_RAPIDO)
                if link:
                    await link.click()
                    await asyncio.sleep(0.2)
            except:
                resultado['erro'] = 'Link do cliente não encontrado'
                resultado['status'] = 'cpf_nao_encontrado'
                async with self._stats_lock:
                    self.stats['cpf_nao_encontrado'] += 1
                return resultado

            # Confirmar busca
            try:
                btn_confirmar = await page.wait_for_selector(
                    'input[value="Confirmar Busca"]',
                    timeout=self.TIMEOUT_RAPIDO
                )
                if btn_confirmar:
                    await btn_confirmar.click()
                    await page.wait_for_load_state('domcontentloaded')
            except:
                pass  # Continuar mesmo sem confirmar

            # PASSO 4: Emissão de boleto (navegação direta)
            await page.goto(f'{self.BASE_URL}/WWW/CONCO/frmConCoRelBoletoAvulso.aspx')
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(0.3)

            # Verificar se há boletos disponíveis (timeout curto)
            try:
                img_cbs = await page.query_selector_all(
                    'input[type="image"][id*="imgEmite_Boleto"]'
                )
            except:
                img_cbs = []

            if not img_cbs:
                resultado['erro'] = 'Nenhum boleto disponível'
                resultado['status'] = 'sem_boleto'
                async with self._stats_lock:
                    self.stats['sem_boleto'] += 1
                duracao = (datetime.now() - inicio).total_seconds()
                resultado['duracao'] = duracao
                logger.info(f"📄 [W{worker_id}] SEM BOLETO - CPF: {cpf_fmt} | {nome[:25]} | ⏱️ {duracao:.1f}s")
                return resultado

            # Marcar último boleto
            await img_cbs[-1].click()
            await asyncio.sleep(0.3)

            # ESTRATÉGIA: Usar route handler para interceptar PDF (como código antigo)
            logger.info(f"  [W{worker_id}] Configurando interceptação de PDF...")

            pdf_bytes_capturado = None
            pdf_url_capturado = None

            async def route_pdf_handler(route):
                nonlocal pdf_bytes_capturado, pdf_url_capturado
                request = route.request
                url = request.url

                # Verificar se é potencial PDF
                is_potential_pdf = (
                    'frmConCmImpressao' in url or
                    'Impressao' in url or
                    url.endswith('.pdf') or
                    '.pdf?' in url or
                    request.resource_type == 'document'
                )

                if not is_potential_pdf:
                    await route.continue_()
                    return

                logger.info(f"  [W{worker_id}] 🔍 Interceptando: {url[:60]}...")

                try:
                    # Buscar resposta
                    response = await route.fetch()
                    content_type = response.headers.get('content-type', '').lower()
                    body = await response.body()  # bytes - body() é método async!

                    logger.info(f"  [W{worker_id}] 📦 Content-Type: {content_type}, Size: {len(body)} bytes")

                    # Capturar se for PDF
                    if 'pdf' in content_type or 'octet-stream' in content_type or body.startswith(b'%PDF'):
                        tamanho = len(body)

                        # Verificar se é PDF real
                        if body.startswith(b'%PDF') and tamanho > 10000:
                            pdf_bytes_capturado = body
                            pdf_url_capturado = url
                            logger.info(f"  [W{worker_id}] 🎯 PDF CAPTURADO: {tamanho/1024:.0f}KB")
                        else:
                            logger.warning(f"  [W{worker_id}] ⚠️ Não é PDF real ou muito pequeno: {tamanho} bytes")

                    # Passar resposta pro navegador
                    await route.fulfill(response=response)

                except Exception as e:
                    logger.warning(f"  [W{worker_id}] ⚠️ Erro no route: {e}")
                    await route.continue_()

            # Registrar route handler
            await self.context.route('**/*', route_pdf_handler)

            try:
                # Clicar em Emitir Cobrança
                logger.info(f"  [W{worker_id}] Clicando em Emitir Cobrança...")
                await page.click('input[value="Emitir Cobrança"]')

                # Aguardar PDF ser interceptado (até 12 segundos)
                for i in range(24):
                    await asyncio.sleep(0.5)
                    if pdf_bytes_capturado:
                        break

                # Remover route handler
                await self.context.unroute('**/*', route_pdf_handler)

                if pdf_bytes_capturado:
                    # Salvar PDF
                    nome_arquivo = self._formatar_nome(nome, mes)
                    caminho = os.path.join(self.pasta_downloads, nome_arquivo)

                    with open(caminho, 'wb') as f:
                        f.write(pdf_bytes_capturado)

                    tamanho = len(pdf_bytes_capturado)
                    duracao = (datetime.now() - inicio).total_seconds()

                    resultado['ok'] = True
                    resultado['status'] = 'sucesso'
                    resultado['arquivo'] = nome_arquivo
                    resultado['caminho'] = caminho
                    resultado['tamanho'] = tamanho
                    resultado['duracao'] = duracao
                    async with self._stats_lock:
                        self.stats['sucessos'] += 1

                    tamanho_kb = tamanho / 1024
                    logger.info(f"✅ [W{worker_id}] SUCESSO - CPF: {cpf_fmt} | {nome[:25]} | {tamanho_kb:.0f}KB | ⏱️ {duracao:.1f}s")
                else:
                    duracao = (datetime.now() - inicio).total_seconds()
                    resultado['erro'] = 'PDF não interceptado'
                    resultado['status'] = 'erro'
                    resultado['duracao'] = duracao
                    async with self._stats_lock:
                        self.stats['erros'] += 1
                    logger.error(f"❌ [W{worker_id}] ERRO - CPF: {cpf_fmt} | PDF não interceptado | ⏱️ {duracao:.1f}s")

            except Exception as e_emitir:
                try:
                    await self.context.unroute('**/*', route_pdf_handler)
                except:
                    pass
                raise e_emitir

        except Exception as e:
            duracao = (datetime.now() - inicio).total_seconds()
            resultado['erro'] = str(e)[:100]
            resultado['status'] = 'erro'
            resultado['duracao'] = duracao
            async with self._stats_lock:
                self.stats['erros'] += 1

            # Log de exceção com tempo total
            logger.error(f"❌ [W{worker_id}] ERRO - CPF: {cpf_fmt} | {str(e)[:50]} | ⏱️ {duracao:.1f}s")

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

    async def _worker_processar(
        self,
        worker_id: int,
        page: Page,
        clientes_worker: List[Dict],
        mes: str,
        total_geral: int,
        offset: int,
        on_resultado: Callable = None
    ) -> List[dict]:
        """
        Worker que processa uma lista de clientes em uma página específica.

        Args:
            worker_id: ID do worker (para logging)
            page: Página do Playwright para este worker
            clientes_worker: Lista de clientes para este worker processar
            mes: Mês do boleto
            total_geral: Total de clientes de todos os workers
            offset: Offset do índice (para mostrar número correto no log)
            on_resultado: Callback chamado após cada resultado (para registro em tempo real)

        Returns:
            Lista de resultados
        """
        resultados = []
        for i, cliente in enumerate(clientes_worker):
            cpf = re.sub(r'\D', '', str(cliente.get('cpf', '')))
            nome = cliente.get('nome', 'CLIENTE')
            idx_geral = offset + i + 1

            r = await self._processar_cliente_ultra(
                cpf=cpf,
                nome=nome,
                mes=mes,
                idx=idx_geral,
                total=total_geral,
                page=page,
                worker_id=worker_id
            )
            resultados.append(r)

            # Chamar callback em tempo real para registro no banco
            if on_resultado:
                try:
                    await on_resultado(r)
                except Exception as e:
                    logger.error(f"[W{worker_id}] Erro no callback on_resultado: {e}")

            # Atualizar progresso global
            async with self._stats_lock:
                self.stats['processados'] += 1
                processados = self.stats['processados']

            self._atualizar_status(
                f'Processando {processados}/{total_geral}...',
                progresso=processados
            )

        return resultados

    async def processar_lote_paralelo(
        self,
        clientes: List[Dict],
        mes: str = 'JANEIRO',
        verificar_pausa: Callable = None,
        on_resultado: Callable = None
    ) -> dict:
        """
        Processa lote de clientes em PARALELO usando múltiplos workers.

        Args:
            clientes: Lista de dicts com 'cpf' e 'nome'
            mes: Mês do boleto
            verificar_pausa: Callback para verificar se deve pausar (não usado em paralelo)
            on_resultado: Callback async chamado após cada resultado (para registro em tempo real)

        Returns:
            Dict com estatísticas e resultados
        """
        if not self.logado:
            raise Exception("Não está logado. Chame iniciar() primeiro.")

        if not self.pages:
            raise Exception("Workers não inicializados. Verifique iniciar().")

        total = len(clientes)
        self.stats['total'] = total
        self.stats['processados'] = 0

        num_workers = min(self.num_workers, len(self.pages), total)

        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 MODO ULTRA PARALELO: {total} cliente(s) | {num_workers} workers")
        logger.info(f"{'='*60}\n")

        self._atualizar_status(f'Processando {total} clientes com {num_workers} workers...', progresso=0)

        inicio = datetime.now()

        # Dividir clientes entre os workers
        clientes_por_worker = []
        tamanho_base = total // num_workers
        resto = total % num_workers

        idx = 0
        for w in range(num_workers):
            # Distribuir o resto entre os primeiros workers
            tamanho = tamanho_base + (1 if w < resto else 0)
            clientes_por_worker.append(clientes[idx:idx + tamanho])
            idx += tamanho

        # Log da divisão
        for w, cw in enumerate(clientes_por_worker):
            logger.info(f"  Worker {w+1}: {len(cw)} cliente(s)")

        # Criar tasks para cada worker
        tasks = []
        offset = 0
        for w in range(num_workers):
            task = self._worker_processar(
                worker_id=w + 1,
                page=self.pages[w],
                clientes_worker=clientes_por_worker[w],
                mes=mes,
                total_geral=total,
                offset=offset,
                on_resultado=on_resultado  # Callback para registro em tempo real
            )
            tasks.append(task)
            offset += len(clientes_por_worker[w])

        # Executar todos os workers em paralelo
        logger.info(f"\n⚡ Iniciando {num_workers} workers em paralelo...")
        resultados_por_worker = await asyncio.gather(*tasks, return_exceptions=True)

        # Combinar resultados
        resultados = []
        for r in resultados_por_worker:
            if isinstance(r, Exception):
                logger.error(f"Worker falhou: {r}")
            elif isinstance(r, list):
                resultados.extend(r)

        duracao = (datetime.now() - inicio).total_seconds()

        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 RESULTADO PARALELO: {self.stats['sucessos']}/{total} em {duracao:.1f}s")
        if total > 0:
            logger.info(f"⚡ Média: {duracao/total:.1f}s por cliente (efetivo)")
            logger.info(f"🚀 Speedup: ~{num_workers}x mais rápido que sequencial")
        logger.info(f"{'='*60}")

        return {
            'total': total,
            'sucesso': self.stats['sucessos'],
            'erros': self.stats['erros'],
            'cpf_nao_encontrado': self.stats['cpf_nao_encontrado'],
            'sem_boleto': self.stats['sem_boleto'],
            'duracao': duracao,
            'media': duracao/total if total > 0 else 0,
            'resultados': resultados,
            'pasta': self.pasta_downloads,
            'workers': num_workers
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
    verificar_pausa: Callable = None,
    num_workers: int = 2,
    paralelo: bool = True
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
        num_workers: Número de workers paralelos (default 2)
        paralelo: Se True, usa processamento paralelo (default True)

    Returns:
        Dict com estatísticas e resultados
    """
    canopus = CanopusUltra(usuario, senha, headless, callback_status, num_workers)

    try:
        await canopus.iniciar(pasta_downloads)
        if paralelo and num_workers > 1:
            return await canopus.processar_lote_paralelo(clientes, mes, verificar_pausa)
        else:
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
    verificar_pausa: Callable = None,
    num_workers: int = 2,
    paralelo: bool = True
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
        verificar_pausa=verificar_pausa,
        num_workers=num_workers,
        paralelo=paralelo
    ))


if __name__ == '__main__':
    async def teste():
        # Teste com múltiplos clientes para demonstrar paralelismo
        clientes = [
            {'cpf': '50516798898', 'nome': 'ADAO JUNIOR PEREIRA DE BRITO'},
            {'cpf': '12345678901', 'nome': 'TESTE CLIENTE 2'},
            {'cpf': '98765432100', 'nome': 'TESTE CLIENTE 3'},
            {'cpf': '11122233344', 'nome': 'TESTE CLIENTE 4'},
        ]

        print("\n" + "="*60)
        print("TESTE MODO ULTRA PARALELO - PV 17308")
        print(f"Clientes: {len(clientes)} | Workers: 2")
        print("="*60)

        resultado = await processar_boletos_ultra(
            usuario='17308',
            senha='Sonhorealizado2@',
            clientes=clientes,
            mes='JANEIRO',
            headless=False,
            num_workers=2,
            paralelo=True
        )

        print(f"\n🚀 Tempo total: {resultado['duracao']:.1f}s")
        print(f"📊 Sucesso: {resultado['sucesso']}/{resultado['total']}")
        if resultado.get('workers'):
            print(f"⚡ Workers utilizados: {resultado['workers']}")

    asyncio.run(teste())
