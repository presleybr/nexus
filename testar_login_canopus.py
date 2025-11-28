#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste de login no Canopus
Testa se o login está funcionando com as credenciais corretas
"""
import sys
import asyncio
from pathlib import Path

# Adicionar paths
backend_path = Path(__file__).resolve().parent / 'backend'
root_path = Path(__file__).resolve().parent

sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(root_path))

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

async def testar_login():
    """Testa login no Canopus"""
    print("=" * 80)
    print("TESTE DE LOGIN NO CANOPUS")
    print("=" * 80)

    # Importar automação
    from automation.canopus.canopus_automation import CanopusAutomation

    # Credenciais
    ponto_venda = "24627"
    usuario_login = ponto_venda.zfill(10)  # 0000024627
    senha = "Sonhorealizado2!"
    codigo_empresa = "0101"

    print(f"\n📋 Dados do teste:")
    print(f"   Ponto de Venda: {ponto_venda}")
    print(f"   Usuário (login): {usuario_login}")
    print(f"   Senha: {'*' * len(senha)}")
    print(f"   Código Empresa: {codigo_empresa}")
    print()

    # Testar em modo NÃO headless para você ver o que acontece
    headless = False

    print(f"🌐 Abrindo Chromium (headless={headless})...")
    print("   IMPORTANTE: O navegador vai abrir na sua tela!")
    print()

    try:
        async with CanopusAutomation(headless=headless) as bot:
            print("✅ Chromium aberto!\n")

            print("🔐 Tentando fazer login...")
            login_ok = await bot.login(
                usuario=usuario_login,
                senha=senha,
                codigo_empresa=codigo_empresa,
                ponto_venda=ponto_venda
            )

            if login_ok:
                print("\n" + "=" * 80)
                print("✅ LOGIN REALIZADO COM SUCESSO!")
                print("=" * 80)
                print("\nO navegador vai ficar aberto por 10 segundos para você ver...")
                await asyncio.sleep(10)
                return True
            else:
                print("\n" + "=" * 80)
                print("❌ FALHA NO LOGIN")
                print("=" * 80)
                print("\nVerifique:")
                print("  1. A senha está correta?")
                print("  2. O usuário está correto?")
                print("  3. O sistema Canopus está acessível?")
                print("\nO navegador vai ficar aberto por 30 segundos para você investigar...")
                await asyncio.sleep(30)
                return False

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ERRO DURANTE O TESTE")
        print("=" * 80)
        print(f"\nErro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n⚠️  ATENÇÃO: Este script vai abrir o navegador Chromium na sua tela!")
    print("    Você poderá ver exatamente o que está acontecendo.")
    print()
    input("Pressione ENTER para continuar...")
    print()

    resultado = asyncio.run(testar_login())

    print("\n" + "=" * 80)
    if resultado:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("\nO login funcionou! O problema pode estar no ambiente do Render.")
    else:
        print("❌ TESTE FALHOU!")
        print("\nO login não funcionou. Verifique as credenciais e tente novamente.")
    print("=" * 80)
