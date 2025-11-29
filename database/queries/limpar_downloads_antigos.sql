-- ============================================================================
-- LIMPAR DOWNLOADS ANTIGOS - downloads_canopus
-- ============================================================================
-- Execute estas queries em ordem se a tabela estiver muito grande

-- PASSO 1: Ver quantos registros existem
SELECT
    COUNT(*) as total_registros,
    SUM(tamanho_bytes) / 1024 / 1024 as tamanho_total_mb,
    pg_size_pretty(pg_total_relation_size('downloads_canopus')) as tamanho_disco
FROM downloads_canopus;


-- PASSO 2: Ver quantos registros têm mais de 30 dias
SELECT
    COUNT(*) as total_mais_30_dias,
    SUM(tamanho_bytes) / 1024 / 1024 as espaco_mb_liberado
FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '30 days';


-- PASSO 3: DELETAR registros com mais de 30 dias
-- ⚠️ CUIDADO: Isso vai DELETAR permanentemente os registros!
-- Descomente as linhas abaixo para executar:

-- DELETE FROM downloads_canopus
-- WHERE data_download < NOW() - INTERVAL '30 days';


-- PASSO 4: VACUUM para liberar espaço em disco
-- Execute depois do DELETE:

-- VACUUM FULL downloads_canopus;


-- ============================================================================
-- ALTERNATIVA: Manter apenas os últimos 1000 registros
-- ============================================================================

-- Ver quantos seriam deletados:
SELECT COUNT(*) as total_deletar
FROM downloads_canopus
WHERE id NOT IN (
    SELECT id
    FROM downloads_canopus
    ORDER BY data_download DESC
    LIMIT 1000
);

-- Deletar (descomente para executar):
-- DELETE FROM downloads_canopus
-- WHERE id NOT IN (
--     SELECT id
--     FROM downloads_canopus
--     ORDER BY data_download DESC
--     LIMIT 1000
-- );


-- ============================================================================
-- VERIFICAR ESPAÇO APÓS LIMPEZA
-- ============================================================================

SELECT
    COUNT(*) as total_registros,
    SUM(tamanho_bytes) / 1024 / 1024 as tamanho_total_mb,
    pg_size_pretty(pg_total_relation_size('downloads_canopus')) as tamanho_disco
FROM downloads_canopus;
