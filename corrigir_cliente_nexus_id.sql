-- Script para corrigir cliente_nexus_id dos boletos e clientes
-- Execute este script no DBeaver conectado ao banco do Render

-- 1. Verificar situação atual
SELECT
    'clientes_nexus' as tabela,
    id,
    nome_empresa,
    ativo
FROM clientes_nexus
ORDER BY id;

SELECT
    'clientes_finais' as info,
    cliente_nexus_id,
    COUNT(*) as total
FROM clientes_finais
GROUP BY cliente_nexus_id
ORDER BY cliente_nexus_id;

SELECT
    'boletos' as info,
    cliente_nexus_id,
    COUNT(*) as total
FROM boletos
GROUP BY cliente_nexus_id
ORDER BY cliente_nexus_id;

-- 2. Atualizar clientes_finais (onde cliente_nexus_id é NULL ou diferente de 3)
UPDATE clientes_finais
SET cliente_nexus_id = 3
WHERE cliente_nexus_id IS NULL OR cliente_nexus_id != 3;

-- 3. Atualizar boletos (onde cliente_nexus_id é NULL ou diferente de 3)
UPDATE boletos
SET cliente_nexus_id = 3
WHERE cliente_nexus_id IS NULL OR cliente_nexus_id != 3;

-- 4. Verificar resultado
SELECT
    'clientes_finais (após correção)' as info,
    cliente_nexus_id,
    COUNT(*) as total
FROM clientes_finais
GROUP BY cliente_nexus_id
ORDER BY cliente_nexus_id;

SELECT
    'boletos (após correção)' as info,
    cliente_nexus_id,
    COUNT(*) as total
FROM boletos
GROUP BY cliente_nexus_id
ORDER BY cliente_nexus_id;

-- 5. Verificar alguns boletos para confirmar
SELECT
    id,
    cliente_nexus_id,
    cliente_final_id,
    numero_boleto,
    mes_referencia,
    ano_referencia,
    pdf_filename,
    created_at
FROM boletos
ORDER BY created_at DESC
LIMIT 10;
