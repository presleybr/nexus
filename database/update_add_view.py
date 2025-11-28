"""
Script para adicionar a VIEW view_dashboard_cliente ao banco de dados
"""

import sys
import os

# Adiciona o backend ao path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from models.database import Database, execute_query

def criar_view_dashboard():
    """Cria a VIEW view_dashboard_cliente"""

    print("=" * 60)
    print("🔧 CRIANDO VIEW DASHBOARD DO CLIENTE")
    print("=" * 60)

    try:
        Database.initialize_pool()
        print("✅ Pool de conexões inicializado")

        # SQL da VIEW
        sql_view = """
        CREATE OR REPLACE VIEW view_dashboard_cliente AS
        SELECT
            cn.id as cliente_nexus_id,
            cn.nome_empresa,
            cn.cnpj,
            cn.whatsapp_numero,
            cn.email_contato,

            -- Estatísticas de boletos
            COUNT(DISTINCT b.id) as total_boletos,
            COUNT(DISTINCT CASE WHEN b.status_envio = 'enviado' THEN b.id END) as boletos_enviados,
            COUNT(DISTINCT CASE WHEN b.status_envio = 'pendente' THEN b.id END) as boletos_pendentes,
            COUNT(DISTINCT CASE WHEN b.vencimento < CURRENT_DATE AND b.status_envio != 'pago' THEN b.id END) as boletos_vencidos,
            COUNT(DISTINCT CASE WHEN b.status_envio = 'pago' THEN b.id END) as boletos_pagos,

            -- Valores
            COALESCE(SUM(b.valor), 0) as valor_total,
            COALESCE(SUM(CASE WHEN b.status_envio = 'pago' THEN b.valor ELSE 0 END), 0) as valor_pago,
            COALESCE(SUM(CASE WHEN b.status_envio = 'pendente' THEN b.valor ELSE 0 END), 0) as valor_pendente,

            -- Disparos
            COUNT(DISTINCT d.id) as total_disparos,
            COUNT(DISTINCT CASE WHEN d.status = 'enviado' THEN d.id END) as disparos_enviados,
            COUNT(DISTINCT CASE WHEN d.status = 'erro' THEN d.id END) as disparos_erro,
            COUNT(DISTINCT CASE WHEN d.status = 'pendente' THEN d.id END) as disparos_pendentes,

            -- Taxa de sucesso (%)
            CASE
                WHEN COUNT(DISTINCT d.id) > 0 THEN
                    ROUND((COUNT(DISTINCT CASE WHEN d.status = 'enviado' THEN d.id END)::numeric / COUNT(DISTINCT d.id)::numeric) * 100, 1)
                ELSE 0
            END as taxa_sucesso_disparos,

            -- Clientes únicos (por CPF)
            COUNT(DISTINCT b.cliente_final_cpf) as total_clientes_unicos,

            -- Data da última atualização
            GREATEST(
                MAX(b.created_at),
                MAX(d.created_at),
                cn.data_cadastro
            ) as ultima_atualizacao

        FROM clientes_nexus cn
        LEFT JOIN boletos b ON b.cliente_nexus_id = cn.id
        LEFT JOIN disparos d ON d.cliente_nexus_id = cn.id
        GROUP BY cn.id, cn.nome_empresa, cn.cnpj, cn.whatsapp_numero, cn.email_contato;
        """

        print("\n📌 Criando VIEW view_dashboard_cliente...")
        execute_query(sql_view)
        print("✅ VIEW criada com sucesso!")

        print("\n" + "=" * 60)
        print("✅ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ ERRO ao criar VIEW: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        Database.close_all_connections()

if __name__ == '__main__':
    sucesso = criar_view_dashboard()
    sys.exit(0 if sucesso else 1)
