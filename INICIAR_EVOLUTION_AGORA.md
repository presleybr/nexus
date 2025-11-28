# 🚀 INICIAR EVOLUTION API - PASSO A PASSO

## ❌ PROBLEMA IDENTIFICADO

O Evolution API **NÃO ESTÁ RODANDO** na porta 8080.

O Flask está tentando conectar, mas não encontra o serviço:
```
Failed to establish a new connection: [WinError 10061]
```

---

## ✅ SOLUÇÃO: INICIAR EVOLUTION API

### Opção 1: Script Automático (RÁPIDO)

1. **Abra um novo Prompt de Comando (CMD)** como Administrador
2. Execute:
```cmd
D:\Nexus\evolution-api\start-evolution.bat
```

### Opção 2: Manual (SE SCRIPT FALHAR)

1. **Abra Docker Desktop** (se não estiver aberto)
   - Aguarde até ver: "Docker Desktop is running"

2. **Abra Prompt de Comando (CMD)** como Administrador

3. **Execute os comandos:**
```cmd
cd D:\Nexus\evolution-api

REM Tente primeiro (Docker versão nova):
docker compose up -d

REM Se der erro, tente (Docker versão antiga):
docker-compose up -d
```

4. **Aguarde aparecer:**
```
✔ Container nexus_evolution_api  Started
```

5. **Aguarde 10-15 segundos** (container precisa inicializar)

6. **Verifique se está rodando:**
```cmd
docker ps
```

Deve aparecer algo como:
```
CONTAINER ID   IMAGE                          STATUS          PORTS
xxxxx          atendai/evolution-api:latest   Up 10 seconds   0.0.0.0:8080->8080/tcp
```

7. **Teste no navegador:**
```
http://localhost:8080
```

---

## 🔍 VERIFICAR STATUS

### Ver containers rodando:
```cmd
docker ps
```

### Ver logs em tempo real:
```cmd
cd D:\Nexus\evolution-api
docker compose logs -f
```
(Pressione CTRL+C para sair)

### Verificar se Evolution API responde:
```cmd
curl http://localhost:8080
```

---

## 🔧 TROUBLESHOOTING

### Erro: "docker compose não é reconhecido"

**Solução 1:** Verifique se Docker Desktop está rodando
- Abra Docker Desktop
- Aguarde inicializar completamente

**Solução 2:** Use `docker-compose` (com hífen):
```cmd
docker-compose up -d
```

**Solução 3:** Reinstale Docker Desktop
- Download: https://www.docker.com/products/docker-desktop/

### Erro: "Porta 8080 já está em uso"

**Solução:** Matar processo na porta 8080
```cmd
REM Ver o que está usando a porta
netstat -ano | findstr :8080

REM Exemplo de resultado:
REM TCP    0.0.0.0:8080    0.0.0.0:0    LISTENING    12345

REM Matar o processo (substitua 12345 pelo PID real)
taskkill /PID 12345 /F

REM Agora tente iniciar novamente
docker compose up -d
```

### Container não inicia

**Ver logs de erro:**
```cmd
cd D:\Nexus\evolution-api
docker compose logs
```

**Recriar container:**
```cmd
docker compose down
docker compose up -d
```

### PostgreSQL não conecta

**Verificar se PostgreSQL está rodando:**
```cmd
REM Abrir serviços do Windows
services.msc

REM Procure por "postgresql" e verifique se está "Em execução"
```

---

## ✅ APÓS EVOLUTION API INICIAR

1. **Recarregue a página do Nexus CRM:**
   - http://localhost:5000/crm/whatsapp

2. **Clique em "Conectar WhatsApp"**

3. **Escaneie o QR Code**

4. **Aguarde conexão**

5. **Pronto!** 🎉

---

## 📊 VERIFICAÇÃO FINAL

Execute estes comandos para confirmar que tudo está funcionando:

```cmd
REM 1. Docker está rodando?
docker --version

REM 2. Container Evolution API está UP?
docker ps | findstr evolution

REM 3. Evolution API responde?
curl http://localhost:8080

REM 4. PostgreSQL está acessível?
REM (se tiver psql instalado)
psql -h localhost -p 5434 -U postgres -d nexus_crm -c "SELECT 1"
```

---

## 🎯 PRÓXIMOS PASSOS

Após Evolution API iniciar:

1. ✅ Evolution API rodando na porta 8080
2. ✅ Flask já está rodando na porta 5000
3. ✅ Acessar: http://localhost:5000/crm/whatsapp
4. ✅ Conectar WhatsApp via QR Code
5. ✅ Testar envio de mensagem

---

## 📞 COMANDOS ÚTEIS

```cmd
REM Ver logs em tempo real
docker compose logs -f

REM Parar Evolution API
docker compose down

REM Reiniciar Evolution API
docker compose restart

REM Ver status de todos containers
docker ps -a

REM Remover container e recriar
docker compose down
docker compose up -d --force-recreate

REM Ver uso de recursos
docker stats
```

---

## 🚀 EXECUÇÃO RÁPIDA

Se tiver pressa, cole isto no CMD como Administrador:

```cmd
cd D:\Nexus\evolution-api && docker compose up -d && timeout /t 15 && echo ✅ Evolution API iniciado! Acesse: http://localhost:8080
```

---

**IMPORTANTE:** O Flask já está rodando e esperando o Evolution API. Assim que você iniciar o Evolution API, tudo vai funcionar automaticamente! 🎉
