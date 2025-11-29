# 🚨 FIX URGENTE: Erro I/O ao Abrir downloads_canopus

## ❌ O que NÃO fazer:

- ❌ **NÃO clique duas vezes na tabela** downloads_canopus no DBeaver
- ❌ **NÃO use** `SELECT * FROM downloads_canopus`
- ❌ **NÃO tente** "Ver Dados" clicando com botão direito

## ✅ O que fazer:

### 1. Abra uma Nova SQL Console no DBeaver

1. Clique com botão direito na conexão
2. Selecione **SQL Editor > New SQL Script**

### 2. Cole e Execute Esta Query:

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
    data_download
FROM downloads_canopus
ORDER BY data_download DESC
LIMIT 100;
```

**Pressione Ctrl+Enter** para executar.

---

## 📊 Verificar Se a Tabela Está Muito Grande:

```sql
SELECT
    COUNT(*) as total_registros,
    SUM(tamanho_bytes) / 1024 / 1024 as tamanho_mb,
    pg_size_pretty(pg_total_relation_size('downloads_canopus')) as tamanho_disco
FROM downloads_canopus;
```

**Se o total_registros for > 1000**, siga os passos abaixo para limpar.

---

## 🧹 LIMPAR TABELA (Se Necessário):

### Opção 1: Deletar Registros com Mais de 30 Dias

```sql
-- 1. Ver quantos seriam deletados
SELECT COUNT(*) as total_deletar
FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '30 days';

-- 2. Se estiver OK, deletar:
DELETE FROM downloads_canopus
WHERE data_download < NOW() - INTERVAL '30 days';

-- 3. Liberar espaço em disco:
VACUUM FULL downloads_canopus;
```

### Opção 2: Manter Apenas os Últimos 500 Registros

```sql
-- 1. Ver quantos seriam deletados
SELECT COUNT(*) as total_deletar
FROM downloads_canopus
WHERE id NOT IN (
    SELECT id
    FROM downloads_canopus
    ORDER BY data_download DESC
    LIMIT 500
);

-- 2. Deletar:
DELETE FROM downloads_canopus
WHERE id NOT IN (
    SELECT id
    FROM downloads_canopus
    ORDER BY data_download DESC
    LIMIT 500
);

-- 3. Liberar espaço:
VACUUM FULL downloads_canopus;
```

### Opção 3: DELETAR TUDO (Começar do Zero)

```sql
-- ⚠️ CUIDADO: Isso deleta TODOS os downloads!
TRUNCATE TABLE downloads_canopus;
```

---

## 🔧 Configurar DBeaver para Nunca Mais Dar Esse Erro:

### 1. Limitar Resultados Automaticamente:

1. **Window > Preferences** (ou **DBeaver > Preferences** no Mac)
2. **Database > SQL Editor > Results**
3. Configure:
   - ✅ **Limit result sets**: `100`
   - ✅ **Use SQL LIMIT/OFFSET**: Habilitado
   - ✅ **Max text content length**: `1000`
4. Clique **OK**

### 2. Aumentar Timeout:

1. Clique com **botão direito** na conexão
2. **Edit Connection**
3. Aba **Driver Properties**
4. Adicione:
   - `socketTimeout` = `60`
   - `connectTimeout` = `30`
5. Clique **OK**

---

## 📁 Arquivos de Ajuda:

Consulte estes arquivos no projeto:

- `database/queries/visualizar_downloads_canopus.sql` - 8 queries prontas
- `database/queries/limpar_downloads_antigos.sql` - Scripts de limpeza
- `database/queries/otimizar_downloads_canopus.sql` - Otimizações avançadas
- `database/DBEAVER_CONFIG_DOWNLOADS_CANOPUS.md` - Guia completo

---

## ❓ FAQ:

**P: A tabela está corrompida?**
R: Não! Ela só tem muitos PDFs grandes em base64. Use as queries certas.

**P: Vou perder dados se deletar registros antigos?**
R: Os PDFs já foram importados para a tabela `boletos`. A tabela `downloads_canopus` é apenas um registro histórico dos downloads.

**P: Posso recuperar um PDF específico?**
R: Sim! Use:
```sql
SELECT caminho_arquivo FROM downloads_canopus WHERE id = 123;
```
(Substitua 123 pelo ID desejado)

---

## ✅ Checklist Rápido:

- [ ] Abri Nova SQL Console no DBeaver
- [ ] Executei a query de RESUMO (sem base64)
- [ ] Verifiquei quantos registros existem
- [ ] Se > 1000, executei limpeza
- [ ] Executei VACUUM FULL
- [ ] Configurei limite de resultados no DBeaver
- [ ] Nunca mais vou clicar duas vezes na tabela! 😅
