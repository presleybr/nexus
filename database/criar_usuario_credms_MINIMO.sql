-- ============================================================================
-- CRIAR USUÁRIO CREDMS - VERSÃO MÍNIMA
-- Apenas usuário e empresa (sem configurações extras)
-- Email: credms@nexusbrasi.ai
-- Senha: credms123
-- ============================================================================

BEGIN;

-- 1. INSERIR USUÁRIO
INSERT INTO usuarios (email, password_hash, tipo, ativo)
VALUES (
    'credms@nexusbrasi.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW', -- Senha: credms123
    'cliente',
    true
)
ON CONFLICT (email) DO UPDATE
SET password_hash = EXCLUDED.password_hash;

-- 2. INSERIR EMPRESA
INSERT INTO clientes_nexus (
    usuario_id,
    nome_empresa,
    cnpj,
    whatsapp_numero,
    email_contato,
    ativo
)
SELECT
    u.id,
    'CredMS - Nexus Brasil',
    '30.767.662/0001-52',
    '556798905585',
    'credms@nexusbrasi.ai',
    true
FROM usuarios u
WHERE u.email = 'credms@nexusbrasi.ai'
ON CONFLICT (cnpj) DO UPDATE
SET
    email_contato = EXCLUDED.email_contato,
    whatsapp_numero = EXCLUDED.whatsapp_numero;

COMMIT;

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================

SELECT
    '✅ USUÁRIO CRIADO COM SUCESSO!' as status;

SELECT
    u.id as usuario_id,
    u.email,
    u.tipo,
    u.ativo,
    cn.id as cliente_id,
    cn.nome_empresa,
    cn.cnpj,
    cn.whatsapp_numero
FROM usuarios u
LEFT JOIN clientes_nexus cn ON cn.usuario_id = u.id
WHERE u.email = 'credms@nexusbrasi.ai';

-- ============================================================================
-- CREDENCIAIS
-- ============================================================================

SELECT
    '📋 CREDENCIAIS DE ACESSO' as info;

SELECT
    'credms@nexusbrasi.ai' as email,
    'credms123' as senha,
    'http://localhost:5000/login-cliente' as url_local;
