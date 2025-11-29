-- ============================================================================
-- QUERIES SEGURAS PARA VISUALIZAR downloads_canopus
-- ============================================================================
-- Use estas queries no DBeaver ao invés de "SELECT *"
-- para evitar erro de I/O ao carregar PDFs base64 grandes

-- 1. RESUMO DA TABELA (sem dados binários)
-- Mostra informações básicas sem carregar os PDFs
SELECT
    id,
    consultor_id,
    cpf,
    nome_arquivo,
    LENGTH(caminho_arquivo) as tamanho_base64,  -- Mostra tamanho do base64
    tamanho_bytes,
    status,
    data_download,
    created_at,
    updated_at
FROM downloads_canopus
ORDER BY created_at DESC
LIMIT 100;  -- Limitar resultados


-- 2. ESTATÍSTICAS DA TABELA
-- Ver quantos registros e tamanho total
SELECT
    COUNT(*) as total_registros,
    SUM(tamanho_bytes) / 1024 / 1024 as tamanho_total_mb,
    AVG(tamanho_bytes) / 1024 as tamanho_medio_kb,
    MIN(data_download) as primeiro_download,
    MAX(data_download) as ultimo_download,
    COUNT(DISTINCT cpf) as total_cpfs_unicos,
    COUNT(DISTINCT consultor_id) as total_consultores
FROM downloads_canopus;


-- 3. DOWNLOADS POR CONSULTOR
-- Ver quantos downloads por consultor
SELECT
    consultor_id,
    COUNT(*) as total_downloads,
    SUM(tamanho_bytes) / 1024 / 1024 as tamanho_total_mb,
    MIN(data_download) as primeiro_download,
    MAX(data_download) as ultimo_download
FROM downloads_canopus
GROUP BY consultor_id
ORDER BY total_downloads DESC;


-- 4. ÚLTIMOS 50 DOWNLOADS (sem base64)
-- Ver os downloads mais recentes sem carregar PDFs
SELECT
    id,
    consultor_id,
    cpf,
    nome_arquivo,
    ROUND(tamanho_bytes::numeric / 1024, 2) as tamanho_kb,
    status,
    data_download,
    created_at
FROM downloads_canopus
ORDER BY data_download DESC
LIMIT 50;


-- 5. BUSCAR UM DOWNLOAD ESPECÍFICO POR CPF (sem base64)
-- Substitua '12345678900' pelo CPF que você quer buscar
SELECT
    id,
    consultor_id,
    cpf,
    nome_arquivo,
    LENGTH(caminho_arquivo) as tamanho_base64,
    tamanho_bytes,
    status,
    data_download
FROM downloads_canopus
WHERE cpf = '12345678900';


-- 6. OBTER PDF BASE64 DE UM REGISTRO ESPECÍFICO
-- Use apenas quando precisar do PDF (substitua o ID)
-- ⚠️ CUIDADO: Isso pode ser lento com PDFs grandes
SELECT
    id,
    nome_arquivo,
    caminho_arquivo  -- Este campo contém o base64
FROM downloads_canopus
WHERE id = 1;  -- Substitua pelo ID desejado


-- 7. DOWNLOADS COM ERRO
-- Ver se há downloads com status de erro
SELECT
    id,
    consultor_id,
    cpf,
    nome_arquivo,
    status,
    data_download
FROM downloads_canopus
WHERE status != 'sucesso'
ORDER BY data_download DESC;


-- 8. DOWNLOADS DUPLICADOS
-- Ver se há PDFs baixados mais de uma vez
SELECT
    cpf,
    nome_arquivo,
    COUNT(*) as total_duplicados
FROM downloads_canopus
GROUP BY cpf, nome_arquivo
HAVING COUNT(*) > 1
ORDER BY total_duplicados DESC;
