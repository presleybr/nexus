"""
Verifica clientes com boletos pendentes para disparo
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


def verificar_clientes():
    """Verifica clientes com boletos pendentes"""

    print("=" * 70)
    print("CLIENTES COM BOLETOS PENDENTES PARA DISPARO")
    print("=" * 70)

    # Buscar clientes com boletos pendentes
    query = """
    SELECT
        cf.id,
        cf.nome_completo,
        cf.whatsapp,
        cf.cpf,
        COUNT(b.id) as total_boletos,
        SUM(CASE WHEN b.status_envio = 'nao_enviado' THEN 1 ELSE 0 END) as boletos_pendentes
    FROM clientes_finais cf
    LEFT JOIN boletos b ON cf.id = b.cliente_final_id
    WHERE cf.cliente_nexus_id = 2
    GROUP BY cf.id, cf.nome_completo, cf.whatsapp, cf.cpf
    HAVING COUNT(b.id) > 0
    ORDER BY cf.nome_completo
    """

    clientes = db.execute_query(query)

    if not clientes:
        print('\n❌ Nenhum cliente com boletos encontrado')
        return

    print(f'\n📊 Total de clientes com boletos: {len(clientes)}\n')

    com_whatsapp = []
    sem_whatsapp = []
    com_pendentes = []

    print("CLIENTES:")
    print("-" * 70)

    for c in clientes:
        status = '✅' if c['whatsapp'] else '❌'
        pendentes_str = f" ({c['boletos_pendentes']} pendentes)" if c['boletos_pendentes'] > 0 else ''

        nome_truncado = c['nome_completo'][:35].ljust(35)
        whatsapp_str = (c['whatsapp'] or 'SEM WHATSAPP').ljust(15)

        print(f"{status} {nome_truncado} | {whatsapp_str} | Boletos: {c['total_boletos']}{pendentes_str}")

        if c['whatsapp']:
            com_whatsapp.append(c)
        else:
            sem_whatsapp.append(c)

        if c['boletos_pendentes'] and c['boletos_pendentes'] > 0:
            com_pendentes.append(c)

    print("\n" + "=" * 70)
    print("📈 RESUMO:")
    print("=" * 70)
    print(f"   Total de clientes: {len(clientes)}")
    print(f"   ✅ Com WhatsApp: {len(com_whatsapp)}")
    print(f"   ❌ Sem WhatsApp: {len(sem_whatsapp)}")
    print(f"   📤 Com boletos pendentes (prontos para enviar): {len(com_pendentes)}")

    # Detalhar clientes prontos para disparo
    if com_pendentes:
        print("\n" + "=" * 70)
        print("🚀 CLIENTES PRONTOS PARA DISPARO:")
        print("=" * 70)

        total_boletos_enviar = 0

        for c in com_pendentes:
            if c['whatsapp']:
                print(f"   ✅ {c['nome_completo'][:40]:40} | {c['whatsapp']:15} | {c['boletos_pendentes']} boleto(s)")
                total_boletos_enviar += c['boletos_pendentes']
            else:
                print(f"   ⚠️  {c['nome_completo'][:40]:40} | SEM WHATSAPP | {c['boletos_pendentes']} boleto(s)")

        print(f"\n   📊 Total de boletos a enviar: {total_boletos_enviar}")

    # Verificar se há boletos no banco
    print("\n" + "=" * 70)
    print("📄 BOLETOS NO BANCO:")
    print("=" * 70)

    boletos_query = """
    SELECT
        status_envio,
        COUNT(*) as total
    FROM boletos
    WHERE cliente_nexus_id = 2
    GROUP BY status_envio
    """

    boletos_stats = db.execute_query(boletos_query)

    for stat in boletos_stats:
        icon = "📤" if stat['status_envio'] == 'enviado' else "⏳"
        print(f"   {icon} {stat['status_envio']:15} : {stat['total']} boleto(s)")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    verificar_clientes()
