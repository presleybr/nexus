#!/usr/bin/env pwsh
# Script de inicialização do Nexus CRM + Portal Consórcio

Write-Host "============================================================" -ForegroundColor Green
Write-Host "NEXUS CRM - Inicialização Automática" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Verificar se venv existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[OK] Ativando ambiente virtual..." -ForegroundColor Cyan
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "[ERRO] Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "Execute: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Pressione ENTER para sair"
    exit 1
}

# Iniciar sistema
Write-Host ""
Write-Host "[OK] Iniciando sistema..." -ForegroundColor Cyan
Write-Host ""

python start.py

# Verificar erro
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERRO] Sistema encerrou com erro" -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
}
