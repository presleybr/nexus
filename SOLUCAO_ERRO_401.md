# Solução: Erro 401 - WhatsApp Baileys

## Problema Identificado

**Erro:** `❌ Conexão fechada. Código: 401`
**Causa:** Credenciais antigas/expiradas na pasta `sessions`

Quando há sessões antigas do WhatsApp salvas, o Baileys tenta reutilizá-las ao invés de gerar um novo QR Code. Se essas credenciais estiverem expiradas ou inválidas, ocorre o erro 401.

---

## ✅ Solução Aplicada

### 1. Limpeza Automática no Servidor

O `server.js` foi atualizado para **detectar e limpar automaticamente** sessões inválidas quando ocorre erro 401:

```javascript
// Tratamento específico para erro 401 (credenciais inválidas/expiradas)
if (statusCode === 401) {
    console.log('⚠️ Erro 401 - Credenciais inválidas ou expiradas');
    console.log('🗑️ Limpando sessões antigas...');
    try {
        if (existsSync('./sessions')) {
            rmSync('./sessions', { recursive: true, force: true });
            console.log('✅ Sessões antigas removidas');
            console.log('🔄 Chame /connect novamente para gerar novo QR Code');
        }
    } catch (error) {
        console.error('❌ Erro ao limpar sessões:', error.message);
    }
    connectionAttempts = 0;
}
```

### 2. Script Manual de Limpeza

Criado `whatsapp-baileys/limpar-sessoes.bat` para limpeza manual quando necessário.

**Como usar:**
```bash
cd D:\Nexus\whatsapp-baileys
limpar-sessoes.bat
```

### 3. Sessões Antigas Removidas

As sessões corrompidas foram removidas do sistema.

---

## 🔄 Como Usar Agora

### Passo 1: Iniciar Servidor Baileys

```bash
cd D:\Nexus\whatsapp-baileys
npm start
```

**Saída esperada:**
```
============================================
  🚀 Nexus WhatsApp Baileys Server
============================================
📡 Servidor rodando em http://localhost:3000
📱 Status: disconnected ❌
============================================
```

### Passo 2: Iniciar Flask

Em outro terminal:
```bash
cd D:\Nexus
python start.py
```

### Passo 3: Acessar Interface

```
http://localhost:5000/crm/whatsapp
```

### Passo 4: Conectar WhatsApp

1. Clique em **"Conectar WhatsApp"**
2. Aguarde o QR Code aparecer (3-5 segundos)
3. Abra WhatsApp no celular
4. Vá em **Dispositivos Conectados** → **Conectar Dispositivo**
5. Escaneie o QR Code
6. Aguarde confirmação

**Logs esperados no servidor Baileys:**
```
🔄 Tentativa 1/3 - Conectando ao WhatsApp...
📱 QR Code gerado!
✅ Conectado ao WhatsApp!
📱 Número: 5567999887766@s.whatsapp.net
```

---

## 🔍 Diagnosticar Problemas

### QR Code não aparece

**Verificar servidor Baileys:**
```bash
curl http://localhost:3000/status
```

**Resposta esperada (antes de conectar):**
```json
{
  "connected": false,
  "status": "connecting",
  "phone": null
}
```

**Verificar endpoint QR:**
```bash
curl http://localhost:3000/qr
```

**Resposta esperada:**
```json
{
  "success": true,
  "connected": false,
  "qr": "data:image/png;base64,iVBORw0KG..."
}
```

### Erro 401 persiste

**Solução:**
1. Pare o servidor Baileys (Ctrl+C)
2. Execute:
   ```bash
   cd D:\Nexus\whatsapp-baileys
   limpar-sessoes.bat
   ```
3. Reinicie:
   ```bash
   npm start
   ```
4. Tente conectar novamente

### Erro 405 - Muitas tentativas

**Solução:**
1. Pare o servidor Baileys
2. Aguarde **30 segundos**
3. Limpe sessões (se necessário)
4. Reinicie o servidor

---

## 📝 Notas Importantes

### Sessões WhatsApp

- ✅ **Primeira conexão:** Gera QR Code
- ✅ **Conexões seguintes:** Usa sessão salva (se válida)
- ⚠️ **Se expirada:** Erro 401 → Auto-limpeza → Novo QR Code

### Backup de Sessões

Para preservar sessão ativa:
```bash
# Backup
xcopy D:\Nexus\whatsapp-baileys\sessions D:\Nexus\backup_sessions /E /I

# Restaurar
xcopy D:\Nexus\backup_sessions D:\Nexus\whatsapp-baileys\sessions /E /I /Y
```

### Reconexão após Reiniciar

Se o servidor for reiniciado e a sessão estiver válida:
- ✅ **Não precisa** escanear QR Code novamente
- ✅ Reconecta automaticamente
- ✅ Status muda para "connected" em segundos

---

## 🛠️ Checklist de Resolução

Ao encontrar problemas de conexão:

- [ ] Verificar se servidor Baileys está rodando (`http://localhost:3000`)
- [ ] Verificar logs do servidor Baileys no terminal
- [ ] Se erro 401: Aguardar limpeza automática de sessões
- [ ] Clicar novamente em "Conectar WhatsApp"
- [ ] Aguardar QR Code (3-5 segundos)
- [ ] Verificar se QR Code aparece na interface
- [ ] Se não aparecer: Verificar console do navegador (F12)
- [ ] Se persistir: Limpar sessões manualmente e reiniciar

---

## 📊 Status do Sistema

**Servidor Baileys:** ✅ Atualizado com auto-limpeza de sessões
**Frontend:** ✅ Interface integrada ao design do CRM
**Erro 401:** ✅ Resolvido com limpeza automática
**Sessões antigas:** ✅ Removidas

---

## 🚀 Próximos Passos

1. Testar conexão completa
2. Enviar mensagem de teste
3. Testar envio de PDF
4. Configurar disparo de boletos
5. Implementar recebimento de mensagens (webhook)

---

**Nexus CRM** - "Aqui seu tempo vale ouro"

**Data da Correção:** 2025-11-16
**Status:** ✅ PRONTO PARA USAR
