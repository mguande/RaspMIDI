#!/bin/bash

echo "========================================"
echo "   RaspMIDI - Sistema de Controle MIDI"
echo "========================================"
echo

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    echo "Ambiente virtual criado com sucesso!"
    echo
fi

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Verificar se as dependências estão instaladas
echo "Verificando dependências..."
if ! python -c "import flask_cors" 2>/dev/null; then
    echo "Instalando dependências..."
    pip install -r requirements.txt
    echo "Dependências instaladas com sucesso!"
    echo
else
    echo "Dependências já estão instaladas."
    echo
fi

# Iniciar o sistema
echo "Iniciando RaspMIDI..."
echo
python run.py 