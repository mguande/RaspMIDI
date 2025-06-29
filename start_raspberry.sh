#!/bin/bash

# RaspMIDI - Script de inicialização para Raspberry Pi
# Este script configura o ambiente e inicia a aplicação

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log colorido
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Diretório do projeto
PROJECT_DIR="/home/matheus/RaspMIDI"
LOG_DIR="$PROJECT_DIR/logs"
CONFIG_FILE="$PROJECT_DIR/config.json"

# Criar diretório de logs se não existir
mkdir -p "$LOG_DIR"

# Função para verificar se o Raspberry Pi está conectado à internet
check_internet() {
    if ping -c 1 8.8.8.8 &> /dev/null; then
        log "Internet disponível"
        return 0
    else
        warn "Sem conexão com internet"
        return 1
    fi
}

# Função para verificar dispositivos MIDI
check_midi_devices() {
    log "Verificando dispositivos MIDI..."
    
    if command -v aconnect &> /dev/null; then
        aconnect -l
    else
        warn "aconnect não encontrado"
    fi
    
    if [ -d "/proc/asound/card*" ]; then
        ls -la /proc/asound/card*/midi*
    fi
}

# Função para configurar permissões
setup_permissions() {
    log "Configurando permissões..."
    
    # Adicionar usuário ao grupo audio
    sudo usermod -a -G audio matheus
    
    # Configurar permissões para dispositivos de áudio
    sudo chmod 666 /dev/snd/* 2>/dev/null || true
    
    # Configurar permissões para dispositivos MIDI
    sudo chmod 666 /dev/snd/midi* 2>/dev/null || true
}

# Função para ativar ambiente virtual
activate_venv() {
    log "Ativando ambiente virtual..."
    
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        error "Ambiente virtual não encontrado"
        return 1
    fi
    
    source "$PROJECT_DIR/venv/bin/activate"
    log "Ambiente virtual ativado"
}

# Função para instalar/atualizar dependências
install_dependencies() {
    log "Verificando dependências..."
    
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        error "requirements.txt não encontrado"
        return 1
    fi
    
    pip install -r "$PROJECT_DIR/requirements.txt"
    log "Dependências instaladas/atualizadas"
}

# Função para inicializar banco de dados
init_database() {
    log "Inicializando banco de dados..."
    
    python -c "from app.database.database import init_db; init_db()" 2>/dev/null || {
        warn "Falha ao inicializar banco de dados"
    }
}

# Função para verificar configuração
check_config() {
    log "Verificando configuração..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        warn "Arquivo de configuração não encontrado, criando padrão..."
        cp "$PROJECT_DIR/raspberry_config.json" "$CONFIG_FILE" 2>/dev/null || {
            error "Não foi possível criar arquivo de configuração"
            return 1
        }
    fi
    
    log "Configuração verificada"
}

# Função para parar aplicação anterior
stop_previous_app() {
    log "Verificando aplicação anterior..."
    
    pkill -f "python.*run.py" 2>/dev/null || true
    sleep 2
}

# Função para iniciar aplicação
start_app() {
    log "Iniciando aplicação RaspMIDI..."
    
    cd "$PROJECT_DIR"
    
    # Iniciar em background com log
    nohup python run.py > "$LOG_DIR/raspmidi_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
    
    APP_PID=$!
    echo $APP_PID > "$PROJECT_DIR/raspmidi.pid"
    
    log "Aplicação iniciada com PID: $APP_PID"
    
    # Aguardar um pouco e verificar se está rodando
    sleep 3
    if kill -0 $APP_PID 2>/dev/null; then
        log "Aplicação está rodando corretamente"
        return 0
    else
        error "Falha ao iniciar aplicação"
        return 1
    fi
}

# Função para mostrar status
show_status() {
    log "Status da aplicação:"
    
    if [ -f "$PROJECT_DIR/raspmidi.pid" ]; then
        PID=$(cat "$PROJECT_DIR/raspmidi.pid")
        if kill -0 $PID 2>/dev/null; then
            echo "✅ Aplicação rodando (PID: $PID)"
        else
            echo "❌ Aplicação não está rodando"
        fi
    else
        echo "❌ PID file não encontrado"
    fi
    
    # Verificar porta
    if netstat -tlnp | grep :5000 > /dev/null; then
        echo "✅ Porta 5000 ativa"
    else
        echo "❌ Porta 5000 não está ativa"
    fi
    
    # Verificar logs
    echo "📋 Logs disponíveis em: $LOG_DIR"
    ls -la "$LOG_DIR"/*.log 2>/dev/null | tail -5 || echo "Nenhum log encontrado"
}

# Função para mostrar informações do sistema
show_system_info() {
    log "Informações do sistema:"
    
    echo "🖥️  Modelo: $(cat /proc/device-tree/model 2>/dev/null || echo 'Desconhecido')"
    echo "💾 Memória: $(free -h | grep Mem | awk '{print $2}')"
    echo "💿 Espaço: $(df -h / | tail -1 | awk '{print $4}') disponível"
    echo "🌡️  Temperatura: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
    echo "📶 IP: $(hostname -I | awk '{print $1}')"
}

# Função principal
main() {
    log "Iniciando RaspMIDI no Raspberry Pi..."
    
    # Verificar se estamos no diretório correto
    if [ ! -d "$PROJECT_DIR" ]; then
        error "Diretório do projeto não encontrado: $PROJECT_DIR"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Mostrar informações do sistema
    show_system_info
    
    # Verificar internet
    check_internet
    
    # Verificar dispositivos MIDI
    check_midi_devices
    
    # Configurar permissões
    setup_permissions
    
    # Ativar ambiente virtual
    activate_venv || exit 1
    
    # Instalar dependências
    install_dependencies || exit 1
    
    # Verificar configuração
    check_config || exit 1
    
    # Inicializar banco de dados
    init_database
    
    # Parar aplicação anterior
    stop_previous_app
    
    # Iniciar aplicação
    start_app || exit 1
    
    # Mostrar status
    show_status
    
    log "RaspMIDI iniciado com sucesso!"
    log "Acesse: http://$(hostname -I | awk '{print $1}'):5000"
}

# Tratamento de sinais
trap 'log "Recebido sinal de parada"; exit 0' SIGTERM SIGINT

# Executar função principal
main "$@" 