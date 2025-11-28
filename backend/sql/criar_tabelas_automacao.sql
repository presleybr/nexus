-- ============================================================================
-- TABELAS PARA AUTOMAÇÃO DE DOWNLOAD DE BOLETOS CANOPUS
-- Sistema: Nexus CRM - Módulo de Automação Canopus
-- Descrição: Estrutura completa para gerenciar consultores, pontos de venda,
--            credenciais, importação de planilhas e logs de download
-- ============================================================================

-- ============================================================================
-- 1. TABELA DE CONSULTORES
-- ============================================================================

CREATE TABLE IF NOT EXISTS consultores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    telefone VARCHAR(20),
    whatsapp VARCHAR(20),

    -- Identificação de empresa e ponto de venda
    empresa VARCHAR(50) NOT NULL, -- 'credms' ou 'semicredito'
    ponto_venda VARCHAR(20), -- Código do ponto ex: '17.308'

    -- Organização de arquivos
    pasta_boletos VARCHAR(100) NOT NULL, -- Nome da pasta para salvar boletos
    cor_identificacao VARCHAR(20), -- 'rosa', 'verde', 'azul', etc (para planilha)

    -- Controle
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Índices
    CONSTRAINT consultores_nome_unique UNIQUE(nome),
    CONSTRAINT consultores_empresa_check CHECK (empresa IN ('credms', 'semicredito'))
);

-- Índices para consultores
CREATE INDEX idx_consultores_ativo ON consultores(ativo);
CREATE INDEX idx_consultores_empresa ON consultores(empresa);
CREATE INDEX idx_consultores_nome ON consultores(nome);

COMMENT ON TABLE consultores IS 'Cadastro dos consultores de consórcio com suas configurações';
COMMENT ON COLUMN consultores.empresa IS 'Empresa do consultor: credms ou semicredito';
COMMENT ON COLUMN consultores.ponto_venda IS 'Código do ponto de venda no sistema Canopus (ex: 17.308)';
COMMENT ON COLUMN consultores.pasta_boletos IS 'Nome da pasta onde salvar boletos do consultor';
COMMENT ON COLUMN consultores.cor_identificacao IS 'Cor usada para identificar clientes na planilha';


-- ============================================================================
-- 2. TABELA DE PONTOS DE VENDA
-- ============================================================================

CREATE TABLE IF NOT EXISTS pontos_venda (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL, -- Ex: '17.308', '17.309'
    nome VARCHAR(150) NOT NULL,
    empresa VARCHAR(50) NOT NULL, -- 'credms' ou 'semicredito'

    -- URL do sistema
    url_base VARCHAR(255) DEFAULT 'https://cnp3.consorciocanopus.com.br',

    -- Controle
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pontos_venda_empresa_check CHECK (empresa IN ('credms', 'semicredito'))
);

-- Índices para pontos_venda
CREATE UNIQUE INDEX idx_pontos_venda_codigo ON pontos_venda(codigo);
CREATE INDEX idx_pontos_venda_empresa ON pontos_venda(empresa);
CREATE INDEX idx_pontos_venda_ativo ON pontos_venda(ativo);

COMMENT ON TABLE pontos_venda IS 'Pontos de venda do sistema Canopus';
COMMENT ON COLUMN pontos_venda.codigo IS 'Código único do ponto de venda (ex: 17.308)';


-- ============================================================================
-- 3. TABELA DE CREDENCIAIS CANOPUS
-- ============================================================================

CREATE TABLE IF NOT EXISTS credenciais_canopus (
    id SERIAL PRIMARY KEY,
    ponto_venda_id INTEGER NOT NULL REFERENCES pontos_venda(id) ON DELETE CASCADE,

    -- Credenciais
    usuario VARCHAR(100) NOT NULL,
    senha_encrypted TEXT NOT NULL, -- Senha criptografada com Fernet
    codigo_empresa VARCHAR(10) DEFAULT '0101', -- Código padrão da empresa no login

    -- Auditoria de uso
    ultimo_login TIMESTAMP,
    ultimo_erro TIMESTAMP,
    mensagem_erro TEXT,

    -- Controle
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(ponto_venda_id, usuario)
);

-- Índices para credenciais_canopus
CREATE INDEX idx_credenciais_ponto_venda ON credenciais_canopus(ponto_venda_id);
CREATE INDEX idx_credenciais_ativo ON credenciais_canopus(ativo);

COMMENT ON TABLE credenciais_canopus IS 'Credenciais de acesso ao sistema Canopus por ponto de venda';
COMMENT ON COLUMN credenciais_canopus.senha_encrypted IS 'Senha criptografada usando Fernet';
COMMENT ON COLUMN credenciais_canopus.codigo_empresa IS 'Código da empresa usado no login (geralmente 0101)';


-- ============================================================================
-- 4. TABELA DE STAGING - IMPORTAÇÃO DE PLANILHAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS clientes_planilha_staging (
    id SERIAL PRIMARY KEY,

    -- Dados do cliente (da planilha)
    cpf VARCHAR(14) NOT NULL,
    nome VARCHAR(255),
    ponto_venda VARCHAR(20), -- Código do ponto de venda
    grupo VARCHAR(50), -- Grupo do consórcio
    cota VARCHAR(50), -- Cota do consórcio
    contemplado BOOLEAN DEFAULT FALSE,

    -- Origem dos dados
    consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL,
    consultor_nome VARCHAR(100), -- Nome do consultor (da planilha)
    arquivo_origem VARCHAR(500), -- Caminho do arquivo Excel
    linha_planilha INTEGER, -- Número da linha na planilha

    -- Status do processamento
    status VARCHAR(50) DEFAULT 'pendente', -- pendente, processado, erro, sincronizado
    mensagem_erro TEXT,

    -- Relacionamento após sincronização
    cliente_final_id INTEGER REFERENCES clientes_finais(id) ON DELETE SET NULL,

    -- Controle
    importado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processado_em TIMESTAMP,
    sincronizado_em TIMESTAMP,

    CONSTRAINT clientes_staging_status_check CHECK (
        status IN ('pendente', 'processado', 'erro', 'sincronizado', 'duplicado')
    )
);

-- Índices para clientes_planilha_staging
CREATE INDEX idx_staging_cpf ON clientes_planilha_staging(cpf);
CREATE INDEX idx_staging_consultor ON clientes_planilha_staging(consultor_id);
CREATE INDEX idx_staging_status ON clientes_planilha_staging(status);
CREATE INDEX idx_staging_arquivo ON clientes_planilha_staging(arquivo_origem);
CREATE INDEX idx_staging_cliente_final ON clientes_planilha_staging(cliente_final_id);

COMMENT ON TABLE clientes_planilha_staging IS 'Área de staging para importação de clientes das planilhas Excel';
COMMENT ON COLUMN clientes_planilha_staging.status IS 'Status: pendente, processado, erro, sincronizado, duplicado';
COMMENT ON COLUMN clientes_planilha_staging.cliente_final_id IS 'ID do cliente após sincronização com clientes_finais';


-- ============================================================================
-- 5. TABELA DE LOG DE DOWNLOADS
-- ============================================================================

CREATE TABLE IF NOT EXISTS log_downloads_boletos (
    id SERIAL PRIMARY KEY,

    -- Relacionamentos
    cliente_final_id INTEGER REFERENCES clientes_finais(id) ON DELETE SET NULL,
    consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL,
    boleto_id INTEGER REFERENCES boletos(id) ON DELETE SET NULL,

    -- Dados do cliente
    cpf VARCHAR(14) NOT NULL,
    nome_cliente VARCHAR(255),

    -- Dados do período
    mes_referencia VARCHAR(20) NOT NULL, -- 'JANEIRO', 'FEVEREIRO', etc
    ano_referencia INTEGER NOT NULL, -- 2024, 2025, etc

    -- Dados do arquivo
    arquivo_nome VARCHAR(255), -- Nome do arquivo PDF
    arquivo_caminho VARCHAR(500), -- Caminho completo do arquivo
    arquivo_tamanho INTEGER, -- Tamanho em bytes

    -- Status do download
    status VARCHAR(50) NOT NULL, -- 'sucesso', 'erro', 'cpf_nao_encontrado', 'sem_boleto', etc
    mensagem_erro TEXT,
    tempo_execucao_segundos DECIMAL(8, 2),

    -- Relacionamento com execução batch
    automacao_id UUID, -- ID da execução batch (se aplicável)

    -- Timestamps
    baixado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enviado_whatsapp BOOLEAN DEFAULT FALSE,
    enviado_whatsapp_em TIMESTAMP,

    CONSTRAINT log_downloads_status_check CHECK (
        status IN ('sucesso', 'erro', 'cpf_nao_encontrado', 'sem_boleto',
                   'timeout', 'credenciais_invalidas', 'erro_navegacao')
    )
);

-- Índices para log_downloads_boletos
CREATE INDEX idx_log_downloads_cliente ON log_downloads_boletos(cliente_final_id);
CREATE INDEX idx_log_downloads_consultor ON log_downloads_boletos(consultor_id);
CREATE INDEX idx_log_downloads_boleto ON log_downloads_boletos(boleto_id);
CREATE INDEX idx_log_downloads_cpf ON log_downloads_boletos(cpf);
CREATE INDEX idx_log_downloads_status ON log_downloads_boletos(status);
CREATE INDEX idx_log_downloads_data ON log_downloads_boletos(baixado_em);
CREATE INDEX idx_log_downloads_mes_ano ON log_downloads_boletos(mes_referencia, ano_referencia);
CREATE INDEX idx_log_downloads_automacao ON log_downloads_boletos(automacao_id);
CREATE INDEX idx_log_downloads_whatsapp ON log_downloads_boletos(enviado_whatsapp);

COMMENT ON TABLE log_downloads_boletos IS 'Log detalhado de todas as tentativas de download de boletos';
COMMENT ON COLUMN log_downloads_boletos.status IS 'Status: sucesso, erro, cpf_nao_encontrado, sem_boleto, timeout, etc';
COMMENT ON COLUMN log_downloads_boletos.automacao_id IS 'UUID da execução batch (relaciona múltiplos downloads)';


-- ============================================================================
-- 6. TABELA DE EXECUÇÕES DA AUTOMAÇÃO
-- ============================================================================

CREATE TABLE IF NOT EXISTS execucoes_automacao (
    id SERIAL PRIMARY KEY,
    automacao_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(), -- Identificador único da execução

    -- Tipo e escopo
    tipo VARCHAR(50) NOT NULL, -- 'manual', 'agendada', 'teste'
    consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL, -- Null = todos

    -- Estatísticas
    total_clientes INTEGER DEFAULT 0,
    processados_sucesso INTEGER DEFAULT 0,
    processados_erro INTEGER DEFAULT 0,
    processados_nao_encontrado INTEGER DEFAULT 0,
    processados_sem_boleto INTEGER DEFAULT 0,

    -- Status e progresso
    status VARCHAR(50) NOT NULL DEFAULT 'iniciada', -- iniciada, em_andamento, concluida, erro, cancelada
    progresso_percentual DECIMAL(5, 2) DEFAULT 0.00, -- 0.00 a 100.00
    mensagem_atual TEXT, -- Mensagem de status atual

    -- Timing
    iniciado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalizado_em TIMESTAMP,
    tempo_total_segundos INTEGER,

    -- Informações adicionais
    parametros JSONB, -- Parâmetros da execução (JSON)
    usuario_execucao VARCHAR(100), -- Usuário que iniciou

    CONSTRAINT execucoes_tipo_check CHECK (
        tipo IN ('manual', 'agendada', 'teste')
    ),
    CONSTRAINT execucoes_status_check CHECK (
        status IN ('iniciada', 'em_andamento', 'concluida', 'erro', 'cancelada')
    )
);

-- Índices para execucoes_automacao
CREATE UNIQUE INDEX idx_execucoes_automacao_id ON execucoes_automacao(automacao_id);
CREATE INDEX idx_execucoes_status ON execucoes_automacao(status);
CREATE INDEX idx_execucoes_tipo ON execucoes_automacao(tipo);
CREATE INDEX idx_execucoes_consultor ON execucoes_automacao(consultor_id);
CREATE INDEX idx_execucoes_data_inicio ON execucoes_automacao(iniciado_em);

COMMENT ON TABLE execucoes_automacao IS 'Registro de cada execução batch da automação';
COMMENT ON COLUMN execucoes_automacao.automacao_id IS 'UUID único para rastrear todos os downloads de uma execução';


-- ============================================================================
-- 7. ALTER TABLE - ADICIONAR COLUNAS EM TABELAS EXISTENTES
-- ============================================================================

-- Adiciona colunas na tabela clientes_finais
DO $$
BEGIN
    -- Adicionar consultor_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='clientes_finais' AND column_name='consultor_id'
    ) THEN
        ALTER TABLE clientes_finais
        ADD COLUMN consultor_id INTEGER REFERENCES consultores(id) ON DELETE SET NULL;

        CREATE INDEX idx_clientes_finais_consultor ON clientes_finais(consultor_id);

        RAISE NOTICE '✅ Coluna consultor_id adicionada em clientes_finais';
    END IF;

    -- Adicionar ponto_venda
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='clientes_finais' AND column_name='ponto_venda'
    ) THEN
        ALTER TABLE clientes_finais
        ADD COLUMN ponto_venda VARCHAR(20);

        CREATE INDEX idx_clientes_finais_ponto_venda ON clientes_finais(ponto_venda);

        RAISE NOTICE '✅ Coluna ponto_venda adicionada em clientes_finais';
    END IF;
END $$;


-- ============================================================================
-- 8. DADOS INICIAIS - CONSULTORES
-- ============================================================================

INSERT INTO consultores (nome, email, telefone, whatsapp, empresa, ponto_venda, pasta_boletos, cor_identificacao, ativo)
VALUES
    ('Dayler', 'dayler@nexus.com', NULL, NULL, 'credms', '17.308', 'Dayler', NULL, TRUE),
    ('Neto', 'neto@nexus.com', NULL, NULL, 'credms', '17.308', 'Neto', 'verde', TRUE),
    ('Mirelli', 'mirelli@nexus.com', NULL, NULL, 'semicredito', '17.309', 'Mirelli', 'rosa', TRUE),
    ('Danner', 'danner@nexus.com', NULL, NULL, 'credms', '17.308', 'Danner', NULL, TRUE)
ON CONFLICT (nome) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

SELECT '✅ Consultores inseridos: Dayler, Neto (verde), Mirelli (rosa), Danner' as resultado;


-- ============================================================================
-- 9. DADOS INICIAIS - PONTOS DE VENDA
-- ============================================================================

INSERT INTO pontos_venda (codigo, nome, empresa, url_base, ativo)
VALUES
    ('17.308', 'CredMS - Ponto 17.308', 'credms', 'https://cnp3.consorciocanopus.com.br', TRUE),
    ('17.309', 'Semicrédito - Ponto 17.309', 'semicredito', 'https://cnp3.consorciocanopus.com.br', TRUE)
ON CONFLICT (codigo) DO UPDATE SET
    nome = EXCLUDED.nome,
    empresa = EXCLUDED.empresa;

SELECT '✅ Pontos de venda inseridos: 17.308 (CredMS), 17.309 (Semicrédito)' as resultado;


-- ============================================================================
-- 10. FUNÇÕES ÚTEIS
-- ============================================================================

-- Função para atualizar timestamp automaticamente
CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualizar updated_at
DROP TRIGGER IF EXISTS trigger_consultores_updated ON consultores;
CREATE TRIGGER trigger_consultores_updated
    BEFORE UPDATE ON consultores
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

DROP TRIGGER IF EXISTS trigger_credenciais_updated ON credenciais_canopus;
CREATE TRIGGER trigger_credenciais_updated
    BEFORE UPDATE ON credenciais_canopus
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();


-- Função para calcular progresso de execução
CREATE OR REPLACE FUNCTION calcular_progresso_execucao(p_automacao_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    v_total INTEGER;
    v_processados INTEGER;
    v_progresso DECIMAL;
BEGIN
    SELECT total_clientes INTO v_total
    FROM execucoes_automacao
    WHERE automacao_id = p_automacao_id;

    IF v_total IS NULL OR v_total = 0 THEN
        RETURN 0.00;
    END IF;

    SELECT
        processados_sucesso + processados_erro +
        processados_nao_encontrado + processados_sem_boleto
    INTO v_processados
    FROM execucoes_automacao
    WHERE automacao_id = p_automacao_id;

    v_progresso := (v_processados::DECIMAL / v_total::DECIMAL) * 100;

    RETURN ROUND(v_progresso, 2);
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 11. VIEWS ÚTEIS
-- ============================================================================

-- View de relatório por consultor
CREATE OR REPLACE VIEW vw_relatorio_downloads_consultor AS
SELECT
    c.id AS consultor_id,
    c.nome AS consultor_nome,
    c.empresa,
    c.cor_identificacao,
    COUNT(l.id) AS total_downloads,
    COUNT(CASE WHEN l.status = 'sucesso' THEN 1 END) AS sucessos,
    COUNT(CASE WHEN l.status = 'erro' THEN 1 END) AS erros,
    COUNT(CASE WHEN l.status = 'cpf_nao_encontrado' THEN 1 END) AS nao_encontrados,
    COUNT(CASE WHEN l.status = 'sem_boleto' THEN 1 END) AS sem_boleto,
    MAX(l.baixado_em) AS ultimo_download,
    AVG(l.tempo_execucao_segundos) AS tempo_medio_segundos
FROM consultores c
LEFT JOIN log_downloads_boletos l ON c.id = l.consultor_id
WHERE c.ativo = TRUE
GROUP BY c.id, c.nome, c.empresa, c.cor_identificacao
ORDER BY c.nome;

COMMENT ON VIEW vw_relatorio_downloads_consultor IS 'Relatório consolidado de downloads por consultor';


-- View de downloads recentes com problemas
CREATE OR REPLACE VIEW vw_downloads_com_problemas AS
SELECT
    l.id,
    l.baixado_em,
    c.nome AS consultor,
    l.cpf,
    l.nome_cliente,
    l.mes_referencia,
    l.ano_referencia,
    l.status,
    l.mensagem_erro
FROM log_downloads_boletos l
LEFT JOIN consultores c ON l.consultor_id = c.id
WHERE l.status != 'sucesso'
ORDER BY l.baixado_em DESC;

COMMENT ON VIEW vw_downloads_com_problemas IS 'Downloads que falharam ou tiveram problemas';


-- View de clientes staging pendentes
CREATE OR REPLACE VIEW vw_staging_pendentes AS
SELECT
    s.id,
    s.cpf,
    s.nome,
    s.ponto_venda,
    s.grupo,
    s.cota,
    c.nome AS consultor_nome,
    s.arquivo_origem,
    s.status,
    s.importado_em
FROM clientes_planilha_staging s
LEFT JOIN consultores c ON s.consultor_id = c.id
WHERE s.status IN ('pendente', 'erro')
ORDER BY s.importado_em DESC;

COMMENT ON VIEW vw_staging_pendentes IS 'Clientes importados pendentes de processamento';


-- View de execuções ativas
CREATE OR REPLACE VIEW vw_execucoes_ativas AS
SELECT
    e.automacao_id,
    e.tipo,
    c.nome AS consultor,
    e.total_clientes,
    e.processados_sucesso,
    e.processados_erro,
    e.status,
    e.progresso_percentual,
    e.mensagem_atual,
    e.iniciado_em,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - e.iniciado_em)) AS segundos_decorridos
FROM execucoes_automacao e
LEFT JOIN consultores c ON e.consultor_id = c.id
WHERE e.status IN ('iniciada', 'em_andamento')
ORDER BY e.iniciado_em DESC;

COMMENT ON VIEW vw_execucoes_ativas IS 'Execuções da automação atualmente em andamento';


-- View de estatísticas gerais
CREATE OR REPLACE VIEW vw_estatisticas_gerais AS
SELECT
    COUNT(DISTINCT l.cliente_final_id) AS total_clientes_com_boletos,
    COUNT(l.id) AS total_downloads_realizados,
    COUNT(CASE WHEN l.status = 'sucesso' THEN 1 END) AS total_sucessos,
    COUNT(CASE WHEN l.status = 'erro' THEN 1 END) AS total_erros,
    COUNT(CASE WHEN l.enviado_whatsapp = TRUE THEN 1 END) AS total_enviados_whatsapp,
    COUNT(CASE WHEN DATE(l.baixado_em) = CURRENT_DATE THEN 1 END) AS downloads_hoje,
    COUNT(CASE WHEN l.baixado_em >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) AS downloads_ultimos_7_dias,
    COUNT(CASE WHEN l.baixado_em >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) AS downloads_ultimos_30_dias
FROM log_downloads_boletos l;

COMMENT ON VIEW vw_estatisticas_gerais IS 'Estatísticas gerais da automação de boletos';


-- ============================================================================
-- 12. GRANTS (ajustar conforme necessário)
-- ============================================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO seu_usuario;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO seu_usuario;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO seu_usuario;


-- ============================================================================
-- 13. MENSAGEM FINAL
-- ============================================================================

SELECT '
============================================================================
✅ TABELAS DE AUTOMAÇÃO CANOPUS CRIADAS COM SUCESSO!
============================================================================

Tabelas criadas:
  1. consultores (4 consultores inseridos)
  2. pontos_venda (2 pontos inseridos)
  3. credenciais_canopus
  4. clientes_planilha_staging
  5. log_downloads_boletos
  6. execucoes_automacao

Alterações em tabelas existentes:
  - clientes_finais: adicionado consultor_id e ponto_venda

Views criadas:
  - vw_relatorio_downloads_consultor
  - vw_downloads_com_problemas
  - vw_staging_pendentes
  - vw_execucoes_ativas
  - vw_estatisticas_gerais

Próximos passos:
  1. Cadastrar credenciais do Canopus
  2. Preparar planilhas Excel dos consultores
  3. Configurar arquivo .env
  4. Executar automação de teste

============================================================================
' AS mensagem_final;
