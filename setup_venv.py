#!/usr/bin/env python3
"""
Script para configurar ambiente virtual no Raspberry Pi
"""

import paramiko
import time

# Configurações do Raspberry Pi
RASPBERRY_IP = "192.168.15.8"
RASPBERRY_USER = "matheus"
RASPBERRY_PASSWORD = "matheus"

def run_ssh_command(command, timeout=30):
    """Executa comando SSH no Raspberry Pi"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=timeout)
        
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        
        client.close()
        return exit_code, output, error
    except Exception as e:
        return -1, "", str(e)

def main():
    print("🐍 Configurando ambiente virtual no Raspberry Pi...")
    print()
    
    # Instala python3-venv se não estiver instalado
    print("1. Instalando python3-venv...")
    exit_code, output, error = run_ssh_command("sudo apt update && sudo apt install -y python3-venv")
    if exit_code == 0:
        print("✅ python3-venv instalado")
    else:
        print(f"❌ Erro: {error}")
    
    print()
    
    # Cria o ambiente virtual
    print("2. Criando ambiente virtual...")
    exit_code, output, error = run_ssh_command("cd /home/matheus/RaspMIDI && python3 -m venv venv")
    if exit_code == 0:
        print("✅ Ambiente virtual criado")
    else:
        print(f"❌ Erro: {error}")
    
    print()
    
    # Ativa o ambiente virtual e instala as dependências
    print("3. Instalando dependências no ambiente virtual...")
    commands = [
        "cd /home/matheus/RaspMIDI",
        "source venv/bin/activate",
        "pip install flask flask-cors paramiko mido python-rtmidi requests"
    ]
    
    full_command = " && ".join(commands)
    exit_code, output, error = run_ssh_command(f"bash -c '{full_command}'")
    
    if exit_code == 0:
        print("✅ Dependências instaladas no ambiente virtual")
    else:
        print(f"❌ Erro: {error}")
    
    print()
    
    # Testa se tudo está funcionando
    print("4. Testando instalação...")
    test_command = "cd /home/matheus/RaspMIDI && source venv/bin/activate && python -c 'import flask, flask_cors, paramiko, mido; print(\"✅ Todas as dependências funcionando!\")'"
    exit_code, output, error = run_ssh_command(f"bash -c '{test_command}'")
    
    if exit_code == 0:
        print("✅ Ambiente virtual configurado com sucesso!")
        print("📝 Para rodar a aplicação, use: cd /home/matheus/RaspMIDI && source venv/bin/activate && python run.py")
    else:
        print(f"❌ Erro no teste: {error}")

if __name__ == "__main__":
    main() 