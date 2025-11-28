"""
Captura requisições HTTP usando o código que JÁ FUNCIONA
Versão 2 - Baseada em testar_busca_cpf.py

Uso: python capturar_requisicoes_v2.py --cpf 708.990.571-36
"""

import asyncio
import json
import os
import argparse
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from db_config import get_connection_params
import psycopg
from psycopg.rows import dict_row
from cryptography.fernet import Fernet

# Chave de criptografia
ENCRYPTION_KEY = b'6vLPQxE7R8YfZ3kN9mQ2wT5uH8jK4nP1sD7gF0aB3cE='


def descriptografar_senha(senha_encrypted) -> str:
    """Descriptografa senha"""
    cipher = Fernet(ENCRYPTION_KEY)

    if isinstance(senha_encrypted, str):
        if senha_encrypted.startswith('\\x'):
            senha_encrypted = bytes.fromhex(senha_encrypted[2:])
        else:
            senha_encrypted = senha_encrypted.encode('utf-8')
    elif isinstance(senha_encrypted, memoryview):
        senha_encrypted = bytes(senha_encrypted)

    return cipher.decrypt(senha_encrypted).decode()


def buscar_credencial(ponto_venda_codigo: str):
    """Busca credencial no banco"""
    conn_params = get_connection_params()

    try:
        with psycopg.connect(**conn_params, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        c.usuario,
                        c.senha_encrypted,
                        c.codigo_empresa,
                        pv.codigo as ponto_venda
                    FROM credenciais_canopus c
                    JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
                    WHERE pv.codigo = %s AND c.ativo = TRUE
                    LIMIT 1
                """, (ponto_venda_codigo,))

                resultado = cur.fetchone()

                if resultado:
                    senha = descriptografar_senha(resultado['senha_encrypted'])
                    return {
                        'usuario': resultado['usuario'],
                        'senha': senha,
                        'codigo_empresa': resultado['codigo_empresa'],
                        'ponto_venda': resultado['ponto_venda']
                    }
                return None

    except Exception as e:
        print(f"[ERRO] Falha ao buscar credencial: {e}")
        return None


async def capturar_com_automacao(cpf: str):
    """Captura requisições executando o fluxo automatizado"""

    print()
    print("=" * 80)
    print("CAPTURA DE REQUISIÇÕES - VERSÃO 2 (AUTOMÁTICO)")
    print("=" * 80)
    print("\nEste script vai:")
    print("  1. Executar o fluxo completo AUTOMATICAMENTE")
    print("  2. Capturar TODAS as requisições HTTP")
    print("  3. Salvar em JSON para análise")
    print()
    print("Vantagem: Usa o código que JÁ FUNCIONA!")
    print("-" * 80)

    # Buscar credencial
    print("\n[*] Buscando credenciais do PV 17.308...")
    cred = buscar_credencial('17.308')

    if not cred:
        print("[ERRO] Credencial não encontrada!")
        print("Execute: python cadastrar_credencial.py")
        return 1

    print(f"[OK] Credencial encontrada - Usuario: {cred['usuario']}")
    print()

    # Lista para armazenar requisições
    requisicoes = []

    async def log_request(request):
        req_data = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'url': request.url,
            'headers': dict(request.headers),
            'post_data': None,
            'resource_type': request.resource_type
        }

        if request.method == 'POST':
            try:
                req_data['post_data'] = request.post_data
            except:
                pass

        requisicoes.append(req_data)

        # Log resumido
        resource_icon = {
            'document': '📄',
            'script': '📜',
            'xhr': '🔄',
            'fetch': '🔄',
        }.get(request.resource_type, '📦')

        print(f"{resource_icon} [{request.method:4}] {request.url[:80]}")

    async def log_response(response):
        # Encontrar requisição correspondente
        for req in reversed(requisicoes):
            if req['url'] == response.url and 'status' not in req:
                req['status'] = response.status
                req['response_headers'] = dict(response.headers)

                # Capturar corpo para HTML/JSON
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' in content_type or 'application/json' in content_type:
                        body = await response.text()
                        if len(body) < 100000:  # < 100KB
                            req['response_body'] = body
                except:
                    pass
                break

    # Iniciar Playwright
    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )

    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )

    page = await context.new_page()
    page.set_default_timeout(60000)

    # Registrar listeners
    page.on('request', log_request)
    page.on('response', log_response)

    print("\n" + "=" * 80)
    print("EXECUTANDO FLUXO AUTOMATIZADO")
    print("=" * 80)

    try:
        # ====================================================================
        # FLUXO 1: LOGIN
        # ====================================================================

        print("\n📍 ETAPA 1: LOGIN")
        print("-" * 80)

        await page.goto('https://cnp3.consorciocanopus.com.br/WWW/frmCorCCCnsLogin.aspx')
        await asyncio.sleep(2)

        # Preencher login
        await page.fill('#ctl00_Conteudo_txtUsuario', cred['usuario'])
        await asyncio.sleep(0.5)
        await page.fill('#ctl00_Conteudo_txtSenha', cred['senha'])
        await asyncio.sleep(0.5)

        # Clicar login
        await page.click('#ctl00_Conteudo_btnEntrar')
        await asyncio.sleep(3)

        print("✅ Login concluído")

        # ====================================================================
        # FLUXO 2: BUSCA DE CLIENTE
        # ====================================================================

        print("\n📍 ETAPA 2: BUSCA DE CLIENTE")
        print("-" * 80)

        # Clicar Atendimento
        await page.click('img[title="Atendimento"]')
        await asyncio.sleep(2)

        # Clicar Busca Avançada
        await page.click('text=Busca avançada')
        await asyncio.sleep(2)

        # Selecionar CPF
        await page.select_option('#ctl00_Conteudo_ddlTipoBusca', 'F')
        await asyncio.sleep(1)

        # Preencher CPF
        await page.fill('#ctl00_Conteudo_txtBusca', cpf)
        await asyncio.sleep(1)

        # Buscar
        await page.click('#ctl00_Conteudo_btnBuscar')
        await asyncio.sleep(2)

        # Clicar no cliente (segundo resultado)
        links = await page.query_selector_all('a[id*="lnkNome"]')
        if len(links) >= 2:
            await links[1].click()
        elif len(links) >= 1:
            await links[0].click()

        await asyncio.sleep(3)

        print("✅ Cliente acessado")

        # ====================================================================
        # FLUXO 3: EMISSÃO DE COBRANÇA
        # ====================================================================

        print("\n📍 ETAPA 3: EMISSÃO DE COBRANÇA")
        print("-" * 80)

        # Clicar Emissão de Cobrança
        await page.click('text=Emissão de Cobrança')
        await asyncio.sleep(3)

        # Selecionar checkbox do boleto (segundo)
        checkboxes = await page.query_selector_all('input[id*="grdBoleto_Avulso"][id*="imgEmite_Boleto"]')
        if len(checkboxes) >= 2:
            await checkboxes[1].click()
        elif len(checkboxes) >= 1:
            await checkboxes[0].click()

        await asyncio.sleep(1)

        # Clicar Emitir (NÃO vamos esperar o PDF, apenas capturar a requisição)
        print("\n⚠️  Vou clicar em 'Emitir Cobrança'...")
        print("    Uma nova aba vai abrir com o PDF.")
        print("    Aguarde 5 segundos e a aba será fechada automaticamente.")

        # Aguardar nova aba
        async with context.expect_page() as new_page_info:
            await page.click('#ctl00_Conteudo_btnEmitir')

        nova_aba = await new_page_info.value
        await nova_aba.wait_for_load_state('load')
        await asyncio.sleep(5)  # Aguardar PDF carregar completamente

        print("✅ PDF carregado (requisição capturada)")

        await nova_aba.close()

        print("\n✅ FLUXO COMPLETO CAPTURADO!")

    except Exception as e:
        print(f"\n⚠️  Erro durante captura: {e}")
        print("Mas as requisições até agora foram capturadas!")

    finally:
        # Aguardar um pouco antes de fechar
        await asyncio.sleep(2)

        # Fechar navegador
        await browser.close()
        await playwright.stop()

    # ========================================================================
    # SALVAR REQUISIÇÕES
    # ========================================================================

    print("\n" + "=" * 80)
    print("SALVANDO REQUISIÇÕES")
    print("=" * 80)

    pasta = Path(r'D:\Nexus\automation\canopus\logs')
    pasta.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = pasta / f'requisicoes_{timestamp}.json'

    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(requisicoes, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {len(requisicoes)} requisições salvas em:")
    print(f"   {arquivo}")

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO")
    print("=" * 80)

    posts = [r for r in requisicoes if r['method'] == 'POST']
    gets = [r for r in requisicoes if r['method'] == 'GET']
    aspx = [r for r in requisicoes if '.aspx' in r['url']]

    print(f"\n📈 Estatísticas:")
    print(f"   Total de requisições: {len(requisicoes)}")
    print(f"   GET:  {len(gets)}")
    print(f"   POST: {len(posts)}")
    print(f"   Páginas ASPX: {len(aspx)}")

    print(f"\n🔍 URLs POST importantes:")
    for r in posts:
        if '.aspx' in r['url']:
            from urllib.parse import urlparse
            parsed = urlparse(r['url'])
            print(f"   → {parsed.path}")

    print(f"\n💾 PRÓXIMO PASSO:")
    print(f"   python mapear_fluxo.py")
    print()

    return 0


def main():
    parser = argparse.ArgumentParser(description='Capturar requisições automaticamente')
    parser.add_argument('--cpf', required=True, help='CPF do cliente para teste')

    args = parser.parse_args()

    return asyncio.run(capturar_com_automacao(args.cpf))


if __name__ == '__main__':
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        sys.exit(0)
