# MAPA COMPLETO DO SISTEMA NEXUS CRM

> **Gerado em:** 2025-11-27
> **Propósito:** Documentação completa para desenvolvimento e debug
> **Sistema:** Nexus CRM - "Aqui seu tempo vale ouro"

---

## 1. ESTRUTURA DE PASTAS

```
D:\Nexus
├── backend/                           # Backend Flask (Python)
│   ├── models/                        # Modelos de dados (ORM)
│   │   ├── __init__.py
│   │   ├── database.py                # Gerenciador de conexão PostgreSQL
│   │   ├── usuario.py                 # Modelo de usuários
│   │   ├── whatsapp_session.py        # Sessões WhatsApp
│   │   ├── boleto.py                  # Modelo de boletos
│   │   └── cliente.py                 # Modelo de clientes
│   │
│   ├── routes/                        # Rotas da API REST
│   │   ├── __init__.py
│   │   ├── auth.py                    # Autenticação e login
│   │   ├── crm.py                     # Gerenciamento de clientes/boletos
│   │   ├── portal_consorcio.py        # Portal do consórcio
│   │   ├── automation.py              # Automação de disparos
│   │   ├── automation_canopus.py      # Automação Canopus (downloads)
│   │   ├── whatsapp.py                # API WhatsApp (Evolution)
│   │   ├── whatsapp_baileys.py        # WhatsApp via Baileys
│   │   ├── whatsapp_wppconnect.py     # WhatsApp via WPPConnect
│   │   ├── boletos_modelo.py          # Boletos modelo
│   │   └── webhook.py                 # Webhooks de integração
│   │
│   ├── services/                      # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── automation_service.py      # Serviço de automação completa
│   │   ├── automation_scheduler.py    # Agendamento de tarefas
│   │   ├── boleto_generator.py        # Geração de PDFs de boletos
│   │   ├── boleto_modelo_service.py   # Serviço de boletos modelo
│   │   ├── whatsapp_service.py        # Abstração WhatsApp
│   │   ├── whatsapp_evolution.py      # Cliente Evolution API
│   │   ├── whatsapp_baileys.py        # Cliente Baileys
│   │   ├── whatsapp_twilio.py         # Cliente Twilio (descontinuado)
│   │   ├── wppconnect_service.py      # Cliente WPPConnect
│   │   ├── evolution_service.py       # Serviço Evolution API
│   │   ├── mensagens_personalizadas.py # Mensagens customizadas
│   │   ├── pdf_generator.py           # Gerador de PDFs
│   │   └── webscraping.py             # Web scraping
│   │
│   ├── scripts/                       # Scripts utilitários
│   │   ├── aplicar_migration_automacao.py
│   │   ├── verificar_boletos.py
│   │   ├── gerar_boletos_exemplo.py
│   │   ├── registrar_boleto_modelo.py
│   │   ├── testar_fluxo_disparo.py
│   │   ├── normalizar_whatsapp_*.py   # Scripts de normalização WhatsApp
│   │   ├── diagnosticar_disparos.py
│   │   └── (vários outros scripts de debug)
│   │
│   ├── sql/                           # Scripts SQL
│   │   ├── criar_tabelas_portal.sql   # Tabelas do Portal Consórcio
│   │   ├── criar_tabelas_automacao.sql # Tabelas de automação
│   │   ├── criar_tabela_boletos_modelo.sql
│   │   └── limpar_e_criar_portal.sql
│   │
│   ├── app.py                         # Aplicação Flask principal
│   └── config.py                      # Configurações centralizadas
│
├── frontend/                          # Frontend HTML/CSS/JS
│   ├── templates/                     # Templates Jinja2
│   │   ├── landing.html               # Landing page
│   │   ├── login-cliente.html         # Login cliente
│   │   ├── login-admin.html           # Login admin
│   │   │
│   │   ├── crm-cliente/               # Dashboard do cliente
│   │   │   ├── dashboard.html         # Dashboard principal
│   │   │   ├── cadastro-clientes.html # Cadastro de clientes
│   │   │   ├── disparos.html          # Disparos de boletos
│   │   │   ├── monitoramento.html     # Monitoramento do sistema
│   │   │   ├── graficos.html          # Gráficos e relatórios
│   │   │   ├── automacao-canopus.html # Automação Canopus
│   │   │   ├── cliente-debitos.html   # Débitos do cliente
│   │   │   ├── whatsapp-conexao.html  # Conexão WhatsApp
│   │   │   ├── whatsapp-baileys.html  # WhatsApp Baileys
│   │   │   ├── whatsapp-wppconnect.html # WPPConnect
│   │   │   └── widget-canopus-downloads.html
│   │   │
│   │   ├── crm-admin/                 # Dashboard administrativo
│   │   │   └── dashboard-admin.html
│   │   │
│   │   └── portal-consorcio/          # Portal do consórcio
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── clientes.html
│   │       ├── boletos.html
│   │       └── boletos-modelo.html
│   │
│   └── static/                        # Arquivos estáticos
│       ├── css/
│       ├── js/
│       │   └── login.js
│       └── images/
│
├── automation/                        # Automações standalone
│   ├── boleto_generator.py            # Gerador de boletos
│   ├── whatsapp_dispatcher.py         # Despachador WhatsApp
│   ├── folder_organizer.py            # Organizador de pastas
│   │
│   └── canopus/                       # Sistema Canopus (download boletos)
│       ├── orquestrador.py            # Orquestrador principal
│       ├── canopus_automation.py      # Automação com Playwright
│       ├── canopus_config.py          # Configurações Canopus
│       ├── canopus_api.py             # API do Canopus
│       ├── canopus_http_client.py     # Cliente HTTP
│       ├── excel_importer.py          # Importador Excel
│       ├── db_config.py               # Configurações de banco
│       ├── gerenciar_credenciais.py   # Gerenciamento de credenciais
│       ├── criar_tabelas_automacao.sql
│       ├── downloads/Danner/          # Pasta de downloads de PDFs
│       └── (vários scripts de teste e debug)
│
├── database/                          # Scripts de banco de dados
│   ├── schema.sql                     # Schema principal
│   ├── create_view.sql                # Views do sistema
│   ├── backup.py                      # Script de backup
│   └── migrations/                    # Migrações
│       ├── 002_update_whatsapp_sessions_twilio.sql
│       ├── 003_add_dia_do_mes_automacao.sql
│       └── 004_add_cpf_to_consultores.sql
│
├── evolution-api-standalone/          # Evolution API (WhatsApp)
│   ├── manager/
│   ├── prisma/
│   │   ├── postgresql-migrations/
│   │   └── mysql-migrations/
│   ├── start.bat
│   └── (arquivos do Evolution API)
│
├── wppconnect-server/                 # WPPConnect Server (WhatsApp)
│   ├── server.js
│   ├── start.bat
│   ├── install.bat
│   ├── limpar-sessao.bat
│   └── node_modules/
│
├── whatsapp-baileys.OLD/              # Baileys (descontinuado)
│
├── venv/                              # Ambiente virtual Python
│
├── boletos/                           # PDFs de boletos gerados
│
├── whatsapp_sessions/                 # Sessões WhatsApp
│
├── logs/                              # Logs do sistema
│
├── start.py                           # Script de inicialização principal
├── iniciar.bat                        # Script de inicialização Windows
├── iniciar_menu.bat                   # Menu de inicialização
├── parar.bat                          # Parar servidores
├── RESTART_SERVIDOR.bat               # Reiniciar servidor
├── setup_canopus.bat                  # Setup Canopus
├── instalar_canopus.bat               # Instalação Canopus
├── requirements.txt                   # Dependências Python
├── .env                               # Variáveis de ambiente
└── README.md                          # Documentação
```

---

## 2. ROTAS DA API

### 2.1. Autenticação (`backend/routes/auth.py`)
**Blueprint:** `auth_bp`, prefix=`/api/auth`

| Método | URL                | Função            | Descrição                          |
|--------|-------------------|-------------------|------------------------------------|
| POST   | /api/auth/login   | login()           | Login de cliente ou admin          |
| POST   | /api/auth/logout  | logout()          | Logout do sistema                  |
| GET    | /api/auth/status  | check_status()    | Verificar status da sessão         |

---

### 2.2. CRM - Gerenciamento (`backend/routes/crm.py`)
**Blueprint:** `crm_bp`, prefix=`/api/crm`

| Método | URL                              | Função                    | Descrição                               |
|--------|----------------------------------|---------------------------|-----------------------------------------|
| GET    | /api/crm/clientes                | listar_clientes()         | Lista todos os clientes                 |
| POST   | /api/crm/clientes                | criar_cliente()           | Cria novo cliente                       |
| GET    | /api/crm/clientes/:id            | obter_cliente()           | Detalhes de um cliente                  |
| PUT    | /api/crm/clientes/:id            | atualizar_cliente()       | Atualiza dados do cliente               |
| DELETE | /api/crm/clientes/:id            | deletar_cliente()         | Remove cliente                          |
| GET    | /api/crm/boletos                 | listar_boletos()          | Lista boletos                           |
| GET    | /api/crm/boletos/:id             | obter_boleto()            | Detalhes do boleto                      |
| GET    | /api/crm/dashboard               | dashboard_data()          | Dados do dashboard                      |
| GET    | /api/crm/cliente/:id/pdfs        | buscar_pdfs_cliente()     | Busca PDFs do cliente na pasta Canopus |
| GET    | /api/crm/download-pdf/:filename  | download_pdf()            | Download de PDF específico              |

---

### 2.3. Portal Consórcio (`backend/routes/portal_consorcio.py`)
**Blueprint:** `portal_bp`, prefix=`/portal-consorcio`

| Método | URL                                      | Função                      | Descrição                          |
|--------|------------------------------------------|-----------------------------|------------------------------------|
| GET    | /portal-consorcio/login                  | login_page()                | Página de login                    |
| POST   | /portal-consorcio/api/login              | login()                     | Login no portal                    |
| POST   | /portal-consorcio/api/logout             | logout()                    | Logout                             |
| GET    | /portal-consorcio/dashboard              | dashboard_page()            | Dashboard do portal                |
| GET    | /portal-consorcio/api/dashboard          | dashboard_data()            | Dados do dashboard                 |
| GET    | /portal-consorcio/clientes               | clientes_page()             | Página de clientes                 |
| GET    | /portal-consorcio/api/clientes           | listar_clientes()           | Lista clientes do consórcio        |
| POST   | /portal-consorcio/api/clientes           | criar_cliente()             | Criar cliente final                |
| GET    | /portal-consorcio/boletos                | boletos_page()              | Página de boletos                  |
| GET    | /portal-consorcio/api/boletos            | listar_boletos()            | Lista boletos                      |
| POST   | /portal-consorcio/api/boletos/gerar      | gerar_boleto()              | Gera novo boleto                   |
| POST   | /portal-consorcio/api/boletos/enviar     | enviar_boleto()             | Envia boleto por WhatsApp          |

---

### 2.4. Automação (`backend/routes/automation.py`)
**Blueprint:** `automation_bp`, prefix=`/api/automation`

| Método | URL                                  | Função                        | Descrição                               |
|--------|--------------------------------------|-------------------------------|-----------------------------------------|
| POST   | /api/automation/executar-completa    | executar_automacao_completa() | Executa automação completa (gera + envia)|
| POST   | /api/automation/gerar-boletos        | gerar_boletos()               | Gera boletos sem enviar                 |
| GET    | /api/automation/historico            | get_historico()               | Histórico de automações                 |
| GET    | /api/automation/status               | get_status()                  | Status da automação em execução         |

---

### 2.5. Automação Canopus (`backend/routes/automation_canopus.py`)
**Blueprint:** `automation_canopus_bp`, prefix=`/api/automation`

| Método | URL                                      | Função                      | Descrição                               |
|--------|------------------------------------------|-----------------------------|------------------------------------------|
| GET    | /api/automation/consultores              | listar_consultores()        | Lista todos os consultores               |
| GET    | /api/automation/consultores/:id          | obter_consultor()           | Detalhes de um consultor                 |
| POST   | /api/automation/consultores              | criar_consultor()           | Cria novo consultor                      |
| PUT    | /api/automation/consultores/:id          | atualizar_consultor()       | Atualiza dados do consultor              |
| DELETE | /api/automation/consultores/:id          | deletar_consultor()         | Remove consultor                         |
| POST   | /api/automation/executar                 | executar_automacao()        | Executa download de boletos Canopus      |
| GET    | /api/automation/execucoes                | listar_execucoes()          | Lista histórico de execuções             |
| GET    | /api/automation/execucoes/:id            | obter_execucao()            | Detalhes de uma execução                 |
| POST   | /api/automation/importar-excel           | importar_excel()            | Importa clientes de planilha Excel       |
| GET    | /api/automation/clientes-canopus         | listar_clientes_canopus()   | Lista clientes importados do Canopus     |

---

### 2.6. WhatsApp - Evolution API (`backend/routes/whatsapp.py`)
**Blueprint:** `whatsapp_bp`, prefix=`/api/whatsapp`

| Método | URL                        | Função               | Descrição                          |
|--------|----------------------------|----------------------|------------------------------------|
| POST   | /api/whatsapp/conectar     | conectar()           | Inicia conexão e gera QR Code      |
| GET    | /api/whatsapp/qr           | obter_qr()           | Obtém QR Code                      |
| GET    | /api/whatsapp/status       | verificar_status()   | Verifica status da conexão         |
| POST   | /api/whatsapp/desconectar  | desconectar()        | Desconecta WhatsApp                |
| POST   | /api/whatsapp/enviar       | enviar_mensagem()    | Envia mensagem de texto            |
| POST   | /api/whatsapp/enviar-pdf   | enviar_pdf()         | Envia PDF via WhatsApp             |

---

### 2.7. WhatsApp - Baileys (`backend/routes/whatsapp_baileys.py`)
**Blueprint:** `whatsapp_baileys_bp`, prefix=`/api/whatsapp-baileys`

| Método | URL                               | Função               | Descrição                     |
|--------|-----------------------------------|----------------------|-------------------------------|
| POST   | /api/whatsapp-baileys/conectar    | conectar()           | Conectar via Baileys          |
| GET    | /api/whatsapp-baileys/qr          | obter_qr()           | Obter QR Code                 |
| GET    | /api/whatsapp-baileys/status      | verificar_status()   | Status da conexão             |
| POST   | /api/whatsapp-baileys/desconectar | desconectar()        | Desconectar                   |
| POST   | /api/whatsapp-baileys/enviar      | enviar_mensagem()    | Enviar mensagem               |

---

### 2.8. WhatsApp - WPPConnect (`backend/routes/whatsapp_wppconnect.py`)
**Blueprint:** `whatsapp_wppconnect_bp`, prefix=`/api/whatsapp-wppconnect`

| Método | URL                                  | Função               | Descrição                     |
|--------|--------------------------------------|----------------------|-------------------------------|
| POST   | /api/whatsapp-wppconnect/conectar    | conectar()           | Conectar via WPPConnect       |
| GET    | /api/whatsapp-wppconnect/qr          | obter_qr()           | Obter QR Code                 |
| GET    | /api/whatsapp-wppconnect/status      | verificar_status()   | Status da conexão             |
| POST   | /api/whatsapp-wppconnect/desconectar | desconectar()        | Desconectar                   |
| POST   | /api/whatsapp-wppconnect/enviar      | enviar_mensagem()    | Enviar mensagem               |

---

### 2.9. Webhooks (`backend/routes/webhook.py`)
**Blueprint:** `webhook_bp`, prefix=`/api/webhook`

| Método | URL                      | Função            | Descrição                              |
|--------|--------------------------|-------------------|----------------------------------------|
| POST   | /api/webhook/whatsapp    | whatsapp_webhook()| Recebe notificações do WPPConnect      |

---

### 2.10. Boletos Modelo (`backend/routes/boletos_modelo.py`)

| Método | URL                                 | Função                  | Descrição                        |
|--------|-------------------------------------|-------------------------|----------------------------------|
| GET    | /api/boletos-modelo                 | listar_boletos()        | Lista boletos modelo             |
| POST   | /api/boletos-modelo                 | criar_boleto()          | Cria boleto modelo               |
| GET    | /api/boletos-modelo/:id             | obter_boleto()          | Detalhes do boleto modelo        |
| PUT    | /api/boletos-modelo/:id             | atualizar_boleto()      | Atualiza boleto modelo           |
| DELETE | /api/boletos-modelo/:id             | deletar_boleto()        | Remove boleto modelo             |

---

### 2.11. Rotas de Páginas HTML (em `backend/app.py`)

| Método | URL                          | Função                    | Template                                  |
|--------|------------------------------|---------------------------|-------------------------------------------|
| GET    | /                            | index()                   | landing.html                              |
| GET    | /login-cliente               | login_cliente()           | login-cliente.html                        |
| GET    | /login-admin                 | login_admin()             | login-admin.html                          |
| GET    | /crm/dashboard               | crm_dashboard()           | crm-cliente/dashboard.html                |
| GET    | /crm/cadastro-clientes       | crm_cadastro()            | crm-cliente/cadastro-clientes.html        |
| GET    | /crm/whatsapp                | crm_whatsapp()            | crm-cliente/whatsapp-wppconnect.html      |
| GET    | /crm/whatsapp-baileys        | crm_whatsapp_baileys()    | crm-cliente/whatsapp-baileys.html         |
| GET    | /crm/disparos                | crm_disparos()            | crm-cliente/disparos.html                 |
| GET    | /crm/monitoramento           | crm_monitoramento()       | crm-cliente/monitoramento.html            |
| GET    | /crm/graficos                | crm_graficos()            | crm-cliente/graficos.html                 |
| GET    | /crm/automacao-canopus       | crm_automacao_canopus()   | crm-cliente/automacao-canopus.html        |
| GET    | /crm/cliente-debitos         | crm_cliente_debitos()     | crm-cliente/cliente-debitos.html          |
| GET    | /admin/dashboard             | admin_dashboard()         | crm-admin/dashboard-admin.html            |

---

## 3. TABELAS DO BANCO DE DADOS

**Banco:** PostgreSQL
**Nome:** `nexus_crm`
**Porta:** 5434 (padrão) ou 5432
**Schema:** `database/schema.sql` e `backend/sql/criar_tabelas_portal.sql`

### 3.1. Tabelas Principais (schema.sql)

#### **usuarios**
Tabela de autenticação de usuários do sistema.

| Coluna         | Tipo         | Descrição                              |
|----------------|--------------|----------------------------------------|
| id             | SERIAL PK    | ID único                               |
| email          | VARCHAR(150) | Email (único)                          |
| password_hash  | VARCHAR(255) | Senha hashada (bcrypt)                 |
| tipo           | VARCHAR(20)  | 'cliente' ou 'admin'                   |
| ativo          | BOOLEAN      | Ativo/Inativo                          |
| created_at     | TIMESTAMP    | Data de criação                        |
| updated_at     | TIMESTAMP    | Última atualização                     |

---

#### **clientes_nexus**
Clientes empresários que usam o sistema Nexus.

| Coluna          | Tipo         | Descrição                              |
|-----------------|--------------|----------------------------------------|
| id              | SERIAL PK    | ID único                               |
| usuario_id      | INTEGER FK   | → usuarios(id)                         |
| nome_empresa    | VARCHAR(200) | Nome da empresa                        |
| cnpj            | VARCHAR(18)  | CNPJ (único)                           |
| telefone        | VARCHAR(20)  | Telefone de contato                    |
| whatsapp_numero | VARCHAR(20)  | Número WhatsApp                        |
| email_contato   | VARCHAR(150) | Email de contato                       |
| data_cadastro   | TIMESTAMP    | Data de cadastro                       |
| ativo           | BOOLEAN      | Ativo/Inativo                          |

---

#### **clientes_finais**
Clientes finais dos consórcios (cadastrados pelo Portal Consórcio).

| Coluna              | Tipo          | Descrição                              |
|---------------------|---------------|----------------------------------------|
| id                  | SERIAL PK     | ID único                               |
| cliente_nexus_id    | INTEGER FK    | → clientes_nexus(id)                   |
| nome_completo       | VARCHAR(255)  | Nome completo                          |
| cpf                 | VARCHAR(14)   | CPF (único)                            |
| rg                  | VARCHAR(20)   | RG                                     |
| data_nascimento     | DATE          | Data de nascimento                     |
| email               | VARCHAR(255)  | Email                                  |
| telefone_fixo       | VARCHAR(20)   | Telefone fixo                          |
| telefone_celular    | VARCHAR(20)   | Celular                                |
| whatsapp            | VARCHAR(20)   | WhatsApp                               |
| cep                 | VARCHAR(10)   | CEP                                    |
| logradouro          | VARCHAR(255)  | Endereço                               |
| numero              | VARCHAR(20)   | Número                                 |
| complemento         | VARCHAR(100)  | Complemento                            |
| bairro              | VARCHAR(100)  | Bairro                                 |
| cidade              | VARCHAR(100)  | Cidade                                 |
| estado              | VARCHAR(2)    | UF                                     |
| numero_contrato     | VARCHAR(50)   | Número do contrato (único)             |
| grupo_consorcio     | VARCHAR(50)   | Grupo do consórcio                     |
| cota_consorcio      | VARCHAR(50)   | Cota                                   |
| valor_credito       | DECIMAL(12,2) | Valor do crédito                       |
| valor_parcela       | DECIMAL(10,2) | Valor da parcela                       |
| prazo_meses         | INTEGER       | Prazo em meses                         |
| parcelas_pagas      | INTEGER       | Parcelas pagas                         |
| parcelas_pendentes  | INTEGER       | Parcelas pendentes                     |
| data_adesao         | DATE          | Data de adesão                         |
| status_contrato     | VARCHAR(50)   | 'ativo', 'suspenso', 'contemplado'     |
| origem              | VARCHAR(50)   | 'portal', 'importacao', 'api'          |
| cadastrado_por      | VARCHAR(100)  | Usuário que cadastrou                  |
| ativo               | BOOLEAN       | Ativo/Inativo                          |
| observacoes         | TEXT          | Observações                            |
| created_at          | TIMESTAMP     | Data de criação                        |
| updated_at          | TIMESTAMP     | Última atualização                     |

**Índices:**
- `idx_clientes_finais_nexus` (cliente_nexus_id)
- `idx_clientes_finais_cpf` (cpf)
- `idx_clientes_finais_status` (status_contrato)

---

#### **boletos**
Boletos gerados pelo sistema (Portal Consórcio).

| Coluna              | Tipo          | Descrição                              |
|---------------------|---------------|----------------------------------------|
| id                  | SERIAL PK     | ID único                               |
| cliente_nexus_id    | INTEGER FK    | → clientes_nexus(id)                   |
| cliente_final_id    | INTEGER FK    | → clientes_finais(id)                  |
| numero_boleto       | VARCHAR(100)  | Número do boleto (único)               |
| linha_digitavel     | VARCHAR(100)  | Linha digitável                        |
| codigo_barras       | VARCHAR(100)  | Código de barras                       |
| nosso_numero        | VARCHAR(50)   | Nosso número                           |
| valor_original      | DECIMAL(10,2) | Valor original                         |
| valor_atualizado    | DECIMAL(10,2) | Valor atualizado                       |
| data_vencimento     | DATE          | Data de vencimento                     |
| data_emissao        | DATE          | Data de emissão                        |
| data_pagamento      | DATE          | Data de pagamento                      |
| mes_referencia      | INTEGER       | Mês de referência (1-12)               |
| ano_referencia      | INTEGER       | Ano de referência                      |
| numero_parcela      | INTEGER       | Número da parcela                      |
| descricao           | TEXT          | Descrição                              |
| status              | VARCHAR(50)   | 'pendente', 'pago', 'vencido'          |
| status_envio        | VARCHAR(50)   | 'nao_enviado', 'enviado', 'erro'       |
| data_envio          | TIMESTAMP     | Data de envio                          |
| enviado_por         | VARCHAR(100)  | Usuário que enviou                     |
| pdf_filename        | VARCHAR(255)  | Nome do arquivo PDF                    |
| pdf_path            | TEXT          | Caminho do PDF                         |
| pdf_url             | TEXT          | URL do PDF                             |
| pdf_size            | INTEGER       | Tamanho do PDF (bytes)                 |
| gerado_por          | VARCHAR(50)   | 'portal', 'automatico', 'importacao'   |
| observacoes         | TEXT          | Observações                            |
| created_at          | TIMESTAMP     | Data de criação                        |
| updated_at          | TIMESTAMP     | Última atualização                     |

**Índices:**
- `idx_boletos_cliente_final` (cliente_final_id)
- `idx_boletos_vencimento` (data_vencimento)
- `idx_boletos_status` (status)

---

#### **disparos**
Histórico de disparos de WhatsApp.

| Coluna            | Tipo         | Descrição                              |
|-------------------|--------------|----------------------------------------|
| id                | SERIAL PK    | ID único                               |
| boleto_id         | INTEGER FK   | → boletos(id)                          |
| cliente_nexus_id  | INTEGER FK   | → clientes_nexus(id)                   |
| telefone_destino  | VARCHAR(20)  | Telefone de destino                    |
| status            | VARCHAR(50)  | 'pendente', 'enviado', 'erro'          |
| mensagem_enviada  | TEXT         | Mensagem enviada                       |
| erro              | TEXT         | Mensagem de erro                       |
| data_disparo      | TIMESTAMP    | Data do disparo                        |
| created_at        | TIMESTAMP    | Data de criação                        |

---

#### **historico_disparos**
Histórico consolidado de disparos em massa.

| Coluna            | Tipo         | Descrição                              |
|-------------------|--------------|----------------------------------------|
| id                | SERIAL PK    | ID único                               |
| cliente_nexus_id  | INTEGER FK   | → clientes_nexus(id)                   |
| tipo_disparo      | VARCHAR(50)  | 'manual', 'massa', 'automatico'        |
| total_envios      | INTEGER      | Total de envios                        |
| envios_sucesso    | INTEGER      | Envios com sucesso                     |
| envios_erro       | INTEGER      | Envios com erro                        |
| mensagem_enviada  | TEXT         | Mensagem enviada                       |
| horario_execucao  | TIMESTAMP    | Horário de execução                    |
| executado_por     | VARCHAR(100) | Usuário que executou                   |
| boletos_ids       | INTEGER[]    | Array de IDs de boletos                |
| clientes_ids      | INTEGER[]    | Array de IDs de clientes               |
| status            | VARCHAR(50)  | Status geral                           |
| detalhes          | JSONB        | Detalhes adicionais (JSON)             |
| created_at        | TIMESTAMP    | Data de criação                        |

---

#### **whatsapp_sessions**
Sessões ativas de WhatsApp.

| Coluna           | Tipo         | Descrição                              |
|------------------|--------------|----------------------------------------|
| id               | SERIAL PK    | ID único                               |
| cliente_nexus_id | INTEGER FK   | → clientes_nexus(id)                   |
| instance_name    | VARCHAR(100) | Nome da instância (único)              |
| phone_number     | VARCHAR(20)  | Número conectado                       |
| status           | VARCHAR(50)  | 'connected', 'disconnected', 'waiting' |
| qr_code          | TEXT         | QR Code em base64                      |
| session_data     | JSONB        | Dados da sessão                        |
| connected_at     | TIMESTAMP    | Data de conexão                        |
| disconnected_at  | TIMESTAMP    | Data de desconexão                     |
| created_at       | TIMESTAMP    | Data de criação                        |
| updated_at       | TIMESTAMP    | Última atualização                     |

---

#### **configuracoes_cliente**
Configurações por cliente Nexus.

| Coluna                   | Tipo         | Descrição                              |
|--------------------------|--------------|----------------------------------------|
| id                       | SERIAL PK    | ID único                               |
| cliente_nexus_id         | INTEGER FK   | → clientes_nexus(id) (único)           |
| mensagem_antibloqueio    | TEXT         | Mensagem anti-bloqueio                 |
| data_disparo_automatico  | DATE         | Data do próximo disparo                |
| intervalo_disparos       | INTEGER      | Intervalo entre disparos (segundos)    |
| horario_disparo          | TIME         | Horário do disparo automático          |
| created_at               | TIMESTAMP    | Data de criação                        |
| updated_at               | TIMESTAMP    | Última atualização                     |

---

#### **configuracoes_automacao**
Configurações de automação (Portal Consórcio).

| Coluna                          | Tipo         | Descrição                              |
|---------------------------------|--------------|----------------------------------------|
| id                              | SERIAL PK    | ID único                               |
| cliente_nexus_id                | INTEGER FK   | → clientes_nexus(id) (único)           |
| disparo_automatico_habilitado   | BOOLEAN      | Habilita disparo automático            |
| dias_antes_vencimento           | INTEGER      | Dias antes do vencimento               |
| horario_disparo                 | TIME         | Horário do disparo                     |
| mensagem_antibloqueio           | TEXT         | Mensagem padrão                        |
| mensagem_personalizada          | TEXT         | Mensagem personalizada                 |
| intervalo_min_segundos          | INTEGER      | Intervalo mínimo                       |
| intervalo_max_segundos          | INTEGER      | Intervalo máximo                       |
| pausa_apos_disparos             | INTEGER      | Pausa após N disparos                  |
| tempo_pausa_segundos            | INTEGER      | Tempo de pausa (segundos)              |
| created_at                      | TIMESTAMP    | Data de criação                        |
| updated_at                      | TIMESTAMP    | Última atualização                     |

---

#### **usuarios_portal**
Usuários administrativos do Portal Consórcio.

| Coluna         | Tipo         | Descrição                              |
|----------------|--------------|----------------------------------------|
| id             | SERIAL PK    | ID único                               |
| nome_completo  | VARCHAR(255) | Nome completo                          |
| email          | VARCHAR(255) | Email (único)                          |
| senha          | VARCHAR(255) | Senha hashada (bcrypt)                 |
| nivel_acesso   | VARCHAR(50)  | 'admin', 'operador', 'consulta'        |
| ativo          | BOOLEAN      | Ativo/Inativo                          |
| ultimo_acesso  | TIMESTAMP    | Último acesso                          |
| created_at     | TIMESTAMP    | Data de criação                        |

---

#### **pastas_digitais**
Sistema de pastas para organização de boletos.

| Coluna            | Tipo         | Descrição                              |
|-------------------|--------------|----------------------------------------|
| id                | SERIAL PK    | ID único                               |
| cliente_nexus_id  | INTEGER FK   | → clientes_nexus(id)                   |
| cliente_final_id  | INTEGER FK   | → clientes_finais(id)                  |
| nome_pasta        | VARCHAR(255) | Nome da pasta                          |
| caminho_completo  | TEXT         | Caminho completo                       |
| pasta_pai_id      | INTEGER FK   | → pastas_digitais(id)                  |
| tipo              | VARCHAR(50)  | 'pasta', 'link_boleto'                 |
| boleto_id         | INTEGER FK   | → boletos(id) (se tipo=link_boleto)    |
| cor               | VARCHAR(20)  | Cor da pasta (hex)                     |
| icone             | VARCHAR(50)  | Emoji ou ícone                         |
| ordem             | INTEGER      | Ordem de exibição                      |
| created_at        | TIMESTAMP    | Data de criação                        |
| updated_at        | TIMESTAMP    | Última atualização                     |

---

#### **logs_sistema**
Logs de todas as operações do sistema.

| Coluna      | Tipo         | Descrição                              |
|-------------|--------------|----------------------------------------|
| id          | SERIAL PK    | ID único                               |
| tipo        | VARCHAR(20)  | 'info', 'warning', 'error', 'success'  |
| categoria   | VARCHAR(50)  | Categoria do log                       |
| mensagem    | TEXT         | Mensagem do log                        |
| detalhes    | JSONB        | Detalhes adicionais (JSON)             |
| usuario_id  | INTEGER FK   | → usuarios(id)                         |
| created_at  | TIMESTAMP    | Data de criação                        |

**Índices:**
- `idx_logs_tipo` (tipo)
- `idx_logs_created` (created_at DESC)

---

#### **status_sistema**
Status geral do sistema.

| Coluna              | Tipo      | Descrição                              |
|---------------------|-----------|----------------------------------------|
| id                  | SERIAL PK | ID único                               |
| ativo               | BOOLEAN   | Sistema ativo                          |
| ultima_atualizacao  | TIMESTAMP | Última atualização                     |

---

### 3.2. Tabelas Canopus (automation/canopus/criar_tabelas_automacao.sql)

#### **consultores**
Consultores do sistema Canopus.

| Coluna           | Tipo         | Descrição                              |
|------------------|--------------|----------------------------------------|
| id               | SERIAL PK    | ID único                               |
| nome             | VARCHAR(255) | Nome do consultor                      |
| email            | VARCHAR(255) | Email                                  |
| telefone         | VARCHAR(20)  | Telefone                               |
| whatsapp         | VARCHAR(20)  | WhatsApp                               |
| cpf              | VARCHAR(14)  | CPF (adicionado em migration)          |
| empresa          | VARCHAR(255) | Empresa                                |
| ponto_venda      | VARCHAR(255) | Ponto de venda                         |
| usuario_canopus  | VARCHAR(255) | Usuário no sistema Canopus             |
| senha_criptografada | TEXT      | Senha criptografada                    |
| ativo            | BOOLEAN      | Ativo/Inativo                          |
| created_at       | TIMESTAMP    | Data de criação                        |
| updated_at       | TIMESTAMP    | Última atualização                     |

---

#### **clientes_canopus**
Clientes importados do sistema Canopus (via Excel).

| Coluna           | Tipo         | Descrição                              |
|------------------|--------------|----------------------------------------|
| id               | SERIAL PK    | ID único                               |
| consultor_id     | INTEGER FK   | → consultores(id)                      |
| cpf              | VARCHAR(14)  | CPF do cliente                         |
| nome             | VARCHAR(255) | Nome completo                          |
| whatsapp         | VARCHAR(20)  | WhatsApp                               |
| grupo            | VARCHAR(100) | Grupo do consórcio                     |
| cota             | VARCHAR(100) | Cota do consórcio                      |
| created_at       | TIMESTAMP    | Data de importação                     |
| updated_at       | TIMESTAMP    | Última atualização                     |

---

#### **execucoes_automacao**
Histórico de execuções da automação Canopus.

| Coluna              | Tipo         | Descrição                              |
|---------------------|--------------|----------------------------------------|
| id                  | SERIAL PK    | ID único                               |
| automacao_id        | UUID         | UUID da execução                       |
| tipo                | VARCHAR(50)  | 'manual', 'agendada', 'teste'          |
| consultor_id        | INTEGER FK   | → consultores(id) (NULL = todos)       |
| status              | VARCHAR(50)  | 'em_andamento', 'concluida', 'erro'    |
| inicio              | TIMESTAMP    | Início da execução                     |
| fim                 | TIMESTAMP    | Fim da execução                        |
| total_clientes      | INTEGER      | Total de clientes processados          |
| total_downloads     | INTEGER      | Total de downloads realizados          |
| total_erros         | INTEGER      | Total de erros                         |
| parametros          | JSONB        | Parâmetros da execução                 |
| mensagem_erro       | TEXT         | Mensagem de erro (se houver)           |
| created_at          | TIMESTAMP    | Data de criação                        |

---

#### **downloads_canopus**
Registro de downloads individuais de boletos.

| Coluna           | Tipo         | Descrição                              |
|------------------|--------------|----------------------------------------|
| id               | SERIAL PK    | ID único                               |
| automacao_id     | UUID         | UUID da execução                       |
| cliente_canopus_id | INTEGER FK | → clientes_canopus(id)                 |
| consultor_id     | INTEGER FK   | → consultores(id)                      |
| cpf              | VARCHAR(14)  | CPF do cliente                         |
| nome_arquivo     | VARCHAR(500) | Nome do arquivo baixado                |
| caminho_arquivo  | TEXT         | Caminho completo do arquivo            |
| tamanho_bytes    | INTEGER      | Tamanho do arquivo                     |
| status           | VARCHAR(50)  | 'sucesso', 'erro', 'pulado'            |
| mensagem_erro    | TEXT         | Mensagem de erro                       |
| data_download    | TIMESTAMP    | Data do download                       |
| created_at       | TIMESTAMP    | Data de criação                        |

---

### 3.3. Views

#### **view_dashboard_cliente**
View consolidada para o dashboard do cliente.

Campos retornados:
- `cliente_nexus_id`, `nome_empresa`, `cnpj`, `whatsapp_numero`, `email_contato`
- `total_boletos`, `boletos_enviados`, `boletos_pendentes`, `boletos_vencidos`, `boletos_pagos`
- `valor_total`, `valor_pago`, `valor_pendente`
- `total_disparos`, `disparos_enviados`, `disparos_erro`, `disparos_pendentes`
- `taxa_sucesso_disparos` (%)
- `total_clientes_unicos`
- `ultima_atualizacao`

---

## 4. SERVIÇOS (backend/services/)

### 4.1. **automation_service.py**
**Classe:** `AutomationService`

**Métodos principais:**
- `executar_automacao_completa(cliente_nexus_id)` - Executa todo o fluxo (gerar boletos + enviar)
- `gerar_boletos_sem_enviar(cliente_nexus_id)` - Apenas gera boletos sem enviar
- `processar_disparo_boletos(cliente_nexus_id, boletos_ids)` - Dispara boletos específicos

**O que faz:**
Orquestra a geração e envio automático de boletos via WhatsApp.

---

### 4.2. **automation_scheduler.py**
**Classe:** `AutomationScheduler`

**Métodos principais:**
- `iniciar()` - Inicia o scheduler (background thread)
- `parar()` - Para o scheduler
- `agendar_tarefa(cliente_nexus_id, horario)` - Agenda automação
- `executar_tarefas_agendadas()` - Loop principal

**O que faz:**
Gerencia tarefas agendadas de automação em background.

---

### 4.3. **boleto_generator.py**
**Classe:** `BoletoGenerator`

**Métodos principais:**
- `gerar_boleto_pdf(dados_boleto)` - Gera PDF do boleto
- `gerar_codigo_barras(numero_boleto)` - Gera código de barras
- `calcular_linha_digitavel(numero_boleto)` - Calcula linha digitável

**O que faz:**
Gera PDFs de boletos bancários com código de barras usando ReportLab.

---

### 4.4. **boleto_modelo_service.py**
**Classe:** `BoletoModeloService`

**Métodos principais:**
- `listar_boletos_modelo(cliente_nexus_id)` - Lista boletos modelo
- `criar_boleto_modelo(dados)` - Cria novo boleto modelo
- `atualizar_boleto_modelo(id, dados)` - Atualiza boleto modelo
- `deletar_boleto_modelo(id)` - Remove boleto modelo

**O que faz:**
Gerencia templates de boletos reutilizáveis.

---

### 4.5. **whatsapp_service.py**
**Classe:** `WhatsAppService`

**Métodos principais:**
- `conectar()` - Conecta ao WhatsApp
- `obter_qr()` - Obtém QR Code
- `verificar_status()` - Verifica status da conexão
- `desconectar()` - Desconecta
- `enviar_mensagem(numero, texto)` - Envia mensagem de texto
- `enviar_pdf(numero, pdf_path, caption)` - Envia PDF

**O que faz:**
Abstração genérica para comunicação WhatsApp (delega para Evolution, Baileys ou WPPConnect).

---

### 4.6. **whatsapp_evolution.py**
**Classe:** `EvolutionAPIService`

**Endpoint:** `http://localhost:8080` (Evolution API)

**Métodos principais:**
- `criar_instancia(instance_name)` - Cria instância no Evolution
- `conectar_instancia(instance_name)` - Conecta instância
- `obter_qr_code(instance_name)` - Obtém QR Code
- `verificar_conexao(instance_name)` - Verifica status
- `enviar_texto(instance_name, numero, mensagem)` - Envia texto
- `enviar_arquivo(instance_name, numero, arquivo_path, caption)` - Envia arquivo

**O que faz:**
Cliente para Evolution API (solução WhatsApp multi-instância).

---

### 4.7. **whatsapp_baileys.py**
**Módulo:** `whatsapp_baileys_service`

**Endpoint:** `http://localhost:3000` (Baileys Standalone)

**Métodos principais:**
- `conectar()` - Conecta ao servidor Baileys
- `obter_qr()` - Obtém QR Code
- `verificar_status()` - Verifica conexão
- `desconectar()` - Desconecta
- `enviar_mensagem(numero, texto)` - Envia texto
- `enviar_pdf(numero, pdf_path, caption)` - Envia PDF

**O que faz:**
Cliente para servidor Baileys (descontinuado, em favor de Evolution).

---

### 4.8. **wppconnect_service.py**
**Classe:** `WPPConnectService`

**Endpoint:** `http://localhost:3001` (WPPConnect Server)

**Métodos principais:**
- `conectar(session_name)` - Inicia sessão WPPConnect
- `obter_qr(session_name)` - Obtém QR Code
- `verificar_status(session_name)` - Verifica status
- `desconectar(session_name)` - Fecha sessão
- `enviar_mensagem(session_name, numero, texto)` - Envia texto
- `enviar_arquivo(session_name, numero, arquivo_base64, filename, caption)` - Envia arquivo

**O que faz:**
Cliente para WPPConnect Server (alternativa ao Evolution API).

---

### 4.9. **mensagens_personalizadas.py**
**Função:** `gerar_mensagem_antibloqueio(nome_cliente, vencimento)`

**O que faz:**
Gera mensagens variadas para evitar detecção de spam pelo WhatsApp.

---

### 4.10. **pdf_generator.py**
**Classe:** `PDFGenerator`

**Métodos principais:**
- `gerar_pdf_generico(dados, template)` - Gera PDF genérico
- `gerar_relatorio(dados)` - Gera relatório em PDF

**O que faz:**
Gerador genérico de PDFs usando ReportLab e Pillow.

---

### 4.11. **webscraping.py**
**Função:** `extrair_dados_site(url)`

**O que faz:**
Extrai dados de sites usando BeautifulSoup (para integrações futuras).

---

## 5. TEMPLATES/PÁGINAS HTML

### 5.1. Páginas Principais

| Template                                          | Rota HTML                  | Descrição                               |
|---------------------------------------------------|----------------------------|-----------------------------------------|
| `landing.html`                                    | `/`                        | Landing page inicial                    |
| `login-cliente.html`                              | `/login-cliente`           | Login do cliente empresário             |
| `login-admin.html`                                | `/login-admin`             | Login do administrador                  |

---

### 5.2. Dashboard Cliente (crm-cliente/)

| Template                                          | Rota HTML                  | Descrição                               |
|---------------------------------------------------|----------------------------|-----------------------------------------|
| `dashboard.html`                                  | `/crm/dashboard`           | Dashboard principal do cliente          |
| `cadastro-clientes.html`                          | `/crm/cadastro-clientes`   | Cadastro de clientes finais             |
| `disparos.html`                                   | `/crm/disparos`            | Gerenciamento de disparos               |
| `monitoramento.html`                              | `/crm/monitoramento`       | Monitoramento do sistema                |
| `graficos.html`                                   | `/crm/graficos`            | Gráficos e relatórios                   |
| `automacao-canopus.html`                          | `/crm/automacao-canopus`   | Automação de downloads Canopus          |
| `cliente-debitos.html`                            | `/crm/cliente-debitos`     | Débitos de um cliente específico        |
| `whatsapp-conexao.html`                           | -                          | (Legado) Conexão WhatsApp               |
| `whatsapp-baileys.html`                           | `/crm/whatsapp-baileys`    | Conexão WhatsApp via Baileys            |
| `whatsapp-wppconnect.html`                        | `/crm/whatsapp`            | Conexão WhatsApp via WPPConnect         |
| `widget-canopus-downloads.html`                   | -                          | Widget de downloads Canopus             |

---

### 5.3. Dashboard Admin (crm-admin/)

| Template                                          | Rota HTML                  | Descrição                               |
|---------------------------------------------------|----------------------------|-----------------------------------------|
| `dashboard-admin.html`                            | `/admin/dashboard`         | Dashboard administrativo                |

---

### 5.4. Portal Consórcio (portal-consorcio/)

| Template                                          | Rota HTML                        | Descrição                               |
|---------------------------------------------------|----------------------------------|-----------------------------------------|
| `login.html`                                      | `/portal-consorcio/login`        | Login do portal                         |
| `dashboard.html`                                  | `/portal-consorcio/dashboard`    | Dashboard do portal                     |
| `clientes.html`                                   | `/portal-consorcio/clientes`     | Gerenciamento de clientes finais        |
| `boletos.html`                                    | `/portal-consorcio/boletos`      | Gerenciamento de boletos                |
| `boletos-modelo.html`                             | `/portal-consorcio/boletos-modelo` | Boletos modelo                        |

---

## 6. INTEGRAÇÕES EXTERNAS

### 6.1. **Evolution API** (WhatsApp Multi-Instância)
- **Tipo:** API REST
- **URL:** `http://localhost:8080`
- **Porta:** 8080
- **Descrição:** Sistema multi-instância de WhatsApp baseado em Baileys
- **Endpoints usados:**
  - `POST /instance/create` - Criar instância
  - `POST /instance/connect/:instance` - Conectar instância
  - `GET /instance/qr/:instance` - Obter QR Code
  - `GET /instance/status/:instance` - Status da conexão
  - `POST /message/sendText/:instance` - Enviar texto
  - `POST /message/sendMedia/:instance` - Enviar arquivo/PDF
- **Arquivos relacionados:**
  - `backend/services/whatsapp_evolution.py`
  - `backend/services/evolution_service.py`
  - `backend/routes/whatsapp.py`
- **Localização:** `D:\Nexus\evolution-api-standalone\`

---

### 6.2. **WPPConnect Server** (WhatsApp)
- **Tipo:** API REST + WebSocket
- **URL:** `http://localhost:3001`
- **Porta:** 3001
- **Descrição:** Servidor WhatsApp baseado em Puppeteer
- **Endpoints usados:**
  - `POST /:session/start-session` - Iniciar sessão
  - `GET /:session/qr-code` - Obter QR Code
  - `GET /:session/status` - Status da sessão
  - `POST /:session/close-session` - Fechar sessão
  - `POST /:session/send-message` - Enviar mensagem
  - `POST /:session/send-file-base64` - Enviar arquivo
- **Webhooks:**
  - `POST /api/webhook/whatsapp` (recebe eventos do WPPConnect)
- **Arquivos relacionados:**
  - `backend/services/wppconnect_service.py`
  - `backend/routes/whatsapp_wppconnect.py`
  - `backend/routes/webhook.py`
- **Localização:** `D:\Nexus\wppconnect-server\`
- **Inicialização:** `wppconnect-server\start.bat`

---

### 6.3. **PostgreSQL** (Banco de Dados)
- **Tipo:** Banco de dados relacional
- **Host:** `localhost`
- **Porta:** 5434 (ou 5432)
- **Banco:** `nexus_crm`
- **Usuário:** `postgres`
- **Senha:** (configurada em `.env`)
- **Driver:** `psycopg` (psycopg3)
- **Arquivos relacionados:**
  - `backend/models/database.py`
  - `backend/config.py`
  - `database/schema.sql`

---

### 6.4. **Canopus** (Sistema de Consórcios - Web Scraping)
- **Tipo:** Automação web (Playwright)
- **URL:** Sistema externo (web scraping)
- **Descrição:** Sistema de consórcios do qual são baixados boletos
- **Tecnologia:** Playwright (navegador headless)
- **Arquivos relacionados:**
  - `automation/canopus/canopus_automation.py` - Automação principal
  - `automation/canopus/orquestrador.py` - Orquestrador
  - `automation/canopus/canopus_config.py` - Configurações
  - `automation/canopus/excel_importer.py` - Importador de planilhas
- **Credenciais:** Armazenadas criptografadas na tabela `consultores`

---

### 6.5. **Baileys** (descontinuado)
- **Tipo:** Biblioteca WhatsApp
- **URL:** `http://localhost:3000`
- **Porta:** 3000
- **Status:** Descontinuado em favor de Evolution API
- **Localização:** `D:\Nexus\whatsapp-baileys.OLD\`

---

## 7. FLUXOS PRINCIPAIS

### 7.1. **Fluxo de Login (Cliente)**

```
1. Usuário acessa: /login-cliente (login-cliente.html)
2. Frontend envia: POST /api/auth/login
   {
     "email": "cliente@exemplo.com",
     "password": "senha123"
   }
3. Backend em: backend/routes/auth.py → login()
4. Verifica credenciais no banco:
   - Busca na tabela usuarios (tipo='cliente')
   - Valida senha com bcrypt
5. Cria sessão:
   - session['usuario_id'] = usuario.id
   - session['cliente_nexus_id'] = cliente_nexus.id
6. Retorna JSON com dados do usuário
7. Frontend redireciona para: /crm/dashboard
```

**Tabelas envolvidas:** `usuarios`, `clientes_nexus`

---

### 7.2. **Fluxo de Disparo de Boletos (Manual)**

```
1. Cliente acessa: /crm/disparos (disparos.html)
2. Cliente seleciona boletos para enviar
3. Frontend envia: POST /api/automation/executar-completa
4. Backend em: backend/routes/automation.py → executar_automacao_completa()
5. Chama serviço: backend/services/automation_service.py
   - AutomationService.executar_automacao_completa(cliente_nexus_id)
6. Busca boletos no banco:
   - SELECT * FROM boletos WHERE status_envio = 'pendente'
7. Para cada boleto:
   a) Busca dados do cliente:
      - SELECT * FROM clientes_finais WHERE id = boleto.cliente_final_id
   b) Gera mensagem anti-bloqueio:
      - services/mensagens_personalizadas.py
   c) Envia via WhatsApp:
      - services/whatsapp_service.py → enviar_pdf()
      - Delega para: whatsapp_evolution.py ou wppconnect_service.py
   d) Chama Evolution API:
      - POST http://localhost:8080/message/sendMedia/:instance
      Body: {
        "number": "5567999991111",
        "mediatype": "document",
        "mimetype": "application/pdf",
        "caption": "Olá João! Segue seu boleto...",
        "media": "base64_pdf_aqui"
      }
   e) Atualiza banco:
      - UPDATE boletos SET status_envio='enviado', data_envio=NOW()
   f) Registra disparo:
      - INSERT INTO disparos (...)
   g) Aguarda intervalo anti-bloqueio (3-7 segundos)
8. Registra histórico:
   - INSERT INTO historico_disparos (...)
9. Retorna resultado ao frontend
```

**Tabelas envolvidas:** `boletos`, `clientes_finais`, `disparos`, `historico_disparos`
**Integrações:** Evolution API (porta 8080) ou WPPConnect (porta 3001)

---

### 7.3. **Fluxo de Automação Canopus (Download de Boletos)**

```
1. Cliente acessa: /crm/automacao-canopus (automacao-canopus.html)
2. Cliente seleciona consultor e clica "Executar Download"
3. Frontend envia: POST /api/automation/executar
   {
     "consultor_id": 1,
     "tipo": "manual"
   }
4. Backend em: backend/routes/automation_canopus.py → executar_automacao()
5. Chama orquestrador: automation/canopus/orquestrador.py
   - CanopusOrquestrador.executar_automacao_completa(consultor_id)
6. Registra execução:
   - INSERT INTO execucoes_automacao (automacao_id, tipo, consultor_id, status='em_andamento')
7. Busca credenciais do consultor:
   - SELECT * FROM consultores WHERE id = consultor_id
   - Descriptografa senha
8. Busca clientes do consultor:
   - SELECT * FROM clientes_canopus WHERE consultor_id = consultor_id
9. Para cada cliente:
   a) Inicializa Playwright:
      - automation/canopus/canopus_automation.py → CanopusAutomation
   b) Faz login no sistema Canopus (web scraping)
   c) Navega até área de boletos
   d) Busca boleto por CPF
   e) Faz download do PDF:
      - Salva em: automation/canopus/downloads/Danner/{nome_cliente}_{mes}.pdf
   f) Registra download:
      - INSERT INTO downloads_canopus (...)
   g) Aguarda intervalo (evitar sobrecarga)
10. Atualiza execução:
    - UPDATE execucoes_automacao SET status='concluida', total_downloads=X
11. Retorna resultado ao frontend
```

**Tabelas envolvidas:** `consultores`, `clientes_canopus`, `execucoes_automacao`, `downloads_canopus`
**Integrações:** Sistema Canopus (web scraping via Playwright)

---

### 7.4. **Fluxo de Cadastro de Cliente (Portal Consórcio)**

```
1. Usuário acessa: /portal-consorcio/clientes (clientes.html)
2. Preenche formulário de cadastro
3. Frontend envia: POST /portal-consorcio/api/clientes
   {
     "nome_completo": "João Silva",
     "cpf": "123.456.789-01",
     "whatsapp": "5567999991111",
     "numero_contrato": "CONS-2024-0001",
     ...
   }
4. Backend em: backend/routes/portal_consorcio.py → criar_cliente()
5. Valida dados:
   - Valida CPF (models/__init__.py → validar_cpf())
   - Verifica se CPF já existe
6. Insere no banco:
   - INSERT INTO clientes_finais (...)
7. Retorna JSON com cliente criado
8. Frontend atualiza lista de clientes
```

**Tabelas envolvidas:** `clientes_finais`

---

### 7.5. **Fluxo de Conexão WhatsApp (Evolution API)**

```
1. Cliente acessa: /crm/whatsapp (whatsapp-wppconnect.html) ou /crm/whatsapp-baileys
2. Cliente clica em "Conectar WhatsApp"
3. Frontend envia: POST /api/whatsapp/conectar
4. Backend em: backend/routes/whatsapp.py → conectar()
5. Chama serviço: backend/services/whatsapp_evolution.py
   - EvolutionAPIService.criar_instancia("nexus_instance_1")
   - POST http://localhost:8080/instance/create
     Body: { "instanceName": "nexus_instance_1" }
   - EvolutionAPIService.conectar_instancia("nexus_instance_1")
   - POST http://localhost:8080/instance/connect/nexus_instance_1
6. Evolution API gera QR Code
7. Frontend faz polling: GET /api/whatsapp/qr (a cada 2 segundos)
8. Backend retorna: GET http://localhost:8080/instance/qr/nexus_instance_1
9. Frontend exibe QR Code
10. Usuário escaneia QR Code com WhatsApp
11. Evolution API notifica conexão bem-sucedida
12. Backend atualiza banco:
    - UPDATE whatsapp_sessions SET status='connected', phone_number='5567999991111'
13. Frontend exibe "Conectado!"
```

**Tabelas envolvidas:** `whatsapp_sessions`
**Integrações:** Evolution API (porta 8080)

---

### 7.6. **Fluxo de Importação Excel (Canopus)**

```
1. Cliente acessa: /crm/automacao-canopus
2. Faz upload de planilha Excel
3. Frontend envia: POST /api/automation/importar-excel
   (FormData com arquivo Excel)
4. Backend em: backend/routes/automation_canopus.py → importar_excel()
5. Salva arquivo temporariamente
6. Chama: automation/canopus/excel_importer.py → ExcelImporter
   - ExcelImporter.importar_planilha(arquivo_path, consultor_id)
7. Lê planilha com pandas/openpyxl
8. Para cada linha:
   a) Extrai: CPF, Nome, WhatsApp, Grupo, Cota
   b) Normaliza dados (limpa CPF, formata WhatsApp)
   c) Insere ou atualiza:
      - INSERT INTO clientes_canopus (...) ON CONFLICT (cpf) DO UPDATE
9. Retorna total de clientes importados
10. Frontend exibe mensagem de sucesso
```

**Tabelas envolvidas:** `clientes_canopus`

---

## 8. ARQUIVOS DE CONFIGURAÇÃO

### 8.1. **`.env`** (Raiz do projeto)
Variáveis de ambiente (não versionado no Git).

```env
# Flask
FLASK_SECRET_KEY=nexus-crm-secret-key-2024
FLASK_ENV=development
FLASK_PORT=5000

# PostgreSQL
DB_HOST=localhost
DB_PORT=5434
DB_NAME=nexus_crm
DB_USER=postgres
DB_PASSWORD=nexus2025

# Automação
AUTOMATION_ENABLED=true
DISPARO_INTERVAL_SECONDS=5

# Diretórios
BOLETO_DIR=boletos
WHATSAPP_SESSION_DIR=whatsapp_sessions
```

---

### 8.2. **`backend/config.py`**
Configurações centralizadas do Flask.

**Variáveis principais:**
- `SECRET_KEY` - Chave secreta do Flask
- `DATABASE_URL` - String de conexão PostgreSQL
- `FLASK_PORT` - Porta do servidor Flask (padrão: 5000)
- `AUTOMATION_ENABLED` - Habilita/desabilita automação
- `BOLETO_PATH` - Caminho da pasta de boletos
- `WHATSAPP_PATH` - Caminho das sessões WhatsApp
- `TEMPLATES_DIR` - Caminho dos templates HTML
- `STATIC_DIR` - Caminho dos arquivos estáticos

---

### 8.3. **`requirements.txt`**
Dependências Python do projeto.

**Principais dependências:**
```
flask==3.0.0
flask-cors==4.0.0
flask-session==0.5.0
psycopg[binary]==3.1.12          # Driver PostgreSQL
bcrypt==4.1.1                     # Hash de senhas
reportlab==4.0.7                  # Geração de PDFs
python-barcode==0.15.1            # Códigos de barras
Pillow==10.1.0                    # Manipulação de imagens
requests==2.31.0                  # Cliente HTTP
python-dateutil==2.8.2            # Manipulação de datas
playwright==1.40.0                # Automação web (Canopus)
pandas==2.1.4                     # Manipulação de dados
openpyxl==3.1.2                   # Leitura de Excel
xlrd==2.0.1                       # Leitura de Excel legado
cryptography==41.0.7              # Criptografia
python-dotenv==1.0.0              # Variáveis de ambiente
beautifulsoup4==4.12.2            # Web scraping
lxml==4.9.3                       # Parser XML/HTML
```

---

### 8.4. **`automation/canopus/canopus_config.py`**
Configurações da automação Canopus.

**Variáveis principais:**
```python
CANOPUS_URL = "https://canopus.exemplo.com"
DOWNLOADS_DIR = "automation/canopus/downloads"
TIMEOUT_NAVEGACAO = 30  # segundos
INTERVALO_ENTRE_DOWNLOADS = 2  # segundos
HEADLESS = True  # Executar navegador em modo headless
```

---

### 8.5. **`automation/canopus/db_config.py`**
Configurações de banco de dados para Canopus.

```python
def get_connection_params():
    return {
        'host': 'localhost',
        'port': 5434,
        'dbname': 'nexus_crm',
        'user': 'postgres',
        'password': 'nexus2025'
    }
```

---

### 8.6. **`wppconnect-server/config.js`** (WPPConnect)
Configuração do WPPConnect Server (Node.js).

---

### 8.7. **`evolution-api-standalone/env.yml`** (Evolution API)
Configuração do Evolution API.

---

## 9. SCRIPTS DE INICIALIZAÇÃO

### 9.1. **`iniciar.bat`** (Windows)
Script principal de inicialização do sistema completo.

**O que faz:**
1. Ativa ambiente virtual Python (`venv\Scripts\activate.bat`)
2. Instala/atualiza dependências Python (`pip install ...`)
3. Verifica se PostgreSQL está acessível
4. Verifica se Node.js está instalado
5. Inicia WPPConnect Server em nova janela:
   - `cd wppconnect-server && node server.js`
6. Inicia Flask (backend + frontend):
   - `python start.py`

**Portas utilizadas:**
- Flask: 5000
- WPPConnect: 3001
- Evolution API: 8080 (se configurado)
- PostgreSQL: 5434

---

### 9.2. **`start.py`**
Script Python de inicialização do Flask.

**O que faz:**
1. Verifica PostgreSQL (`verificar_postgres()`)
2. Inicializa banco de dados (`inicializar_banco_e_dados()`):
   - Cria banco `nexus_crm` se não existir
   - Executa `database/schema.sql`
   - Popula dados iniciais (`database/seed_data.py`)
3. Verifica WPPConnect Server (`verificar_wppconnect()`)
4. Inicia aplicação Flask (`backend/app.py`)

---

### 9.3. **`iniciar_menu.bat`**
Menu interativo para escolher o que iniciar.

**Opções:**
1. Iniciar tudo (Flask + WPPConnect)
2. Apenas Flask
3. Apenas WPPConnect
4. Apenas Evolution API
5. Executar setup

---

### 9.4. **`parar.bat`**
Para todos os servidores.

**O que faz:**
- `taskkill /F /IM python.exe` (Flask)
- `taskkill /F /IM node.exe` (WPPConnect/Evolution)

---

### 9.5. **`RESTART_SERVIDOR.bat`**
Reinicia o servidor Flask.

**O que faz:**
1. Executa `parar.bat`
2. Aguarda 2 segundos
3. Executa `iniciar.bat`

---

### 9.6. **`setup_canopus.bat`**
Instala dependências da automação Canopus.

**O que faz:**
1. Ativa `venv`
2. Instala: `playwright`, `pandas`, `openpyxl`, `cryptography`, etc.
3. Executa: `playwright install` (baixa navegadores)

---

### 9.7. **`instalar_canopus.bat`**
Instalação completa da automação Canopus.

**O que faz:**
1. Executa `setup_canopus.bat`
2. Cria tabelas no banco:
   - `automation/canopus/criar_tabelas_automacao.sql`

---

### 9.8. **`wppconnect-server/start.bat`**
Inicia apenas o WPPConnect Server.

```batch
npm start
```

---

### 9.9. **`wppconnect-server/install.bat`**
Instala dependências do WPPConnect.

```batch
npm install --legacy-peer-deps --force
```

---

### 9.10. **`wppconnect-server/limpar-sessao.bat`**
Limpa sessões armazenadas do WPPConnect.

**O que faz:**
- Deleta pasta `tokens/` (sessões salvas)

---

## 10. PROBLEMAS CONHECIDOS / TODOs

### 10.1. Comentários TODO/FIXME encontrados no código:

**Em `backend/routes/auth.py`:**
```python
# TODO: Implementar refresh token
# TODO: Adicionar rate limiting para evitar brute force
```

**Em `backend/services/automation_service.py`:**
```python
# FIXME: Melhorar tratamento de erro quando WhatsApp desconecta durante envio
# TODO: Adicionar retry automático em caso de falha
```

**Em `automation/canopus/canopus_automation.py`:**
```python
# TODO: Implementar detecção de CAPTCHA
# FIXME: Timeout muito curto em redes lentas
# TODO: Adicionar log detalhado de cada etapa
```

**Em `backend/services/whatsapp_evolution.py`:**
```python
# TODO: Implementar webhook para receber eventos da Evolution API
# FIXME: Não está tratando erro 429 (rate limit)
```

**Em `frontend/templates/crm-cliente/disparos.html`:**
```html
<!-- TODO: Adicionar barra de progresso em tempo real -->
<!-- FIXME: Não está atualizando status após disparo -->
```

---

### 10.2. Código comentado importante:

**Em `backend/routes/whatsapp.py` (linha 45):**
```python
# Código antigo usando Twilio (descontinuado)
# from services.whatsapp_twilio import TwilioService
# twilio_service = TwilioService()
```

**Em `automation/canopus/orquestrador.py` (linha 120):**
```python
# Versão antiga de download (sem tratamento de duplicatas)
# for cliente in clientes:
#     download_pdf(cliente.cpf)
```

---

### 10.3. Bugs conhecidos:

1. **WhatsApp desconecta durante disparo em massa:**
   - **Arquivo:** `backend/services/automation_service.py`
   - **Descrição:** Se o disparo demorar muito, a sessão WhatsApp pode expirar
   - **Workaround:** Verificar status antes de cada envio

2. **Normalização de WhatsApp com 13 dígitos:**
   - **Arquivo:** `backend/scripts/normalizar_whatsapp_*.py`
   - **Descrição:** Números com 13 dígitos não são normalizados corretamente
   - **Solução:** Executar `backend/scripts/ajustar_numeros_13_digitos.py`

3. **Evolution API retorna QR Code expirado:**
   - **Arquivo:** `backend/services/whatsapp_evolution.py`
   - **Descrição:** QR Code expira após 60 segundos, mas frontend não atualiza
   - **Workaround:** Clicar novamente em "Conectar"

4. **Playwright não encontra navegadores:**
   - **Arquivo:** `automation/canopus/canopus_automation.py`
   - **Descrição:** Navegadores não instalados
   - **Solução:** Executar `playwright install`

---

## 11. DIAGRAMA DE ARQUITETURA

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USUÁRIO (Navegador)                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ HTTP/HTTPS
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                       FRONTEND (HTML/CSS/JS)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Landing Page │  │ Login Cliente│  │ Dashboard CRM│             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Disparos     │  │ Monitoramento│  │ Automação    │             │
│  │              │  │              │  │ Canopus      │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ REST API (JSON)
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                    BACKEND (Flask - Python)                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  ROUTES (Blueprints)                                       │    │
│  │  • auth.py          • crm.py             • automation.py   │    │
│  │  • whatsapp.py      • portal_consorcio.py • webhook.py     │    │
│  └────────────────────────────┬───────────────────────────────┘    │
│                               │                                     │
│  ┌────────────────────────────▼───────────────────────────────┐    │
│  │  SERVICES (Lógica de Negócio)                              │    │
│  │  • automation_service.py     • boleto_generator.py         │    │
│  │  • whatsapp_service.py       • automation_scheduler.py     │    │
│  │  • mensagens_personalizadas.py                             │    │
│  └────────────────────────────┬───────────────────────────────┘    │
│                               │                                     │
│  ┌────────────────────────────▼───────────────────────────────┐    │
│  │  MODELS (ORM / Database)                                   │    │
│  │  • database.py  • usuario.py  • boleto.py  • cliente.py    │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────┬────────────────┬────────────────┬───────────────────┘
                │                │                │
        ┌───────▼──────┐  ┌──────▼─────┐  ┌──────▼──────┐
        │  PostgreSQL  │  │  Evolution │  │ WPPConnect  │
        │              │  │  API       │  │ Server      │
        │  Porta: 5434 │  │  Porta:8080│  │  Porta: 3001│
        └──────────────┘  └────────────┘  └─────────────┘
                │                │                │
                │                │                │
        ┌───────▼──────┐  ┌──────▼─────┐  ┌──────▼──────┐
        │   Tabelas:   │  │  WhatsApp  │  │  WhatsApp   │
        │  • usuarios  │  │  Multi-    │  │  Puppeteer  │
        │  • boletos   │  │  Instância │  │             │
        │  • clientes  │  │  (Baileys) │  │             │
        └──────────────┘  └────────────┘  └─────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              AUTOMAÇÃO CANOPUS (Playwright - Python)                │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  orquestrador.py                                           │    │
│  │    ├── excel_importer.py (Importa clientes Excel)         │    │
│  │    ├── canopus_automation.py (Web scraping)               │    │
│  │    └── db_config.py (Conexão PostgreSQL)                  │    │
│  └────────────────────────────┬───────────────────────────────┘    │
│                               │                                     │
│                       ┌───────▼──────┐                              │
│                       │  Sistema     │                              │
│                       │  Canopus     │                              │
│                       │  (Externo)   │                              │
│                       └──────────────┘                              │
│                               │                                     │
│                       ┌───────▼──────┐                              │
│                       │  Downloads:  │                              │
│                       │  PDFs Boletos│                              │
│                       └──────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 12. VARIÁVEIS DE AMBIENTE (.env)

```env
# ============================================
# CONFIGURAÇÕES DO FLASK
# ============================================
FLASK_SECRET_KEY=nexus-crm-secret-key-2024
FLASK_ENV=development
FLASK_PORT=5000

# ============================================
# CONFIGURAÇÕES DO POSTGRESQL
# ============================================
DB_HOST=localhost
DB_PORT=5434
DB_NAME=nexus_crm
DB_USER=postgres
DB_PASSWORD=nexus2025

# ============================================
# CONFIGURAÇÕES DE AUTOMAÇÃO
# ============================================
AUTOMATION_ENABLED=true
DISPARO_INTERVAL_SECONDS=5

# ============================================
# DIRETÓRIOS
# ============================================
BOLETO_DIR=boletos
WHATSAPP_SESSION_DIR=whatsapp_sessions

# ============================================
# EVOLUTION API (Opcional)
# ============================================
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-chave-aqui

# ============================================
# WPPCONNECT (Opcional)
# ============================================
WPPCONNECT_URL=http://localhost:3001
WPPCONNECT_SECRET_KEY=sua-chave-aqui
```

---

## 13. COMANDOS ÚTEIS

### 13.1. Inicialização

```bash
# Iniciar sistema completo (Windows)
iniciar.bat

# Iniciar apenas Flask
python start.py

# Iniciar apenas WPPConnect
cd wppconnect-server
npm start

# Iniciar apenas Evolution API
cd evolution-api-standalone
npm start
```

---

### 13.2. Banco de Dados

```bash
# Conectar ao PostgreSQL
psql -h localhost -p 5434 -U postgres -d nexus_crm

# Executar schema
psql -h localhost -p 5434 -U postgres -d nexus_crm -f database/schema.sql

# Backup do banco
python database/backup.py

# Popular com dados fake
python database/seed_data.py
```

---

### 13.3. Automação Canopus

```bash
# Instalar dependências Canopus
setup_canopus.bat

# Executar orquestrador manualmente
cd automation/canopus
python orquestrador.py

# Importar clientes de Excel
python excel_importer.py planilha.xlsx

# Testar credenciais do consultor
python testar_credencial.py
```

---

### 13.4. WhatsApp

```bash
# Limpar sessões WPPConnect
cd wppconnect-server
limpar-sessao.bat

# Verificar status Evolution API
curl http://localhost:8080/instance/status/nexus_instance_1
```

---

### 13.5. Debug

```bash
# Verificar boletos no banco
python backend/scripts/verificar_boletos.py

# Diagnosticar disparos
python backend/scripts/diagnosticar_disparos.py

# Testar fluxo completo
python backend/scripts/testar_fluxo_disparo.py

# Normalizar WhatsApp
python backend/scripts/normalizar_todos_whatsapp.py
```

---

## 14. CONCLUSÃO

Este documento fornece um mapeamento completo do sistema **Nexus CRM**, incluindo:

- Estrutura de pastas e arquivos
- Todas as rotas da API REST
- Schema completo do banco de dados PostgreSQL
- Descrição de todos os serviços e integrações
- Fluxos principais do sistema (login, disparo, automação)
- Configurações e variáveis de ambiente
- Scripts de inicialização
- Problemas conhecidos e TODOs

**Para dúvidas ou atualizações, consulte:**
- Código-fonte em `D:\Nexus\`
- Logs do sistema em `D:\Nexus\logs\`
- Documentação adicional em `README.md`

---

**Gerado em:** 2025-11-27
**Versão:** 1.0
**Sistema:** Nexus CRM - "Aqui seu tempo vale ouro"
