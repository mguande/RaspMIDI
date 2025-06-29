@echo off
echo 🚀 Deploy Completo RaspMIDI
echo.

echo 📋 Passos do deploy:
echo 1. Iniciar servidor de arquivos no PC
echo 2. Executar deploy no Raspberry Pi
echo.

echo 🌐 Iniciando servidor de arquivos...
echo 💡 O servidor ficará rodando em http://localhost:8000
echo 💡 Pressione Ctrl+C para parar o servidor quando terminar
echo.

python start_file_server.py

echo.
echo ✅ Servidor parado
pause 