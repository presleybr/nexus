#!/bin/bash
# Script para preparar repositório para GitHub

echo "🚀 Preparando Nexus CRM para GitHub..."

# 1. Inicializar Git
if [ ! -d ".git" ]; then
    echo "📦 Inicializando Git..."
    git init
    git branch -M main
fi

# 2. Configurar remote
echo "🔗 Configurando remote GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/presleybr/nexus.git

# 3. Adicionar arquivos
echo "📝 Adicionando arquivos..."
git add .

# 4. Criar commit
echo "✅ Criando commit..."
git commit -m "feat: Preparação para deploy no Render.com

- Adiciona Dockerfile para Render
- Configura Playwright/Chromium
- Cria render.yaml para deploy automático
- Adiciona .env.example com variáveis documentadas
- Cria migrations SQL consolidadas
- Adiciona README_RENDER.md com guia completo
- Configura .gitignore para PDFs e logs
"

echo "
📋 PRÓXIMOS PASSOS:

1. Faça push para o GitHub:
   git push -u origin main

2. Vá para https://dashboard.render.com

3. Crie PostgreSQL Database (Free ou Starter)

4. Execute migrations no banco

5. Crie Web Service apontando para o repositório

6. Configure variáveis de ambiente secretas

7. Aguarde o build (10-15 min primeira vez)

✨ Pronto! Sistema estará rodando no Render.com
"
