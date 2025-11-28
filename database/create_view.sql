-- ============================================================
-- SQL PARA CRIAR VIEW DO DASHBOARD
-- Execute este arquivo para adicionar a VIEW ao banco de dados
-- ============================================================

-- Remove a VIEW se já existir
DROP VIEW IF EXISTS view_dashboard_cliente;

-- Cria a VIEW para o dashboard do cliente
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

-- Verifica se a VIEW foi criada
SELECT 'VIEW view_dashboard_cliente criada com sucesso!' as mensagem;
