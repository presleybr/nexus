-- ============================================================================
-- SCRIPT PARA CRIAR USUÁRIO CREDMS NO RENDER
-- ============================================================================
-- Email: credms@nexusbrasi.ai
-- Senha: credms123
-- CNPJ: 30.767.662/0001-52
-- WhatsApp: +55 67 9890-5585
-- ============================================================================

-- 1. Limpar registros existentes (se houver)
DELETE FROM clientes_nexus WHERE email_contato = 'credms@nexusbrasi.ai';
DELETE FROM usuarios WHERE email = 'credms@nexusbrasi.ai';

-- 2. Criar usuário com hash correto (senha: credms123)
INSERT INTO usuarios (email, password_hash, tipo, ativo, created_at, updated_at)
VALUES (
    'credms@nexusbrasi.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW',
    'cliente',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 3. Criar cliente Nexus associado
INSERT INTO clientes_nexus (
    usuario_id,
    nome_empresa,
    cnpj,
    whatsapp_numero,
    email_contato,
    ativo,
    data_cadastro
)
SELECT
    u.id,
    'CredMS - Nexus Brasil',
    '30.767.662/0001-52',
    '556798905585',
    'credms@nexusbrasi.ai',
    true,
    CURRENT_TIMESTAMP
FROM usuarios u
WHERE u.email = 'credms@nexusbrasi.ai';

-- 4. Verificar criação
SELECT
    u.id,
    u.email,
    u.tipo,
    u.ativo,
    LENGTH(u.password_hash) as hash_length,
    c.nome_empresa,
    c.cnpj,
    c.whatsapp_numero
FROM usuarios u
LEFT JOIN clientes_nexus c ON c.usuario_id = u.id
WHERE u.email = 'credms@nexusbrasi.ai';
