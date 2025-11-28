-- Adiciona coluna CPF à tabela consultores
-- Migration 004: Adicionar CPF para integração com Canopus

ALTER TABLE consultores ADD COLUMN IF NOT EXISTS cpf VARCHAR(11);

-- Criar índice único para CPF (permitindo NULL para registros antigos)
CREATE UNIQUE INDEX IF NOT EXISTS idx_consultores_cpf ON consultores(cpf) WHERE cpf IS NOT NULL;

-- Comentário na coluna
COMMENT ON COLUMN consultores.cpf IS 'CPF do consultor sem pontos e traços';
