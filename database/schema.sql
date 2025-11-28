-- ============================================================
-- SCHEMA DO BANCO DE DADOS - CRM NEXUS
-- Sistema completo de gerenciamento de clientes e boletos
-- ============================================================

-- Tabela de usuários (login para clientes e administradores)
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('cliente', 'admin')),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de clientes da Nexus (empresários que usam o sistema)
CREATE TABLE IF NOT EXISTS clientes_nexus (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    nome_empresa VARCHAR(200) NOT NULL,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    whatsapp_numero VARCHAR(20),
    email_contato VARCHAR(150),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT true
);

-- Tabela de boletos gerados
CREATE TABLE IF NOT EXISTS boletos (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    cliente_final_cpf VARCHAR(14) NOT NULL,
    cliente_final_nome VARCHAR(200) NOT NULL,
    mes_referencia VARCHAR(20) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    vencimento DATE NOT NULL,
    pdf_path VARCHAR(500),
    status_envio VARCHAR(50) DEFAULT 'pendente',
    data_envio TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para busca rápida de boletos
CREATE INDEX IF NOT EXISTS idx_boletos_mes ON boletos(mes_referencia);
CREATE INDEX IF NOT EXISTS idx_boletos_status ON boletos(status_envio);
CREATE INDEX IF NOT EXISTS idx_boletos_cliente_nexus ON boletos(cliente_nexus_id);

-- Tabela de disparos de WhatsApp
CREATE TABLE IF NOT EXISTS disparos (
    id SERIAL PRIMARY KEY,
    boleto_id INTEGER REFERENCES boletos(id) ON DELETE CASCADE,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    telefone_destino VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'pendente' CHECK (status IN ('pendente', 'enviado', 'erro', 'cancelado')),
    mensagem_enviada TEXT,
    erro TEXT,
    data_disparo TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de configurações por cliente
CREATE TABLE IF NOT EXISTS configuracoes_cliente (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE UNIQUE,
    mensagem_antibloqueio TEXT DEFAULT 'Olá! Você receberá seu boleto em instantes.',
    data_disparo_automatico DATE,
    intervalo_disparos INTEGER DEFAULT 5,
    horario_disparo TIME DEFAULT '09:00:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de sessões WhatsApp
CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    instance_name VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20),
    status VARCHAR(50) DEFAULT 'disconnected',
    qr_code TEXT,
    session_data JSONB,
    connected_at TIMESTAMP,
    disconnected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de logs do sistema
CREATE TABLE IF NOT EXISTS logs_sistema (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('info', 'warning', 'error', 'success')),
    categoria VARCHAR(50),
    mensagem TEXT NOT NULL,
    detalhes JSONB,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para busca de logs
CREATE INDEX IF NOT EXISTS idx_logs_tipo ON logs_sistema(tipo);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs_sistema(created_at DESC);

-- Tabela de status do sistema
CREATE TABLE IF NOT EXISTS status_sistema (
    id SERIAL PRIMARY KEY,
    ativo BOOLEAN DEFAULT true,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inicializa o status do sistema
INSERT INTO status_sistema (ativo, ultima_atualizacao)
SELECT true, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM status_sistema WHERE id = 1);

-- Função para atualizar o campo updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualizar updated_at
DROP TRIGGER IF EXISTS update_usuarios_updated_at ON usuarios;
CREATE TRIGGER update_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_configuracoes_updated_at ON configuracoes_cliente;
CREATE TRIGGER update_configuracoes_updated_at
    BEFORE UPDATE ON configuracoes_cliente
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_whatsapp_sessions_updated_at ON whatsapp_sessions;
CREATE TRIGGER update_whatsapp_sessions_updated_at
    BEFORE UPDATE ON whatsapp_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- VIEW PARA DASHBOARD DO CLIENTE
-- ============================================================

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
