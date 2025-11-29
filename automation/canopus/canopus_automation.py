"""
Automação Canopus usando Playwright Async
Bot para download automatizado de boletos do sistema Canopus
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import random

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Download,
    TimeoutError as PlaywrightTimeoutError
)

from canopus_config import CanopusConfig
import pandas as pd

# Configurar logging para tempo real no console
logger = logging.getLogger(__name__)

# Forçar output sem buffering para logs em tempo real
class UnbufferedStreamHandler(logging.StreamHandler):
    """Handler que força flush imediato após cada log"""
    def emit(self, record):
        super().emit(record)
        self.flush()

# Configurar handler para stdout com flush imediato
if not logger.handlers:
    handler = UnbufferedStreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def buscar_cliente_banco(cpf: str) -> Optional[Dict[str, Any]]:
    """
    Busca dados do cliente no banco de dados baseado no CPF

    Args:
        cpf: CPF do cliente (com ou sem formatação)

    Returns:
        Dicionário com nome e outras informações ou None se não encontrado
    """
    try:
        import psycopg
        from psycopg.rows import dict_row
        import os

        # Limpar CPF (remover pontos e hífens)
        cpf_limpo = ''.join(filter(str.isdigit, cpf))

        # Usar DATABASE_URL do ambiente (funciona tanto local quanto Render)
        database_url = os.getenv('DATABASE_URL',
            'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2')

        logger.info(f"🔍 DEBUG: Conectando ao banco para buscar CPF {cpf}")
        sys.stdout.flush()

        # Conectar ao banco usando DATABASE_URL
        conn = psycopg.connect(database_url, row_factory=dict_row)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT nome_completo, cpf, ponto_venda
                FROM clientes_finais
                WHERE cpf = %s AND ativo = TRUE
                LIMIT 1
            """, (cpf_limpo,))

            resultado = cur.fetchone()

        conn.close()

        if resultado:
            logger.info(f"✅ DEBUG: Cliente encontrado - Nome: {resultado['nome_completo']}")
            sys.stdout.flush()
            return {
                'nome': resultado['nome_completo'],
                'cpf': resultado['cpf'],
                'ponto_venda': resultado['ponto_venda']
            }
        else:
            logger.warning(f"⚠️ Cliente com CPF {cpf} não encontrado no banco")
            sys.stdout.flush()
            return None

    except Exception as e:
        logger.error(f"❌ Erro ao buscar cliente no banco: {e}")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        return None


def buscar_cliente_planilha(cpf: str, planilha_path: Path = None) -> Optional[Dict[str, Any]]:
    """
    Busca dados do cliente na planilha Excel baseado no CPF
    DEPRECATED: Use buscar_cliente_banco() para buscar do banco de dados

    Args:
        cpf: CPF do cliente (com ou sem formatação)
        planilha_path: Caminho da planilha (usa padrão se não fornecido)

    Returns:
        Dicionário com nome e outras informações ou None se não encontrado
    """
    try:
        # Caminho padrão da planilha
        if not planilha_path:
            planilha_path = Path(r"D:\Nexus\automation\canopus\excel_files\DENER__PLANILHA_GERAL.xlsx")

        if not planilha_path.exists():
            logger.warning(f"Planilha não encontrada: {planilha_path}")
            return None

        # Ler planilha (linha 12 contém os cabeçalhos)
        df = pd.read_excel(planilha_path, header=12)

        # Limpar CPF (remover formatação)
        cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))

        # Buscar CPF na planilha
        # A coluna CPF pode ter formatação diferente, então limpar também
        df['CPF_LIMPO'] = df['CPF'].astype(str).apply(lambda x: ''.join(filter(str.isdigit, x)))

        cliente = df[df['CPF_LIMPO'] == cpf_limpo]

        if cliente.empty:
            logger.warning(f"Cliente com CPF {cpf} não encontrado na planilha")
            return None

        # Pegar primeira ocorrência
        linha = cliente.iloc[0]

        return {
            'nome': str(linha.get('Concorciado', '')).strip() if pd.notna(linha.get('Concorciado')) else '',
            'grupo_cota': str(linha.get('G/C', '')).strip() if pd.notna(linha.get('G/C')) else '',
            'ponto_venda': str(linha.get('P.V', '')).strip() if pd.notna(linha.get('P.V')) else '',
            'situacao': str(linha.get('SITUAÇÃO', '')).strip() if pd.notna(linha.get('SITUAÇÃO')) else '',
        }

    except Exception as e:
        logger.error(f"Erro ao buscar cliente na planilha: {e}")
        return None


def obter_nome_mes(numero_mes: int) -> str:
    """
    Converte número do mês para nome em português

    Args:
        numero_mes: Número do mês (1-12)

    Returns:
        Nome do mês em maiúsculas
    """
    meses = {
        1: 'JANEIRO',
        2: 'FEVEREIRO',
        3: 'MARÇO',
        4: 'ABRIL',
        5: 'MAIO',
        6: 'JUNHO',
        7: 'JULHO',
        8: 'AGOSTO',
        9: 'SETEMBRO',
        10: 'OUTUBRO',
        11: 'NOVEMBRO',
        12: 'DEZEMBRO'
    }
    return meses.get(numero_mes, '')


# ============================================================================
# CLASSE PRINCIPAL DE AUTOMAÇÃO
# ============================================================================

class CanopusAutomation:
    """Automação do sistema Canopus com Playwright"""

    def __init__(
        self,
        config: CanopusConfig = None,
        headless: bool = None
    ):
        """
        Inicializa a automação

        Args:
            config: Configuração (usa padrão se não fornecido)
            headless: Modo headless (sobrescreve config se fornecido)
        """
        self.config = config or CanopusConfig
        self.headless = headless if headless is not None else self.config.PLAYWRIGHT_CONFIG['headless']

        # Estado do navegador
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Estado da sessão
        self.logado = False
        self.empresa_atual = None
        self.ponto_venda_atual = None
        self.usuario_atual = None

        # Estatísticas
        self.stats = {
            'downloads_sucesso': 0,
            'downloads_erro': 0,
            'cpf_nao_encontrado': 0,
            'sem_boleto': 0,
            'inicio_sessao': None,
            'fim_sessao': None,
        }

    # ========================================================================
    # MÉTODOS DE CONTROLE DO NAVEGADOR
    # ========================================================================

    async def iniciar_navegador(self):
        """Inicia o navegador Playwright"""
        logger.info("🌐 Iniciando navegador...")

        try:
            # Iniciar Playwright
            logger.info("🚀 Iniciando Playwright...")
            sys.stdout.flush()
            self.playwright = await async_playwright().start()
            logger.info("✅ Playwright iniciado")
            sys.stdout.flush()

            # Configurações do navegador
            pw_config = self.config.PLAYWRIGHT_CONFIG

            # Argumentos anti-detecção extras
            anti_detection_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]

            # Argumentos para FORÇAR logs do Chromium
            chromium_log_args = [
                '--enable-logging=stderr',  # Logs para stderr
                '--v=2',  # Verbose level 2 (mais detalhado)
                '--log-level=0',  # Log level 0 = INFO
            ]

            # Lançar navegador
            logger.info(f"🌐 Lançando navegador (headless={self.headless})...")
            sys.stdout.flush()

            if pw_config['browser_type'] == 'firefox':
                self.browser = await self.playwright.firefox.launch(
                    headless=self.headless,
                    slow_mo=pw_config['slow_mo']
                )
            elif pw_config['browser_type'] == 'webkit':
                self.browser = await self.playwright.webkit.launch(
                    headless=self.headless,
                    slow_mo=pw_config['slow_mo']
                )
            else:  # chromium (padrão)
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=pw_config['browser_args'] + anti_detection_args + chromium_log_args,
                    slow_mo=pw_config['slow_mo'],
                    # Forçar logs do Chromium para stderr (que será capturado)
                    chromium_sandbox=False  # Desabilitar sandbox para melhor logging
                )

            logger.info("✅ Navegador lançado com sucesso")
            sys.stdout.flush()

            # Criar contexto
            logger.info("🔧 Criando contexto do navegador...")
            sys.stdout.flush()

            self.context = await self.browser.new_context(
                viewport=pw_config['viewport'],
                user_agent=pw_config['user_agent'],
                accept_downloads=pw_config['accept_downloads'],
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
            )

            # Script anti-detecção (executado em todas as páginas)
            await self.context.add_init_script("""
                // Remover webdriver flag
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Sobrescrever plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Chrome runtime
                window.chrome = { runtime: {} };
            """)

            # Criar página
            logger.info("📄 Criando nova página...")
            sys.stdout.flush()
            self.page = await self.context.new_page()
            logger.info("✅ Página criada")
            sys.stdout.flush()

            # Configurar listeners para capturar logs do navegador em TEMPO REAL
            logger.info("🔧 Configurando listeners de console e erros...")
            sys.stdout.flush()

            # Listener de console - captura TODOS os console.log, console.warn, console.error da página
            self.page.on("console", lambda msg: logger.info(f"🖥️  [BROWSER CONSOLE] [{msg.type}] {msg.text}"))

            # Listener de erros de página - captura erros JavaScript e outros
            self.page.on("pageerror", lambda exc: logger.error(f"❌ [BROWSER ERROR] {exc}"))

            # Listener de requests - útil para debug de chamadas de rede
            self.page.on("request", lambda req: logger.debug(f"📤 [REQUEST] {req.method} {req.url}"))

            # Listener de responses - útil para debug de respostas
            self.page.on("response", lambda res: logger.debug(f"📥 [RESPONSE] {res.status} {res.url}"))

            logger.info("✅ Listeners configurados para logging em tempo real")
            sys.stdout.flush()

            # Configurar timeouts
            timeout_nav = self.config.TIMEOUTS['navegacao']
            self.page.set_default_timeout(timeout_nav)
            logger.info(f"⏱️ Timeout configurado: {timeout_nav}ms")
            sys.stdout.flush()

            logger.info("✅ Navegador iniciado com sucesso!")
            sys.stdout.flush()
            self.stats['inicio_sessao'] = datetime.now()

        except Exception as e:
            logger.error(f"❌ Erro ao iniciar navegador: {e}")
            raise

    async def fechar_navegador(self):
        """Fecha o navegador"""
        logger.info("🔒 Fechando navegador...")

        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.stats['fim_sessao'] = datetime.now()
            logger.info("✅ Navegador fechado")

        except Exception as e:
            logger.error(f"❌ Erro ao fechar navegador: {e}")

    async def screenshot(self, nome: str = None):
        """Tira screenshot da página atual"""
        if not self.page:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Adicionar extensão .png se não tiver
        if nome:
            nome_arquivo = f"{nome}.png" if not nome.endswith('.png') else nome
        else:
            nome_arquivo = f"screenshot_{timestamp}.png"

        caminho = self.config.LOGS_DIR / nome_arquivo

        await self.page.screenshot(path=str(caminho))
        logger.info(f"📸 Screenshot: {caminho.name}")

    # ========================================================================
    # MÉTODOS DE LOGIN E AUTENTICAÇÃO
    # ========================================================================

    async def login(
        self,
        usuario: str,
        senha: str,
        codigo_empresa: str = None,
        ponto_venda: str = None
    ) -> bool:
        """
        Realiza login no sistema Canopus

        Args:
            usuario: Nome de usuário
            senha: Senha
            codigo_empresa: Código da empresa (OPCIONAL - não usado no login)
            ponto_venda: Código do ponto de venda (OPCIONAL - não usado no login)

        Returns:
            True se login bem-sucedido, False caso contrário
        """
        logger.info(f"🔐 Fazendo login - User: {usuario}")

        try:
            # Navegar para página de login
            logger.info(f"Navegando para: {self.config.URLS['login']}")
            await self.page.goto(self.config.URLS['login'])
            await self._delay_humanizado()

            # Screenshot antes do login
            await self.screenshot("antes_login")

            # Preencher usuário
            logger.info("Preenchendo usuário...")
            usuario_input = self.config.SELECTORS['login']['usuario_input']
            await self.page.fill(usuario_input, usuario)
            await self._delay_humanizado(0.3, 0.7)

            # Preencher senha
            logger.info("Preenchendo senha...")
            senha_input = self.config.SELECTORS['login']['senha_input']
            await self.page.fill(senha_input, senha)
            await self._delay_humanizado(0.5, 1.0)

            # Screenshot antes de clicar
            await self.screenshot("antes_clicar_login")

            # Clicar em entrar
            logger.info("Clicando no botão Login...")
            botao_entrar = self.config.SELECTORS['login']['botao_entrar']
            await self.page.click(botao_entrar)

            # Aguardar navegação após login
            logger.info("Aguardando navegação...")
            await asyncio.sleep(self.config.DELAYS['apos_login'])

            # Screenshot após login
            await self.screenshot("apos_login")

            # Verificar se login foi bem-sucedido
            url_atual = self.page.url
            logger.info(f"URL após login: {url_atual}")

            if 'login' not in url_atual.lower():
                logger.info("✅ Login realizado com sucesso!")
                self.logado = True
                self.empresa_atual = codigo_empresa
                self.ponto_venda_atual = ponto_venda
                self.usuario_atual = usuario
                return True

            # Verificar mensagem de erro
            try:
                erro_selector = self.config.SELECTORS['login']['erro_login']
                erro_element = await self.page.query_selector(erro_selector)

                if erro_element:
                    mensagem_erro = await erro_element.text_content()
                    logger.error(f"❌ Erro no login: {mensagem_erro}")

            except:
                pass

            logger.error("❌ Login falhou")
            await self.screenshot("login_falhou")
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao fazer login: {e}")
            await self.screenshot("erro_login")
            return False

    async def selecionar_empresa(self, codigo_empresa: str) -> bool:
        """
        Seleciona empresa (se necessário)

        Args:
            codigo_empresa: Código da empresa

        Returns:
            True se selecionado com sucesso
        """
        # PLACEHOLDER: Implementar se houver seleção de empresa após login
        logger.debug(f"Empresa {codigo_empresa} selecionada")
        self.empresa_atual = codigo_empresa
        return True

    # ========================================================================
    # MÉTODOS DE BUSCA DE CLIENTE
    # ========================================================================

    async def navegar_busca_avancada(self) -> bool:
        """
        Navega para a página de busca avançada

        Fluxo:
        1. Clicar no ícone de Atendimento (pessoa)
        2. Clicar em "Busca avançada"

        Returns:
            True se navegou com sucesso
        """
        logger.info("🔍 Navegando para busca avançada...")

        try:
            # 1. Clicar no ícone de Atendimento (pessoa)
            logger.info("Clicando no ícone de Atendimento...")
            icone_atendimento = self.config.SELECTORS['busca']['icone_atendimento']
            await self.page.click(icone_atendimento)
            await self._delay_humanizado(1.0, 2.0)
            await self.screenshot("apos_clicar_atendimento")

            # 2. Clicar em "Busca avançada"
            logger.info("Clicando em 'Busca avançada'...")
            botao_busca_avancada = self.config.SELECTORS['busca']['botao_busca_avancada']
            await self.page.click(botao_busca_avancada)
            await self._delay_humanizado(1.0, 2.0)
            await self.screenshot("apos_busca_avancada")

            logger.info("✅ Navegado para busca avançada")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao navegar para busca: {e}")
            await self.screenshot("erro_navegar_busca")
            return False

    async def buscar_cliente_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente pelo CPF

        Args:
            cpf: CPF do cliente (será limpo automaticamente)

        Returns:
            Dicionário com dados do cliente ou None se não encontrado
        """
        cpf_limpo = self.config.limpar_cpf(cpf)
        cpf_formatado = self.config.formatar_cpf(cpf_limpo)

        logger.info(f"🔍 Buscando cliente: {cpf_formatado}")
        sys.stdout.flush()

        try:
            # Garantir que estamos na página de busca avançada
            await self.navegar_busca_avancada()

            # 1. Selecionar "CPF" no dropdown
            logger.info("Selecionando tipo de busca: CPF")
            sys.stdout.flush()
            select_tipo = self.config.SELECTORS['busca']['select_tipo_busca']
            await self.page.select_option(select_tipo, value='F')  # F = CPF
            await self._delay_humanizado(0.5, 1.0)
            await self.screenshot("apos_selecionar_cpf")

            # 2. Preencher CPF no campo de busca
            logger.info(f"Preenchendo CPF: {cpf_formatado}")
            sys.stdout.flush()
            cpf_input = self.config.SELECTORS['busca']['cpf_input']

            # Limpar campo antes
            await self.page.fill(cpf_input, '')
            await self._delay_humanizado(0.2, 0.5)

            # Preencher CPF (pode ser com ou sem formatação)
            await self.page.fill(cpf_input, cpf_formatado)
            await self._delay_humanizado(0.5, 1.0)
            await self.screenshot("apos_preencher_cpf")

            # 3. Clicar em buscar
            logger.info("Clicando em Buscar...")
            sys.stdout.flush()
            botao_buscar = self.config.SELECTORS['busca']['botao_buscar']
            await self.page.click(botao_buscar)

            # Aguardar resultados
            logger.info("Aguardando resultados da busca...")
            sys.stdout.flush()
            await asyncio.sleep(self.config.DELAYS['apos_busca'])
            await self.screenshot("resultado_busca")

            # Verificar se encontrou resultado
            # Buscar link do cliente (grupo/cota)
            try:
                cliente_link_selector = self.config.SELECTORS['busca']['cliente_link']

                logger.info("Aguardando link do cliente aparecer...")
                sys.stdout.flush()
                # Aguardar o link aparecer
                await self.page.wait_for_selector(
                    cliente_link_selector,
                    timeout=self.config.TIMEOUTS['busca']
                )

                # Buscar todos os links
                links = await self.page.query_selector_all(cliente_link_selector)
                logger.info(f"Encontrados {len(links)} resultado(s)")
                sys.stdout.flush()

                # Clicar no SEGUNDO link (índice 1) - o primeiro sempre está vazio
                if len(links) >= 2:
                    logger.info("Clicando no segundo resultado (com grupo/cota)...")
                    await links[1].click()  # Índice 1 = segundo item
                    await self._delay_humanizado(2.0, 3.0)
                    await self.screenshot("apos_clicar_cliente")

                    logger.info(f"✅ Cliente acessado: {cpf_formatado}")

                    return {
                        'cpf': cpf_limpo,
                        'cpf_formatado': cpf_formatado,
                        'encontrado': True,
                    }
                elif len(links) == 1:
                    # Se só tiver 1 link, clicar nele
                    logger.info("Apenas 1 resultado encontrado, clicando...")
                    await links[0].click()
                    await self._delay_humanizado(2.0, 3.0)
                    await self.screenshot("apos_clicar_cliente")

                    return {
                        'cpf': cpf_limpo,
                        'cpf_formatado': cpf_formatado,
                        'encontrado': True,
                    }
                else:
                    logger.warning("⚠️ Nenhum resultado encontrado")
                    await self.screenshot("sem_resultados")
                    return None

            except PlaywrightTimeoutError:
                # Verificar se há mensagem de "nenhum resultado"
                try:
                    sem_resultado = self.config.SELECTORS['busca']['nenhum_resultado']
                    elemento = await self.page.query_selector(sem_resultado)

                    if elemento:
                        logger.warning(f"⚠️ Cliente não encontrado: {cpf_formatado}")
                        self.stats['cpf_nao_encontrado'] += 1
                        return None

                except:
                    pass

                logger.warning(f"⚠️ Timeout ao buscar cliente: {cpf_formatado}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar cliente: {e}")
            await self.screenshot(f"erro_busca_{cpf_limpo}")
            return None

    # ========================================================================
    # MÉTODOS DE EMISSÃO DE BOLETO
    # ========================================================================

    async def navegar_emissao_cobranca(self) -> bool:
        """
        Navega para página de emissão de cobrança

        Clica no link "Emissão de Cobrança" no menu do cliente

        Returns:
            True se navegou com sucesso
        """
        logger.info("📄 Navegando para emissão de cobrança...")

        try:
            # Clicar no link "Emissão de Cobrança"
            menu_emissao = self.config.SELECTORS['emissao']['menu_emissao']

            logger.info(f"Clicando em 'Emissão de Cobrança'...")
            await self.page.click(menu_emissao)
            await self._delay_humanizado(2.0, 3.0)
            await self.screenshot("apos_clicar_emissao")

            logger.info("✅ Navegado para emissão de cobrança")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao navegar para emissão: {e}")
            await self.screenshot("erro_navegar_emissao")
            return False

    async def selecionar_parcela(self, mes: str, ano: int = None) -> bool:
        """
        Seleciona parcela do mês para emissão

        Args:
            mes: Mês da parcela (ex: 'DEZEMBRO')
            ano: Ano da parcela (opcional)

        Returns:
            True se selecionou com sucesso
        """
        logger.info(f"📅 Selecionando parcela: {mes} {ano or ''}")

        try:
            # PLACEHOLDER: Ajustar conforme sistema real
            select_parcela = self.config.SELECTORS['emissao']['select_parcela']

            # Aguardar select aparecer
            await self.page.wait_for_selector(select_parcela)

            # Selecionar por texto (ajustar conforme formato do sistema)
            # Pode ser por label, value, ou índice
            texto_opcao = f"{mes.upper()}/{ano}" if ano else mes.upper()

            await self.page.select_option(select_parcela, label=texto_opcao)
            await self._delay_humanizado(0.5, 1.0)

            logger.info(f"✅ Parcela {mes} selecionada")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao selecionar parcela: {e}")
            return False

    async def emitir_baixar_boleto(
        self,
        destino: Path,
        nome_arquivo: str = None,
        cpf: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Emite e baixa o boleto

        Args:
            destino: Diretório de destino
            nome_arquivo: Nome do arquivo (gerado automaticamente se não fornecido)
            cpf: CPF do cliente (para buscar nome na planilha)

        Returns:
            Dicionário com informações do boleto ou None se falhar
        """
        logger.info("📥 Emitindo e baixando boleto...")
        sys.stdout.flush()

        try:
            # 1. Aguardar a página de emissão carregar
            logger.info("Aguardando página de emissão carregar...")
            sys.stdout.flush()
            await asyncio.sleep(2)
            await self.screenshot("tela_emissao")

            # BUSCAR INFORMAÇÕES DO CLIENTE NA PLANILHA E EXTRAIR MÊS DO BOLETO
            nome_cliente = ''
            mes_boleto = ''

            # Buscar nome do cliente no banco de dados baseado no CPF
            if cpf:
                logger.info(f"📋 Buscando dados do cliente no banco para CPF: {cpf}...")
                sys.stdout.flush()
                dados_cliente = buscar_cliente_banco(cpf)

                if dados_cliente:
                    nome_cliente = dados_cliente.get('nome', '')
                    # Remover porcentagem e números (ex: "70%", "- 70%")
                    if '%' in nome_cliente:
                        nome_cliente = nome_cliente.split('%')[0].strip()
                    # Remover números finais (ex: "70", "80")
                    import re
                    nome_cliente = re.sub(r'\s*-?\s*\d+\s*$', '', nome_cliente).strip()

                    logger.info(f"👤 Nome do cliente (banco): {nome_cliente}")
                    sys.stdout.flush()
                else:
                    logger.warning(f"⚠️ Cliente não encontrado no banco de dados")
                    sys.stdout.flush()

            # Extrair mês do boleto da página (da tabela) - SEMPRE DA ÚLTIMA LINHA
            info_boleto = await self.page.evaluate("""
                () => {
                    // Extrair mês da data de vencimento da ÚLTIMA linha da tabela
                    let mesBoleto = '';

                    // Mapeamento de números de mês para nomes
                    const mesesNomes = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO',
                                       'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'];

                    // Procurar na tabela de boletos
                    const tabela = document.querySelector('table[id*="grdBoleto_Avulso"]');
                    if (tabela) {
                        const linhas = tabela.querySelectorAll('tr');

                        // Pegar a ÚLTIMA linha que contém dados (não o cabeçalho)
                        if (linhas.length >= 2) {
                            const ultimaLinha = linhas[linhas.length - 1];
                            const celulas = ultimaLinha.querySelectorAll('td');

                            // Procurar por célula que contenha data no formato DD/MM/AAAA
                            for (const celula of celulas) {
                                const texto = celula.textContent.trim();

                                // Regex para encontrar data DD/MM/AAAA ou DD/MM/AA
                                const regexData = /(\d{1,2})\/(\d{1,2})\/(\d{2,4})/;
                                const match = texto.match(regexData);

                                if (match) {
                                    // match[2] contém o mês (MM)
                                    const mesNumero = parseInt(match[2], 10);

                                    // Converter número do mês para nome (1=JANEIRO, 12=DEZEMBRO)
                                    if (mesNumero >= 1 && mesNumero <= 12) {
                                        mesBoleto = mesesNomes[mesNumero - 1];
                                        console.log(`✅ Data encontrada: ${texto}, Mês extraído: ${mesBoleto}`);
                                        break;
                                    }
                                }
                            }
                        }
                    }

                    return {
                        mes: mesBoleto
                    };
                }
            """)

            mes_boleto = info_boleto.get('mes', '').strip()

            # Se não encontrou mês na página, usar mês atual
            if not mes_boleto:
                mes_atual = datetime.now().month
                mes_boleto = obter_nome_mes(mes_atual)
                logger.warning(f"⚠️ Mês não encontrado na página, usando mês atual: {mes_boleto}")
                sys.stdout.flush()
            else:
                logger.info(f"📅 Mês do boleto (página): {mes_boleto}")
                sys.stdout.flush()

            # Se nome_arquivo não foi fornecido, gerar automaticamente
            if not nome_arquivo:
                if nome_cliente and mes_boleto:
                    # Limpar nome do cliente (remover caracteres especiais)
                    nome_limpo = ''.join(c if c.isalnum() or c in ' -_' else '' for c in nome_cliente)
                    nome_limpo = nome_limpo.replace(' ', '_')

                    nome_arquivo = f"{nome_limpo}_{mes_boleto}.pdf"
                    logger.info(f"📝 Nome do arquivo gerado: {nome_arquivo}")
                    sys.stdout.flush()
                else:
                    # Fallback para nome padrão (datetime já importado no topo)
                    nome_arquivo = f"boleto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    logger.warning(f"⚠️ Usando nome padrão: {nome_arquivo}")
                    sys.stdout.flush()

            # 1. AGUARDAR e clicar nos checkboxes dos boletos
            checkbox_selector = self.config.SELECTORS['emissao']['checkbox_boleto']

            logger.info(f"Aguardando checkboxes aparecerem: {checkbox_selector}")
            sys.stdout.flush()

            try:
                # Aguardar o primeiro checkbox aparecer (timeout 10s)
                await self.page.wait_for_selector(checkbox_selector, timeout=10000)
                logger.info("✅ Checkboxes detectados na página!")
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"❌ Timeout aguardando checkboxes: {e}")
                sys.stdout.flush()
                await self.screenshot("timeout_checkboxes")
                raise Exception("Checkboxes não apareceram na página")

            # Aguardar mais 1 segundo para garantir que todos carregaram
            await asyncio.sleep(1)

            logger.info(f"Buscando checkboxes: {checkbox_selector}")
            sys.stdout.flush()
            checkboxes = await self.page.query_selector_all(checkbox_selector)
            logger.info(f"Encontrados {len(checkboxes)} checkbox(es)")
            sys.stdout.flush()

            if len(checkboxes) > 0:
                # SEMPRE selecionar a ÚLTIMA checkbox (última cobrança/parcela)
                ultimo_indice = len(checkboxes) - 1
                logger.info(f"✅ Selecionando ÚLTIMA checkbox (índice {ultimo_indice}) - última cobrança/parcela")

                # Garantir que o checkbox está visível antes de clicar
                await checkboxes[ultimo_indice].scroll_into_view_if_needed()
                await asyncio.sleep(0.5)

                await checkboxes[ultimo_indice].click()  # Índice -1 = último item
                logger.info(f"✅ Checkbox da última cobrança clicado! (Total: {len(checkboxes)} parcelas)")
                await asyncio.sleep(1)
                await self.screenshot("checkbox_selecionado")
            else:
                logger.error("❌ Nenhum checkbox encontrado!")
                await self.screenshot("sem_checkboxes")
                raise Exception("Nenhum checkbox de boleto encontrado na página")

            # 2. Configurar interceptação de resposta de rede ANTES de clicar
            logger.info("Configurando interceptação de PDF...")

            pdf_bytes_interceptado = None
            pdf_url_interceptado = None

            # Ampliar escopo de interceptação para pegar TODAS as requisições
            # v2.0 - Múltiplas estratégias de captura (response.finished + fetch direto)
            todas_respostas_pdf = []

            async def interceptar_pdf(response):
                nonlocal pdf_bytes_interceptado, pdf_url_interceptado, todas_respostas_pdf

                # Verificar se é uma resposta de PDF
                try:
                    content_type = response.headers.get('content-type', '').lower()
                    url = response.url

                    # Log TODAS as respostas potenciais para debug
                    if ('pdf' in content_type or
                        'octet-stream' in content_type or
                        'frmConCmImpressao' in url or
                        url.endswith('.pdf') or
                        '.pdf?' in url):

                        logger.info(f"📥 Interceptando resposta: {url[:70]}...")
                        logger.info(f"   Content-Type: {content_type}")
                        logger.info(f"   Status: {response.status}")
                        sys.stdout.flush()

                        # IMPORTANTE: Aguardar a resposta completar antes de acessar body
                        # Isso evita erros de "Response body is unavailable"
                        try:
                            await response.finished()
                            logger.info("✅ Resposta finalizada, acessando body...")
                            sys.stdout.flush()
                        except Exception as e_finish:
                            logger.warning(f"⚠️ Erro ao aguardar finish: {e_finish}")
                            sys.stdout.flush()

                        body = await response.body()
                        tamanho = len(body)
                        logger.info(f"📦 Corpo recebido: {tamanho} bytes ({tamanho/1024:.1f} KB)")
                        sys.stdout.flush()

                        # Armazenar TODAS as respostas para análise posterior
                        todas_respostas_pdf.append({
                            'url': url,
                            'content_type': content_type,
                            'body': body,
                            'tamanho': tamanho
                        })

                        # Verificar se é um PDF REAL (começa com %PDF)
                        is_real_pdf = body.startswith(b'%PDF')
                        if is_real_pdf:
                            logger.info(f"✅ PDF REAL detectado! (começa com %PDF)")
                            sys.stdout.flush()
                        else:
                            # NÃO é PDF real - logar conteúdo
                            preview = body[:300].decode('latin-1', errors='ignore')
                            logger.warning(f"⚠️ NÃO é PDF real! Preview: {preview[:100]}")
                            sys.stdout.flush()

                        # Só capturar se for um PDF REAL com header correto
                        if is_real_pdf and (pdf_bytes_interceptado is None or tamanho > len(pdf_bytes_interceptado)):
                            pdf_bytes_interceptado = body
                            pdf_url_interceptado = url
                            logger.info(f"🎯 PDF CAPTURADO: {tamanho} bytes ({tamanho/1024:.1f} KB) de {url[:50]}...")
                            sys.stdout.flush()

                except Exception as e:
                    logger.error(f"❌ Erro ao interceptar resposta: {e}")
                    sys.stdout.flush()
                    import traceback
                    traceback.print_exc()
                    sys.stdout.flush()

            # Preparar nome do arquivo
            if not nome_arquivo:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"boleto_{timestamp}.pdf"

            caminho_final = destino / nome_arquivo

            # Registrar handler de resposta no CONTEXTO (para capturar em todas as abas)
            self.context.on('response', interceptar_pdf)

            try:
                # 3. Aguardar e clicar no botão Emitir
                botao_emitir = self.config.SELECTORS['emissao']['botao_emitir']
                logger.info(f"Aguardando botão 'Emitir Cobrança': {botao_emitir}")

                try:
                    # Aguardar botão aparecer (timeout 5s)
                    await self.page.wait_for_selector(botao_emitir, timeout=5000)
                    logger.info("✅ Botão detectado!")
                except Exception as e:
                    logger.error(f"❌ Timeout aguardando botão: {e}")
                    await self.screenshot("timeout_botao")
                    raise Exception(f"Botão não encontrado: {botao_emitir}")

                # Garantir que está visível
                botao = await self.page.query_selector(botao_emitir)
                await botao.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)

                is_visible = await botao.is_visible()
                logger.info(f"Botão visível: {is_visible}")

                # Configurar listener de download ANTES de clicar
                download_capturado = None

                async def capturar_download(download):
                    nonlocal download_capturado
                    download_capturado = download
                    logger.info(f"📥 Download detectado: {download.suggested_filename}")

                self.page.on('download', capturar_download)

                # 4. ESTRATÉGIA: Capturar aba popup e usar diretamente
                logger.info("Clicando em 'Emitir Cobrança'...")
                await self.screenshot("antes_emitir")

                # IMPORTANTE: Injetar script NO CONTEXTO antes da aba abrir
                # Isso previne que a aba feche automaticamente
                try:
                    await self.context.add_init_script("""
                        // Bloquear window.close() para prevenir fechamento automático
                        window.close = function() {
                            console.log('[BLOQUEADO] Tentativa de fechar aba bloqueada!');
                        };
                        console.log('[SCRIPT] Script de prevenção de fechamento carregado');
                    """)
                    logger.info("🔒 Script de prevenção de fechamento injetado no contexto")
                    sys.stdout.flush()
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao injetar script no contexto: {e}")
                    sys.stdout.flush()

                # Capturar a nova aba que será aberta
                nova_aba_pdf = None

                async def capturar_nova_aba(page):
                    nonlocal nova_aba_pdf, pdf_bytes_interceptado, pdf_url_interceptado
                    nova_aba_pdf = page
                    logger.info(f"📄 Nova aba detectada: {page.url}")
                    sys.stdout.flush()

                    # Capturar logs do console JavaScript
                    page.on('console', lambda msg: logger.info(f"[CONSOLE] {msg.text}"))

                    # ESTRATÉGIA AGRESSIVA: Usar page.route() para interceptar PDF ANTES do navegador processar
                    async def route_pdf(route):
                        nonlocal pdf_bytes_interceptado, pdf_url_interceptado
                        request = route.request
                        url = request.url

                        logger.info(f"🔀 [ROUTE] Interceptando: {url[:100]}")
                        sys.stdout.flush()

                        # Continuar com a requisição normalmente
                        response = await route.fetch()

                        # Verificar se é PDF
                        headers = response.headers
                        content_type = headers.get('content-type', '').lower()

                        logger.info(f"🔀 [ROUTE] Content-Type: {content_type}, Status: {response.status}")
                        sys.stdout.flush()

                        # Se for PDF, capturar o body ANTES de passar pro navegador
                        if 'pdf' in content_type or 'frmConCmImpressao' in url:
                            body = await response.body()
                            logger.info(f"🔀 [ROUTE] PDF CAPTURADO: {len(body)} bytes ({len(body)/1024:.1f} KB)")
                            sys.stdout.flush()

                            # Verificar se é PDF real
                            if body.startswith(b'%PDF'):
                                pdf_bytes_interceptado = body
                                pdf_url_interceptado = url
                                logger.info(f"✅ [ROUTE] PDF REAL confirmado!")
                                sys.stdout.flush()

                        # Passar resposta pro navegador
                        await route.fulfill(response=response)

                    # Registrar route handler para TODAS as requisições
                    await page.route('**/*', route_pdf)
                    logger.info("🎯 Route handler registrado para captura agressiva")
                    sys.stdout.flush()

                    # IMPORTANTE: Registrar handler de response NESTA aba específica (fallback)
                    # Isso garante que capturamos o PDF antes do browser processar
                    page.on('response', interceptar_pdf)
                    logger.info("🎯 Handler de PDF registrado na nova aba")
                    sys.stdout.flush()

                    # Log de navegação
                    page.on('framenavigated', lambda frame: logger.info(f"🧭 [NAV] Frame navegou: {frame.url[:100]}"))
                    logger.info("🎯 Listeners de navegação registrados")
                    sys.stdout.flush()

                self.context.on('page', capturar_nova_aba)

                # Clicar no botão
                await self.page.click(botao_emitir)
                logger.info("✅ Clique executado")
                sys.stdout.flush()

                # Aguardar nova aba ser capturada (até 3 segundos)
                contador = 0
                while not nova_aba_pdf and contador < 30:  # 3 segundos
                    await asyncio.sleep(0.1)
                    contador += 1

                # Remover listener
                self.context.remove_listener('page', capturar_nova_aba)

                if not nova_aba_pdf:
                    logger.error("❌ Nova aba com PDF não abriu")
                    sys.stdout.flush()
                    raise Exception("Nova aba com PDF não abriu")

                logger.info(f"✅ Nova aba capturada: {nova_aba_pdf.url[:80] if nova_aba_pdf.url else 'carregando...'}")
                sys.stdout.flush()

                # ESTRATÉGIA: Aguardar o interceptador capturar o PDF real
                # O site faz uma segunda request com o PDF depois do HTML
                nova_aba_controlada = nova_aba_pdf

                try:
                    pdf_bytes = None

                    # Aguardar até 20 segundos pelo interceptador pegar o PDF real (mais tempo para Render)
                    logger.info("⏳ Aguardando interceptador capturar PDF real (até 20s)...")
                    sys.stdout.flush()
                    for tentativa in range(200):  # 200 x 100ms = 20 segundos
                        if pdf_bytes_interceptado and len(pdf_bytes_interceptado) > 10000:
                            pdf_bytes = pdf_bytes_interceptado
                            logger.info(f"✅ PDF INTERCEPTADO: {len(pdf_bytes)} bytes ({len(pdf_bytes)/1024:.1f} KB)")
                            logger.info(f"   URL: {pdf_url_interceptado[:80] if pdf_url_interceptado else 'N/A'}")
                            sys.stdout.flush()
                            break

                        # Log a cada 5 segundos
                        if tentativa % 50 == 0 and tentativa > 0:
                            logger.info(f"⏳ Ainda aguardando... ({tentativa/10:.0f}s)")
                            sys.stdout.flush()

                        await asyncio.sleep(0.1)

                    # Log do resultado da espera
                    if pdf_bytes_interceptado:
                        logger.warning(f"⚠️ PDF interceptado mas muito pequeno: {len(pdf_bytes_interceptado)} bytes")
                        sys.stdout.flush()
                    else:
                        logger.warning(f"⚠️ Nenhum PDF foi interceptado após 10s de espera")
                        logger.info(f"📊 Respostas capturadas: {len(todas_respostas_pdf)}")
                        sys.stdout.flush()

                    # Se não foi interceptado, tentar JavaScript (se a aba ainda estiver aberta)
                    if not pdf_bytes:
                        # ESTRATÉGIA 1: Tentar extrair PDF diretamente da nova aba que foi aberta
                        logger.info("🔄 Tentando extrair PDF da aba popup que foi aberta...")
                        sys.stdout.flush()

                        try:
                            # Aguardar mais tempo no Render para garantir que a aba carregou
                            logger.info("⏳ Aguardando aba carregar completamente...")
                            sys.stdout.flush()
                            await asyncio.sleep(5)  # Aumentado de 2 para 5 segundos

                            # Verificar a URL atual da aba
                            url_atual = nova_aba_pdf.url
                            logger.info(f"📍 URL da aba popup: {url_atual[:100]}")
                            sys.stdout.flush()

                            # Log do estado da página
                            try:
                                titulo = await nova_aba_pdf.title()
                                logger.info(f"📄 Título da página: {titulo}")
                                sys.stdout.flush()
                            except:
                                pass

                            # Se a URL contém PDF ou é a página de impressão, tentar extrair
                            if 'frmConCmImpressao' in url_atual or 'pdf' in url_atual.lower():
                                logger.info("🎯 URL válida detectada, tentando fetch direto...")
                                sys.stdout.flush()

                                # Fazer fetch direto da URL na aba
                                pdf_data_fetch = await nova_aba_pdf.evaluate(f"""
                                    async () => {{
                                        try {{
                                            const response = await fetch('{url_atual}');
                                            if (!response.ok) throw new Error('Fetch falhou: ' + response.status);

                                            const blob = await response.blob();
                                            const buffer = await blob.arrayBuffer();
                                            const bytes = new Uint8Array(buffer);

                                            console.log('[FETCH] PDF baixado: ' + bytes.length + ' bytes');
                                            return {{success: true, bytes: Array.from(bytes)}};
                                        }} catch(e) {{
                                            console.error('[FETCH] Erro: ' + e.message);
                                            return {{success: false, error: e.message}};
                                        }}
                                    }}
                                """)

                                if pdf_data_fetch and pdf_data_fetch.get('success'):
                                    pdf_bytes = bytes(pdf_data_fetch['bytes'])
                                    logger.info(f"✅ PDF extraído por fetch direto: {len(pdf_bytes)} bytes")
                                    sys.stdout.flush()

                        except Exception as e_fetch:
                            logger.warning(f"⚠️ Fetch direto falhou: {e_fetch}")
                            sys.stdout.flush()

                        # ESTRATÉGIA 2: Se ainda não temos PDF, verificar respostas interceptadas
                        if not pdf_bytes and todas_respostas_pdf and len(todas_respostas_pdf) > 0:
                            # Pegar a URL da última response interceptada
                            ultima_url = todas_respostas_pdf[-1]['url']
                            logger.info(f"🔗 Abrindo PDF em nova aba controlada: {ultima_url[:80]}...")

                            # Abrir a URL em uma NOVA aba que CONTROLAMOS (não vai fechar sozinha)
                            nova_aba_nossa = await self.context.new_page()

                            try:
                                await nova_aba_nossa.goto(ultima_url, timeout=15000, wait_until='networkidle')
                                logger.info("✅ PDF carregado em nossa aba")

                                # Aguardar mais um pouco para garantir que o PDF carregou
                                await asyncio.sleep(2)

                                # Tentar extrair via JavaScript desta aba
                                nova_aba_controlada = nova_aba_nossa

                            except Exception as e:
                                logger.error(f"❌ Erro ao navegar para URL do PDF: {e}")
                                await nova_aba_nossa.close()
                                raise

                        logger.info("📥 Iniciando extração do PDF via JavaScript...")
                        sys.stdout.flush()

                        try:
                            nova_aba_controlada.set_default_timeout(30000)  # 30 segundos (aumentado)

                            pdf_data = await nova_aba_controlada.evaluate("""
                                async () => {
                                    console.log('[JS] ========================================');
                                    console.log('[JS] Iniciando extração do PDF do Canopus');
                                    console.log('[JS] ========================================');

                                    // Procurar embed tag
                                    const embed = document.querySelector('embed[type="application/pdf"]');

                                    if (!embed) {
                                        console.error('[JS] ❌ ERRO: Embed não encontrado no DOM!');
                                        console.log('[JS] Tags encontradas:', document.querySelectorAll('embed').length);
                                        return {success: false, error: 'Embed PDF não encontrado no DOM'};
                                    }

                                    console.log('[JS] ✅ Embed encontrado!');
                                    console.log('[JS] Aguardando URL do PDF carregar...');

                                    // AGUARDAR ATIVAMENTE até o embed ter URL válida
                                    // Aumentado para 30 segundos no Render
                                    let pdfUrl = null;
                                    const MAX_TENTATIVAS = 100;  // 100 x 300ms = 30 segundos

                                    for (let i = 0; i < MAX_TENTATIVAS; i++) {
                                        const src = embed.src;

                                        // Verificar se tem URL válida do Canopus
                                        if (src && src !== 'about:blank' &&
                                            (src.includes('frmConCmImpressao') || src.includes('.aspx') || src.includes('pdf'))) {
                                            pdfUrl = src;
                                            console.log(`[JS] ✅ PDF URL encontrada na tentativa ${i+1}!`);
                                            console.log(`[JS] URL: ${pdfUrl.substring(0, 100)}...`);
                                            break;
                                        }

                                        // Log a cada 10 tentativas (3 segundos)
                                        if (i % 10 === 0 && i > 0) {
                                            console.log(`[JS] ⏳ Tentativa ${i}/${MAX_TENTATIVAS}: src="${src ? src.substring(0, 50) : 'null'}"`);
                                        }

                                        await new Promise(r => setTimeout(r, 300));
                                    }

                                    // Validar se encontrou URL válida
                                    if (!pdfUrl || pdfUrl === 'about:blank') {
                                        console.error('[JS] ❌ ERRO: URL do PDF não carregou após 30 segundos!');
                                        console.error(`[JS] URL final: "${pdfUrl}"`);
                                        return {
                                            success: false,
                                            error: 'Timeout: URL do PDF não carregou no embed'
                                        };
                                    }

                                    console.log('[JS] 📡 Fazendo download do PDF...');
                                    console.log(`[JS] URL completa: ${pdfUrl}`);

                                    // Fazer fetch do PDF
                                    try {
                                        const response = await fetch(pdfUrl);

                                        console.log(`[JS] Response status: ${response.status}`);
                                        console.log(`[JS] Content-Type: ${response.headers.get('content-type')}`);

                                        if (!response.ok) {
                                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                                        }

                                        const blob = await response.blob();
                                        console.log(`[JS] Blob recebido: ${blob.size} bytes (${(blob.size/1024).toFixed(1)} KB)`);

                                        if (blob.size === 0) {
                                            throw new Error('Blob vazio - PDF sem conteúdo');
                                        }

                                        // Validar que é realmente PDF
                                        const buffer = await blob.arrayBuffer();
                                        const bytes = new Uint8Array(buffer);

                                        // Verificar magic number do PDF (%PDF)
                                        const isPDF = bytes[0] === 0x25 && bytes[1] === 0x50 &&
                                                     bytes[2] === 0x44 && bytes[3] === 0x46;

                                        if (!isPDF) {
                                            console.error('[JS] ❌ ERRO: Arquivo não é PDF!');
                                            console.error(`[JS] Primeiros bytes: ${Array.from(bytes.slice(0, 10))}`);
                                            throw new Error('Arquivo baixado não é um PDF válido');
                                        }

                                        console.log('[JS] ✅ PDF VÁLIDO extraído com sucesso!');
                                        console.log(`[JS] Tamanho: ${bytes.length} bytes (${(bytes.length/1024).toFixed(1)} KB)`);

                                        return {
                                            success: true,
                                            bytes: Array.from(bytes),
                                            size: bytes.length,
                                            url: pdfUrl
                                        };

                                    } catch (fetchError) {
                                        console.error('[JS] ❌ ERRO no fetch do PDF:', fetchError.toString());
                                        return {
                                            success: false,
                                            error: `Erro ao baixar PDF: ${fetchError.toString()}`
                                        };
                                    }
                                }
                            """)

                            # Processar resultado
                            if pdf_data and pdf_data.get('success'):
                                pdf_bytes = bytes(pdf_data['bytes'])
                                tamanho_kb = len(pdf_bytes) / 1024
                                logger.info("=" * 80)
                                logger.info("✅ PDF EXTRAÍDO COM SUCESSO VIA JAVASCRIPT!")
                                logger.info(f"   Tamanho: {len(pdf_bytes)} bytes ({tamanho_kb:.1f} KB)")
                                logger.info(f"   URL: {pdf_data.get('url', 'N/A')[:100]}...")
                                logger.info("=" * 80)
                                sys.stdout.flush()
                            else:
                                erro = pdf_data.get('error', 'Desconhecido') if pdf_data else 'Sem resposta do JavaScript'
                                logger.error("=" * 80)
                                logger.error("❌ FALHA NA EXTRAÇÃO DO PDF")
                                logger.error(f"   Erro: {erro}")
                                logger.error("=" * 80)
                                sys.stdout.flush()
                                pdf_bytes = None  # Forçar validação a falhar

                        except Exception as e_extract:
                            logger.error("=" * 80)
                            logger.error("❌ EXCEPTION durante extração JavaScript")
                            logger.error(f"   Tipo: {type(e_extract).__name__}")
                            logger.error(f"   Mensagem: {str(e_extract)}")
                            logger.error("=" * 80)
                            sys.stdout.flush()
                            pdf_bytes = None  # Forçar validação a falhar

                    # VALIDAÇÃO CRÍTICA: Verificar se extraiu PDF válido
                    TAMANHO_MINIMO_PDF = 20000  # 20KB - boletos devem ter pelo menos isso

                    if not pdf_bytes:
                        logger.error("❌ ERRO CRÍTICO: Nenhum PDF foi extraído!")
                        logger.error("   O embed do PDF não carregou ou não foi possível fazer fetch")
                        raise Exception("Falha ao extrair PDF do Canopus - nenhum dado recebido")

                    tamanho_kb = len(pdf_bytes) / 1024
                    logger.info(f"📊 PDF extraído: {len(pdf_bytes)} bytes ({tamanho_kb:.1f} KB)")

                    if len(pdf_bytes) < TAMANHO_MINIMO_PDF:
                        logger.error(f"❌ ERRO CRÍTICO: PDF muito pequeno ({tamanho_kb:.1f} KB)")
                        logger.error(f"   Tamanho mínimo esperado: {TAMANHO_MINIMO_PDF/1024:.1f} KB")
                        logger.error(f"   Isso geralmente indica que o PDF não foi carregado corretamente")
                        logger.error(f"   Possíveis causas:")
                        logger.error(f"     1. Embed do PDF não carregou completamente")
                        logger.error(f"     2. URL do PDF estava incorreta")
                        logger.error(f"     3. Problema de rede/timeout")
                        raise Exception(f"PDF inválido - tamanho muito pequeno ({tamanho_kb:.1f} KB < {TAMANHO_MINIMO_PDF/1024:.1f} KB)")

                    # Validar que é realmente um PDF (bytes começam com %PDF)
                    if not pdf_bytes.startswith(b'%PDF'):
                        logger.error("❌ ERRO CRÍTICO: Arquivo não é um PDF válido!")
                        logger.error(f"   Primeiros 50 bytes: {pdf_bytes[:50]}")
                        raise Exception("Arquivo extraído não é um PDF válido (não começa com %PDF)")

                    logger.info("✅ PDF válido! Salvando arquivo...")

                    # Salvar PDF
                    with open(caminho_final, 'wb') as f:
                        f.write(pdf_bytes)

                    logger.info(f"💾 PDF salvo: {nome_arquivo}")
                    logger.info(f"📊 Tamanho final: {len(pdf_bytes)} bytes ({tamanho_kb:.1f} KB)")
                    logger.info(f"📁 Caminho: {caminho_final}")
                    sys.stdout.flush()

                    # AGUARDAR 2 SEGUNDOS para você VER que o PDF foi salvo
                    logger.info("✅ PDF salvo com sucesso! Aguardando 2 segundos...")
                    sys.stdout.flush()
                    await asyncio.sleep(2)

                    # Fechar abas (pode ter 2: popup original + nossa aba)
                    try:
                        await nova_aba_controlada.close()
                        logger.info("🔒 Aba do PDF fechada")
                    except:
                        pass

                    # Fechar popup original se ainda estiver aberta
                    try:
                        if nova_aba_pdf and nova_aba_pdf != nova_aba_controlada:
                            await nova_aba_pdf.close()
                            logger.info("🔒 Aba popup original fechada")
                    except:
                        pass

                    # IMPORTANTE: Voltar para a aba principal após fechar as abas
                    await self.page.bring_to_front()
                    logger.info("✅ Voltou para aba principal - Pronto para próximo CPF")

                    # Remover listener
                    try:
                        self.page.remove_listener('download', capturar_download)
                        self.context.remove_listener('response', interceptar_pdf)
                    except:
                        pass

                    self.stats['downloads_sucesso'] += 1

                    return {
                        'arquivo_nome': nome_arquivo,
                        'arquivo_caminho': str(caminho_final),
                        'arquivo_tamanho': len(pdf_bytes),
                        'pdf_url': pdf_url_interceptado if pdf_url_interceptado else 'N/A',
                        'data_download': datetime.now(),
                        'sucesso': True,
                    }

                except Exception as e_pdf:
                    logger.error(f"❌ Erro ao gerar PDF da aba controlada: {e_pdf}")
                    # Fechar todas as abas
                    try:
                        await nova_aba_controlada.close()
                    except:
                        pass
                    try:
                        if nova_aba_pdf and nova_aba_pdf != nova_aba_controlada:
                            await nova_aba_pdf.close()
                    except:
                        pass
                    # Voltar para aba principal mesmo com erro
                    try:
                        await self.page.bring_to_front()
                        logger.info("✅ Voltou para aba principal (após erro)")
                    except:
                        pass
                    raise

            except PlaywrightTimeoutError as e:
                logger.error(f"❌ Timeout ao baixar boleto: {e}")
                self.stats['downloads_erro'] += 1
                await self.screenshot("timeout_boleto")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao baixar boleto: {e}")
            self.stats['downloads_erro'] += 1
            await self.screenshot("erro_boleto")
            return None

    async def _extrair_dados_boleto(self) -> Dict[str, Any]:
        """Extrai dados do boleto da página"""
        dados = {
            'numero_boleto': None,
            'valor': None,
            'vencimento': None,
        }

        try:
            # Número do boleto
            # PLACEHOLDER: Ajustar seletor
            num_selector = self.config.SELECTORS['emissao']['numero_boleto']
            num_element = await self.page.query_selector(num_selector)
            if num_element:
                dados['numero_boleto'] = (await num_element.text_content()).strip()

            # Valor
            # PLACEHOLDER: Ajustar seletor
            valor_selector = self.config.SELECTORS['emissao']['valor_boleto']
            valor_element = await self.page.query_selector(valor_selector)
            if valor_element:
                dados['valor'] = (await valor_element.text_content()).strip()

            # Vencimento
            # PLACEHOLDER: Ajustar seletor
            venc_selector = self.config.SELECTORS['emissao']['data_vencimento']
            venc_element = await self.page.query_selector(venc_selector)
            if venc_element:
                dados['vencimento'] = (await venc_element.text_content()).strip()

        except Exception as e:
            logger.debug(f"Erro ao extrair dados do boleto: {e}")

        return dados

    # ========================================================================
    # MÉTODO PRINCIPAL - PROCESSAMENTO COMPLETO
    # ========================================================================

    async def processar_cliente_completo(
        self,
        cpf: str,
        mes: str,
        ano: int,
        destino: Path,
        nome_arquivo: str = None
    ) -> Dict[str, Any]:
        """
        Processa um cliente completo: busca + emissão + download

        Args:
            cpf: CPF do cliente
            mes: Mês do boleto
            ano: Ano do boleto
            destino: Diretório de destino
            nome_arquivo: Nome do arquivo (opcional)

        Returns:
            Dicionário com resultado do processamento
        """
        cpf_limpo = self.config.limpar_cpf(cpf)
        inicio = datetime.now()

        resultado = {
            'cpf': cpf_limpo,
            'cpf_formatado': self.config.formatar_cpf(cpf_limpo),
            'mes': mes,
            'ano': ano,
            'status': None,
            'mensagem': None,
            'dados_cliente': None,
            'dados_boleto': None,
            'tempo_execucao_segundos': 0,
        }

        # Log de início claro
        logger.info("")
        logger.info("╔" + "═" * 78 + "╗")
        logger.info(f"║ 🎯 INICIANDO PROCESSAMENTO - CPF: {self.config.formatar_cpf(cpf_limpo)}")
        logger.info("╚" + "═" * 78 + "╝")

        try:
            # 1. Buscar cliente
            cliente = await self.buscar_cliente_cpf(cpf)

            if not cliente:
                resultado['status'] = self.config.Status.CPF_NAO_ENCONTRADO
                resultado['mensagem'] = 'Cliente não encontrado no sistema'
                return resultado

            resultado['dados_cliente'] = cliente

            # 2. Navegar para emissão
            if not await self.navegar_emissao_cobranca():
                resultado['status'] = self.config.Status.ERRO_NAVEGACAO
                resultado['mensagem'] = 'Erro ao navegar para emissão'
                return resultado

            # 3. Selecionar parcela (DESABILITADO - sistema seleciona automaticamente)
            # if not await self.selecionar_parcela(mes, ano):
            #     resultado['status'] = self.config.Status.SEM_BOLETO
            #     resultado['mensagem'] = 'Erro ao selecionar parcela'
            #     return resultado

            # 4. Emitir e baixar boleto
            boleto = await self.emitir_baixar_boleto(destino, nome_arquivo, cpf=cpf)

            if not boleto:
                resultado['status'] = self.config.Status.SEM_BOLETO
                resultado['mensagem'] = 'Boleto não disponível ou erro ao baixar'
                return resultado

            # Sucesso!
            resultado['status'] = self.config.Status.SUCESSO
            resultado['mensagem'] = 'Boleto baixado com sucesso'
            resultado['dados_boleto'] = boleto

            # Log de sucesso visual
            logger.info("")
            logger.info("╔" + "═" * 78 + "╗")
            logger.info(f"║ ✅ BOLETO BAIXADO COM SUCESSO!")
            logger.info(f"║ 📁 Arquivo: {boleto.get('arquivo_nome', 'N/A')}")
            logger.info(f"║ 📊 Tamanho: {boleto.get('arquivo_tamanho', 0) / 1024:.1f} KB")
            logger.info("╚" + "═" * 78 + "╝")
            logger.info("")

        except PlaywrightTimeoutError as e:
            resultado['status'] = self.config.Status.TIMEOUT
            resultado['mensagem'] = f'Timeout: {str(e)}'
            await self.screenshot(f"timeout_{cpf_limpo}")

        except Exception as e:
            resultado['status'] = self.config.Status.ERRO
            resultado['mensagem'] = f'Erro: {str(e)}'
            await self.screenshot(f"erro_{cpf_limpo}")

        finally:
            # Calcular tempo de execução
            fim = datetime.now()
            resultado['tempo_execucao_segundos'] = (fim - inicio).total_seconds()

        return resultado

    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================

    async def _delay_humanizado(self, minimo: float = None, maximo: float = None):
        """
        Adiciona delay aleatório para parecer mais humano

        Args:
            minimo: Delay mínimo em segundos
            maximo: Delay máximo em segundos
        """
        min_delay = minimo or self.config.DELAYS['minimo_humanizado']
        max_delay = maximo or self.config.DELAYS['maximo_humanizado']

        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    def log_estatisticas(self):
        """Loga estatísticas da sessão"""
        logger.info("\n" + "=" * 80)
        logger.info("ESTATÍSTICAS DA SESSÃO")
        logger.info("=" * 80)
        logger.info(f"✅ Downloads sucesso: {self.stats['downloads_sucesso']}")
        logger.info(f"❌ Downloads erro: {self.stats['downloads_erro']}")
        logger.info(f"⚠️ CPF não encontrado: {self.stats['cpf_nao_encontrado']}")
        logger.info(f"📄 Sem boleto: {self.stats['sem_boleto']}")

        if self.stats['inicio_sessao'] and self.stats['fim_sessao']:
            duracao = self.stats['fim_sessao'] - self.stats['inicio_sessao']
            logger.info(f"⏱️ Duração da sessão: {duracao}")

        logger.info("=" * 80 + "\n")

    # ========================================================================
    # CONTEXT MANAGER
    # ========================================================================

    async def __aenter__(self):
        """Async context manager - entrada"""
        await self.iniciar_navegador()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager - saída"""
        self.log_estatisticas()
        await self.fechar_navegador()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def exemplo_uso():
    """Exemplo de como usar a automação"""
    print("=" * 80)
    print("EXEMPLO DE USO - AUTOMAÇÃO CANOPUS")
    print("=" * 80)

    # Usar context manager
    async with CanopusAutomation(headless=False) as bot:
        # Fazer login
        login_ok = await bot.login(
            codigo_empresa='0101',
            ponto_venda='17.308',
            usuario='SEU_USUARIO',  # AJUSTAR
            senha='SUA_SENHA'  # AJUSTAR
        )

        if not login_ok:
            print("❌ Falha no login")
            return

        # Processar um cliente
        resultado = await bot.processar_cliente_completo(
            cpf='12345678901',  # AJUSTAR
            mes='DEZEMBRO',
            ano=2024,
            destino=CanopusConfig.DOWNLOADS_DIR,
            nome_arquivo='teste_boleto.pdf'
        )

        print(f"\nResultado: {resultado['status']}")
        print(f"Mensagem: {resultado['mensagem']}")


if __name__ == "__main__":
    print("\n⚠️ LEMBRE-SE:")
    print("1. Ajustar seletores CSS em config.py conforme sistema real")
    print("2. Configurar credenciais de teste")
    print("3. Executar com headless=False para debug inicial\n")

    # Descomentar para executar exemplo
    # asyncio.run(exemplo_uso())

    print("✅ Módulo carregado. Use asyncio.run() para executar.")
