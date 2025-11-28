-- ============================================================================
-- NEXUS CRM - SCRIPT COMPLETO DE CRIAÇÃO DE BANCO DE DADOS
-- ============================================================================
-- INSTRUÇÕES PARA EXECUÇÃO NO DBEAVER:
--
-- 1. Conecte-se ao PostgreSQL no DBeaver
-- 2. Crie o banco de dados (se ainda não existir):
--    CREATE DATABASE nexus_crm;
-- 3. Selecione o banco nexus_crm
-- 4. Abra este arquivo no DBeaver
-- 5. Clique em "Execute SQL Script" (Ctrl+X) ou botão ▶ com dropdown
-- 6. Aguarde a execução completa
-- 7. Verifique se todas as tabelas foram criadas:
--    SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
--
-- ============================================================================

-- Remover objetos existentes (CUIDADO: apaga todos os dados!)
-- Descomente apenas se quiser limpar o banco completamente
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;

-- ============================================================================
-- PARTE 1: TABELAS BASE DO CRM
-- ============================================================================

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
    session_name VARCHAR(100),
    instance_name VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20),
    status VARCHAR(50) DEFAULT 'disconnected',
    qr_code TEXT,
    session_data JSONB,

    -- Colunas para Twilio
    provider VARCHAR(50) DEFAULT 'twilio',
    twilio_account_sid VARCHAR(100),
    twilio_phone VARCHAR(50),

    connected_at TIMESTAMP,
    disconnected_at TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para whatsapp_sessions
CREATE INDEX IF NOT EXISTS idx_whatsapp_sessions_provider ON whatsapp_sessions(provider);
CREATE INDEX IF NOT EXISTS idx_whatsapp_sessions_status ON whatsapp_sessions(status);

-- Comentários
COMMENT ON COLUMN whatsapp_sessions.provider IS 'Provedor WhatsApp: twilio, baileys, evolution';
COMMENT ON COLUMN whatsapp_sessions.twilio_account_sid IS 'Account SID do Twilio';
COMMENT ON COLUMN whatsapp_sessions.twilio_phone IS 'Número do WhatsApp Twilio (formato: whatsapp:+14155238886)';

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

-- Índices para logs
CREATE INDEX IF NOT EXISTS idx_logs_tipo ON logs_sistema(tipo);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs_sistema(created_at DESC);

-- Tabela de status do sistema
CREATE TABLE IF NOT EXISTS status_sistema (
    id SERIAL PRIMARY KEY,
    ativo BOOLEAN DEFAULT true,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- PARTE 2: TABELAS DE AUTOMAÇÃO CANOPUS
-- ============================================================================

-- Tabela de Consultores
CREATE TABLE IF NOT EXISTS consultores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(11),
    email VARCHAR(150),
    telefone VARCHAR(20),
    ponto_venda_id INTEGER,
    pasta_downloads VARCHAR(255),
    planilha_excel VARCHAR(255),
    link_planilha_drive TEXT,
    ultima_atualizacao_planilha TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para consultores
CREATE INDEX IF NOT EXISTS idx_consultores_ativo ON consultores(ativo);
CREATE INDEX IF NOT EXISTS idx_consultores_nome ON consultores(nome);
CREATE UNIQUE INDEX IF NOT EXISTS idx_consultores_cpf ON consultores(cpf) WHERE cpf IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_consultores_link_planilha ON consultores(link_planilha_drive) WHERE link_planilha_drive IS NOT NULL;

-- Comentários
COMMENT ON TABLE consultores IS 'Cadastro dos consultores de consórcio';
COMMENT ON COLUMN consultores.cpf IS 'CPF do consultor sem pontos e traços';
COMMENT ON COLUMN consultores.pasta_downloads IS 'Pasta onde os boletos do consultor serão salvos';
COMMENT ON COLUMN consultores.planilha_excel IS 'Caminho da planilha Excel com CPFs dos clientes';
COMMENT ON COLUMN consultores.link_planilha_drive IS 'Link do Google Drive da planilha do consultor (formato: https://drive.google.com/file/d/...)';

-- Tabela de Pontos de Venda
CREATE TABLE IF NOT EXISTS pontos_venda (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    url_canopus VARCHAR(255) DEFAULT 'https://cnp3.consorciocanopus.com.br',
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para pontos_venda
CREATE UNIQUE INDEX IF NOT EXISTS idx_pontos_venda_codigo ON pontos_venda(codigo);
CREATE INDEX IF NOT EXISTS idx_pontos_venda_ativo ON pontos_venda(ativo);

COMMENT ON TABLE pontos_venda IS 'Pontos de venda do sistema Canopus';

-- Adicionar FK depois que a tabela existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'consultores_ponto_venda_id_fkey'
    ) THEN
        ALTER TABLE consultores
        ADD CONSTRAINT consultores_ponto_venda_id_fkey
        FOREIGN KEY (ponto_venda_id) REFERENCES pontos_venda(id);
    END IF;
END $$;

-- Tabela de Credenciais Canopus
CREATE TABLE IF NOT EXISTS credenciais_canopus (
    id SERIAL PRIMARY KEY,
    ponto_venda_id INTEGER NOT NULL REFERENCES pontos_venda(id) ON DELETE CASCADE,
    usuario VARCHAR(100) NOT NULL,
    senha_encrypted TEXT NOT NULL,
    tipo_credencial VARCHAR(50) DEFAULT 'PRINCIPAL',
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_uso TIMESTAMP,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ponto_venda_id, usuario)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_credenciais_ponto_venda ON credenciais_canopus(ponto_venda_id);
CREATE INDEX IF NOT EXISTS idx_credenciais_ativo ON credenciais_canopus(ativo);

COMMENT ON TABLE credenciais_canopus IS 'Credenciais de acesso ao sistema Canopus por ponto de venda';

-- Tabela de Configurações da Automação Canopus
CREATE TABLE IF NOT EXISTS config_automacao_canopus (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    tipo VARCHAR(50) DEFAULT 'STRING',
    descricao TEXT,
    categoria VARCHAR(100),
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE UNIQUE INDEX IF NOT EXISTS idx_config_chave ON config_automacao_canopus(chave);
CREATE INDEX IF NOT EXISTS idx_config_categoria ON config_automacao_canopus(categoria);


-- ============================================================================
-- PARTE 3: TABELAS DO PORTAL CONSÓRCIO
-- ============================================================================

-- Tabela de clientes finais
CREATE TABLE IF NOT EXISTS clientes_finais (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    consultor_id INTEGER,
    ponto_venda_id INTEGER,

    -- Dados Pessoais
    nome_completo VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    rg VARCHAR(20),
    data_nascimento DATE,
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
    status_contrato VARCHAR(50) DEFAULT 'ativo',

    -- Metadados
    origem VARCHAR(50) DEFAULT 'portal',
    cadastrado_por VARCHAR(100),
    ativo BOOLEAN DEFAULT true,
    observacoes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adicionar FKs para consultores e pontos_venda
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'clientes_finais_consultor_id_fkey'
    ) THEN
        ALTER TABLE clientes_finais
        ADD CONSTRAINT clientes_finais_consultor_id_fkey
        FOREIGN KEY (consultor_id) REFERENCES consultores(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'clientes_finais_ponto_venda_id_fkey'
    ) THEN
        ALTER TABLE clientes_finais
        ADD CONSTRAINT clientes_finais_ponto_venda_id_fkey
        FOREIGN KEY (ponto_venda_id) REFERENCES pontos_venda(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Índices para clientes_finais
CREATE INDEX IF NOT EXISTS idx_clientes_finais_nexus ON clientes_finais(cliente_nexus_id);
CREATE INDEX IF NOT EXISTS idx_clientes_finais_cpf ON clientes_finais(cpf);
CREATE INDEX IF NOT EXISTS idx_clientes_finais_status ON clientes_finais(status_contrato);
CREATE INDEX IF NOT EXISTS idx_clientes_finais_consultor ON clientes_finais(consultor_id);
CREATE INDEX IF NOT EXISTS idx_clientes_finais_ponto_venda ON clientes_finais(ponto_venda_id);

-- Tabela de boletos
CREATE TABLE IF NOT EXISTS boletos (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    cliente_final_id INTEGER REFERENCES clientes_finais(id) ON DELETE CASCADE,
    log_download_id INTEGER,

    -- Dados do Boleto do Portal
    numero_boleto VARCHAR(100) UNIQUE,
    linha_digitavel VARCHAR(100),
    codigo_barras VARCHAR(100),
    nosso_numero VARCHAR(50),
    valor_original DECIMAL(10, 2),
    valor_atualizado DECIMAL(10, 2),
    data_vencimento DATE,
    data_emissao DATE,
    data_pagamento DATE,

    -- Dados do Boleto CRM Base (compatibilidade)
    cliente_final_cpf VARCHAR(14),
    cliente_final_nome VARCHAR(200),
    mes_referencia VARCHAR(20),
    vencimento DATE,
    valor DECIMAL(10, 2),

    -- Referência
    mes_referencia_num INTEGER,
    ano_referencia INTEGER,
    numero_parcela INTEGER,
    descricao TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'pendente',
    status_envio VARCHAR(50) DEFAULT 'nao_enviado',
    data_envio TIMESTAMP,
    enviado_por VARCHAR(100),

    -- Arquivo PDF
    pdf_filename VARCHAR(255),
    pdf_path TEXT,
    pdf_url TEXT,
    pdf_size INTEGER,

    -- Metadados
    gerado_por VARCHAR(50) DEFAULT 'portal',
    observacoes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para boletos
CREATE INDEX IF NOT EXISTS idx_boletos_mes ON boletos(mes_referencia);
CREATE INDEX IF NOT EXISTS idx_boletos_status ON boletos(status);
CREATE INDEX IF NOT EXISTS idx_boletos_cliente_nexus ON boletos(cliente_nexus_id);
CREATE INDEX IF NOT EXISTS idx_boletos_cliente_final ON boletos(cliente_final_id);
CREATE INDEX IF NOT EXISTS idx_boletos_vencimento ON boletos(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_boletos_log_download ON boletos(log_download_id);

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

-- Tabela de usuários do portal
CREATE TABLE IF NOT EXISTS usuarios_portal (
    id SERIAL PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    nivel_acesso VARCHAR(50) DEFAULT 'operador',
    ativo BOOLEAN DEFAULT true,
    ultimo_acesso TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de pastas digitais
CREATE TABLE IF NOT EXISTS pastas_digitais (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    cliente_final_id INTEGER REFERENCES clientes_finais(id) ON DELETE CASCADE,
    nome_pasta VARCHAR(255) NOT NULL,
    caminho_completo TEXT NOT NULL,
    pasta_pai_id INTEGER REFERENCES pastas_digitais(id) ON DELETE CASCADE,
    tipo VARCHAR(50) DEFAULT 'pasta',
    boleto_id INTEGER REFERENCES boletos(id) ON DELETE CASCADE,
    cor VARCHAR(20) DEFAULT '#39FF14',
    icone VARCHAR(50) DEFAULT '📁',
    ordem INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pastas_cliente_final ON pastas_digitais(cliente_final_id);

-- Tabela de histórico de disparos
CREATE TABLE IF NOT EXISTS historico_disparos (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE,
    tipo_disparo VARCHAR(50) NOT NULL,
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

-- Tabela de configurações de automação
CREATE TABLE IF NOT EXISTS configuracoes_automacao (
    id SERIAL PRIMARY KEY,
    cliente_nexus_id INTEGER REFERENCES clientes_nexus(id) ON DELETE CASCADE UNIQUE,

    -- Disparo Automático
    disparo_automatico_habilitado BOOLEAN DEFAULT false,
    dia_do_mes INTEGER DEFAULT 1 CHECK (dia_do_mes >= 1 AND dia_do_mes <= 31),
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

-- Comentários
COMMENT ON COLUMN configuracoes_automacao.dia_do_mes IS 'Dia do mês (1-31) para execução automática dos disparos';
COMMENT ON COLUMN configuracoes_automacao.disparo_automatico_habilitado IS 'Liga/Desliga o disparo automático mensal';


-- ============================================================================
-- PARTE 4: TABELAS DE LOG DE DOWNLOADS
-- ============================================================================

-- Tabela de Log de Downloads
CREATE TABLE IF NOT EXISTS log_downloads_boletos (
    id SERIAL PRIMARY KEY,
    consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL,
    ponto_venda_id INTEGER REFERENCES pontos_venda(id) ON DELETE SET NULL,
    cliente_final_id INTEGER REFERENCES clientes_finais(id) ON DELETE SET NULL,
    boleto_id INTEGER REFERENCES boletos(id) ON DELETE SET NULL,

    -- Dados do cliente
    cpf_cliente VARCHAR(14),
    nome_cliente VARCHAR(255),

    -- Dados do download
    status VARCHAR(50) NOT NULL,
    mensagem_erro TEXT,

    -- Dados do boleto baixado
    mes_referencia VARCHAR(20),
    valor_boleto DECIMAL(10, 2),
    data_vencimento DATE,
    numero_boleto VARCHAR(100),
    caminho_pdf VARCHAR(500),

    -- Informações técnicas
    tempo_execucao_segundos DECIMAL(8, 2),
    ip_execucao VARCHAR(50),
    usuario_execucao VARCHAR(100),

    -- Controle
    data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processado_envio BOOLEAN DEFAULT FALSE,
    data_processamento TIMESTAMP
);

-- Adicionar FK para boletos apontar para log_downloads
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'boletos_log_download_id_fkey'
    ) THEN
        ALTER TABLE boletos
        ADD CONSTRAINT boletos_log_download_id_fkey
        FOREIGN KEY (log_download_id) REFERENCES log_downloads_boletos(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Índices
CREATE INDEX IF NOT EXISTS idx_log_downloads_consultor ON log_downloads_boletos(consultor_id);
CREATE INDEX IF NOT EXISTS idx_log_downloads_status ON log_downloads_boletos(status);
CREATE INDEX IF NOT EXISTS idx_log_downloads_data ON log_downloads_boletos(data_execucao);
CREATE INDEX IF NOT EXISTS idx_log_downloads_cpf ON log_downloads_boletos(cpf_cliente);
CREATE INDEX IF NOT EXISTS idx_log_downloads_processado ON log_downloads_boletos(processado_envio);
CREATE INDEX IF NOT EXISTS idx_log_downloads_mes ON log_downloads_boletos(mes_referencia);

COMMENT ON TABLE log_downloads_boletos IS 'Log de todas as tentativas de download de boletos via automação';

-- Tabela de Execuções da Automação
CREATE TABLE IF NOT EXISTS execucoes_automacao (
    id SERIAL PRIMARY KEY,
    tipo_execucao VARCHAR(50) NOT NULL,
    consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL,

    -- Estatísticas
    total_clientes INTEGER DEFAULT 0,
    total_sucessos INTEGER DEFAULT 0,
    total_erros INTEGER DEFAULT 0,
    total_nao_encontrados INTEGER DEFAULT 0,

    -- Status e timing
    status VARCHAR(50) NOT NULL,
    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_fim TIMESTAMP,
    tempo_total_segundos DECIMAL(10, 2),

    -- Informações adicionais
    observacoes TEXT,
    parametros_execucao JSONB,
    usuario_execucao VARCHAR(100),

    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_execucoes_status ON execucoes_automacao(status);
CREATE INDEX IF NOT EXISTS idx_execucoes_data_inicio ON execucoes_automacao(data_inicio);
CREATE INDEX IF NOT EXISTS idx_execucoes_consultor ON execucoes_automacao(consultor_id);


-- ============================================================================
-- PARTE 5: FUNÇÕES E TRIGGERS
-- ============================================================================

-- Função para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Função para atualizar data_atualizacao
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
DROP TRIGGER IF EXISTS update_usuarios_updated_at ON usuarios;
CREATE TRIGGER update_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_configuracoes_updated_at ON configuracoes_cliente;
CREATE TRIGGER update_configuracoes_updated_at
    BEFORE UPDATE ON configuracoes_cliente
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_whatsapp_sessions_updated_at ON whatsapp_sessions;
CREATE TRIGGER update_whatsapp_sessions_updated_at
    BEFORE UPDATE ON whatsapp_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_clientes_finais_updated_at ON clientes_finais;
CREATE TRIGGER update_clientes_finais_updated_at
    BEFORE UPDATE ON clientes_finais
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_boletos_updated_at ON boletos;
CREATE TRIGGER update_boletos_updated_at
    BEFORE UPDATE ON boletos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers para data_atualizacao
DROP TRIGGER IF EXISTS trigger_consultores_updated ON consultores;
CREATE TRIGGER trigger_consultores_updated
    BEFORE UPDATE ON consultores
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trigger_pontos_venda_updated ON pontos_venda;
CREATE TRIGGER trigger_pontos_venda_updated
    BEFORE UPDATE ON pontos_venda
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trigger_credenciais_updated ON credenciais_canopus;
CREATE TRIGGER trigger_credenciais_updated
    BEFORE UPDATE ON credenciais_canopus
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trigger_config_updated ON config_automacao_canopus;
CREATE TRIGGER trigger_config_updated
    BEFORE UPDATE ON config_automacao_canopus
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();


-- ============================================================================
-- PARTE 6: VIEWS
-- ============================================================================

-- View Dashboard do Cliente
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
    COALESCE(SUM(COALESCE(b.valor, b.valor_original)), 0) as valor_total,
    COALESCE(SUM(CASE WHEN b.status_envio = 'pago' OR b.status = 'pago' THEN COALESCE(b.valor, b.valor_original) ELSE 0 END), 0) as valor_pago,
    COALESCE(SUM(CASE WHEN b.status_envio = 'pendente' OR b.status = 'pendente' THEN COALESCE(b.valor, b.valor_original) ELSE 0 END), 0) as valor_pendente,

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

    -- Clientes únicos
    COUNT(DISTINCT COALESCE(b.cliente_final_cpf, cf.cpf)) as total_clientes_unicos,

    -- Data da última atualização
    GREATEST(
        MAX(b.created_at),
        MAX(d.created_at),
        cn.data_cadastro
    ) as ultima_atualizacao

FROM clientes_nexus cn
LEFT JOIN boletos b ON b.cliente_nexus_id = cn.id
LEFT JOIN disparos d ON d.cliente_nexus_id = cn.id
LEFT JOIN clientes_finais cf ON cf.cliente_nexus_id = cn.id
GROUP BY cn.id, cn.nome_empresa, cn.cnpj, cn.whatsapp_numero, cn.email_contato;

-- View de relatório de downloads por consultor
CREATE OR REPLACE VIEW vw_relatorio_downloads_consultor AS
SELECT
    c.id as consultor_id,
    c.nome as consultor_nome,
    pv.nome as ponto_venda,
    COUNT(l.id) as total_downloads,
    COUNT(CASE WHEN l.status = 'SUCESSO' THEN 1 END) as sucessos,
    COUNT(CASE WHEN l.status = 'ERRO' THEN 1 END) as erros,
    COUNT(CASE WHEN l.status = 'CPF_NAO_ENCONTRADO' THEN 1 END) as nao_encontrados,
    SUM(CASE WHEN l.status = 'SUCESSO' THEN l.valor_boleto ELSE 0 END) as valor_total_boletos,
    MAX(l.data_execucao) as ultimo_download,
    AVG(l.tempo_execucao_segundos) as tempo_medio_download
FROM consultores c
LEFT JOIN log_downloads_boletos l ON c.id = l.consultor_id
LEFT JOIN pontos_venda pv ON l.ponto_venda_id = pv.id
WHERE c.ativo = TRUE
GROUP BY c.id, c.nome, pv.nome
ORDER BY c.nome;

-- View de downloads com problemas
CREATE OR REPLACE VIEW vw_downloads_com_problemas AS
SELECT
    l.id,
    l.data_execucao,
    c.nome as consultor,
    pv.nome as ponto_venda,
    l.cpf_cliente,
    l.nome_cliente,
    l.status,
    l.mensagem_erro,
    l.mes_referencia
FROM log_downloads_boletos l
LEFT JOIN consultores c ON l.consultor_id = c.id
LEFT JOIN pontos_venda pv ON l.ponto_venda_id = pv.id
WHERE l.status != 'SUCESSO'
ORDER BY l.data_execucao DESC;

-- View de boletos pendentes de envio
CREATE OR REPLACE VIEW vw_boletos_pendentes_envio AS
SELECT
    l.id as log_id,
    l.boleto_id,
    cf.id as cliente_id,
    cf.nome_completo,
    cf.whatsapp,
    l.caminho_pdf,
    l.valor_boleto,
    l.data_vencimento,
    l.numero_boleto,
    l.mes_referencia,
    c.nome as consultor_nome
FROM log_downloads_boletos l
INNER JOIN clientes_finais cf ON l.cliente_final_id = cf.id
LEFT JOIN consultores c ON l.consultor_id = c.id
WHERE l.status = 'SUCESSO'
    AND l.processado_envio = FALSE
    AND cf.whatsapp IS NOT NULL
ORDER BY l.data_execucao;


-- ============================================================================
-- PARTE 7: DADOS INICIAIS
-- ============================================================================

-- Inicializar status do sistema
INSERT INTO status_sistema (ativo, ultima_atualizacao)
SELECT true, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM status_sistema WHERE id = 1);

-- Inserir usuário admin do portal
INSERT INTO usuarios_portal (nome_completo, email, senha, nivel_acesso)
VALUES ('Admin Portal', 'admin@portal.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW', 'admin')
ON CONFLICT (email) DO NOTHING;
-- Senha: admin123

-- Inserir pontos de venda
INSERT INTO pontos_venda (codigo, nome, descricao) VALUES
    ('CREDMS', 'CredMS', 'Ponto de venda CredMS'),
    ('SEMICREDITO', 'Semicrédito', 'Ponto de venda Semicrédito')
ON CONFLICT (codigo) DO NOTHING;

-- Inserir consultores de exemplo
INSERT INTO consultores (nome, pasta_downloads, planilha_excel) VALUES
    ('Dayler', 'D:\Nexus\automation\canopus\downloads\Dayler\', 'D:\Nexus\automation\canopus\excel_files\Dayler.xlsx'),
    ('Neto', 'D:\Nexus\automation\canopus\downloads\Neto\', 'D:\Nexus\automation\canopus\excel_files\Neto.xlsx'),
    ('Mirelli', 'D:\Nexus\automation\canopus\downloads\Mirelli\', 'D:\Nexus\automation\canopus\excel_files\Mirelli.xlsx'),
    ('Danner', 'D:\Nexus\automation\canopus\downloads\Danner\', 'D:\Nexus\automation\canopus\excel_files\Danner.xlsx')
ON CONFLICT DO NOTHING;

-- Inserir configurações padrão da automação Canopus
INSERT INTO config_automacao_canopus (chave, valor, tipo, descricao, categoria) VALUES
    ('TIMEOUT_NAVEGACAO', '30', 'INTEGER', 'Timeout padrão para navegação (segundos)', 'TIMEOUT'),
    ('TIMEOUT_DOWNLOAD', '60', 'INTEGER', 'Timeout para download de boletos (segundos)', 'TIMEOUT'),
    ('HEADLESS_MODE', 'false', 'BOOLEAN', 'Executar navegador em modo headless', 'NAVEGACAO'),
    ('MAX_RETENTATIVAS', '3', 'INTEGER', 'Número máximo de tentativas por download', 'EXECUCAO'),
    ('INTERVALO_ENTRE_DOWNLOADS', '2', 'INTEGER', 'Intervalo em segundos entre downloads', 'EXECUCAO'),
    ('MES_PADRAO_DOWNLOAD', 'DEZEMBRO', 'STRING', 'Mês padrão para download de boletos', 'DOWNLOADS'),
    ('CAMINHO_BASE_DOWNLOADS', 'D:\Nexus\automation\canopus\downloads\', 'STRING', 'Caminho base para salvar downloads', 'DOWNLOADS'),
    ('ENVIAR_WHATSAPP_AUTOMATICO', 'false', 'BOOLEAN', 'Enviar boletos automaticamente via WhatsApp após download', 'INTEGRACAO')
ON CONFLICT (chave) DO NOTHING;


-- ============================================================================
-- FINALIZAÇÃO
-- ============================================================================

-- Listar todas as tabelas criadas
SELECT
    '✅ SCRIPT EXECUTADO COM SUCESSO!' as status,
    COUNT(*) as total_tabelas
FROM pg_tables
WHERE schemaname = 'public';

-- Mostrar todas as tabelas
SELECT
    tablename as tabela,
    'Criada com sucesso' as status
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
