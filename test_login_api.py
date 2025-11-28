import requests
import json

url = 'http://localhost:5000/api/auth/login'
data = {
    'email': 'empresa1@nexus.com',
    'password': 'admin123'
}

print("Testando login API...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print("\n" + "="*60)

try:
    response = requests.post(url, json=data)

    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"\nResponse Text:")
    print(response.text)

    if response.status_code == 200:
        print("\nJSON Response:")
        print(json.dumps(response.json(), indent=2))

except Exception as e:
    print(f"Erro na requisicao: {e}")
    import traceback
    traceback.print_exc()
