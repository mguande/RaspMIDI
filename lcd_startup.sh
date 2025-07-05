#!/bin/bash
# Script para configurar LCD MPI3501
sleep 10
con2fbmap 1 1
sleep 2
export DISPLAY=:0
nohup chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/display > /tmp/chromium.log 2>&1 &
