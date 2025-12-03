"""
Script de debug para mapear TODOS os campos da página de login
Identifica campos de segurança, CAPTCHA, etc.
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from playwright.async_api import async_playwright

async def debug_login_fields():
    """Debug completo da página de login"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 80)
        print("DEBUG: Mapeando página de login do Canopus")
        print("=" * 80)

        # Navegar para login
        url = 'https://cnp3.consorciocanopus.com.br/WWW/frmCorCCCnsLogin.aspx'
        print(f"\n🌐 Navegando para: {url}")
        await page.goto(url, wait_until='networkidle')

        print("\n" + "=" * 80)
        print("TODOS OS INPUTS NA PÁGINA")
        print("=" * 80)

        # Mapear TODOS os inputs
        inputs = await page.query_selector_all('input')

        for i, inp in enumerate(inputs):
            inp_id = await inp.get_attribute('id') or ''
            inp_name = await inp.get_attribute('name') or ''
            inp_type = await inp.get_attribute('type') or ''
            inp_value = await inp.get_attribute('value') or ''
            inp_placeholder = await inp.get_attribute('placeholder') or ''
            inp_class = await inp.get_attribute('class') or ''

            # Verificar se está visível
            is_visible = await inp.is_visible()

            print(f"\n[{i}] Input:")
            print(f"    ID: {inp_id}")
            print(f"    Name: {inp_name}")
            print(f"    Type: {inp_type}")
            print(f"    Value: {inp_value[:50] if inp_value else ''}")
            print(f"    Placeholder: {inp_placeholder}")
            print(f"    Class: {inp_class}")
            print(f"    Visível: {is_visible}")

        # Pegar texto completo da página
        print("\n" + "=" * 80)
        print("TEXTO DA PÁGINA")
        print("=" * 80)

        page_text = await page.evaluate("() => document.body.innerText")
        print(page_text)

        # Procurar especificamente por campos relacionados a segurança
        print("\n" + "=" * 80)
        print("BUSCA POR CAMPOS DE SEGURANÇA")
        print("=" * 80)

        security_keywords = ['segur', 'captcha', 'token', 'caracteres', 'verif']

        for keyword in security_keywords:
            # Buscar inputs
            selector_id = f'input[id*="{keyword}" i]'
            selector_name = f'input[name*="{keyword}" i]'

            found_by_id = await page.query_selector_all(selector_id)
            found_by_name = await page.query_selector_all(selector_name)

            if found_by_id or found_by_name:
                print(f"\n✅ Encontrado com '{keyword}':")
                print(f"   Por ID: {len(found_by_id)} campo(s)")
                print(f"   Por Name: {len(found_by_name)} campo(s)")

        # Tirar screenshot
        screenshot_path = Path(__file__).parent / 'logs' / 'debug_login_page.png'
        screenshot_path.parent.mkdir(exist_ok=True)
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n📸 Screenshot salvo: {screenshot_path}")

        print("\n⏸️  Pressione Enter para fechar...")
        input()

        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug_login_fields())
