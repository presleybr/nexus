"""
Cliente HTTP FINAL para sistema Canopus
Baseado nos seletores e URLs que JÁ FUNCIONAM na automação Playwright

URLs e campos extraídos de:
- config.py (seletores reais)
- canopus_automation.py (fluxo funcionando)
- testar_busca_cpf.py (teste validado)
"""

import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import warnings

import requests
from bs4 import BeautifulSoup

from config import CanopusConfig

# Suprimir warnings de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CanopusAPI')


class CanopusAPIFinal:
    """
    Cliente HTTP para sistema Canopus - VERSÃO FINAL
    Usa os mesmos seletores e URLs da automação Playwright que funciona
    """

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()

        # Headers completos para parecer navegador real
        self.session.headers.update({
            'User-Agent': CanopusConfig.PLAYWRIGHT_CONFIG['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        })

        # Configurar adapter com retry e keep-alive
        adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        # Desabilitar verificação SSL (pode ser necessário)
        self.session.verify = True  # Manter True por padrão

        self.timeout = timeout
        self._logged_in = False
        self._usuario_atual = None

    def _extract_asp_fields(self, html: str) -> Dict[str, str]:
        """Extrai campos ocultos do ASP.NET"""
        soup = BeautifulSoup(html, 'html.parser')
        fields = {}

        hidden_fields = [
            '__VIEWSTATE',
            '__VIEWSTATEGENERATOR',
            '__EVENTVALIDATION',
            '__EVENTTARGET',
            '__EVENTARGUMENT',
            '__LASTFOCUS',
            '__SCROLLPOSITIONX',
            '__SCROLLPOSITIONY',
        ]

        for field_name in hidden_fields:
            field = soup.find('input', {'name': field_name})
            if field:
                value = field.get('value', '')
                if value:  # Só adiciona se tiver valor
                    fields[field_name] = value

        return fields

    def _extract_field_value_by_id(self, html: str, field_id: str) -> Optional[str]:
        """Extrai valor de um campo pelo ID"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remover # do ID se tiver
        field_id = field_id.lstrip('#')

        field = soup.find('input', {'id': field_id})
        if field:
            return field.get('value', '')

        field = soup.find('select', {'id': field_id})
        if field:
            selected = field.find('option', {'selected': True})
            if selected:
                return selected.get('value', '')

        return None

    def _get_field_name_from_id(self, html: str, field_id: str) -> Optional[str]:
        """Converte ID do campo para name (para POST)"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remover # do ID
        field_id = field_id.lstrip('#')

        # Procurar campo
        field = soup.find(['input', 'select', 'button'], {'id': field_id})
        if field:
            return field.get('name') or field_id

        return field_id

    def login(self, usuario: str, senha: str) -> bool:
        """
        Faz login no sistema Canopus

        Baseado em: config.py SELECTORS['login']
        URL: https://cnp3.consorciocanopus.com.br/WWW/frmCorCCCnsLogin.aspx

        Campos REAIS:
        - #edtUsuario (usuario)
        - #edtSenha (senha)
        - #btnLogin (botão)
        """
        try:
            logger.info(f"🔐 Fazendo login: {usuario}")

            # URL real do sistema (pode ter applicationKey)
            login_url = CanopusConfig.URLS['login']

            # 1. GET na página de login (pega ViewState)
            logger.debug(f"Acessando: {login_url}")

            try:
                # Tentar primeiro sem applicationKey
                response = self.session.get(
                    login_url,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()

            except (requests.ConnectionError, requests.exceptions.SSLError) as e:
                # Se falhar, pode ser SSL ou conexão
                logger.warning(f"⚠️ Erro na primeira tentativa: {e}")
                logger.info("Tentando com verificação SSL desabilitada...")

                # Tentar sem verificar SSL
                self.session.verify = False
                response = self.session.get(
                    login_url,
                    timeout=self.timeout,
                    allow_redirects=True
                )

            # Extrair campos ASP.NET
            asp_fields = self._extract_asp_fields(response.text)
            logger.debug(f"Campos ASP extraídos: {list(asp_fields.keys())}")

            # Converter IDs para nomes de campos
            soup = BeautifulSoup(response.text, 'html.parser')

            # Pegar os NAME attributes dos campos (ASP.NET usa names, não IDs)
            usuario_field = soup.find('input', {'id': 'edtUsuario'})
            senha_field = soup.find('input', {'id': 'edtSenha'})
            botao_field = soup.find('input', {'id': 'btnLogin'})

            if not usuario_field or not senha_field or not botao_field:
                logger.error("❌ Campos de login não encontrados no HTML!")
                return False

            usuario_name = usuario_field.get('name', 'edtUsuario')
            senha_name = senha_field.get('name', 'edtSenha')
            botao_name = botao_field.get('name', 'btnLogin')
            botao_value = botao_field.get('value', 'Login')

            logger.debug(f"Campo usuário: {usuario_name}")
            logger.debug(f"Campo senha: {senha_name}")
            logger.debug(f"Botão: {botao_name}")

            # 2. POST com credenciais
            login_data = {
                **asp_fields,
                usuario_name: usuario,
                senha_name: senha,
                botao_name: botao_value,
            }

            logger.debug("Enviando credenciais...")
            response = self.session.post(
                login_url,
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )

            # 3. Verificar se login OK
            # Se redirecionou para frmMain.aspx = sucesso
            if 'frmMain.aspx' in response.url:
                self._logged_in = True
                self._usuario_atual = usuario
                logger.info("✅ Login bem-sucedido!")
                return True

            # Verificar erros comuns
            if 'senha inválida' in response.text.lower() or 'senha incorreta' in response.text.lower():
                logger.error("❌ Senha inválida")
                return False

            if 'usuário inválido' in response.text.lower() or 'usuário incorreto' in response.text.lower():
                logger.error("❌ Usuário inválido")
                return False

            # Se ainda está na página de login
            if 'frmCorCCCnsLogin.aspx' in response.url:
                logger.error("❌ Login falhou - ainda na página de login")
                # Salvar HTML para debug
                debug_file = CanopusConfig.LOGS_DIR / 'login_falhou.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.debug(f"HTML salvo em: {debug_file}")
                return False

            logger.warning("⚠️ Status do login incerto")
            return False

        except requests.RequestException as e:
            logger.error(f"❌ Erro de rede no login: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado no login: {e}")
            import traceback
            traceback.print_exc()
            return False

    def buscar_cliente_por_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente por CPF

        Fluxo baseado em canopus_automation.py:
        1. Clicar em Atendimento (ícone)
        2. Clicar em "Busca avançada"
        3. Selecionar "CPF" (valor 'F')
        4. Preencher CPF
        5. Clicar "Buscar"

        Seletores REAIS (config.py):
        - #ctl00_img_Atendimento (ícone)
        - #ctl00_Conteudo_btnBuscaAvancada (botão)
        - #ctl00_Conteudo_cbxCriterioBusca (dropdown - valor 'F' = CPF)
        - #ctl00_Conteudo_edtContextoBusca (input CPF)
        - #ctl00_Conteudo_btnBuscar (botão buscar)
        """
        if not self._logged_in:
            logger.error("❌ Não está logado!")
            return None

        try:
            cpf_limpo = re.sub(r'[^\d]', '', cpf)
            cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

            logger.info(f"🔍 Buscando cliente: {cpf_formatado}")

            # Nota: Como é interação com menus (JavaScript),
            # precisamos encontrar a URL direta da busca avançada
            # Vamos tentar acessar direto ou simular o clique

            # Tentar URL direta (pode variar)
            busca_urls = [
                f'{CanopusConfig.CANOPUS_BASE_URL}/WWW/CONCO/frmConCoConsulta.aspx',
                f'{CanopusConfig.CANOPUS_BASE_URL}/WWW/CONAT/frmConAtBuscaAvancada.aspx',
                f'{CanopusConfig.CANOPUS_BASE_URL}/WWW/frmBuscaAvancada.aspx',
            ]

            busca_url = None
            for url in busca_urls:
                try:
                    logger.debug(f"Tentando URL de busca: {url}")
                    response = self.session.get(url, timeout=self.timeout)
                    if response.status_code == 200 and 'busca' in response.text.lower():
                        busca_url = url
                        logger.debug(f"✅ URL de busca encontrada: {url}")
                        break
                except:
                    continue

            if not busca_url:
                logger.error("❌ Não foi possível encontrar URL de busca avançada")
                logger.info("💡 Dica: Execute 'python capturar_requisicoes_v2.py --cpf XXX' para mapear a URL exata")
                return None

            # Extrair campos ASP
            asp_fields = self._extract_asp_fields(response.text)

            # Montar POST de busca
            soup = BeautifulSoup(response.text, 'html.parser')

            # Encontrar campos pelo ID (converter para name)
            tipo_busca_field = soup.find('select', {'id': 'ctl00_Conteudo_cbxCriterioBusca'})
            cpf_field = soup.find('input', {'id': 'ctl00_Conteudo_edtContextoBusca'})
            buscar_btn = soup.find('input', {'id': 'ctl00_Conteudo_btnBuscar'})

            if not tipo_busca_field or not cpf_field or not buscar_btn:
                logger.error("❌ Campos de busca não encontrados!")
                return None

            search_data = {
                **asp_fields,
                tipo_busca_field.get('name'): 'F',  # F = CPF
                cpf_field.get('name'): cpf_formatado,
                buscar_btn.get('name'): buscar_btn.get('value', 'Buscar'),
            }

            logger.debug("Executando busca...")
            response = self.session.post(
                busca_url,
                data=search_data,
                timeout=self.timeout
            )

            # Parsear resultado
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procurar link do cliente
            # Seletor real: a[id*="grdBuscaAvancada"][id*="lnkID_Documento"]
            cliente_links = soup.select('a[id*="grdBuscaAvancada"][id*="lnkID_Documento"]')

            if not cliente_links:
                logger.warning(f"⚠️ Cliente não encontrado: {cpf_formatado}")
                return None

            # Pegar segundo link (primeiro é header)
            if len(cliente_links) >= 2:
                cliente_link = cliente_links[1]
            else:
                cliente_link = cliente_links[0]

            cliente_url = cliente_link.get('href')

            logger.info(f"✅ Cliente encontrado: {cpf_formatado}")

            return {
                'cpf': cpf_limpo,
                'cpf_formatado': cpf_formatado,
                'encontrado': True,
                'url': cliente_url,
            }

        except requests.RequestException as e:
            logger.error(f"❌ Erro de rede na busca: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado na busca: {e}")
            import traceback
            traceback.print_exc()
            return None

    def emitir_boleto(self, cliente_url: str) -> Optional[bytes]:
        """
        Emite boleto e retorna PDF

        Fluxo:
        1. Acessar página do cliente
        2. Navegar para Emissão de Cobrança
        3. Selecionar checkbox do boleto
        4. Clicar "Emitir Cobrança"
        5. Baixar PDF

        Seletores REAIS:
        - #ctl00_Conteudo_Menu_CONAT_grdMenu_CONAT_ctl05_hlkFormulario (link Emissão)
        - input[id*="grdBoleto_Avulso"][id*="imgEmite_Boleto"] (checkbox)
        - #ctl00_Conteudo_btnEmitir (botão emitir)
        """
        if not self._logged_in:
            logger.error("❌ Não está logado!")
            return None

        try:
            logger.info("📄 Emitindo boleto...")

            # 1. Acessar cliente
            if cliente_url:
                if not cliente_url.startswith('http'):
                    cliente_url = f"{CanopusConfig.CANOPUS_BASE_URL}{cliente_url}"

                logger.debug(f"Acessando cliente: {cliente_url}")
                response = self.session.get(cliente_url, timeout=self.timeout)
                response.raise_for_status()

            # 2. Navegar para emissão (clicar no link do menu)
            # URL pode ser obtida do link ou tentada diretamente
            emissao_urls = [
                f'{CanopusConfig.CANOPUS_BASE_URL}/WWW/CONCM/frmConCmEmissao.aspx',
                f'{CanopusConfig.CANOPUS_BASE_URL}/WWW/CONCM/frmEmissaoCobranca.aspx',
            ]

            emissao_url = None
            for url in emissao_urls:
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    if response.status_code == 200:
                        emissao_url = url
                        break
                except:
                    continue

            if not emissao_url:
                logger.error("❌ URL de emissão não encontrada")
                return None

            # 3. Extrair campos e montar POST
            asp_fields = self._extract_asp_fields(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Encontrar checkboxes de boleto
            checkboxes = soup.select('input[id*="grdBoleto_Avulso"][id*="imgEmite_Boleto"]')

            if not checkboxes:
                logger.error("❌ Nenhum boleto disponível para emissão")
                return None

            # Pegar segundo checkbox (primeiro geralmente é header)
            if len(checkboxes) >= 2:
                checkbox = checkboxes[1]
            else:
                checkbox = checkboxes[0]

            checkbox_name = checkbox.get('name')

            # Botão emitir
            botao_emitir = soup.find('input', {'id': 'ctl00_Conteudo_btnEmitir'})
            if not botao_emitir:
                logger.error("❌ Botão 'Emitir Cobrança' não encontrado")
                return None

            emitir_data = {
                **asp_fields,
                checkbox_name: 'on',  # Selecionar checkbox
                botao_emitir.get('name'): botao_emitir.get('value', 'Emitir Cobrança'),
            }

            logger.debug("Emitindo boleto...")
            response = self.session.post(
                emissao_url,
                data=emitir_data,
                timeout=self.timeout
            )

            # 4. Parsear resposta para encontrar PDF
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procurar iframe ou link do PDF
            pdf_iframe = soup.find('iframe', {'src': re.compile('frmConCmImpressao')})

            if pdf_iframe:
                pdf_url = pdf_iframe.get('src')
                if not pdf_url.startswith('http'):
                    pdf_url = f"{CanopusConfig.CANOPUS_BASE_URL}{pdf_url}"

                logger.debug(f"Baixando PDF: {pdf_url}")
                response = self.session.get(pdf_url, timeout=self.timeout)

                if response.status_code == 200 and len(response.content) > 1000:
                    logger.info(f"✅ PDF baixado: {len(response.content)} bytes")
                    return response.content
                else:
                    logger.error("❌ PDF muito pequeno ou inválido")
                    return None
            else:
                logger.error("❌ Link do PDF não encontrado")
                return None

        except requests.RequestException as e:
            logger.error(f"❌ Erro de rede ao emitir: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao emitir: {e}")
            import traceback
            traceback.print_exc()
            return None

    def baixar_boleto(self, pdf_bytes: bytes, cpf: str, consultor: str = "Danner") -> str:
        """Salva PDF em arquivo"""
        pasta = CanopusConfig.DOWNLOADS_DIR / consultor
        pasta.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cpf_limpo = re.sub(r'[^\d]', '', cpf)
        arquivo = pasta / f"boleto_{cpf_limpo}_{timestamp}.pdf"

        with open(arquivo, 'wb') as f:
            f.write(pdf_bytes)

        tamanho_kb = len(pdf_bytes) / 1024
        logger.info(f"✅ Salvo: {arquivo.name} ({tamanho_kb:.1f} KB)")

        return str(arquivo)

    def logout(self):
        """Faz logout"""
        if self._logged_in:
            try:
                self.session.get(f'{CanopusConfig.CANOPUS_BASE_URL}/WWW/Logout.aspx', timeout=5)
            except:
                pass
            finally:
                self._logged_in = False
                self._usuario_atual = None
                logger.info("🔒 Logout realizado")


# =============================================================================
# TESTE RÁPIDO
# =============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("CANOPUS API - VERSÃO FINAL")
    print("Baseada nos seletores e URLs que JÁ FUNCIONAM")
    print("=" * 80)
    print()

    print("⚠️  NOTA: Esta API HTTP precisa que você execute primeiro:")
    print("   python capturar_requisicoes_v2.py --cpf SEU_CPF")
    print()
    print("   Isso vai mapear as URLs exatas do sistema.")
    print()
    print("=" * 80)
