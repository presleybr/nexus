# 🏢 PORTAL CONSÓRCIO - INSTRUÇÕES DE IMPLEMENTAÇÃO

## ✅ O QUE JÁ FOI CRIADO

1. **SQL das tabelas:** `backend/sql/criar_tabelas_portal.sql`
   - 6 tabelas criadas
   - Índices e triggers
   - Dados iniciais (usuário admin, 5 clientes exemplo)

## ❌ PROBLEMA ENCONTRADO

Erro de encoding UTF-8 ao conectar no PostgreSQL via Python no Windows.

## 🔧 SOLUÇÃO MANUAL

### PASSO 1: Executar SQL Manualmente

Opção A - Via pgAdmin:
1. Abra pgAdmin
2. Conecte no servidor localhost:5434
3. Abra o database `nexus_crm`
4. Vá em Tools → Query Tool
5. Abra o arquivo `backend/sql/criar_tabelas_portal.sql`
6. Execute (F5)

Opção B - Via linha de comando (se psql estiver instalado):
```bash
psql -h localhost -p 5434 -U nexus_user -d nexus_crm -f backend/sql/criar_tabelas_portal.sql
# Senha: nexus2025
```

### PASSO 2: Verificar Tabelas Criadas

Execute no pgAdmin:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('clientes_finais', 'boletos', 'usuarios_portal',
                   'pastas_digitais', 'historico_disparos', 'configuracoes_automacao')
ORDER BY table_name;
```

Deve retornar 6 tabelas.

### PASSO 3: Verificar Dados Iniciais

```sql
-- Usuário admin do portal (senha: admin123)
SELECT * FROM usuarios_portal;

-- 5 clientes finais de exemplo
SELECT COUNT(*) FROM clientes_finais;

-- Configuração de automação
SELECT * FROM configuracoes_automacao;
```

## 📦 PRÓXIMOS PASSOS APÓS CRIAR TABELAS

### 1. Instalar Dependências

```bash
pip install reportlab python-barcode Pillow --break-system-packages
```

### 2. Criar Pasta de Boletos

```bash
mkdir boletos
```

### 3. Arquivos Pendentes de Criação

Por favor, solicite a criação dos seguintes componentes em sequência:

#### Backend:
1. `backend/services/boleto_generator.py` - Gerador de PDF boletos
2. `backend/routes/portal_consorcio.py` - Rotas do Portal
3. Atualizar `backend/routes/crm.py` - Adicionar rotas para CRM consumir dados
4. Atualizar `backend/app.py` - Registrar blueprint do Portal

#### Frontend - Portal Consórcio:
5. `frontend/templates/portal-consorcio/login.html`
6. `frontend/templates/portal-consorcio/dashboard.html`
7. `frontend/templates/portal-consorcio/clientes.html`
8. `frontend/templates/portal-consorcio/boletos.html`

#### Frontend - CRM Cliente:
9. `frontend/templates/crm-cliente/clientes-finais.html`
10. `frontend/templates/crm-cliente/boletos-digital.html`
11. `frontend/templates/crm-cliente/disparos-massa.html`

## 🔐 CREDENCIAIS DO PORTAL

Após criar as tabelas, você poderá fazer login no Portal com:

**URL:** `http://localhost:5000/portal-consorcio/login`
**Email:** `admin@portal.com`
**Senha:** `admin123`

## 🎯 ARQUITETURA FINAL

```
┌─────────────────────────────────────────────────┐
│          PORTAL CONSÓRCIO                       │
│     (/portal-consorcio)                         │
│                                                  │
│  • Login Admin                                   │
│  • Cadastro Clientes Finais                     │
│  • Geração de Boletos PDF                       │
│  • Upload de Carnês                             │
│                                                  │
│         ↓ (PostgreSQL)                          │
│                                                  │
└─────────────────────────────────────────────────┘
                    ↓
        ┌──────────────────────┐
        │   clientes_finais    │
        │   boletos            │
        │   pastas_digitais    │
        └──────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          CRM CLIENTE NEXUS                      │
│     (/crm)                                      │
│                                                  │
│  • Visualiza Clientes Finais                    │
│  • Visualiza Boletos                            │
│  • Pastas Digitais                              │
│  • Disparo WhatsApp                             │
│  • Histórico                                     │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 📊 DADOS DE TESTE JÁ INSERIDOS

5 clientes finais cadastrados:
1. João da Silva Santos - CPF 123.456.789-01
2. Maria Oliveira Costa - CPF 234.567.890-12
3. Pedro Henrique Souza - CPF 345.678.901-23
4. Ana Paula Rodrigues - CPF 456.789.012-34
5. Carlos Eduardo Lima - CPF 567.890.123-45

Todos vinculados ao `cliente_nexus_id = 2` (empresa cliente do CRM)

## 🚀 COMANDOS PARA CONTINUAR

Após executar o SQL manualmente:

```bash
# 1. Instalar dependências
pip install reportlab python-barcode Pillow

# 2. Criar pasta de boletos
mkdir boletos

# 3. Solicitar criação do boleto_generator.py
# (Arqui

vo grande ~300 linhas)

# 4. Solicitar criação das rotas do Portal
# (Arquivo grande ~800 linhas)

# 5. Solicitar criação dos templates
# (11 arquivos HTML)
```

## ⚠️ IMPORTANTE

As tabelas SQL estão prontas em `backend/sql/criar_tabelas_portal.sql`.
Você só precisa executá-las uma vez no banco de dados.

Após isso, volte aqui e solicite a criação dos próximos componentes (backend e frontend).

## 📝 CHECKLIST

- [ ] Executar SQL (criar tabelas)
- [ ] Verificar 6 tabelas criadas
- [ ] Verificar dados iniciais
- [ ] Instalar dependências Python
- [ ] Criar pasta `boletos/`
- [ ] Solicitar criação do `boleto_generator.py`
- [ ] Solicitar criação do `portal_consorcio.py` (rotas)
- [ ] Solicitar criação dos templates HTML
- [ ] Testar login no Portal
- [ ] Testar geração de boleto
- [ ] Testar visualização no CRM

---

**Status Atual:** Tabelas SQL prontas, aguardando execução manual
**Próximo Passo:** Executar SQL e depois solicitar criação dos componentes Python
