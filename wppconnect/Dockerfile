# Dockerfile leve para WPPConnect no Render
# Baseado no iniciar.bat do localhost
FROM node:18-alpine

# Instalar apenas dependências essenciais para WPPConnect
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# Configurar Puppeteer para usar Chromium do Alpine
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências (production only)
RUN npm ci --omit=dev --ignore-scripts 2>&1 | grep -v "deprecated" || true

# Copiar código do servidor
COPY . .

# Expor porta
EXPOSE 10000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
  CMD node -e "require('http').get('http://localhost:10000', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Iniciar servidor (sem Playwright, apenas WPPConnect)
CMD ["node", "server.js"]
