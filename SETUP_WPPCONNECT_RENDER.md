# Como Configurar WPPConnect Server no Render.com

## Visão Geral

Vamos adicionar o WPPConnect Server como um **segundo serviço** no mesmo projeto Render do Nexus CRM. Isso permite que os dois serviços rodem no mesmo projeto e se comuniquem facilmente.

## Estrutura do Projeto

```
nexus/
├── backend/           # Servidor Flask (já existe)
├── frontend/          # Templates HTML (já existe)
├── wppconnect/        # NOVO: Servidor WPPConnect
│   ├── package.json
│   ├── server.js
│   └── .env
└── render.yaml        # NOVO: Configuração multi-service
```

## Passo 1: Adicionar WPPConnect ao Repositório

### 1.1 Criar pasta wppconnect

```bash
cd D:\Nexus
mkdir wppconnect
cd wppconnect
```

### 1.2 Inicializar projeto Node.js

```bash
npm init -y
npm install @wppconnect-team/wppconnect-server
```

### 1.3 Criar servidor básico

Crie `wppconnect/server.js`:

```javascript
const wppconnect = require('@wppconnect-team/wppconnect-server');

// Configuração
const serverOptions = {
  secretKey: process.env.SECRET_KEY || 'CHANGE_HERE_YOUR_SECRET_KEY',
  host: process.env.HOST || 'http://localhost',
  port: process.env.PORT || 3001,
  deviceName: 'Nexus CRM',
  poweredBy: 'Nexus CRM - WPPConnect',
  startAllSession: true,
  tokenStoreType: 'file',
  maxListeners: 15
};

wppconnect.create(serverOptions)
  .then((server) => console.log('✅ WPPConnect Server iniciado!'))
  .catch((error) => console.error('❌ Erro ao iniciar WPPConnect:', error));
```

### 1.4 Atualizar package.json

Edite `wppconnect/package.json`:

```json
{
  "name": "nexus-wppconnect",
  "version": "1.0.0",
  "description": "WPPConnect Server para Nexus CRM",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "@wppconnect-team/wppconnect-server": "^2.0.0"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=8.0.0"
  }
}
```

### 1.5 Criar .gitignore para Node

Crie `wppconnect/.gitignore`:

```
node_modules/
tokens/
.env
*.log
```

## Passo 2: Configurar Render com Múltiplos Serviços

### 2.1 Criar render.yaml na raiz do projeto

Crie `D:\Nexus\render.yaml`:

```yaml
services:
  # Serviço 1: Backend Flask (Nexus CRM)
  - type: web
    name: nexus-crm-backend
    env: python
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: python backend/app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: nexus-postgres
          property: connectionString
      - key: FLASK_ENV
        value: production
      - key: WPPCONNECT_URL
        value: https://nexus-wppconnect.onrender.com
      - key: FLASK_SECRET_KEY
        generateValue: true

  # Serviço 2: WPPConnect Server (Node.js)
  - type: web
    name: nexus-wppconnect
    env: node
    region: oregon
    buildCommand: cd wppconnect && npm install
    startCommand: cd wppconnect && npm start
    envVars:
      - key: PORT
        value: 10000
      - key: SECRET_KEY
        generateValue: true
      - key: HOST
        value: https://nexus-wppconnect.onrender.com
      - key: BASE_URL
        value: https://nexus-wppconnect.onrender.com

# Banco de dados (compartilhado)
databases:
  - name: nexus-postgres
    databaseName: nexus_crm
    user: nexus_user
```

## Passo 3: Configurar Manualmente no Render (Alternativa)

Se preferir criar manualmente no dashboard do Render:

### 3.1 Criar Segundo Web Service

1. No dashboard do Render, vá para seu projeto Nexus
2. Clique em **"New +"** → **"Web Service"**
3. Conecte ao mesmo repositório GitHub
4. Configure:
   - **Name**: `nexus-wppconnect`
   - **Region**: Oregon (mesma do backend principal)
   - **Branch**: `main`
   - **Root Directory**: `wppconnect`
   - **Environment**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`

### 3.2 Configurar Variáveis de Ambiente

No painel do serviço `nexus-wppconnect`, adicione:

```
PORT=10000
SECRET_KEY=SEU_SECRET_KEY_AQUI
HOST=https://nexus-wppconnect.onrender.com
BASE_URL=https://nexus-wppconnect.onrender.com
```

### 3.3 Atualizar Backend Flask

No painel do serviço `nexus-crm-backend`, atualize:

```
WPPCONNECT_URL=https://nexus-wppconnect.onrender.com
```

## Passo 4: Fazer Deploy

### 4.1 Commit e Push

```bash
cd D:\Nexus
git add wppconnect/
git add render.yaml
git commit -m "feat: Add WPPConnect Server to Render project"
git push origin main
```

### 4.2 Deploy Automático

O Render detectará o `render.yaml` e criará automaticamente:
- ✅ Serviço `nexus-crm-backend` (Flask)
- ✅ Serviço `nexus-wppconnect` (Node.js)
- ✅ Banco de dados PostgreSQL (compartilhado)

### 4.3 Aguardar Build

- Backend Flask: ~3-5 minutos
- WPPConnect: ~2-3 minutos

## Passo 5: Testar a Integração

### 5.1 Verificar WPPConnect está online

```bash
curl https://nexus-wppconnect.onrender.com/api/sessions/status
```

### 5.2 Testar no Nexus CRM

1. Acesse https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp
2. Clique em "Conectar WhatsApp"
3. O QR Code deve aparecer
4. Escaneie com WhatsApp
5. Após conectar, teste envio de mensagem

## Arquitetura Final

```
┌─────────────────────────────────────────────┐
│         Render.com - Projeto Nexus          │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │   nexus-crm-backend (Flask)         │   │
│  │   https://nexus-crm-backend...      │   │
│  │   - Routes API                      │   │
│  │   - Business Logic                  │   │
│  │   - Templates                       │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│                 │ HTTP Requests             │
│                 │ WPPCONNECT_URL            │
│                 ▼                           │
│  ┌─────────────────────────────────────┐   │
│  │   nexus-wppconnect (Node.js)        │   │
│  │   https://nexus-wppconnect...       │   │
│  │   - WhatsApp Web Integration        │   │
│  │   - QR Code Generation              │   │
│  │   - Message Sending                 │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │   PostgreSQL Database               │   │
│  │   - Shared by both services         │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Vantagens desta Abordagem

✅ **Tudo no mesmo projeto**: Fácil de gerenciar
✅ **Rede interna**: Serviços se comunicam rapidamente
✅ **Mesmo billing**: Um só lugar para pagar
✅ **Logs centralizados**: Debugar fica mais fácil
✅ **Auto-deploy**: Push no GitHub → deploy automático

## Custos no Render

### Free Tier
- ⚠️ Free tier **NÃO suporta múltiplos serviços**
- Você precisa de pelo menos **Starter Plan**

### Starter Plan ($7/mês por serviço)
- nexus-crm-backend: $7/mês
- nexus-wppconnect: $7/mês
- **Total: $14/mês**

### Vantagens do Starter
- 750 horas/mês (suficiente para rodar 24/7)
- Auto-scaling
- Persistent disk (sessões WhatsApp mantidas)
- SSL gratuito

## Alternativa: Free Tier Dividido

Se quiser economizar, pode manter um serviço free e pagar outro:

1. **nexus-crm-backend** → Render Starter ($7/mês)
2. **nexus-wppconnect** → Railway Free ($5 crédito/mês)

Configure no backend:
```
WPPCONNECT_URL=https://seu-projeto.railway.app
```

## Troubleshooting

### Erro: "Root directory not found"

No Render, ao criar o serviço WPPConnect, defina:
- Root Directory: `wppconnect`

### Erro: "Module not found"

Verifique que o `buildCommand` tem `cd wppconnect &&`:
```
Build Command: cd wppconnect && npm install
Start Command: cd wppconnect && npm start
```

### Serviços não se comunicam

Verifique que a URL está correta:
```bash
# No backend Flask
echo $WPPCONNECT_URL
# Deve mostrar: https://nexus-wppconnect.onrender.com
```

### WhatsApp desconecta frequentemente

Configure health checks no `render.yaml`:

```yaml
services:
  - type: web
    name: nexus-wppconnect
    healthCheckPath: /api/sessions/status
    autoDeploy: true
```

## Próximos Passos

1. ✅ Criar pasta `wppconnect/` com os arquivos
2. ✅ Criar `render.yaml` na raiz
3. ✅ Commit e push
4. ✅ Aguardar deploy
5. ✅ Testar conexão WhatsApp

## Monitoramento

### Logs do WPPConnect
```bash
# No dashboard do Render
https://dashboard.render.com/web/[seu-service-id]/logs
```

### Verificar Status
```bash
curl https://nexus-wppconnect.onrender.com/api/sessions/status
```

### Endpoints Disponíveis

- `GET /api/sessions/status` - Status da sessão
- `POST /api/sessions/start` - Iniciar sessão
- `GET /api/sessions/qrcode` - Obter QR Code
- `POST /api/messages/send` - Enviar mensagem

## Suporte

- Render Docs: https://render.com/docs/yaml-spec
- WPPConnect Docs: https://wppconnect.io/
- Issues Nexus: https://github.com/presleybr/nexus/issues
