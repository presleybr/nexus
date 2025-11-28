# CORRECAO: Erro SSL ao Instalar WPPConnect

## PROBLEMA IDENTIFICADO

Erro ao instalar dependencias NPM:
```
npm error ERR_SSL_CIPHER_OPERATION_FAILED
npm error error:1C800066:Provider routines:ossl_gcm_stream_update:cipher operation failed
```

**Causa:** Incompatibilidade entre Node.js 20 e OpenSSL 3.x com configuracoes de rede/proxy.

---

## SOLUCAO 1: Usar Node.js 18 LTS (RECOMENDADO)

### Passo 1: Desinstalar Node.js 20
1. Painel de Controle > Programas > Desinstalar Node.js

### Passo 2: Instalar Node.js 18 LTS
1. Baixar: https://nodejs.org/dist/v18.20.4/node-v18.20.4-x64.msi
2. Instalar normalmente
3. Reiniciar terminal

### Passo 3: Reinstalar Dependencias
```bash
cd D:\Nexus\wppconnect-server
rm -rf node_modules package-lock.json
npm install
```

---

## SOLUCAO 2: Usar --legacy-openssl-provider (Node.js 20)

### Opcao A: Variavel de Ambiente

**PowerShell:**
```powershell
$env:NODE_OPTIONS="--openssl-legacy-provider"
cd D:\Nexus\wppconnect-server
npm install
```

**CMD:**
```cmd
set NODE_OPTIONS=--openssl-legacy-provider
cd D:\Nexus\wppconnect-server
npm install
```

### Opcao B: Modificar package.json

Editar `package.json`:
```json
{
  "scripts": {
    "start": "node --openssl-legacy-provider server.js",
    "dev": "nodemon --openssl-legacy-provider server.js",
    "install-fix": "cross-env NODE_OPTIONS='--openssl-legacy-provider' npm install"
  }
}
```

Instalar cross-env globalmente:
```bash
npm install -g cross-env
```

Depois:
```bash
npm run install-fix
```

---

## SOLUCAO 3: Instalar Manualmente com Yarn

### Passo 1: Instalar Yarn
```bash
npm install -g yarn
```

### Passo 2: Limpar e Reinstalar
```bash
cd D:\Nexus\wppconnect-server
rm -rf node_modules package-lock.json
yarn install
```

---

## SOLUCAO 4: Usar Proxy/VPN Alternativo

Se o erro e de rede:

```bash
# Desabilitar proxy
npm config delete proxy
npm config delete https-proxy

# Usar registry alternativo
npm config set registry https://registry.npmmirror.com

# Reinstalar
cd D:\Nexus\wppconnect-server
rm -rf node_modules
npm install
```

---

## SOLUCAO 5: Instalacao Offline (ULTIMA OPCAO)

Se nenhuma solucao funcionar, vou criar arquivo com dependencias pre-instaladas.

**Usuario deve informar se chegou neste ponto!**

---

## VERIFICAR INSTALACAO BEM-SUCEDIDA

```bash
cd D:\Nexus\wppconnect-server
node -e "console.log(require('express'))"
```

Se mostrar `[Function: createApplication]` = SUCESSO!

---

## TESTAR SERVIDOR

```bash
cd D:\Nexus\wppconnect-server
npm start
```

Abrir navegador em: http://localhost:3001

Devera mostrar:
```json
{
  "service": "Nexus WPPConnect Server",
  "status": "running",
  "connected": false,
  "phone": null,
  "version": "1.0.0"
}
```

---

## CONTATO

Se nenhuma solucao funcionar, favor informar:
1. Versao do Node.js: `node --version`
2. Versao do NPM: `npm --version`
3. Sistema Operacional
4. Logs completos do erro
