"""
Script de Automação - Disparo Automático de Boletos via WhatsApp
Executa a automação completa (Etapas 21-33)
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from services import automation_service
from models import ClienteNexus, Database


def executar_automacao_todas_empresas():
    """Executa automação completa para todas as empresas"""

    print("=" * 60)
    print("🤖 AUTOMAÇÃO COMPLETA - NEXUS CRM")
    print("   Geração e Disparo Automático de Boletos")
    print("=" * 60)

    Database.initialize_pool()

    try:
        empresas = ClienteNexus.listar_todos()

        print(f"\n📊 Total de empresas: {len(empresas)}\n")

        for i, empresa in enumerate(empresas, 1):
            print(f"\n{'='*60}")
            print(f"🏢 [{i}/{len(empresas)}] {empresa['nome_empresa']}")
            print(f"{'='*60}")

            # Verifica se WhatsApp está conectado
            if not empresa.get('whatsapp_conectado'):
                print("⚠️  WhatsApp não conectado. Pulando...")
                continue

            # Executa automação
            resultado = automation_service.executar_automacao_completa(empresa['id'])

            print(f"\n📊 Resultado:")
            print(f"   • Clientes processados: {resultado['clientes_processados']}")
            print(f"   • Boletos gerados: {resultado['boletos_gerados']}")
            print(f"   • Boletos enviados: {resultado['boletos_enviados']}")
            print(f"   • Erros: {resultado['erros']}")
            print(f"   • Tempo total: {resultado['tempo_total_segundos']}s")

        print("\n" + "=" * 60)
        print("✅ AUTOMAÇÃO CONCLUÍDA PARA TODAS AS EMPRESAS!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

    finally:
        Database.close_all_connections()


if __name__ == '__main__':
    executar_automacao_todas_empresas()
