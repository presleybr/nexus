"""
Script para descobrir a API real do Canopus
Intercepta todas as requisicoes durante o download de um boleto
"""
import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CapturarAPI')


class CapturadorAPICanopus:
    """Captura todas as requisicoes HTTP durante o fluxo de download"""

    BASE_URL = 'https://cnp3.consorciocanopus.com.br/WWW'

    def __init__(self):
        self.requisicoes = []
        self.respostas = []
        self.pdfs_encontrados = []
        self.playwright = None
        self.browser = None
        self.page = None

    async def iniciar(self, headless: bool = False):
        """Inicia navegador com interceptacao"""
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=headless,  # False para VER o que esta acontecendo
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )

        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        )

        self.page = await context.new_page()

        # Tentar aplicar stealth
        try:
            from playwright_stealth import stealth_async
            await stealth_async(self.page)
            logger.info("Stealth aplicado")
        except ImportError:
            logger.warning("playwright_stealth nao instalado, continuando sem stealth")

        # INTERCEPTAR TODAS AS REQUISICOES
        self.page.on('request', self._capturar_request)
        self.page.on('response', self._capturar_response)

        logger.info("Navegador iniciado com interceptacao ativa")

    def _capturar_request(self, request):
        """Captura cada requisicao"""
        dados = {
            'timestamp': datetime.now().isoformat(),
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
            'post_data': request.post_data,
            'resource_type': request.resource_type,
        }
        self.requisicoes.append(dados)

        # Log para requisicoes importantes
        url_lower = request.url.lower()
        if any(x in url_lower for x in ['boleto', 'pdf', 'download', 'cobranca', 'gerar', 'busca', 'cota', 'avulso', 'emissao']):
            logger.info(f">>> {request.method} {request.url[:100]}")
            if request.post_data:
                # Mostrar campos importantes do payload
                post = request.post_data
                if '__EVENTTARGET' in post:
                    import re
                    target = re.search(r'__EVENTTARGET=([^&]*)', post)
                    if target:
                        logger.info(f"    __EVENTTARGET: {target.group(1)}")

    async def _capturar_response(self, response):
        """Captura cada resposta"""
        content_type = response.headers.get('content-type', '')

        dados = {
            'timestamp': datetime.now().isoformat(),
            'url': response.url,
            'status': response.status,
            'headers': dict(response.headers),
            'content_type': content_type,
        }

        # Se for PDF, capturar!
        if 'pdf' in content_type.lower() or 'octet-stream' in content_type.lower():
            logger.info(f"PDF ENCONTRADO!")
            logger.info(f"   URL: {response.url}")
            logger.info(f"   Status: {response.status}")
            logger.info(f"   Content-Type: {content_type}")

            # Tentar pegar o body
            try:
                body = await response.body()
                dados['body_size'] = len(body)
                dados['is_pdf'] = body[:4] == b'%PDF'

                if dados['is_pdf']:
                    logger.info(f"   CONFIRMADO: PDF valido ({len(body)} bytes)")
                    self.pdfs_encontrados.append(dados)
            except:
                pass

        self.respostas.append(dados)

    async def login(self, usuario: str, senha: str, codigo_empresa: str = '0101'):
        """Faz login no Canopus - IGUAL AO PLAYWRIGHT QUE FUNCIONA"""
        logger.info(f"Fazendo login: {usuario}")

        # Formatar usuario com zeros a esquerda (10 digitos)
        usuario_formatado = str(usuario).strip().zfill(10)

        # 1. Acessar pagina de login
        await self.page.goto(f'{self.BASE_URL}/frmCorCCCnsLogin.aspx')
        await asyncio.sleep(2)

        # 2. Preencher usuario
        campo_usuario = await self.page.query_selector('#edtUsuario')
        if campo_usuario:
            await campo_usuario.fill(usuario_formatado)
            logger.info(f"   Usuario preenchido: {usuario_formatado}")
        else:
            logger.error("Campo usuario nao encontrado!")
            return False

        await asyncio.sleep(0.5)

        # 3. Preencher senha
        campo_senha = await self.page.query_selector('#edtSenha')
        if campo_senha:
            await campo_senha.fill(senha)
            logger.info(f"   Senha preenchida: {'*' * len(senha)}")
        else:
            logger.error("Campo senha nao encontrado!")
            return False

        await asyncio.sleep(0.5)

        # 4. Clicar no botao login
        btn_login = await self.page.query_selector('#btnLogin')
        if btn_login:
            await btn_login.click()
            logger.info("   Clicou em Login")
        else:
            logger.error("Botao login nao encontrado!")
            return False

        await asyncio.sleep(3)

        # 5. Verificar sucesso
        url_atual = self.page.url
        if 'frmMain.aspx' in url_atual:
            logger.info("Login OK!")
            return True
        else:
            logger.error(f"Login falhou. URL: {url_atual}")
            return False

    async def navegar_para_atendimento(self):
        """Navega para o menu de Atendimento e clica em Busca Avançada"""
        logger.info("Navegando para Atendimento...")

        # Clicar no menu Atendimento
        img_atendimento = await self.page.query_selector('#ctl00_img_Atendimento')
        if img_atendimento:
            await img_atendimento.click()
            logger.info("   Clicou em Atendimento")
            await asyncio.sleep(2)
        else:
            # Tentar clicar por coordenadas ou outro seletor
            try:
                await self.page.click('img[id*="Atendimento"]')
                await asyncio.sleep(2)
            except:
                logger.error("Menu Atendimento nao encontrado!")
                return False

        # Clicar em Busca Avançada
        btn_busca_avancada = '#ctl00_Conteudo_btnBuscaAvancada'
        try:
            await self.page.wait_for_selector(btn_busca_avancada, timeout=10000)
            await self.page.click(btn_busca_avancada)
            logger.info("   Clicou em Busca Avancada")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"   Busca Avancada nao encontrada: {e}")
            # Tirar screenshot para debug
            await self.page.screenshot(path='debug_atendimento.png')
            return True  # Continuar mesmo assim

    async def buscar_cliente(self, cpf: str):
        """Busca um cliente por CPF na tela de busca"""
        logger.info(f"Buscando CPF: {cpf}")

        # Formatar CPF
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

        # Aguardar o dropdown de tipo de busca aparecer (já estamos na busca avançada)
        select_tipo = '#ctl00_Conteudo_cbxCriterioBusca'

        # Selecionar tipo de busca = CPF (F)
        try:
            await self.page.wait_for_selector(select_tipo, timeout=30000)
            await self.page.select_option(select_tipo, 'F')
            logger.info("   Selecionou CPF como criterio")
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"   Erro ao selecionar criterio: {e}")
            await self.page.screenshot(path='debug_select_cpf.png')

        # Preencher CPF
        campo_busca = await self.page.query_selector('#ctl00_Conteudo_edtContextoBusca')
        if campo_busca:
            await campo_busca.fill(cpf_formatado)
            logger.info(f"   CPF preenchido: {cpf_formatado}")
        else:
            logger.error("Campo busca nao encontrado!")
            return False

        await asyncio.sleep(0.5)

        # Clicar buscar
        btn_buscar = await self.page.query_selector('#ctl00_Conteudo_btnBuscar')
        if btn_buscar:
            await btn_buscar.click()
            logger.info("   Clicou em Buscar")
        else:
            logger.error("Botao buscar nao encontrado!")
            return False

        await asyncio.sleep(3)

        # Verificar se encontrou resultados (seletor correto do Playwright)
        resultado = await self.page.query_selector('a[id*="grdBuscaAvancada"][id*="lnkID_Documento"]')
        if resultado:
            logger.info("Cliente encontrado!")
            return True
        else:
            logger.warning("Cliente nao encontrado na busca")
            # Tirar screenshot para debug
            await self.page.screenshot(path='debug_busca.png')
            logger.info("Screenshot salvo em debug_busca.png")
            return False

    async def acessar_cliente(self):
        """Clica no cliente encontrado"""
        logger.info("Acessando cliente...")

        # Clicar no primeiro resultado da grid (seletor correto do Playwright)
        links = await self.page.query_selector_all('a[id*="grdBuscaAvancada"][id*="lnkID_Documento"]')

        if links and len(links) > 0:
            # Pegar o segundo link (ctl03) que geralmente e o correto
            link = links[1] if len(links) > 1 else links[0]
            await link.click()
            logger.info("   Clicou no cliente")
            await asyncio.sleep(3)
            return True
        else:
            logger.error("Nenhum link de cliente encontrado!")
            return False

    async def navegar_para_boletos(self):
        """Navega ate a pagina de emissao de boletos via menu"""
        logger.info("Navegando para emissao de cobranca...")

        # Clicar no link "Emissão de Cobrança" no menu do cliente
        menu_emissao = '#ctl00_Conteudo_Menu_CONAT_grdMenu_CONAT_ctl05_hlkFormulario'

        try:
            await self.page.wait_for_selector(menu_emissao, timeout=10000)
            await self.page.click(menu_emissao)
            logger.info("   Clicou em Emissao de Cobranca")
            await asyncio.sleep(3)
            return True
        except Exception as e:
            logger.warning(f"   Menu Emissao nao encontrado: {e}")
            # Tentar URL direta como fallback
            await self.page.goto(f'{self.BASE_URL}/CONCO/frmConCoRelBoletoAvulso.aspx')
            await asyncio.sleep(3)
            return True

    async def baixar_boleto(self):
        """Tenta baixar o boleto - AQUI VAMOS CAPTURAR A REQUISICAO"""
        logger.info("Tentando baixar boleto...")

        # Marcar quantas requisicoes temos antes
        qtd_antes = len(self.requisicoes)

        # 1. Clicar no checkbox do boleto
        try:
            checkbox = await self.page.query_selector('input[id*="imgEmite_Boleto"]')
            if checkbox:
                await checkbox.click()
                logger.info("   Clicou no checkbox do boleto")
                await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"   Checkbox nao encontrado: {e}")

        # 2. Clicar no botao Emitir
        try:
            btn_emitir = await self.page.query_selector('#ctl00_Conteudo_btnEmitir')
            if btn_emitir:
                await btn_emitir.click()
                logger.info("   Clicou em Emitir")
                await asyncio.sleep(3)
        except Exception as e:
            logger.warning(f"   Botao Emitir nao encontrado: {e}")

        # 3. Verificar popup
        try:
            btn_popup = await self.page.query_selector('#ctl00_Conteudo_btnVerificaPopUp')
            if btn_popup:
                await btn_popup.click()
                logger.info("   Clicou em VerificaPopUp")
                await asyncio.sleep(3)
        except:
            pass

        # Ver quantas requisicoes novas
        qtd_depois = len(self.requisicoes)
        novas = qtd_depois - qtd_antes

        logger.info(f"{novas} novas requisicoes capturadas durante o download")

        # Aguardar mais um pouco para capturar o PDF
        await asyncio.sleep(5)

    def salvar_capturas(self, arquivo: str = 'capturas_canopus.json'):
        """Salva todas as capturas em JSON"""
        dados = {
            'timestamp': datetime.now().isoformat(),
            'total_requisicoes': len(self.requisicoes),
            'total_respostas': len(self.respostas),
            'pdfs_encontrados': self.pdfs_encontrados,
            'requisicoes_relevantes': [
                r for r in self.requisicoes
                if any(x in r['url'].lower() for x in ['boleto', 'pdf', 'download', 'cobranca', 'gerar', 'avulso', 'emissao', 'report'])
            ],
            'todas_requisicoes': self.requisicoes,
        }

        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)

        logger.info(f"Salvo em: {arquivo}")

        # Resumo
        print(f"\n{'='*60}")
        print("RESUMO DA CAPTURA")
        print(f"{'='*60}")
        print(f"Total de requisicoes: {len(self.requisicoes)}")
        print(f"PDFs encontrados: {len(self.pdfs_encontrados)}")

        if self.pdfs_encontrados:
            print(f"\nURLs DOS PDFs:")
            for pdf in self.pdfs_encontrados:
                print(f"   {pdf['url']}")

        # Mostrar requisicoes POST relevantes
        posts_relevantes = [
            r for r in self.requisicoes
            if r['method'] == 'POST' and any(x in r['url'].lower() for x in ['boleto', 'cobranca', 'gerar', 'avulso', 'emissao'])
        ]

        if posts_relevantes:
            print(f"\nREQUISICOES POST RELEVANTES:")
            for req in posts_relevantes[-5:]:  # Ultimas 5
                print(f"\n   URL: {req['url']}")
                if req['post_data']:
                    # Extrair campos importantes
                    post = req['post_data']
                    if '__EVENTTARGET' in post:
                        import re
                        target = re.search(r'__EVENTTARGET=([^&]*)', post)
                        if target:
                            print(f"   __EVENTTARGET: {target.group(1)}")

        print(f"\n{'='*60}")

    async def fechar(self):
        """Fecha o navegador"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def executar_captura(usuario: str, senha: str, cpf_teste: str, headless: bool = False):
    """Executa o fluxo completo de captura"""
    capturador = CapturadorAPICanopus()

    try:
        await capturador.iniciar(headless=headless)

        # Login
        login_ok = await capturador.login(usuario, senha)
        if not login_ok:
            logger.error("Falha no login, abortando")
            capturador.salvar_capturas('capturas_canopus_login_falhou.json')
            return

        # Navegar para atendimento
        await capturador.navegar_para_atendimento()

        # Buscar cliente
        encontrou = await capturador.buscar_cliente(cpf_teste)
        if not encontrou:
            logger.error("Cliente nao encontrado")
            # Salvar capturas parciais antes de abortar
            capturador.salvar_capturas('capturas_canopus_parcial.json')
            return

        # Acessar cliente
        await capturador.acessar_cliente()

        # Navegar para boletos
        await capturador.navegar_para_boletos()

        # Baixar boleto (captura a requisicao)
        await capturador.baixar_boleto()

        # Esperar um pouco para capturar tudo
        await asyncio.sleep(3)

        # Salvar capturas
        capturador.salvar_capturas()

    except Exception as e:
        logger.error(f"Erro durante captura: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await capturador.fechar()


# Para rodar diretamente
if __name__ == '__main__':
    import sys

    # Pegar credenciais dos argumentos ou usar padrao
    usuario = sys.argv[1] if len(sys.argv) > 1 else '24627'
    senha = sys.argv[2] if len(sys.argv) > 2 else 'DIGITE_A_SENHA'
    cpf_teste = sys.argv[3] if len(sys.argv) > 3 else '50516798898'

    print(f"""
{'='*60}
        CAPTURADOR DE API - CANOPUS
{'='*60}

Este script vai:
  1. Fazer login no Canopus
  2. Navegar ate um cliente
  3. Baixar um boleto
  4. CAPTURAR todas as requisicoes HTTP
  5. Salvar em capturas_canopus.json

Usuario: {usuario}
CPF teste: {cpf_teste}

{'='*60}
    """)

    asyncio.run(executar_captura(usuario, senha, cpf_teste, headless=False))
