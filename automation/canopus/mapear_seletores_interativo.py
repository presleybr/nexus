"""
Script interativo para mapear seletores do Canopus pós-login

Este script:
1. Faz login no Canopus
2. Para em cada etapa para você mapear os seletores
3. Salva os seletores mapeados em um arquivo JSON
4. Você pode usar DevTools (F12) para inspecionar os elementos

Uso: python mapear_seletores_interativo.py
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Importar módulos
from canopus_automation import CanopusAutomation
from config import CanopusConfig

# Importar credenciais do banco
try:
    from db_config import get_connection_params
    import psycopg
    from psycopg.rows import dict_row
    from cryptography.fernet import Fernet
except ImportError as e:
    print(f"[ERRO] Falta dependência: {e}")
    print("Execute: pip install psycopg cryptography")
    sys.exit(1)


# Chave de criptografia (mesma do cadastrar_credencial.py)
ENCRYPTION_KEY = b'6vLPQxE7R8YfZ3kN9mQ2wT5uH8jK4nP1sD7gF0aB3cE='


def descriptografar_senha(senha_encrypted) -> str:
    """Descriptografa senha"""
    cipher = Fernet(ENCRYPTION_KEY)

    # Se vier como string em formato hex do PostgreSQL (ex: \x67414141...)
    if isinstance(senha_encrypted, str):
        # Remover prefixo \x e converter de hex para bytes
        if senha_encrypted.startswith('\\x'):
            senha_encrypted = bytes.fromhex(senha_encrypted[2:])
        else:
            # Se for string normal, converter
            senha_encrypted = senha_encrypted.encode('utf-8')
    elif isinstance(senha_encrypted, memoryview):
        # Se vier como memoryview, converter para bytes
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
                    # Descriptografar senha
                    try:
                        senha = descriptografar_senha(resultado['senha_encrypted'])
                        return {
                            'usuario': resultado['usuario'],
                            'senha': senha,
                            'codigo_empresa': resultado['codigo_empresa'],
                            'ponto_venda': resultado['ponto_venda']
                        }
                    except Exception as e_decrypt:
                        print(f"[ERRO] Falha ao descriptografar senha: {e_decrypt}")
                        import traceback
                        traceback.print_exc()
                        return None
                return None

    except Exception as e:
        print(f"[ERRO] Falha ao buscar credencial: {e}")
        import traceback
        traceback.print_exc()
        return None


def salvar_seletores(seletores: dict):
    """Salva seletores mapeados em JSON"""
    arquivo = Path(__file__).parent / "seletores_mapeados.json"

    dados = {
        'data_mapeamento': datetime.now().isoformat(),
        'seletores': seletores
    }

    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Seletores salvos em: {arquivo}")


async def mapear_interativo():
    """Processo interativo de mapeamento"""

    print()
    print("=" * 80)
    print("         MAPEAMENTO INTERATIVO DE SELETORES - CANOPUS")
    print("=" * 80)
    print()

    # Buscar credencial do banco
    print("[*] Buscando credenciais do PV 17.308...")
    cred = buscar_credencial('17.308')

    if not cred:
        print("[ERRO] Credencial não encontrada para PV 17.308!")
        print()
        print("Verificando pontos de venda cadastrados...")

        # Listar pontos disponíveis
        conn_params = get_connection_params()
        try:
            with psycopg.connect(**conn_params, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT pv.codigo, pv.nome, COUNT(c.id) as qtd_credenciais
                        FROM pontos_venda pv
                        LEFT JOIN credenciais_canopus c ON pv.id = c.ponto_venda_id AND c.ativo = TRUE
                        WHERE pv.ativo = TRUE
                        GROUP BY pv.codigo, pv.nome
                        ORDER BY pv.codigo
                    """)
                    pontos = cur.fetchall()

                    if pontos:
                        print()
                        print("Pontos de venda cadastrados:")
                        for p in pontos:
                            status = "✓ COM credencial" if p['qtd_credenciais'] > 0 else "✗ SEM credencial"
                            print(f"  - PV {p['codigo']}: {p['nome']} [{status}]")
                    else:
                        print("[ERRO] Nenhum ponto de venda cadastrado!")
        except Exception as e:
            print(f"[ERRO] Falha ao verificar: {e}")

        print()
        print("Solução: Execute python cadastrar_credencial.py")
        return 1

    print(f"[OK] Credencial encontrada - Usuario: {cred['usuario']}")
    print()

    # Pegar um CPF de exemplo da planilha
    cpf_exemplo = "057.434.159-51"  # Você pode mudar para um CPF real da planilha

    print("=" * 80)
    print("IMPORTANTE: Este processo é INTERATIVO")
    print("=" * 80)
    print()
    print("O navegador vai abrir e fazer login.")
    print("Depois, vamos PAUSAR em cada etapa para você:")
    print("  1. Inspecionar a página (F12)")
    print("  2. Encontrar os seletores CSS")
    print("  3. Digitar os seletores aqui")
    print()
    print("Você terá TEMPO ILIMITADO em cada etapa.")
    print()

    input("▶️ Pressione ENTER para começar...")

    # Inicializar bot
    config = CanopusConfig()
    bot = CanopusAutomation(config, headless=False)  # Navegador visível

    seletores_mapeados = {
        'login': {
            'usuario_input': '#edtUsuario',
            'senha_input': '#edtSenha',
            'botao_entrar': '#btnLogin',
        }
    }

    try:
        # 1. FAZER LOGIN
        print()
        print("=" * 80)
        print("ETAPA 1: FAZENDO LOGIN")
        print("=" * 80)
        print()

        await bot.iniciar_navegador()

        login_ok = await bot.login(
            usuario=cred['usuario'],
            senha=cred['senha'],
            codigo_empresa=cred['codigo_empresa'],
            ponto_venda=cred['ponto_venda']
        )

        if not login_ok:
            print("[ERRO] Login falhou!")
            return 1

        print("[OK] Login realizado com sucesso!")
        print()

        # 2. MAPEAR BUSCA DE CLIENTE
        print("=" * 80)
        print("ETAPA 2: MAPEAR BUSCA DE CLIENTE (CPF)")
        print("=" * 80)
        print()
        print("Agora você está logado no sistema.")
        print()
        print("📋 TAREFAS:")
        print("  1. Encontre onde buscar cliente por CPF")
        print("  2. Pressione F12 para abrir DevTools")
        print("  3. Use o seletor de elementos (🔍)")
        print("  4. Anote os seletores abaixo:")
        print()
        print("Seletores necessários:")
        print("  - Menu/Link para acessar busca de cliente")
        print("  - Campo de input do CPF")
        print("  - Botão de buscar/pesquisar")
        print()

        input("▶️ Quando estiver pronto, pressione ENTER...")

        print()
        print("Digite os seletores (deixe vazio para pular):")
        print()

        busca = {}

        menu_busca = input("  Menu/Link de busca (ex: a[href*='busca']): ").strip()
        if menu_busca:
            busca['menu_busca'] = menu_busca

        cpf_input = input("  Campo CPF (ex: input[name='cpf']): ").strip()
        if cpf_input:
            busca['cpf_input'] = cpf_input

        botao_buscar = input("  Botão Buscar (ex: button.btn-buscar): ").strip()
        if botao_buscar:
            busca['botao_buscar'] = botao_buscar

        resultado_lista = input("  Lista de resultados (ex: .resultado-busca): ").strip()
        if resultado_lista:
            busca['resultado_lista'] = resultado_lista

        if busca:
            seletores_mapeados['busca'] = busca
            print("[OK] Seletores de busca salvos!")

        # 3. TESTAR BUSCA (se mapeou)
        if 'busca' in seletores_mapeados and 'cpf_input' in seletores_mapeados['busca']:
            print()
            print("=" * 80)
            print("ETAPA 3: TESTAR BUSCA")
            print("=" * 80)
            print()
            print(f"Vamos tentar buscar o CPF: {cpf_exemplo}")
            print()

            testar = input("Testar busca agora? (s/n): ").strip().lower()

            if testar == 's':
                try:
                    # Navegar para busca (se tiver menu)
                    if 'menu_busca' in busca:
                        print(f"[*] Clicando em menu de busca: {busca['menu_busca']}")
                        await bot.page.click(busca['menu_busca'])
                        await asyncio.sleep(2)

                    # Preencher CPF
                    print(f"[*] Preenchendo CPF: {cpf_exemplo}")
                    await bot.page.fill(busca['cpf_input'], cpf_exemplo)
                    await asyncio.sleep(1)

                    # Clicar buscar
                    if 'botao_buscar' in busca:
                        print(f"[*] Clicando em buscar")
                        await bot.page.click(busca['botao_buscar'])
                        await asyncio.sleep(3)

                    await bot.screenshot("apos_busca_teste")
                    print("[OK] Busca executada! Screenshot salvo.")

                except Exception as e:
                    print(f"[ERRO] Falha na busca: {e}")

        # 4. MAPEAR EMISSÃO DE BOLETO
        print()
        print("=" * 80)
        print("ETAPA 4: MAPEAR EMISSÃO DE BOLETO")
        print("=" * 80)
        print()
        print("Agora precisamos mapear a tela de emissão de boleto.")
        print()
        print("📋 TAREFAS:")
        print("  1. Navegue até a tela de emissão/cobrança do cliente")
        print("  2. Identifique os elementos:")
        print("     - Seletor de parcela/mês")
        print("     - Botão de gerar/emitir boleto")
        print("     - Indicador de sucesso")
        print()

        input("▶️ Quando estiver na tela de emissão, pressione ENTER...")

        print()
        print("Digite os seletores:")
        print()

        emissao = {}

        menu_emissao = input("  Menu de emissão (ex: a[href*='emissao']): ").strip()
        if menu_emissao:
            emissao['menu_emissao'] = menu_emissao

        select_parcela = input("  Seletor de parcela (ex: select[name='parcela']): ").strip()
        if select_parcela:
            emissao['select_parcela'] = select_parcela

        botao_emitir = input("  Botão emitir (ex: button#btnEmitir): ").strip()
        if botao_emitir:
            emissao['botao_emitir'] = botao_emitir

        mensagem_sucesso = input("  Mensagem sucesso (ex: .alert-success): ").strip()
        if mensagem_sucesso:
            emissao['mensagem_sucesso'] = mensagem_sucesso

        if emissao:
            seletores_mapeados['emissao'] = emissao
            print("[OK] Seletores de emissão salvos!")

        # 5. MAPEAR DOWNLOAD
        print()
        print("=" * 80)
        print("ETAPA 5: MAPEAR DOWNLOAD DO PDF")
        print("=" * 80)
        print()
        print("Por fim, precisamos do botão/link de download do PDF.")
        print()

        input("▶️ Quando estiver vendo o link de download, pressione ENTER...")

        print()

        download = {}

        link_pdf = input("  Link/Botão download PDF (ex: a[href*='.pdf']): ").strip()
        if link_pdf:
            download['link_pdf'] = link_pdf

        botao_download = input("  Botão download (ex: button.btn-download): ").strip()
        if botao_download:
            download['botao_download'] = botao_download

        if download:
            seletores_mapeados['download'] = download
            print("[OK] Seletores de download salvos!")

        # SALVAR TUDO
        print()
        print("=" * 80)
        print("RESUMO DOS SELETORES MAPEADOS")
        print("=" * 80)
        print()
        print(json.dumps(seletores_mapeados, indent=2, ensure_ascii=False))
        print()

        salvar_seletores(seletores_mapeados)

        print()
        print("=" * 80)
        print("PRÓXIMOS PASSOS")
        print("=" * 80)
        print()
        print("1. Revisar seletores_mapeados.json")
        print("2. Copiar seletores para config.py")
        print("3. Testar automação completa")
        print()

        input("Pressione ENTER para fechar o navegador...")

    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        await bot.fechar_navegador()

    return 0


if __name__ == '__main__':
    try:
        sys.exit(asyncio.run(mapear_interativo()))
    except KeyboardInterrupt:
        print("\n\n[CANCELADO]")
        sys.exit(0)
