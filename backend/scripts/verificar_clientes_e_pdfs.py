"""
Verifica clientes no banco e PDFs de boletos da Canopus
"""

import sys
import os
import io

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import db


def verificar_tudo():
    """Verifica clientes e boletos"""

    print("=" * 70)
    print("DIAGNÓSTICO COMPLETO: CLIENTES E BOLETOS")
    print("=" * 70)

    # 1. Verificar clientes no banco
    print("\n📊 1. CLIENTES NO BANCO PostgreSQL:")
    print("-" * 70)

    clientes_query = """
    SELECT
        id,
        nome_completo,
        whatsapp,
        cpf,
        created_at
    FROM clientes_finais
    WHERE cliente_nexus_id = 2
    ORDER BY nome_completo
    LIMIT 20
    """

    clientes = db.execute_query(clientes_query)

    if not clientes:
        print("❌ Nenhum cliente encontrado no banco!")
        print("   Você precisa importar os clientes da planilha primeiro.")
    else:
        print(f"✅ {len(clientes)} cliente(s) encontrado(s)\n")

        for idx, c in enumerate(clientes[:10], 1):  # Mostra só os primeiros 10
            whatsapp_str = c['whatsapp'] or 'SEM WHATSAPP'
            print(f"   {idx:2}. {c['nome_completo'][:35]:35} | {whatsapp_str:15} | CPF: {c['cpf']}")

        if len(clientes) > 10:
            print(f"   ... e mais {len(clientes) - 10} cliente(s)")

    # 2. Verificar boletos no banco
    print("\n" + "=" * 70)
    print("📄 2. BOLETOS NO BANCO PostgreSQL:")
    print("-" * 70)

    boletos_query = """
    SELECT COUNT(*) as total FROM boletos WHERE cliente_nexus_id = 2
    """

    boletos_count = db.execute_query(boletos_query)
    total_boletos = boletos_count[0]['total'] if boletos_count else 0

    if total_boletos == 0:
        print("❌ Nenhum boleto encontrado no banco!")
        print("   Os boletos precisam ser importados/gerados.")
    else:
        print(f"✅ {total_boletos} boleto(s) encontrado(s)")

        # Detalhes dos boletos
        boletos_stats = db.execute_query("""
        SELECT
            status_envio,
            COUNT(*) as total
        FROM boletos
        WHERE cliente_nexus_id = 2
        GROUP BY status_envio
        """)

        for stat in boletos_stats:
            icon = "📤" if stat['status_envio'] == 'enviado' else "⏳"
            print(f"   {icon} {stat['status_envio']:15} : {stat['total']} boleto(s)")

    # 3. Verificar PDFs da Canopus
    print("\n" + "=" * 70)
    print("📁 3. PDFs DE BOLETOS DA CANOPUS:")
    print("-" * 70)

    pasta_canopus = r'D:\Nexus\automation\canopus\downloads\Danner'

    if os.path.exists(pasta_canopus):
        pdfs = [f for f in os.listdir(pasta_canopus) if f.endswith('.pdf')]

        if pdfs:
            print(f"✅ {len(pdfs)} PDF(s) encontrado(s) em: {pasta_canopus}\n")

            # Mostra os primeiros 10 PDFs
            for idx, pdf in enumerate(pdfs[:10], 1):
                tamanho = os.path.getsize(os.path.join(pasta_canopus, pdf))
                tamanho_kb = tamanho / 1024
                print(f"   {idx:2}. {pdf[:50]:50} ({tamanho_kb:.1f} KB)")

            if len(pdfs) > 10:
                print(f"   ... e mais {len(pdfs) - 10} PDF(s)")
        else:
            print(f"❌ Nenhum PDF encontrado em: {pasta_canopus}")
    else:
        print(f"❌ Pasta não existe: {pasta_canopus}")

    # 4. Resumo e próximos passos
    print("\n" + "=" * 70)
    print("🎯 RESUMO E PRÓXIMOS PASSOS:")
    print("=" * 70)

    tem_clientes = len(clientes) > 0 if clientes else False
    tem_boletos_banco = total_boletos > 0
    tem_pdfs = os.path.exists(pasta_canopus) and len([f for f in os.listdir(pasta_canopus) if f.endswith('.pdf')]) > 0

    if not tem_clientes:
        print("❌ PASSO 1: Importar clientes da planilha")
        print("   → Execute o script de importação de clientes")
    else:
        print("✅ PASSO 1: Clientes já importados")

    if not tem_boletos_banco and tem_pdfs:
        print("⚠️  PASSO 2: Importar boletos dos PDFs para o banco")
        print("   → Os PDFs existem, mas não estão registrados no banco")
        print("   → Precisamos criar registros de boletos no PostgreSQL")
    elif tem_boletos_banco:
        print("✅ PASSO 2: Boletos já registrados no banco")
    else:
        print("❌ PASSO 2: Não há PDFs nem boletos no banco")

    if tem_clientes and tem_boletos_banco:
        print("✅ PASSO 3: Pronto para disparar boletos!")
        print("   → Você pode usar o sistema de disparos agora")
    else:
        print("⏳ PASSO 3: Aguardando passos anteriores")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    verificar_tudo()
