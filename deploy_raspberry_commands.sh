#!/bin/bash

# Script de deploy completo para Raspberry Pi
# Execute estes comandos diretamente no shell do Raspberry Pi

echo "🚀 RaspMIDI - Deploy Completo"
echo "=================================="
echo ""

# Configurações
RASPBERRY_PATH="/home/matheus/RaspMIDI"
GIT_REPO="https://github.com/seu-usuario/RaspMIDI.git"  # Ajuste para seu repositório

# Função para verificar se o comando foi executado com sucesso
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1"
        exit 1
    fi
}

# 1. Parar serviços
echo "🛑 1. Parando serviços..."
echo "   Parando aplicação Flask..."
pkill -f "python run.py" 2>/dev/null
sleep 2
check_status "Aplicação parada"

echo "   Parando serviço systemd (se existir)..."
sudo systemctl stop raspmidi 2>/dev/null
check_status "Serviço systemd parado"

# 2. Navegar para o diretório
echo ""
echo "📁 2. Navegando para o diretório..."
cd "$RASPBERRY_PATH" || exit 1
check_status "Diretório acessado: $(pwd)"

# 3. Backup dos arquivos importantes
echo ""
echo "💾 3. Fazendo backup dos arquivos importantes..."
mkdir -p backup/$(date +%Y%m%d_%H%M%S)
cp -r app/web/static backup/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null
cp -r logs backup/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null
cp *.json backup/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null
check_status "Backup criado"

# 4. Atualizar do Git
echo ""
echo "📥 4. Atualizando do Git..."
if [ -d ".git" ]; then
    echo "   Repositório Git encontrado, fazendo pull..."
    git stash 2>/dev/null
    git pull origin main
    check_status "Git pull realizado"
else
    echo "   Repositório Git não encontrado, clonando..."
    cd ..
    rm -rf RaspMIDI
    git clone "$GIT_REPO" RaspMIDI
    cd RaspMIDI
    check_status "Repositório clonado"
fi

# 5. Atualizar dependências Python
echo ""
echo "🐍 5. Atualizando dependências Python..."
if [ -d "venv" ]; then
    echo "   Ambiente virtual encontrado, ativando..."
    source venv/bin/activate
else
    echo "   Criando novo ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
fi

echo "   Atualizando pip..."
pip install --upgrade pip
check_status "Pip atualizado"

echo "   Instalando dependências..."
pip install -r requirements.txt
check_status "Dependências instaladas"

# 6. Configurar permissões
echo ""
echo "🔧 6. Configurando permissões..."
sudo usermod -a -G audio matheus 2>/dev/null
sudo chmod 666 /dev/snd/* 2>/dev/null
check_status "Permissões configuradas"

# 7. Criar diretórios necessários
echo ""
echo "📁 7. Criando diretórios necessários..."
mkdir -p logs
mkdir -p app/web/static/css
mkdir -p app/web/static/js
check_status "Diretórios criados"

# 8. Verificar arquivos de configuração
echo ""
echo "⚙️ 8. Verificando configurações..."
if [ ! -f "raspberry_config.json" ]; then
    echo "   Criando arquivo de configuração..."
    cat > raspberry_config.json << EOF
{
  "midi": {
    "input_device": "Chocolate MIDI In",
    "output_device": "Zoom G3X MIDI Out",
    "auto_detect": true,
    "fallback_devices": [
      "USB MIDI Device",
      "MIDI Device",
      "USB Audio Device"
    ]
  },
  "bluetooth": {
    "enabled": false,
    "device_name": "RaspMIDI",
    "pin": "1234"
  },
  "cache": {
    "timeout": 300,
    "max_size": 100
  },
  "raspberry_pi": {
    "wifi_hotspot": true,
    "autostart": true,
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "log_level": "INFO",
    "log_file": "logs/raspmidi.log",
    "max_log_size": "10MB",
    "backup_count": 5
  },
  "web": {
    "title": "RaspMIDI Controller",
    "theme": "dark",
    "auto_refresh": true,
    "refresh_interval": 5000
  },
  "security": {
    "enable_auth": false,
    "username": "admin",
    "password": "raspmidi2024"
  },
  "performance": {
    "max_connections": 10,
    "timeout": 30,
    "keep_alive": true
  }
}
EOF
    check_status "Arquivo de configuração criado"
else
    echo "   Arquivo de configuração já existe"
fi

# 9. Iniciar aplicação
echo ""
echo "🚀 9. Iniciando aplicação..."
echo "   Iniciando Flask app..."
nohup python run.py > logs/app.log 2>&1 &
sleep 3
check_status "Aplicação iniciada"

# 10. Verificar status
echo ""
echo "🔍 10. Verificando status..."
if pgrep -f "python run.py" > /dev/null; then
    echo "✅ Aplicação está rodando"
    echo "📋 Processos:"
    ps aux | grep "python run.py" | grep -v grep
else
    echo "❌ Aplicação não está rodando"
    echo "📋 Logs:"
    tail -20 logs/app.log
    exit 1
fi

# 11. Verificar porta
echo ""
echo "🌐 11. Verificando porta..."
if netstat -tlnp | grep ":5000" > /dev/null; then
    echo "✅ Porta 5000 está ativa"
    echo "📍 Acesse: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "❌ Porta 5000 não está ativa"
fi

# 12. Habilitar serviço systemd (opcional)
echo ""
echo "⚙️ 12. Configurando serviço systemd..."
if [ -f "raspmidi.service" ]; then
    sudo cp raspmidi.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable raspmidi
    echo "✅ Serviço systemd configurado"
else
    echo "⚠️ Arquivo raspmidi.service não encontrado"
fi

echo ""
echo "🎉 Deploy concluído com sucesso!"
echo "=================================="
echo "🌐 Acesse: http://$(hostname -I | awk '{print $1}'):5000"
echo "📋 Logs: tail -f logs/app.log"
echo "🔄 Reiniciar: pkill -f 'python run.py' && nohup python run.py > logs/app.log 2>&1 &" 