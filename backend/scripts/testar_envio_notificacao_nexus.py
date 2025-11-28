"""
Testa envio REAL de notificação para o número da Nexus
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whatsapp_service import whatsapp_service
from models.cliente import ClienteNexus

print("\n" + "="*80)
print("TESTE DE NOTIFICACAO PARA NEXUS")
print("="*80 + "\n")

NUMERO_NEXUS = '556796600884'
CLIENTE_NEXUS_ID = 2

print(f"[1] Numero destino: {NUMERO_NEXUS}")
print(f"[2] Verificando conexão WhatsApp...\n")

# Verifica se está conectado
conectado = whatsapp_service.verificar_conexao(CLIENTE_NEXUS_ID)
print(f"WhatsApp conectado: {conectado}\n")

if not conectado:
    print("[ERRO] WhatsApp nao esta conectado!")
    print("Conecte o WhatsApp antes de testar.\n")
    print("="*80 + "\n")
    sys.exit(1)

# Busca dados do cliente
cliente_nexus = ClienteNexus.buscar_por_id(CLIENTE_NEXUS_ID)
nome_empresa = cliente_nexus.get('nome_empresa', 'Empresa Teste') if cliente_nexus else 'Empresa Teste'

print(f"[3] Enviando mensagem de INICIO para {NUMERO_NEXUS}...\n")

# Mensagem de início (mesma do sistema)
mensagem_inicio = f"""
Olá! Seus boletos foram gerados com sucesso.

📊 Total de boletos: 30 (TESTE)
⏰ Iniciando disparo automático...

Sistema Nexus - Aqui seu tempo vale ouro
""".strip()

try:
    resultado = whatsapp_service.enviar_mensagem(
        NUMERO_NEXUS,
        mensagem_inicio,
        CLIENTE_NEXUS_ID
    )

    if resultado.get('sucesso'):
        print("[OK] Mensagem de INICIO enviada com sucesso!")
        print(f"ID da mensagem: {resultado.get('id_mensagem')}")
        print(f"Timestamp: {resultado.get('timestamp')}\n")
    else:
        print(f"[ERRO] Falha ao enviar mensagem de inicio:")
        print(f"Erro: {resultado.get('erro')}\n")

except Exception as e:
    print(f"[ERRO] Excecao ao enviar mensagem:")
    print(f"{str(e)}\n")

# Aguarda um pouco
import time
print("Aguardando 3 segundos...\n")
time.sleep(3)

print(f"[4] Enviando mensagem de FIM para {NUMERO_NEXUS}...\n")

# Mensagem final (mesma do sistema)
mensagem_final = """
✅ *DISPAROS FINALIZADOS COM SUCESSO!*

🕐 *Finalizado em:* 26/11/2025 às 15:30:00
⏱️ *Tempo total:* 15.5 minutos (TESTE)

📊 *Estatísticas do Disparo:*
• Total processado: 30 clientes
• Boletos enviados: 29
• Taxa de sucesso: 96.7%

📅 *Próximo disparo automático:*
• Data: 26/12/2025
• Os boletos serão gerados e enviados automaticamente

✨ *Nexus - Aqui seu tempo vale ouro!*
Obrigado por confiar em nossos serviços.
""".strip()

try:
    resultado = whatsapp_service.enviar_mensagem(
        NUMERO_NEXUS,
        mensagem_final,
        CLIENTE_NEXUS_ID
    )

    if resultado.get('sucesso'):
        print("[OK] Mensagem de FIM enviada com sucesso!")
        print(f"ID da mensagem: {resultado.get('id_mensagem')}")
        print(f"Timestamp: {resultado.get('timestamp')}\n")
    else:
        print(f"[ERRO] Falha ao enviar mensagem final:")
        print(f"Erro: {resultado.get('erro')}\n")

except Exception as e:
    print(f"[ERRO] Excecao ao enviar mensagem final:")
    print(f"{str(e)}\n")

print("="*80)
print("TESTE CONCLUIDO")
print("="*80)
print("\nVerifique seu WhatsApp no numero 67 9660-0884")
print("Voce deve ter recebido 2 mensagens:")
print("  1. Mensagem de INICIO (com emoji de relogio)")
print("  2. Mensagem de FIM (com estatisticas)\n")
print("="*80 + "\n")
