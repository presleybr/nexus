-- ============================================================================
-- Migration: Adicionar credenciais do PV 17308
-- Data: 2025-12-04
-- Descrição: Insere credenciais do Ponto de Venda 17308 na tabela credenciais_canopus
-- ============================================================================

-- Verificar se já existe e inserir/atualizar
INSERT INTO credenciais_canopus (ponto_venda, usuario, senha, codigo_empresa, ativo, created_at, updated_at)
VALUES (
    '17308',            -- ponto_venda
    '17308',            -- usuario (mesmo que o PV, será formatado com zfill(10) no login)
    'Sonhorealizado2@', -- senha
    '0101',             -- codigo_empresa (mesmo do PV 24627)
    true,               -- ativo
    NOW(),              -- created_at
    NOW()               -- updated_at
)
ON CONFLICT (ponto_venda) DO UPDATE SET
    usuario = EXCLUDED.usuario,
    senha = EXCLUDED.senha,
    codigo_empresa = EXCLUDED.codigo_empresa,
    ativo = EXCLUDED.ativo,
    updated_at = NOW();

-- Verificar resultado
SELECT ponto_venda, usuario, codigo_empresa, ativo, created_at, updated_at
FROM credenciais_canopus
WHERE ponto_venda IN ('17308', '24627')
ORDER BY ponto_venda;
