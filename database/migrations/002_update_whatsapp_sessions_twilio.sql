-- ============================================
-- Migração: Atualizar whatsapp_sessions para Twilio
-- Data: 2025-11-16
-- Descrição: Adiciona colunas para Twilio e migra dados
-- ============================================

-- Adicionar coluna provider se não existir
ALTER TABLE IF EXISTS whatsapp_sessions
ADD COLUMN IF NOT EXISTS provider VARCHAR(50) DEFAULT 'twilio';

-- Adicionar colunas específicas do Twilio
ALTER TABLE IF EXISTS whatsapp_sessions
ADD COLUMN IF NOT EXISTS twilio_account_sid VARCHAR(100);

ALTER TABLE IF EXISTS whatsapp_sessions
ADD COLUMN IF NOT EXISTS twilio_phone VARCHAR(50);

-- Adicionar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_sessions_provider ON whatsapp_sessions(provider);
CREATE INDEX IF NOT EXISTS idx_whatsapp_sessions_status ON whatsapp_sessions(status);

-- Comentários nas colunas
COMMENT ON COLUMN whatsapp_sessions.provider IS 'Provedor WhatsApp: twilio, baileys, evolution';
COMMENT ON COLUMN whatsapp_sessions.twilio_account_sid IS 'Account SID do Twilio';
COMMENT ON COLUMN whatsapp_sessions.twilio_phone IS 'Número do WhatsApp Twilio (formato: whatsapp:+14155238886)';

-- Limpar sessões antigas (opcional - comentado por segurança)
-- TRUNCATE TABLE whatsapp_sessions CASCADE;

-- Inserir/atualizar sessão Twilio para cada cliente
INSERT INTO whatsapp_sessions (
    cliente_nexus_id,
    session_name,
    status,
    provider,
    twilio_account_sid,
    twilio_phone,
    connected_at,
    criado_em,
    atualizado_em
)
SELECT
    id,
    'twilio_' || id,
    'connected',
    'twilio',
    'AC3daccc77955ee03eccdd580bf494bb08',
    'whatsapp:+14155238886',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM clientes_nexus
WHERE NOT EXISTS (
    SELECT 1 FROM whatsapp_sessions WHERE cliente_nexus_id = clientes_nexus.id
)
ON CONFLICT (cliente_nexus_id) DO UPDATE
SET
    provider = 'twilio',
    status = 'connected',
    twilio_account_sid = 'AC3daccc77955ee03eccdd580bf494bb08',
    twilio_phone = 'whatsapp:+14155238886',
    connected_at = CURRENT_TIMESTAMP,
    atualizado_em = CURRENT_TIMESTAMP;

-- Verificar resultado
SELECT
    COUNT(*) as total_sessoes,
    COUNT(CASE WHEN provider = 'twilio' THEN 1 END) as sessoes_twilio,
    COUNT(CASE WHEN status = 'connected' THEN 1 END) as sessoes_conectadas
FROM whatsapp_sessions;

-- Exibir algumas sessões de exemplo
SELECT
    id,
    cliente_nexus_id,
    session_name,
    provider,
    status,
    twilio_phone,
    connected_at
FROM whatsapp_sessions
ORDER BY id
LIMIT 5;
