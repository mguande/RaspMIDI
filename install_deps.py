#!/usr/bin/env python3
"""
Script para instalar dependências no Raspberry Pi
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
    print("📦 Instalando dependências no Raspberry Pi...")
    print()
    
    # Atualiza o pip
    print("1. Atualizando pip...")
    exit_code, output, error = run_ssh_command("python3 -m pip install --upgrade pip")
    if exit_code == 0:
        print("✅ Pip atualizado")
    else:
        print(f"❌ Erro: {error}")
    
    print()
    
    # Instala as dependências
    print("2. Instalando dependências...")
    deps = [
        "flask",
        "flask-cors", 
        "paramiko",
        "mido",
        "python-rtmidi",
        "requests"
    ]
    
    for dep in deps:
        print(f"   Instalando {dep}...")
        exit_code, output, error = run_ssh_command(f"python3 -m pip install {dep}")
        if exit_code == 0:
            print(f"   ✅ {dep} instalado")
        else:
            print(f"   ❌ Erro ao instalar {dep}: {error}")
    
    print()
    
    # Verifica se as dependências estão instaladas
    print("3. Verificando instalação...")
    exit_code, output, error = run_ssh_command("python3 -c 'import flask, flask_cors, paramiko, mido; print(\"✅ Todas as dependências instaladas!\")'")
    if exit_code == 0:
        print("✅ Todas as dependências estão funcionando!")
    else:
        print(f"❌ Erro na verificação: {error}")

if __name__ == "__main__":
    main() 