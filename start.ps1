Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RaspMIDI - Sistema de Controle MIDI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se o ambiente virtual existe
if (-not (Test-Path "venv")) {
    Write-Host "Criando ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Ambiente virtual criado com sucesso!" -ForegroundColor Green
    Write-Host ""
}

# Ativar ambiente virtual
Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Verificar se as dependências estão instaladas
Write-Host "Verificando dependências..." -ForegroundColor Yellow
try {
    python -c "import flask_cors" 2>$null
    Write-Host "Dependências já estão instaladas." -ForegroundColor Green
} catch {
    Write-Host "Instalando dependências..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "Dependências instaladas com sucesso!" -ForegroundColor Green
}
Write-Host ""

# Iniciar o sistema
Write-Host "Iniciando RaspMIDI..." -ForegroundColor Yellow
Write-Host ""
python run.py

Read-Host "Pressione Enter para sair" 