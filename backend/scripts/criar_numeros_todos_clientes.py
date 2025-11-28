"""
Criar números de notificação para todos os clientes nexus
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def criar_numeros():
    print("=" * 60)
    print("CRIANDO NÚMEROS DE NOTIFICAÇÃO PARA TODOS OS CLIENTES")
    print("=" * 60)

    # Número padrão para todos
    whatsapp_padrao = "556796600884"

    # Buscar todos os clientes nexus
    clientes = db.execute_query("SELECT id, nome_empresa FROM clientes_nexus ORDER BY id")

    for cliente in clientes:
        cliente_id = cliente['id']
        nome_empresa = cliente['nome_empresa']

        # Verificar se já tem número cadastrado
        existe = db.execute_query(
            "SELECT id FROM numeros_notificacao WHERE cliente_nexus_id = %s",
            (cliente_id,)
        )

        if existe:
            print(f"[SKIP] Cliente {cliente_id} ({nome_empresa}) já tem número cadastrado")
        else:
            # Criar número
            db.execute_update("""
                INSERT INTO numeros_notificacao (cliente_nexus_id, nome, whatsapp)
                VALUES (%s, %s, %s)
            """, (cliente_id, f"Empresário - {nome_empresa}", whatsapp_padrao))

            print(f"[OK] Número criado para cliente {cliente_id} ({nome_empresa})")

    print("\n" + "=" * 60)
    print("CONCLUÍDO!")
    print("=" * 60)

    # Mostrar todos os números cadastrados
    print("\nNúmeros cadastrados:")
    numeros = db.execute_query("""
        SELECT nn.id, nn.nome, nn.whatsapp, cn.nome_empresa
        FROM numeros_notificacao nn
        JOIN clientes_nexus cn ON nn.cliente_nexus_id = cn.id
        ORDER BY nn.id
    """)

    for n in numeros:
        print(f"  ID {n['id']}: {n['nome']} ({n['nome_empresa']}) - {n['whatsapp']}")

if __name__ == '__main__':
    criar_numeros()
