# 🚀 NEXUS CRM + PORTAL CONSÓRCIO

**Aqui seu tempo vale ouro ⏱️**

Sistema completo de CRM com automação de boletos via WhatsApp + Portal de Consórcio integrado. Desenvolvido em Python (Flask) com PostgreSQL e interface web moderna.

## 🎉 NOVIDADES

### ✅ WPPCONNECT INTEGRADO (Novo!)
**WhatsApp estável e confiável substituindo Baileys!**
- ✅ Servidor Node.js dedicado (porta 3001)
- ✅ Inicialização automática via `iniciar.bat`
- ✅ Conexão por QR Code simples
- ✅ Envio de mensagens e PDFs
- ✅ Anti-bloqueio configurável
- ✅ Envio em massa otimizado

### ✅ PORTAL CONSÓRCIO
**Sistema completo de gestão de consórcios!**
- Login independente para administração
- CRUD completo de clientes finais (5 já cadastrados!)
- Geração de boletos PDF profissionais (individual e lote)
- Integração automática com CRM Cliente
- Links diretos na landing page

---

## ⚡ INICIAR RAPIDAMENTE (TUDO DE UMA VEZ)

### Windows (Recomendado):
```bash
iniciar.bat
```
**Este comando inicia automaticamente:**
- ✅ Ambiente virtual Python
- ✅ Flask (porta 5000)
- ✅ WPPConnect Server para WhatsApp (porta 3001)
- ✅ Abre navegador automaticamente

### Para PARAR tudo:
```bash
parar.bat
```

### PowerShell:
```bash
.\iniciar.ps1
```

### Linux/Mac:
```bash
source venv/bin/activate
python start.py
```

**Acessos:**
- **Landing Page:** http://localhost:5000/
- **Portal Consórcio:** http://localhost:5000/portal-consorcio/login (admin@portal.com / admin123)
- **CRM Cliente:** http://localhost:5000/login-cliente (cliente@teste.com / senha123)

---

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API Endpoints](#api-endpoints)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

---

## 🎯 Sobre o Projeto

O **Nexus CRM** é um sistema completo de gerenciamento de clientes e automação de boletos. Ele permite que empresas:

- Cadastrem seus clientes
- Gerem boletos em PDF automaticamente
- Conectem ao WhatsApp via QR Code
- Enviem boletos automaticamente via WhatsApp
- Monitorem disparos e estatísticas em tempo real

O sistema implementa as **33 etapas do manual oficial de automação**, incluindo:
- Geração automática de boletos
- Organização em pastas
- Disparo com mensagem anti-bloqueio
- Notificações automáticas
- Dashboard com gráficos e relatórios

---

## ✨ Funcionalidades

### 🔐 Autenticação
- Login para clientes e administradores
- Sessões seguras com bcrypt
- Proteção de rotas

### 👥 Gestão de Clientes
- Cadastro de clientes finais
- Validação de CPF/CNPJ
- Busca e filtros avançados
- Edição e exclusão

### 📄 Boletos
- Geração automática de PDFs profissionais
- Boletos personalizados com dados da empresa
- Organização automática em pastas
- Registro completo no banco de dados

### 📱 Integração WhatsApp
- Conexão via QR Code
- Envio de mensagens de texto
- Envio de PDFs/documentos
- Disparo em massa com anti-bloqueio
- Intervalo configurável entre envios

### 🤖 Automação Completa
- Processamento de todos os clientes
- Geração em lote de boletos
- Disparo automático com anti-bloqueio
- Notificações ao empresário (início e fim)
- Histórico de automações

### 📊 Dashboard
- Estatísticas em tempo real
- Gráficos de envios
- Monitoramento de status
- Últimos boletos gerados

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.10+**
- **Flask 3.0** - Framework web
- **PostgreSQL** - Banco de dados
- **psycopg2** - Driver PostgreSQL
- **bcrypt** - Criptografia de senhas
- **ReportLab** - Geração de PDFs
- **Flask-Session** - Gerenciamento de sessões
- **Flask-CORS** - Cross-Origin Resource Sharing

### Frontend
- **HTML5**
- **CSS3** (Design moderno responsivo)
- **JavaScript** (Vanilla)
- **Google Fonts** (Poppins)

### Automação
- **Selenium** - Web scraping
- **BeautifulSoup4** - Parse HTML
- Sistema de filas para disparos

---

## 📦 Requisitos

### Sistema Operacional
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS 10.15+

### Software Necessário
1. **Python 3.10 ou superior**
   - Download: https://www.python.org/downloads/

2. **PostgreSQL 12 ou superior**
   - Windows: https://www.postgresql.org/download/windows/
   - Linux: `sudo apt install postgresql postgresql-contrib`
   - macOS: `brew install postgresql`

3. **Git** (opcional, para clonar o projeto)
   - Download: https://git-scm.com/downloads

---

## 🚀 Instalação

### Passo 1: Clonar/Baixar o Projeto

```bash
# Opção 1: Clonar via Git
git clone https://github.com/seu-usuario/nexus-crm.git
cd nexus-crm

# Opção 2: Extrair o ZIP
# Extraia o arquivo ZIP em D:\Nexus
cd D:\Nexus
```

### Passo 2: Configurar o PostgreSQL

1. Instale o PostgreSQL
2. Inicie o serviço PostgreSQL
3. Crie o usuário postgres (se não existir):

```sql
-- Acesse o psql como administrador
CREATE USER postgres WITH PASSWORD 'postgres';
ALTER USER postgres WITH SUPERUSER;
```

### Passo 3: Configurar Variáveis de Ambiente

Edite o arquivo `.env` na raiz do projeto:

```env
# Configurações do Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nexus_crm
DB_USER=postgres
DB_PASSWORD=SUA_SENHA_AQUI  # Altere para sua senha

# Configurações da Aplicação
FLASK_SECRET_KEY=nexus-crm-secret-key-2024
FLASK_ENV=development
FLASK_PORT=5000
```

### Passo 4: Instalar Dependências Python

```bash
# Navegue até a pasta do projeto
cd D:\Nexus

# Crie um ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instale as dependências
pip install -r backend/requirements.txt
```

### Passo 5: Inicializar o Banco de Dados

```bash
# Execute o script de inicialização do banco
python database/init_db.py

# Popule com dados fake para testes (opcional)
python database/seed_data.py
```

### Passo 6: Iniciar o Sistema

```bash
# Inicie o servidor Flask
python start.py
```

O sistema estará disponível em: **http://localhost:5000**

---

## 📖 Uso

### Primeiro Acesso

1. Acesse http://localhost:5000
2. Clique em "Entrar como Cliente" ou "Acesso Admin"

### Usuários Padrão (após executar seed_data.py)

**Clientes:**
- Email: `empresa1@nexus.com` / Senha: `empresa123`
- Email: `empresa2@nexus.com` / Senha: `empresa223`
- Email: `empresa3@nexus.com` / Senha: `empresa323`

**Administrador:**
- Email: `admin@nexus.com` / Senha: `admin123`

### Fluxo de Uso Típico

1. **Login**: Faça login com suas credenciais
2. **Cadastrar Clientes**: Vá em "Clientes" e cadastre seus clientes finais
3. **Conectar WhatsApp**: Vá em "WhatsApp" e escaneie o QR Code
4. **Gerar Boletos**: No Dashboard ou em "Disparos", clique em "Gerar Boletos"
5. **Enviar Boletos**: Execute a "Automação Completa" para enviar via WhatsApp
6. **Monitorar**: Acompanhe estatísticas no Dashboard

---

## 📂 Estrutura do Projeto

```
D:\Nexus\
├── backend/
│   ├── app.py                  # Aplicação Flask principal
│   ├── config.py               # Configurações do sistema
│   ├── requirements.txt        # Dependências Python
│   ├── models/                 # Modelos do banco de dados
│   │   ├── database.py         # Conexão PostgreSQL
│   │   ├── usuario.py          # Modelo de usuário
│   │   ├── cliente.py          # Modelos de clientes
│   │   └── boleto.py           # Modelos de boletos
│   ├── routes/                 # Rotas da API
│   │   ├── auth.py             # Autenticação
│   │   ├── crm.py              # CRM endpoints
│   │   ├── whatsapp.py         # WhatsApp endpoints
│   │   └── automation.py       # Automação endpoints
│   └── services/               # Serviços do sistema
│       ├── pdf_generator.py    # Geração de PDFs
│       ├── whatsapp_service.py # Serviço WhatsApp
│       ├── webscraping.py      # Web scraping
│       └── automation_service.py # Automação completa
├── frontend/
│   ├── static/
│   │   ├── css/                # Estilos CSS
│   │   └── js/                 # Scripts JavaScript
│   └── templates/              # Templates HTML
│       ├── landing.html        # Página inicial
│       ├── login-cliente.html  # Login cliente
│       ├── login-admin.html    # Login admin
│       ├── crm-cliente/        # Páginas do CRM
│       └── crm-admin/          # Painel admin
├── database/
│   ├── schema.sql              # Schema do banco
│   ├── init_db.py              # Inicialização
│   └── seed_data.py            # Dados fake
├── automation/                 # Scripts de automação
├── boletos/                    # PDFs gerados (criado automaticamente)
├── .env                        # Variáveis de ambiente
├── .gitignore                  # Git ignore
├── start.py                    # Script de inicialização
└── README.md                   # Este arquivo
```

---

## 🔌 API Endpoints

### Autenticação
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/registrar` - Registrar novo usuário
- `GET /api/auth/verificar-sessao` - Verificar sessão ativa

### CRM
- `GET /api/crm/dashboard` - Dados do dashboard
- `GET /api/crm/clientes` - Listar clientes
- `POST /api/crm/clientes` - Criar cliente
- `PUT /api/crm/clientes/:id` - Atualizar cliente
- `DELETE /api/crm/clientes/:id` - Deletar cliente
- `GET /api/crm/boletos` - Listar boletos
- `GET /api/crm/configuracoes` - Buscar configurações

### WhatsApp
- `GET /api/whatsapp/qr-code` - Gerar QR Code
- `POST /api/whatsapp/conectar` - Conectar WhatsApp
- `POST /api/whatsapp/enviar-mensagem` - Enviar mensagem
- `POST /api/whatsapp/enviar-pdf` - Enviar PDF
- `POST /api/whatsapp/disparo-massa` - Disparo em massa

### Automação
- `POST /api/automation/executar-completa` - Automação completa (etapas 21-33)
- `POST /api/automation/gerar-boletos` - Apenas gerar boletos
- `GET /api/automation/historico` - Histórico de automações

---

## 🔧 Configurações Avançadas

### Alterar Porta do Servidor

Edite o arquivo `.env`:
```env
FLASK_PORT=8080  # Altere para a porta desejada
```

### Configurar Intervalo de Disparos

No CRM, vá em "Configurações" e altere:
- **Intervalo entre disparos** (em segundos)
- **Mensagem anti-bloqueio**
- **Data/hora de disparo automático**

### Habilitar Modo Produção

No `.env`:
```env
FLASK_ENV=production
```

---

## 🐛 Solução de Problemas

### Erro: "PostgreSQL não está acessível"
- Verifique se o PostgreSQL está rodando
- Confirme usuário e senha no `.env`
- Teste conexão: `psql -U postgres -h localhost`

### Erro: "Módulo não encontrado"
- Ative o ambiente virtual: `venv\Scripts\activate`
- Reinstale dependências: `pip install -r backend/requirements.txt`

### Erro: "Porta 5000 já em uso"
- Altere a porta no `.env`
- Ou encerre o processo usando a porta 5000

### Boletos não estão sendo gerados
- Verifique se há clientes cadastrados
- Verifique logs no terminal
- Confira permissões da pasta `boletos/`

---

## 📝 Roadmap

- [ ] Integração real com WhatsApp Web via whatsapp-web.js
- [ ] Gráficos interativos com Chart.js
- [ ] Exportação de relatórios em Excel
- [ ] Sistema de notificações push
- [ ] App mobile (React Native)
- [ ] Integração com gateways de pagamento
- [ ] Multi-idiomas (i18n)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 👨‍💻 Autor

**Sistema CRM Nexus**
- Desenvolvido com ❤️ em Python + Flask
- Aqui seu tempo vale ouro ⏱️

---

## 📞 Suporte

Para suporte e dúvidas:
- 📧 Email: suporte@nexuscrm.com
- 💬 Issues: https://github.com/seu-usuario/nexus-crm/issues
- 📚 Documentação: Veja o arquivo `docs/MANUAL.md`

---

**🎉 Obrigado por usar o Nexus CRM!**

*Sistema de automação que transforma horas de trabalho manual em minutos de eficiência.*
