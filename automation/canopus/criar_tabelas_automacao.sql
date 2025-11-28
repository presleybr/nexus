-- ============================================================================
-- TABELAS PARA AUTOMAÇÃO DE DOWNLOAD DE BOLETOS CANOPUS
-- Sistema: Nexus CRM - Módulo de Automação Canopus
-- Descrição: Estrutura para gerenciar consultores, pontos de venda,
--            credenciais e logs de download automatizado de boletos
-- ============================================================================

-- Tabela de Consultores
-- Armazena informações dos consultores que possuem carteira de clientes
CREATE TABLE IF NOT EXISTS consultores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    telefone VARCHAR(20),
    ponto_venda_id INTEGER, -- Relacionamento com ponto de venda padrão
    pasta_downloads VARCHAR(255), -- Caminho da pasta onde salvar boletos (ex: /Danner/Boletos/)
    planilha_excel VARCHAR(255), -- Caminho da planilha Excel do consultor
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para consultores
CREATE INDEX idx_consultores_ativo ON consultores(ativo);
CREATE INDEX idx_consultores_nome ON consultores(nome);

COMMENT ON TABLE consultores IS 'Cadastro dos consultores de consórcio';
COMMENT ON COLUMN consultores.pasta_downloads IS 'Pasta onde os boletos do consultor serão salvos';
COMMENT ON COLUMN consultores.planilha_excel IS 'Caminho da planilha Excel com CPFs dos clientes';


-- Tabela de Pontos de Venda
-- Armazena os diferentes pontos de venda do Canopus
CREATE TABLE IF NOT EXISTS pontos_venda (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL, -- Ex: 'CREDMS', 'SEMICREDITO'
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    url_canopus VARCHAR(255) DEFAULT 'https://cnp3.consorciocanopus.com.br',
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para pontos_venda
CREATE UNIQUE INDEX idx_pontos_venda_codigo ON pontos_venda(codigo);
CREATE INDEX idx_pontos_venda_ativo ON pontos_venda(ativo);

COMMENT ON TABLE pontos_venda IS 'Pontos de venda do sistema Canopus';
COMMENT ON COLUMN pontos_venda.codigo IS 'Código único do ponto de venda (usado para identificação)';


-- Tabela de Credenciais Canopus
-- Armazena credenciais de acesso ao sistema Canopus por ponto de venda
CREATE TABLE IF NOT EXISTS credenciais_canopus (
    id SERIAL PRIMARY KEY,
    ponto_venda_id INTEGER NOT NULL REFERENCES pontos_venda(id) ON DELETE CASCADE,
    usuario VARCHAR(100) NOT NULL,
    senha_encrypted TEXT NOT NULL, -- Senha criptografada
    tipo_credencial VARCHAR(50) DEFAULT 'PRINCIPAL', -- PRINCIPAL, BACKUP, etc.
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_uso TIMESTAMP,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ponto_venda_id, usuario)
);

-- Índices para credenciais_canopus
CREATE INDEX idx_credenciais_ponto_venda ON credenciais_canopus(ponto_venda_id);
CREATE INDEX idx_credenciais_ativo ON credenciais_canopus(ativo);

COMMENT ON TABLE credenciais_canopus IS 'Credenciais de acesso ao sistema Canopus por ponto de venda';
COMMENT ON COLUMN credenciais_canopus.senha_encrypted IS 'Senha criptografada usando Fernet ou similar';
COMMENT ON COLUMN credenciais_canopus.tipo_credencial IS 'Tipo da credencial: PRINCIPAL, BACKUP, etc.';


-- Tabela de Log de Downloads
-- Registra todas as tentativas de download de boletos
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
    status VARCHAR(50) NOT NULL, -- 'SUCESSO', 'ERRO', 'CPF_NAO_ENCONTRADO', 'SEM_BOLETO_DISPONIVEL', etc.
    mensagem_erro TEXT,

    -- Dados do boleto baixado
    mes_referencia VARCHAR(20), -- Ex: 'DEZEMBRO/2024'
    valor_boleto DECIMAL(10, 2),
    data_vencimento DATE,
    numero_boleto VARCHAR(100),
    caminho_pdf VARCHAR(500), -- Caminho onde o PDF foi salvo

    -- Informações técnicas
    tempo_execucao_segundos DECIMAL(8, 2), -- Tempo que levou o download
    ip_execucao VARCHAR(50),
    usuario_execucao VARCHAR(100), -- Usuário que executou a automação

    -- Controle
    data_execucao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processado_envio BOOLEAN DEFAULT FALSE, -- Se já foi processado para envio WhatsApp
    data_processamento TIMESTAMP
);

-- Índices para log_downloads_boletos
CREATE INDEX idx_log_downloads_consultor ON log_downloads_boletos(consultor_id);
CREATE INDEX idx_log_downloads_status ON log_downloads_boletos(status);
CREATE INDEX idx_log_downloads_data ON log_downloads_boletos(data_execucao);
CREATE INDEX idx_log_downloads_cpf ON log_downloads_boletos(cpf_cliente);
CREATE INDEX idx_log_downloads_processado ON log_downloads_boletos(processado_envio);
CREATE INDEX idx_log_downloads_mes ON log_downloads_boletos(mes_referencia);

COMMENT ON TABLE log_downloads_boletos IS 'Log de todas as tentativas de download de boletos via automação';
COMMENT ON COLUMN log_downloads_boletos.status IS 'Status do download: SUCESSO, ERRO, CPF_NAO_ENCONTRADO, SEM_BOLETO_DISPONIVEL, TIMEOUT, etc.';
COMMENT ON COLUMN log_downloads_boletos.processado_envio IS 'Indica se este download já foi processado para envio via WhatsApp';


-- Tabela de Configurações da Automação
-- Armazena configurações gerais do sistema de automação
CREATE TABLE IF NOT EXISTS config_automacao_canopus (
    id SERIAL PRIMARY KEY,
    chave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    tipo VARCHAR(50) DEFAULT 'STRING', -- STRING, INTEGER, BOOLEAN, JSON, etc.
    descricao TEXT,
    categoria VARCHAR(100), -- Ex: 'TIMEOUT', 'NAVEGACAO', 'DOWNLOADS', etc.
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para config_automacao_canopus
CREATE UNIQUE INDEX idx_config_chave ON config_automacao_canopus(chave);
CREATE INDEX idx_config_categoria ON config_automacao_canopus(categoria);

COMMENT ON TABLE config_automacao_canopus IS 'Configurações gerais da automação Canopus';


-- Tabela de Execuções da Automação
-- Registra cada execução completa da automação (batch de downloads)
CREATE TABLE IF NOT EXISTS execucoes_automacao (
    id SERIAL PRIMARY KEY,
    tipo_execucao VARCHAR(50) NOT NULL, -- 'MANUAL', 'AGENDADA', 'TESTE'
    consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL,

    -- Estatísticas da execução
    total_clientes INTEGER DEFAULT 0,
    total_sucessos INTEGER DEFAULT 0,
    total_erros INTEGER DEFAULT 0,
    total_nao_encontrados INTEGER DEFAULT 0,

    -- Status e timing
    status VARCHAR(50) NOT NULL, -- 'INICIADA', 'EM_ANDAMENTO', 'CONCLUIDA', 'ERRO', 'CANCELADA'
    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_fim TIMESTAMP,
    tempo_total_segundos DECIMAL(10, 2),

    -- Informações adicionais
    observacoes TEXT,
    parametros_execucao JSONB, -- Parâmetros usados na execução (formato JSON)
    usuario_execucao VARCHAR(100),

    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para execucoes_automacao
CREATE INDEX idx_execucoes_status ON execucoes_automacao(status);
CREATE INDEX idx_execucoes_data_inicio ON execucoes_automacao(data_inicio);
CREATE INDEX idx_execucoes_consultor ON execucoes_automacao(consultor_id);

COMMENT ON TABLE execucoes_automacao IS 'Registro de cada execução batch da automação';


-- ============================================================================
-- ADIÇÃO DE COLUNAS EM TABELAS EXISTENTES
-- ============================================================================

-- Adiciona relacionamento do cliente_final com consultor (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='clientes_finais' AND column_name='consultor_id'
    ) THEN
        ALTER TABLE clientes_finais
        ADD COLUMN consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL;

        CREATE INDEX idx_clientes_finais_consultor ON clientes_finais(consultor_id);
    END IF;
END $$;

-- Adiciona ponto de venda ao cliente_final (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='clientes_finais' AND column_name='ponto_venda_id'
    ) THEN
        ALTER TABLE clientes_finais
        ADD COLUMN ponto_venda_id INTEGER REFERENCES pontos_venda(id) ON DELETE SET NULL;

        CREATE INDEX idx_clientes_finais_ponto_venda ON clientes_finais(ponto_venda_id);
    END IF;
END $$;

-- Adiciona referência de execução ao boleto (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='boletos' AND column_name='log_download_id'
    ) THEN
        ALTER TABLE boletos
        ADD COLUMN log_download_id INTEGER REFERENCES log_downloads_boletos(id) ON DELETE SET NULL;

        CREATE INDEX idx_boletos_log_download ON boletos(log_download_id);
    END IF;
END $$;


-- ============================================================================
-- DADOS INICIAIS
-- ============================================================================

-- Inserir pontos de venda principais
INSERT INTO pontos_venda (codigo, nome, descricao) VALUES
    ('CREDMS', 'CredMS', 'Ponto de venda CredMS'),
    ('SEMICREDITO', 'Semicrédito', 'Ponto de venda Semicrédito')
ON CONFLICT (codigo) DO NOTHING;

-- Inserir consultores de exemplo (ajustar conforme sua necessidade)
INSERT INTO consultores (nome, pasta_downloads, planilha_excel) VALUES
    ('Dayler', 'D:\Nexus\automation\canopus\downloads\Dayler\', 'D:\Nexus\automation\canopus\excel_files\Dayler.xlsx'),
    ('Neto', 'D:\Nexus\automation\canopus\downloads\Neto\', 'D:\Nexus\automation\canopus\excel_files\Neto.xlsx'),
    ('Mirelli', 'D:\Nexus\automation\canopus\downloads\Mirelli\', 'D:\Nexus\automation\canopus\excel_files\Mirelli.xlsx'),
    ('Danner', 'D:\Nexus\automation\canopus\downloads\Danner\', 'D:\Nexus\automation\canopus\excel_files\Danner.xlsx')
ON CONFLICT DO NOTHING;

-- Inserir configurações padrão
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
-- VIEWS ÚTEIS
-- ============================================================================

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

COMMENT ON VIEW vw_relatorio_downloads_consultor IS 'Relatório consolidado de downloads por consultor';


-- View de downloads recentes com problemas
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

COMMENT ON VIEW vw_downloads_com_problemas IS 'Downloads que falharam ou tiveram problemas';


-- View de boletos para envio WhatsApp
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

COMMENT ON VIEW vw_boletos_pendentes_envio IS 'Boletos baixados com sucesso e prontos para envio via WhatsApp';


-- ============================================================================
-- FUNÇÕES ÚTEIS
-- ============================================================================

-- Função para atualizar timestamp de atualização
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualizar data_atualizacao
CREATE TRIGGER trigger_consultores_updated
    BEFORE UPDATE ON consultores
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_pontos_venda_updated
    BEFORE UPDATE ON pontos_venda
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_credenciais_updated
    BEFORE UPDATE ON credenciais_canopus
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_config_updated
    BEFORE UPDATE ON config_automacao_canopus
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();


-- ============================================================================
-- GRANTS (ajustar conforme seu usuário PostgreSQL)
-- ============================================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO seu_usuario;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO seu_usuario;


-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================

SELECT 'Tabelas de automação Canopus criadas com sucesso!' as resultado;
