#!/bin/bash
# Script para testar o serviço LCD
echo "🧪 Testando serviço LCD..."

# Verificar se o framebuffer está disponível
if [ -e /dev/fb1 ]; then
    echo "✅ Framebuffer /dev/fb1 disponível"
else
    echo "❌ Framebuffer /dev/fb1 não encontrado"
    exit 1
fi

# Verificar se o serviço está rodando
if sudo systemctl is-active --quiet raspmidi-lcd.service; then
    echo "✅ Serviço LCD está rodando"
else
    echo "❌ Serviço LCD não está rodando"
    echo "Iniciando serviço..."
    sudo systemctl start raspmidi-lcd.service
    sleep 3
    
    if sudo systemctl is-active --quiet raspmidi-lcd.service; then
        echo "✅ Serviço LCD iniciado com sucesso"
    else
        echo "❌ Falha ao iniciar serviço LCD"
        sudo systemctl status raspmidi-lcd.service
    fi
fi

# Verificar logs
echo "📋 Últimos logs do serviço LCD:"
sudo journalctl -u raspmidi-lcd.service -n 10 --no-pager
