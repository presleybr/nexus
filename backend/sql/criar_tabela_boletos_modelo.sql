-- ============================================
-- TABELA: boletos_modelo
-- Armazena boletos modelo/template para uso geral
-- ============================================

CREATE TABLE IF NOT EXISTS boletos_modelo (
    id SERIAL PRIMARY KEY,

    -- Identificação
    nome VARCHAR(255) NOT NULL UNIQUE, -- ex: "Modelo Banese", "Modelo Padrão"
    descricao TEXT,
    tipo VARCHAR(50) DEFAULT 'generico', -- generico, banco_especifico, personalizado
    banco VARCHAR(100), -- ex: "Banese", "Banco do Brasil"

    -- Arquivo PDF
    pdf_filename VARCHAR(255) NOT NULL,
    pdf_path TEXT NOT NULL,
    pdf_size INTEGER, -- bytes

    -- Status
    ativo BOOLEAN DEFAULT true,
    padrao BOOLEAN DEFAULT false, -- se é o modelo padrão do sistema

    -- Uso
    total_envios INTEGER DEFAULT 0, -- quantas vezes foi enviado
    ultimo_envio TIMESTAMP,

    -- Metadados
    uploaded_by VARCHAR(100), -- usuário que fez upload
    observacoes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_boletos_modelo_ativo ON boletos_modelo(ativo);
CREATE INDEX IF NOT EXISTS idx_boletos_modelo_padrao ON boletos_modelo(padrao);

-- Comentários
COMMENT ON TABLE boletos_modelo IS 'Armazena boletos modelo/template para envio em massa';
COMMENT ON COLUMN boletos_modelo.padrao IS 'Define se este é o boleto modelo padrão do sistema';
COMMENT ON COLUMN boletos_modelo.total_envios IS 'Contador de quantas vezes este modelo foi enviado';
