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

from config import CanopusConfig

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

        # Headers idênticos ao navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })

        self.session.verify = False  # SSL pode dar problema
        self.timeout = timeout
        self._logged_in = False

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
            # Formatar usuário com zeros à esquerda (total 10 dígitos)
            usuario_formatado = usuario.zfill(10)
            logger.info(f"🔐 Login: {usuario} → {usuario_formatado}")

            # 1. GET na página de login
            url_login = f'{self.BASE_URL}/frmCorCCCnsLogin.aspx'
            logger.debug(f"GET {url_login}")

            response = self.session.get(url_login, timeout=self.timeout)
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
                'edtUsuario': usuario_formatado,  # Com zeros: 0000024627
                'edtSenha': senha,
                'hdnTokenRecaptcha': '',
                'as_fid': '',  # Gerado automaticamente
            }

            # 4. POST login
            logger.debug("POST login...")
            response = self.session.post(
                url_login,
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )

            # 5. Verificar sucesso
            # Se redirecionou para frmMain.aspx = sucesso
            if 'frmMain.aspx' in response.url or response.status_code == 200:
                # Verificar se tem ValidaSessaoLogin
                if 'ValidaSessaoLogin' in response.text or 'frmMain' in response.text:
                    self._logged_in = True
                    logger.info("✅ Login OK!")
                    return True

            logger.error("❌ Login falhou")
            logger.debug(f"URL final: {response.url}")
            logger.debug(f"Status: {response.status_code}")

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
            response = self.session.get(url_main, timeout=self.timeout)

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

            response = self.session.post(
                url_main,
                data=atendimento_data,
                timeout=self.timeout,
                allow_redirects=True
            )

            # 2. Acessar frmBuscaCota.aspx
            url_busca = f'{self.BASE_URL}/CONAT/frmBuscaCota.aspx'
            response = self.session.get(url_busca, timeout=self.timeout)

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

            response = self.session.post(
                url_busca,
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
            response = self.session.post(
                url_busca,
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

            # Pegar página atual
            response = self.session.get(url_busca, timeout=self.timeout)
            asp_fields = self._extract_asp_fields(response.text)

            # Extrair CPF da busca anterior (campo pode estar preenchido)
            soup = BeautifulSoup(response.text, 'html.parser')
            cpf_field = soup.find('input', {'id': 'ctl00_Conteudo_edtContextoBusca'})
            cpf_valor = cpf_field.get('value', '') if cpf_field else ''

            # Clicar no link
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

            response = self.session.post(
                url_busca,
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

            # 1. Acessar página de emissão
            url_emissao = f'{self.BASE_URL}/CONCO/frmConCoRelBoletoAvulso.aspx'
            response = self.session.get(url_emissao, timeout=self.timeout)

            asp_fields = self._extract_asp_fields(response.text)

            # 2. Clicar no checkbox do boleto (ctl03)
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

            response = self.session.post(
                url_emissao,
                data=checkbox_data,
                timeout=self.timeout
            )

            # 3. Clicar em "Emitir" (btnEmitir)
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

            response = self.session.post(
                url_emissao,
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

            response = self.session.post(
                url_emissao,
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

            # 6. Baixar PDF
            if not pdf_url.startswith('http'):
                pdf_url = f'{self.BASE_URL}/{pdf_url}'

            logger.debug(f"Baixando PDF: {pdf_url}")
            response = self.session.get(pdf_url, timeout=self.timeout)

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

    def salvar_pdf(self, pdf_bytes: bytes, cpf: str, consultor: str = "Danner") -> str:
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


if __name__ == '__main__':
    print("=" * 80)
    print("CANOPUS HTTP CLIENT - BASEADO EM MAPEAMENTO REAL")
    print("=" * 80)
    print("\nUse test_http_client.py para testar!")
