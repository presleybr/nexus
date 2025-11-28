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
