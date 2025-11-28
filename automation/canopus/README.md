# 🤖 Automação Canopus - Download de Boletos

Sistema automatizado para download de boletos do sistema Canopus de consórcios, integrado ao CRM Nexus.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Esta automação substitui o processo manual de download de boletos, que antes envolvia:
1. Abrir planilhas Excel de cada consultor
2. Acessar o sistema Canopus manualmente
3. Buscar cada cliente por CPF
4. Baixar boletos individualmente
5. Organizar arquivos por consultor

### O que a automação faz:

✅ Lê automaticamente planilhas Excel dos consultores
✅ Faz login no sistema Canopus
✅ Busca clientes por CPF
✅ Baixa boletos do mês especificado
✅ Organiza arquivos por consultor
✅ Registra logs detalhados de cada operação
✅ Integra com CRM para envio via WhatsApp

---

## ⚡ Funcionalidades

### Principais
- **Automação completa** usando Playwright
- **Multi-consultor** - processa carteiras de múltiplos consultores
- **Multi-ponto de venda** - suporta CredMS, Semicrédito, etc.
- **Import Excel** - lê planilhas automaticamente
- **Logging robusto** - rastreia sucessos e falhas
- **Integração com PostgreSQL** - armazena histórico completo
- **Modo headless** - executa em background ou visível
- **Retry automático** - tenta novamente em caso de falha
- **Estatísticas em tempo real** - acompanhe o progresso

### Recursos Avançados
- Credenciais criptografadas no banco
- Execução agendada ou manual
- Callback de progresso
- Screenshot em caso de erro
- Reinicialização automática do navegador (evita problemas de memória)
- Delay humanizado entre ações

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.9+
- PostgreSQL 12+ (já configurado no Nexus)
- Acesso ao sistema Canopus

### Passo 1: Instalar dependências

```bash
cd D:\Nexus\automation\canopus
pip install -r requirements.txt
```

### Passo 2: Instalar navegador Playwright

```bash
playwright install chromium
```

### Passo 3: Criar tabelas no banco de dados

```bash
# Conectar ao PostgreSQL (porta 5434)
psql -h localhost -p 5434 -U postgres -d nexus_crm

# Executar script SQL
\i criar_tabelas_automacao.sql
```

Ou via Python:

```bash
python -c "import psycopg; conn = psycopg.connect('host=localhost port=5434 dbname=nexus_crm user=postgres password=sua_senha'); conn.execute(open('criar_tabelas_automacao.sql').read())"
```

---

## ⚙️ Configuração

### 1. Arquivo .env

Crie um arquivo `.env` na pasta `automation/canopus/`:

```bash
# Banco de dados (usar mesmas configs do Nexus)
DB_HOST=localhost
DB_PORT=5434
DB_NAME=nexus_crm
DB_USER=postgres
DB_PASSWORD=sua_senha

# Chave de criptografia (gerar nova!)
ENCRYPTION_KEY=sua_chave_fernet_aqui

# Configurações do navegador
CANOPUS_HEADLESS=false

# Timeouts (em milissegundos)
TIMEOUT_NAVEGACAO=30000
TIMEOUT_DOWNLOAD=60000

# Mês padrão para download
MES_PADRAO=DEZEMBRO

# Integração WhatsApp
WHATSAPP_API_URL=http://localhost:3001
ENVIAR_WHATSAPP_AUTO=false
```

### 2. Gerar chave de criptografia

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copie a chave gerada e adicione ao `.env`.

### 3. Cadastrar consultores no banco

```sql
INSERT INTO consultores (nome, pasta_downloads, planilha_excel, ponto_venda_id)
VALUES
  ('Dayler', 'D:\Nexus\automation\canopus\downloads\Dayler\', 'D:\Nexus\automation\canopus\excel_files\Dayler.xlsx', 1),
  ('Neto', 'D:\Nexus\automation\canopus\downloads\Neto\', 'D:\Nexus\automation\canopus\excel_files\Neto.xlsx', 1);
```

### 4. Cadastrar credenciais do Canopus

Use o script helper:

```bash
python gerenciar_credenciais.py --adicionar --ponto CREDMS --usuario seu_usuario --senha sua_senha
```

Ou insira manualmente no banco (senha será criptografada).

### 5. Preparar planilhas Excel

Coloque as planilhas dos consultores em `excel_files/`:
- `Dayler.xlsx`
- `Neto.xlsx`
- `Mirelli.xlsx`
- etc.

**Formato esperado da planilha:**

| CPF | NOME | PONTO_VENDA | WHATSAPP |
|-----|------|-------------|----------|
| 123.456.789-01 | João Silva | CREDMS | 67999998888 |
| 987.654.321-00 | Maria Santos | SEMICREDITO | 67988887777 |

> **Nota:** As colunas podem ter nomes variados (CPF/DOCUMENTO, NOME/CLIENTE, etc.). O importador é flexível.

---

## 📖 Uso

### Executar para um consultor específico

```bash
python main.py --consultor 1 --mes DEZEMBRO --visible
```

Parâmetros:
- `--consultor ID`: ID do consultor no banco
- `--mes MES`: Mês de referência (DEZEMBRO, JANEIRO, etc.)
- `--visible`: Executar com navegador visível
- `--headless`: Executar em background

### Executar para todos os consultores

```bash
python main.py --todos --mes DEZEMBRO --headless
```

### Testar importação de planilhas

```bash
python excel_importer.py
```

### Testar bot (sem executar)

```bash
python canopus_bot.py
```

---

## 📁 Estrutura do Projeto

```
automation/canopus/
│
├── config.py                      # Configurações centralizadas
├── main.py                        # Script principal
├── canopus_bot.py                 # Classe do bot Playwright
├── excel_importer.py              # Importador de planilhas
├── gerenciar_credenciais.py       # Helper para credenciais
│
├── criar_tabelas_automacao.sql    # Script de criação de tabelas
├── requirements.txt               # Dependências Python
├── .env                           # Variáveis de ambiente (não versionar!)
├── README.md                      # Esta documentação
│
├── downloads/                     # Boletos baixados (por consultor)
│   ├── Dayler/
│   ├── Neto/
│   └── ...
│
├── excel_files/                   # Planilhas dos consultores
│   ├── Dayler.xlsx
│   ├── Neto.xlsx
│   └── ...
│
├── logs/                          # Logs da automação
│   ├── canopus_automation.log
│   ├── downloads.log
│   └── erros.log
│
└── temp/                          # Arquivos temporários
```

---

## 🔧 Troubleshooting

### Problema: "Credenciais não encontradas"

**Solução:** Cadastre as credenciais:
```bash
python gerenciar_credenciais.py --adicionar --ponto CREDMS --usuario SEU_USER --senha SUA_SENHA
```

### Problema: "Planilha não encontrada"

**Solução:** Verifique o caminho no banco:
```sql
SELECT id, nome, planilha_excel FROM consultores;
-- Atualizar caminho se necessário
UPDATE consultores SET planilha_excel = 'D:\Nexus\automation\canopus\excel_files\Consultor.xlsx' WHERE id = 1;
```

### Problema: "CPF não encontrado no sistema"

**Causas possíveis:**
1. CPF incorreto na planilha
2. Cliente não existe no ponto de venda selecionado
3. Formatação do CPF não aceita pelo sistema

**Solução:** Verifique os logs em `logs/downloads.log` para detalhes.

### Problema: "Timeout ao baixar boleto"

**Solução:** Aumente o timeout no `.env`:
```bash
TIMEOUT_DOWNLOAD=120000  # 2 minutos
```

### Problema: Seletores CSS não funcionam

**Causa:** Os seletores no `config.py` precisam ser ajustados para o sistema real.

**Solução:**
1. Execute com `--visible` para ver o navegador
2. Use as ferramentas do desenvolvedor (F12) para identificar os seletores corretos
3. Atualize em `config.py` na seção `SELECTORS`

### Problema: "Erro de criptografia"

**Solução:** Gere nova chave e atualize `.env`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 📊 Monitoramento

### Ver logs em tempo real

```bash
# Windows
Get-Content -Path logs\canopus_automation.log -Wait -Tail 50

# Linux/Mac
tail -f logs/canopus_automation.log
```

### Consultar logs no banco

```sql
-- Downloads recentes
SELECT * FROM log_downloads_boletos
ORDER BY data_execucao DESC
LIMIT 50;

-- Sucessos do dia
SELECT COUNT(*) as total
FROM log_downloads_boletos
WHERE DATE(data_execucao) = CURRENT_DATE
  AND status = 'SUCESSO';

-- Erros recentes
SELECT * FROM vw_downloads_com_problemas
LIMIT 20;

-- Relatório por consultor
SELECT * FROM vw_relatorio_downloads_consultor;
```

---

## 🔄 Agendamento (Futuro)

Para executar automaticamente todos os meses:

### Windows (Task Scheduler)
```bash
schtasks /create /sc monthly /d 1 /tn "Canopus Download Boletos" /tr "python D:\Nexus\automation\canopus\main.py --todos --mes ATUAL --headless"
```

### Linux (Cron)
```bash
0 9 1 * * cd /path/to/nexus/automation/canopus && python main.py --todos --mes ATUAL --headless
```

---

## 🤝 Integração com WhatsApp

Após downloads bem-sucedidos, os boletos podem ser enviados automaticamente via WhatsApp.

### Ver boletos pendentes de envio

```sql
SELECT * FROM vw_boletos_pendentes_envio;
```

### Script de envio (criar separadamente)

```python
# enviar_boletos_whatsapp.py
# TODO: Implementar integração com WPPConnect
```

---

## 📝 Logs e Auditoria

Todos os downloads são registrados com:
- CPF e nome do cliente
- Status (sucesso, erro, não encontrado, etc.)
- Caminho do PDF baixado
- Tempo de execução
- Mensagens de erro (se houver)
- Consultor responsável
- Ponto de venda utilizado

Isso permite auditoria completa e rastreabilidade.

---

## ⚠️ Avisos Importantes

1. **NUNCA** compartilhe o arquivo `.env` (contém credenciais)
2. **Sempre** teste com poucos clientes primeiro (`--consultor` específico)
3. **Monitore** os logs durante execução
4. **Ajuste** os seletores CSS conforme o sistema Canopus real
5. **Faça backup** do banco antes de executar em produção

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `logs/`
2. Consulte esta documentação
3. Verifique o banco de dados (tabelas `log_downloads_boletos` e `execucoes_automacao`)

---

## 📜 Changelog

### Versão 1.0.0 (Inicial)
- ✅ Estrutura básica da automação
- ✅ Importação de planilhas Excel
- ✅ Bot Playwright para Canopus
- ✅ Integração com PostgreSQL
- ✅ Logging e auditoria
- ✅ Criptografia de credenciais
- ✅ Suporte multi-consultor e multi-ponto de venda

---

**Desenvolvido para Nexus CRM** 🚀
