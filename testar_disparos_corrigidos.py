"""
Script de Teste - Verificar Correção dos Disparos
Testa se a query está retornando clientes corretamente após a correção
"""

import sys
import os
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import ClienteFinal, Database
from models.database import execute_query

def testar_query_clientes():
    """Testa se a query com limit=None está funcionando"""

    print("=" * 60)
    print("🧪 TESTE DE CORREÇÃO - QUERY DE CLIENTES")
    print("=" * 60)

    Database.initialize_pool()

    try:
        # 1. Buscar todos os clientes Nexus
        query_nexus = "SELECT id, nome_empresa FROM clientes_nexus WHERE ativo = true LIMIT 1"
        clientes_nexus = execute_query(query_nexus, fetch=True)

        if not clientes_nexus:
            print("\n❌ Nenhum cliente Nexus encontrado no banco")
            return

        cliente_nexus_id = clientes_nexus[0]['id']
        nome_empresa = clientes_nexus[0]['nome_empresa']

        print(f"\n✅ Cliente Nexus encontrado: {nome_empresa} (ID: {cliente_nexus_id})")

        # 2. Testar query COM limite (método antigo)
        print("\n" + "=" * 60)
        print("📊 Teste 1: Query COM LIMITE (limit=100)")
        print("=" * 60)

        clientes_com_limite = ClienteFinal.listar_por_cliente_nexus(
            cliente_nexus_id,
            limit=100
        )

        print(f"✅ Retornou {len(clientes_com_limite)} clientes")
        if clientes_com_limite:
            print(f"\n📋 Exemplo do primeiro cliente:")
            cliente = clientes_com_limite[0]
            print(f"   • Nome: {cliente.get('nome', 'N/A')}")
            print(f"   • WhatsApp: {cliente.get('whatsapp', 'NÃO CADASTRADO')}")
            print(f"   • CPF: {cliente.get('cpf', 'N/A')}")

        # 3. Testar query SEM limite (método corrigido)
        print("\n" + "=" * 60)
        print("📊 Teste 2: Query SEM LIMITE (limit=None) - CORREÇÃO APLICADA")
        print("=" * 60)

        clientes_sem_limite = ClienteFinal.listar_por_cliente_nexus(
            cliente_nexus_id,
            limit=None
        )

        print(f"✅ Retornou {len(clientes_sem_limite)} clientes")

        if not clientes_sem_limite:
            print("\n⚠️  PROBLEMA: Query não retornou nenhum cliente!")
            print("   Verifique se há clientes cadastrados no banco.")
            return

        # 4. Verificar quantos clientes TÊM WhatsApp cadastrado
        print("\n" + "=" * 60)
        print("📱 Análise: Clientes com WhatsApp Cadastrado")
        print("=" * 60)

        com_whatsapp = [c for c in clientes_sem_limite if c.get('whatsapp')]
        sem_whatsapp = [c for c in clientes_sem_limite if not c.get('whatsapp')]

        print(f"\n✅ Com WhatsApp: {len(com_whatsapp)}")
        print(f"❌ Sem WhatsApp: {len(sem_whatsapp)}")

        if com_whatsapp:
            print(f"\n📋 Exemplos de clientes COM WhatsApp:")
            for i, cliente in enumerate(com_whatsapp[:3], 1):
                print(f"   {i}. {cliente.get('nome', 'N/A')} - {cliente.get('whatsapp')}")

        if sem_whatsapp:
            print(f"\n⚠️  Clientes SEM WhatsApp (não receberão boletos):")
            for i, cliente in enumerate(sem_whatsapp[:5], 1):
                print(f"   {i}. {cliente.get('nome', 'N/A')}")

        # 5. Resumo final
        print("\n" + "=" * 60)
        print("📊 RESUMO DO TESTE")
        print("=" * 60)

        if clientes_sem_limite and com_whatsapp:
            print("\n✅ CORREÇÃO FUNCIONANDO!")
            print(f"   • Query retorna {len(clientes_sem_limite)} clientes")
            print(f"   • {len(com_whatsapp)} clientes receberão boletos")
            print(f"   • {len(sem_whatsapp)} clientes precisam cadastrar WhatsApp")
        elif clientes_sem_limite and not com_whatsapp:
            print("\n⚠️  ATENÇÃO!")
            print(f"   • Query funciona ({len(clientes_sem_limite)} clientes encontrados)")
            print(f"   • MAS nenhum cliente tem WhatsApp cadastrado")
            print(f"   • Cadastre os números de WhatsApp dos clientes")
        else:
            print("\n❌ PROBLEMA AINDA EXISTE")
            print("   • Query não está retornando clientes")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

    finally:
        Database.close_all_connections()


if __name__ == '__main__':
    testar_query_clientes()
