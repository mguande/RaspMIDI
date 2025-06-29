# Script de Deploy Simples para Raspberry Pi
$RASPBERRY_IP = "192.168.15.8"
$RASPBERRY_USER = "matheus"
$RASPBERRY_PASSWORD = "matheus"

Write-Host "🚀 Deploy automático para Raspberry Pi" -ForegroundColor Green

# Deploy do arquivo JavaScript
Write-Host "📁 Deployando app.js..." -ForegroundColor Yellow
$scpCmd = "scp -o StrictHostKeyChecking=no app/web/static/js/app.js ${RASPBERRY_USER}@${RASPBERRY_IP}:/home/${RASPBERRY_USER}/RaspMIDI/app/web/static/js/"
echo $RASPBERRY_PASSWORD | & $scpCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ app.js deployado com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao deployar app.js" -ForegroundColor Red
}

# Reinicia a aplicação
Write-Host "🔄 Reiniciando aplicação..." -ForegroundColor Yellow

# Para o processo atual
$sshCmd = "ssh -o StrictHostKeyChecking=no ${RASPBERRY_USER}@${RASPBERRY_IP} 'pkill -f \"python run.py\"'"
echo $RASPBERRY_PASSWORD | & $sshCmd

Start-Sleep -Seconds 2

# Inicia a aplicação
$startCmd = "ssh -o StrictHostKeyChecking=no ${RASPBERRY_USER}@${RASPBERRY_IP} 'cd /home/${RASPBERRY_USER}/RaspMIDI && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &'"
echo $RASPBERRY_PASSWORD | & $startCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Aplicação reiniciada com sucesso" -ForegroundColor Green
    Write-Host "🌐 Acesse: http://${RASPBERRY_IP}:5000" -ForegroundColor Cyan
} else {
    Write-Host "❌ Erro ao reiniciar aplicação" -ForegroundColor Red
}

Write-Host "🎉 Deploy concluído!" -ForegroundColor Green 