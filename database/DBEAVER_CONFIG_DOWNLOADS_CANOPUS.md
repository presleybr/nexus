# Como Resolver Erro I/O no DBeaver ao Acessar downloads_canopus

## Problema

Erro: `An I/O error occurred while sending to the backend.`

Causa: A tabela `downloads_canopus` armazena PDFs em **base64** na coluna `caminho_arquivo`. Quando você tenta abrir a tabela com `SELECT *`, o DBeaver tenta carregar TODOS os PDFs de uma vez, causando timeout/erro de I/O.

---

## Soluções

### ✅ Solução 1: Usar Queries Específicas (RECOMENDADO)

**Não use** `SELECT * FROM downloads_canopus` no DBeaver!

Use as queries otimizadas do arquivo `database/queries/visualizar_downloads_canopus.sql`:

```sql
-- Ver resumo SEM carregar PDFs
SELECT
    id,
    consultor_id,
    cpf,
    nome_arquivo,
    LENGTH(caminho_arquivo) as tamanho_base64,
    tamanho_bytes,
    status,
    data_download,
    created_at
FROM downloads_canopus
ORDER BY created_at DESC
LIMIT 100;
```

---

### ✅ Solução 2: Configurar DBeaver para Limitar Resultados

1. **Abra DBeaver**
2. Vá em: **Window > Preferences** (Windows/Linux) ou **DBeaver > Preferences** (Mac)
3. Navegue para: **Database > SQL Editor > Results**
4. Configure:
   - ✅ **Limit result sets**: `100` ou `500`
   - ✅ **Use SQL LIMIT/OFFSET**: Habilitado
   - ✅ **Max text content length**: `1000` (limita tamanho de textos grandes)
5. Clique em **Apply** e **OK**

---

### ✅ Solução 3: Configurar Timeout de Conexão

Se mesmo com LIMIT você tem erro:

1. **Clique com botão direito** na conexão do banco
2. Selecione **Edit Connection**
3. Vá na aba **Driver Properties**
4. Adicione/altere:
   - `socketTimeout`: `60` (segundos)
   - `connectTimeout`: `30` (segundos)
   - `loginTimeout`: `30` (segundos)
5. Clique em **OK**

---

### ✅ Solução 4: Excluir Coluna `caminho_arquivo` da Visualização

No DBeaver, você pode ocultar colunas grandes:

1. Execute a query sem a coluna problemática:

```sql
SELECT
    id,
    consultor_id,
    cpf,
    nome_arquivo,
    tamanho_bytes,
    status,
    data_download,
    created_at,
    updated_at
    -- caminho_arquivo NÃO INCLUÍDO!
FROM downloads_canopus
ORDER BY created_at DESC;
```

---

### ✅ Solução 5: Limpar Registros Antigos

Se a tabela está muito grande (muitos registros):

1. **Ver quantos registros há:**

```sql
SELECT COUNT(*) as total FROM downloads_canopus;
```

2. **Ver tamanho da tabela:**

```sql
SELECT pg_size_pretty(pg_total_relation_size('downloads_canopus')) as tamanho;
```

3. **Deletar registros antigos** (mais de 90 dias):

```sql
-- Primeiro, ver quantos seriam deletados
SELECT COUNT(*) FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '90 days';

-- Se OK, deletar:
DELETE FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '90 days';
```

4. **Limpar espaço:**

```sql
VACUUM FULL downloads_canopus;
```

---

### ✅ Solução 6: Criar Índices (Performance)

Execute as queries do arquivo `database/queries/otimizar_downloads_canopus.sql`:

```sql
-- Índice por CPF
CREATE INDEX IF NOT EXISTS idx_downloads_canopus_cpf
ON downloads_canopus(cpf);

-- Índice por data
CREATE INDEX IF NOT EXISTS idx_downloads_canopus_data
ON downloads_canopus(data_download DESC);

-- Atualizar estatísticas
ANALYZE downloads_canopus;
```

---

### ✅ Solução 7: Visualizar Apenas 1 PDF Específico

Se você precisa ver o base64 de um PDF específico:

```sql
-- Buscar por ID
SELECT
    id,
    nome_arquivo,
    caminho_arquivo  -- Base64 do PDF
FROM downloads_canopus
WHERE id = 123;  -- Substitua pelo ID desejado

-- OU buscar por CPF + nome do arquivo
SELECT
    id,
    nome_arquivo,
    caminho_arquivo
FROM downloads_canopus
WHERE cpf = '12345678900'
  AND nome_arquivo LIKE '%boleto%'
LIMIT 1;
```

---

## Queries Úteis Já Prontas

Todas no arquivo `database/queries/visualizar_downloads_canopus.sql`:

1. **Resumo da tabela** (sem base64)
2. **Estatísticas** (total de registros, tamanho, etc)
3. **Downloads por consultor**
4. **Últimos 50 downloads**
5. **Buscar por CPF**
6. **Obter PDF específico** (apenas quando necessário)
7. **Downloads com erro**
8. **Duplicatas**

---

## Manutenção Recomendada

### Mensal:
1. **Verificar tamanho da tabela:**
   ```sql
   SELECT pg_size_pretty(pg_total_relation_size('downloads_canopus'));
   ```

2. **Limpar downloads antigos:**
   ```sql
   DELETE FROM downloads_canopus
   WHERE data_download < NOW() - INTERVAL '90 days';
   ```

3. **Vacuum:**
   ```sql
   VACUUM ANALYZE downloads_canopus;
   ```

### Trimestral:
1. **Remover duplicatas** (use script em `otimizar_downloads_canopus.sql`)
2. **Verificar índices:**
   ```sql
   SELECT indexname, indexdef
   FROM pg_indexes
   WHERE tablename = 'downloads_canopus';
   ```

---

## Prevenção

Para evitar o problema no futuro:

1. **✅ Configure autovacuum no PostgreSQL** (já está habilitado no Render)
2. **✅ Crie job para limpar registros antigos automaticamente**
3. **✅ Use índices adequados** (já criados nas soluções acima)
4. **✅ Sempre use LIMIT em queries** ao explorar a tabela

---

## Arquivos de Referência

- `database/queries/visualizar_downloads_canopus.sql` - Queries seguras para visualização
- `database/queries/otimizar_downloads_canopus.sql` - Scripts de manutenção e otimização
