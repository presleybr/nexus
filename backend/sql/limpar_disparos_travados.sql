-- Limpar todos os disparos travados (em andamento há mais de 10 minutos)
-- Isso resolve disparos que ficaram presos devido a erros

UPDATE historico_disparos
SET status = 'erro',
    detalhes = '{"mensagem": "Disparo cancelado automaticamente - estava travado"}'::jsonb
WHERE status = 'em_andamento'
AND horario_execucao < NOW() - INTERVAL '10 minutes';

-- Verificar o que foi atualizado
SELECT
    id,
    tipo_disparo,
    horario_execucao,
    status,
    detalhes
FROM historico_disparos
WHERE status = 'erro'
AND detalhes->>'mensagem' LIKE '%travado%'
ORDER BY horario_execucao DESC
LIMIT 10;
