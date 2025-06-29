@echo off
echo 🚀 Deploy automático para Raspberry Pi

REM Configurações
set RASPBERRY_IP=192.168.15.8
set RASPBERRY_USER=matheus
set RASPBERRY_PASSWORD=matheus

echo 📁 Deployando app.js...
echo %RASPBERRY_PASSWORD% | scp -o StrictHostKeyChecking=no app/web/static/js/app.js %RASPBERRY_USER%@%RASPBERRY_IP%:/home/%RASPBERRY_USER%/RaspMIDI/app/web/static/js/

if %ERRORLEVEL% EQU 0 (
    echo ✅ app.js deployado com sucesso
) else (
    echo ❌ Erro ao deployar app.js
)

echo 🔄 Reiniciando aplicação...

REM Para o processo atual
echo %RASPBERRY_PASSWORD% | ssh -o StrictHostKeyChecking=no %RASPBERRY_USER%@%RASPBERRY_IP% "pkill -f 'python run.py'"

timeout /t 2 /nobreak > nul

REM Inicia a aplicação
echo %RASPBERRY_PASSWORD% | ssh -o StrictHostKeyChecking=no %RASPBERRY_USER%@%RASPBERRY_IP% "cd /home/%RASPBERRY_USER%/RaspMIDI && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &"

if %ERRORLEVEL% EQU 0 (
    echo ✅ Aplicação reiniciada com sucesso
    echo 🌐 Acesse: http://%RASPBERRY_IP%:5000
) else (
    echo ❌ Erro ao reiniciar aplicação
)

echo 🎉 Deploy concluído!
pause 