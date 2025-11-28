FROM python:3.13-slim

# Instalar dependências do sistema para Playwright e PostgreSQL
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copiar código da aplicação
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY automation/ ./automation/

# Criar diretórios necessários
RUN mkdir -p automation/canopus/downloads/Danner \
    automation/canopus/excel_files \
    boletos \
    logs

# Variáveis de ambiente padrão para logs em tempo real
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV FLASK_APP=backend/app.py
ENV PORT=5000

# Expor porta
EXPOSE 5000

# Comando de inicialização (com -u para unbuffered)
# Redirecionar stderr para stdout para capturar TODOS os logs (incluindo Chromium)
CMD ["sh", "-c", "python -u backend/app.py 2>&1"]
