"""
Script de Automação - Geração de Boletos
Pode ser executado standalone ou via cron/scheduler
"""

import sys
import os

# Adiciona o backend ao path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from services import automation_service
from models import ClienteNexus, Database


def gerar_boletos_todas_empresas():
    """Gera boletos para todas as empresas cadastradas"""

    print("🚀 Iniciando geração de boletos...")

    Database.initialize_pool()

    try:
        # Busca todas as empresas
        empresas = ClienteNexus.listar_todos()

        print(f"📊 Encontradas {len(empresas)} empresas")

        for empresa in empresas:
            print(f"\n🏢 Processando: {empresa['nome_empresa']}")

            resultado = automation_service.gerar_boletos_sem_enviar(empresa['id'])

            print(f"✅ {resultado['total_gerados']} boletos gerados")
            print(f"📁 Pasta: {resultado['pasta']}")

        print("\n✅ Geração concluída para todas as empresas!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    finally:
        Database.close_all_connections()


if __name__ == '__main__':
    gerar_boletos_todas_empresas()
