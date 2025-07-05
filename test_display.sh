#!/bin/bash
# Script para testar o display
echo "Iniciando RaspMIDI Display..."
chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/display
