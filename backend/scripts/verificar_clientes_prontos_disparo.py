"""
Verifica quais clientes estão PRONTOS para receber disparos
Filtra apenas números REAIS (não placeholders)
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


def verificar_clientes_prontos():
    """Verifica clientes com boletos pendentes e números REAIS"""

    print("=" * 70)
    print("CLIENTES PRONTOS PARA DISPARO (NÚMEROS REAIS)")
    print("=" * 70)

    # Buscar clientes com boletos pendentes e números REAIS
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
    AND cf.whatsapp IS NOT NULL
    AND cf.whatsapp != ''
    AND cf.whatsapp != '55679999999999'
    AND cf.whatsapp != '0000000000'
    AND cf.ativo = true
    GROUP BY cf.id, cf.nome_completo, cf.whatsapp, cf.cpf
    HAVING COUNT(b.id) > 0
    ORDER BY cf.nome_completo
    """

    clientes = db.execute_query(query)

    if not clientes:
        print('\n❌ Nenhum cliente com números válidos encontrado')
        return

    print(f'\n📊 Total de clientes com WhatsApp REAL: {len(clientes)}\n')

    com_pendentes = []

    print("CLIENTES COM NÚMEROS REAIS:")
    print("-" * 70)

    for c in clientes:
        pendentes_str = f" ({c['boletos_pendentes']} pendentes)" if c['boletos_pendentes'] > 0 else ''

        nome_truncado = c['nome_completo'][:35].ljust(35)
        whatsapp_str = c['whatsapp'].ljust(15)

        print(f"✅ {nome_truncado} | {whatsapp_str} | Boletos: {c['total_boletos']}{pendentes_str}")

        if c['boletos_pendentes'] and c['boletos_pendentes'] > 0:
            com_pendentes.append(c)

    print("\n" + "=" * 70)
    print("📈 RESUMO:")
    print("=" * 70)
    print(f"   Total de clientes com WhatsApp real: {len(clientes)}")
    print(f"   📤 Clientes com boletos pendentes: {len(com_pendentes)}")

    # Detalhar clientes prontos para disparo
    if com_pendentes:
        print("\n" + "=" * 70)
        print("🚀 PRONTOS PARA DISPARO AGORA:")
        print("=" * 70)

        total_boletos_enviar = 0

        for c in com_pendentes:
            print(f"   ✅ {c['nome_completo'][:40]:40} | {c['whatsapp']:15} | {c['boletos_pendentes']} boleto(s)")
            total_boletos_enviar += c['boletos_pendentes']

        print(f"\n   📊 Total de boletos a enviar: {total_boletos_enviar}")
        print(f"   ⏱️  Tempo estimado: {total_boletos_enviar * 10 / 60:.1f} minutos (10s por cliente)")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    verificar_clientes_prontos()
