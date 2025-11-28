"""
Script para adicionar WhatsApps de teste aos clientes sem número
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def adicionar_whatsapp():
    print("="*60)
    print("ADICIONANDO WHATSAPP DE TESTE")
    print("="*60)

    # Buscar clientes sem WhatsApp
    clientes_sem_whatsapp = db.execute_query("""
        SELECT id, nome_completo, whatsapp
        FROM clientes_finais
        WHERE cliente_nexus_id = 2
        AND (whatsapp IS NULL OR whatsapp = '' OR LENGTH(whatsapp) < 10)
        AND ativo = true
    """)

    print(f"\nClientes sem WhatsApp: {len(clientes_sem_whatsapp) if clientes_sem_whatsapp else 0}")

    if not clientes_sem_whatsapp:
        print("Todos os clientes já têm WhatsApp!")
        return

    # WhatsApp de teste (número do empresário)
    whatsapp_teste = "556796600884"

    count = 0
    for cliente in clientes_sem_whatsapp[:10]:  # Apenas os primeiros 10 para teste
        db.execute_update("""
            UPDATE clientes_finais
            SET whatsapp = %s
            WHERE id = %s
        """, (whatsapp_teste, cliente['id']))

        print(f"[OK] WhatsApp adicionado: {cliente['nome_completo']} -> {whatsapp_teste}")
        count += 1

    print(f"\n[OK] Total atualizado: {count} clientes")
    print(f"WhatsApp de teste usado: {whatsapp_teste}")

if __name__ == '__main__':
    adicionar_whatsapp()
