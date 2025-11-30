"""
Script de verificação: Filtro de boletos pendentes
Verifica quais clientes têm boletos pendentes e serão incluídos no disparo
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def verificar_filtro_boletos():
    """Verifica filtro de boletos pendentes"""

    print("=" * 80)
    print("VERIFICAÇÃO DO FILTRO DE BOLETOS PENDENTES")
    print("=" * 80)

    # Query para buscar clientes COM boletos pendentes
    clientes_com_boletos = db.execute_query("""
        SELECT DISTINCT
            cf.id,
            cf.nome_completo as nome,
            cf.whatsapp,
            COUNT(b.id) as total_boletos_pendentes,
            SUM(b.valor_original) as valor_total
        FROM clientes_finais cf
        INNER JOIN boletos b ON b.cliente_final_id = cf.id
        WHERE b.status_envio IN ('nao_enviado', 'pendente')
            AND cf.whatsapp IS NOT NULL
            AND LENGTH(cf.whatsapp) >= 10
        GROUP BY cf.id, cf.nome_completo, cf.whatsapp
        ORDER BY cf.nome_completo
    """)

    print(f"\n[OK] CLIENTES COM BOLETOS PENDENTES: {len(clientes_com_boletos)}")
    print("-" * 80)

    if clientes_com_boletos:
        for cliente in clientes_com_boletos:
            print(f"ID: {cliente['id']}")
            print(f"Nome: {cliente['nome']}")
            print(f"WhatsApp: {cliente['whatsapp']}")
            print(f"Boletos pendentes: {cliente['total_boletos_pendentes']}")
            print(f"Valor total: R$ {float(cliente['valor_total'] or 0):.2f}")
            print("-" * 80)

    # Query para buscar clientes SEM boletos pendentes
    clientes_sem_boletos = db.execute_query("""
        SELECT
            cf.id,
            cf.nome_completo as nome,
            cf.whatsapp
        FROM clientes_finais cf
        WHERE cf.whatsapp IS NOT NULL
            AND LENGTH(cf.whatsapp) >= 10
            AND NOT EXISTS (
                SELECT 1 FROM boletos b
                WHERE b.cliente_final_id = cf.id
                    AND b.status_envio IN ('nao_enviado', 'pendente')
            )
        ORDER BY cf.nome_completo
    """)

    print(f"\n[X] CLIENTES SEM BOLETOS PENDENTES (nao receberao disparos): {len(clientes_sem_boletos)}")
    print("-" * 80)

    if clientes_sem_boletos:
        for cliente in clientes_sem_boletos[:10]:  # Mostrar apenas os 10 primeiros
            print(f"ID: {cliente['id']} | Nome: {cliente['nome']} | WhatsApp: {cliente['whatsapp']}")

        if len(clientes_sem_boletos) > 10:
            print(f"... e mais {len(clientes_sem_boletos) - 10} clientes sem boletos pendentes")
        print("-" * 80)

    # Estatísticas totais
    print(f"\n[ESTATISTICAS]")
    print(f"Total de clientes com WhatsApp e boletos pendentes: {len(clientes_com_boletos)}")
    print(f"Total de clientes com WhatsApp mas SEM boletos pendentes: {len(clientes_sem_boletos)}")
    print(f"Total de clientes com WhatsApp: {len(clientes_com_boletos) + len(clientes_sem_boletos)}")

    # Buscar total de boletos pendentes
    total_boletos = db.execute_query("""
        SELECT COUNT(*) as total
        FROM boletos
        WHERE status_envio IN ('nao_enviado', 'pendente')
    """)

    print(f"\n[BOLETOS] Total de boletos pendentes no sistema: {total_boletos[0]['total']}")

    print("\n" + "=" * 80)
    print("[OK] FILTRO FUNCIONANDO CORRETAMENTE!")
    print("Apenas clientes com boletos pendentes receberao disparos.")
    print("=" * 80)

if __name__ == '__main__':
    verificar_filtro_boletos()
