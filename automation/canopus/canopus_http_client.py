"""
Cliente HTTP Real para Canopus
Baseado no mapeamento completo de requisições reais

Requisições mapeadas em: logs/requisicoes_20251126_001008.json
Análise em: mapear_fluxo.py
"""

import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import urllib3

import requests
from bs4 import BeautifulSoup

from canopus_config import CanopusConfig

# Suprimir warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CanopusHTTP')


class CanopusHTTPClient:
    """
    Cliente HTTP Real do Canopus
    Simula exatamente as requisições do navegador
    """

    BASE_URL = 'https://cnp3.consorciocanopus.com.br/WWW'

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()

        # Headers ULTRA-REALISTAS idênticos ao navegador Chrome real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })

        # CRÍTICO: Manter verify=True para não ser detectado como bot
        self.session.verify = True
        self.timeout = timeout
        self._logged_in = False
        self.last_url = None  # Para Referer dinâmico

        # Configurar retry strategy (comportamento humano: tentar novamente)
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _safe_request(self, method: str, url: str, delay_before: float = 0.5, **kwargs):
        """
        Faz requisição HTTP SEGURA com:
        - Delay antes (simula tempo humano)
        - Referer automático (simula navegação real)
        - Retry em caso de falha

        Args:
            method: 'GET' ou 'POST'
            url: URL alvo
            delay_before: Delay em segundos antes da requisição (padrão: 0.5s)
            **kwargs: Argumentos para requests (data, json, etc)
        """
        import time
        import random

        # ANTI-DETECÇÃO: Delay aleatório antes da requisição
        actual_delay = delay_before + random.uniform(0, 0.3)  # Variação humana
        logger.debug(f"🕐 Delay antes de {method} {url}: {actual_delay:.2f}s")
        time.sleep(actual_delay)

        # ANTI-DETECÇÃO: Adicionar Referer se houver URL anterior
        headers = kwargs.get('headers', {})
        if self.last_url and self.last_url != url:
            headers['Referer'] = self.last_url
            logger.debug(f"📎 Referer: {self.last_url[:60]}...")

        kwargs['headers'] = headers

        # Fazer requisição
        if method.upper() == 'GET':
            response = self.session.get(url, **kwargs)
        else:
            response = self.session.post(url, **kwargs)

        # Atualizar última URL (para próximo Referer)
        self.last_url = url

        return response

    def _extract_asp_fields(self, html: str) -> Dict[str, str]:
        """Extrai campos ASP.NET do HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        fields = {}

        # Campos obrigatórios do ASP.NET
        asp_fields = [
            '__VIEWSTATE',
            '__VIEWSTATEGENERATOR',
            '__EVENTVALIDATION',
            '__VSIG',  # Campo específico do Canopus
            '__VIEWSTATEENCRYPTED',
            '__EVENTTARGET',
            '__EVENTARGUMENT',
            '__LASTFOCUS',
            '__SCROLLPOSITIONX',
            '__SCROLLPOSITIONY',
        ]

        for field_name in asp_fields:
            field = soup.find('input', {'name': field_name})
            if field and field.get('value'):
                fields[field_name] = field.get('value', '')

        return fields

    def login(self, usuario: str, senha: str) -> bool:
        """
        Login no Canopus

        Baseado em:
        POST /WWW/frmCorCCCnsLogin.aspx
        Campos:
          - edtUsuario: 000024627+  (com zeros à esquerda)
          - edtSenha: Sonhorealizado2!
          - __EVENTTARGET: btnLogin
        """
        try:
            # CORREÇÃO: Garantir formato com zeros à esquerda (10 dígitos)
            # O Canopus exige formato: 0000024627 (10 dígitos com zeros)
            usuario_formatado = str(usuario).strip().zfill(10)
            logger.info(f"🔐 Login: {usuario_formatado}")

            # 1. GET na página de login (COM DELAY)
            url_login = f'{self.BASE_URL}/frmCorCCCnsLogin.aspx'
            logger.debug(f"GET {url_login}")

            response = self._safe_request('GET', url_login, delay_before=1.0, timeout=self.timeout)
            response.raise_for_status()

            # 2. Extrair campos ASP
            asp_fields = self._extract_asp_fields(response.text)
            logger.debug(f"Campos ASP: {list(asp_fields.keys())}")

            # 3. Montar POST de login (campos REAIS do mapeamento)
            login_data = {
                **asp_fields,
                '__LASTFOCUS': '',
                '__EVENTTARGET': 'btnLogin',
                '__EVENTARGUMENT': '',
                'edtUsuario': usuario_formatado,  # Com zeros à esquerda (10 dígitos)
                'edtSenha': senha,
                'hdnTokenRecaptcha': '',
                'as_fid': '',  # Gerado automaticamente
            }

            # Log detalhado dos campos do formulário
            logger.info(f"📝 Campos do formulário de login:")
            logger.info(f"   edtUsuario: {usuario_formatado}")
            logger.info(f"   edtSenha: {'*' * len(senha)}")
            logger.info(f"   __VIEWSTATE presente: {'Sim' if '__VIEWSTATE' in asp_fields else 'Não'}")
            logger.info(f"   __EVENTVALIDATION presente: {'Sim' if '__EVENTVALIDATION' in asp_fields else 'Não'}")
            logger.info(f"   __EVENTTARGET: {login_data.get('__EVENTTARGET', 'N/A')}")
            logger.info(f"   Total de campos ASP: {len(asp_fields)}")

            # Log completo dos campos (exceto senha e ViewState gigante)
            logger.info(f"🔍 DEBUG - Todos os campos do POST:")
            for key, value in login_data.items():
                if 'senha' in key.lower():
                    logger.info(f"   {key}: ********")
                elif 'viewstate' in key.lower():
                    logger.info(f"   {key}: {value[:50] if value else 'vazio'}...")
                else:
                    logger.info(f"   {key}: {value}")

            # 4. POST login (COM DELAY e Referer)
            logger.info("📤 Enviando POST de login...")
            response = self._safe_request(
                'POST',
                url_login,
                delay_before=1.5,  # Delay maior (humano preenchendo formulário)
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )

            # 5. Verificar sucesso
            logger.info(f"🔍 DEBUG Login - URL final: {response.url}")
            logger.info(f"🔍 DEBUG Login - Status: {response.status_code}")
            logger.info(f"🔍 DEBUG Login - Tamanho HTML: {len(response.text)} bytes")

            # Procurar mensagens de erro no HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procurar por QUALQUER span com texto de erro
            error_spans = soup.find_all('span', {'class': re.compile('.*erro.*', re.I)})
            error_spans += soup.find_all('span', {'id': re.compile('.*erro.*', re.I)})
            error_spans += soup.find_all('div', {'class': re.compile('.*erro.*|.*alert.*', re.I)})

            if error_spans:
                for span in error_spans:
                    texto = span.get_text(strip=True)
                    if texto:
                        logger.error(f"❌ Mensagem de erro no HTML: {texto}")

            # Verificar título da página
            title = soup.find('title')
            if title:
                logger.info(f"📄 Título da página: {title.get_text(strip=True)}")

            # Procurar por scripts que possam ter mensagens de erro
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string if script.string else ''
                if 'alert' in script_text.lower() or 'erro' in script_text.lower():
                    logger.warning(f"⚠️ Script com possível erro: {script_text[:200]}...")

            # Se redirecionou para frmMain.aspx = sucesso
            if 'frmMain.aspx' in response.url:
                self._logged_in = True
                logger.info("✅ Login OK! (detectado por URL)")
                return True

            # Verificar se tem ValidaSessaoLogin ou frmMain no HTML
            if 'ValidaSessaoLogin' in response.text or 'frmMain' in response.text or 'bem-vindo' in response.text.lower():
                self._logged_in = True
                logger.info("✅ Login OK! (detectado por conteúdo)")
                return True

            logger.error("❌ Login falhou - não detectou sucesso")
            logger.error(f"   URL: {response.url}")
            logger.error(f"   HTML preview: {response.text[:500]}")

            # Salvar HTML completo para análise
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(response.text)
                    logger.error(f"   💾 HTML completo salvo em: {f.name}")
            except Exception as e:
                logger.warning(f"⚠️ Não conseguiu salvar HTML: {e}")

            return False

        except Exception as e:
            logger.error(f"❌ Erro no login: {e}")
            return False

    def buscar_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente por CPF

        Baseado em:
        POST /WWW/CONAT/frmBuscaCota.aspx
        Campos:
          - ctl00$Conteudo$cbxCriterioBusca: F
          - ctl00$Conteudo$edtContextoBusca: 708.990.571-36
          - ctl00$Conteudo$btnBuscar: Buscar
        """
        if not self._logged_in:
            logger.error("❌ Não logado!")
            return None

        try:
            cpf_limpo = re.sub(r'[^\d]', '', cpf)
            cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

            logger.info(f"🔍 Buscando: {cpf_formatado}")

            # 1. Navegar para busca (clicar em Atendimento primeiro)
            # POST /WWW/frmMain.aspx com img_Atendimento
            url_main = f'{self.BASE_URL}/frmMain.aspx'
            response = self._safe_request('GET', url_main, delay_before=1.5, timeout=self.timeout)

            asp_fields = self._extract_asp_fields(response.text)

            # Clicar em Atendimento
            atendimento_data = {
                **asp_fields,
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                'ctl00$hdnID_Modulo': '',
                'ctl00$img_Atendimento.x': '12',
                'ctl00$img_Atendimento.y': '23',
                'as_fid': '',
            }

            response = self._safe_request(
                'POST',
                url_main,
                delay_before=1.5,
                data=atendimento_data,
                timeout=self.timeout,
                allow_redirects=True
            )

            # 2. Acessar frmBuscaCota.aspx
            url_busca = f'{self.BASE_URL}/CONAT/frmBuscaCota.aspx'
            response = self._safe_request('GET', url_busca, delay_before=1.5, timeout=self.timeout)

            asp_fields = self._extract_asp_fields(response.text)

            # 3. Selecionar CPF no dropdown (EVENTTARGET = cbxCriterioBusca)
            select_cpf_data = {
                **asp_fields,
                '__LASTFOCUS': '',
                '__EVENTTARGET': 'ctl00$Conteudo$cbxCriterioBusca',
                '__EVENTARGUMENT': '',
                'ctl00$hdnID_Modulo': '',
                'ctl00$Conteudo$cbxCriterioBusca': 'F',  # F = CPF
                'ctl00$Conteudo$edtContextoBusca': '',
                'as_fid': '',
            }

            response = self._safe_request(
                'POST',
                url_busca,
                delay_before=1.0,
                data=select_cpf_data,
                timeout=self.timeout
            )

            # 4. Preencher CPF e buscar
            asp_fields = self._extract_asp_fields(response.text)

            buscar_data = {
                **asp_fields,
                '__LASTFOCUS': '',
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                'ctl00$hdnID_Modulo': '',
                'ctl00$Conteudo$cbxCriterioBusca': 'F',
                'ctl00$Conteudo$edtContextoBusca': cpf_formatado,
                'ctl00$Conteudo$btnBuscar': 'Buscar',
            }

            logger.debug("POST busca...")
            response = self._safe_request(
                'POST',
                url_busca,
                delay_before=2.0,  # Delay maior para evitar 500
                data=buscar_data,
                timeout=self.timeout
            )

            # 5. Parsear resultado
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procurar link do resultado (grdBuscaAvancada)
            links = soup.select('a[id*="grdBuscaAvancada"][id*="lnkGrupoCota"]')

            if not links:
                logger.warning(f"⚠️ CPF não encontrado: {cpf_formatado}")
                return None

            # Pegar primeiro link (ctl03)
            link = links[0] if len(links) == 1 else links[1]

            logger.info(f"✅ Cliente encontrado!")

            return {
                'cpf': cpf_limpo,
                'cpf_formatado': cpf_formatado,
                'link_elemento': link.get('id'),  # Ex: ctl00_Conteudo_grdBuscaAvancada_ctl03_lnkGrupoCota
                'encontrado': True,
            }

        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            import traceback
            traceback.print_exc()
            return None

    def acessar_cliente(self, link_elemento: str) -> bool:
        """
        Acessa o cliente clicando no link da busca

        Baseado em:
        POST /WWW/CONAT/frmBuscaCota.aspx
        __EVENTTARGET: ctl00$Conteudo$grdBuscaAvancada$ctl03$lnkGrupoCota
        """
        try:
            logger.info(f"📂 Acessando cliente...")

            url_busca = f'{self.BASE_URL}/CONAT/frmBuscaCota.aspx'

            # Pegar página atual (COM DELAY aumentado para evitar 500)
            response = self._safe_request('GET', url_busca, delay_before=1.5, timeout=self.timeout)
            asp_fields = self._extract_asp_fields(response.text)

            # Extrair CPF da busca anterior (campo pode estar preenchido)
            soup = BeautifulSoup(response.text, 'html.parser')
            cpf_field = soup.find('input', {'id': 'ctl00_Conteudo_edtContextoBusca'})
            cpf_valor = cpf_field.get('value', '') if cpf_field else ''

            # Clicar no link (COM DELAY aumentado)
            click_data = {
                **asp_fields,
                '__LASTFOCUS': '',
                '__EVENTTARGET': link_elemento,
                '__EVENTARGUMENT': '',
                'ctl00$hdnID_Modulo': '',
                'ctl00$Conteudo$cbxCriterioBusca': 'F',
                'ctl00$Conteudo$edtContextoBusca': cpf_valor,
                'as_fid': '',
            }

            response = self._safe_request(
                'POST',
                url_busca,
                delay_before=2.0,  # Delay maior para evitar 500 errors
                data=click_data,
                timeout=self.timeout,
                allow_redirects=True
            )

            # Deve redirecionar para frmConAtCnsAtendimento.aspx
            if 'frmConAtCnsAtendimento' in response.url or response.status_code == 200:
                logger.info("✅ Cliente acessado!")
                return True

            logger.error("❌ Falha ao acessar cliente")
            return False

        except Exception as e:
            logger.error(f"❌ Erro ao acessar cliente: {e}")
            return False

    def emitir_boleto(self) -> Optional[bytes]:
        """
        Emite boleto e retorna PDF

        Baseado em:
        GET /WWW/CONCO/frmConCoRelBoletoAvulso.aspx
        POST com checkbox e botão emitir
        """
        try:
            logger.info("📄 Emitindo boleto...")

            # 1. Acessar página de emissão (COM DELAY aumentado)
            url_emissao = f'{self.BASE_URL}/CONCO/frmConCoRelBoletoAvulso.aspx'
            response = self._safe_request('GET', url_emissao, delay_before=1.5, timeout=self.timeout)

            asp_fields = self._extract_asp_fields(response.text)

            # 2. Clicar no checkbox do boleto (COM DELAY - simula leitura da lista)
            checkbox_data = {
                **asp_fields,
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__SCROLLPOSITIONX': '0',
                '__SCROLLPOSITIONY': '0',
                'ctl00$hdnID_Modulo': '',
                'ctl00$Conteudo$edtForma': '',
                'ctl00$Conteudo$edtDT_Compensacao': datetime.now().strftime('%d/%m/%Y'),
                'ctl00$Conteudo$rdlTipoEmissao': 'BA',
                'ctl00$Conteudo$grdBoleto_Avulso$ctl03$imgEmite_Boleto.x': '11',
                'ctl00$Conteudo$grdBoleto_Avulso$ctl03$imgEmite_Boleto.y': '7',
                'ctl00$Conteudo$hdn_VL_Total_Receber_Sem_TxCob': '',
                'ctl00$Conteudo$hid_SN_Debito_Conta_Cota': 'N',
                'ctl00$Conteudo$hid_SN_Debito_Conta_Forma_Recebimento': 'N',
                'ctl00$Conteudo$hid_SN_Agenda_Debito_Avulso': 'N',
                'ctl00$Conteudo$hid_SN_Mesma_Conta_Debito': 'N',
                'as_fid': '',
            }

            response = self._safe_request(
                'POST',
                url_emissao,
                delay_before=2.0,  # Delay aumentado para evitar 500
                data=checkbox_data,
                timeout=self.timeout
            )

            # 3. Clicar em "Emitir" (COM DELAY aumentado)
            asp_fields = self._extract_asp_fields(response.text)

            emitir_data = {
                **asp_fields,
                '__EVENTTARGET': 'ctl00$Conteudo$btnEmitir',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__SCROLLPOSITIONX': '0',
                '__SCROLLPOSITIONY': '0',
                'ctl00$hdnID_Modulo': '',
                'ctl00$Conteudo$edtForma': '',
                'ctl00$Conteudo$edtDT_Compensacao': datetime.now().strftime('%d/%m/%Y'),
                'ctl00$Conteudo$rdlTipoEmissao': 'BA',
                'ctl00$Conteudo$hdn_VL_Total_Receber_Sem_TxCob': '',
                'ctl00$Conteudo$hid_SN_Debito_Conta_Cota': 'N',
                'ctl00$Conteudo$hid_SN_Debito_Conta_Forma_Recebimento': 'N',
                'ctl00$Conteudo$hid_SN_Agenda_Debito_Avulso': 'N',
                'ctl00$Conteudo$hid_SN_Mesma_Conta_Debito': 'N',
            }

            response = self._safe_request(
                'POST',
                url_emissao,
                delay_before=1.5,  # Delay aumentado
                data=emitir_data,
                timeout=self.timeout
            )

            # 4. Verificar popup (btnVerificaPopUp)
            asp_fields = self._extract_asp_fields(response.text)

            popup_data = {
                **asp_fields,
                '__EVENTTARGET': 'ctl00$Conteudo$btnVerificaPopUp',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__SCROLLPOSITIONX': '0',
                '__SCROLLPOSITIONY': '0',
                'ctl00$hdnID_Modulo': '',
                'ctl00$Conteudo$edtForma': '',
                'ctl00$Conteudo$edtDT_Compensacao': datetime.now().strftime('%d/%m/%Y'),
                'ctl00$Conteudo$rdlTipoEmissao': 'BA',
                'ctl00$Conteudo$hdn_VL_Total_Receber_Sem_TxCob': '',
                'ctl00$Conteudo$hid_SN_Debito_Conta_Cota': 'N',
                'ctl00$Conteudo$hid_SN_Debito_Conta_Forma_Recebimento': 'N',
                'ctl00$Conteudo$hid_SN_Agenda_Debito_Avulso': 'N',
                'ctl00$Conteudo$hid_SN_Mesma_Conta_Debito': 'N',
            }

            response = self._safe_request(
                'POST',
                url_emissao,
                delay_before=1.0,
                data=popup_data,
                timeout=self.timeout
            )

            # 5. Procurar URL do PDF no HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procurar script que abre o PDF
            scripts = soup.find_all('script')
            pdf_url = None

            for script in scripts:
                if script.string and 'window.open' in script.string:
                    # Extrair URL do window.open
                    match = re.search(r'window\.open\(["\']([^"\']+)["\']', script.string)
                    if match:
                        pdf_url = match.group(1)
                        break

            if not pdf_url:
                logger.error("❌ URL do PDF não encontrada")
                return None

            # 6. Baixar PDF (COM DELAY - simula aguardar geração)
            if not pdf_url.startswith('http'):
                pdf_url = f'{self.BASE_URL}/{pdf_url}'

            logger.debug(f"Baixando PDF: {pdf_url}")
            response = self._safe_request('GET', pdf_url, delay_before=0.6, timeout=self.timeout)

            if response.status_code == 200 and len(response.content) > 1000:
                logger.info(f"✅ PDF baixado: {len(response.content)} bytes")
                return response.content
            else:
                logger.error("❌ PDF inválido")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao emitir: {e}")
            import traceback
            traceback.print_exc()
            return None

    def salvar_pdf(self, pdf_bytes: bytes, cpf: str, consultor: str = "Danner", nome_cliente: str = None, mes: str = None) -> str:
        """
        Salva PDF em arquivo com formato igual ao Playwright.

        Formato do nome: NOME_CLIENTE_MES.pdf
        Exemplo: ADAO_JUNIOR_PEREIRA_DE_BRITO_DEZEMBRO.pdf

        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            cpf: CPF do cliente
            consultor: Nome da pasta do consultor (default: Danner)
            nome_cliente: Nome do cliente para o arquivo
            mes: Mês do boleto (ex: DEZEMBRO)

        Returns:
            Caminho completo do arquivo salvo
        """
        pasta = CanopusConfig.DOWNLOADS_DIR / consultor
        pasta.mkdir(parents=True, exist_ok=True)

        # Formatar nome do arquivo igual ao Playwright
        if nome_cliente and mes:
            # Limpar nome do cliente (remover caracteres especiais)
            import unicodedata
            nome_limpo = unicodedata.normalize('NFKD', nome_cliente)
            nome_limpo = nome_limpo.encode('ASCII', 'ignore').decode('ASCII')
            nome_limpo = ''.join(c if c.isalnum() or c in ' -_' else '' for c in nome_limpo)
            nome_limpo = nome_limpo.strip().upper().replace(' ', '_')

            # Formato: NOME_CLIENTE_MES.pdf
            nome_arquivo = f"{nome_limpo}_{mes.upper()}.pdf"
        else:
            # Fallback: usa CPF + timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cpf_limpo = re.sub(r'[^\d]', '', cpf)
            nome_arquivo = f"boleto_{cpf_limpo}_{timestamp}.pdf"

        arquivo = pasta / nome_arquivo

        with open(arquivo, 'wb') as f:
            f.write(pdf_bytes)

        tamanho_kb = len(pdf_bytes) / 1024
        logger.info(f"✅ Salvo: {arquivo.name} ({tamanho_kb:.1f} KB)")

        return str(arquivo)


if __name__ == '__main__':
    print("=" * 80)
    print("CANOPUS HTTP CLIENT - BASEADO EM MAPEAMENTO REAL")
    print("=" * 80)
    print("\nUse test_http_client.py para testar!")
