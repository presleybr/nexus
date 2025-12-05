"""
Cliente HTTP Puro para Canopus - Downloads Ultra-Rapidos
Baseado na engenharia reversa da API

Performance esperada: ~1-2 segundos por boleto
"""
import requests
import re
import logging
import os
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, parse_qs, urlparse
import time
import urllib3

# Suprimir warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CanopusHTTPPuro')


class CanopusHTTPPuro:
    """
    Cliente HTTP puro para Canopus.
    Replica o fluxo do navegador via requisicoes diretas.
    """

    BASE_URL = 'https://cnp3.consorciocanopus.com.br'

    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
        self.viewstate = ''
        self.viewstate_generator = ''
        self.event_validation = ''

        # Headers padrao (identicos ao Chrome real)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

        # Desabilitar verificacao SSL (o site tem certificado valido, mas evita problemas)
        self.session.verify = False

        # Configurar retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _extrair_campos_aspnet(self, html: str) -> dict:
        """Extrai campos hidden do ASP.NET (__VIEWSTATE, etc)"""
        soup = BeautifulSoup(html, 'html.parser')

        campos = {}

        # Campos ASP.NET comuns
        nomes = ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION',
                 '__VSTATE', '__VSIG', '__EVENTTARGET', '__EVENTARGUMENT',
                 '__LASTFOCUS', '__SCROLLPOSITIONX', '__SCROLLPOSITIONY',
                 '__VIEWSTATEENCRYPTED']

        for nome in nomes:
            campo = soup.find('input', {'name': nome})
            if campo:
                campos[nome] = campo.get('value', '')

        return campos

    def _extrair_application_key(self, html: str) -> str:
        """Extrai o applicationKey do HTML de resposta"""

        # Tentar diferentes padroes
        padroes = [
            r'applicationKey=([a-zA-Z0-9%\+/=\-_]+)',
            r"applicationKey['\"]?\s*[=:]\s*['\"]?([a-zA-Z0-9%\+/=\-_]+)",
            r'frmConCmImpressao\.aspx\?applicationKey=([a-zA-Z0-9%\+/=\-_]+)',
            r"window\.open\(['\"].*applicationKey=([a-zA-Z0-9%\+/=\-_]+)",
        ]

        for padrao in padroes:
            match = re.search(padrao, html)
            if match:
                return match.group(1)

        # Tentar via BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Procurar em scripts
        for script in soup.find_all('script'):
            if script.string and 'applicationKey' in str(script.string):
                match = re.search(r'applicationKey=([a-zA-Z0-9%\+/=\-_]+)', script.string)
                if match:
                    return match.group(1)

        # Procurar em links
        for link in soup.find_all('a', href=True):
            if 'applicationKey' in link['href']:
                match = re.search(r'applicationKey=([a-zA-Z0-9%\+/=\-_]+)', link['href'])
                if match:
                    return match.group(1)

        # Procurar em iframes
        for iframe in soup.find_all('iframe', src=True):
            if 'applicationKey' in iframe['src']:
                match = re.search(r'applicationKey=([a-zA-Z0-9%\+/=\-_]+)', iframe['src'])
                if match:
                    return match.group(1)

        return None

    def login(self, usuario: str, senha: str) -> bool:
        """
        Faz login no Canopus.
        Usuario deve ter 10 digitos (com zeros a esquerda).
        """
        usuario_formatado = str(usuario).strip().zfill(10)
        logger.info(f"Login: {usuario_formatado}")

        try:
            # 1. GET na pagina de login para pegar campos ASP.NET
            url_login = f"{self.BASE_URL}/WWW/frmCorCCCnsLogin.aspx"
            response = self.session.get(url_login, timeout=30)

            if response.status_code != 200:
                logger.error(f"Erro ao acessar pagina de login: {response.status_code}")
                return False

            campos = self._extrair_campos_aspnet(response.text)
            logger.info(f"Campos ASP.NET extraidos: {len(campos)}")

            # 2. POST do login
            dados_login = {
                **campos,
                'edtUsuario': usuario_formatado,
                'edtSenha': senha,
                '__EVENTTARGET': 'btnLogin',
                '__EVENTARGUMENT': '',
            }

            response = self.session.post(url_login, data=dados_login, timeout=30, allow_redirects=True)

            # 3. Verificar sucesso
            if 'frmMain.aspx' in response.url or 'Main' in response.text:
                logger.info("Login OK!")
                self.logged_in = True
                time.sleep(2.0)  # Delay pos-login anti-bot
                return True

            # Verificar se tem CAPTCHA
            if 'caracteres de seguranca' in response.text.lower():
                logger.error("CAPTCHA detectado - usar Playwright")
                return False

            # Verificar erro de senha
            if 'incorreta' in response.text.lower() or 'invalid' in response.text.lower():
                logger.error("Senha incorreta")
                return False

            logger.error("Login falhou - motivo desconhecido")
            logger.debug(f"URL final: {response.url}")
            return False

        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False

    def _navegar_atendimento(self) -> bool:
        """Navega para o menu de Atendimento"""
        logger.info("Navegando para Atendimento...")

        try:
            time.sleep(1.5)  # Delay anti-bot
            url = f"{self.BASE_URL}/WWW/frmMain.aspx"
            response = self.session.get(url, timeout=30)
            campos = self._extrair_campos_aspnet(response.text)

            time.sleep(1.0)  # Delay anti-bot

            # Clicar no icone de Atendimento
            dados = {
                **campos,
                'ctl00$img_Atendimento.x': '25',
                'ctl00$img_Atendimento.y': '25',
            }

            response = self.session.post(url, data=dados, timeout=30)

            if response.status_code == 200:
                logger.info("Menu Atendimento acessado")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro ao navegar: {e}")
            return False

    def buscar_cliente(self, cpf: str) -> dict:
        """
        Busca cliente por CPF.
        Retorna dict com CD_Grupo e CD_Cota se encontrado.
        """
        cpf_limpo = re.sub(r'[^\d]', '', cpf)
        cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

        logger.info(f"Buscando: {cpf_formatado}")

        try:
            # Navegar para atendimento primeiro
            self._navegar_atendimento()
            time.sleep(1.5)  # Delay anti-bot

            # Acessar pagina de busca
            url_busca = f"{self.BASE_URL}/WWW/CONAT/frmBuscaCota.aspx"
            response = self.session.get(url_busca, timeout=30)
            campos = self._extrair_campos_aspnet(response.text)

            time.sleep(1.0)  # Delay anti-bot

            # Selecionar CPF no dropdown (primeiro POST)
            dados_select = {
                **campos,
                '__EVENTTARGET': 'ctl00$Conteudo$cbxCriterioBusca',
                '__EVENTARGUMENT': '',
                'ctl00$Conteudo$cbxCriterioBusca': 'F',
                'ctl00$Conteudo$edtContextoBusca': '',
            }

            response = self.session.post(url_busca, data=dados_select, timeout=30)
            campos = self._extrair_campos_aspnet(response.text)
            time.sleep(1.0)  # Delay anti-bot

            # POST da busca
            dados_busca = {
                **campos,
                'ctl00$Conteudo$cbxCriterioBusca': 'F',
                'ctl00$Conteudo$edtContextoBusca': cpf_formatado,
                '__EVENTTARGET': 'ctl00$Conteudo$btnBuscar',
                '__EVENTARGUMENT': '',
            }

            response = self.session.post(url_busca, data=dados_busca, timeout=30)

            if response.status_code != 200:
                logger.error(f"Erro na busca: {response.status_code}")
                return None

            # Extrair CD_Grupo e CD_Cota do resultado
            soup = BeautifulSoup(response.text, 'html.parser')

            # Procurar link do cliente na tabela
            link = soup.find('a', href=re.compile(r'CD_Grupo=.*CD_Cota='))

            if link:
                href = link['href']
                match = re.search(r'CD_Grupo=(\d+)&CD_Cota=(\d+)', href)
                if match:
                    resultado = {
                        'cd_grupo': match.group(1),
                        'cd_cota': match.group(2),
                        'nome': link.text.strip() if link.text else 'Cliente'
                    }
                    logger.info(f"Cliente encontrado: Grupo {resultado['cd_grupo']}, Cota {resultado['cd_cota']}")
                    return resultado

            # Tentar outro padrao (lnkID_Documento)
            link = soup.find('a', id=re.compile(r'lnkID_Documento'))
            if link:
                # Clicar no link para ir para a pagina do cliente
                onclick = link.get('href', '')
                if 'CD_Grupo' in onclick:
                    match = re.search(r'CD_Grupo=(\d+).*CD_Cota=(\d+)', onclick)
                    if match:
                        resultado = {
                            'cd_grupo': match.group(1),
                            'cd_cota': match.group(2),
                            'nome': link.text.strip() if link.text else 'Cliente'
                        }
                        logger.info(f"Cliente encontrado: Grupo {resultado['cd_grupo']}, Cota {resultado['cd_cota']}")
                        return resultado

            logger.warning(f"Cliente nao encontrado: {cpf}")
            return None

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return None

    def acessar_cliente(self, cd_grupo: str, cd_cota: str) -> bool:
        """Acessa a pagina do cliente"""
        logger.info(f"Acessando cliente: Grupo {cd_grupo}, Cota {cd_cota}")

        try:
            time.sleep(1.5)  # Delay anti-bot
            url = f"{self.BASE_URL}/WWW/CONAT/frmConAtSrcConsorciado.aspx?CD_Grupo={cd_grupo}&CD_Cota={cd_cota}"
            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                logger.info("Cliente acessado")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro ao acessar cliente: {e}")
            return False

    def navegar_boletos(self) -> bool:
        """Navega para a pagina de boletos"""
        logger.info("Navegando para boletos...")

        try:
            time.sleep(1.5)  # Delay anti-bot
            url = f"{self.BASE_URL}/WWW/CONCO/frmConCoRelBoletoAvulso.aspx"
            response = self.session.get(url, timeout=30)

            if response.status_code == 200 and 'Boleto' in response.text:
                logger.info("Pagina de boletos acessada")
                return True

            return False

        except Exception as e:
            logger.error(f"Erro: {e}")
            return False

    def emitir_boleto(self, mes: str = None, ano: int = None) -> str:
        """
        Emite o boleto e retorna o applicationKey.
        """
        logger.info("Emitindo boleto...")

        try:
            time.sleep(1.0)  # Delay anti-bot
            url = f"{self.BASE_URL}/WWW/CONCO/frmConCoRelBoletoAvulso.aspx"
            response = self.session.get(url, timeout=30)
            campos = self._extrair_campos_aspnet(response.text)

            time.sleep(1.0)  # Delay anti-bot

            # 1. Selecionar o boleto (checkbox)
            dados = {
                **campos,
                'ctl00$Conteudo$rdlTipoEmissao': 'BA',
                'ctl00$Conteudo$grdBoleto_Avulso$ctl02$imgEmite_Boleto.x': '10',
                'ctl00$Conteudo$grdBoleto_Avulso$ctl02$imgEmite_Boleto.y': '10',
            }

            response = self.session.post(url, data=dados, timeout=30)
            campos = self._extrair_campos_aspnet(response.text)
            time.sleep(1.5)  # Delay anti-bot

            # 2. Clicar em Emitir
            dados = {
                **campos,
                '__EVENTTARGET': 'ctl00$Conteudo$btnEmitir',
                '__EVENTARGUMENT': '',
                'ctl00$Conteudo$rdlTipoEmissao': 'BA',
            }

            response = self.session.post(url, data=dados, timeout=30)

            # 3. Verificar popup / extrair applicationKey
            application_key = self._extrair_application_key(response.text)

            if not application_key:
                # Tentar clicar em VerificaPopUp
                campos = self._extrair_campos_aspnet(response.text)
                dados = {
                    **campos,
                    '__EVENTTARGET': 'ctl00$Conteudo$btnVerificaPopUp',
                    '__EVENTARGUMENT': '',
                    'ctl00$Conteudo$rdlTipoEmissao': 'BA',
                }
                response = self.session.post(url, data=dados, timeout=30)
                application_key = self._extrair_application_key(response.text)

            if application_key:
                logger.info(f"ApplicationKey obtido: {application_key[:30]}...")
                return application_key

            logger.error("Nao foi possivel obter applicationKey")
            # Salvar HTML para debug
            with open('/tmp/canopus_debug.html', 'w') as f:
                f.write(response.text)
            logger.info("HTML salvo em /tmp/canopus_debug.html para debug")
            return None

        except Exception as e:
            logger.error(f"Erro ao emitir: {e}")
            return None

    def baixar_pdf(self, application_key: str) -> bytes:
        """Baixa o PDF usando o applicationKey"""
        logger.info("Baixando PDF...")

        try:
            url = f"{self.BASE_URL}/WWW/CONCM/frmConCmImpressao.aspx?applicationKey={application_key}"

            response = self.session.get(url, timeout=60)

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')

                # Verificar se eh PDF
                if 'pdf' in content_type.lower() or response.content[:4] == b'%PDF':
                    logger.info(f"PDF baixado: {len(response.content)} bytes")
                    return response.content

                # Pode ser uma pagina que redireciona para o PDF
                # Tentar extrair URL do PDF do HTML
                if 'text/html' in content_type:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Procurar iframe ou embed com PDF
                    for tag in soup.find_all(['iframe', 'embed', 'object']):
                        src = tag.get('src') or tag.get('data')
                        if src and ('pdf' in src.lower() or 'applicationKey' in src):
                            pdf_url = urljoin(self.BASE_URL, src)
                            pdf_response = self.session.get(pdf_url, timeout=60)
                            if pdf_response.content[:4] == b'%PDF':
                                logger.info(f"PDF baixado via iframe: {len(pdf_response.content)} bytes")
                                return pdf_response.content

            logger.error(f"Falha ao baixar PDF: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Erro ao baixar PDF: {e}")
            return None

    def baixar_boleto_completo(self, cpf: str, pasta_destino: str, nome_cliente: str = None, mes: str = 'DEZEMBRO') -> dict:
        """
        Fluxo completo: busca cliente -> emite boleto -> baixa PDF -> salva arquivo
        """
        inicio = time.time()
        cpf_limpo = re.sub(r'[^\d]', '', cpf)

        try:
            # 1. Buscar cliente
            cliente = self.buscar_cliente(cpf)
            if not cliente:
                return {'sucesso': False, 'erro': 'Cliente nao encontrado'}

            # 2. Acessar cliente
            if not self.acessar_cliente(cliente['cd_grupo'], cliente['cd_cota']):
                return {'sucesso': False, 'erro': 'Falha ao acessar cliente'}

            # 3. Navegar para boletos
            if not self.navegar_boletos():
                return {'sucesso': False, 'erro': 'Falha ao acessar boletos'}

            # 4. Emitir boleto
            app_key = self.emitir_boleto()
            if not app_key:
                return {'sucesso': False, 'erro': 'Falha ao emitir boleto'}

            # 5. Baixar PDF
            pdf_bytes = self.baixar_pdf(app_key)
            if not pdf_bytes:
                return {'sucesso': False, 'erro': 'Falha ao baixar PDF'}

            # 6. Salvar arquivo
            nome = nome_cliente or cliente.get('nome', 'CLIENTE')
            nome_arquivo = self._formatar_nome_arquivo(nome, mes)

            os.makedirs(pasta_destino, exist_ok=True)
            caminho = os.path.join(pasta_destino, nome_arquivo)

            with open(caminho, 'wb') as f:
                f.write(pdf_bytes)

            tempo = time.time() - inicio
            logger.info(f"Boleto salvo: {nome_arquivo} ({tempo:.1f}s)")

            return {
                'sucesso': True,
                'nome_arquivo': nome_arquivo,
                'caminho': caminho,
                'tamanho': len(pdf_bytes),
                'tempo': tempo
            }

        except Exception as e:
            logger.error(f"Erro no fluxo: {e}")
            return {'sucesso': False, 'erro': str(e)}

    def _formatar_nome_arquivo(self, nome: str, mes: str) -> str:
        """Formata nome do arquivo"""
        import unicodedata
        nome_limpo = unicodedata.normalize('NFKD', nome)
        nome_limpo = nome_limpo.encode('ASCII', 'ignore').decode('ASCII')
        nome_limpo = re.sub(r'[^\w\s-]', '', nome_limpo)
        nome_limpo = nome_limpo.strip().upper().replace(' ', '_')
        return f"{nome_limpo}_{mes.upper()}.pdf"


# Funcao para processar multiplos clientes
def processar_lote_http(clientes: list, usuario: str, senha: str, pasta_destino: str, mes: str = 'DEZEMBRO'):
    """
    Processa um lote de clientes via HTTP puro.

    Parametros:
        clientes: Lista de dicts com 'cpf' e 'nome'
        usuario: PV do Canopus
        senha: Senha
        pasta_destino: Onde salvar os PDFs
        mes: Mes de referencia
    """
    logger.info(f"Processando {len(clientes)} clientes via HTTP Puro")

    cliente_http = CanopusHTTPPuro()

    # Login
    if not cliente_http.login(usuario, senha):
        logger.error("Falha no login - abortando")
        return {'erro': 'Falha no login'}

    resultados = {
        'total': len(clientes),
        'sucesso': 0,
        'erro': 0,
        'detalhes': []
    }

    for i, cliente in enumerate(clientes, 1):
        cpf = cliente.get('cpf', '')
        nome = cliente.get('nome', 'CLIENTE')

        logger.info(f"\n{'='*50}")
        logger.info(f"Cliente {i}/{len(clientes)}: {nome}")
        logger.info(f"   CPF: {cpf}")

        resultado = cliente_http.baixar_boleto_completo(
            cpf=cpf,
            pasta_destino=pasta_destino,
            nome_cliente=nome,
            mes=mes
        )

        if resultado['sucesso']:
            resultados['sucesso'] += 1
        else:
            resultados['erro'] += 1

        resultados['detalhes'].append({
            'cpf': cpf,
            'nome': nome,
            **resultado
        })

    logger.info(f"\n{'='*50}")
    logger.info(f"RESUMO: {resultados['sucesso']}/{resultados['total']} sucesso")

    return resultados


# Teste rapido
if __name__ == '__main__':
    import sys

    usuario = sys.argv[1] if len(sys.argv) > 1 else '17308'
    senha = sys.argv[2] if len(sys.argv) > 2 else 'SUA_SENHA'
    cpf = sys.argv[3] if len(sys.argv) > 3 else '50516798898'

    cliente = CanopusHTTPPuro()

    if cliente.login(usuario, senha):
        resultado = cliente.baixar_boleto_completo(
            cpf=cpf,
            pasta_destino='./downloads',
            mes='JANEIRO'
        )
        print(f"\nResultado: {resultado}")
    else:
        print("Falha no login")
