# 🚀 Deploy Nexus CRM no Render.com

Este guia mostra como fazer deploy do Nexus CRM no Render.com.

## ⚠️ LIMITAÇÕES IMPORTANTES

### Armazenamento Efêmero
- **Problema**: Render.com tem disco efêmero - arquivos salvos somem ao reiniciar
- **Impacto**: PDFs de boletos e planilhas Excel são perdidos
- **Solução**: Use AWS S3, Cloudflare R2 ou Google Cloud Storage

### Chromium/Playwright
- **Problema**: Consome muita memória (512MB+)
- **Solução**: Use plano Starter (/mês) ou superior

## 📋 Checklist Pré-Deploy

- [ ] Conta no Render.com criada
- [ ] Código no GitHub (repositório público ou privado)
- [ ] Credenciais Canopus em mãos
- [ ] (Opcional) Bucket S3 configurado

## 🎯 Passo a Passo

### 1. Preparar Repositório GitHub

```bash
cd D:/Nexus
git init
git remote add origin https://github.com/presleybr/nexus.git
git add .
git commit -m "Deploy inicial Render.com"
git push -u origin main
```

### 2. Criar PostgreSQL Database

1. Acesse [Render Dashboard](https://dashboard.render.com)
2. New + → PostgreSQL
3. Configurações:
   - Name: `nexus-crm-db`
   - Database: `nexus_crm`
   - User: `postgres`
   - Region: Oregon (US West)
   - Plan: **Free** ou **Starter**
4. Copie a **Internal Database URL**

### 3. Executar Migrations

```bash
# Conecte ao banco
psql <INTERNAL_DATABASE_URL>

# Execute migrations
\i database/init_database.sql

# Verifique tabelas
\dt

# Saia
\q
```

### 4. Criar Web Service (Backend)

1. New + → Web Service
2. Conecte repositório: `presleybr/nexus`
3. Configurações:
   - Name: `nexus-crm-backend`
   - Region: Oregon (mesma do banco!)
   - Environment: **Docker**
   - Dockerfile Path: `./Dockerfile`
   - Plan: **Starter** (/mês recomendado)

4. **Environment Variables**:

```
DATABASE_URL=<cole aqui Internal Database URL>
SECRET_KEY=<gere chave aleatória>
JWT_SECRET_KEY=<gere outra chave>
FLASK_ENV=production
PORT=5000
PLAYWRIGHT_HEADLESS=true

# Canopus (suas credenciais)
CANOPUS_URL=https://app.canopus.com.br
CANOPUS_LOGIN=<seu login>
CANOPUS_SENHA=<sua senha>
CANOPUS_CODIGO_EMPRESA=<código>
CANOPUS_PONTO_VENDA_DEFAULT=24627
```

5. Health Check: `/health`
6. Deploy! (primeira vez: 10-15 min)

### 5. Criar Static Site (Frontend)

1. New + → Static Site
2. Conecte mesmo repositório
3. Configurações:
   - Name: `nexus-crm-frontend`
   - Build Command: `echo Static`
   - Publish Directory: `frontend`

4. **Redirects/Rewrites**:
   - Source: `/api/*`
   - Destination: `https://nexus-crm-backend.onrender.com/api/*`
   - Type: Rewrite

### 6. Testar

```bash
# Backend
curl https://nexus-crm-backend.onrender.com/health

# Frontend
open https://nexus-crm-frontend.onrender.com
```

## 🗂️ Configurar S3 (Recomendado)

### AWS S3

1. Crie bucket S3: `nexus-crm-files`
2. Configure CORS e acesso público
3. Adicione variáveis no Render:

```
USE_EXTERNAL_STORAGE=true
S3_BUCKET_NAME=nexus-crm-files
S3_REGION=us-east-1
S3_ACCESS_KEY=AKIA...
S3_SECRET_KEY=...
```

### Cloudflare R2 (Alternativa mais barata)

```
USE_EXTERNAL_STORAGE=true
S3_BUCKET_NAME=nexus-crm
S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```

## 🐛 Troubleshooting

### Build falha

```
# Erro: Playwright install
# Solução: Verifique Dockerfile tem install-deps
```

### Chromium crash

```
# Erro: Out of memory
# Solução: Upgrade para plano Standard
```

### PDFs não salvam

```
# Causa: Armazenamento efêmero
# Solução: Configure S3
```

## 📊 Monitoramento

```bash
# Logs em tempo real
render logs nexus-crm-backend --tail

# Métricas
# Dashboard > Service > Metrics
```

## 💰 Custos Estimados

| Recurso | Plano | Custo/mês |
|---------|-------|-----------|
| PostgreSQL | Free | /usr/bin/bash |
| PostgreSQL | Starter |  |
| Backend | Starter |  |
| Frontend | Free | /usr/bin/bash |
| **Total Mínimo** | | **/mês** |

## 🔐 Variáveis Secretas

**NUNCA** commite senhas! Use secrets do Render:

1. Dashboard > Service > Environment
2. Marque variáveis como "Secret"
3. Use `sync: false` no render.yaml

## 🚀 Deploy Automático

Após configurado, todo `git push` faz deploy automático!

```bash
git add .
git commit -m "feat: nova feature"
git push origin main
# Render faz deploy automaticamente
```

## 📚 Recursos

- [Render Docs](https://render.com/docs)
- [Playwright no Render](https://render.com/docs/deploy-playwright)
- [PostgreSQL no Render](https://render.com/docs/databases)

---

**Desenvolvido com ❤️ para funcionar em produção**
