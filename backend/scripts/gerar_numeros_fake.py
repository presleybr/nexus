"""
Gera números de WhatsApp FAKE (mas válidos) para cada cliente com boleto
Formato: 5567999XXXXX (únicos para teste)
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


def gerar_numeros_fake():
    """
    Gera números de WhatsApp fake mas válidos para cada cliente com boleto
    Formato: 5567999XXXXX (MS) - números sequenciais únicos
    """

    print("=" * 70)
    print("GERAÇÃO DE NÚMEROS FAKE PARA TESTE")
    print("=" * 70)

    # Buscar clientes com boletos pendentes e placeholder
    clientes = db.execute_query("""
        SELECT DISTINCT
            cf.id,
            cf.nome_completo,
            cf.cpf,
            cf.whatsapp
        FROM clientes_finais cf
        INNER JOIN boletos b ON b.cliente_final_id = cf.id
        WHERE cf.cliente_nexus_id = 2
        AND cf.whatsapp = '55679999999999'
        AND b.status_envio = 'nao_enviado'
        ORDER BY cf.nome_completo
    """)

    if not clientes:
        print("\n❌ Nenhum cliente encontrado com placeholder")
        return

    print(f"\n✅ Encontrados {len(clientes)} clientes para gerar números\n")
    print("GERANDO NÚMEROS FAKE (formato válido brasileiro):")
    print("-" * 70)

    stats = {
        'total': len(clientes),
        'atualizados': 0,
        'erros': 0
    }

    # Gerar números sequenciais: 5567999100001, 5567999100002, etc.
    base_numero = 5567999100000

    for idx, cliente in enumerate(clientes, 1):
        try:
            # Gerar número fake único
            numero_fake = str(base_numero + idx)

            # Atualizar no banco
            db.execute_update("""
                UPDATE clientes_finais
                SET whatsapp = %s, telefone_celular = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (numero_fake, numero_fake, cliente['id']))

            print(f"   {idx:2}. {cliente['nome_completo'][:40]:40} | {numero_fake}")
            stats['atualizados'] += 1

        except Exception as e:
            print(f"   ❌ Erro: {cliente['nome_completo']} - {str(e)}")
            stats['erros'] += 1

    print("\n" + "=" * 70)
    print("📊 RESUMO:")
    print("=" * 70)
    print(f"   Total: {stats['total']}")
    print(f"   ✅ Números gerados: {stats['atualizados']}")
    print(f"   ❌ Erros: {stats['erros']}")
    print("\n" + "=" * 70)
    print("📌 IMPORTANTE:")
    print("=" * 70)
    print("   ✅ Números gerados no formato brasileiro válido")
    print("   ✅ Cada cliente tem um número ÚNICO")
    print("   ✅ Formato: 5567999100001, 5567999100002, etc.")
    print("   ✅ Você pode alterar pelo CRM depois para números reais")
    print("   ✅ O sistema de disparo usará o número atualizado")
    print("\n   🚀 PRONTO PARA TESTAR DISPAROS!")
    print("=" * 70)

    # Verificar quantos ficaram prontos
    prontos = db.execute_query("""
        SELECT COUNT(*) as total
        FROM clientes_finais cf
        INNER JOIN boletos b ON b.cliente_final_id = cf.id
        WHERE cf.cliente_nexus_id = 2
        AND cf.whatsapp != '55679999999999'
        AND cf.whatsapp != '0000000000'
        AND b.status_envio = 'nao_enviado'
    """)

    total_prontos = prontos[0]['total'] if prontos else 0

    print(f"\n📊 CLIENTES PRONTOS PARA DISPARO: {total_prontos}")
    print("=" * 70)


if __name__ == '__main__':
    gerar_numeros_fake()
