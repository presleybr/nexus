-- ============================================================================
-- CRIAR USUÁRIO CREDMS - VERSÃO ULTRA MÍNIMA
-- APENAS usuário e empresa (NADA MAIS!)
-- Email: credms@nexusbrasi.ai
-- Senha: credms123
-- ============================================================================

-- 1. CRIAR USUÁRIO
INSERT INTO usuarios (email, password_hash, tipo, ativo)
VALUES (
    'credms@nexusbrasi.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW',
    'cliente',
    true
)
ON CONFLICT (email) DO NOTHING;

-- 2. CRIAR EMPRESA
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
ON CONFLICT (cnpj) DO NOTHING;

-- 3. VERIFICAR
SELECT
    u.id,
    u.email,
    cn.nome_empresa,
    cn.cnpj
FROM usuarios u
LEFT JOIN clientes_nexus cn ON cn.usuario_id = u.id
WHERE u.email = 'credms@nexusbrasi.ai';
