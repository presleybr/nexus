"""
Script para verificar boletos no banco de dados
"""

import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.models.database import db


def verificar_boletos():
    """Verifica boletos no banco de dados"""
    print("=" * 80)
    print("VERIFICACAO DE BOLETOS NO BANCO DE DADOS")
    print("=" * 80)

    try:
        # Total de boletos
        total = db.execute_query("SELECT COUNT(*) as total FROM boletos", ())
        print(f"\n[INFO] Total de boletos: {total[0]['total']}")

        # Boletos por status
        por_status = db.execute_query("""
            SELECT status, COUNT(*) as qtd
            FROM boletos
            GROUP BY status
        """, ())

        if por_status:
            print("\n[INFO] Boletos por status:")
            for row in por_status:
                print(f"  - {row['status']}: {row['qtd']}")

        # Boletos por status de envio
        por_envio = db.execute_query("""
            SELECT status_envio, COUNT(*) as qtd
            FROM boletos
            GROUP BY status_envio
        """, ())

        if por_envio:
            print("\n[INFO] Boletos por status de envio:")
            for row in por_envio:
                print(f"  - {row['status_envio']}: {row['qtd']}")

        # Últimos 5 boletos
        ultimos = db.execute_query("""
            SELECT b.id, b.numero_boleto, b.valor_original, b.data_vencimento,
                   b.status, b.status_envio, cf.nome_completo
            FROM boletos b
            LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
            ORDER BY b.created_at DESC
            LIMIT 5
        """, ())

        if ultimos:
            print("\n[INFO] Ultimos 5 boletos:")
            print("-" * 80)
            for boleto in ultimos:
                print(f"ID: {boleto['id']} | Cliente: {boleto.get('nome_completo', 'N/A')}")
                print(f"Numero: {boleto['numero_boleto']} | Valor: R$ {boleto['valor_original']}")
                print(f"Vencimento: {boleto['data_vencimento']} | Status: {boleto['status']}/{boleto['status_envio']}")
                print("-" * 80)
        else:
            print("\n[AVISO] Nenhum boleto encontrado no banco de dados!")

        # Total de clientes finais
        clientes = db.execute_query("SELECT COUNT(*) as total FROM clientes_finais", ())
        print(f"\n[INFO] Total de clientes finais: {clientes[0]['total']}")

    except Exception as e:
        print(f"\n[ERRO] Erro ao verificar boletos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    verificar_boletos()
