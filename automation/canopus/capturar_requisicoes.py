"""
Script para capturar todas as requisições HTTP que o site Canopus faz.
Executa o fluxo completo e salva as requisições em JSON.

USO:
    1. Configure variáveis de ambiente:
       set CANOPUS_USUARIO=seu_usuario
       set CANOPUS_SENHA=sua_senha
       set CANOPUS_CPF_TESTE=12345678901

    2. Execute:
       python capturar_requisicoes.py

    3. Complete o fluxo manualmente no browser

    4. Analise: automation/canopus/requisicoes_capturadas.json
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

async def capturar_requisicoes():
    """Captura todas as requisições durante o fluxo de download"""

    requisicoes = []
    respostas_importantes = []

    async def on_request(request):
        """Callback para cada requisição"""
        if 'canopus' in request.url.lower():
            req_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'url': request.url,
                'resource_type': request.resource_type,
                'headers': dict(request.headers),
                'post_data': None
            }

            if request.method == 'POST':
                try:
                    req_data['post_data'] = request.post_data
                except:
                    pass

            requisicoes.append(req_data)
            print(f"📤 {request.method} {request.url[:80]}")

    async def on_response(response):
        """Callback para respostas importantes"""
        content_type = response.headers.get('content-type', '')

        # Capturar PDFs e HTMLs importantes
        if 'pdf' in content_type.lower() or 'html' in content_type.lower():
            respostas_importantes.append({
                'url': response.url,
                'status': response.status,
                'content_type': content_type,
                'headers': dict(response.headers)
            })

            if 'pdf' in content_type.lower():
                print(f"📥 PDF DETECTADO: {response.url}")

    # Buscar credenciais do banco ou variáveis de ambiente
    usuario = os.environ.get('CANOPUS_USUARIO', '')
    senha = os.environ.get('CANOPUS_SENHA', '')
    cpf_teste = os.environ.get('CANOPUS_CPF_TESTE', '')

    if not usuario or not senha:
        print("❌ Configure as variáveis de ambiente:")
        print("   set CANOPUS_USUARIO=seu_usuario")
        print("   set CANOPUS_SENHA=sua_senha")
        print("   set CANOPUS_CPF_TESTE=12345678901")
        return

    print("=" * 60)
    print("🔍 CAPTURADOR DE REQUISIÇÕES HTTP - CANOPUS")
    print("=" * 60)
    print(f"Usuário: {usuario}")
    print(f"CPF teste: {cpf_teste}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()

        # Registrar listeners
        page.on('request', on_request)
        page.on('response', on_response)

        try:
            print("\n📍 ETAPA 1: Navegando para login...")
            await page.goto('https://cnp3.consorciocanopus.com.br/')
            await page.wait_for_load_state('networkidle')

            print("\n⏳ Complete o LOGIN manualmente e pressione ENTER...")
            input(">>> ")

            print("\n⏳ Navegue até a BUSCA AVANÇADA, busque o CPF e BAIXE O BOLETO...")
            print("   Pressione ENTER quando terminar...")
            input(">>> ")

        except Exception as e:
            print(f"❌ Erro: {e}")

        finally:
            cookies = await context.cookies()
            await browser.close()

    # Salvar resultados
    print("\n" + "=" * 60)
    print("📊 RESULTADOS")
    print("=" * 60)

    requisicoes_post = [r for r in requisicoes if r['method'] == 'POST']

    print(f"\nTotal de requisições: {len(requisicoes)}")
    print(f"Requisições POST: {len(requisicoes_post)}")

    resultado = {
        'data_captura': datetime.now().isoformat(),
        'requisicoes': requisicoes,
        'respostas_importantes': respostas_importantes,
        'cookies': [{'name': c['name'], 'domain': c['domain']} for c in cookies]
    }

    output_path = Path('requisicoes_capturadas.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Resultados salvos em: {output_path}")

if __name__ == '__main__':
    asyncio.run(capturar_requisicoes())
