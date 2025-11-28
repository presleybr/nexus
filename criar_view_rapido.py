"""
Script rápido para criar a VIEW sem importar models
"""
import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5434')
DB_NAME = os.getenv('DB_NAME', 'nexus_crm')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'nexus2025')

conninfo = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

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

print("=" * 60)
print("🔧 CRIANDO VIEW view_dashboard_cliente")
print("=" * 60)

try:
    print(f"\n📌 Conectando ao PostgreSQL...")
    print(f"   Host: {DB_HOST}")
    print(f"   Port: {DB_PORT}")
    print(f"   Database: {DB_NAME}")

    with psycopg.connect(conninfo, autocommit=True) as conn:
        print("✅ Conectado ao banco de dados")

        with conn.cursor() as cursor:
            print("\n📌 Criando VIEW...")
            cursor.execute(sql_view)
            print("✅ VIEW view_dashboard_cliente criada com sucesso!")

            # Verifica se a VIEW foi criada
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.views
                WHERE table_schema = 'public'
                AND table_name = 'view_dashboard_cliente'
            """)
            count = cursor.fetchone()[0]

            if count > 0:
                print("✅ Verificação: VIEW existe no banco de dados")
            else:
                print("❌ ERRO: VIEW não foi encontrada após criação")

    print("\n" + "=" * 60)
    print("✅ SUCESSO! Atualize a página do dashboard agora.")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
