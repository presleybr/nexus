# ✅ Como Testar Persistência de Sessão WhatsApp

## O que foi implementado:

1. **Persistência no Banco de Dados**: Status da conexão (conectado/desconectado) é salvo no PostgreSQL
2. **Recuperação de Sessão**: Quando o servidor reinicia, verifica no banco se havia uma conexão ativa
3. **Tokens do WPPConnect**: Sessão do WhatsApp é salva em `/app/tokens/nexus-crm`
4. **Logout Explícito**: Só desconecta quando clicar no botão "Desconectar"

---

## 📋 Passo-a-Passo para Testar:

### 1. **Executar Migração SQL** (Se ainda não executou)

No Render Dashboard > PostgreSQL > nexus-crm-db > Queries:

```sql
CREATE TABLE IF NOT EXISTS whatsapp_status (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(100) NOT NULL UNIQUE DEFAULT 'nexus-crm',
    is_connected BOOLEAN DEFAULT FALSE,
    phone_number VARCHAR(20),
    qr_code TEXT,
    last_connected_at TIMESTAMP,
    last_disconnected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO whatsapp_status (session_name, is_connected)
VALUES ('nexus-crm', FALSE)
ON CONFLICT (session_name) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_whatsapp_status_session ON whatsapp_status(session_name);
```

---

### 2. **Conectar WhatsApp pela Primeira Vez**

1. Acesse: https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp
2. Clique em **"Conectar WhatsApp"**
3. Escaneie o QR code com seu celular
4. Aguarde mostrar: **✅ Conectado** + número do telefone

---

### 3. **Verificar no Banco de Dados** (Opcional)

Execute no Render Queries:

```sql
SELECT * FROM whatsapp_status WHERE session_name = 'nexus-crm';
```

Deve mostrar:
- `is_connected`: `true`
- `phone_number`: Seu número
- `last_connected_at`: Data/hora atual

---

### 4. **Testar Reload da Página**

1. **Pressione F5** ou recarregue a página
2. ✅ **Deve continuar mostrando**: "✅ Conectado" + número
3. ❌ **Não deve**: Pedir para escanear QR code novamente
4. ✅ **Botões devem estar**:
   - "Conectar WhatsApp": Oculto
   - "Desconectar": Visível
   - Card de teste: Visível

---

### 5. **Testar Reinício do Servidor** (Simulação)

No Render Dashboard > web/nexus-wppconnect:

1. Clique em **Manual Deploy > Clear build cache & deploy**
2. Aguarde deploy terminar (~5 minutos)
3. Acesse novamente: https://nexus-crm-backend-6jxi.onrender.com/crm/whatsapp
4. ✅ **Deve continuar mostrando**: "✅ Conectado" + número
5. ❌ **Não deve**: Pedir para escanear QR code novamente

---

### 6. **Testar Logout**

1. Clique no botão **"Desconectar"**
2. ✅ **Deve mostrar**:
   - Status: "❌ Desconectado"
   - Número: Oculto
   - Botão "Conectar WhatsApp": Visível
   - Botão "Desconectar": Oculto

3. **Verifique no banco** (Opcional):

```sql
SELECT * FROM whatsapp_status WHERE session_name = 'nexus-crm';
```

Deve mostrar:
- `is_connected`: `false`
- `phone_number`: `null`
- `last_disconnected_at`: Data/hora atual

---

### 7. **Testar Reload Após Logout**

1. Pressione **F5**
2. ✅ **Deve continuar mostrando**: "❌ Desconectado"
3. ✅ **Botão "Conectar WhatsApp"** deve estar visível

---

## 🔍 Verificar Logs (Se algo não funcionar):

### Backend (Nexus CRM):
https://dashboard.render.com/web/nexus-crm-backend/logs

Procure por:
- `[WHATSAPP SERVICE]` - Chamadas ao WPPConnect
- `Erro ao conectar` - Problemas de conexão

### WPPConnect:
https://dashboard.render.com/web/nexus-wppconnect/logs

Procure por:
- `📊 [INIT] Sessão conectada encontrada no banco!` - Recuperou sessão
- `🎉🎉🎉 [POLL] CONEXÃO DETECTADA!` - Detectou nova conexão
- `🔒 [LOGOUT] WhatsApp desconectado` - Logout executado
- `💾 [DB] Status salvo no banco` - Salvou no banco
- `❌ [DB] Erro ao conectar` - Problema com PostgreSQL

---

## 🐛 Problemas Comuns:

### Problema: "Desconectado" após reload
**Causa**: Tabela `whatsapp_status` não existe
**Solução**: Execute a migração SQL (passo 1)

### Problema: QR Code não aparece
**Causa**: WPPConnect não conseguiu iniciar Chromium
**Solução**: Veja logs do WPPConnect e procure por erros de Chromium

### Problema: Conecta mas depois desconecta sozinho
**Causa**: Variável `DATABASE_URL` não configurada no WPPConnect
**Solução**: Verificar no Render Dashboard > web/nexus-wppconnect > Environment

### Problema: "Live connection count: 3/3"
**Causa**: Vazamento de conexões
**Solução**: Execute: `database/queries/EMERGENCIA_MATAR_CONEXOES.sql`

---

## ✅ Comportamento Esperado:

| Ação | Resultado Esperado |
|------|-------------------|
| Primeira conexão | Escaneia QR, mostra "Conectado" + número |
| Reload da página | Continua "Conectado" (não pede QR novamente) |
| Reiniciar servidor | Continua "Conectado" (sessão recuperada) |
| Clicar "Desconectar" | Mostra "Desconectado", salva no banco |
| Reload após logout | Continua "Desconectado" |
| Conectar novamente | Escaneia QR, conecta normalmente |

---

## 📊 Verificações Técnicas:

### 1. Verificar se há tokens salvos:

No WPPConnect logs, procure por:
```
[nexus-crm:browser] Using browser folder '/app/tokens/nexus-crm'
```

### 2. Verificar polling de status:

No frontend (console do navegador), deve aparecer:
```
[STATUS WHATSAPP] {success: true, connected: true, phone: "5567999999999", ...}
```

A cada 5 segundos.

### 3. Verificar banco de dados:

```sql
-- Ver histórico de conexões
SELECT
    is_connected,
    phone_number,
    last_connected_at,
    last_disconnected_at
FROM whatsapp_status
WHERE session_name = 'nexus-crm';
```

---

## 🎯 Resumo:

- ✅ Sessão persiste após reload
- ✅ Sessão persiste após reinício do servidor
- ✅ Status salvo no PostgreSQL
- ✅ Frontend consulta status a cada 5 segundos
- ✅ Só desconecta quando clicar em "Desconectar"
- ✅ Tokens salvos em `/app/tokens/nexus-crm`
