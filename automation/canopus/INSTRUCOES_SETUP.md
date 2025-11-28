# Instruções de Setup - Automação Canopus para Dener

## ✅ Correções Aplicadas

### 1. Senha do PostgreSQL Corrigida
- ❌ Senha antiga: `postgres`
- ✅ Senha nova: `nexus2025`

### 2. Configuração Centralizada
Criado `db_config.py` com todas as credenciais:

```python
DB_HOST = "localhost"
DB_PORT = 5434
DB_NAME = "nexus_crm"
DB_USER = "postgres"
DB_PASSWORD = "nexus2025"
```

### 3. Scripts Atualizados
Todos os scripts agora importam de `db_config.py`:
- ✅ `executar_sql.py`
- ✅ `cadastrar_credencial.py`
- ✅ `processar_dener.py`
- ✅ `orquestrador.py`

## 🚀 Passo a Passo - Executar Agora

### Passo 1: Testar Conexão com PostgreSQL

```cmd
cd D:\Nexus\automation\canopus
python testar_conexao_db.py
```

**Saída esperada:**
```
================================================================================
TESTE DE CONEXAO - POSTGRESQL
================================================================================

Configuracoes do banco:

Host: localhost
Porta: 5434
Banco: nexus_crm
Usuario: postgres
Senha: **********

[*] Tentando conectar...
[OK] Conectado com sucesso!

[*] Testando query...
[OK] PostgreSQL versao: PostgreSQL 14.x...

[*] Listando tabelas do banco...
[OK] Encontradas X tabelas:
  - clientes_finais
  - boletos
  - usuarios_portal
  ...

================================================================================
TESTE CONCLUIDO COM SUCESSO!
================================================================================
```

### Passo 2: Criar Tabelas da Automação

```cmd
python executar_sql.py
```

**O que faz:**
1. Conecta ao PostgreSQL com senha correta
2. Lê `backend/sql/criar_tabelas_automacao.sql`
3. Cria 6 tabelas:
   - `consultores`
   - `pontos_venda`
   - `credenciais_canopus`
   - `clientes_planilha_staging`
   - `log_downloads_boletos`
   - `execucoes_automacao`
4. Pergunta se quer inserir dados do Dener (responda **S**)

**Saída esperada:**
```
================================================================================
EXECUTAR SQL - CRIAR TABELAS AUTOMACAO CANOPUS
================================================================================

[OK] Arquivo SQL encontrado: backend\sql\criar_tabelas_automacao.sql
[OK] Arquivo SQL lido (XXXXX caracteres)

Conectando ao PostgreSQL...

Host: localhost
Porta: 5434
Banco: nexus_crm
Usuario: postgres
Senha: **********

[OK] Conectado ao PostgreSQL

Executando comandos SQL...

[OK] Comandos SQL executados com sucesso!

Verificando tabelas criadas...
[OK] 6 tabelas encontradas:
  - clientes_planilha_staging
  - consultores
  - credenciais_canopus
  - execucoes_automacao
  - log_downloads_boletos
  - pontos_venda

================================================================================
SQL EXECUTADO COM SUCESSO!
================================================================================

Deseja inserir os dados do Dener agora? (S/N): S

================================================================================
INSERIR DADOS DO DENER
================================================================================

[*] Inserindo pontos de venda...
[OK] Pontos de venda inseridos: 17308, 24627
[*] Inserindo consultor Dener...
[OK] Consultor inserido: ID=1, Nome=Dener

================================================================================
DADOS DO DENER INSERIDOS COM SUCESSO!
================================================================================
```

### Passo 3: Testar Importação da Planilha

```cmd
python testar_dener.py
```

### Passo 4: Cadastrar Credenciais

```cmd
python cadastrar_credencial.py
```

Cadastre as credenciais para **ambos** os pontos de venda:
1. Ponto 17308
2. Ponto 24627

### Passo 5: Processar Dener

```cmd
# Listar todos os clientes
python processar_dener.py --listar

# Exportar para JSON
python processar_dener.py --exportar

# Simular processamento
python processar_dener.py --simular
```

## 📁 Arquivos Criados/Atualizados

```
automation/canopus/
├── db_config.py                    ✅ NOVO - Configuração centralizada
├── testar_conexao_db.py            ✅ NOVO - Testa conexão PostgreSQL
├── executar_sql.py                 ✅ ATUALIZADO - Usa db_config
├── cadastrar_credencial.py         ✅ ATUALIZADO - Usa db_config
├── processar_dener.py              ✅ ATUALIZADO - Usa db_config
├── orquestrador.py                 ✅ ATUALIZADO - Usa db_config
├── excel_importer_dener.py         ✅ Importador específico Dener
├── testar_dener.py                 ✅ Teste da planilha
└── INSTRUCOES_SETUP.md             ✅ Este arquivo
```

## 🔧 Troubleshooting

### Erro: "Falha ao conectar"

1. **PostgreSQL não está rodando**
   ```cmd
   # Verificar se está rodando
   netstat -an | findstr 5434
   ```

2. **Senha incorreta**
   - Verifique em `db_config.py`
   - Senha correta: `nexus2025`

3. **Banco não existe**
   ```cmd
   psql -h localhost -p 5434 -U postgres -l
   ```
   Se `nexus_crm` não aparecer, crie:
   ```cmd
   psql -h localhost -p 5434 -U postgres
   CREATE DATABASE nexus_crm;
   ```

### Erro: "psycopg nao instalado"

```cmd
pip install psycopg psycopg-binary psycopg-pool
```

### Erro: "Planilha nao encontrada"

Certifique-se de que a planilha está em:
```
D:\Nexus\planilhas\DENER__PLANILHA_GERAL.xlsx
```

## 📊 Próximos Passos

Após executar o setup com sucesso:

1. ✅ Tabelas criadas
2. ✅ Dados do Dener inseridos
3. ✅ Planilha testada
4. ✅ Credenciais cadastradas
5. ⏭️ **Mapear seletores CSS do Canopus**
6. ⏭️ **Testar login no Canopus**
7. ⏭️ **Implementar download de boletos**

## 🎯 Comando de Teste Completo

Para testar tudo de uma vez:

```cmd
cd D:\Nexus\automation\canopus

echo [1/5] Testando conexao...
python testar_conexao_db.py

echo [2/5] Criando tabelas...
python executar_sql.py

echo [3/5] Testando planilha...
python testar_dener.py

echo [4/5] Listando clientes...
python processar_dener.py --listar

echo [5/5] Simulando processamento...
python processar_dener.py --simular
```

---

**Dúvidas?** Verifique `README_DENER.md` para documentação completa.
