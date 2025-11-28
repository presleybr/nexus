"""
Captura as requisições HTTP do sistema Canopus
Abre navegador e loga todas as requisições para análise

Uso: python capturar_requisicoes.py
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def main():
    print("=" * 80)
    print("CAPTURA DE REQUISIÇÕES - CANOPUS")
    print("=" * 80)
    print("\nEste script vai capturar todas as requisições HTTP.")
    print("Faça o fluxo completo manualmente:")
    print("  1. Login")
    print("  2. Buscar cliente (CPF)")
    print("  3. Navegar para Emissão de Cobrança")
    print("  4. Emitir boleto")
    print("\nTodas as requisições serão salvas em um arquivo JSON.")
    print("-" * 80)

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

        # Log resumido no console
        resource_icon = {
            'document': '📄',
            'script': '📜',
            'stylesheet': '🎨',
            'image': '🖼️',
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

                # Para respostas pequenas, capturar corpo
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'text/html' in content_type or 'application/json' in content_type:
                        body = await response.text()
                        if len(body) < 100000:  # Só guardar se menor que 100KB
                            req['response_body'] = body
                except:
                    pass

                break

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--no-sandbox',
        ]
    )

    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ignore_https_errors=True,
        java_script_enabled=True,
    )

    page = await context.new_page()

    # Configurar timeout maior
    page.set_default_timeout(60000)  # 60 segundos

    # Registrar listeners
    page.on('request', log_request)
    page.on('response', log_response)

    # Abrir Canopus - tentar várias URLs
    print("\n🌐 Abrindo Canopus...")

    urls_tentar = [
        'https://cnp3.consorciocanopus.com.br/WWW/frmCorCCCnsLogin.aspx',
        'https://cnp3.consorciocanopus.com.br/www/frmCorCCCnsLogin.aspx',
        'https://cnp3.consorciocanopus.com.br/',
    ]

    sucesso = False
    for url in urls_tentar:
        try:
            print(f"Tentando: {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            print(f"✅ Conectado: {url}")
            sucesso = True
            break
        except Exception as e:
            print(f"❌ Falhou: {str(e)[:100]}")
            continue

    if not sucesso:
        print("\n❌ Não foi possível conectar ao Canopus!")
        print("\nPossíveis causas:")
        print("  1. Servidor fora do ar")
        print("  2. VPN/Firewall bloqueando")
        print("  3. URL mudou")
        print("\nTente abrir no navegador normal primeiro:")
        print("  https://cnp3.consorciocanopus.com.br")
        await browser.close()
        await playwright.stop()
        return

    print("\n" + "=" * 80)
    print("NAVEGADOR ABERTO - FAÇA O FLUXO COMPLETO MANUALMENTE")
    print("=" * 80)
    print("\n📋 CHECKLIST:")
    print("  [ ] 1. Fazer login")
    print("  [ ] 2. Clicar em Atendimento")
    print("  [ ] 3. Clicar em Busca Avançada")
    print("  [ ] 4. Selecionar CPF")
    print("  [ ] 5. Buscar cliente")
    print("  [ ] 6. Clicar no cliente encontrado")
    print("  [ ] 7. Clicar em Emissão de Cobrança")
    print("  [ ] 8. Selecionar boleto")
    print("  [ ] 9. Emitir Cobrança")
    print("\n⏸️  Quando terminar, volte aqui e pressione ENTER.\n")

    # Aguardar usuário
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, input, "Pressione ENTER para salvar e encerrar...")

    # Salvar requisições
    pasta = r'D:\Nexus\automation\canopus\logs'
    os.makedirs(pasta, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = os.path.join(pasta, f'requisicoes_{timestamp}.json')

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

    print(f"\n💾 Execute agora:")
    print(f"   python mapear_fluxo.py")
    print(f"\n   OU:")
    print(f"   python mapear_fluxo.py {arquivo}")

    await browser.close()
    await playwright.stop()

    print("\n✅ Encerrado!")

if __name__ == '__main__':
    asyncio.run(main())
