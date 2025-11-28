-- ============================================
-- PORTAL CONSÓRCIO - SISTEMA NEXUS CRM
-- Script de criação de tabelas
-- Database: nexus_crm (porta 5434)
-- ============================================

-- ============================================
-- TABELA: clientes_finais
-- Clientes do consórcio cadastrados pelo Portal
-- Cada cliente_nexus_id vê apenas seus clientes
-- ============================================
CREATE TABLE IF NOT EXISTS clientes_finais (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,

    -- Dados Pessoais
    nome_completo VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    rg VARCHAR(20),
data_nascimento DATE,/
    email VARCHAR(255),
    telefone_fixo VARCHAR(20),
    telefone_celular VARCHAR(20) NOT NULL,
    whatsapp VARCHAR(20) NOT NULL,

    -- Endereço
    cep VARCHAR(10),
    logradouro VARCHAR(255),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),

    -- Dados do Consórcio
    numero_contrato VARCHAR(50) UNIQUE NOT NULL,
    grupo_consorcio VARCHAR(50) NOT NULL,
    cota_consorcio VARCHAR(50) NOT NULL,
    valor_credito DECIMAL(12, 2) NOT NULL,
    valor_parcela DECIMAL(10, 2) NOT NULL,
    prazo_meses INTEGER NOT NULL,
    parcelas_pagas INTEGER DEFAULT 0,
    parcelas_pendentes INTEGER,
    data_adesao DATE NOT NULL,
    status_contrato VARCHAR(50) DEFAULT 'ativo', -- ativo, suspenso, contemplado, cancelado

    -- Metadados
    origem VARCHAR(50) DEFAULT 'portal', -- portal, importacao, api
    cadastrado_por VARCHAR(100), -- usuário que cadastrou
    ativo BOOLEAN DEFAULT true,
    observacoes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: boletos
-- Boletos gerados pelo Portal Consórcio
-- ============================================
CREATE TABLE IF NOT EXISTS boletos (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    cliente_final_id INTEGER REFERENCES clientes_finais(id) ON DELETE CASCADE,

    -- Dados do Boleto
    numero_boleto VARCHAR(100) UNIQUE NOT NULL,
    linha_digitavel VARCHAR(100),
    codigo_barras VARCHAR(100),
    nosso_numero VARCHAR(50),
    valor_original DECIMAL(10, 2) NOT NULL,
    valor_atualizado DECIMAL(10, 2),
    data_vencimento DATE NOT NULL,
    data_emissao DATE NOT NULL,
    data_pagamento DATE,

    -- Referência
    mes_referencia INTEGER NOT NULL, -- 1-12
    ano_referencia INTEGER NOT NULL,
    numero_parcela INTEGER NOT NULL,
    descricao TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'pendente', -- pendente, pago, vencido, cancelado
    status_envio VARCHAR(50) DEFAULT 'nao_enviado', -- nao_enviado, enviado, erro
    data_envio TIMESTAMP,
    enviado_por VARCHAR(100), -- usuário que enviou

    -- Arquivo PDF
    pdf_filename VARCHAR(255),
    pdf_path TEXT,
    pdf_url TEXT,
    pdf_size INTEGER, -- bytes

    -- Metadados
    gerado_por VARCHAR(50) DEFAULT 'portal', -- portal, automatico, importacao
    observacoes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: usuarios_portal (admin do Portal)
-- ============================================
CREATE TABLE IF NOT EXISTS usuarios_portal (
    id SERIAL PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL, -- bcrypt
    nivel_acesso VARCHAR(50) DEFAULT 'operador', -- admin, operador, consulta
    ativo BOOLEAN DEFAULT true,
    ultimo_acesso TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: pastas_digitais
-- Sistema de organização de boletos por cliente
-- ============================================
CREATE TABLE IF NOT EXISTS pastas_digitais (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    cliente_final_id INTEGER REFERENCES clientes_finais(id) ON DELETE CASCADE,

    nome_pasta VARCHAR(255) NOT NULL,
    caminho_completo TEXT NOT NULL,
    pasta_pai_id INTEGER REFERENCES pastas_digitais(id) ON DELETE CASCADE,
    tipo VARCHAR(50) DEFAULT 'pasta', -- pasta, link_boleto

    -- Se tipo = link_boleto
    boleto_id INTEGER REFERENCES boletos(id) ON DELETE CASCADE,

    cor VARCHAR(20) DEFAULT '#39FF14',
    icone VARCHAR(50) DEFAULT '📁',
    ordem INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: historico_disparos
-- ============================================
CREATE TABLE IF NOT EXISTS historico_disparos (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,

    tipo_disparo VARCHAR(50) NOT NULL, -- manual, massa, automatico
    total_envios INTEGER DEFAULT 0,
    envios_sucesso INTEGER DEFAULT 0,
    envios_erro INTEGER DEFAULT 0,

    mensagem_enviada TEXT,
    horario_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executado_por VARCHAR(100),

    boletos_ids INTEGER[],
    clientes_ids INTEGER[],

    status VARCHAR(50) DEFAULT 'concluido',
    detalhes JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABELA: configuracoes_automacao
-- ============================================
CREATE TABLE IF NOT EXISTS configuracoes_automacao (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE UNIQUE,

    -- Disparo Automático
    disparo_automatico_habilitado BOOLEAN DEFAULT false,
    dias_antes_vencimento INTEGER DEFAULT 3,
    horario_disparo TIME DEFAULT '09:00:00',

    -- Mensagens
    mensagem_antibloqueio TEXT DEFAULT 'Olá! Tudo bem? Segue em anexo seu boleto. Qualquer dúvida, estamos à disposição!',
    mensagem_personalizada TEXT,

    -- Intervalos anti-bloqueio
    intervalo_min_segundos INTEGER DEFAULT 3,
    intervalo_max_segundos INTEGER DEFAULT 7,
    pausa_apos_disparos INTEGER DEFAULT 20,
    tempo_pausa_segundos INTEGER DEFAULT 60,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ÍNDICES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_clientes_finais_nexus ON clientes_finais(cliente_nexus_id);
CREATE INDEX IF NOT EXISTS idx_clientes_finais_cpf ON clientes_finais(cpf);
CREATE INDEX IF NOT EXISTS idx_clientes_finais_status ON clientes_finais(status_contrato);

CREATE INDEX IF NOT EXISTS idx_boletos_cliente_final ON boletos(cliente_final_id);
CREATE INDEX IF NOT EXISTS idx_boletos_vencimento ON boletos(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_boletos_status ON boletos(status);

CREATE INDEX IF NOT EXISTS idx_pastas_cliente_final ON pastas_digitais(cliente_final_id);

-- ============================================
-- TRIGGERS
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_clientes_finais_updated_at BEFORE UPDATE ON clientes_finais
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_boletos_updated_at BEFORE UPDATE ON boletos
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- DADOS INICIAIS
-- ============================================

-- Criar usuário admin do portal
INSERT INTO usuarios_portal (nome_completo, email, senha, nivel_acesso)
VALUES ('Admin Portal', 'admin@portal.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW', 'admin')
ON CONFLICT (email) DO NOTHING;
-- Senha: admin123

-- Inserir configuração padrão para cliente ID 2
INSERT INTO configuracoes_automacao (cliente_nexus_id, mensagem_antibloqueio)
VALUES (2, 'Olá! Tudo bem? Segue em anexo seu boleto. Qualquer dúvida, estamos à disposição!')
ON CONFLICT (cliente_nexus_id) DO NOTHING;

-- Inserir clientes finais de exemplo para cliente_nexus_id = 2
INSERT INTO clientes_finais (
    cliente_nexus_id, nome_completo, cpf, data_nascimento, telefone_celular, whatsapp,
    numero_contrato, grupo_consorcio, cota_consorcio, valor_credito, valor_parcela,
    prazo_meses, data_adesao, cidade, estado, cadastrado_por
) VALUES
(2, 'João da Silva Santos', '123.456.789-01', '1985-03-15', '(67) 99999-1111', '5567999991111',
 'CONS-2024-0001', 'G-001', 'C-0123', 50000.00, 850.00, 60, '2024-01-15', 'Campo Grande', 'MS', 'portal'),
(2, 'Maria Oliveira Costa', '234.567.890-12', '1990-07-22', '(67) 99999-2222', '5567999992222',
 'CONS-2024-0002', 'G-001', 'C-0124', 75000.00, 1200.00, 60, '2024-01-20', 'Campo Grande', 'MS', 'portal'),
(2, 'Pedro Henrique Souza', '345.678.901-23', '1988-11-10', '(67) 99999-3333', '5567999993333',
 'CONS-2024-0003', 'G-002', 'C-0089', 100000.00, 1650.00, 72, '2024-02-01', 'Dourados', 'MS', 'portal'),
(2, 'Ana Paula Rodrigues', '456.789.012-34', '1995-05-18', '(67) 99999-4444', '5567999994444',
 'CONS-2024-0004', 'G-002', 'C-0090', 60000.00, 950.00, 60, '2024-02-10', 'Dourados', 'MS', 'portal'),
(2, 'Carlos Eduardo Lima', '567.890.123-45', '1982-09-25', '(67) 99999-5555', '5567999995555',
 'CONS-2024-0005', 'G-003', 'C-0045', 120000.00, 2000.00, 72, '2024-03-01', 'Campo Grande', 'MS', 'portal')
ON CONFLICT (cpf) DO NOTHING;
