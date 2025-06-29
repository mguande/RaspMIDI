@echo off
echo ========================================
echo    RaspMIDI - Sistema de Controle MIDI
echo ========================================
echo.

REM Verificar se o ambiente virtual existe
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    echo Ambiente virtual criado com sucesso!
    echo.
)

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Verificar se as dependências estão instaladas
echo Verificando dependências...
python -c "import flask_cors" 2>nul
if errorlevel 1 (
    echo Instalando dependências...
    pip install -r requirements.txt
    echo Dependências instaladas com sucesso!
    echo.
) else (
    echo Dependências já estão instaladas.
    echo.
)

REM Iniciar o sistema
echo Iniciando RaspMIDI...
echo.
python run.py

pause 