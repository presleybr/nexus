"""
Bot de Automação para Sistema Canopus
Automatiza login, busca de clientes e download de boletos usando Playwright
"""

from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import time
import random
from datetime import datetime
from cryptography.fernet import Fernet

from config import CanopusConfig

# Configurar logging
logger = logging.getLogger(__name__)


class CanopusBot:
    """Classe principal para automação do sistema Canopus"""

    def __init__(
        self,
        config: CanopusConfig = None,
        headless: bool = None,
        download_path: str = None
    ):
        """
        Inicializa o bot

        Args:
            config: Configurações da automação
            headless: Executar em modo headless (sobrescreve config)
            download_path: Caminho para downloads (sobrescreve config)
        """
        self.config = config or CanopusConfig
        self.headless = headless if headless is not None else self.config.HEADLESS
        self.download_path = download_path or str(self.config.TEMP_DIR)

        # Criar pasta de downloads
        Path(self.download_path).mkdir(parents=True, exist_ok=True)

        # Controle de sessão
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None

        # Estado
        self.logado = False
        self.ponto_venda_atual = None
        self.downloads_realizados = 0

        # Estatísticas
        self.stats = {
            "sucessos": 0,
            "erros": 0,
            "cpf_nao_encontrado": 0,
            "sem_boleto": 0,
            "inicio": None,
            "fim": None,
        }

    def __enter__(self):
        """Context manager - entrada"""
        self.iniciar_navegador()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - saída"""
        self.fechar_navegador()

    def iniciar_navegador(self):
        """Inicia o navegador Playwright"""
        logger.info("🌐 Iniciando navegador...")

        try:
            self.playwright = sync_playwright().start()

            # Selecionar tipo de navegador
            if self.config.BROWSER_TYPE == "firefox":
                self.browser = self.playwright.firefox.launch(headless=self.headless)
            elif self.config.BROWSER_TYPE == "webkit":
                self.browser = self.playwright.webkit.launch(headless=self.headless)
            else:  # chromium (padrão)
                self.browser = self.playwright.chromium.launch(
                    headless=self.headless,
                    args=self.config.BROWSER_ARGS
                )

            # Criar contexto com configurações
            self.context = self.browser.new_context(
                viewport=self.config.VIEWPORT,
                user_agent=self.config.USER_AGENT,
                accept_downloads=True,
                downloads_path=self.download_path,
            )

            # Criar nova página
            self.page = self.context.new_page()

            # Configurar timeouts
            self.page.set_default_timeout(self.config.TIMEOUT_NAVEGACAO)

            logger.info("✅ Navegador iniciado com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao iniciar navegador: {e}")
            raise

    def fechar_navegador(self):
        """Fecha o navegador"""
        logger.info("🔒 Fechando navegador...")

        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            logger.info("✅ Navegador fechado")

        except Exception as e:
            logger.error(f"❌ Erro ao fechar navegador: {e}")

    def fazer_login(
        self,
        usuario: str,
        senha: str,
        ponto_venda_codigo: str = "CREDMS"
    ) -> bool:
        """
        Realiza login no sistema Canopus

        Args:
            usuario: Nome de usuário
            senha: Senha
            ponto_venda_codigo: Código do ponto de venda

        Returns:
            True se login bem-sucedido, False caso contrário
        """
        logger.info(f"🔐 Fazendo login - Usuário: {usuario}, Ponto: {ponto_venda_codigo}")

        try:
            # Navegar para página de login
            logger.info(f"Navegando para: {self.config.CANOPUS_LOGIN_URL}")
            self.page.goto(self.config.CANOPUS_LOGIN_URL)

            # Aguardar página carregar
            self._delay_humanizado()

            # Preencher usuário
            logger.info("Preenchendo usuário...")
            self.page.fill(
                self.config.SELECTORS["login"]["username"],
                usuario
            )

            # Preencher senha
            logger.info("Preenchendo senha...")
            self.page.fill(
                self.config.SELECTORS["login"]["password"],
                senha
            )

            # Selecionar ponto de venda
            if "ponto_venda" in self.config.SELECTORS["login"]:
                logger.info(f"Selecionando ponto de venda: {ponto_venda_codigo}")
                pv_info = self.config.PONTOS_VENDA.get(ponto_venda_codigo)
                if pv_info:
                    self.page.select_option(
                        self.config.SELECTORS["login"]["ponto_venda"],
                        value=pv_info["valor_select"]
                    )

            # Aguardar um pouco (parecer humano)
            self._delay_humanizado()

            # Clicar em login
            logger.info("Clicando em login...")
            self.page.click(self.config.SELECTORS["login"]["submit"])

            # Aguardar navegação após login
            time.sleep(self.config.DELAY_APOS_LOGIN)

            # Verificar se login foi bem-sucedido
            # AJUSTAR: Verificar elemento específico da página logada
            # Exemplo: verificar se existe menu, dashboard, etc.
            # Por enquanto, verificar se URL mudou

            url_atual = self.page.url
            if "login" not in url_atual.lower():
                logger.info("✅ Login realizado com sucesso!")
                self.logado = True
                self.ponto_venda_atual = ponto_venda_codigo
                return True
            else:
                # Verificar se há mensagem de erro
                logger.error("❌ Login falhou - ainda na página de login")
                self.logado = False
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao fazer login: {e}")
            self.logado = False
            return False

    def buscar_cliente_por_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente no sistema pelo CPF

        Args:
            cpf: CPF do cliente (pode estar formatado ou não)

        Returns:
            Dicionário com dados do cliente ou None se não encontrado
        """
        # Limpar CPF
        cpf_limpo = self.config.limpar_cpf(cpf)
        cpf_formatado = self.config.formatar_cpf(cpf_limpo)

        logger.info(f"🔍 Buscando cliente: {cpf_formatado}")

        try:
            # Navegar para busca avançada
            # AJUSTAR: URL e seletores conforme sistema real
            # Por enquanto, assumindo que há um link ou botão "Busca Avançada"

            # Exemplo: self.page.goto(f"{self.config.CANOPUS_URL}/busca-avancada")
            # Ou: self.page.click("text=Busca Avançada")

            # Aguardar campo de busca
            self.page.wait_for_selector(
                self.config.SELECTORS["busca"]["cpf_input"],
                timeout=self.config.TIMEOUT_ELEMENTO
            )

            # Limpar campo e preencher CPF
            self.page.fill(
                self.config.SELECTORS["busca"]["cpf_input"],
                cpf_formatado  # ou cpf_limpo, conforme sistema aceitar
            )

            # Aguardar um pouco
            self._delay_humanizado(minimo=0.5, maximo=1.5)

            # Clicar em buscar
            self.page.click(self.config.SELECTORS["busca"]["btn_buscar"])

            # Aguardar resultados
            time.sleep(self.config.DELAY_APOS_BUSCA)

            # Verificar se cliente foi encontrado
            # AJUSTAR: Seletores conforme sistema real

            # Tentar encontrar resultado
            try:
                resultado = self.page.wait_for_selector(
                    self.config.SELECTORS["busca"]["resultado_cliente"],
                    timeout=5000  # 5 segundos
                )

                if resultado:
                    # Extrair nome do cliente
                    nome_element = self.page.query_selector(
                        self.config.SELECTORS["busca"]["nome_cliente"]
                    )
                    nome = nome_element.inner_text() if nome_element else "N/A"

                    logger.info(f"✅ Cliente encontrado: {nome}")

                    # Clicar no cliente para abrir detalhes
                    self.page.click(self.config.SELECTORS["busca"]["link_cliente"])

                    # Aguardar página de detalhes carregar
                    self._delay_humanizado()

                    return {
                        "cpf": cpf_limpo,
                        "cpf_formatado": cpf_formatado,
                        "nome": nome,
                        "encontrado": True,
                    }

            except PlaywrightTimeout:
                # Cliente não encontrado
                logger.warning(f"⚠️ Cliente não encontrado: {cpf_formatado}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao buscar cliente: {e}")
            return None

    def baixar_boleto(
        self,
        mes_referencia: str = None,
        nome_arquivo: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Baixa boleto do cliente atual

        Args:
            mes_referencia: Mês do boleto (ex: "DEZEMBRO", "JANEIRO")
            nome_arquivo: Nome personalizado para o arquivo (opcional)

        Returns:
            Dicionário com informações do boleto ou None se falhar
        """
        mes = mes_referencia or self.config.MES_PADRAO
        logger.info(f"📥 Baixando boleto - Mês: {mes}")

        try:
            # Navegar para emissão de cobrança
            # AJUSTAR: Conforme sistema real
            # Pode ser um link, botão, ou menu

            # Aguardar select de parcela
            self.page.wait_for_selector(
                self.config.SELECTORS["emissao"]["select_parcela"],
                timeout=self.config.TIMEOUT_ELEMENTO
            )

            # Selecionar parcela do mês
            # AJUSTAR: Lógica de seleção conforme sistema
            # Pode ser por value, texto, etc.
            # Exemplo: self.page.select_option(selector, label=mes)

            self._delay_humanizado()

            # Clicar em emitir cobrança
            self.page.click(self.config.SELECTORS["emissao"]["btn_emitir"])

            # Aguardar PDF ser gerado
            time.sleep(2)

            # Verificar se há link para PDF
            try:
                link_pdf = self.page.wait_for_selector(
                    self.config.SELECTORS["emissao"]["link_pdf"],
                    timeout=10000
                )

                if link_pdf:
                    # Extrair número do boleto se disponível
                    numero_boleto = None
                    try:
                        num_element = self.page.query_selector(
                            self.config.SELECTORS["emissao"]["numero_boleto"]
                        )
                        if num_element:
                            numero_boleto = num_element.inner_text().strip()
                    except:
                        pass

                    # Iniciar download
                    logger.info("📥 Iniciando download do PDF...")

                    with self.page.expect_download(timeout=self.config.TIMEOUT_DOWNLOAD) as download_info:
                        link_pdf.click()

                    download = download_info.value

                    # Aguardar download completar
                    caminho_temp = download.path()

                    # Mover para destino final com nome adequado
                    if nome_arquivo:
                        destino = Path(self.download_path) / nome_arquivo
                    else:
                        # Gerar nome baseado em timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        destino = Path(self.download_path) / f"boleto_{timestamp}.pdf"

                    download.save_as(str(destino))

                    logger.info(f"✅ Boleto baixado: {destino.name}")

                    self.stats["sucessos"] += 1
                    self.downloads_realizados += 1

                    return {
                        "sucesso": True,
                        "caminho_pdf": str(destino),
                        "numero_boleto": numero_boleto,
                        "mes_referencia": mes,
                        "data_download": datetime.now(),
                    }

            except PlaywrightTimeout:
                logger.warning("⚠️ Boleto não disponível ou timeout")
                self.stats["sem_boleto"] += 1
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao baixar boleto: {e}")
            self.stats["erros"] += 1
            return None

    def processar_cliente(
        self,
        cpf: str,
        nome_arquivo: str = None,
        mes_referencia: str = None
    ) -> Dict[str, Any]:
        """
        Processa um cliente completo: busca + download

        Args:
            cpf: CPF do cliente
            nome_arquivo: Nome do arquivo PDF (opcional)
            mes_referencia: Mês do boleto (opcional)

        Returns:
            Dicionário com resultado do processamento
        """
        inicio = time.time()
        resultado = {
            "cpf": self.config.limpar_cpf(cpf),
            "status": None,
            "mensagem": None,
            "dados_cliente": None,
            "dados_boleto": None,
            "tempo_execucao": 0,
        }

        try:
            # Buscar cliente
            cliente = self.buscar_cliente_por_cpf(cpf)

            if not cliente:
                resultado["status"] = self.config.Status.CPF_NAO_ENCONTRADO
                resultado["mensagem"] = "Cliente não encontrado no sistema"
                self.stats["cpf_nao_encontrado"] += 1
                return resultado

            resultado["dados_cliente"] = cliente

            # Baixar boleto
            boleto = self.baixar_boleto(
                mes_referencia=mes_referencia,
                nome_arquivo=nome_arquivo
            )

            if not boleto:
                resultado["status"] = self.config.Status.SEM_BOLETO_DISPONIVEL
                resultado["mensagem"] = "Boleto não disponível para o mês especificado"
                return resultado

            # Sucesso!
            resultado["status"] = self.config.Status.SUCESSO
            resultado["mensagem"] = "Boleto baixado com sucesso"
            resultado["dados_boleto"] = boleto

        except PlaywrightTimeout as e:
            resultado["status"] = self.config.Status.TIMEOUT
            resultado["mensagem"] = f"Timeout: {str(e)}"
            self.stats["erros"] += 1

        except Exception as e:
            resultado["status"] = self.config.Status.ERRO
            resultado["mensagem"] = f"Erro: {str(e)}"
            self.stats["erros"] += 1

        finally:
            # Calcular tempo de execução
            resultado["tempo_execucao"] = round(time.time() - inicio, 2)

        return resultado

    def processar_lote(
        self,
        clientes: List[Dict[str, Any]],
        pasta_destino: str = None,
        mes_referencia: str = None,
        callback_progresso=None
    ) -> List[Dict[str, Any]]:
        """
        Processa um lote de clientes

        Args:
            clientes: Lista de dicionários com dados dos clientes
            pasta_destino: Pasta onde salvar boletos
            mes_referencia: Mês dos boletos
            callback_progresso: Função callback(atual, total, resultado)

        Returns:
            Lista com resultados de cada processamento
        """
        logger.info(f"📊 Processando lote de {len(clientes)} clientes...")

        # Configurar pasta de destino
        if pasta_destino:
            self.download_path = pasta_destino
            Path(pasta_destino).mkdir(parents=True, exist_ok=True)

        # Resetar estatísticas
        self.stats = {
            "sucessos": 0,
            "erros": 0,
            "cpf_nao_encontrado": 0,
            "sem_boleto": 0,
            "inicio": datetime.now(),
            "fim": None,
        }

        resultados = []

        for idx, cliente in enumerate(clientes, 1):
            cpf = cliente.get("cpf")
            nome = cliente.get("nome", "")

            logger.info(f"\n{'=' * 80}")
            logger.info(f"[{idx}/{len(clientes)}] Processando: {nome or cpf}")
            logger.info(f"{'=' * 80}")

            # Gerar nome do arquivo
            cpf_limpo = self.config.limpar_cpf(cpf)
            nome_arquivo = f"{cpf_limpo}.pdf"

            # Processar cliente
            resultado = self.processar_cliente(
                cpf=cpf,
                nome_arquivo=nome_arquivo,
                mes_referencia=mes_referencia
            )

            # Adicionar informações extras
            resultado["nome_cliente"] = nome
            resultado["indice"] = idx

            resultados.append(resultado)

            # Callback de progresso
            if callback_progresso:
                callback_progresso(idx, len(clientes), resultado)

            # Delay entre downloads
            if idx < len(clientes):
                time.sleep(self.config.DELAY_ENTRE_DOWNLOADS)

            # Reiniciar navegador se necessário
            if self.downloads_realizados >= self.config.REINICIAR_NAVEGADOR_APOS:
                logger.info("🔄 Reiniciando navegador (limite de downloads atingido)...")
                self.fechar_navegador()
                time.sleep(2)
                self.iniciar_navegador()
                # Refazer login aqui se necessário
                self.downloads_realizados = 0

        # Finalizar estatísticas
        self.stats["fim"] = datetime.now()

        # Log final
        self._log_estatisticas()

        return resultados

    def _delay_humanizado(self, minimo: float = None, maximo: float = None):
        """
        Adiciona delay aleatório para parecer mais humano

        Args:
            minimo: Delay mínimo em segundos
            maximo: Delay máximo em segundos
        """
        min_delay = minimo or self.config.DELAY_MINIMO
        max_delay = maximo or self.config.DELAY_MAXIMO
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def _log_estatisticas(self):
        """Loga estatísticas da execução"""
        logger.info("\n" + "=" * 80)
        logger.info("ESTATÍSTICAS DA EXECUÇÃO")
        logger.info("=" * 80)
        logger.info(f"✅ Sucessos: {self.stats['sucessos']}")
        logger.info(f"❌ Erros: {self.stats['erros']}")
        logger.info(f"⚠️ CPF não encontrado: {self.stats['cpf_nao_encontrado']}")
        logger.info(f"📄 Sem boleto disponível: {self.stats['sem_boleto']}")

        if self.stats["inicio"] and self.stats["fim"]:
            duracao = self.stats["fim"] - self.stats["inicio"]
            logger.info(f"⏱️ Duração total: {duracao}")

        logger.info("=" * 80 + "\n")

    def screenshot(self, nome: str = None):
        """
        Tira screenshot da página atual

        Args:
            nome: Nome do arquivo (opcional)
        """
        if not self.page:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Adicionar extensão .png se não tiver
        if nome:
            nome_arquivo = f"{nome}.png" if not nome.endswith('.png') else nome
        else:
            nome_arquivo = f"screenshot_{timestamp}.png"

        caminho = self.config.LOGS_DIR / nome_arquivo

        self.page.screenshot(path=str(caminho))
        logger.info(f"📸 Screenshot salvo: {caminho}")


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Exemplo de uso básico
    print("=" * 80)
    print("TESTE DO BOT CANOPUS")
    print("=" * 80)
    print("\n⚠️ Este é apenas um exemplo. Ajuste conforme seu sistema real.\n")

    # Usar context manager
    with CanopusBot(headless=False) as bot:
        # Fazer login (AJUSTAR CREDENCIAIS)
        # sucesso = bot.fazer_login(
        #     usuario="seu_usuario",
        #     senha="sua_senha",
        #     ponto_venda_codigo="CREDMS"
        # )
        #
        # if sucesso:
        #     # Processar alguns clientes
        #     clientes_teste = [
        #         {"cpf": "12345678901", "nome": "Cliente Teste 1"},
        #         {"cpf": "98765432100", "nome": "Cliente Teste 2"},
        #     ]
        #
        #     resultados = bot.processar_lote(
        #         clientes=clientes_teste,
        #         mes_referencia="DEZEMBRO"
        #     )
        #
        #     print("\nResultados:")
        #     for res in resultados:
        #         print(f"  - {res['cpf']}: {res['status']}")

        print("\n⚠️ Descomente o código acima e configure suas credenciais para testar.")
