# Script PowerShell para preparar repositório GitHub

Write-Host "🚀 Preparando Nexus CRM para GitHub..." -ForegroundColor Green

# 1. Verificar se Git está instalado
try {
    git --version | Out-Null
} catch {
    Write-Host "❌ Git não encontrado! Instale em: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

# 2. Inicializar Git
if (-not (Test-Path ".git")) {
    Write-Host "📦 Inicializando Git..." -ForegroundColor Yellow
    git init
    git branch -M main
}

# 3. Configurar remote
Write-Host "🔗 Configurando remote GitHub..." -ForegroundColor Yellow
git remote remove origin 2>$null
git remote add origin https://github.com/presleybr/nexus.git

# 4. Adicionar arquivos
Write-Host "📝 Adicionando arquivos..." -ForegroundColor Yellow
git add .

# 5. Criar commit
Write-Host "✅ Criando commit..." -ForegroundColor Yellow
git commit -m "feat: Preparação para deploy no Render.com

- Adiciona Dockerfile para Render
- Configura Playwright/Chromium
- Cria render.yaml para deploy automático
- Adiciona .env.example com variáveis documentadas
- Cria migrations SQL consolidadas
- Adiciona README_RENDER.md com guia completo
- Configura .gitignore para PDFs e logs
"

Write-Host ""
Write-Host "📋 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Faça push para o GitHub:" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Vá para https://dashboard.render.com" -ForegroundColor White
Write-Host ""
Write-Host "3. Crie PostgreSQL Database (Free ou Starter)" -ForegroundColor White
Write-Host ""
Write-Host "4. Execute migrations no banco" -ForegroundColor White
Write-Host ""
Write-Host "5. Crie Web Service apontando para o repositório" -ForegroundColor White
Write-Host ""
Write-Host "6. Configure variáveis de ambiente secretas" -ForegroundColor White
Write-Host ""
Write-Host "7. Aguarde o build (10-15 min primeira vez)" -ForegroundColor White
Write-Host ""
Write-Host "✨ Pronto! Sistema estará rodando no Render.com" -ForegroundColor Green
Write-Host ""
