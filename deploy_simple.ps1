# Script de deploy simples para Raspberry Pi
# Configuração
$RASPBERRY_IP = "192.168.15.8"
$RASPBERRY_USER = "matheus"
$PROJECT_DIR = "/home/matheus/RaspMIDI"

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    switch ($Type) {
        "SUCCESS" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "ERROR" { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "[$timestamp] ⚠️ $Message" -ForegroundColor Yellow }
        default { Write-Host "[$timestamp] ℹ️ $Message" -ForegroundColor Cyan }
    }
}

function Deploy-RaspberryPi {
    Write-Host "🚀 Iniciando deploy para Raspberry Pi..." -ForegroundColor Magenta
    Write-Host "📍 IP: $RASPBERRY_IP" -ForegroundColor White
    Write-Host "👤 Usuário: $RASPBERRY_USER" -ForegroundColor White
    Write-Host "📁 Diretório: $PROJECT_DIR" -ForegroundColor White
    
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "📋 COMANDOS PARA EXECUTAR MANUALMENTE" -ForegroundColor Yellow
    Write-Host "="*50 -ForegroundColor Gray
    
    Write-Host "`n1️⃣ Parar o serviço:" -ForegroundColor Cyan
    Write-Host "ssh $RASPBERRY_USER@$RASPBERRY_IP 'sudo systemctl stop raspmidi.service'" -ForegroundColor White
    
    Write-Host "`n2️⃣ Atualizar código:" -ForegroundColor Cyan
    Write-Host "ssh $RASPBERRY_USER@$RASPBERRY_IP 'cd $PROJECT_DIR && git pull origin main'" -ForegroundColor White
    
    Write-Host "`n3️⃣ Instalar dependências:" -ForegroundColor Cyan
    Write-Host "ssh $RASPBERRY_USER@$RASPBERRY_IP 'cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt'" -ForegroundColor White
    
    Write-Host "`n4️⃣ Reiniciar serviço:" -ForegroundColor Cyan
    Write-Host "ssh $RASPBERRY_USER@$RASPBERRY_IP 'sudo systemctl start raspmidi.service'" -ForegroundColor White
    
    Write-Host "`n5️⃣ Verificar status:" -ForegroundColor Cyan
    Write-Host "ssh $RASPBERRY_USER@$RASPBERRY_IP 'sudo systemctl status raspmidi.service'" -ForegroundColor White
    
    Write-Host "`n6️⃣ Testar API:" -ForegroundColor Cyan
    Write-Host "curl http://$RASPBERRY_IP`:5000/api/status" -ForegroundColor White
    
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "🌐 Acesse: http://$RASPBERRY_IP`:5000" -ForegroundColor Cyan
    Write-Host "="*50 -ForegroundColor Gray
    
    Write-Host "`n💡 Dica: Execute os comandos um por vez no terminal" -ForegroundColor Yellow
}

# Executa o script
Deploy-RaspberryPi 