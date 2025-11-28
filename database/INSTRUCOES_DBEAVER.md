# Como Criar Todas as Tabelas no DBeaver

## Passo a Passo Completo

### 1. Conectar ao PostgreSQL no DBeaver

1. Abra o **DBeaver**
2. Clique em **"Nova Conexão"** ou `Ctrl + Shift + N`
3. Selecione **PostgreSQL**
4. Configure a conexão:
   ```
   Host: localhost
   Port: 5432
   Database: postgres (inicialmente)
   Username: postgres
   Password: sua_senha_aqui
   ```
5. Clique em **"Testar Conexão"**
6. Se ok, clique em **"Finalizar"**

### 2. Criar o Banco de Dados (se não existir)

1. Na árvore de conexões, clique com botão direito em **"Databases"**
2. Selecione **"Criar Novo Banco de Dados"**
3. Nome: `nexus_crm`
4. Encoding: `UTF8`
5. Clique em **"OK"**

**OU execute o SQL:**
```sql
CREATE DATABASE nexus_crm
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TEMPLATE = template0;
```

### 3. Conectar ao Banco nexus_crm

1. Na árvore de conexões, expanda sua conexão PostgreSQL
2. Expanda **"Databases"**
3. Clique com botão direito em **"nexus_crm"**
4. Selecione **"Definir como banco de dados padrão"**
5. Ou dê duplo clique em **nexus_crm** para conectar

### 4. Abrir o Script SQL

1. No DBeaver, vá em: **Arquivo → Abrir Arquivo** (`Ctrl + O`)
2. Navegue até: `D:\Nexus\database\criar_todas_tabelas.sql`
3. Clique em **"Abrir"**

**OU:**
- Arraste o arquivo `criar_todas_tabelas.sql` para dentro do DBeaver

### 5. Executar o Script

#### Opção 1: Executar Tudo (Recomendado)

1. Com o script aberto, clique no botão **▼** ao lado do ▶ (Play)
2. Selecione **"Execute SQL Script"** ou pressione `Ctrl + X`
3. Aguarde a execução (pode levar 10-30 segundos)
4. Verifique os resultados no painel inferior

#### Opção 2: Executar Passo a Passo (Para Debug)

1. Selecione um bloco SQL (por exemplo, CREATE TABLE usuarios)
2. Pressione `Ctrl + Enter` para executar apenas o bloco selecionado
3. Repita para cada seção

### 6. Verificar se Tudo Foi Criado

Execute esta query para listar todas as tabelas:

```sql
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Tabelas esperadas (31 tabelas):**
- boletos
- clientes_finais
- clientes_nexus
- config_automacao_canopus
- configuracoes_automacao
- configuracoes_cliente
- consultores
- credenciais_canopus
- disparos
- execucoes_automacao
- historico_disparos
- log_downloads_boletos
- logs_sistema
- pastas_digitais
- pontos_venda
- status_sistema
- usuarios
- usuarios_portal
- whatsapp_sessions

**Views (4 views):**
- view_dashboard_cliente
- vw_boletos_pendentes_envio
- vw_downloads_com_problemas
- vw_relatorio_downloads_consultor

### 7. Atualizar a Árvore de Objetos

1. Na árvore de conexões do DBeaver
2. Clique com botão direito em **"nexus_crm"**
3. Selecione **"Atualizar"** ou pressione `F5`
4. Expanda **"Schemas → public → Tables"**
5. Você deve ver todas as 31 tabelas criadas

### 8. Verificar Dados Iniciais

Verifique se os dados iniciais foram inseridos:

```sql
-- Ver pontos de venda
SELECT * FROM pontos_venda;

-- Ver consultores
SELECT * FROM consultores;

-- Ver usuário admin do portal
SELECT * FROM usuarios_portal;

-- Ver configurações
SELECT * FROM config_automacao_canopus;
```

## Erros Comuns e Soluções

### Erro: "database nexus_crm already exists"
**Solução:** O banco já existe, pule a etapa 2 e vá direto para a etapa 3.

### Erro: "relation already exists"
**Solução:** Algumas tabelas já existem. Você pode:
- Ignorar (o script usa `CREATE TABLE IF NOT EXISTS`)
- OU limpar o banco primeiro (CUIDADO - apaga dados!):
  ```sql
  DROP SCHEMA public CASCADE;
  CREATE SCHEMA public;
  ```

### Erro: "permission denied"
**Solução:** Certifique-se de estar conectado como usuário `postgres` ou outro usuário com permissões de SUPERUSER.

### Erro: "syntax error"
**Solução:** Certifique-se de estar executando todo o script, não apenas partes dele.

### Script não executa tudo
**Solução:** Use `Ctrl + X` (Execute SQL Script) em vez de `Ctrl + Enter` (Execute Statement).

## Como Limpar e Recriar (Reset Completo)

Se precisar apagar TUDO e recomeçar do zero:

```sql
-- ⚠️ CUIDADO: ISSO APAGA TODOS OS DADOS!

-- Desconectar todos os usuários do banco
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'nexus_crm' AND pid <> pg_backend_pid();

-- Apagar e recriar o banco
DROP DATABASE IF EXISTS nexus_crm;
CREATE DATABASE nexus_crm
    WITH
    ENCODING = 'UTF8'
    TEMPLATE = template0;
```

Depois execute o script `criar_todas_tabelas.sql` novamente.

## Atalhos Úteis do DBeaver

- `Ctrl + X` - Execute SQL Script (todo o arquivo)
- `Ctrl + Enter` - Execute Statement (bloco selecionado)
- `Ctrl + \` - Formatar SQL
- `F5` - Atualizar árvore de objetos
- `Ctrl + Space` - Autocompletar SQL
- `Ctrl + Shift + E` - Abrir editor SQL

## Estrutura do Banco Criada

### Tabelas Principais
- **usuarios** - Login de clientes e administradores
- **clientes_nexus** - Empresários que usam o CRM
- **clientes_finais** - Clientes finais dos consórcios
- **boletos** - Boletos gerados (Portal e CRM)
- **disparos** - Histórico de envios WhatsApp

### Tabelas de Automação
- **consultores** - Consultores de consórcio
- **pontos_venda** - Pontos de venda Canopus
- **credenciais_canopus** - Credenciais de acesso
- **log_downloads_boletos** - Log de downloads automáticos
- **execucoes_automacao** - Execuções batch

### Tabelas de Configuração
- **configuracoes_cliente** - Configs por cliente
- **configuracoes_automacao** - Configs de automação
- **config_automacao_canopus** - Configs Canopus
- **whatsapp_sessions** - Sessões WhatsApp

### Tabelas Auxiliares
- **logs_sistema** - Logs gerais
- **historico_disparos** - Histórico de disparos em massa
- **pastas_digitais** - Organização de arquivos
- **usuarios_portal** - Usuários do Portal Consórcio

## Próximos Passos

Após criar as tabelas:

1. **Configurar o arquivo `.env`**
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=nexus_crm
   DB_USER=postgres
   DB_PASSWORD=sua_senha_aqui
   ```

2. **Executar o sistema**
   ```bash
   cd D:\Nexus
   iniciar.bat
   ```

3. **Fazer login**
   - Portal: http://localhost:5000/portal-consorcio/login
   - Email: admin@portal.com
   - Senha: admin123

## Suporte

Se tiver problemas, verifique:
- PostgreSQL está rodando? (Services do Windows)
- Senha correta no DBeaver?
- Versão do PostgreSQL ≥ 12?
- Encoding do banco é UTF8?

---

**Script criado com sucesso!** ✅
