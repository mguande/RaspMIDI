#!/bin/bash

# 1. Instalar e habilitar o serviço systemd
SERVICE_PATH="/home/matheus/RaspMIDI/raspmidi.service"
SERVICE_TARGET="/etc/systemd/system/raspmidi.service"

if [ -f "$SERVICE_PATH" ]; then
    echo "Copiando serviço para /etc/systemd/system..."
    sudo cp "$SERVICE_PATH" "$SERVICE_TARGET"
    sudo systemctl daemon-reload
    sudo systemctl enable raspmidi.service
    sudo systemctl restart raspmidi.service
    echo "Serviço raspmidi.service instalado e habilitado!"
else
    echo "Arquivo de serviço não encontrado em $SERVICE_PATH"
fi

# 2. Criar atalho no desktop do usuário pi
DESKTOP_FILE="/home/pi/Desktop/RaspMIDI.desktop"
cat <<EOF | sudo tee "$DESKTOP_FILE" > /dev/null
[Desktop Entry]
Name=RaspMIDI
Comment=Abrir interface do RaspMIDI
Exec=chromium-browser --kiosk http://localhost:5000
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
EOF

sudo chmod +x "$DESKTOP_FILE"
echo "Atalho criado em $DESKTOP_FILE"

echo "Tudo pronto! Reinicie o Raspberry Pi para testar o autostart." 