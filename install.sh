#!/bin/bash

# RaspMIDI - Script de Instalação
# Este script instala e configura o RaspMIDI no Raspberry Pi

set -e

echo "🎵 RaspMIDI - Instalação"
echo "=========================="

# Verifica se está rodando no Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Aviso: Este script foi projetado para Raspberry Pi"
    read -p "Continuar mesmo assim? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Atualiza o sistema
echo "📦 Atualizando sistema..."
sudo apt update
sudo apt upgrade -y

# Instala dependências do sistema
echo "🔧 Instalando dependências do sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    bluetooth \
    bluez \
    libbluetooth-dev \
    portaudio19-dev \
    python3-dev \
    build-essential

# Instala dependências MIDI
echo "🎹 Instalando dependências MIDI..."
sudo apt install -y \
    timidity \
    timidity-daemon \
    libasound2-dev \
    libjack-jackd2-dev

# Cria diretório do projeto
PROJECT_DIR="/home/pi/RaspMIDI"
echo "📁 Criando diretório do projeto: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"

# Copia arquivos do projeto (assumindo que está no diretório atual)
echo "📋 Copiando arquivos do projeto..."
cp -r . "$PROJECT_DIR/"

# Define permissões
echo "🔐 Configurando permissões..."
sudo chown -R pi:pi "$PROJECT_DIR"
chmod +x "$PROJECT_DIR/run.py"

# Cria ambiente virtual Python
echo "🐍 Criando ambiente virtual Python..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# Instala dependências Python
echo "📦 Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configura Bluetooth
echo "🔵 Configurando Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Adiciona usuário ao grupo bluetooth
sudo usermod -a -G bluetooth pi

# Configura serviço systemd
echo "⚙️ Configurando serviço systemd..."
sudo cp raspmidi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raspmidi.service

# Cria diretórios necessários
echo "📂 Criando diretórios..."
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"

# Configura permissões finais
sudo chown -R pi:pi "$PROJECT_DIR"

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "🎵 Para iniciar o RaspMIDI:"
echo "   sudo systemctl start raspmidi"
echo ""
echo "🌐 Acesse a interface web em:"
echo "   http://seu-raspberry-pi:5000"
echo ""
echo "📱 Use seu celular para controle remoto!"
echo ""
echo "📋 Comandos úteis:"
echo "   sudo systemctl start raspmidi    # Iniciar serviço"
echo "   sudo systemctl stop raspmidi     # Parar serviço"
echo "   sudo systemctl status raspmidi   # Verificar status"
echo "   sudo journalctl -u raspmidi -f   # Ver logs"
echo ""
echo "🎛️ Conecte o Zoom G3X e Chocolate MIDI via USB"
echo "🔵 Configure o Bluetooth para o Chocolate (opcional)"
echo ""
echo "🎉 RaspMIDI está pronto para uso!" 