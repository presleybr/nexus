-- Migração 006: Adicionar tabela de status do WhatsApp
-- Data: 2025-01-29

-- Tabela para armazenar status da conexão WhatsApp
CREATE TABLE IF NOT EXISTS whatsapp_status (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(100) NOT NULL UNIQUE DEFAULT 'nexus-crm',
    is_connected BOOLEAN DEFAULT FALSE,
    phone_number VARCHAR(20),
    qr_code TEXT,
    last_connected_at TIMESTAMP,
    last_disconnected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir registro padrão
INSERT INTO whatsapp_status (session_name, is_connected)
VALUES ('nexus-crm', FALSE)
ON CONFLICT (session_name) DO NOTHING;

-- Índice para busca rápida
CREATE INDEX IF NOT EXISTS idx_whatsapp_status_session ON whatsapp_status(session_name);

-- Comentários
COMMENT ON TABLE whatsapp_status IS 'Armazena o status da conexão WhatsApp do sistema';
COMMENT ON COLUMN whatsapp_status.session_name IS 'Nome da sessão WhatsApp (sempre nexus-crm)';
COMMENT ON COLUMN whatsapp_status.is_connected IS 'Indica se o WhatsApp está conectado';
COMMENT ON COLUMN whatsapp_status.phone_number IS 'Número de telefone conectado';
COMMENT ON COLUMN whatsapp_status.qr_code IS 'QR Code base64 para conexão';
COMMENT ON COLUMN whatsapp_status.last_connected_at IS 'Última vez que conectou';
COMMENT ON COLUMN whatsapp_status.last_disconnected_at IS 'Última vez que desconectou';
