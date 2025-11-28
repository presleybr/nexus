# Automação Canopus - Configuração para DENER

## Estrutura da Planilha

**Arquivo**: `D:\Nexus\planilhas\DENER__PLANILHA_GERAL.xlsx`

- Cabeçalho na **LINHA 12**
- Total: ~152 clientes com CPF válido
- Pontos de Venda na planilha: **17308** e **24627**
- **IMPORTANTE**: Atualmente importamos **APENAS PV 24627**
- Filtragem: Apenas clientes com situação **"Em dia"**

### Colunas da Planilha

| Índice | Nome | Descrição | Exemplo |
|--------|------|-----------|---------|
| 0 | CPF | CPF do cliente | 000.000.000-00 |
| 1 | G/C | Grupo/Cota | "8200 2118" |
| 2 | LANCE | Info de lance | - |
| 3 | BOLETOS | Status boleto | - |
| 4 | SITUAÇÃO | Status do cliente | "Em dia" |
| 5 | Concorciado | Nome (com sufixos) | "JEFFERSON DOURADO - 70%" |
| 6 | P.V | Ponto de Venda | 17308 ou 24627 |
| 7 | Valor | Valor do crédito | - |
| 8+ | Datas | Datas das parcelas | jun, jul, ago... |

## Passo a Passo - Configuração Inicial

### 1. Criar Tabelas no Banco de Dados

```cmd
cd D:\Nexus\automation\canopus
python executar_sql.py
```

Este script irá:
- Conectar ao PostgreSQL (localhost:5434)
- Executar `criar_tabelas_automacao.sql`
- Criar todas as tabelas necessárias
- Perguntar se quer inserir dados do Dener (responda **S**)

**Saída esperada:**
```
[OK] Comandos SQL executados com sucesso!
[OK] 6 tabelas encontradas:
  - clientes_planilha_staging
  - consultores
  - credenciais_canopus
  - execucoes_automacao
  - log_downloads_boletos
  - pontos_venda

Deseja inserir os dados do Dener agora? (S/N): S

[OK] Pontos de venda inseridos: 17308, 24627
[OK] Consultor inserido: ID=1, Nome=Dener
```

### 2. Testar Importação da Planilha

```cmd
python testar_dener.py
```

**O que faz:**
- Lê a planilha do Dener
- Extrai clientes com situação "Em dia"
- Mostra primeiros 10 clientes
- Exibe estatísticas por ponto de venda
- Salva JSON em `temp/dener_clientes.json`

**Saída esperada:**
```
[OK] Planilha encontrada: DENER__PLANILHA_GERAL.xlsx

[1/4] Lendo planilha...
[OK] 152 clientes extraidos (apenas 'Em dia')

[2/4] Primeiros 10 clientes:
 1. JEFFERSON DOURADO MENDES              | CPF: 01234567890 | PV: 17308 | G/C: 8200/2118
 2. MARIA SILVA SANTOS                    | CPF: 09876543210 | PV: 24627 | G/C: 8201/3456
 ...

[3/4] Estatisticas:
Total de clientes 'Em dia': 152

Por Ponto de Venda:
  Ponto 17308: 100 clientes ( 65.8%)
  Ponto 24627:  52 clientes ( 34.2%)
```

### 3. Cadastrar Credenciais do Canopus

```cmd
python cadastrar_credencial.py
```

**Fluxo interativo:**
```
[*] Pontos de venda disponiveis:
  1. [17308] CredMS - Ponto 17308 (credms)
  2. [24627] CM CRED MS - Ponto 24627 (credms)

Selecione o ponto de venda (numero): 1

Usuario do Canopus: seu_usuario
Senha do Canopus: ********** (não aparece na tela)
Codigo empresa (default: 0101):

[OK] Credencial cadastrada com sucesso!
```

**Repita** para cadastrar credenciais do outro ponto de venda se necessário.

### 4. Listar Clientes a Processar

```cmd
python processar_dener.py --listar
```

**Mostra:**
- Todos os clientes "Em dia"
- Agrupados por ponto de venda
- CPF, Nome, Grupo/Cota

```
[Ponto 17308] - 100 clientes
--------------------------------------------------------------------------------
  1. JEFFERSON DOURADO MENDES                  | CPF: 01234567890 | G/C: 8200/2118
  2. ANA PAULA COSTA                           | CPF: 09876543210 | G/C: 8201/1234
  ...
```

### 5. Exportar para JSON

```cmd
python processar_dener.py --exportar
```

Cria arquivo: `automation/canopus/temp/dener_clientes.json`

### 6. Simular Processamento

```cmd
python processar_dener.py --simular
```

**Simula o fluxo completo:**
```
Total de clientes para processar: 152

Quantos clientes deseja simular? (0 para todos): 5

[1/5] Processando: JEFFERSON DOURADO MENDES
     CPF: 01234567890
     Ponto: 17308
     Grupo/Cota: 8200/2118
     -> [SIMULADO] Buscaria no Canopus...
     -> [SIMULADO] Baixaria boleto de DEZEMBRO/2024...
     -> [SIMULADO] Salvaria em: automation/canopus/downloads/Dener/01234567890_DEZ_2024.pdf
```

## Scripts Disponíveis

### `executar_sql.py`
Cria tabelas e insere dados iniciais do Dener.

**Uso:**
```cmd
python executar_sql.py
```

### `testar_dener.py`
Testa importação da planilha do Dener.

**Uso:**
```cmd
python testar_dener.py
```

### `cadastrar_credencial.py`
Cadastra credenciais do Canopus (interativo).

**Uso:**
```cmd
python cadastrar_credencial.py
```

### `processar_dener.py`
Processa clientes do Dener (listar, exportar, simular).

**Uso:**
```cmd
python processar_dener.py --listar          # Lista clientes
python processar_dener.py --exportar        # Exporta JSON
python processar_dener.py --simular         # Simula processamento
```

### `excel_importer_dener.py`
Módulo de importação específico para estrutura do Dener.

**Uso programático:**
```python
from excel_importer_dener import ExcelImporterDener

importador = ExcelImporterDener()
clientes = importador.extrair_clientes()
stats = importador.estatisticas(clientes)
```

## Próximos Passos

### 1. Mapear Seletores CSS do Canopus

Execute o teste de login para identificar os seletores reais:

```cmd
cd automation\canopus
python teste_automacao.py --teste login --usuario SEU_USUARIO --senha SUA_SENHA --ponto-venda 17308
```

**IMPORTANTE:** Este teste vai **FALHAR** propositalmente! O objetivo é abrir o navegador visível para você usar o DevTools (F12) e identificar os seletores CSS corretos.

Atualize os seletores em `config.py`:

```python
SELECTORS = {
    'login': {
        'campo_empresa': '#codigo_empresa',      # ATUALIZAR
        'campo_ponto_venda': '#ponto_venda',     # ATUALIZAR
        'campo_usuario': '#usuario',             # ATUALIZAR
        'campo_senha': '#senha',                 # ATUALIZAR
        'botao_login': 'button[type="submit"]',  # ATUALIZAR
    },
    # ... outros seletores
}
```

### 2. Testar Conexão com Canopus

Após mapear os seletores, teste o login real:

```cmd
python teste_automacao.py --teste login --usuario X --senha Y --ponto-venda 17308
```

### 3. Implementar Download de Boletos

Quando os seletores estiverem mapeados, podemos implementar o download real usando `canopus_automation.py`.

### 4. Processar Clientes

Após tudo configurado:

```cmd
python orquestrador.py download --consultor Dener --mes DEZEMBRO --ano 2024
```

Ou use o menu interativo:

```cmd
iniciar_menu.bat
```

Escolha opção [4] → Menu Automação → Opção [3] → Baixar Boletos

## Estrutura de Arquivos

```
D:\Nexus\
├── planilhas/
│   └── DENER__PLANILHA_GERAL.xlsx          # Planilha do Dener
├── automation/canopus/
│   ├── executar_sql.py                     # ✅ Cria tabelas
│   ├── testar_dener.py                     # ✅ Testa importação
│   ├── cadastrar_credencial.py             # ✅ Cadastra credenciais
│   ├── processar_dener.py                  # ✅ Processa Dener
│   ├── excel_importer_dener.py             # ✅ Importador específico
│   ├── config.py                           # Configurações (atualizar seletores)
│   ├── canopus_automation.py               # Automação Playwright
│   ├── orquestrador.py                     # Orquestrador completo
│   ├── temp/
│   │   └── dener_clientes.json             # JSON exportado
│   └── downloads/
│       └── Dener/                          # Boletos baixados aqui
└── backend/sql/
    └── criar_tabelas_automacao.sql         # Schema do banco
```

## Troubleshooting

### Erro: "Planilha nao encontrada"

Verifique se a planilha está em:
```
D:\Nexus\planilhas\DENER__PLANILHA_GERAL.xlsx
```

### Erro: "Falha ao conectar ao banco"

1. PostgreSQL está rodando?
2. Porta 5434 está correta?
3. Banco `nexus_crm` existe?

Teste manualmente:
```cmd
psql -h localhost -p 5434 -U postgres -d nexus_crm
```

### Erro: "psycopg nao instalado"

```cmd
pip install psycopg psycopg-binary psycopg-pool
```

### Erro: "cryptography nao instalado"

```cmd
pip install cryptography
```

### Erro ao ler Excel

Certifique-se de que `openpyxl` está instalado:
```cmd
pip install openpyxl pandas
```

## Contato

Para dúvidas sobre a automação do Dener, verifique:
1. Este README
2. Logs em `automation/canopus/logs/`
3. Tabela `execucoes_automacao` no banco de dados

---

**Aqui seu tempo vale ouro** ⏱️
