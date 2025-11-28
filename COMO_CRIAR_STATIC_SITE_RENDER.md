# 🎨 Como Criar Static Site no Render.com

**Backend já rodando em:** https://nexus-crm-backend-6jxi.onrender.com

## 📋 Passo a Passo Completo

### 1. Acessar Render Dashboard

1. Vá para https://dashboard.render.com
2. Faça login com sua conta

### 2. Criar Novo Static Site

1. Clique em **"New +"** (canto superior direito)
2. Selecione **"Static Site"**
3. Conecte ao seu repositório GitHub: **`presleybr/nexus`**
4. Clique em **"Connect"**

### 3. Configurar o Static Site

Preencha os campos exatamente assim:

#### Informações Básicas

| Campo | Valor |
|-------|-------|
| **Name** | `nexus-crm-frontend` |
| **Region** | `Oregon (US West)` (mesma do backend!) |
| **Branch** | `main` |
| **Root Directory** | (deixe vazio) |
| **Build Command** | `echo "Static site - no build needed"` |
| **Publish Directory** | `frontend` |

#### Auto-Deploy

- ✅ Deixe marcado "Auto-Deploy" (deploy automático a cada push)

### 4. Configurar Redirects e Rewrites (CRÍTICO!)

**Depois que criar o site**, vá em:

1. Dashboard do Static Site → **"Redirects/Rewrites"**
2. Clique em **"Add Rule"**

#### Regra 1: API Requests (Rewrite)

Adicione esta regra para redirecionar chamadas `/api/*` para o backend:

| Campo | Valor |
|-------|-------|
| **Source** | `/api/*` |
| **Destination** | `https://nexus-crm-backend-6jxi.onrender.com/api/:splat` |
| **Action** | `Rewrite` |

Clique em **"Save"**

#### Regra 2: Health Check (Rewrite)

| Campo | Valor |
|-------|-------|
| **Source** | `/health` |
| **Destination** | `https://nexus-crm-backend-6jxi.onrender.com/health` |
| **Action** | `Rewrite` |

Clique em **"Save"**

#### Regra 3: Fallback para Index (Redirect)

Para SPAs (Single Page Applications) - caso você tenha rotas client-side:

| Campo | Valor |
|-------|-------|
| **Source** | `/*` |
| **Destination** | `/index.html` |
| **Action** | `Rewrite` |

Clique em **"Save"**

**ORDEM IMPORTA!** As regras devem estar nesta ordem:
1. `/api/*` → backend (Rewrite)
2. `/health` → backend (Rewrite)
3. `/*` → `/index.html` (Rewrite)

### 5. Configurar Headers (CORS)

1. Vá em **"Headers"** no dashboard do Static Site
2. Clique em **"Add Header"**

#### Header 1: CORS

| Campo | Valor |
|-------|-------|
| **Path** | `/*` |
| **Name** | `Access-Control-Allow-Origin` |
| **Value** | `*` |

Clique em **"Save"**

### 6. Deploy

1. Clique em **"Create Static Site"**
2. Aguarde o deploy (1-3 minutos)
3. Você receberá uma URL tipo: `https://nexus-crm-frontend.onrender.com`

### 7. Testar o Site

Após o deploy, acesse:

```
https://nexus-crm-frontend.onrender.com
```

**Você deve ver:**
- ✅ Landing page do Nexus CRM
- ✅ Botão "Entrar como Cliente"
- ✅ Botão "Portal Consórcio"

### 8. Testar o Login

1. Acesse: `https://nexus-crm-frontend.onrender.com/login-cliente`
2. Digite:
   - Email: `credms@nexusbrasi.ai`
   - Senha: `credms123`
3. Clique em **"Entrar"**

**Se aparecer erro "Credenciais inválidas":**
- O usuário não foi criado no banco do Render
- Veja próxima seção

### 9. Criar Usuário no Banco do Render

Se o login não funcionar, você precisa criar o usuário no banco do Render:

#### Conectar ao Banco do Render no DBeaver

1. No Render Dashboard → PostgreSQL Database → **"Info"**
2. Copie a **"External Database URL"**
   - Exemplo: `postgresql://user:pass@dpg-xxx-oregon-postgres.render.com:5432/nexus_crm_xxx`

3. No DBeaver:
   - **File → New → Database Connection**
   - Selecione **PostgreSQL**
   - Clique em **"URL"** (aba superior)
   - Cole a URL completa
   - Clique em **"Test Connection"**
   - Clique em **"Finish"**

#### Executar Script de Criação

1. Conectado ao banco do Render no DBeaver
2. Abra o arquivo: `D:\Nexus\database\criar_usuario_credms_FINAL.sql`
3. Execute todo o script: `Ctrl + X`
4. Verifique se apareceu: "CRIADO COM SUCESSO!"

#### Testar Novamente

1. Volte para: `https://nexus-crm-frontend.onrender.com/login-cliente`
2. Login: `credms@nexusbrasi.ai` / `credms123`
3. Deve funcionar agora! ✅

---

## 🔧 Configuração Alternativa (render.yaml)

Se preferir configurar via código, adicione isso no `render.yaml`:

```yaml
services:
  # ... (backend já existe)

  # Static Site Frontend
  - type: web
    name: nexus-crm-frontend
    env: static
    staticPublishPath: ./frontend
    buildCommand: echo "Static site ready"
    routes:
      - type: rewrite
        source: /api/*
        destination: https://nexus-crm-backend-6jxi.onrender.com/api/*
      - type: rewrite
        source: /health
        destination: https://nexus-crm-backend-6jxi.onrender.com/health
```

---

## 🐛 Troubleshooting

### Erro: "Failed to fetch" ao fazer login

**Causa:** Frontend não está conseguindo se comunicar com o backend

**Solução:**
1. Verifique se os Redirects estão configurados corretamente
2. Vá em "Redirects/Rewrites" e confirme:
   - `/api/*` → `https://nexus-crm-backend-6jxi.onrender.com/api/:splat`
   - Action: **Rewrite** (não Redirect!)

### Erro: "Credenciais inválidas"

**Causa:** Usuário não existe no banco do Render

**Solução:**
1. Conecte ao banco do Render (External Database URL)
2. Execute o script `criar_usuario_credms_FINAL.sql`
3. Tente fazer login novamente

### Erro: CORS

**Causa:** Requisições sendo bloqueadas por CORS

**Solução:**
1. Verifique se configurou o header CORS no Static Site
2. Ou configure CORS no backend (já deve estar configurado)

### Static Site não atualiza após push

**Causa:** Cache ou deploy não foi acionado

**Solução:**
1. Vá no dashboard do Static Site
2. Clique em **"Manual Deploy"** → **"Deploy latest commit"**
3. Aguarde 1-2 minutos

---

## 📊 Arquitetura Final

```
┌─────────────────────────────────────────┐
│          USUÁRIO ACESSA                 │
│  nexus-crm-frontend.onrender.com        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│       STATIC SITE (Frontend)            │
│  nexus-crm-frontend.onrender.com        │
│  - Serve HTML/CSS/JS                    │
│  - Landing page, Login, Dashboard       │
└────────────────┬────────────────────────┘
                 │
                 │ /api/* → rewrite
                 ▼
┌─────────────────────────────────────────┐
│       WEB SERVICE (Backend)             │
│  nexus-crm-backend-6jxi.onrender.com    │
│  - API Flask                            │
│  - Autenticação, Boletos, WhatsApp      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│       PostgreSQL Database               │
│  dpg-xxx.oregon-postgres.render.com     │
│  - Usuários, Clientes, Boletos          │
└─────────────────────────────────────────┘
```

---

## ✅ Checklist Final

Após seguir todos os passos, confirme:

- [ ] Static Site criado com nome `nexus-crm-frontend`
- [ ] Publish Directory configurado como `frontend`
- [ ] Redirect `/api/*` configurado como **Rewrite**
- [ ] Redirect aponta para `https://nexus-crm-backend-6jxi.onrender.com/api/:splat`
- [ ] Deploy finalizado (URL verde no dashboard)
- [ ] Landing page abre corretamente
- [ ] Login page abre (`/login-cliente`)
- [ ] Usuário criado no banco do Render
- [ ] Login funciona com `credms@nexusbrasi.ai` / `credms123`

---

## 🎉 Pronto!

Seu sistema completo está no ar:

- **Frontend:** https://nexus-crm-frontend.onrender.com
- **Backend API:** https://nexus-crm-backend-6jxi.onrender.com
- **Health Check:** https://nexus-crm-backend-6jxi.onrender.com/health

**Próximos passos:**
1. Configurar domínio customizado (opcional)
2. Conectar WhatsApp (Twilio ou WPPConnect)
3. Cadastrar clientes finais
4. Configurar automação de boletos

---

**Dúvidas?** Consulte a documentação oficial do Render:
- https://render.com/docs/static-sites
- https://render.com/docs/redirects-rewrites
