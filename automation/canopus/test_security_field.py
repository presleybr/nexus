"""
Script de teste para identificar campo de segurança/CAPTCHA no login
"""
import asyncio
import sys
from pathlib import Path

# Adicionar diretório ao path
sys.path.append(str(Path(__file__).parent))

from playwright.async_api import async_playwright

async def test_security_field():
    """Testa e identifica o campo de segurança"""

    async with async_playwright() as p:
        # Lançar navegador visível para debug
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("🌐 Navegando para página de login...")
        await page.goto('https://cnp3.consorciocanopus.com.br/WWW/frmCorCCCnsLogin.aspx')
        await page.wait_for_load_state('networkidle')

        print("\n📄 Buscando todos os inputs na página...")
        inputs = await page.query_selector_all('input')

        for i, inp in enumerate(inputs):
            inp_id = await inp.get_attribute('id') or 'N/A'
            inp_name = await inp.get_attribute('name') or 'N/A'
            inp_type = await inp.get_attribute('type') or 'N/A'
            inp_placeholder = await inp.get_attribute('placeholder') or 'N/A'

            print(f"\nInput #{i}:")
            print(f"  ID: {inp_id}")
            print(f"  Name: {inp_name}")
            print(f"  Type: {inp_type}")
            print(f"  Placeholder: {inp_placeholder}")

        print("\n📄 Buscando labels na página...")
        labels = await page.query_selector_all('label')

        for i, label in enumerate(labels):
            text = await label.text_content()
            label_for = await label.get_attribute('for') or 'N/A'
            print(f"\nLabel #{i}:")
            print(f"  Text: {text.strip()}")
            print(f"  For: {label_for}")

        print("\n📄 Buscando spans com texto 'segur' ou 'captcha' ou 'caracteres'...")
        all_text = await page.evaluate("""
            () => {
                const body = document.body.innerText;
                return body;
            }
        """)

        if 'segur' in all_text.lower() or 'caracteres' in all_text.lower():
            print("✅ ENCONTRADO texto com 'segurança' ou 'caracteres'!")
            print(f"Conteúdo da página:\n{all_text[:1000]}")
        else:
            print("❌ NÃO encontrado texto com 'segurança' ou 'caracteres'")

        print("\n\n⏸️  Navegador ficará aberto - pressione Enter para fechar...")
        input()

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_security_field())
