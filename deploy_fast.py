#!/usr/bin/env python3
"""
Script para deploy RÁPIDO no Raspberry Pi - apenas arquivos essenciais
"""

import os
import subprocess
import sys
import time
import paramiko

# Configurações do Raspberry Pi
RASPBERRY_IP = "192.168.15.8"
RASPBERRY_USER = "matheus"
RASPBERRY_PASSWORD = "matheus"
RASPBERRY_PATH = f"/home/{RASPBERRY_USER}/RaspMIDI"

def run_ssh_command(command, timeout=10):
    """Executa comando SSH no Raspberry Pi usando paramiko"""
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

def copy_file_to_raspberry(local_file, remote_path):
    """Copia arquivo para o Raspberry Pi usando paramiko"""
    try:
        print(f"📁 {os.path.basename(local_file)}...")
        
        if not os.path.exists(local_file):
            print(f"⚠️ Arquivo não encontrado: {local_file}")
            return False
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        
        # Copia o arquivo
        remote_file = f"{remote_path}/{os.path.basename(local_file)}"
        sftp.put(local_file, remote_file)
        
        sftp.close()
        client.close()
        
        print(f"✅ OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def restart_app():
    """Reinicia a aplicação rapidamente usando ambiente virtual"""
    print("🔄 Reiniciando...")
    
    # Para processo manual
    run_ssh_command("pkill -f 'python run.py'")
    time.sleep(1)
    
    # Inicia novamente usando o ambiente virtual
    start_command = "cd /home/matheus/RaspMIDI && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &"
    run_ssh_command(f"bash -c '{start_command}'")
    time.sleep(3)
    
    # Testa se está rodando
    exit_code, output, error = run_ssh_command("ps aux | grep 'python run.py' | grep -v grep")
    if exit_code == 0 and output:
        print("✅ App rodando!")
        return True
    else:
        print("❌ App não iniciou")
        return False

def main():
    """Função principal - DEPLOY RÁPIDO"""
    print("⚡ DEPLOY RÁPIDO - Apenas arquivos essenciais")
    print(f"📍 {RASPBERRY_IP}")
    print()
    
    # Apenas os arquivos mais importantes
    files_to_deploy = [
        ("app/web/static/js/app.js", f"{RASPBERRY_PATH}/app/web/static/js/"),
        ("app/web/static/css/style.css", f"{RASPBERRY_PATH}/app/web/static/css/"),
        ("app/web/templates/palco.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("run.py", f"{RASPBERRY_PATH}/"),
    ]
    
    print("📦 Copiando arquivos...")
    for local_file, remote_path in files_to_deploy:
        copy_file_to_raspberry(local_file, remote_path)
    
    print("\n🔄 Reiniciando aplicação...")
    if restart_app():
        print("\n🎉 Deploy rápido concluído!")
    else:
        print("\n❌ Falha no deploy")

if __name__ == "__main__":
    main() 