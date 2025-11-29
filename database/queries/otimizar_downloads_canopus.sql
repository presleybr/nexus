-- ============================================================================
-- OTIMIZAÇÃO E MANUTENÇÃO: downloads_canopus
-- ============================================================================

-- PROBLEMA: Tabela com muitos PDFs base64 grandes causa timeout/erro I/O
-- SOLUÇÃO: Limpar registros antigos, criar índices, vacuum

-- ============================================================================
-- 1. LIMPAR DOWNLOADS ANTIGOS (mais de 90 dias)
-- ============================================================================
-- ATENÇÃO: Execute com cuidado! Isso DELETA registros antigos.
-- Recomendado: Fazer backup antes de executar

-- Primeiro, ver quantos registros seriam deletados:
SELECT
    COUNT(*) as total_para_deletar,
    MIN(data_download) as mais_antigo,
    MAX(data_download) as mais_recente,
    SUM(tamanho_bytes) / 1024 / 1024 as espaco_mb_liberado
FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '90 days';

-- Se estiver OK, execute o DELETE:
-- DELETE FROM downloads_canopus
-- WHERE data_download < NOW() - INTERVAL '90 days';


-- ============================================================================
-- 2. LIMPAR DUPLICATAS (manter apenas o mais recente)
-- ============================================================================
-- Ver duplicatas antes de deletar:
SELECT
    cpf,
    nome_arquivo,
    COUNT(*) as total,
    array_agg(id ORDER BY data_download DESC) as ids,
    MAX(data_download) as mais_recente
FROM downloads_canopus
GROUP BY cpf, nome_arquivo
HAVING COUNT(*) > 1
ORDER BY total DESC;

-- Deletar duplicatas (mantém o mais recente):
-- DELETE FROM downloads_canopus
-- WHERE id IN (
--     SELECT id
--     FROM (
--         SELECT id,
--                ROW_NUMBER() OVER (
--                    PARTITION BY cpf, nome_arquivo
--                    ORDER BY data_download DESC
--                ) as rn
--         FROM downloads_canopus
--     ) t
--     WHERE rn > 1
-- );


-- ============================================================================
-- 3. CRIAR ÍNDICES PARA MELHORAR PERFORMANCE
-- ============================================================================
-- Índices ajudam queries específicas a rodar mais rápido

-- Índice por CPF (muito usado nas buscas)
CREATE INDEX IF NOT EXISTS idx_downloads_canopus_cpf
ON downloads_canopus(cpf);

-- Índice por consultor_id
CREATE INDEX IF NOT EXISTS idx_downloads_canopus_consultor
ON downloads_canopus(consultor_id);

-- Índice por data_download (para ordenação e filtros por data)
CREATE INDEX IF NOT EXISTS idx_downloads_canopus_data
ON downloads_canopus(data_download DESC);

-- Índice composto CPF + nome_arquivo (detectar duplicatas rápido)
CREATE INDEX IF NOT EXISTS idx_downloads_canopus_cpf_arquivo
ON downloads_canopus(cpf, nome_arquivo);

-- Índice por status
CREATE INDEX IF NOT EXISTS idx_downloads_canopus_status
ON downloads_canopus(status);


-- ============================================================================
-- 4. VACUUM E ANALYZE (limpar espaço e atualizar estatísticas)
-- ============================================================================
-- VACUUM remove registros deletados fisicamente
-- ANALYZE atualiza estatísticas para o otimizador de queries

-- VACUUM completo (libera espaço):
VACUUM FULL downloads_canopus;

-- ANALYZE (atualiza estatísticas):
ANALYZE downloads_canopus;

-- Ou fazer tudo de uma vez:
VACUUM FULL ANALYZE downloads_canopus;


-- ============================================================================
-- 5. VERIFICAR TAMANHO DA TABELA
-- ============================================================================
SELECT
    pg_size_pretty(pg_total_relation_size('downloads_canopus')) as tamanho_total,
    pg_size_pretty(pg_table_size('downloads_canopus')) as tamanho_tabela,
    pg_size_pretty(pg_indexes_size('downloads_canopus')) as tamanho_indices;


-- ============================================================================
-- 6. PARTICIONAMENTO (avançado - se tabela ficar MUITO grande)
-- ============================================================================
-- Se a tabela crescer muito (milhões de registros), considere particionar por data.
-- Isso divide a tabela em pedaços menores por mês/ano.

-- Exemplo: Criar tabela particionada por mês
-- (APENAS execute se realmente necessário)

-- CREATE TABLE downloads_canopus_partitioned (
--     LIKE downloads_canopus INCLUDING ALL
-- ) PARTITION BY RANGE (data_download);

-- CREATE TABLE downloads_canopus_2025_01 PARTITION OF downloads_canopus_partitioned
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- CREATE TABLE downloads_canopus_2025_02 PARTITION OF downloads_canopus_partitioned
--     FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- (Depois migrar dados da tabela antiga para a particionada)


-- ============================================================================
-- 7. CONFIGURAR AUTOVACUUM (ajustar se necessário)
-- ============================================================================
-- O PostgreSQL tem AUTOVACUUM automático, mas você pode ajustar:

-- ALTER TABLE downloads_canopus SET (
--     autovacuum_vacuum_scale_factor = 0.1,  -- Vacuum quando 10% mudar
--     autovacuum_analyze_scale_factor = 0.05  -- Analyze quando 5% mudar
-- );
