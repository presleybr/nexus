"""
Script para importar boletos de dezembro da pasta para o banco de dados
"""
import requests

print("\n" + "="*80)
print("IMPORTANDO BOLETOS DE DEZEMBRO PARA O BANCO DE DADOS")
print("="*80 + "\n")

# Fazer chamada POST para a API
url = "http://127.0.0.1:5000/api/automation/importar-boletos"

print("[INFO] Chamando API de importação...")
print(f"[URL] {url}\n")

try:
    response = requests.post(url, timeout=300)  # 5 minutos de timeout

    if response.status_code == 200:
        result = response.json()

        if result.get('success'):
            data = result.get('data', {})

            print("[OK] Importação concluída com sucesso!\n")
            print("="*80)
            print("ESTATÍSTICAS:")
            print("="*80)
            print(f"📁 Total de PDFs encontrados: {data.get('total_pdfs', 0)}")
            print(f"✅ Importados: {data.get('importados', 0)}")
            print(f"⏭️  Já existentes: {data.get('ja_existentes', 0)}")
            print(f"⚠️  Sem cliente: {data.get('sem_cliente', 0)}")
            print(f"❌ Erros: {data.get('erros', 0)}")
            print("="*80 + "\n")

            if data.get('importados', 0) > 0:
                print("✨ Boletos importados com sucesso para o banco!")
                print("   Agora os clientes devem aparecer com boletos na lista.\n")
        else:
            print(f"[ERRO] {result.get('error', 'Erro desconhecido')}")
    else:
        print(f"[ERRO] Status HTTP: {response.status_code}")
        print(f"[RESPOSTA] {response.text}")

except requests.exceptions.ConnectionError:
    print("[ERRO] Não foi possível conectar ao servidor.")
    print("       Verifique se o Flask está rodando em http://127.0.0.1:5000")
except requests.exceptions.Timeout:
    print("[ERRO] Timeout na requisição (mais de 5 minutos)")
except Exception as e:
    print(f"[ERRO] {e}")

print("\n")
