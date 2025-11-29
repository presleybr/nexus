
# ⚡ Instruções Rápidas - Deploy WPPConnect no Render

## ✅ O que acabamos de fazer

Criamos **dois serviços** no mesmo projeto Render:
1. **nexus-crm-backend** (Flask) - Backend principal
2. **nexus-wppconnect** (Node.js) - Servidor WhatsApp ← NOVO!

## 📋 Próximos Passos

### Passo 1: Aguardar Deploy Automático

Acabei de fazer push para GitHub. O Render vai:
- ✅ Detectar o `render.yaml` atualizado
- ✅ Criar automaticamente o serviço `nexus-wppconnect`
- ✅ Fazer build e deploy

**Tempo estimado:** 5-7 minutos

### Passo 2: Verificar no Dashboard do Render

1. Acesse: https://dashboard.render.com/
2. Vá para o projeto "Nexus CRM"
3. Você deve ver **2 serviços**:
   - `nexus-crm-backend` (já existia)
   - `nexus-wppconnect` (NOVO - criado automaticamente)

### Passo 3: Configurar Variáveis de Ambiente

#### 3.1 Serviço: nexus-wppconnect

Acesse o serviço `nexus-wppconnect` → Environment

Adicione/Atualize:
```
HOST=https://nexus-wppconnect.onrender.com
BASE_URL=https://nexus-wppconnect.onrender.com
```

**⚠️ IMPORTANTE:** Substitua `nexus-wppconnect` pela URL real que o Render gerou!

Exemplo: Se o Render gerou `https://nexus-wppconnect-abc123.onrender.com`, use essa URL.

#### 3.2 Serviço: nexus-crm-backend

Acesse o serviço `nexus-crm-backend` → Environment

Adicione/Atualize:
```
WPPCONNECT_URL=https://nexus-wppconnect.onrender.com
```

**⚠️ IMPORTANTE:** Use a mesma URL do passo anterior!

### Passo 4: Redeploy dos Serviços

Após configurar as variáveis:

1. **nexus-wppconnect**: Clique em "Manual Deploy" → "Deploy latest commit"
2. **nexus-crm-backend**: Clique em "Manual Deploy" → "Deploy latest commit"

Aguarde ~3-5 minutos para cada serviço ficar online.

### Passo 5: Testar WPPConnect

#### 5.1 Verificar se WPPConnect está online

Abra no navegador:
```
https://nexus-wppconnect.onrender.com/
```

Deve retornar algo como:
```json
{
  "status": "running"
}
```

#### 5.2 Testar no Nexus CRM

1. Acesse: https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp
2. Clique em **"Conectar WhatsApp"**
3. Aguarde alguns segundos
4. **QR Code deve aparecer!**
5. Escaneie com WhatsApp do celular
6. Após conectar, status muda para "Conectado ✅"

### Passo 6: Enviar Mensagem de Teste

1. No painel WhatsApp, insira seu número: `5511999999999`
2. Clique em "Enviar Teste"
3. Deve receber mensagem no WhatsApp! 🎉

## 🎯 URLs Importantes

Após deploy, suas URLs serão:

| Serviço | URL | Função |
|---------|-----|--------|
| Backend | https://nexus-crm-backend-6jxi.onrender.com | API Flask + Frontend |
| WPPConnect | https://nexus-wppconnect.onrender.com | WhatsApp Server |

## 📊 Custos

**Free Tier não suporta múltiplos serviços!**

Você precisa de:
- **nexus-crm-backend**: Starter ($7/mês)
- **nexus-wppconnect**: Starter ($7/mês)

**Total: $14/mês**

**Alternativa mais barata:**
- Backend no Render Starter ($7/mês)
- WPPConnect no Railway Free ($5 crédito/mês)
- Total: $7/mês + gratuito

## 🔍 Verificação de Problemas

### Problema: Serviço não foi criado automaticamente

**Solução:**
1. Vá em dashboard.render.com
2. Clique em "New +" → "Blueprint"
3. Conecte ao repositório `presleybr/nexus`
4. O Render vai ler o `render.yaml` e criar tudo

### Problema: Build falhou

**Solução:**
1. Verifique os logs do serviço
2. Procure por erros de `npm install`
3. Se necessário, force rebuild: "Manual Deploy" → "Clear build cache & deploy"

### Problema: QR Code não aparece

**Solução:**
1. Verifique que `WPPCONNECT_URL` está configurada no backend
2. Teste o endpoint diretamente:
   ```
   curl https://nexus-wppconnect.onrender.com/
   ```
3. Verifique logs de ambos serviços

### Problema: "Connection refused"

**Solução:**
1. Confirme que as URLs nas variáveis de ambiente estão corretas
2. Aguarde 1-2 minutos após deploy (serviços precisam iniciar)
3. Verifique que ambos serviços estão "Live" (verde)

## 📝 Checklist Final

Antes de considerar finalizado, verifique:

- [ ] Serviço `nexus-wppconnect` aparece no dashboard
- [ ] Build do `nexus-wppconnect` concluído com sucesso
- [ ] Variável `HOST` configurada no `nexus-wppconnect`
- [ ] Variável `BASE_URL` configurada no `nexus-wppconnect`
- [ ] Variável `WPPCONNECT_URL` configurada no `nexus-crm-backend`
- [ ] Ambos serviços estão "Live" (status verde)
- [ ] URL do WPPConnect responde com `{"status": "running"}`
- [ ] QR Code aparece em `/crm/whatsapp`
- [ ] Consegue conectar WhatsApp escaneando QR Code
- [ ] Mensagem de teste é recebida no WhatsApp

## 🎓 Documentação Completa

Leia para mais detalhes:
- `SETUP_WPPCONNECT_RENDER.md` - Guia completo de configuração
- `wppconnect/README.md` - Documentação do serviço WPPConnect
- `SETUP_WHATSAPP_WPPCONNECT.md` - Alternativas (Railway, Heroku, VPS)

## 🆘 Precisa de Ajuda?

Se algo não funcionar:
1. Verifique os logs no dashboard do Render
2. Leia a documentação completa
3. Abra issue: https://github.com/presleybr/nexus/issues

---

**Status Atual:** Deploy iniciado ✅
**Próximo Passo:** Aguarde 5 minutos e vá para o Passo 2
