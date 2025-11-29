# Configuração WhatsApp - WPPConnect Server

## Visão Geral

O Nexus CRM usa **WPPConnect** para integração com WhatsApp. Como o Render.com não permite rodar processos Node.js adicionais junto com o servidor Flask, você precisa hospedar o WPPConnect Server externamente.

## Opção 1: Railway.app (Recomendado)

### 1. Criar Conta no Railway
- Acesse https://railway.app/
- Faça login com GitHub

### 2. Criar Novo Projeto
- Clique em "New Project"
- Selecione "Deploy from GitHub repo"
- Escolha o repositório WPPConnect Server: https://github.com/wppconnect-team/wppconnect-server

### 3. Configurar Variáveis de Ambiente
No Railway, adicione estas variáveis:
```
PORT=3001
SECRET_KEY=CHANGE_HERE_YOUR_SECRET_KEY
HOST=http://localhost
BASE_URL=https://SEU_PROJETO.railway.app
```

### 4. Deploy
- Railway fará deploy automaticamente
- Anote a URL gerada (ex: `https://wppconnect-production.railway.app`)

### 5. Configurar no Render
No painel do Render (seu app Nexus):
- Vá em "Environment"
- Adicione nova variável:
  ```
  WPPCONNECT_URL=https://wppconnect-production.railway.app
  ```
- Clique "Save Changes"
- Faça redeploy do Nexus

## Opção 2: Heroku

### 1. Criar App no Heroku
```bash
heroku create meu-wppconnect-server
```

### 2. Clonar e Deploy
```bash
git clone https://github.com/wppconnect-team/wppconnect-server.git
cd wppconnect-server
git push heroku main
```

### 3. Configurar Variáveis
```bash
heroku config:set SECRET_KEY=CHANGE_HERE_YOUR_SECRET_KEY
heroku config:set BASE_URL=https://meu-wppconnect-server.herokuapp.com
```

### 4. Configurar no Render
```
WPPCONNECT_URL=https://meu-wppconnect-server.herokuapp.com
```

## Opção 3: VPS/Servidor Próprio

### 1. Instalar Node.js
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Clonar WPPConnect Server
```bash
git clone https://github.com/wppconnect-team/wppconnect-server.git
cd wppconnect-server
npm install
```

### 3. Configurar
Edite `.env`:
```
PORT=3001
SECRET_KEY=CHANGE_HERE_YOUR_SECRET_KEY
HOST=http://localhost
BASE_URL=http://SEU_IP_OU_DOMINIO:3001
```

### 4. Iniciar com PM2
```bash
npm install -g pm2
pm2 start npm --name "wppconnect" -- start
pm2 save
pm2 startup
```

### 5. Configurar Firewall
```bash
sudo ufw allow 3001
```

### 6. Configurar no Render
```
WPPCONNECT_URL=http://SEU_IP_OU_DOMINIO:3001
```

## Endpoints do WPPConnect Server

O servidor WPPConnect expõe os seguintes endpoints que o Nexus CRM usa:

### Verificar Servidor
```
GET /
Resposta: { "status": "running" }
```

### Iniciar Sessão
```
POST /start
Resposta: { "success": true, "message": "Session started" }
```

### Obter QR Code
```
GET /qr
Resposta: { "success": true, "qr": "data:image/png;base64,...", "connected": false }
```

### Verificar Status
```
GET /status
Resposta: { "success": true, "connected": true, "phone": "5511999999999" }
```

### Enviar Mensagem
```
POST /send-text
Body: { "phone": "5511999999999", "message": "Olá!" }
Resposta: { "success": true, "messageId": "..." }
```

### Enviar Arquivo
```
POST /send-file
Body: { "phone": "5511999999999", "filePath": "/path/to/file.pdf", "caption": "Segue anexo" }
Resposta: { "success": true, "messageId": "..." }
```

### Desconectar
```
POST /logout
Resposta: { "success": true, "message": "Logged out" }
```

## Testando a Conexão

### 1. Verificar se o servidor está rodando
```bash
curl https://SEU_WPPCONNECT_URL/
```

Deve retornar:
```json
{ "status": "running" }
```

### 2. No Nexus CRM
1. Acesse https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp
2. Clique em "Conectar WhatsApp"
3. O QR Code deve aparecer
4. Escaneie com WhatsApp do celular
5. Após conectar, o status mudará para "Conectado"

## Troubleshooting

### Erro: "WPPConnect Server não está rodando"
- Verifique se o servidor WPPConnect está online
- Teste o endpoint `/` com curl
- Verifique se a variável `WPPCONNECT_URL` está correta no Render

### QR Code não aparece
- Aguarde alguns segundos após clicar em "Conectar"
- Verifique os logs do WPPConnect Server
- Tente desconectar e conectar novamente

### Erro: "Timeout ao conectar"
- Verifique se há firewall bloqueando a conexão
- Certifique-se de que a URL está acessível publicamente
- Aumente o timeout nas configurações se necessário

### Conexão cai frequentemente
- Use um servidor dedicado em vez de free tier
- Considere Railway ou VPS ao invés de Heroku free
- Configure health checks e auto-restart (PM2)

## Segurança

### Autenticação
O WPPConnect Server usa `SECRET_KEY` para autenticação. Configure uma chave forte:
```bash
SECRET_KEY=$(openssl rand -hex 32)
```


### HTTPS
Em produção, SEMPRE use HTTPS:
- Railway e Heroku fornecem HTTPS automaticamente
- Em VPS, use nginx + Let's Encrypt

### Whitelist de IPs (Opcional)
No servidor WPPConnect, configure whitelist de IPs permitidos:
```javascript
// No arquivo config.js do WPPConnect
module.exports = {
  allowedIPs: ['IP_DO_RENDER_NEXUS']
}
```

## Custos Estimados

### Railway
- Free tier: $5 de crédito/mês (suficiente para testes)
- Hobby: $5/mês (recomendado para produção)

### Heroku
- Free tier: DESCONTINUADO
- Hobby: $7/mês

### VPS (DigitalOcean, Vultr, etc)
- 1GB RAM: $5-6/mês
- 2GB RAM: $10-12/mês (recomendado)

## Monitoramento

### Logs no Railway
```
railway logs
```

### Logs no Heroku
```
heroku logs --tail -a meu-wppconnect-server
```

### Logs com PM2
```
pm2 logs wppconnect
```

## Backup da Sessão

Para não perder a sessão do WhatsApp ao reiniciar:

1. Configure volume persistente (Railway/Render)
2. Ou faça backup da pasta `tokens/` do WPPConnect Server
3. Em VPS, a pasta já é persistente por padrão

## Suporte

- Documentação WPPConnect: https://wppconnect.io/
- GitHub WPPConnect: https://github.com/wppconnect-team/wppconnect-server
- Issues Nexus CRM: https://github.com/presleybr/nexus/issues
