-- ============================================================================
-- CRIAR USUÁRIO CREDMS NO BANCO DO RENDER
-- Execute este SQL no DBeaver conectado ao banco do Render
-- ============================================================================

-- LIMPAR usuário anterior (se existir)
DELETE FROM clientes_nexus WHERE email_contato = 'credms@nexusbrasi.ai';
DELETE FROM usuarios WHERE email = 'credms@nexusbrasi.ai';

-- CRIAR usuário
INSERT INTO usuarios (email, password_hash, tipo, ativo, created_at, updated_at)
VALUES (
    'credms@nexusbrasi.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5iGw4SY.oqhxW',
    'cliente',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- CRIAR empresa
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

-- VERIFICAR
SELECT
    '✅ USUÁRIO CRIADO COM SUCESSO NO RENDER!' as status;

SELECT
    u.id,
    u.email,
    u.tipo,
    u.ativo,
    cn.nome_empresa,
    cn.cnpj,
    cn.whatsapp_numero
FROM usuarios u
LEFT JOIN clientes_nexus cn ON cn.usuario_id = u.id
WHERE u.email = 'credms@nexusbrasi.ai';
