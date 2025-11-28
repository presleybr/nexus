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
-- ============================================
-- Migration: Adicionar campo dia_do_mes para agendamento mensal
-- Data: 2025-01-16
-- ============================================

-- Adicionar campo dia_do_mes na tabela configuracoes_automacao
ALTER TABLE configuracoes_automacao
ADD COLUMN IF NOT EXISTS dia_do_mes INTEGER DEFAULT 1 CHECK (dia_do_mes >= 1 AND dia_do_mes <= 31);

-- Comentário explicativo
COMMENT ON COLUMN configuracoes_automacao.dia_do_mes IS 'Dia do mês (1-31) para execução automática dos disparos';
COMMENT ON COLUMN configuracoes_automacao.disparo_automatico_habilitado IS 'Liga/Desliga o disparo automático mensal';

-- Atualizar configurações existentes para dia 1 como padrão
UPDATE configuracoes_automacao
SET dia_do_mes = 1
WHERE dia_do_mes IS NULL;
-- Adiciona coluna CPF à tabela consultores
-- Migration 004: Adicionar CPF para integração com Canopus

ALTER TABLE consultores ADD COLUMN IF NOT EXISTS cpf VARCHAR(11);

-- Criar índice único para CPF (permitindo NULL para registros antigos)
CREATE UNIQUE INDEX IF NOT EXISTS idx_consultores_cpf ON consultores(cpf) WHERE cpf IS NOT NULL;

-- Comentário na coluna
COMMENT ON COLUMN consultores.cpf IS 'CPF do consultor sem pontos e traços';
-- Migração: Adicionar campo link_planilha_drive na tabela consultores
-- Data: 2025-01-15
-- Descrição: Permite armazenar links do Google Drive para cada consultor

-- Adicionar coluna link_planilha_drive
ALTER TABLE consultores
ADD COLUMN IF NOT EXISTS link_planilha_drive TEXT;

-- Adicionar comentário na coluna
COMMENT ON COLUMN consultores.link_planilha_drive IS 'Link do Google Drive da planilha do consultor (formato: https://drive.google.com/file/d/...)';

-- Adicionar coluna ultima_atualizacao_planilha
ALTER TABLE consultores
ADD COLUMN IF NOT EXISTS ultima_atualizacao_planilha TIMESTAMP;

-- Adicionar comentário
COMMENT ON COLUMN consultores.ultima_atualizacao_planilha IS 'Data e hora da última atualização da planilha do Drive';

-- Atualizar o link do Dener (se existir)
UPDATE consultores
SET link_planilha_drive = 'CONFIGURAR_LINK_AQUI'
WHERE nome ILIKE '%dener%' OR nome ILIKE '%danner%';

-- Criar índice para performance
CREATE INDEX IF NOT EXISTS idx_consultores_link_planilha ON consultores(link_planilha_drive) WHERE link_planilha_drive IS NOT NULL;

-- Log
DO $$
BEGIN
    RAISE NOTICE 'Migração 005 aplicada com sucesso: campo link_planilha_drive adicionado à tabela consultores';
END $$;
