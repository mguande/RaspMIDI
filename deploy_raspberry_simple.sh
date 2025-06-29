#!/bin/bash

# Script de deploy simples para Raspberry Pi
# Execute este script diretamente no Raspberry Pi

echo "🚀 Deploy direto no Raspberry Pi"
echo "📍 PC IP: 192.168.15.7"
echo "📍 Porta: 8000"
echo ""

# Configurações
RASPBERRY_PATH="/home/matheus/RaspMIDI"
PC_IP="192.168.15.7"
PC_PORT="8000"

# Função para baixar arquivo
download_file() {
    local remote_path=$1
    local local_path=$2
    
    echo "📁 Baixando $remote_path..."
    
    # Cria o diretório se não existir
    mkdir -p "$(dirname "$local_path")"
    
    # Baixa o arquivo
    if curl -s -o "$local_path" "http://$PC_IP:$PC_PORT/$remote_path"; then
        echo "✅ $remote_path baixado com sucesso"
        return 0
    else
        echo "❌ Erro ao baixar $remote_path"
        return 1
    fi
}

# Função para reiniciar aplicação
restart_app() {
    echo "🔄 Reiniciando aplicação..."
    
    # Para o processo atual
    pkill -f "python run.py" 2>/dev/null
    echo "✅ Processo anterior finalizado"
    
    # Aguarda um pouco
    sleep 2
    
    # Vai para o diretório da aplicação
    cd "$RASPBERRY_PATH" || exit 1
    
    # Inicia a aplicação
    source venv/bin/activate
    nohup python run.py > logs/app.log 2>&1 &
    
    echo "✅ Aplicação reiniciada com sucesso"
}

# Função para verificar status
check_status() {
    echo "🔍 Verificando status da aplicação..."
    
    if pgrep -f "python run.py" > /dev/null; then
        echo "✅ Aplicação está rodando"
        echo "📋 Processos:"
        ps aux | grep "python run.py" | grep -v grep
    else
        echo "❌ Aplicação não está rodando"
    fi
}

# Lista de arquivos para baixar
files=(
    "app/web/static/js/app.js:$RASPBERRY_PATH/app/web/static/js/app.js"
    "app/main.py:$RASPBERRY_PATH/app/main.py"
    "run.py:$RASPBERRY_PATH/run.py"
)

echo "📥 Baixando arquivos..."
all_success=true

for file_pair in "${files[@]}"; do
    IFS=':' read -r remote_path local_path <<< "$file_pair"
    
    if ! download_file "$remote_path" "$local_path"; then
        all_success=false
    fi
done

if [ "$all_success" = true ]; then
    echo ""
    echo "🎉 Todos os arquivos baixados com sucesso!"
    
    # Reinicia a aplicação
    restart_app
    
    # Aguarda um pouco e verifica o status
    sleep 3
    check_status
    
    echo ""
    echo "🎉 Deploy concluído!"
    echo "🌐 Acesse: http://192.168.15.8:5000"
else
    echo ""
    echo "❌ Deploy falhou!"
    exit 1
fi 