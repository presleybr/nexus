"""
Script para criar boleto de teste para disparo individual
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import db

def criar_boleto_teste():
    print("=" * 60)
    print("CRIANDO BOLETO DE TESTE PARA DISPARO INDIVIDUAL")
    print("=" * 60)

    # Buscar cliente com WhatsApp
    cliente = db.execute_query("""
        SELECT id, nome_completo, whatsapp, cliente_nexus_id
        FROM clientes_finais
        WHERE cliente_nexus_id = 2
        AND whatsapp IS NOT NULL
        LIMIT 1
    """)

    if not cliente:
        print("[ERRO] Nenhum cliente encontrado com WhatsApp")
        return

    c = cliente[0]
    print(f"\n[OK] Cliente encontrado: {c['nome_completo']} (ID: {c['id']})")
    print(f"     WhatsApp: {c['whatsapp']}")

    # Criar boleto de teste
    boleto = db.execute_query("""
        INSERT INTO boletos (
            cliente_nexus_id,
            cliente_final_id,
            numero_boleto,
            valor_original,
            data_vencimento,
            data_emissao,
            mes_referencia,
            ano_referencia,
            numero_parcela,
            descricao,
            status,
            status_envio,
            pdf_filename,
            pdf_path,
            gerado_por
        ) VALUES (
            2,
            %s,
            %s,
            100.00,
            CURRENT_DATE + INTERVAL '7 days',
            CURRENT_DATE,
            11,
            2024,
            1,
            'Boleto de teste para disparo individual',
            'pendente',
            'nao_enviado',
            'boleto_teste.pdf',
            'D:/Nexus/automation/canopus/downloads/Danner/TESTE.pdf',
            'teste'
        ) RETURNING id
    """, (c['id'], f'TESTE-{c["id"]}-11-2024'))

    print(f"\n[OK] Boleto de teste criado!")
    print(f"     Boleto ID: {boleto[0]['id']}")
    print(f"     Número: TESTE-{c['id']}-11-2024")
    print(f"\n{'=' * 60}")
    print(f"SUCESSO! Cliente {c['nome_completo']} agora aparecerá na lista!")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    criar_boleto_teste()
