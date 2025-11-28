"""
MODO DE CAPTURA - Para diagnosticar o fluxo real
Execute este script e faça o processo manualmente no Chromium
O script vai capturar todas as ações e seletores
"""
import asyncio
from playwright.async_api import async_playwright
import sys
sys.path.insert(0, 'D:/Nexus/backend')
sys.path.insert(0, 'D:/Nexus/automation/canopus')

from db_config import get_connection_params
import psycopg
from cryptography.fernet import Fernet

# Chave de criptografia
ENCRYPTION_KEY = b'6vLPQxE7R8YfZ3kN9mQ2wT5uH8jK4nP1sD7gF0aB3cE='

def obter_credenciais():
    """Buscar credenciais do banco"""
    conn = psycopg.connect(**get_connection_params())
    cur = conn.cursor()

    cur.execute("""
        SELECT c.usuario, c.senha_encrypted, c.codigo_empresa
        FROM credenciais_canopus c
        INNER JOIN pontos_venda pv ON c.ponto_venda_id = pv.id
        WHERE pv.codigo = '24627' AND c.ativo = TRUE
        LIMIT 1
    """)

    cred = cur.fetchone()
    conn.close()

    if cred:
        # Descriptografar senha
        cipher = Fernet(ENCRYPTION_KEY)
        senha_encrypted = cred[1]

        if senha_encrypted.startswith('\\x'):
            senha_encrypted = bytes.fromhex(senha_encrypted[2:])

        senha = cipher.decrypt(senha_encrypted).decode()

        return {
            'usuario': cred[0],
            'senha': senha,
            'codigo_empresa': cred[2]
        }

    return None

async def capturar_fluxo():
    print('=' * 80)
    print('MODO DE CAPTURA - Diagnóstico do Fluxo')
    print('=' * 80)
    print()

    # Buscar credenciais
    print('[1/5] Buscando credenciais...')
    credenciais = obter_credenciais()

    if not credenciais:
        print('[ERRO] Credenciais não encontradas!')
        return

    print(f'[OK] Usuário: {credenciais["usuario"]}')
    print()

    # Abrir navegador
    print('[2/5] Abrindo Chromium...')
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500,  # Devagar para você acompanhar
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        print('[OK] Chromium aberto')
        print()

        # Fazer login
        print('[3/5] Fazendo login...')
        await page.goto('https://cnp3.consorciocanopus.com.br/WWW/frmCorCCCnsLogin.aspx')
        await asyncio.sleep(1)

        await page.fill('#edtUsuario', credenciais['usuario'])
        await page.fill('#edtSenha', credenciais['senha'])
        await page.click('#btnLogin')

        await asyncio.sleep(3)
        print('[OK] Login realizado')
        print()

        # Instruções
        print('=' * 80)
        print('AGORA FAÇA O PROCESSO MANUALMENTE:')
        print('=' * 80)
        print()
        print('1. Clique no ícone de Atendimento (pessoa)')
        print('2. Clique em "Busca avançada"')
        print('3. Selecione "CPF" no dropdown')
        print('4. Digite o CPF: 70899057136')
        print('5. Clique em "Buscar"')
        print('6. Clique no nome do cliente')
        print('7. Clique em "Emissão de Cobrança"')
        print()
        print('[4/5] AGUARDANDO VOCÊ CHEGAR NA TELA DE EMISSÃO...')
        print('      (Pressione ENTER quando estiver na tela de Emissão de Cobrança)')
        input()

        # Capturar estrutura da página
        print()
        print('[5/5] Capturando estrutura da página...')
        print()

        info = await page.evaluate("""
            () => {
                // Capturar checkboxes
                const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                const checkboxInfo = Array.from(checkboxes).map(cb => ({
                    id: cb.id,
                    name: cb.name,
                    visible: cb.offsetParent !== null
                }));

                // Capturar inputs de imagem
                const imgInputs = document.querySelectorAll('input[id*="imgEmite_Boleto"]');
                const imgInfo = Array.from(imgInputs).map(img => ({
                    id: img.id,
                    type: img.type,
                    visible: img.offsetParent !== null
                }));

                // Capturar botões
                const botoes = document.querySelectorAll('input[type="button"], button');
                const botoesInfo = Array.from(botoes).map(btn => ({
                    id: btn.id,
                    value: btn.value || btn.textContent,
                    visible: btn.offsetParent !== null
                })).filter(b => b.value && b.value.toLowerCase().includes('emit'));

                return {
                    checkboxes: checkboxInfo,
                    imgInputs: imgInfo,
                    botoes: botoesInfo
                };
            }
        """)

        print('CHECKBOXES ENCONTRADOS:')
        for idx, cb in enumerate(info['checkboxes']):
            print(f'  {idx + 1}. ID: {cb["id"]}, Name: {cb["name"]}, Visível: {cb["visible"]}')

        print()
        print('INPUTS DE IMAGEM (imgEmite_Boleto):')
        for idx, img in enumerate(info['imgInputs']):
            print(f'  {idx + 1}. ID: {img["id"]}, Type: {img["type"]}, Visível: {img["visible"]}')

        print()
        print('BOTÕES COM "EMIT":')
        for idx, btn in enumerate(info['botoes']):
            print(f'  {idx + 1}. ID: {btn["id"]}, Value: {btn["value"]}, Visível: {btn["visible"]}')

        print()
        print('=' * 80)
        print('AGORA VOU TENTAR CLICAR AUTOMATICAMENTE:')
        print('=' * 80)
        print()

        # Tentar encontrar e clicar no checkbox
        if len(info['imgInputs']) > 0:
            checkbox_id = info['imgInputs'][1]['id'] if len(info['imgInputs']) > 1 else info['imgInputs'][0]['id']
            print(f'[*] Clicando no checkbox: #{checkbox_id}')

            try:
                await page.click(f'#{checkbox_id}')
                print('[OK] Checkbox clicado!')
            except Exception as e:
                print(f'[ERRO] Não conseguiu clicar: {e}')

        await asyncio.sleep(1)

        # Tentar encontrar e clicar no botão
        if len(info['botoes']) > 0:
            botao_id = info['botoes'][0]['id']
            print(f'[*] Clicando no botão: #{botao_id}')

            try:
                await page.click(f'#{botao_id}')
                print('[OK] Botão clicado!')
            except Exception as e:
                print(f'[ERRO] Não conseguiu clicar: {e}')

        print()
        print('=' * 80)
        print('AGUARDANDO 10 SEGUNDOS PARA VOCÊ VER O RESULTADO...')
        print('=' * 80)
        await asyncio.sleep(10)

        print()
        print('[OK] Diagnóstico completo!')
        print('     O navegador vai fechar em 5 segundos...')
        await asyncio.sleep(5)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(capturar_fluxo())
