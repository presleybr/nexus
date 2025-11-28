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
