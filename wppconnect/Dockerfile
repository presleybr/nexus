# Dockerfile leve para WPPConnect no Render
# Baseado no iniciar.bat do localhost
FROM node:18-alpine

# Instalar dependências essenciais para WPPConnect + Chromium
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    font-noto-emoji \
    dbus \
    udev \
    && rm -rf /var/cache/apk/*

# Verificar e configurar Chromium
RUN which chromium-browser || which chromium || echo "Chromium not found" \
    && chmod +x /usr/bin/chromium-browser 2>/dev/null || true \
    && ln -sf /usr/bin/chromium-browser /usr/bin/chromium 2>/dev/null || true

# Configurar Puppeteer para usar Chromium do Alpine
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    CHROME_BIN=/usr/bin/chromium-browser \
    NODE_ENV=production

# Criar pasta para tokens/sessões do WhatsApp com permissões corretas
RUN mkdir -p /app/tokens && chmod -R 777 /app/tokens

WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências (production only)
# Usar npm install ao invés de npm ci pois package-lock pode estar desatualizado
RUN npm install --omit=dev --ignore-scripts 2>&1 | grep -v "deprecated" || true

# Copiar código do servidor
COPY . .

# Executar script de detecção do Chromium e salvar path
RUN node detect-chromium.js || echo "Chromium detection script failed"

# Expor porta
EXPOSE 10000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s \
  CMD node -e "require('http').get('http://localhost:10000', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Iniciar servidor (sem Playwright, apenas WPPConnect)
CMD ["node", "server.js"]
