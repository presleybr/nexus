-- Migração 007: Criar tabela numeros_notificacao
-- Data: 2025-01-29
-- Descrição: Tabela para armazenar números WhatsApp que recebem notificações de disparos

-- Criar tabela numeros_notificacao
CREATE TABLE IF NOT EXISTS numeros_notificacao (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER NOT NULL REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    whatsapp VARCHAR(20) NOT NULL,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índice para busca por cliente
CREATE INDEX IF NOT EXISTS idx_numeros_notificacao_cliente
ON numeros_notificacao(cliente_nexus_id);

-- Comentários
COMMENT ON TABLE numeros_notificacao IS 'Números WhatsApp que recebem notificações sobre disparos automáticos';
COMMENT ON COLUMN numeros_notificacao.cliente_nexus_id IS 'ID do cliente Nexus (usuário do CRM)';
COMMENT ON COLUMN numeros_notificacao.nome IS 'Nome/descrição do número (ex: João - Gerente)';
COMMENT ON COLUMN numeros_notificacao.whatsapp IS 'Número WhatsApp no formato 5567999999999';
COMMENT ON COLUMN numeros_notificacao.ativo IS 'Se o número está ativo para receber notificações';
