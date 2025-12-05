"""
Canopus Hibrido - Playwright + JavaScript Console
=================================================
Combina login via Playwright com downloads via script JS injetado.
Resultado: Downloads 10-20x mais rapidos!

Fluxo:
1. Playwright abre navegador e faz login
2. Apos login, injeta script JavaScript
3. Script JS faz fetch() das paginas usando sessao autenticada
4. Downloads sao capturados pelo Playwright
5. Arquivos salvos na pasta de destino
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Configurar logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class CanopusHibrido:
    """
    Automacao hibrida: Playwright para login + JavaScript para downloads rapidos.
    """

    BASE_URL = 'https://cnp3.consorciocanopus.com.br'

    def __init__(self, usuario: str, senha: str, headless: bool = True):
        self.usuario = str(usuario).strip().zfill(10)  # Formatado com zeros
        self.senha = senha
        self.headless = headless
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.downloads_capturados = []
        self.pasta_downloads = None

    async def iniciar(self, pasta_downloads: str = None):
        """Inicia o navegador e faz login."""
        self.pasta_downloads = pasta_downloads or f"/tmp/boletos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.pasta_downloads, exist_ok=True)

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )

        # Configurar captura de downloads
        self.context.on('download', self._handle_download)

        self.page = await self.context.new_page()

        # Tentar aplicar stealth
        try:
            from playwright_stealth import stealth_async
            await stealth_async(self.page)
            logger.info("Stealth aplicado")
        except ImportError:
            logger.warning("playwright_stealth nao instalado")

        # Fazer login
        logou = await self._fazer_login()
        if not logou:
            raise Exception("Falha no login do Canopus")

        logger.info("Login realizado com sucesso!")
        return True

    async def _handle_download(self, download):
        """Callback para capturar downloads."""
        try:
            nome_sugerido = download.suggested_filename
            caminho = os.path.join(self.pasta_downloads, nome_sugerido)
            await download.save_as(caminho)
            tamanho = os.path.getsize(caminho)
            self.downloads_capturados.append({
                'arquivo': nome_sugerido,
                'caminho': caminho,
                'tamanho': tamanho
            })
            logger.info(f"Download capturado: {nome_sugerido} ({tamanho/1024:.1f} KB)")
        except Exception as e:
            logger.error(f"Erro ao salvar download: {e}")

    async def _fazer_login(self) -> bool:
        """Faz login no Canopus via Playwright."""
        try:
            logger.info(f"Fazendo login: {self.usuario}")

            await self.page.goto(f'{self.BASE_URL}/WWW/frmCorCCCnsLogin.aspx')
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(1)

            # Preencher credenciais
            await self.page.fill('#edtUsuario', self.usuario)
            await asyncio.sleep(0.3)
            await self.page.fill('#edtSenha', self.senha)
            await asyncio.sleep(0.3)

            # Clicar em Login
            await self.page.click('#btnLogin')
            await asyncio.sleep(2)

            # Verificar se logou (procurar elemento do menu)
            try:
                await self.page.wait_for_selector('#ctl00_img_Atendimento', timeout=10000)
                return True
            except:
                # Verificar URL
                if 'frmMain.aspx' in self.page.url:
                    return True

                # Tentar detectar erro de login
                try:
                    erro = await self.page.query_selector('.erro, .mensagem-erro, #lblMensagem')
                    if erro:
                        texto = await erro.text_content()
                        logger.error(f"Erro no login: {texto}")
                except:
                    pass

                logger.error(f"Login falhou. URL atual: {self.page.url}")
                return False

        except Exception as e:
            logger.error(f"Erro durante login: {e}")
            return False

    async def processar_clientes(self, clientes: list, mes: str = 'JANEIRO', ano: int = 2026) -> dict:
        """
        Processa lista de clientes injetando script JavaScript.

        Args:
            clientes: Lista de dicts com 'cpf' e 'nome'
            mes: Mes de referencia
            ano: Ano de referencia

        Returns:
            Dict com resultados do processamento
        """

        # Preparar lista de CPFs para o script
        clientes_js = []
        for c in clientes:
            cpf = ''.join(filter(str.isdigit, str(c.get('cpf', ''))))
            nome = c.get('nome', 'CLIENTE')
            if cpf and len(cpf) == 11:
                clientes_js.append({'cpf': cpf, 'nome': nome})

        if not clientes_js:
            return {'sucesso': False, 'erro': 'Nenhum cliente valido'}

        logger.info(f"Iniciando processamento de {len(clientes_js)} clientes via JS Console")

        # Gerar o script JavaScript
        script = self._gerar_script_js(clientes_js, mes, ano)

        # Injetar e executar o script
        try:
            resultado = await self.page.evaluate(script)

            # Aguardar downloads completarem
            await asyncio.sleep(3)

            return {
                'sucesso': True,
                'total': len(clientes_js),
                'resultado_js': resultado,
                'downloads': self.downloads_capturados,
                'pasta': self.pasta_downloads
            }

        except Exception as e:
            logger.error(f"Erro ao executar script JS: {e}")
            return {'sucesso': False, 'erro': str(e)}

    def _gerar_script_js(self, clientes: list, mes: str, ano: int) -> str:
        """Gera o script JavaScript para injetar no console."""

        clientes_json = json.dumps(clientes, ensure_ascii=False)

        script = f'''
(async function() {{
    const CONFIG = {{
        clientes: {clientes_json},
        mes: '{mes}',
        ano: {ano},
        delayEntreClientes: 800,
        delayEntreAcoes: 400
    }};

    const delay = ms => new Promise(r => setTimeout(r, ms));

    const formatarCPF = cpf => {{
        const n = cpf.replace(/\\D/g, '');
        return `${{n.slice(0,3)}}.${{n.slice(3,6)}}.${{n.slice(6,9)}}-${{n.slice(9)}}`;
    }};

    const formatarNomeArquivo = (nome, mes) => {{
        return nome
            .normalize('NFD')
            .replace(/[\\u0300-\\u036f]/g, '')
            .toUpperCase()
            .replace(/[^A-Z0-9\\s]/g, '')
            .trim()
            .replace(/\\s+/g, '_') + '_' + mes.toUpperCase() + '.pdf';
    }};

    const extrairCamposASP = (html) => {{
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const campos = {{}};
        doc.querySelectorAll('input[type="hidden"]').forEach(el => {{
            if (el.name) campos[el.name] = el.value || '';
        }});
        return campos;
    }};

    const navegarAtendimento = async () => {{
        try {{
            const urlMain = '/WWW/frmMain.aspx';
            let resp = await fetch(urlMain, {{ credentials: 'include' }});
            let html = await resp.text();
            let campos = extrairCamposASP(html);

            const form = new URLSearchParams();
            Object.entries(campos).forEach(([k, v]) => form.append(k, v));
            form.set('ctl00$img_Atendimento.x', '25');
            form.set('ctl00$img_Atendimento.y', '25');

            resp = await fetch(urlMain, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: form.toString(),
                credentials: 'include'
            }});

            return resp.ok;
        }} catch (e) {{
            console.error('Erro ao navegar atendimento:', e);
            return false;
        }}
    }};

    const buscarCliente = async (cpf) => {{
        try {{
            const urlBusca = '/WWW/CONAT/frmBuscaCota.aspx';
            let resp = await fetch(urlBusca, {{ credentials: 'include' }});
            let html = await resp.text();
            let campos = extrairCamposASP(html);

            // Selecionar CPF no dropdown
            let form = new URLSearchParams();
            Object.entries(campos).forEach(([k, v]) => form.append(k, v));
            form.set('ctl00$Conteudo$cbxCriterioBusca', 'F');
            form.set('ctl00$Conteudo$edtContextoBusca', '');
            form.set('__EVENTTARGET', 'ctl00$Conteudo$cbxCriterioBusca');
            form.set('__EVENTARGUMENT', '');

            resp = await fetch(urlBusca, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: form.toString(),
                credentials: 'include'
            }});
            html = await resp.text();
            campos = extrairCamposASP(html);

            await delay(CONFIG.delayEntreAcoes);

            // Buscar CPF
            form = new URLSearchParams();
            Object.entries(campos).forEach(([k, v]) => form.append(k, v));
            form.set('ctl00$Conteudo$cbxCriterioBusca', 'F');
            form.set('ctl00$Conteudo$edtContextoBusca', formatarCPF(cpf));
            form.set('__EVENTTARGET', 'ctl00$Conteudo$btnBuscar');
            form.set('__EVENTARGUMENT', '');

            resp = await fetch(urlBusca, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: form.toString(),
                credentials: 'include'
            }});
            html = await resp.text();

            const mGrupo = html.match(/CD_Grupo=(\\d+)/);
            const mCota = html.match(/CD_Cota=(\\d+)/);

            if (mGrupo && mCota) {{
                return {{ ok: true, grupo: mGrupo[1], cota: mCota[1] }};
            }}
            return {{ ok: false, erro: 'Cliente nao encontrado' }};
        }} catch (e) {{
            return {{ ok: false, erro: e.message }};
        }}
    }};

    const acessarCliente = async (grupo, cota) => {{
        try {{
            const url = `/WWW/CONAT/frmConAtSrcConsorciado.aspx?CD_Grupo=${{grupo}}&CD_Cota=${{cota}}`;
            const resp = await fetch(url, {{ credentials: 'include' }});
            return resp.ok;
        }} catch (e) {{
            return false;
        }}
    }};

    const baixarBoleto = async (nomeCliente) => {{
        try {{
            const urlBoleto = '/WWW/CONCO/frmConCoRelBoletoAvulso.aspx';

            let resp = await fetch(urlBoleto, {{ credentials: 'include' }});
            let html = await resp.text();
            let campos = extrairCamposASP(html);

            // Selecionar boleto (checkbox)
            let form = new URLSearchParams();
            Object.entries(campos).forEach(([k, v]) => form.append(k, v));
            form.set('ctl00$Conteudo$rdlTipoEmissao', 'BA');
            form.set('ctl00$Conteudo$grdBoleto_Avulso$ctl02$imgEmite_Boleto.x', '10');
            form.set('ctl00$Conteudo$grdBoleto_Avulso$ctl02$imgEmite_Boleto.y', '10');

            resp = await fetch(urlBoleto, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: form.toString(),
                credentials: 'include'
            }});
            html = await resp.text();
            campos = extrairCamposASP(html);

            await delay(CONFIG.delayEntreAcoes);

            // Emitir
            form = new URLSearchParams();
            Object.entries(campos).forEach(([k, v]) => form.append(k, v));
            form.set('__EVENTTARGET', 'ctl00$Conteudo$btnEmitir');
            form.set('__EVENTARGUMENT', '');
            form.set('ctl00$Conteudo$rdlTipoEmissao', 'BA');

            resp = await fetch(urlBoleto, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: form.toString(),
                credentials: 'include'
            }});
            html = await resp.text();

            let matchKey = html.match(/applicationKey=([a-zA-Z0-9%\\+\\/=\\-_]+)/);

            if (!matchKey) {{
                // Tentar VerificaPopUp
                campos = extrairCamposASP(html);
                form = new URLSearchParams();
                Object.entries(campos).forEach(([k, v]) => form.append(k, v));
                form.set('__EVENTTARGET', 'ctl00$Conteudo$btnVerificaPopUp');
                form.set('__EVENTARGUMENT', '');
                form.set('ctl00$Conteudo$rdlTipoEmissao', 'BA');

                resp = await fetch(urlBoleto, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                    body: form.toString(),
                    credentials: 'include'
                }});
                html = await resp.text();
                matchKey = html.match(/applicationKey=([a-zA-Z0-9%\\+\\/=\\-_]+)/);
            }}

            if (!matchKey) {{
                return {{ ok: false, erro: 'applicationKey nao encontrado' }};
            }}

            // Baixar PDF
            const urlPDF = `/WWW/CONCM/frmConCmImpressao.aspx?applicationKey=${{matchKey[1]}}`;
            resp = await fetch(urlPDF, {{ credentials: 'include' }});

            if (!resp.ok) {{
                return {{ ok: false, erro: `HTTP ${{resp.status}}` }};
            }}

            const blob = await resp.blob();

            if (!blob.type.includes('pdf') && blob.size < 1000) {{
                return {{ ok: false, erro: 'Resposta nao eh PDF' }};
            }}

            // Disparar download (Playwright vai capturar)
            const nomeArquivo = formatarNomeArquivo(nomeCliente, CONFIG.mes);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = nomeArquivo;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            return {{ ok: true, arquivo: nomeArquivo, tamanho: blob.size }};
        }} catch (e) {{
            return {{ ok: false, erro: e.message }};
        }}
    }};

    // PROCESSAR TODOS
    const total = CONFIG.clientes.length;
    let sucesso = 0;
    let erro = 0;
    const erros = [];
    const downloads = [];

    console.log(`Iniciando: ${{total}} clientes`);
    const inicio = Date.now();

    // Navegar para atendimento primeiro
    await navegarAtendimento();
    await delay(CONFIG.delayEntreAcoes);

    for (let i = 0; i < total; i++) {{
        const cliente = CONFIG.clientes[i];
        const cpf = cliente.cpf;
        const nome = cliente.nome;

        console.log(`[${{i+1}}/${{total}}] ${{nome}}`);

        const busca = await buscarCliente(cpf);
        if (!busca.ok) {{
            console.error(`ERRO: ${{busca.erro}}`);
            erro++;
            erros.push({{ cpf, nome, erro: busca.erro }});
            continue;
        }}

        await delay(CONFIG.delayEntreAcoes);

        const acessou = await acessarCliente(busca.grupo, busca.cota);
        if (!acessou) {{
            console.error(`ERRO: Falha ao acessar`);
            erro++;
            erros.push({{ cpf, nome, erro: 'Falha ao acessar' }});
            continue;
        }}

        await delay(CONFIG.delayEntreAcoes);

        const download = await baixarBoleto(nome);
        if (!download.ok) {{
            console.error(`ERRO: ${{download.erro}}`);
            erro++;
            erros.push({{ cpf, nome, erro: download.erro }});
            continue;
        }}

        console.log(`OK: ${{download.arquivo}}`);
        sucesso++;
        downloads.push({{ cpf, nome, arquivo: download.arquivo }});

        if (i < total - 1) {{
            await delay(CONFIG.delayEntreClientes);
        }}
    }}

    const duracao = ((Date.now() - inicio) / 1000).toFixed(1);

    console.log(`\\nRESULTADO: ${{sucesso}}/${{total}} em ${{duracao}}s`);

    return {{
        total,
        sucesso,
        erro,
        erros,
        downloads,
        duracao: parseFloat(duracao)
    }};
}})();
'''
        return script

    async def fechar(self):
        """Fecha o navegador."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Navegador fechado")


async def processar_lote_hibrido(
    usuario: str,
    senha: str,
    clientes: list,
    mes: str = 'JANEIRO',
    ano: int = 2026,
    pasta_downloads: str = None,
    headless: bool = True
) -> dict:
    """
    Funcao principal para processar lote de clientes via metodo hibrido.

    Args:
        usuario: Usuario Canopus (PV)
        senha: Senha Canopus
        clientes: Lista de dicts com 'cpf' e 'nome'
        mes: Mes de referencia
        ano: Ano de referencia
        pasta_downloads: Pasta para salvar os PDFs
        headless: Se True, roda sem interface grafica

    Returns:
        Dict com resultados do processamento
    """
    canopus = CanopusHibrido(usuario, senha, headless)

    try:
        await canopus.iniciar(pasta_downloads)
        resultado = await canopus.processar_clientes(clientes, mes, ano)
        return resultado
    finally:
        await canopus.fechar()


def processar_lote_hibrido_sync(
    usuario: str,
    senha: str,
    clientes: list,
    mes: str = 'JANEIRO',
    ano: int = 2026,
    pasta_downloads: str = None,
    headless: bool = True
) -> dict:
    """
    Wrapper sincrono para usar com Flask.
    """
    return asyncio.run(processar_lote_hibrido(
        usuario=usuario,
        senha=senha,
        clientes=clientes,
        mes=mes,
        ano=ano,
        pasta_downloads=pasta_downloads,
        headless=headless
    ))


# Para testes
if __name__ == '__main__':
    import sys

    async def teste():
        # Usar argumentos da linha de comando ou valores padrao
        usuario = sys.argv[1] if len(sys.argv) > 1 else '17308'
        senha = sys.argv[2] if len(sys.argv) > 2 else 'SUA_SENHA'

        clientes = [
            {'cpf': '50516798898', 'nome': 'ADAO JUNIOR PEREIRA DE BRITO'},
        ]

        print(f"\nTestando metodo hibrido")
        print(f"Usuario: {usuario}")
        print(f"Clientes: {len(clientes)}")
        print("-" * 50)

        resultado = await processar_lote_hibrido(
            usuario=usuario,
            senha=senha,
            clientes=clientes,
            mes='JANEIRO',
            ano=2026,
            headless=False  # False para ver o navegador
        )

        print("\n" + "=" * 50)
        print("RESULTADO:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

    asyncio.run(teste())
