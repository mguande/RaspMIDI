# Script de deploy para Raspberry Pi usando PowerShell
# Configuração
$RASPBERRY_IP = "192.168.15.8"
$RASPBERRY_USER = "pi"
$RASPBERRY_PASS = "raspberry"
$PROJECT_DIR = "/home/pi/RaspMIDI"

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    switch ($Type) {
        "SUCCESS" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "ERROR" { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "[$timestamp] ⚠️ $Message" -ForegroundColor Yellow }
        "INFO" { Write-Host "[$timestamp] ℹ️ $Message" -ForegroundColor Cyan }
    }
}

function Run-SSHCommand {
    param([string]$Command, [string]$Description)
    
    Write-Status $Description "INFO"
    Write-Host "📝 Comando: $Command" -ForegroundColor Gray
    
    try {
        # Executa o comando SSH
        $sshCommand = "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $RASPBERRY_USER@$RASPBERRY_IP `"$Command`""
        
        $result = Invoke-Expression $sshCommand 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Comando executado com sucesso" "SUCCESS"
            if ($result) {
                Write-Host "✅ Saída: $result" -ForegroundColor Green
            }
            return $true
        } else {
            Write-Status "Comando falhou com código $LASTEXITCODE" "ERROR"
            if ($result) {
                Write-Host "❌ Erro: $result" -ForegroundColor Red
            }
            return $false
        }
    }
    catch {
        Write-Status "Erro ao executar comando: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-Connectivity {
    Write-Status "Testando conectividade com Raspberry Pi..." "INFO"
    
    try {
        $ping = Test-Connection -ComputerName $RASPBERRY_IP -Count 1 -Quiet
        if ($ping) {
            Write-Status "Raspberry Pi está acessível" "SUCCESS"
            return $true
        } else {
            Write-Status "Raspberry Pi não está acessível" "ERROR"
            return $false
        }
    }
    catch {
        Write-Status "Erro ao testar conectividade: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Deploy-RaspberryPi {
    Write-Host "🚀 Iniciando deploy para Raspberry Pi..." -ForegroundColor Magenta
    Write-Host "📍 IP: $RASPBERRY_IP" -ForegroundColor White
    Write-Host "👤 Usuário: $RASPBERRY_USER" -ForegroundColor White
    Write-Host "📁 Diretório: $PROJECT_DIR" -ForegroundColor White
    
    # Testa conectividade
    if (-not (Test-Connectivity)) {
        Write-Status "Não foi possível conectar ao Raspberry Pi" "ERROR"
        return $false
    }
    
    # 1. Para o serviço
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "🛑 PARANDO SERVIÇO" -ForegroundColor Yellow
    Write-Host "="*50 -ForegroundColor Gray
    
    $stopCmd = "sudo systemctl stop raspmidi.service"
    if (-not (Run-SSHCommand $stopCmd "Parando serviço raspmidi")) {
        Write-Status "Aviso: Não foi possível parar o serviço" "WARNING"
    }
    
    # 2. Atualiza o código
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "📥 ATUALIZANDO CÓDIGO" -ForegroundColor Yellow
    Write-Host "="*50 -ForegroundColor Gray
    
    $updateCmd = "cd $PROJECT_DIR && git pull origin main"
    if (-not (Run-SSHCommand $updateCmd "Atualizando código via git")) {
        Write-Status "Falha ao atualizar código" "ERROR"
        return $false
    }
    
    # 3. Instala dependências
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "📦 INSTALANDO DEPENDÊNCIAS" -ForegroundColor Yellow
    Write-Host "="*50 -ForegroundColor Gray
    
    $depsCmd = "cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"
    if (-not (Run-SSHCommand $depsCmd "Instalando dependências Python")) {
        Write-Status "Falha ao instalar dependências" "ERROR"
        return $false
    }
    
    # 4. Reinicia o serviço
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "🔄 REINICIANDO SERVIÇO" -ForegroundColor Yellow
    Write-Host "="*50 -ForegroundColor Gray
    
    $startCmd = "sudo systemctl start raspmidi.service"
    if (-not (Run-SSHCommand $startCmd "Reiniciando serviço raspmidi")) {
        Write-Status "Falha ao reiniciar serviço" "ERROR"
        return $false
    }
    
    # 5. Verifica status
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "✅ VERIFICANDO STATUS" -ForegroundColor Yellow
    Write-Host "="*50 -ForegroundColor Gray
    
    $statusCmd = "sudo systemctl status raspmidi.service"
    Run-SSHCommand $statusCmd "Verificando status do serviço"
    
    # 6. Testa conectividade da API
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "🌐 TESTANDO CONECTIVIDADE" -ForegroundColor Yellow
    Write-Host "="*50 -ForegroundColor Gray
    
    Write-Status "Aguardando 5 segundos para o serviço inicializar..." "INFO"
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-WebRequest -Uri "http://$RASPBERRY_IP`:5000/api/status" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Status "API está respondendo!" "SUCCESS"
        } else {
            Write-Status "API retornou status $($response.StatusCode)" "WARNING"
        }
    }
    catch {
        Write-Status "API não está respondendo: $($_.Exception.Message)" "ERROR"
    }
    
    Write-Host "`n" + "="*50 -ForegroundColor Gray
    Write-Host "🎉 DEPLOY CONCLUÍDO!" -ForegroundColor Green
    Write-Host "="*50 -ForegroundColor Gray
    Write-Host "🌐 Acesse: http://$RASPBERRY_IP`:5000" -ForegroundColor Cyan
    
    return $true
}

# Executa o deploy
try {
    $success = Deploy-RaspberryPi
    if ($success) {
        Write-Status "Deploy realizado com sucesso!" "SUCCESS"
        exit 0
    } else {
        Write-Status "Deploy falhou!" "ERROR"
        exit 1
    }
}
catch {
    Write-Status "Erro inesperado: $($_.Exception.Message)" "ERROR"
    exit 1
} 