-- ============================================================================
-- CRIAR USUÁRIO E EMPRESA CREDMS
-- Email: credms@nexusbrasi.ai
-- Senha: credms123
-- ============================================================================

-- 1. INSERIR USUÁRIO (com senha criptografada em bcrypt)
INSERT INTO usuarios (email, password_hash, tipo, ativo)
VALUES (
    'credms@nexusbrasi.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW', -- Hash de "credms123"
    'cliente',
    true
)
ON CONFLICT (email) DO NOTHING
RETURNING id;

-- 2. INSERIR EMPRESA CREDMS
-- IMPORTANTE: Substitua <USUARIO_ID> pelo ID retornado acima
-- Ou execute tudo de uma vez usando WITH

WITH novo_usuario AS (
    INSERT INTO usuarios (email, password_hash, tipo, ativo)
    VALUES (
        'credms@nexusbrasi.ai',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW',
        'cliente',
        true
    )
    ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
    RETURNING id
)
INSERT INTO clientes_nexus (
    usuario_id,
    nome_empresa,
    cnpj,
    telefone,
    whatsapp_numero,
    email_contato,
    ativo
)
SELECT
    id,
    'CredMS - Nexus Brasil',
    '00.000.000/0001-00', -- Substitua pelo CNPJ real
    '(67) 99999-0000',    -- Substitua pelo telefone real
    '5567999990000',      -- Substitua pelo WhatsApp real (apenas números)
    'credms@nexusbrasi.ai',
    true
FROM novo_usuario
ON CONFLICT (cnpj) DO NOTHING
RETURNING id;

-- 3. CRIAR CONFIGURAÇÕES PADRÃO PARA O CLIENTE
WITH cliente_credms AS (
    SELECT id FROM clientes_nexus WHERE email_contato = 'credms@nexusbrasi.ai'
)
INSERT INTO configuracoes_cliente (
    cliente_nexus_id,
    mensagem_antibloqueio,
    intervalo_disparos,
    horario_disparo
)
SELECT
    id,
    'Olá! Segue em anexo seu boleto. Qualquer dúvida, estamos à disposição!',
    5,
    '09:00:00'
FROM cliente_credms
ON CONFLICT (cliente_nexus_id) DO NOTHING;

-- 4. CRIAR CONFIGURAÇÕES DE AUTOMAÇÃO
WITH cliente_credms AS (
    SELECT id FROM clientes_nexus WHERE email_contato = 'credms@nexusbrasi.ai'
)
INSERT INTO configuracoes_automacao (
    cliente_nexus_id,
    disparo_automatico_habilitado,
    dia_do_mes,
    dias_antes_vencimento,
    horario_disparo,
    mensagem_antibloqueio,
    intervalo_min_segundos,
    intervalo_max_segundos,
    pausa_apos_disparos,
    tempo_pausa_segundos
)
SELECT
    id,
    false,  -- Automação desabilitada por padrão
    1,      -- Dia 1 do mês
    3,      -- 3 dias antes do vencimento
    '09:00:00',
    'Olá! Tudo bem? Segue em anexo seu boleto. Qualquer dúvida, estamos à disposição!',
    3,      -- Intervalo mínimo 3 segundos
    7,      -- Intervalo máximo 7 segundos
    20,     -- Pausa após 20 disparos
    60      -- Pausa de 60 segundos
FROM cliente_credms
ON CONFLICT (cliente_nexus_id) DO NOTHING;

-- 5. CRIAR SESSÃO WHATSAPP INICIAL (Twilio)
WITH cliente_credms AS (
    SELECT id FROM clientes_nexus WHERE email_contato = 'credms@nexusbrasi.ai'
)
INSERT INTO whatsapp_sessions (
    cliente_nexus_id,
    session_name,
    status,
    provider,
    twilio_account_sid,
    twilio_phone
)
SELECT
    id,
    'credms_session',
    'disconnected',
    'twilio',
    'AC3daccc77955ee03eccdd580bf494bb08',  -- Substitua pelo Account SID real
    'whatsapp:+14155238886'                 -- Substitua pelo número Twilio real
FROM cliente_credms
ON CONFLICT (cliente_nexus_id) DO NOTHING;

-- ============================================================================
-- VERIFICAÇÃO - Execute para conferir se tudo foi criado
-- ============================================================================

SELECT
    u.id as usuario_id,
    u.email,
    u.tipo,
    u.ativo as usuario_ativo,
    cn.id as cliente_nexus_id,
    cn.nome_empresa,
    cn.cnpj,
    cn.whatsapp_numero,
    cn.email_contato,
    cn.ativo as empresa_ativa,
    cc.mensagem_antibloqueio,
    ca.disparo_automatico_habilitado,
    ws.status as whatsapp_status,
    ws.provider as whatsapp_provider
FROM usuarios u
JOIN clientes_nexus cn ON cn.usuario_id = u.id
LEFT JOIN configuracoes_cliente cc ON cc.cliente_nexus_id = cn.id
LEFT JOIN configuracoes_automacao ca ON ca.cliente_nexus_id = cn.id
LEFT JOIN whatsapp_sessions ws ON ws.cliente_nexus_id = cn.id
WHERE u.email = 'credms@nexusbrasi.ai';

-- ============================================================================
-- LOGIN NO SISTEMA
-- ============================================================================
-- Acesse: http://localhost:5000/login-cliente
-- Email: credms@nexusbrasi.ai
-- Senha: credms123
-- ============================================================================
