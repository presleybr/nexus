-- ============================================================================
-- 🚨 EMERGÊNCIA: MATAR CONEXÕES E LIMPAR BANCO
-- ============================================================================
-- Execute este script quando o banco travar com "Datasource was invalidated"

-- ============================================================================
-- 1. VER CONEXÕES ATIVAS
-- ============================================================================
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    state_change,
    NOW() - state_change AS duracao,
    query
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid <> pg_backend_pid()
ORDER BY state_change;


-- ============================================================================
-- 2. MATAR TODAS AS CONEXÕES IDLE (Paradas há mais de 5 minutos)
-- ============================================================================
SELECT
    pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database()
  AND state = 'idle'
  AND NOW() - state_change > INTERVAL '5 minutes'
  AND pid <> pg_backend_pid();


-- ============================================================================
-- 3. MATAR TODAS AS CONEXÕES IDLE IN TRANSACTION (Transações travadas)
-- ============================================================================
SELECT
    pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database()
  AND state = 'idle in transaction'
  AND NOW() - state_change > INTERVAL '2 minutes'
  AND pid <> pg_backend_pid();


-- ============================================================================
-- 4. MATAR TODAS AS CONEXÕES (EMERGÊNCIA TOTAL)
-- ============================================================================
-- ⚠️ USE APENAS EM CASO EXTREMO! Vai derrubar todas as conexões
-- Descomente as linhas abaixo para executar:

-- SELECT
--     pg_terminate_backend(pid)
-- FROM pg_stat_activity
-- WHERE datname = current_database()
--   AND pid <> pg_backend_pid();


-- ============================================================================
-- 5. LIMPAR DUPLICATAS EM clientes_finais
-- ============================================================================
-- Ver quantas duplicatas existem:
SELECT
    cpf,
    COUNT(*) as total_duplicatas,
    array_agg(id ORDER BY created_at DESC) as ids
FROM clientes_finais
GROUP BY cpf
HAVING COUNT(*) > 1
ORDER BY total_duplicatas DESC;

-- Deletar duplicatas (mantém apenas o mais recente):
-- ⚠️ BACKUP ANTES! Descomente para executar:

-- DELETE FROM clientes_finais
-- WHERE id IN (
--     SELECT id
--     FROM (
--         SELECT id,
--                ROW_NUMBER() OVER (
--                    PARTITION BY cpf
--                    ORDER BY created_at DESC
--                ) as rn
--         FROM clientes_finais
--     ) t
--     WHERE rn > 1
-- );


-- ============================================================================
-- 6. LIMPAR DUPLICATAS EM boletos
-- ============================================================================
-- Ver quantas duplicatas existem:
SELECT
    cliente_final_id,
    numero_boleto,
    COUNT(*) as total_duplicatas,
    array_agg(id ORDER BY created_at DESC) as ids
FROM boletos
GROUP BY cliente_final_id, numero_boleto
HAVING COUNT(*) > 1
ORDER BY total_duplicatas DESC;

-- Deletar duplicatas (mantém apenas o mais recente):
-- ⚠️ BACKUP ANTES! Descomente para executar:

-- DELETE FROM boletos
-- WHERE id IN (
--     SELECT id
--     FROM (
--         SELECT id,
--                ROW_NUMBER() OVER (
--                    PARTITION BY cliente_final_id, numero_boleto
--                    ORDER BY created_at DESC
--                ) as rn
--         FROM boletos
--     ) t
--     WHERE rn > 1
-- );


-- ============================================================================
-- 7. LIMPAR REGISTROS ANTIGOS (Liberar Espaço)
-- ============================================================================
-- Deletar downloads_canopus com mais de 7 dias:
SELECT COUNT(*) as total_deletar
FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '7 days';

-- Execute para deletar (descomente):
-- DELETE FROM downloads_canopus
-- WHERE data_download < NOW() - INTERVAL '7 days';


-- ============================================================================
-- 8. VACUUM E REINDEX (Limpar e Reorganizar)
-- ============================================================================
-- Liberar espaço em disco e reorganizar índices:
VACUUM FULL ANALYZE clientes_finais;
VACUUM FULL ANALYZE boletos;
VACUUM FULL ANALYZE downloads_canopus;

REINDEX TABLE clientes_finais;
REINDEX TABLE boletos;
REINDEX TABLE downloads_canopus;


-- ============================================================================
-- 9. VERIFICAR ESTATÍSTICAS FINAIS
-- ============================================================================
SELECT
    'clientes_finais' as tabela,
    COUNT(*) as total_registros,
    pg_size_pretty(pg_total_relation_size('clientes_finais')) as tamanho
FROM clientes_finais
UNION ALL
SELECT
    'boletos' as tabela,
    COUNT(*) as total_registros,
    pg_size_pretty(pg_total_relation_size('boletos')) as tamanho
FROM boletos
UNION ALL
SELECT
    'downloads_canopus' as tabela,
    COUNT(*) as total_registros,
    pg_size_pretty(pg_total_relation_size('downloads_canopus')) as tamanho
FROM downloads_canopus;


-- ============================================================================
-- 10. CONFIGURAR TIMEOUTS (Evitar problema futuro)
-- ============================================================================
-- Configurar timeout de conexões idle:
ALTER DATABASE nexus_crm SET idle_in_transaction_session_timeout = '5min';
ALTER DATABASE nexus_crm SET statement_timeout = '30s';
