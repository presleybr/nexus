# 🚀 Guia de Deploy Evolution API - Render.com (PRODUÇÃO)

## 📋 VISÃO GERAL

Este guia mostra como configurar a Evolution API no Render.com para o Nexus CRM em **PRODUÇÃO**.

**Arquitetura:**
```
┌─────────────────────────────────────────┐
│  Render Service 1: Evolution API        │
│  URL: nexus-evolution-api.onrender.com  │
│  Porta: 10000                            │
└──────────────────┬──────────────────────┘
                   │ (REST API)
                   ▼
┌─────────────────────────────────────────┐
│  Render Service 2: Nexus Backend        │
│  URL: nexus-crm-backend-6jxi.onrender.com │
│  Porta: 3000                             │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  PostgreSQL Database                    │
│  (Compartilhado entre os dois serviços) │
└─────────────────────────────────────────┘
```

---

## 🎯 PASSO 1: DEPLOY DA EVOLUTION API NO RENDER

### 1.1 Criar Novo Web Service

1. Acesse: **https://dashboard.render.com/**
2. Clique em **"New +" → "Web Service"**
3. Conecte seu GitHub (se ainda não conectou)
4. Ou use **"Public Git Repository"** com a URL:
   ```
   https://github.com/EvolutionAPI/evolution-api
   ```

### 1.2 Configurar Serviço

Preencha os campos:

| Campo | Valor |
|-------|-------|
| **Name** | `nexus-evolution-api` |
| **Region** | `Oregon (US West)` ou sua preferência |
| **Branch** | `main` |
| **Root Directory** | _(deixar vazio)_ |
| **Runtime** | `Node` |
| **Build Command** | `npm install` |
| **Start Command** | `npm start` |
| **Instance Type** | `Free` _(ou Starter $7/mês para melhor performance)_ |

### 1.3 Configurar Variáveis de Ambiente

Na seção **"Environment Variables"**, adicione:

#### ⚡ OBRIGATÓRIAS:

```env
SERVER_URL=https://nexus-evolution-api.onrender.com
PORT=10000
AUTHENTICATION_API_KEY=NexusSecret2024!@#$%
AUTHENTICATION_TYPE=apikey
```

> ⚠️ **IMPORTANTE:** Anote o valor de `AUTHENTICATION_API_KEY` - você vai precisar depois!

#### 🗄️ BANCO DE DADOS (PostgreSQL):

**Opção A - Usar PostgreSQL existente do Nexus:**

Copie a `DATABASE_URL` do seu serviço Nexus:

1. Vá em: Dashboard Render → `nexus-crm-backend-6jxi` → Environment
2. Copie o valor de `DATABASE_URL`
3. Adicione as variáveis:

```env
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://nexus_user:sua_senha@dpg-xyz.oregon-postgres.render.com:5432/nexus_db
DATABASE_CONNECTION_CLIENT_NAME=evolution_api
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=false
DATABASE_SAVE_MESSAGE_UPDATE=false
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
```

**Opção B - Criar novo PostgreSQL (Separado):**

1. Em Render, clique em **"New +" → "PostgreSQL"**
2. Name: `nexus-evolution-db`
3. Database: `evolution`
4. User: `evolution`
5. Region: `Oregon (US West)` _(mesma região!)_
6. Depois de criado, copie a **Internal Database URL**
7. Use nas variáveis acima

#### 📝 LOGS E QR CODE:

```env
LOG_LEVEL=ERROR
LOG_COLOR=false
LOG_BAILEYS=error
QRCODE_LIMIT=30
QRCODE_COLOR=#198754
DEL_INSTANCE=false
```

#### 🔔 WEBHOOK (Opcional - para eventos em tempo real):

```env
WEBHOOK_GLOBAL_ENABLED=false
```

_(Configure depois se quiser receber eventos de mensagem)_

### 1.4 Criar Serviço

1. Clique em **"Create Web Service"**
2. Aguarde 5-10 minutos para o deploy
3. Quando aparecer "Live ✅", copie a URL gerada

---

## 🎯 PASSO 2: TESTAR EVOLUTION API

Após deploy completo, teste se está funcionando:

### Teste 1: Health Check

Abra no navegador:
```
https://nexus-evolution-api.onrender.com
```

Deve retornar algo como:
```json
{
  "status": 200,
  "message": "Welcome to the Evolution API",
  "version": "2.x.x"
}
```

### Teste 2: Criar Instância (via cURL ou Postman)

**Usando cURL:**
```bash
curl -X POST https://nexus-evolution-api.onrender.com/instance/create \
  -H "apikey: NexusSecret2024!@#$%" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "nexus-crm",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

**Usando Postman:**
- **Method:** POST
- **URL:** `https://nexus-evolution-api.onrender.com/instance/create`
- **Headers:**
  ```
  apikey: NexusSecret2024!@#$%
  Content-Type: application/json
  ```
- **Body (JSON):**
  ```json
  {
    "instanceName": "nexus-crm",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }
  ```

**Resposta esperada:**
```json
{
  "instance": {
    "instanceName": "nexus-crm",
    "status": "created"
  }
}
```

✅ **Se funcionou, Evolution API está OK!**

---

## 🎯 PASSO 3: CONFIGURAR BACKEND NEXUS

Agora vamos conectar o backend Nexus à Evolution API.

### 3.1 Adicionar Variáveis de Ambiente no Nexus Backend

1. Acesse: **https://dashboard.render.com/**
2. Selecione: **`nexus-crm-backend-6jxi`** (ou o nome do seu backend)
3. Vá em: **"Environment"**
4. Clique em **"Add Environment Variable"**

**Adicione estas 3 variáveis:**

```env
EVOLUTION_API_URL=https://nexus-evolution-api.onrender.com
EVOLUTION_API_KEY=NexusSecret2024!@#$%
EVOLUTION_INSTANCE_NAME=nexus-crm
```

> ⚠️ Use a **MESMA** chave que você definiu no `AUTHENTICATION_API_KEY` da Evolution API!

### 3.2 Salvar e Redeploy

1. Clique em **"Save Changes"**
2. Render fará **redeploy automático** do backend
3. Aguarde 3-5 minutos

---

## 🎯 PASSO 4: TESTAR INTEGRAÇÃO COMPLETA

### 4.1 Testar Health Check do Backend

```bash
curl https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp
```

Deve retornar:
```json
{
  "status": "running",
  "service": "Nexus WhatsApp Server (Evolution API)",
  "connected": false,
  "evolutionAPI": "https://nexus-evolution-api.onrender.com"
}
```

### 4.2 Conectar WhatsApp

1. Acesse no navegador: **https://seu-frontend.com/crm/whatsapp**
2. Clique em **"Conectar WhatsApp"**
3. Aguarde o **QR Code** aparecer (pode demorar 10-20 segundos no Render gratuito)
4. No celular:
   - Abra WhatsApp
   - Vá em **"Dispositivos Conectados"**
   - Clique **"Conectar Dispositivo"**
   - Escaneie o QR Code
5. Aguarde confirmação

### 4.3 Verificar Status

```bash
curl https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp/status
```

Se conectado:
```json
{
  "success": true,
  "connected": true,
  "phone": "5511999999999",
  "state": "open"
}
```

---

## 🎯 PASSO 5: TESTAR ENVIO DE MENSAGEM

### Enviar mensagem de texto:

```bash
curl -X POST https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp/send-text \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "message": "Teste Evolution API em produção!"
  }'
```

### Enviar PDF:

```bash
curl -X POST https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp/send-file \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "filePath": "https://exemplo.com/boleto.pdf",
    "caption": "Seu boleto",
    "filename": "boleto.pdf"
  }'
```

---

## ✅ CHECKLIST FINAL

Marque conforme concluir:

- [ ] Evolution API deployada no Render
- [ ] Variáveis de ambiente configuradas na Evolution API
- [ ] PostgreSQL conectado
- [ ] Health check da Evolution API funcionando
- [ ] Instância `nexus-crm` criada
- [ ] Backend Nexus atualizado com variáveis EVOLUTION_*
- [ ] Backend Nexus redeployado
- [ ] QR Code gerado com sucesso
- [ ] WhatsApp conectado
- [ ] Mensagem de teste enviada
- [ ] PDF de teste enviado

---

## 🔧 TROUBLESHOOTING

### ❌ Evolution API não inicia

**Erro:** Service failed to start

**Solução:**
1. Vá em **Logs** no painel do Render
2. Procure por erros
3. Verifique se todas as variáveis estão corretas
4. Certifique-se que `PORT=10000`

### ❌ Backend não conecta na Evolution API

**Erro:** "Não foi possível conectar à Evolution API"

**Solução:**
1. Verifique se `EVOLUTION_API_URL` está correto (sem `/` no final)
2. Verifique se `EVOLUTION_API_KEY` é EXATAMENTE igual ao `AUTHENTICATION_API_KEY`
3. Teste manualmente: `curl https://nexus-evolution-api.onrender.com`

### ❌ QR Code não aparece

**Erro:** "Aguardando QR Code..."

**Solução:**
1. Aguarde 30 segundos (Render gratuito é lento no primeiro acesso)
2. Tente chamar `/start` novamente
3. Verifique logs da Evolution API

### ❌ Desconecta após algum tempo

**Solução:**
- Certifique-se que `DATABASE_ENABLED=true`
- Verifique se o PostgreSQL está acessível
- No Render gratuito, serviços "dormem" após 15min de inatividade

### ❌ Instance not found

**Solução:**
- Execute o curl de criar instância novamente (Passo 2, Teste 2)

---

## 📊 MONITORAMENTO

### Ver logs da Evolution API:
```
Dashboard Render → nexus-evolution-api → Logs
```

### Ver logs do Backend Nexus:
```
Dashboard Render → nexus-crm-backend-6jxi → Logs
```

### Ver status do PostgreSQL:
```
Dashboard Render → PostgreSQL Database → Metrics
```

---

## 💡 DICAS DE PRODUÇÃO

1. **Performance:** Considere upgrade para plano Starter ($7/mês) para:
   - Mais memória RAM
   - Não dormir após 15min
   - Melhor tempo de resposta

2. **Segurança:**
   - Mude `AUTHENTICATION_API_KEY` para algo forte
   - Nunca compartilhe a API Key
   - Use HTTPS sempre (Render já fornece)

3. **Backup:**
   - PostgreSQL no Render faz backup automático
   - Sessões ficam salvas no banco

4. **Escalabilidade:**
   - Evolution API suporta múltiplas instâncias
   - Você pode criar `nexus-crm-2`, `nexus-crm-3`, etc.

---

## 🎉 SUCESSO!

Agora seu Nexus CRM está rodando com Evolution API em **PRODUÇÃO no Render.com**!

**Benefícios:**
- ✅ Muito mais estável que WPPConnect
- ✅ Consome menos memória (sem Chromium)
- ✅ Persistência automática de sessões
- ✅ Reconexão automática após reiniciar
- ✅ API REST completa e documentada
- ✅ Suporte a webhooks

---

## 📚 DOCUMENTAÇÃO ADICIONAL

- **Evolution API:** https://doc.evolution-api.com/
- **GitHub:** https://github.com/EvolutionAPI/evolution-api
- **Render Docs:** https://render.com/docs

---

## 📞 PRÓXIMOS PASSOS

1. ✅ Testar disparo de boletos em produção
2. ✅ Configurar webhook (opcional) para receber mensagens
3. ✅ Monitorar logs por alguns dias
4. ✅ Considerar upgrade para plano pago se necessário

**Parabéns! Sistema em produção! 🚀**
