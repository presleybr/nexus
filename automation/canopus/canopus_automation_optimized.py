"""
Automação Canopus OTIMIZADA
Melhorias de performance e anti-detecção

Melhorias:
- Reutilização de navegador entre downloads
- Técnicas anti-detecção (stealth)
- Interceptação melhorada de PDF
- Timeouts otimizados
- Retry automático
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import random

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError
)

from config import CanopusConfig
import pandas as pd

logger = logging.getLogger(__name__)


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

        # Limpar CPF (remover pontos e hífens)
        cpf_limpo = ''.join(filter(str.isdigit, cpf))

        # Conectar ao banco
        conn = psycopg.connect(
            host='localhost',
            port=5434,
            dbname='nexus_crm',
            user='postgres',
            password='nexus2025',
            row_factory=dict_row
        )

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
            return {
                'nome': resultado['nome_completo'],
                'cpf': resultado['cpf'],
                'ponto_venda': resultado['ponto_venda']
            }
        else:
            logger.warning(f"Cliente com CPF {cpf} não encontrado no banco")
            return None

    except Exception as e:
        logger.error(f"Erro ao buscar cliente no banco: {e}")
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


class CanopusAutomationOptimized:
    """Automação Canopus otimizada com anti-detecção"""

    def __init__(self, headless: bool = False):
        self.config = CanopusConfig
        self.headless = headless

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.logado = False
        self.usuario_atual = None

        self.stats = {
            'downloads_sucesso': 0,
            'downloads_erro': 0,
            'cpf_nao_encontrado': 0,
            'tempo_total': 0,
        }

    async def iniciar_navegador(self):
        """Inicia navegador com técnicas anti-detecção"""
        logger.info("🌐 Iniciando navegador otimizado...")

        try:
            self.playwright = await async_playwright().start()

            # Argumentos anti-detecção
            args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-infobars',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--no-sandbox',
            ]

            # Lançar navegador
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=args,
                slow_mo=50  # Reduzir de 100ms para 50ms
            )

            # Contexto com anti-detecção
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                accept_downloads=True,
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                permissions=['geolocation'],
                java_script_enabled=True,
            )

            # Remover webdriver flag
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Sobrescrever plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // Sobrescrever languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en']
                });

                // Chrome runtime
                window.chrome = {
                    runtime: {}
                };
            """)

            # Criar página
            self.page = await self.context.new_page()

            # Timeouts otimizados
            self.page.set_default_timeout(20000)  # 20s (reduzido de 30s)

            logger.info("✅ Navegador iniciado (anti-detecção ativado)")

        except Exception as e:
            logger.error(f"❌ Erro ao iniciar navegador: {e}")
            raise

    async def fechar_navegador(self):
        """Fecha navegador"""
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
            logger.info("✅ Navegador fechado")
        except Exception as e:
            logger.error(f"❌ Erro ao fechar navegador: {e}")

    async def screenshot(self, nome: str = None):
        """Screenshot (apenas se necessário)"""
        if not self.page or self.headless:
            return

        try:
            nome_arquivo = f"{nome}.png" if nome and not nome.endswith('.png') else nome or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            caminho = self.config.LOGS_DIR / nome_arquivo
            await self.page.screenshot(path=str(caminho))
        except:
            pass  # Ignorar erros de screenshot

    async def login(self, usuario: str, senha: str) -> bool:
        """Login otimizado"""
        logger.info(f"🔐 Login: {usuario}")

        try:
            # Navegar para login
            await self.page.goto(
                self.config.URLS['login'],
                wait_until='load'  # Usar 'load' para garantir estabilidade
            )
            await asyncio.sleep(1.5)

            # Aguardar elementos estarem prontos
            await self.page.wait_for_selector('#ctl00_Conteudo_txtUsuario', state='visible', timeout=10000)

            # Preencher e enviar
            await self.page.fill('#ctl00_Conteudo_txtUsuario', usuario)
            await self.page.fill('#ctl00_Conteudo_txtSenha', senha)

            # Clicar e aguardar navegação
            await self.page.click('#ctl00_Conteudo_btnEntrar')
            await asyncio.sleep(3)  # Tempo para login processar

            # Verificar sucesso
            url_atual = self.page.url
            if 'login' not in url_atual.lower():
                logger.info("✅ Login OK!")
                self.logado = True
                self.usuario_atual = usuario
                return True

            logger.error("❌ Login falhou")
            return False

        except Exception as e:
            logger.error(f"❌ Erro no login: {e}")
            return False

    async def buscar_cliente_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """Busca cliente otimizada"""
        cpf_limpo = self.config.limpar_cpf(cpf)
        cpf_formatado = self.config.formatar_cpf(cpf_limpo)

        logger.info(f"🔍 Buscando: {cpf_formatado}")

        try:
            # Clicar Atendimento
            await self.page.click('img[title="Atendimento"]', timeout=10000)
            await asyncio.sleep(1)  # Reduzido de 2s

            # Busca Avançada
            await self.page.click('text=Busca avançada', timeout=10000)
            await asyncio.sleep(1)

            # Selecionar CPF
            await self.page.select_option('#ctl00_Conteudo_ddlTipoBusca', 'F')
            await asyncio.sleep(0.5)  # Reduzido de 1s

            # Preencher e buscar
            await self.page.fill('#ctl00_Conteudo_txtBusca', cpf_formatado)
            await self.page.click('#ctl00_Conteudo_btnBuscar')
            await asyncio.sleep(1.5)  # Reduzido de 2s

            # Clicar no resultado
            links = await self.page.query_selector_all('a[id*="lnkNome"]')
            if len(links) >= 2:
                await links[1].click()
            elif len(links) >= 1:
                await links[0].click()
            else:
                logger.warning(f"⚠️ Cliente não encontrado: {cpf_formatado}")
                return None

            await asyncio.sleep(2)  # Reduzido de 3s

            logger.info(f"✅ Cliente acessado: {cpf_formatado}")
            return {
                'cpf': cpf_limpo,
                'cpf_formatado': cpf_formatado,
                'encontrado': True,
            }

        except PlaywrightTimeoutError:
            logger.warning(f"⚠️ Timeout ao buscar: {cpf_formatado}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return None

    async def navegar_emissao_cobranca(self) -> bool:
        """Navega para emissão"""
        logger.info("📄 Navegando para emissão...")

        try:
            await self.page.click('text=Emissão de Cobrança', timeout=10000)
            await asyncio.sleep(2)  # Reduzido de 3s
            logger.info("✅ Navegado para emissão")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao navegar: {e}")
            return False

    async def emitir_baixar_boleto(
        self,
        destino: Path,
        nome_arquivo: str = None,
        cpf: str = None
    ) -> Optional[Dict[str, Any]]:
        """Emite e baixa boleto - OTIMIZADO COM MÚLTIPLAS ESTRATÉGIAS"""
        logger.info("📥 Emitindo boleto...")

        try:
            await asyncio.sleep(1.5)

            # BUSCAR INFORMAÇÕES DO CLIENTE NA PLANILHA E EXTRAIR MÊS DO BOLETO
            nome_cliente = ''
            mes_boleto = ''

            # Buscar nome do cliente no banco de dados baseado no CPF
            if cpf and not nome_arquivo:
                logger.info(f"📋 Buscando dados do cliente no banco para CPF: {cpf}...")
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
                else:
                    logger.warning(f"⚠️ Cliente não encontrado no banco de dados")

            # Extrair mês do boleto da página (da tabela)
            if not nome_arquivo:
                logger.info("📋 Extraindo mês do boleto da página...")

                info_boleto = await self.page.evaluate("""
                    () => {
                        // Extrair mês do boleto da tabela
                        let mesBoleto = '';

                        // Procurar na tabela de boletos pela linha do segundo item (índice 1)
                        const tabela = document.querySelector('table[id*="grdBoleto_Avulso"]');
                        if (tabela) {
                            const linhas = tabela.querySelectorAll('tr');
                            // A segunda linha (índice 2) geralmente contém o boleto com valor
                            if (linhas.length >= 3) {
                                const segundaLinha = linhas[2];
                                const celulas = segundaLinha.querySelectorAll('td');

                                // Procurar por célula que contenha o mês (geralmente na 3ª ou 4ª coluna)
                                for (const celula of celulas) {
                                    const texto = celula.textContent.trim().toUpperCase();
                                    // Buscar por meses em português
                                    const meses = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO',
                                                   'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'];

                                    for (const mes of meses) {
                                        if (texto.includes(mes)) {
                                            mesBoleto = mes;
                                            break;
                                        }
                                    }

                                    if (mesBoleto) break;
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
                else:
                    logger.info(f"📅 Mês do boleto (página): {mes_boleto}")

                # Gerar nome do arquivo automaticamente
                if nome_cliente and mes_boleto:
                    # Limpar nome do cliente (remover caracteres especiais)
                    nome_limpo = ''.join(c if c.isalnum() or c in ' -_' else '' for c in nome_cliente)
                    nome_limpo = nome_limpo.replace(' ', '_')

                    nome_arquivo = f"{nome_limpo}_{mes_boleto}.pdf"
                    logger.info(f"📝 Nome do arquivo gerado: {nome_arquivo}")
                else:
                    # Fallback para nome padrão
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_arquivo = f"boleto_{timestamp}.pdf"
                    logger.warning(f"⚠️ Usando nome padrão: {nome_arquivo}")

            # Selecionar checkbox
            checkboxes = await self.page.query_selector_all(
                'input[id*="grdBoleto_Avulso"][id*="imgEmite_Boleto"]'
            )

            if not checkboxes:
                logger.error("❌ Nenhum checkbox encontrado")
                return None

            # Clicar segundo checkbox
            checkbox_idx = 1 if len(checkboxes) >= 2 else 0
            await checkboxes[checkbox_idx].click()
            await asyncio.sleep(0.5)

            caminho_final = destino / nome_arquivo

            # ESTRATÉGIA 1: Interceptação de response
            pdf_bytes_interceptado = None
            pdf_url_real = None

            async def interceptar_pdf(response):
                nonlocal pdf_bytes_interceptado, pdf_url_real
                try:
                    content_type = response.headers.get('content-type', '').lower()
                    url = response.url

                    # Log para debug
                    if 'pdf' in content_type or 'frmConCmImpressao' in url:
                        logger.info(f"📄 Resposta PDF detectada: {url}")
                        logger.info(f"   Content-Type: {content_type}")

                    if ('pdf' in content_type or
                        'octet-stream' in content_type or
                        'frmConCmImpressao' in url):

                        body = await response.body()
                        tamanho = len(body)
                        logger.info(f"📦 Corpo recebido: {tamanho} bytes")

                        # Só atualizar se for maior (capturar maior chunk)
                        if pdf_bytes_interceptado is None or tamanho > len(pdf_bytes_interceptado):
                            pdf_bytes_interceptado = body
                            pdf_url_real = url
                            logger.info(f"✅ PDF atualizado: {tamanho} bytes")
                except Exception as e:
                    logger.debug(f"Erro ao interceptar response: {e}")

            # Registrar interceptador
            self.context.on('response', interceptar_pdf)

            nova_aba = None

            try:
                # Clicar em Emitir e aguardar nova aba
                logger.info("🖱️  Clicando em Emitir...")
                async with self.context.expect_page(timeout=25000) as new_page_info:
                    await self.page.click('#ctl00_Conteudo_btnEmitir')

                nova_aba = await new_page_info.value
                logger.info(f"📂 Nova aba aberta: {nova_aba.url}")

                # ESTRATÉGIA 2: Aguardar URL mudar de about:blank
                tentativas_url = 0
                while nova_aba.url == 'about:blank' and tentativas_url < 10:
                    await asyncio.sleep(0.5)
                    tentativas_url += 1
                    logger.debug(f"⏳ Aguardando URL mudar... ({tentativas_url}/10)")

                if nova_aba.url != 'about:blank':
                    logger.info(f"🔗 URL carregada: {nova_aba.url}")
                    pdf_url_real = nova_aba.url

                # Aguardar load completo
                try:
                    await nova_aba.wait_for_load_state('load', timeout=15000)
                    logger.info("✅ Página carregada")
                except:
                    logger.warning("⚠️  Timeout no load, continuando...")

                # Aguardar PDF carregar completamente
                await asyncio.sleep(4)  # Tempo para PDF renderizar

                # ESTRATÉGIA 3: Se interceptação falhou, tentar via CDP ou fetch
                if not pdf_bytes_interceptado or len(pdf_bytes_interceptado) < 10000:
                    logger.warning(f"⚠️  Interceptação incompleta ({len(pdf_bytes_interceptado) if pdf_bytes_interceptado else 0} bytes)")

                    # Se temos URL real, tentar buscar diretamente
                    if pdf_url_real and pdf_url_real != 'about:blank':
                        logger.info(f"🔄 Tentando fetch direto da URL: {pdf_url_real}")
                        try:
                            # Usar a própria página para fazer fetch (mantém sessão)
                            pdf_content = await nova_aba.evaluate("""
                                async (url) => {
                                    const response = await fetch(url);
                                    const blob = await response.blob();
                                    const buffer = await blob.arrayBuffer();
                                    return Array.from(new Uint8Array(buffer));
                                }
                            """, pdf_url_real)

                            if pdf_content and len(pdf_content) > 10000:
                                pdf_bytes_interceptado = bytes(pdf_content)
                                logger.info(f"✅ PDF obtido via fetch: {len(pdf_bytes_interceptado)} bytes")
                        except Exception as e:
                            logger.warning(f"⚠️  Fetch direto falhou: {e}")

                # ESTRATÉGIA 4: Tentar obter via page.pdf() se ainda não temos
                if not pdf_bytes_interceptado or len(pdf_bytes_interceptado) < 10000:
                    logger.info("🔄 Tentando page.pdf()...")
                    try:
                        pdf_bytes_interceptado = await nova_aba.pdf()
                        logger.info(f"✅ PDF obtido via page.pdf(): {len(pdf_bytes_interceptado)} bytes")
                    except Exception as e:
                        logger.warning(f"⚠️  page.pdf() falhou: {e}")

                # Salvar PDF se temos conteúdo válido
                if pdf_bytes_interceptado and len(pdf_bytes_interceptado) > 1000:
                    with open(caminho_final, 'wb') as f:
                        f.write(pdf_bytes_interceptado)

                    tamanho_kb = len(pdf_bytes_interceptado) / 1024
                    logger.info(f"💾 PDF salvo: {nome_arquivo} ({tamanho_kb:.1f} KB)")

                    # Fechar aba
                    try:
                        if nova_aba and not nova_aba.is_closed():
                            await nova_aba.close()
                    except:
                        pass

                    self.stats['downloads_sucesso'] += 1

                    return {
                        'arquivo_nome': nome_arquivo,
                        'arquivo_caminho': str(caminho_final),
                        'arquivo_tamanho': len(pdf_bytes_interceptado),
                        'pdf_url': pdf_url_real or nova_aba.url,
                        'data_download': datetime.now(),
                        'sucesso': True,
                    }
                else:
                    logger.error(f"❌ PDF inválido ou incompleto: {len(pdf_bytes_interceptado) if pdf_bytes_interceptado else 0} bytes")

                    # Screenshot para debug
                    try:
                        if nova_aba and not nova_aba.is_closed():
                            await nova_aba.screenshot(path=str(self.config.LOGS_DIR / "pdf_falha.png"))
                            logger.info("📸 Screenshot salvo: pdf_falha.png")
                    except:
                        pass

                    # Fechar aba
                    try:
                        if nova_aba and not nova_aba.is_closed():
                            await nova_aba.close()
                    except:
                        pass

                    return None

            finally:
                self.context.remove_listener('response', interceptar_pdf)

        except PlaywrightTimeoutError:
            logger.error("❌ Timeout ao baixar boleto")
            self.stats['downloads_erro'] += 1
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao baixar boleto: {e}")
            self.stats['downloads_erro'] += 1
            return None

    async def processar_cliente_completo(
        self,
        cpf: str,
        destino: Path,
        nome_arquivo: str = None
    ) -> Dict[str, Any]:
        """Processa cliente completo (otimizado)"""
        inicio = datetime.now()
        cpf_limpo = self.config.limpar_cpf(cpf)

        resultado = {
            'cpf': cpf_limpo,
            'cpf_formatado': self.config.formatar_cpf(cpf_limpo),
            'status': None,
            'mensagem': None,
            'arquivo': None,
            'tempo_segundos': 0,
        }

        try:
            # Buscar
            cliente = await self.buscar_cliente_cpf(cpf)
            if not cliente:
                resultado['status'] = 'CPF_NAO_ENCONTRADO'
                resultado['mensagem'] = 'Cliente não encontrado'
                self.stats['cpf_nao_encontrado'] += 1
                return resultado

            # Navegar para emissão
            if not await self.navegar_emissao_cobranca():
                resultado['status'] = 'ERRO_NAVEGACAO'
                resultado['mensagem'] = 'Erro ao navegar para emissão'
                return resultado

            # Emitir e baixar
            boleto = await self.emitir_baixar_boleto(destino, nome_arquivo, cpf=cpf)
            if not boleto:
                resultado['status'] = 'SEM_BOLETO'
                resultado['mensagem'] = 'Erro ao baixar boleto'
                return resultado

            # Sucesso
            resultado['status'] = 'SUCESSO'
            resultado['mensagem'] = 'Boleto baixado com sucesso'
            resultado['arquivo'] = boleto['arquivo_caminho']

        except Exception as e:
            resultado['status'] = 'ERRO'
            resultado['mensagem'] = f'Erro: {str(e)}'
            logger.error(f"❌ Erro ao processar {cpf}: {e}")

        finally:
            fim = datetime.now()
            resultado['tempo_segundos'] = (fim - inicio).total_seconds()
            self.stats['tempo_total'] += resultado['tempo_segundos']

        return resultado

    def log_estatisticas(self):
        """Loga estatísticas"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 ESTATÍSTICAS DA SESSÃO")
        logger.info("=" * 80)
        logger.info(f"✅ Downloads sucesso: {self.stats['downloads_sucesso']}")
        logger.info(f"❌ Downloads erro: {self.stats['downloads_erro']}")
        logger.info(f"⚠️  CPF não encontrado: {self.stats['cpf_nao_encontrado']}")
        logger.info(f"⏱️  Tempo total: {self.stats['tempo_total']:.1f}s")

        if self.stats['downloads_sucesso'] > 0:
            media = self.stats['tempo_total'] / self.stats['downloads_sucesso']
            logger.info(f"📈 Tempo médio/boleto: {media:.1f}s")

        logger.info("=" * 80 + "\n")

    async def __aenter__(self):
        await self.iniciar_navegador()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.log_estatisticas()
        await self.fechar_navegador()


# Exemplo de uso
if __name__ == "__main__":
    print("Use test_otimizado.py para testar!")
