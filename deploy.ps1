# Script de Deploy Automático para Raspberry Pi
# Configurações
$RASPBERRY_IP = "192.168.15.8"
$RASPBERRY_USER = "matheus"
$RASPBERRY_PASSWORD = "matheus"
$RASPBERRY_PATH = "/home/$RASPBERRY_USER/RaspMIDI"

Write-Host "🚀 Deploy automático para Raspberry Pi" -ForegroundColor Green
Write-Host "📍 IP: $RASPBERRY_IP" -ForegroundColor Cyan
Write-Host "👤 Usuário: $RASPBERRY_USER" -ForegroundColor Cyan
Write-Host ""

# Função para executar comando SSH
function Invoke-SSHCommand {
    param(
        [string]$Command
    )
    
    $sshCmd = "ssh -o StrictHostKeyChecking=no $RASPBERRY_USER@$RASPBERRY_IP `"$Command`""
    
    # Cria um arquivo temporário com a senha
    $tempFile = [System.IO.Path]::GetTempFileName()
    "echo '$RASPBERRY_PASSWORD' | $sshCmd" | Out-File -FilePath $tempFile -Encoding ASCII
    
    try {
        $result = Invoke-Expression "& $tempFile"
        return $true, $result, ""
    }
    catch {
        return $false, "", $_.Exception.Message
    }
    finally {
        if (Test-Path $tempFile) {
            Remove-Item $tempFile -Force
        }
    }
}

# Função para copiar arquivo
function Copy-FileToRaspberry {
    param(
        [string]$LocalFile,
        [string]$RemotePath
    )
    
    Write-Host "📁 Deployando $LocalFile..." -ForegroundColor Yellow
    
    if (Test-Path $LocalFile) {
        $scpCmd = "scp -o StrictHostKeyChecking=no `"$LocalFile`" $RASPBERRY_USER@$RASPBERRY_IP`:$RemotePath"
        
        # Cria um arquivo temporário com a senha
        $tempFile = [System.IO.Path]::GetTempFileName()
        "echo '$RASPBERRY_PASSWORD' | $scpCmd" | Out-File -FilePath $tempFile -Encoding ASCII
        
        try {
            $result = Invoke-Expression "& $tempFile"
            Write-Host "✅ $LocalFile deployado com sucesso" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "❌ Erro ao deployar $LocalFile : $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
        finally {
            if (Test-Path $tempFile) {
                Remove-Item $tempFile -Force
            }
        }
    }
    else {
        Write-Host "⚠️ Arquivo não encontrado: $LocalFile" -ForegroundColor Yellow
        return $false
    }
}

# Deploy dos arquivos principais
$filesToDeploy = @(
    @{Local = "app/web/static/js/app.js"; Remote = "$RASPBERRY_PATH/app/web/static/js/"},
    @{Local = "app/main.py"; Remote = "$RASPBERRY_PATH/app/"},
    @{Local = "run.py"; Remote = "$RASPBERRY_PATH/"}
)

$allSuccess = $true
foreach ($file in $filesToDeploy) {
    if (-not (Copy-FileToRaspberry -LocalFile $file.Local -RemotePath $file.Remote)) {
        $allSuccess = $false
    }
}

if ($allSuccess) {
    Write-Host "🔄 Reiniciando aplicação..." -ForegroundColor Yellow
    
    # Para o processo atual
    $success, $output, $error = Invoke-SSHCommand "pkill -f 'python run.py'"
    if ($success) {
        Write-Host "✅ Processo anterior finalizado" -ForegroundColor Green
    }
    
    # Aguarda um pouco
    Start-Sleep -Seconds 2
    
    # Inicia a aplicação
    $startCmd = "cd $RASPBERRY_PATH && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &"
    $success, $output, $error = Invoke-SSHCommand $startCmd
    
    if ($success) {
        Write-Host "✅ Aplicação reiniciada com sucesso" -ForegroundColor Green
        Write-Host "🌐 Acesse: http://$RASPBERRY_IP`:5000" -ForegroundColor Cyan
    }
    else {
        Write-Host "❌ Erro ao reiniciar aplicação: $error" -ForegroundColor Red
    }
    
    # Aguarda um pouco e verifica o status
    Start-Sleep -Seconds 3
    
    Write-Host "🔍 Verificando status da aplicação..." -ForegroundColor Yellow
    $success, $output, $error = Invoke-SSHCommand "ps aux | grep 'python run.py' | grep -v grep"
    
    if ($success -and $output) {
        Write-Host "✅ Aplicação está rodando" -ForegroundColor Green
        Write-Host "📋 Processos:" -ForegroundColor Cyan
        Write-Host $output
    }
    else {
        Write-Host "❌ Aplicação não está rodando" -ForegroundColor Red
    }
    
    Write-Host "`n🎉 Deploy concluído!" -ForegroundColor Green
}
else {
    Write-Host "`n❌ Deploy falhou!" -ForegroundColor Red
} 