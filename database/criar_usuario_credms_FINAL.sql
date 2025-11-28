

-- CRIAR USU�RIO E EMPRESA EM UMA �NICA TRANSA��O
BEGIN;

-- 1. INSERIR USU�RIO (com senha criptografada em bcrypt)
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
-- 2. INSERIR EMPRESA CREDMS
nova_empresa AS (
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
        '30.767.662/0001-52',
        NULL,                    -- Sem telefone fixo
        '556798905585',          -- WhatsApp: +55 67 9890-5585 (apenas n�meros)
        'credms@nexusbrasi.ai',
        true
    FROM novo_usuario
    ON CONFLICT (cnpj) DO UPDATE
    SET
        email_contato = EXCLUDED.email_contato,
        whatsapp_numero = EXCLUDED.whatsapp_numero
    RETURNING id
),
-- 3. CRIAR CONFIGURA��ES PADR�O
nova_config_cliente AS (
    INSERT INTO configuracoes_cliente (
        cliente_nexus_id,
        mensagem_antibloqueio,
        intervalo_disparos,
        horario_disparo
    )
    SELECT
        id,
        'Ol�! Segue em anexo seu boleto. Qualquer d�vida, estamos � disposi��o!',
        5,
        '09:00:00'
    FROM nova_empresa
    ON CONFLICT (cliente_nexus_id) DO NOTHING
    RETURNING id
),
-- 4. CRIAR CONFIGURA��ES DE AUTOMA��O
nova_config_automacao AS (
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
        false,  -- Automa��o desabilitada por padr�o
        1,      -- Dia 1 do m�s
        3,      -- 3 dias antes do vencimento
        '09:00:00',
        'Ol�! Tudo bem? Segue em anexo seu boleto. Qualquer d�vida, estamos � disposi��o!',
        3,      -- Intervalo m�nimo 3 segundos
        7,      -- Intervalo m�ximo 7 segundos
        20,     -- Pausa ap�s 20 disparos
        60      -- Pausa de 60 segundos
    FROM nova_empresa
    ON CONFLICT (cliente_nexus_id) DO NOTHING
    RETURNING id
),
-- 5. CRIAR SESS�O WHATSAPP INICIAL
nova_sessao_whatsapp AS (
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
        NULL,  -- Configurar depois com Account SID real do Twilio
        NULL   -- Configurar depois com n�mero Twilio real
    FROM nova_empresa
    ON CONFLICT (cliente_nexus_id) DO NOTHING
    RETURNING id
)
-- 6. RETORNAR RESUMO DA CRIA��O
SELECT
    'USU�RIO E EMPRESA CREDMS CRIADOS COM SUCESSO!' as status,
    nu.id as usuario_id,
    ne.id as empresa_id
FROM novo_usuario nu, nova_empresa ne;

COMMIT;

-- ============================================================================
-- VERIFICA��O COMPLETA - Execute para conferir tudo
-- ============================================================================

SELECT
    '========================================' as separador,
    'DADOS DA EMPRESA CREDMS' as titulo,
    '========================================' as separador2;

SELECT
    u.id as usuario_id,
    u.email,
    u.tipo as tipo_usuario,
    u.ativo as usuario_ativo,
    u.created_at as data_cadastro_usuario,

    cn.id as cliente_nexus_id,
    cn.nome_empresa,
    cn.cnpj,
    cn.telefone,
    cn.whatsapp_numero,
    cn.email_contato,
    cn.ativo as empresa_ativa,
    cn.data_cadastro as data_cadastro_empresa,

    cc.id as config_cliente_id,
    cc.mensagem_antibloqueio,
    cc.intervalo_disparos,
    cc.horario_disparo,

    ca.id as config_automacao_id,
    ca.disparo_automatico_habilitado,
    ca.dia_do_mes,
    ca.dias_antes_vencimento,
    ca.intervalo_min_segundos,
    ca.intervalo_max_segundos,

    ws.id as whatsapp_session_id,
    ws.status as whatsapp_status,
    ws.provider as whatsapp_provider,
    ws.session_name

FROM usuarios u
JOIN clientes_nexus cn ON cn.usuario_id = u.id
LEFT JOIN configuracoes_cliente cc ON cc.cliente_nexus_id = cn.id
LEFT JOIN configuracoes_automacao ca ON ca.cliente_nexus_id = cn.id
LEFT JOIN whatsapp_sessions ws ON ws.cliente_nexus_id = cn.id
WHERE u.email = 'credms@nexusbrasi.ai';

-- ============================================================================
-- INFORMA��ES DE LOGIN
-- ============================================================================

SELECT
    '========================================' as separador,
    'CREDENCIAIS DE LOGIN' as titulo,
    '========================================' as separador2;

SELECT
    'http://localhost:5000/login-cliente' as url_login_local,
    'https://nexus-crm-frontend.onrender.com/login-cliente' as url_login_render,
    'credms@nexusbrasi.ai' as email,
    'credms123' as senha,
    '30.767.662/0001-52' as cnpj,
    '+55 67 9890-5585' as whatsapp,
    '556798905585' as whatsapp_formato_banco;

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
