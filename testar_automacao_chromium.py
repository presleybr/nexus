#!/usr/bin/env python3
"""
Script de teste para verificar se a automação Chromium está funcionando
"""
import sys
from pathlib import Path

# Adicionar paths
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("TESTE DE AUTOMAÇÃO CHROMIUM - CANOPUS")
print("=" * 80)

# 1. Verificar importações
print("\n1️⃣ Verificando importações...")
try:
    from automation.canopus.canopus_automation import CanopusAutomation
    print("   ✅ CanopusAutomation importado com sucesso")
except ImportError as e:
    print(f"   ❌ Erro ao importar CanopusAutomation: {e}")
    sys.exit(1)

try:
    from automation.canopus.canopus_config import CanopusConfig
    print("   ✅ CanopusConfig importado com sucesso")
except ImportError as e:
    print(f"   ❌ Erro ao importar CanopusConfig: {e}")
    sys.exit(1)

# 2. Verificar Playwright
print("\n2️⃣ Verificando Playwright...")
try:
    import playwright
    print(f"   ✅ Playwright instalado - versão: {playwright.__version__}")
except ImportError:
    print("   ❌ Playwright não instalado!")
    print("   Execute: pip install playwright")
    print("   E depois: playwright install chromium")
    sys.exit(1)

# 3. Verificar se Chromium está instalado
print("\n3️⃣ Verificando Chromium...")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        # Tentar obter o caminho do Chromium
        browser_type = p.chromium
        print("   ✅ Chromium encontrado!")
        print(f"   📁 Executável: {browser_type.executable_path}")
except Exception as e:
    print(f"   ❌ Chromium não encontrado: {e}")
    print("   Execute: playwright install chromium")
    sys.exit(1)

# 4. Verificar banco de dados e credenciais
print("\n4️⃣ Verificando banco de dados...")
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = 'postgresql://nexus_user:nc68h5fdIbK8ZGdcqWcMo7aYHxhDSffN@dpg-d4kldk0gjchc73a8hm7g-a.oregon-postgres.render.com/nexus_crm_14w2'

try:
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()
    print("   ✅ Conectado ao banco do Render")

    # Verificar clientes
    cur.execute("SELECT COUNT(*) as total FROM clientes_finais WHERE ponto_venda = '24627' AND ativo = TRUE")
    total_clientes = cur.fetchone()['total']
    print(f"   📊 Total de clientes ativos (PV 24627): {total_clientes}")

    # Verificar credenciais
    cur.execute("SELECT COUNT(*) as total FROM credenciais_canopus WHERE ponto_venda = '24627' AND ativo = TRUE")
    tem_credenciais = cur.fetchone()['total']

    if tem_credenciais > 0:
        print(f"   ✅ Credenciais Canopus configuradas (PV 24627)")
    else:
        print(f"   ⚠️ ATENÇÃO: Nenhuma credencial configurada para PV 24627!")
        print(f"   Execute: python configurar_credenciais_canopus_render.py")

    cur.close()
    conn.close()

except Exception as e:
    print(f"   ❌ Erro ao conectar ao banco: {e}")
    sys.exit(1)

# 5. Verificar paths de download
print("\n5️⃣ Verificando paths de download...")
import os

download_base_dir = os.getenv('DOWNLOAD_BASE_DIR')
if download_base_dir:
    print(f"   ✅ DOWNLOAD_BASE_DIR configurado: {download_base_dir}")
else:
    # Usar path padrão relativo
    default_path = Path(__file__).parent / 'automation' / 'canopus' / 'downloads'
    print(f"   ⚠️ DOWNLOAD_BASE_DIR não configurado, usando padrão:")
    print(f"   📁 {default_path}")

    # Criar se não existir
    default_path.mkdir(parents=True, exist_ok=True)
    print(f"   ✅ Pasta criada/verificada")

# 6. Teste rápido de abertura do navegador
print("\n6️⃣ Teste de abertura do Chromium (10 segundos)...")
print("   Abrindo Chromium em modo headless para teste...")

try:
    import asyncio
    from automation.canopus.canopus_automation import CanopusAutomation

    async def teste_chromium():
        async with CanopusAutomation(headless=True) as bot:
            print("   ✅ Chromium aberto com sucesso!")
            print("   Aguardando 3 segundos...")
            await asyncio.sleep(3)
            print("   ✅ Chromium fechado")

    asyncio.run(teste_chromium())

except Exception as e:
    print(f"   ❌ Erro ao abrir Chromium: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 80)
print("\n🚀 A automação está pronta para funcionar!")
print("\nPróximos passos:")
print("1. Certifique-se de que as credenciais estão configuradas")
print("2. Acesse o frontend e clique em 'Iniciar Download' (ETAPA 3)")
print("3. Monitore os logs para ver o progresso")
print("\n" + "=" * 80)
