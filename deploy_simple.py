#!/usr/bin/env python3
"""
Script de deploy simples para Raspberry Pi usando paramiko
"""

import paramiko
import time
import os

# Configurações
RASPBERRY_IP = "192.168.15.8"
RASPBERRY_USER = "matheus"
RASPBERRY_PASSWORD = "raspberry"  # Ajuste se necessário
RASPBERRY_PATH = "/home/matheus/RaspMIDI"

def deploy():
    print("🚀 Deploy no Raspberry Pi...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD)
    
    print("✅ Conectado")
    
    # Para processos anteriores
    ssh.exec_command("pkill -f 'python run.py'")
    time.sleep(2)
    
    # Cria logs e inicia
    commands = [
        f"mkdir -p {RASPBERRY_PATH}/logs",
        f"cd {RASPBERRY_PATH} && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &"
    ]
    
    for cmd in commands:
        ssh.exec_command(cmd)
        time.sleep(1)
    
    time.sleep(3)
    
    # Verifica status
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'python run.py' | grep -v grep")
    if stdout.read().strip():
        print("✅ Aplicação rodando em http://192.168.15.8:5000")
    else:
        print("❌ Aplicação não iniciou")
    
    ssh.close()

if __name__ == "__main__":
    deploy() 