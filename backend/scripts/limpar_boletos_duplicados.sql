-- Script para remover boletos duplicados
-- Mantém apenas o boleto mais antigo (menor ID) de cada cliente/mês/ano

-- 1. Ver quantos duplicados existem
SELECT
    cliente_final_id,
    mes_referencia,
    ano_referencia,
    COUNT(*) as quantidade,
    STRING_AGG(id::text, ', ') as ids_duplicados
FROM boletos
GROUP BY cliente_final_id, mes_referencia, ano_referencia
HAVING COUNT(*) > 1
ORDER BY quantidade DESC;

-- 2. DELETAR DUPLICADOS (mantém apenas o mais antigo)
-- ATENÇÃO: Execute esta query com cuidado!
WITH duplicados AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY cliente_final_id, mes_referencia, ano_referencia
            ORDER BY id ASC  -- Mantém o mais antigo (menor ID)
        ) as rn
    FROM boletos
)
DELETE FROM boletos
WHERE id IN (
    SELECT id FROM duplicados WHERE rn > 1
);

-- 3. Verificar resultado - deve retornar 0 linhas
SELECT
    cliente_final_id,
    mes_referencia,
    ano_referencia,
    COUNT(*) as quantidade
FROM boletos
GROUP BY cliente_final_id, mes_referencia, ano_referencia
HAVING COUNT(*) > 1;
