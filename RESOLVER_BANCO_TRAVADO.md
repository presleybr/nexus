# 🚨 EMERGÊNCIA: Banco de Dados Travado

## Sintomas:
- ❌ "Datasource was invalidated"
- ❌ "Live connection count: 3/3"
- ❌ Frontend mostra 1000 boletos
- ❌ Usuários duplicados 10 vezes
- ❌ Erro I/O na tabela downloads_canopus
- ❌ Sistema inteiro não funciona

## Causa:
**Vazamento de conexões** - O backend abre conexões com PostgreSQL mas não fecha corretamente. Render Free Tier limita a 3 conexões simultâneas.

---

## 🆘 SOLUÇÃO IMEDIATA (Execute AGORA):

### 1. **Acesse o Render Dashboard**
   - https://dashboard.render.com/
   - PostgreSQL > nexus-crm-db > **Queries**

### 2. **MATAR TODAS AS CONEXÕES**

Cole e execute este SQL:

```sql
-- Ver quais conexões estão ativas
SELECT
    pid,
    usename,
    state,
    NOW() - state_change AS duracao,
    LEFT(query, 50) as query_inicio
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid <> pg_backend_pid()
ORDER BY state_change;

-- MATAR TODAS (EMERGÊNCIA)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid <> pg_backend_pid();
```

✅ Isso vai liberar todas as 3 conexões travadas!

---

### 3. **LIMPAR DUPLICATAS**

#### a) Ver quantas duplicatas existem:

```sql
-- Duplicatas em clientes_finais
SELECT
    cpf,
    COUNT(*) as total,
    MIN(id) as id_manter,
    array_agg(id ORDER BY created_at DESC) as todos_ids
FROM clientes_finais
GROUP BY cpf
HAVING COUNT(*) > 1
ORDER BY total DESC
LIMIT 20;

-- Duplicatas em boletos
SELECT
    numero_boleto,
    COUNT(*) as total,
    array_agg(id ORDER BY created_at DESC) as todos_ids
FROM boletos
GROUP BY numero_boleto
HAVING COUNT(*) > 1
ORDER BY total DESC
LIMIT 20;
```

#### b) Deletar duplicatas (mantém o mais recente):

```sql
-- Limpar duplicatas em clientes_finais
DELETE FROM clientes_finais
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY cpf
                   ORDER BY created_at DESC
               ) as rn
        FROM clientes_finais
    ) t
    WHERE rn > 1
);

-- Limpar duplicatas em boletos
DELETE FROM boletos
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY numero_boleto
                   ORDER BY created_at DESC
               ) as rn
        FROM boletos
    ) t
    WHERE rn > 1
);
```

---

### 4. **LIMPAR downloads_canopus**

Essa tabela tem PDFs grandes em base64 e está causando timeout:

```sql
-- Ver tamanho atual
SELECT
    COUNT(*) as total_registros,
    pg_size_pretty(pg_total_relation_size('downloads_canopus')) as tamanho
FROM downloads_canopus;

-- Deletar registros com mais de 7 dias
DELETE FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '7 days';

-- OU deletar TUDO (se quiser começar do zero)
-- TRUNCATE TABLE downloads_canopus;
```

---

### 5. **VACUUM (Liberar Espaço)**

```sql
VACUUM FULL ANALYZE clientes_finais;
VACUUM FULL ANALYZE boletos;
VACUUM FULL ANALYZE downloads_canopus;
```

---

### 6. **CONFIGURAR TIMEOUTS (Evitar problema futuro)**

```sql
-- Matar conexões idle após 5 minutos
ALTER DATABASE nexus_crm SET idle_in_transaction_session_timeout = '5min';

-- Timeout de queries longas: 2 minutos
ALTER DATABASE nexus_crm SET statement_timeout = '2min';
```

---

### 7. **REINICIAR BACKEND (Render Dashboard)**

- Vá para: https://dashboard.render.com/web/nexus-crm-backend
- Clique em **Manual Deploy > Clear build cache & deploy**

Isso vai:
- ✅ Fechar todas as conexões antigas do backend
- ✅ Reiniciar a aplicação
- ✅ Aplicar as correções de código que eu vou fazer

---

## 📊 Verificar Se Resolveu:

### a) Conexões Livres:

```sql
SELECT
    COUNT(*) as total_conexoes,
    COUNT(*) FILTER (WHERE state = 'active') as ativas,
    COUNT(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity
WHERE datname = current_database();
```

Deve mostrar **0-1 conexões ativas** (não 3/3).

### b) Total de Registros:

```sql
SELECT
    'clientes_finais' as tabela,
    COUNT(*) as total
FROM clientes_finais
UNION ALL
SELECT
    'boletos' as tabela,
    COUNT(*) as total
FROM boletos;
```

Deve mostrar valores **normais** (não 1000 boletos nem 10x duplicados).

---

## 🔧 Correções de Código (Eu vou fazer):

Identificei 7 lugares no código abrindo conexões sem fechar:
- `automation_canopus.py` linhas: 259, 2117, 2448, 3178, 3225, 3271, 3354

Vou corrigir todos para usar `with` ou `try/finally`.

---

## ⚠️ Prevenção Futura:

### Opção 1: Manter Render Free (Limite: 3 conexões)
- ✅ Execute os timeouts (passo 6)
- ✅ Aguarde minhas correções de código
- ✅ Limpe downloads_canopus semanalmente

### Opção 2: Upgrade para Render Starter ($7/mês)
- ✅ 40 conexões simultâneas (muito mais margem)
- ✅ Mais memória e CPU
- ✅ Melhor performance geral

---

## 📁 Arquivo de Referência:

`database/queries/EMERGENCIA_MATAR_CONEXOES.sql` - Todas as queries acima em um único arquivo.

---

## ✅ Checklist Rápido:

- [ ] Executei SQL para matar conexões
- [ ] Deletei duplicatas em clientes_finais
- [ ] Deletei duplicatas em boletos
- [ ] Limpei downloads_canopus antigos
- [ ] Executei VACUUM
- [ ] Configurei timeouts
- [ ] Reiniciei o backend no Render
- [ ] Verifiquei que sistema voltou a funcionar
