#!/usr/bin/env python3
"""Script para testar login do Portal"""

import requests
import json

def testar_login():
    url = "http://localhost:5000/portal-consorcio/api/login"

    # Dados de login
    dados = {
        "email": "admin@portal.com",
        "senha": "admin123"
    }

    print("[INFO] Testando login do Portal Consórcio...")
    print(f"[INFO] URL: {url}")
    print(f"[INFO] Email: {dados['email']}")

    try:
        response = requests.post(url, json=dados)

        print(f"\n[INFO] Status Code: {response.status_code}")
        print(f"[INFO] Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n[SUCCESS] Login funcionando corretamente!")
            return True
        else:
            print("\n[ERROR] Login falhou!")
            return False

    except Exception as e:
        print(f"\n[ERROR] Erro ao testar login: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    testar_login()
