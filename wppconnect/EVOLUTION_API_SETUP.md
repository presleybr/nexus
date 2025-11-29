# 🚀 Guia de Deploy da Evolution API no Render.com

## Passo 1: Criar Serviço Evolution API no Render

1. **Acesse:** https://dashboard.render.com/
2. **Clique em:** "New +" → "Web Service"
3. **Configure:**
   - **Repository:** `https://github.com/EvolutionAPI/evolution-api`
   - **Branch:** `main`
   - **Name:** `nexus-evolution-api`
   - **Region:** `Oregon (US West)` ou sua preferência
   - **Build Command:** `npm install`
   - **Start Command:** `npm start`
   - **Instance Type:** `Free`

---

## Passo 2: Configurar Variáveis de Ambiente

No painel do Render, adicione estas variáveis de ambiente:

### Básicas (OBRIGATÓRIAS):

```env
# URL da Evolution API (será a URL do seu serviço Render)
SERVER_URL=https://nexus-evolution-api.onrender.com

# Porta (deixar 8080 ou 10000 para Render)
PORT=10000

# Chave de API (IMPORTANTE: Mude para uma senha forte!)
AUTHENTICATION_API_KEY=sua-chave-secreta-aqui-123456

# Modo de autenticação
AUTHENTICATION_TYPE=apikey
```

### Conexão com PostgreSQL (RECOMENDADO):

```env
# Database (use o mesmo PostgreSQL do Nexus)
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=sua-connection-string-postgresql
DATABASE_CONNECTION_CLIENT_NAME=evolution_api
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=false
DATABASE_SAVE_MESSAGE_UPDATE=false
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
```

### Webhook (OPCIONAL - para receber eventos):

```env
# Webhook Global (seu backend Nexus)
WEBHOOK_GLOBAL_ENABLED=false
WEBHOOK_GLOBAL_URL=https://nexus-crm-backend-6jxi.onrender.com/webhook/whatsapp
WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=true
```

### Storage (Sessões):

```env
# Salvar sessões no PostgreSQL
STORE_MESSAGES=false
STORE_MESSAGE_UP=false
STORE_CONTACTS=true
STORE_CHATS=true
```

### Configurações Adicionais:

```env
# Logs
LOG_LEVEL=ERROR
LOG_COLOR=true
LOG_BAILEYS=error

# QR Code
QRCODE_LIMIT=30
QRCODE_COLOR=#198754

# Limpeza automática
DEL_INSTANCE=false
```

---

## Passo 3: Deploy

1. Clique em **"Create Web Service"**
2. Aguarde o deploy (5-10 minutos)
3. Acesse a URL gerada: `https://nexus-evolution-api.onrender.com`

---

## Passo 4: Verificar se está funcionando

Teste a API:

```bash
curl https://nexus-evolution-api.onrender.com
```

Resposta esperada:
```json
{
  "status": 200,
  "message": "Welcome to the Evolution API"
}
```

---

## Passo 5: Criar uma Instância WhatsApp

### Via cURL:

```bash
curl -X POST https://nexus-evolution-api.onrender.com/instance/create \
  -H "apikey: sua-chave-secreta-aqui-123456" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "nexus-crm",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

### Via Postman/Insomnia:

**POST** `https://nexus-evolution-api.onrender.com/instance/create`

**Headers:**
```
apikey: sua-chave-secreta-aqui-123456
Content-Type: application/json
```

**Body:**
```json
{
  "instanceName": "nexus-crm",
  "qrcode": true,
  "integration": "WHATSAPP-BAILEYS"
}
```

---

## Passo 6: Conectar WhatsApp (Obter QR Code)

```bash
curl https://nexus-evolution-api.onrender.com/instance/connect/nexus-crm \
  -H "apikey: sua-chave-secreta-aqui-123456"
```

Resposta:
```json
{
  "instance": {
    "instanceName": "nexus-crm",
    "status": "open"
  },
  "qrcode": {
    "code": "data:image/png;base64,iVBORw0KG...",
    "pairingCode": null
  }
}
```

Use o campo `qrcode.code` para exibir o QR Code no frontend!

---

## Passo 7: Configurar Backend Nexus

No seu backend Nexus (`wppconnect/server.js`), adicione estas variáveis:

```env
# Evolution API
EVOLUTION_API_URL=https://nexus-evolution-api.onrender.com
EVOLUTION_API_KEY=sua-chave-secreta-aqui-123456
EVOLUTION_INSTANCE_NAME=nexus-crm
```

---

## 📚 Documentação da API

### Endpoints Principais:

#### 1. Criar Instância
```
POST /instance/create
```

#### 2. Conectar (Obter QR Code)
```
GET /instance/connect/{instanceName}
```

#### 3. Status da Conexão
```
GET /instance/connectionState/{instanceName}
```

#### 4. Enviar Mensagem de Texto
```
POST /message/sendText/{instanceName}
Body: { "number": "5511999999999", "text": "Olá!" }
```

#### 5. Enviar Arquivo
```
POST /message/sendMedia/{instanceName}
Body: { "number": "5511999999999", "mediatype": "document", "media": "https://...", "fileName": "boleto.pdf" }
```

#### 6. Logout
```
DELETE /instance/logout/{instanceName}
```

### Documentação completa:
https://doc.evolution-api.com/

---

## 🔧 Troubleshooting

### Erro: "Instance not found"
- Crie a instância primeiro com `/instance/create`

### Erro: "Unauthorized"
- Verifique se o `apikey` está correto no header

### QR Code não aparece
- Verifique se `qrcode: true` foi enviado ao criar a instância
- Aguarde alguns segundos e tente novamente

### Desconecta após algum tempo
- Verifique se `DATABASE_ENABLED=true` está configurado
- Confirme que a connection string do PostgreSQL está correta

---

## ✅ Próximos Passos

Após configurar a Evolution API:

1. Execute `npm install` no diretório `wppconnect/`
2. Configure as variáveis de ambiente no Render do backend Nexus
3. Faça deploy do novo backend
4. Teste a integração!

---

## 📞 Suporte

- Documentação oficial: https://doc.evolution-api.com/
- GitHub: https://github.com/EvolutionAPI/evolution-api
- Discord: https://evolution-api.com/discord
