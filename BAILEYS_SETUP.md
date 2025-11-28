# WhatsApp Baileys - Nexus CRM

## ✅ Sistema Configurado com Baileys

O Nexus CRM está configurado para usar **Baileys** como provedor WhatsApp, permitindo conectar qualquer número via QR Code diretamente pelo frontend.

---

## Por que Baileys?

✅ **QR Code** - Conecta qualquer número WhatsApp escaneando QR Code
✅ **Flexibilidade** - Cliente pode usar seu próprio número
✅ **Grátis** - Sem custos de API
✅ **Local** - Dados ficam no servidor, mais privacidade
✅ **Controle Total** - Gerenciamento completo pelo CRM

---

## Arquitetura do Sistema

```
Frontend (CRM Cliente)
    ↓
Flask API (Python)
    ↓
whatsapp_baileys.py (serviço)
    ↓
HTTP Requests
    ↓
Servidor Baileys (Node.js - porta 3000)
    ↓
WhatsApp Web Protocol
```

---

## Arquivos Principais

### 1. Servidor Node.js
📁 `whatsapp-baileys/server.js` - Servidor Baileys com Express

**Características:**
- ES Modules
- fetchLatestBaileysVersion (sempre atualizado)
- Limite de 3 tentativas de conexão
- Sem reconexão automática infinita
- Tratamento específico para erro 405

### 2. Serviço Python
📁 `backend/services/whatsapp_baileys.py`

**Métodos:**
- `conectar()` - Inicia conexão via Baileys
- `obter_qr()` - Retorna QR Code em base64
- `verificar_status()` - Status da conexão
- `enviar_mensagem()` - Envia texto
- `enviar_pdf()` - Envia PDF
- `enviar_boleto_completo()` - Mensagem + delay + PDF
- `desconectar()` - Encerra conexão

### 3. Rotas Flask
📁 `backend/routes/whatsapp.py`

**Endpoints:**
- `POST /api/whatsapp/conectar`
- `GET /api/whatsapp/qr`
- `GET /api/whatsapp/status`
- `POST /api/whatsapp/enviar-mensagem`
- `POST /api/whatsapp/enviar-pdf`
- `POST /api/whatsapp/desconectar`
- `POST /api/whatsapp/teste`

### 4. Frontend
📁 `frontend/templates/crm-cliente/whatsapp-conexao.html`

**Recursos:**
- Interface Bootstrap 5
- Polling automático de QR Code (3s)
- Polling de status (5s)
- Seção de teste de envio
- Instruções claras

---

## Como Iniciar

### Passo 1: Instalar Dependências Node.js

```bash
cd whatsapp-baileys
npm install
```

### Passo 2: Iniciar Servidor Baileys

**Opção A - Script Automático:**
```bash
start-whatsapp-baileys.bat
```

**Opção B - Manual:**
```bash
cd whatsapp-baileys
nvm use 20.18.0
npm start
```

### Passo 3: Iniciar Flask

```bash
python start.py
```

Isso irá:
- ✅ Verificar PostgreSQL
- ✅ Inicializar banco
- ✅ Iniciar servidor Baileys automaticamente
- ✅ Iniciar Flask

### Passo 4: Acessar Interface

```
http://localhost:5000/crm/whatsapp
```

---

## Fluxo de Conexão

1. **Cliente acessa** `/crm/whatsapp`
2. **Clica em** "Conectar WhatsApp"
3. **Backend chama** `POST http://localhost:3000/connect`
4. **Baileys gera** QR Code
5. **Frontend exibe** QR Code (polling a cada 3s)
6. **Cliente escaneia** QR com WhatsApp
7. **WhatsApp conecta**
8. **Status atualiza** para "Conectado"
9. **Cliente pode** enviar mensagens

---

## Exemplo de Uso

### Via Interface Web

1. Acesse `http://localhost:5000/crm/whatsapp`
2. Clique em "Conectar WhatsApp"
3. Escaneie QR Code
4. Digite número de teste
5. Clique em "Enviar Teste"

### Via Python

```python
from services.whatsapp_baileys import whatsapp_service

# Conectar
result = whatsapp_service.conectar()

# Enviar mensagem
result = whatsapp_service.enviar_mensagem(
    telefone="67999887766",
    mensagem="Olá do Nexus CRM!"
)

# Enviar PDF
result = whatsapp_service.enviar_pdf(
    telefone="67999887766",
    caminho_pdf="D:/Nexus/boletos/boleto.pdf",
    caption="Seu boleto",
    filename="boleto.pdf"
)

# Enviar boleto completo
result = whatsapp_service.enviar_boleto_completo(
    telefone="67999887766",
    pdf_path="D:/Nexus/boletos/boleto.pdf",
    mensagem_antibloqueio="Olá! Seu boleto chegará em instantes..."
)
```

---

## Solução de Problemas

### Erro 405 - "Muitas tentativas"

**Causa:** WhatsApp bloqueou temporariamente

**Solução:**
```bash
# 1. Pare o servidor Baileys (Ctrl+C)
# 2. Delete sessões antigas
cd whatsapp-baileys
rmdir /s sessions

# 3. Aguarde 30 segundos
# 4. Reinicie
npm start
```

### QR Code não aparece

**Solução:**
1. Verifique se servidor Baileys está rodando:
```bash
curl http://localhost:3000/status
```

2. Verifique logs do servidor Baileys
3. Restart do servidor

### Conexão cai após escanear

**Solução:**
1. Aguarde 1 minuto
2. Delete pasta `sessions`
3. Tente novamente

### Porta 3000 já em uso

**Solução:**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID [PID] /F

# Linux/Mac
lsof -i :3000
kill -9 [PID]
```

---

## Logs

### Servidor Baileys
```
🔄 Tentativa 1/3 - Conectando ao WhatsApp...
📱 QR Code gerado!
✅ Conectado ao WhatsApp!
📱 Número: 5567999887766@s.whatsapp.net
```

### Flask
```
[WHATSAPP] Cliente 1 iniciando conexão
[WHATSAPP] Resposta do Baileys: {'success': True}
[WHATSAPP] Solicitando QR Code
[WHATSAPP] Enviando mensagem para 67999887766
✅ Mensagem enviada com sucesso
```

### Browser Console (F12)
```javascript
[STATUS] {connected: false, status: "disconnected"}
[CONECTAR] Iniciando conexão...
[QR] Solicitando QR Code...
[QR] Resposta: {success: true, qr: "data:image/png..."}
```

---

## Estrutura de Arquivos

```
D:\Nexus\
├── whatsapp-baileys/
│   ├── server.js          ← Servidor Baileys (ES Modules)
│   ├── package.json       ← "type": "module"
│   ├── sessions/          ← Sessões WhatsApp (auto-criada)
│   ├── .gitignore         ← Ignora sessions/
│   └── README.md
│
├── backend/
│   ├── services/
│   │   └── whatsapp_baileys.py  ← Serviço Python
│   └── routes/
│       └── whatsapp.py          ← Rotas Flask
│
├── frontend/
│   └── templates/
│       └── crm-cliente/
│           └── whatsapp-conexao.html  ← Interface QR Code
│
├── start-whatsapp-baileys.bat  ← Script inicialização
└── start.py                     ← Inicia sistema completo
```

---

## Melhores Práticas

### Evitar Bloqueios

1. **Não reconectar múltiplas vezes** - Aguarde 30s entre tentativas
2. **Delay entre mensagens** - Use 3-7s (já implementado)
3. **Mensagens personalizadas** - Evite spam
4. **Limite diário** - Máximo 50-100 mensagens/dia para novos números

### Manutenção

1. **Backup sessões** - Copie pasta `sessions` periodicamente
2. **Atualizar Baileys** - `npm update @whiskeysockets/baileys`
3. **Monitorar logs** - Verifique erros frequentes
4. **Restart semanal** - Evita problemas de memória

### Segurança

1. **Não compartilhe sessões** - Contêm credenciais
2. **Não versione `sessions`** - Já está no .gitignore
3. **Firewall** - Limite acesso à porta 3000
4. **HTTPS em produção** - Para comunicação Flask-Baileys

---

## Comparação: Baileys vs Twilio

| Recurso | Baileys | Twilio |
|---------|---------|--------|
| QR Code | ✅ Sim | ❌ Não |
| Número próprio | ✅ Qualquer | ❌ Sandbox/Aprovado |
| Custo | 🆓 Grátis | 💰 Pago |
| Conexão | ⚠️ Manual | ✅ Automática |
| Bloqueios | ⚠️ Possível | ✅ Raro |
| Flexibilidade | ✅ Total | ⚠️ Limitada |
| Suporte | ❌ Comunidade | ✅ Oficial |

**Escolha Baileys quando:**
- Cliente quer usar seu próprio número
- Quer controle total
- Não tem orçamento para API paga
- Precisa de flexibilidade

---

## Próximos Passos

- [ ] Testar conexão via QR Code
- [ ] Enviar mensagem de teste
- [ ] Configurar disparo de boletos
- [ ] Implementar webhooks (receber mensagens)
- [ ] Configurar backup automático de sessões

---

## Comandos Úteis

```bash
# Iniciar sistema completo
python start.py

# Apenas Baileys
cd whatsapp-baileys && npm start

# Verificar status Baileys
curl http://localhost:3000/status

# Verificar status Flask
curl http://localhost:5000/api/whatsapp/status

# Logs Baileys (no terminal)
# Logs Flask (no terminal do Python)
# Logs Browser (F12 > Console)
```

---

**Nexus CRM** - "Aqui seu tempo vale ouro"

**Status:** ✅ CONFIGURADO COM BAILEYS
**Versão:** 1.0.0 (Baileys 6.6.0)
**Data:** 2025-11-16
