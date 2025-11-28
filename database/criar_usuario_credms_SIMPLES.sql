-- ============================================================================
-- CRIAR USUÁRIO E EMPRESA CREDMS - VERSÃO SIMPLIFICADA
-- Email: credms@nexusbrasi.ai
-- Senha: credms123
-- CNPJ: 30.767.662/0001-52
-- WhatsApp: +55 67 9890-5585
-- ============================================================================
-- COMPATÍVEL COM BANCO QUE NÃO TEM TODAS AS MIGRATIONS
-- ============================================================================

BEGIN;

-- 1. INSERIR USUÁRIO
WITH novo_usuario AS (
    INSERT INTO usuarios (email, password_hash, tipo, ativo)
    VALUES (
        'credms@nexusbrasi.ai',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW', -- Senha: credms123
        'cliente',
        true
    )
    ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
    RETURNING id
),
-- 2. INSERIR EMPRESA
nova_empresa AS (
    INSERT INTO clientes_nexus (
        usuario_id,
        nome_empresa,
        cnpj,
        whatsapp_numero,
        email_contato,
        ativo
    )
    SELECT
        id,
        'CredMS - Nexus Brasil',
        '30.767.662/0001-52',
        '556798905585',
        'credms@nexusbrasi.ai',
        true
    FROM novo_usuario
    ON CONFLICT (cnpj) DO UPDATE
    SET
        email_contato = EXCLUDED.email_contato,
        whatsapp_numero = EXCLUDED.whatsapp_numero
    RETURNING id
),
-- 3. CONFIGURAÇÕES CLIENTE (se a tabela existir)
nova_config_cliente AS (
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
    FROM nova_empresa
    ON CONFLICT (cliente_nexus_id) DO NOTHING
    RETURNING id
),
-- 4. WHATSAPP SESSION
nova_sessao_whatsapp AS (
    INSERT INTO whatsapp_sessions (
        cliente_nexus_id,
        session_name,
        status,
        provider
    )
    SELECT
        id,
        'credms_session',
        'disconnected',
        'twilio'
    FROM nova_empresa
    ON CONFLICT (cliente_nexus_id) DO NOTHING
    RETURNING id
)
-- RETORNAR RESUMO
SELECT
    'USUÁRIO E EMPRESA CREDMS CRIADOS COM SUCESSO!' as status,
    nu.id as usuario_id,
    ne.id as empresa_id
FROM novo_usuario nu, nova_empresa ne;

COMMIT;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

SELECT
    'Verificação dos Dados Criados' as titulo;

SELECT
    u.id as usuario_id,
    u.email,
    u.tipo,
    u.ativo,
    cn.id as cliente_id,
    cn.nome_empresa,
    cn.cnpj,
    cn.whatsapp_numero,
    cn.email_contato
FROM usuarios u
JOIN clientes_nexus cn ON cn.usuario_id = u.id
WHERE u.email = 'credms@nexusbrasi.ai';

-- ============================================================================
-- CREDENCIAIS DE LOGIN
-- ============================================================================

SELECT
    'CREDENCIAIS DE ACESSO' as info;

SELECT
    'http://localhost:5000/login-cliente' as url_local,
    'https://nexus-crm-frontend.onrender.com/login-cliente' as url_render,
    'credms@nexusbrasi.ai' as email,
    'credms123' as senha;

-- ============================================================================
-- FIM
-- ============================================================================
