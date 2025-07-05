#!/bin/bash
# Script para aguardar RaspMIDI e iniciar LCD
echo "🖥️ Iniciando configuração do LCD..."

# Aguarda o sistema inicializar
sleep 15

# Configura o LCD
echo "📱 Configurando LCD..."
con2fbmap 1 1
sleep 2

# Aguarda o serviço RaspMIDI estar pronto
echo "⏳ Aguardando serviço RaspMIDI..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ Serviço RaspMIDI está pronto!"
        break
    fi
    
    echo "⏳ Tentativa $((attempt + 1))/$max_attempts - Aguardando RaspMIDI..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Timeout aguardando RaspMIDI"
    exit 1
fi

# Aguarda mais um pouco para garantir que tudo está estável
sleep 5

# Configura display X11
export DISPLAY=:0

# Para qualquer Chromium existente
pkill -f chromium 2>/dev/null
sleep 2

# Inicia Chromium em modo kiosk na página do palco
echo "🌐 Iniciando Chromium no LCD..."
nohup chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/palco > /tmp/chromium.log 2>&1 &

echo "✅ LCD configurado e Chromium iniciado!"
