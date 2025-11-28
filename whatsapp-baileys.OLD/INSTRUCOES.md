# Instruções - WhatsApp Baileys Nexus CRM

## Correções Aplicadas

### Problema Resolvido: Erro 405
O erro 405 ocorre quando o WhatsApp rejeita muitas tentativas de conexão seguidas.

### Soluções Implementadas:

1. **Limite de Tentativas**: Máximo de 3 tentativas automáticas
2. **fetchLatestBaileysVersion**: Usa versão mais recente do WhatsApp Web
3. **Browser Info Corrigida**: `['Nexus CRM', 'Chrome', '10.0.0']`
4. **Logs Reduzidos**: Pino com level 'error' para evitar spam
5. **Sem Reconexão Automática**: Evita loops de reconexão
6. **Tratamento Específico Erro 405**: Reseta contador e aguarda 30s

## Como Usar

### 1. Iniciar o Servidor Baileys

```bash
# Opção 1: Via script (recomendado)
start-whatsapp-baileys.bat

# Opção 2: Manual
cd whatsapp-baileys
nvm use 20.18.0
npm start
```

### 2. Iniciar o Flask

```bash
python start.py
```

### 3. Acessar Interface

```
http://localhost:5000/crm/whatsapp
```

### 4. Conectar WhatsApp

1. Clique em **"Conectar WhatsApp"**
2. Aguarde o QR Code aparecer (pode levar 5-10 segundos)
3. Abra WhatsApp no celular
4. Vá em: **Configurações > Aparelhos Conectados > Conectar Aparelho**
5. Escaneie o QR Code
6. Aguarde confirmação (status mudará para "Conectado")

## Solução de Problemas

### Erro 405 - "Muitas tentativas"

**Causa**: WhatsApp bloqueou temporariamente por excesso de tentativas

**Solução**:
1. Pare o servidor Baileys (Ctrl+C)
2. Delete a pasta `sessions` (se existir)
```bash
cd whatsapp-baileys
rmdir /s sessions
```
3. Aguarde 30 segundos
4. Reinicie o servidor
5. Tente conectar novamente

### QR Code não aparece

**Solução**:
1. Verifique se o servidor Baileys está rodando:
```bash
curl http://localhost:3000/status
```

2. Verifique os logs do servidor Baileys
3. Se necessário, reinicie o servidor

### Conexão cai após escanear QR

**Possíveis Causas**:
- WhatsApp Web bloqueou temporariamente
- Versão do Baileys incompatível
- Firewall bloqueando conexão

**Solução**:
1. Aguarde 1 minuto
2. Delete sessões antigas
3. Tente novamente com QR Code novo

### "WhatsApp não conectado" ao enviar mensagem

**Solução**:
1. Verifique status: `http://localhost:3000/status`
2. Se `connected: false`, reconecte via interface
3. Aguarde status mudar para "Conectado"

## Logs e Debugging

### Logs do Servidor Baileys

```
🔄 Tentativa 1/3 - Conectando ao WhatsApp...
📱 QR Code gerado!
✅ Conectado ao WhatsApp!
```

### Logs de Erro

```
❌ Conexão fechada. Código: 405
⚠️ Erro 405 - Aguarde 30 segundos antes de tentar novamente
```

### Logs do Flask

```
[WHATSAPP] Cliente 1 iniciando conexão
[WHATSAPP] Resposta do Baileys: {'success': True}
[WHATSAPP] Solicitando QR Code
[WHATSAPP] Enviando mensagem para 67999887766
```

### Console do Browser (F12)

```javascript
[STATUS] {connected: false, status: "disconnected"}
[CONECTAR] Iniciando conexão...
[QR] Solicitando QR Code...
[QR] Resposta: {success: true, qr: "data:image/png;base64,..."}
```

## Endpoints da API

### POST /connect
Inicia conexão com WhatsApp
```bash
curl -X POST http://localhost:3000/connect
```

### GET /qr
Obtém QR Code em base64
```bash
curl http://localhost:3000/qr
```

### GET /status
Verifica status da conexão
```bash
curl http://localhost:3000/status
```

### POST /send-text
Envia mensagem de texto
```bash
curl -X POST http://localhost:3000/send-text \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5567999887766",
    "message": "Olá do Nexus CRM!"
  }'
```

### POST /send-file
Envia arquivo PDF
```bash
curl -X POST http://localhost:3000/send-file \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5567999887766",
    "filePath": "D:/Nexus/boletos/boleto.pdf",
    "filename": "boleto.pdf",
    "caption": "Seu boleto"
  }'
```

### POST /logout
Desconecta do WhatsApp
```bash
curl -X POST http://localhost:3000/logout
```

## Melhores Práticas

### Evitar Bloqueios

1. **Não reconectar múltiplas vezes**: Aguarde 30s entre tentativas
2. **Manter sessão**: Não delete `sessions` sem necessidade
3. **Um dispositivo por vez**: Não conecte o mesmo número em múltiplos lugares
4. **Respeitar limites**: Não envie spam

### Manutenção

1. **Backup da sessão**: Copie a pasta `sessions` periodicamente
2. **Atualizar Baileys**: `npm update @whiskeysockets/baileys`
3. **Monitorar logs**: Verifique erros frequentes
4. **Reiniciar semanalmente**: Evita problemas de memória

### Segurança

1. **Não compartilhe sessões**: Contêm credenciais sensíveis
2. **Não versione `sessions`**: Já está no .gitignore
3. **Use HTTPS em produção**: Para comunicação Flask-Baileys
4. **Proteja endpoints**: Adicione autenticação se expor externamente

## Estrutura de Arquivos

```
whatsapp-baileys/
├── server.js              # Servidor Express + Baileys (ATUALIZADO)
├── package.json           # Dependências (ES Modules)
├── sessions/              # Sessões WhatsApp (NÃO versionar)
├── .gitignore            # Ignora sessions e node_modules
├── README.md             # Documentação técnica
└── INSTRUCOES.md         # Este arquivo
```

## Status do Sistema

### Verificar se tudo está funcionando

```bash
# 1. Teste servidor Baileys
curl http://localhost:3000/

# 2. Teste status
curl http://localhost:3000/status

# 3. Teste Flask
curl http://localhost:5000/api/whatsapp/status
```

### Resposta Esperada

```json
// http://localhost:3000/
{
  "service": "Nexus WhatsApp Baileys",
  "status": "running",
  "connected": false,
  "version": "1.0.0"
}

// http://localhost:3000/status
{
  "connected": false,
  "status": "disconnected",
  "phone": null
}
```

## Próximos Passos

1. ✅ Servidor atualizado e corrigido
2. ✅ Integração com Flask funcionando
3. ✅ Interface web pronta
4. ⏳ Testar conexão real com WhatsApp
5. ⏳ Testar envio de mensagens
6. ⏳ Implementar disparo em massa

## Suporte

Em caso de problemas:
1. Verifique os logs do servidor Baileys
2. Verifique os logs do Flask
3. Verifique o Console do navegador (F12)
4. Se erro 405 persistir, aguarde 1 hora antes de tentar novamente
5. Em último caso, use um número diferente para testes

---

**Nexus CRM** - "Aqui seu tempo vale ouro"
