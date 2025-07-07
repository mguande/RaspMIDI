#!/bin/bash
# Script para testar o LCD manualmente
echo "🧪 Testando LCD manualmente..."

# Configura LCD
con2fbmap 1 1
sleep 2

# Verifica se RaspMIDI está rodando
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ RaspMIDI está rodando"
    
    # Para Chromium existente
    pkill -f chromium 2>/dev/null
    sleep 2
    
    # Inicia Chromium
    export DISPLAY=:0
    nohup chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/palco > /tmp/chromium.log 2>&1 &
    
    echo "✅ Chromium iniciado no LCD"
else
    echo "❌ RaspMIDI não está rodando"
fi
