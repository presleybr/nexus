"""
Atualiza WhatsApp dos 36 clientes usando match com clientes antigos que têm números REAIS
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


def atualizar_whatsapp_por_nome():
    """
    Busca clientes antigos (com WhatsApp real) e atualiza os novos (com placeholder)
    fazendo match por NOME
    """

    print("=" * 70)
    print("ATUALIZAÇÃO DE WHATSAPP POR MATCH DE NOME")
    print("=" * 70)

    # Buscar clientes COM números reais (os antigos importados da planilha)
    clientes_com_numero = db.execute_query("""
        SELECT nome_completo, whatsapp, cpf
        FROM clientes_finais
        WHERE cliente_nexus_id = 2
        AND whatsapp IS NOT NULL
        AND whatsapp != '55679999999999'
        AND whatsapp != '0000000000'
        AND whatsapp != ''
        ORDER BY nome_completo
    """)

    print(f"\n✅ Encontrados {len(clientes_com_numero)} clientes com números reais\n")

    # Buscar clientes COM placeholder (os novos importados dos PDFs)
    clientes_placeholder = db.execute_query("""
        SELECT id, nome_completo, cpf
        FROM clientes_finais
        WHERE cliente_nexus_id = 2
        AND whatsapp = '55679999999999'
        ORDER BY nome_completo
    """)

    print(f"✅ Encontrados {len(clientes_placeholder)} clientes com placeholder\n")

    stats = {
        'total': len(clientes_placeholder),
        'atualizados': 0,
        'nao_encontrado': 0
    }

    # Para cada cliente com placeholder, tentar encontrar match por nome
    for cliente_new in clientes_placeholder:
        nome_new = cliente_new['nome_completo'].strip().upper()

        # Buscar match EXATO de nome
        match_found = None
        for cliente_old in clientes_com_numero:
            nome_old = cliente_old['nome_completo'].strip().upper()

            if nome_new == nome_old:
                match_found = cliente_old
                break

        if match_found:
            whatsapp_real = match_found['whatsapp']

            # Atualizar
            db.execute_update("""
                UPDATE clientes_finais
                SET whatsapp = %s, telefone_celular = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (whatsapp_real, whatsapp_real, cliente_new['id']))

            print(f"✅ {cliente_new['nome_completo'][:40]:40} | {whatsapp_real}")
            stats['atualizados'] += 1
        else:
            print(f"⚠️  {cliente_new['nome_completo'][:40]:40} | SEM MATCH")
            stats['nao_encontrado'] += 1

    print("\n" + "=" * 70)
    print("📊 RESUMO:")
    print("=" * 70)
    print(f"   Total processados: {stats['total']}")
    print(f"   ✅ Atualizados: {stats['atualizados']}")
    print(f"   ⚠️  Não encontrados: {stats['nao_encontrado']}")
    print("=" * 70)


if __name__ == '__main__':
    atualizar_whatsapp_por_nome()
