# 🚀 Como Iniciar o WPPConnect Server

## O que é o erro 400?
O erro `POST /api/whatsapp/wppconnect/iniciar HTTP/1.1" 400` indica que o **WPPConnect Server não está rodando**.

## ✅ Solução Rápida:

### 1. Abra um novo terminal/prompt de comando

### 2. Navegue até a pasta do WPPConnect:
```bash
cd D:\Nexus\wppconnect-server
```

### 3. Inicie o servidor:
```bash
npm start
```

**OU**, se tiver o arquivo `start.bat`:
```bash
start.bat
```

### 4. Aguarde a mensagem:
```
✓ WPPConnect server is running on http://localhost:3001
```

### 5. Agora volte ao sistema e tente conectar o WhatsApp novamente

---

## 🔍 Verificar se está rodando:

Abra o navegador e acesse:
```
http://localhost:3001
```

Se aparecer uma página ou resposta, significa que está funcionando! ✅

---

## 💡 Dica:
Mantenha este terminal **aberto** enquanto usar o sistema. Se fechar, o WhatsApp não funcionará.

---

## 🐛 Problemas?

Se ainda não funcionar, verifique:
1. Node.js está instalado? (`node --version`)
2. As dependências foram instaladas? (`npm install`)
3. A porta 3001 está disponível?
