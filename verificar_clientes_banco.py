"""
Verificar quais clientes Nexus têm clientes finais cadastrados
"""

import sys
import os
import codecs

if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import Database, execute_query

def verificar_clientes():
    print("=" * 70)
    print("🔍 VERIFICAÇÃO DE CLIENTES NO BANCO")
    print("=" * 70)

    Database.initialize_pool()

    try:
        # 1. Listar todos os clientes Nexus
        print("\n📊 CLIENTES NEXUS CADASTRADOS:")
        print("-" * 70)

        query_nexus = """
            SELECT id, nome_empresa, whatsapp_numero
            FROM clientes_nexus
            WHERE ativo = true
            ORDER BY id
        """
        clientes_nexus = execute_query(query_nexus, fetch=True)

        if not clientes_nexus:
            print("❌ Nenhum cliente Nexus encontrado!")
            return

        for cn in clientes_nexus:
            print(f"\nID: {cn['id']} - {cn['nome_empresa']}")
            print(f"   WhatsApp: {cn.get('whatsapp_numero', 'Não cadastrado')}")

        # 2. Para cada cliente Nexus, contar clientes finais
        print("\n" + "=" * 70)
        print("👥 CLIENTES FINAIS POR EMPRESA:")
        print("-" * 70)

        query_count = """
            SELECT
                cn.id,
                cn.nome_empresa,
                COUNT(cf.id) as total_clientes,
                COUNT(CASE WHEN cf.whatsapp IS NOT NULL AND cf.whatsapp != '' THEN 1 END) as com_whatsapp
            FROM clientes_nexus cn
            LEFT JOIN clientes_finais cf ON cn.id = cf.cliente_nexus_id AND cf.ativo = true
            WHERE cn.ativo = true
            GROUP BY cn.id, cn.nome_empresa
            ORDER BY cn.id
        """

        resultado = execute_query(query_count, fetch=True)

        total_geral = 0
        total_com_whatsapp = 0

        for r in resultado:
            total_clientes = r['total_clientes']
            com_whatsapp = r['com_whatsapp']
            sem_whatsapp = total_clientes - com_whatsapp

            total_geral += total_clientes
            total_com_whatsapp += com_whatsapp

            print(f"\n🏢 {r['nome_empresa']} (ID: {r['id']})")
            print(f"   Total de clientes: {total_clientes}")
            print(f"   • Com WhatsApp: {com_whatsapp}")
            print(f"   • Sem WhatsApp: {sem_whatsapp}")

            if total_clientes == 0:
                print(f"   ⚠️  NENHUM CLIENTE CADASTRADO!")
            elif com_whatsapp == 0:
                print(f"   ⚠️  Nenhum cliente tem WhatsApp cadastrado!")

        # 3. Resumo geral
        print("\n" + "=" * 70)
        print("📊 RESUMO GERAL:")
        print("-" * 70)
        print(f"Total de clientes finais no sistema: {total_geral}")
        print(f"Clientes com WhatsApp cadastrado: {total_com_whatsapp}")
        print(f"Clientes sem WhatsApp: {total_geral - total_com_whatsapp}")

        if total_geral == 0:
            print("\n❌ PROBLEMA: Não há clientes finais cadastrados no sistema!")
            print("\n💡 SOLUÇÃO:")
            print("   1. Acesse o sistema via navegador")
            print("   2. Vá em 'Cadastro de Clientes'")
            print("   3. Importe ou cadastre os clientes finais")
            print("   4. Certifique-se de cadastrar os números de WhatsApp")
        elif total_com_whatsapp == 0:
            print("\n⚠️  PROBLEMA: Nenhum cliente tem WhatsApp cadastrado!")
            print("\n💡 SOLUÇÃO:")
            print("   1. Acesse o sistema via navegador")
            print("   2. Vá em 'Cadastro de Clientes'")
            print("   3. Edite os clientes e adicione os números de WhatsApp")
        else:
            print(f"\n✅ Sistema pronto para disparos!")
            print(f"   {total_com_whatsapp} clientes receberão boletos")

        # 4. Mostrar exemplos de clientes (se houver)
        if total_geral > 0:
            print("\n" + "=" * 70)
            print("📋 EXEMPLOS DE CLIENTES CADASTRADOS:")
            print("-" * 70)

            query_exemplos = """
                SELECT
                    cn.nome_empresa,
                    cf.nome_completo,
                    cf.whatsapp,
                    cf.cpf
                FROM clientes_finais cf
                JOIN clientes_nexus cn ON cf.cliente_nexus_id = cn.id
                WHERE cf.ativo = true
                ORDER BY cf.created_at DESC
                LIMIT 5
            """

            exemplos = execute_query(query_exemplos, fetch=True)

            for ex in exemplos:
                print(f"\n• {ex['nome_completo']}")
                print(f"  Empresa: {ex['nome_empresa']}")
                print(f"  WhatsApp: {ex.get('whatsapp') or 'NÃO CADASTRADO'}")
                print(f"  CPF: {ex.get('cpf', 'N/A')}")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

    finally:
        Database.close_all_connections()


if __name__ == '__main__':
    verificar_clientes()
