"""
Testa envio de notificação para AMBOS os números da Nexus
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whatsapp_service import whatsapp_service

print("\n" + "="*80)
print("TESTE DE NOTIFICACAO PARA AMBOS OS NUMEROS")
print("="*80 + "\n")

NUMEROS_NEXUS = ['556796600884', '556798905585']
CLIENTE_NEXUS_ID = 2

print(f"[INFO] Numeros destino:")
for num in NUMEROS_NEXUS:
    print(f"  - {num}")
print()

# Verifica se está conectado
conectado = whatsapp_service.verificar_conexao(CLIENTE_NEXUS_ID)
print(f"WhatsApp conectado: {conectado}\n")

if not conectado:
    print("[ERRO] WhatsApp nao esta conectado!")
    print("Conecte o WhatsApp antes de testar.\n")
    print("="*80 + "\n")
    sys.exit(1)

# Mensagem de teste
mensagem_teste = """🧪 *TESTE DE NOTIFICACAO*

📊 Total de boletos: 25 (TESTE)
⏰ Iniciando disparo automático...

Sistema Nexus - Aqui seu tempo vale ouro"""

print(f"[INFO] Enviando mensagem de teste...\n")

for i, numero in enumerate(NUMEROS_NEXUS, 1):
    print(f"[{i}/2] Enviando para {numero}...")

    try:
        resultado = whatsapp_service.enviar_mensagem(
            numero,
            mensagem_teste,
            CLIENTE_NEXUS_ID
        )

        if resultado.get('sucesso'):
            print(f"  ✅ Enviado com sucesso!")
            print(f"  ID: {resultado.get('id_mensagem')}")
        else:
            print(f"  ❌ ERRO: {resultado.get('erro')}")

    except Exception as e:
        print(f"  ❌ EXCECAO: {str(e)}")

    print()

print("="*80)
print("TESTE CONCLUIDO")
print("="*80)
print("\nVerifique os WhatsApps:")
print("  1. 67 9660-0884")
print("  2. 67 9890-5585")
print("\nAmbos devem ter recebido a mensagem de teste.\n")
print("="*80 + "\n")
