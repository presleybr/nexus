# 🔧 Como Criar Serviço WPPConnect Manualmente no Render

## Passo a Passo Completo

### Passo 1: Acessar Dashboard do Render

1. Acesse: https://dashboard.render.com/
2. Faça login com sua conta
3. Você verá a lista de seus projetos/serviços

### Passo 2: Criar Novo Web Service

1. Clique no botão **"New +"** (canto superior direito)
2. Selecione **"Web Service"**

### Passo 3: Conectar ao Repositório

1. **Connect a repository**:
   - Se já conectou antes, selecione `presleybr/nexus`
   - Se não, clique em "Configure account" e autorize o GitHub

2. Depois de selecionar o repositório `presleybr/nexus`, clique em **"Connect"**

### Passo 4: Configurar o Serviço

Preencha os campos com EXATAMENTE estes valores:

#### Configurações Básicas

| Campo | Valor |
|-------|-------|
| **Name** | `nexus-wppconnect` |
| **Region** | `Oregon (US West)` |
| **Branch** | `main` |
| **Root Directory** | `wppconnect` ⚠️ IMPORTANTE! |
| **Environment** | `Node` |
| **Build Command** | `npm install` |
| **Start Command** | `npm start` |

⚠️ **ATENÇÃO:** O campo **Root Directory** é ESSENCIAL! Deve ser exatamente `wppconnect`

#### Plano

- **Instance Type**: Selecione `Starter` ($7/mês)
  - ⚠️ Free tier NÃO funciona para múltiplos serviços

### Passo 5: Configurar Variáveis de Ambiente

Antes de fazer deploy, clique em **"Advanced"** e adicione as variáveis:

| Key | Value |
|-----|-------|
| `PORT` | `10000` |
| `SECRET_KEY` | `SUA_CHAVE_SECRETA_AQUI` (gere uma aleatória) |
| `NODE_VERSION` | `18.17.0` |

⚠️ **Para gerar SECRET_KEY segura:**
```bash
# No terminal local, rode:
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**NÃO configure `HOST` e `BASE_URL` ainda!** Faremos isso depois do deploy.

### Passo 6: Criar o Serviço

1. Revise todas as configurações
2. Clique no botão **"Create Web Service"** (no final da página)
3. O Render começará o build automaticamente

### Passo 7: Aguardar Build

O processo de build leva ~3-5 minutos:

1. Você verá a tela de logs
2. Aguarde até aparecer:
   ```
   ✅ WPPConnect Server iniciado com sucesso!
   🌐 Servidor rodando em: ...
   ```
3. O status mudará para **"Live"** (verde)

### Passo 8: Copiar a URL do Serviço

Depois que o serviço estiver **Live**:

1. No topo da página, você verá a URL gerada
2. Exemplo: `https://nexus-wppconnect.onrender.com`
3. **Copie esta URL!** Você vai usar nos próximos passos

### Passo 9: Adicionar Variáveis de Ambiente Faltantes

Agora que você tem a URL, vamos adicionar as variáveis faltantes:

1. Clique em **"Environment"** (menu lateral esquerdo)
2. Clique em **"Add Environment Variable"**
3. Adicione estas 2 variáveis:

| Key | Value |
|-----|-------|
| `HOST` | A URL que você copiou (ex: `https://nexus-wppconnect.onrender.com`) |
| `BASE_URL` | A mesma URL (ex: `https://nexus-wppconnect.onrender.com`) |

4. Clique em **"Save Changes"**
5. O Render fará **redeploy automático** (~2 minutos)

### Passo 10: Configurar WPPCONNECT_URL no Backend

Agora precisamos configurar o backend para apontar para o WPPConnect:

1. Volte para o dashboard: https://dashboard.render.com/
2. Clique no serviço **`nexus-crm-backend`** (ou similar)
3. Vá em **"Environment"** (menu lateral)
4. Procure se já existe `WPPCONNECT_URL`:
   - **Se existe:** Clique em "Edit" e atualize o valor
   - **Se não existe:** Clique em "Add Environment Variable"

5. Configure:

| Key | Value |
|-----|-------|
| `WPPCONNECT_URL` | A URL do WPPConnect (ex: `https://nexus-wppconnect.onrender.com`) |

6. Clique em **"Save Changes"**
7. O backend fará redeploy automático

### Passo 11: Testar o WPPConnect

#### 11.1 Testar o Serviço Diretamente

Abra no navegador (substitua pela sua URL):
```
https://nexus-wppconnect.onrender.com/
```

**Deve retornar:**
```json
{
  "status": "running"
}
```

Se retornar isso, **SUCESSO!** O WPPConnect está rodando! ✅

#### 11.2 Testar no Nexus CRM

1. Acesse: https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp
2. Clique em **"Conectar WhatsApp"**
3. Aguarde 5-10 segundos
4. **O QR Code deve aparecer!**
5. Escaneie com WhatsApp do celular (WhatsApp > Menu > Dispositivos Conectados > Conectar Dispositivo)
6. Após escanear, o status muda para **"Conectado ✅"**

#### 11.3 Enviar Mensagem de Teste

1. No painel WhatsApp, campo "Telefone de Teste"
2. Digite seu número com DDI: `5511999999999`
3. Clique em **"Enviar Mensagem de Teste"**
4. Você deve receber a mensagem no WhatsApp! 🎉

## 🔍 Troubleshooting

### Problema: Build Failed

**Erro:** `npm install failed`

**Solução:**
1. Verifique que **Root Directory** está configurado como `wppconnect`
2. Vá em Settings → "Clear build cache & deploy"

---

**Erro:** `Cannot find module '@wppconnect-team/wppconnect-server'`

**Solução:**
1. Verifique os logs de build
2. Certifique-se que `npm install` foi executado
3. Force rebuild: Settings → "Clear build cache & deploy"

### Problema: Service Started but Not Responding

**Erro:** URL retorna timeout ou erro 503

**Solução:**
1. Aguarde 1-2 minutos após status "Live" (servidor precisa inicializar)
2. Verifique os logs: Logs → procure por "WPPConnect Server iniciado"
3. Confirme que `PORT` está configurada como `10000`

### Problema: QR Code Não Aparece

**Erro:** Frontend não mostra QR Code

**Solução:**
1. Verifique que `WPPCONNECT_URL` está configurada no backend
2. Teste o endpoint diretamente:
   ```bash
   curl https://nexus-wppconnect.onrender.com/
   ```
3. Verifique logs do backend para erros de conexão
4. Confirme que ambos serviços estão "Live"

### Problema: "Connection Refused"

**Erro:** Backend não consegue conectar ao WPPConnect

**Solução:**
1. Confirme que as URLs estão corretas (sem / no final)
2. Verifique que `WPPCONNECT_URL` no backend = URL do serviço WPPConnect
3. Aguarde 1-2 minutos após deploy
4. Teste acessar a URL no navegador

## ✅ Checklist de Verificação

Antes de considerar concluído:

- [ ] Serviço `nexus-wppconnect` criado no Render
- [ ] Status do serviço está "Live" (verde)
- [ ] Build concluído sem erros
- [ ] Variáveis de ambiente configuradas:
  - [ ] `PORT` = `10000`
  - [ ] `SECRET_KEY` = (sua chave)
  - [ ] `NODE_VERSION` = `18.17.0`
  - [ ] `HOST` = URL do serviço
  - [ ] `BASE_URL` = URL do serviço
- [ ] Variável `WPPCONNECT_URL` configurada no backend
- [ ] Backend fez redeploy após adicionar `WPPCONNECT_URL`
- [ ] URL do WPPConnect responde `{"status": "running"}`
- [ ] QR Code aparece em `/crm/whatsapp`
- [ ] Conseguiu conectar WhatsApp
- [ ] Mensagem de teste foi recebida

## 📸 Screenshots das Configurações

### Tela de Criação do Serviço

```
┌─────────────────────────────────────┐
│ Create a New Web Service            │
├─────────────────────────────────────┤
│ Name: nexus-wppconnect              │
│ Region: Oregon (US West)            │
│ Branch: main                        │
│ Root Directory: wppconnect ← IMPORTANTE!
│ Runtime: Node                       │
│ Build Command: npm install          │
│ Start Command: npm start            │
│ Plan: Starter ($7/month)            │
└─────────────────────────────────────┘
```

### Variáveis de Ambiente (Primeira vez)

```
PORT = 10000
SECRET_KEY = abc123...xyz789
NODE_VERSION = 18.17.0
```

### Variáveis de Ambiente (Após deploy)

```
PORT = 10000
SECRET_KEY = abc123...xyz789
NODE_VERSION = 18.17.0
HOST = https://nexus-wppconnect.onrender.com
BASE_URL = https://nexus-wppconnect.onrender.com
```

### Backend - Variável WPPCONNECT_URL

```
WPPCONNECT_URL = https://nexus-wppconnect.onrender.com
```

## 💰 Custos Estimados

**Plano Necessário:**
- Free tier **NÃO** suporta este serviço
- **Starter Plan**: $7/mês

**Total no Render:**
- nexus-crm-backend: $7/mês
- nexus-wppconnect: $7/mês
- **Total: $14/mês**

## 🎓 Referências

- Render Docs: https://render.com/docs
- WPPConnect Docs: https://wppconnect.io/
- Repositório: https://github.com/presleybr/nexus

## 📞 Suporte

Se encontrar problemas:
1. Leia a seção Troubleshooting acima
2. Verifique os logs no Render (Logs → últimas linhas)
3. Abra issue: https://github.com/presleybr/nexus/issues

---

**Última atualização:** 2025-11-29
