# Configuração do Chromium/Playwright no Render.com

## Problema

O código de automação Canopus usa **Playwright** com **Chromium** para acessar o portal e baixar boletos. Por padrão, o Render.com não inclui Chromium nos containers, então é necessário configurá-lo manualmente.

## Sintomas de Chromium não instalado

- Erro: `playwright._impl._api_types.Error: Executable doesn't exist`
- Erro: `Browser type chromium not found`
- Endpoint `/api/automation/baixar-boletos-ponto-venda` retorna erro 503
- Log mostra: `❌ Automação Canopus não disponível`

## Soluções para Render

### Opção 1: Adicionar Buildpack do Playwright (Recomendado)

1. No seu serviço Render, vá em **Environment** → **Build Command**
2. Modifique o build command para:

```bash
pip install -r requirements.txt && playwright install --with-deps chromium
```

Isso instalará o Chromium e todas as dependências do sistema necessárias.

### Opção 2: Usar Docker (Mais Controle)

Crie um `Dockerfile` na raiz do projeto:

```dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright e Chromium
RUN playwright install chromium
RUN playwright install-deps

# Copiar código
COPY . .

# Expor porta
EXPOSE 5000

# Comando de start
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "backend.app:app"]
```

Em seguida, configure o Render para usar Docker:
- **Environment** → Selecione "Docker"
- Aponte para o Dockerfile

### Opção 3: Usar headless=True (Limitado)

Se o Chromium ainda não funcionar, você pode tentar rodar em modo headless:

No arquivo `automation_canopus.py`, linha 1123:

```python
async with CanopusAutomation(headless=True) as bot:
```

Isso pode reduzir alguns problemas de dependências gráficas, mas ainda requer Chromium instalado.

## Configurações Adicionais Necessárias

### 1. Variável de Ambiente para Downloads

Adicione no Render em **Environment** → **Environment Variables**:

```
DOWNLOAD_BASE_DIR=/app/automation/canopus/downloads
```

### 2. Credenciais do Canopus

Execute o script de configuração de credenciais:

```bash
python configurar_credenciais_canopus_render.py
```

Isso criará a tabela `credenciais_canopus` e inserirá as credenciais de acesso ao portal Canopus.

### 3. Timeout aumentado

Como o download de boletos pode demorar, aumente o timeout do Gunicorn:

No comando de start do Render:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 600 backend.app:app
```

O `--timeout 600` define 10 minutos de timeout (ajuste conforme necessário).

## Verificar se está funcionando

Após configurar, teste o endpoint:

```bash
curl -X POST https://seu-app.onrender.com/api/automation/baixar-boletos-ponto-venda \
  -H "Content-Type: application/json" \
  -d '{"ponto_venda": "24627", "mes": "DEZEMBRO", "ano": 2025}'
```

Verifique os logs do Render. Você deve ver:

```
🌐 Abrindo Chromium...
✅ Chromium aberto!
🔐 FAZENDO LOGIN NO PONTO 24627
✅ LOGIN REALIZADO COM SUCESSO!
📄 Processando 1/XX: CPF XXXXXXXXX
```

## Problemas Comuns

### "Executable doesn't exist"

**Solução**: Chromium não foi instalado. Use a Opção 1 ou 2 acima.

### "Browser closed unexpectedly"

**Solução**: Faltam dependências do sistema. Use a Opção 2 (Docker) que instala todas as libs necessárias.

### "Timeout waiting for browser to start"

**Solução**: Aumente o timeout do Gunicorn e verifique os recursos do container Render (pode precisar upgrade do plano).

### "Permission denied" ao criar pasta de downloads

**Solução**: Verifique que `DOWNLOAD_BASE_DIR` aponta para `/app/...` (dentro do container) e não para paths do Windows (`D:\...`).

## Limitações do Render Free Tier

- **Ephemeral Storage**: Arquivos baixados serão perdidos ao reiniciar o serviço
- **CPU/RAM**: Chromium consome bastante memória. Pode ser necessário upgrade para plano pago
- **Timeout**: Render pode desligar serviços inativos após 15 minutos no plano gratuito

## Alternativas ao Chromium no Render

Se o Chromium não funcionar bem no Render:

1. **Usar serviço separado**: Rode a automação Canopus em uma VM separada (EC2, DigitalOcean, etc.) e apenas a API Flask no Render
2. **Scheduled Jobs**: Use Render Cron Jobs para rodar downloads periodicamente em vez de sob demanda
3. **Serverless com maior timeout**: AWS Lambda com Playwright layer (mas tem limite de 15 minutos)

## Próximos Passos

1. Escolher uma das opções (recomendo Opção 1 para começar)
2. Executar `configurar_credenciais_canopus_render.py`
3. Testar o endpoint de download
4. Monitorar logs para verificar funcionamento
5. Se necessário, migrar para Docker (Opção 2) para mais controle
