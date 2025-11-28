-- Script para verificar e entender a estrutura de IDs

-- 1. Ver todos os usuários
SELECT
    'USUARIOS' as tabela,
    id,
    email,
    tipo,
    ativo
FROM usuarios
ORDER BY id;

-- 2. Ver todos os clientes_nexus e seus usuários
SELECT
    'CLIENTES_NEXUS' as tabela,
    cn.id as cliente_nexus_id,
    cn.usuario_id,
    cn.nome_empresa,
    cn.ativo,
    u.email as usuario_email
FROM clientes_nexus cn
LEFT JOIN usuarios u ON cn.usuario_id = u.id
ORDER BY cn.id;

-- 3. Ver distribuição de boletos por cliente_nexus_id
SELECT
    'DISTRIBUIÇÃO BOLETOS' as info,
    cliente_nexus_id,
    COUNT(*) as total_boletos
FROM boletos
GROUP BY cliente_nexus_id
ORDER BY cliente_nexus_id;

-- 4. Ver distribuição de clientes_finais por cliente_nexus_id
SELECT
    'DISTRIBUIÇÃO CLIENTES' as info,
    cliente_nexus_id,
    COUNT(*) as total_clientes
FROM clientes_finais
GROUP BY cliente_nexus_id
ORDER BY cliente_nexus_id;

-- 5. Ver alguns boletos recentes com seus relacionamentos
SELECT
    'BOLETOS RECENTES' as info,
    b.id as boleto_id,
    b.cliente_nexus_id,
    b.cliente_final_id,
    cf.nome_completo as cliente_nome,
    b.numero_boleto,
    b.mes_referencia,
    b.ano_referencia,
    b.pdf_size,
    b.created_at
FROM boletos b
LEFT JOIN clientes_finais cf ON b.cliente_final_id = cf.id
ORDER BY b.created_at DESC
LIMIT 10;
