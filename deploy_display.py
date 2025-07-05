#!/usr/bin/env python3
"""
Script para deploy completo incluindo arquivos do display
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

def restart_service():
    """Reinicia o serviço systemd"""
    print("🔄 Reiniciando serviço...")
    
    exit_code, output, error = run_ssh_command("sudo systemctl restart raspmidi.service")
    if exit_code == 0:
        print("✅ Serviço reiniciado")
        time.sleep(3)
        
        # Verifica se está rodando
        exit_code2, output2, error2 = run_ssh_command("sudo systemctl is-active raspmidi.service")
        if exit_code2 == 0 and "active" in output2:
            print("✅ Serviço ativo")
            return True
        else:
            print("❌ Serviço não está ativo")
            return False
    else:
        print(f"❌ Erro ao reiniciar serviço: {error}")
        return False

def main():
    """Função principal - DEPLOY COMPLETO"""
    print("🚀 DEPLOY COMPLETO - Incluindo Display")
    print(f"📍 {RASPBERRY_IP}")
    print()
    
    # Arquivos para deploy
    files_to_deploy = [
        ("app/web/static/js/app.js", f"{RASPBERRY_PATH}/app/web/static/js/"),
        ("app/web/static/css/style.css", f"{RASPBERRY_PATH}/app/web/static/css/"),
        ("app/web/templates/palco.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/web/templates/palco-display.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/main.py", f"{RASPBERRY_PATH}/app/"),
        ("run.py", f"{RASPBERRY_PATH}/"),
    ]
    
    print("📦 Copiando arquivos...")
    for local_file, remote_path in files_to_deploy:
        copy_file_to_raspberry(local_file, remote_path)
    
    print("\n🔄 Reiniciando aplicação...")
    if restart_service():
        print("\n🎉 Deploy completo concluído!")
        print("\n📋 URLs disponíveis:")
        print("- Palco normal: http://192.168.15.8:5000/palco")
        print("- Display 3.5\": http://192.168.15.8:5000/display")
        print("- Home: http://192.168.15.8:5000/")
    else:
        print("\n❌ Falha no deploy")

if __name__ == "__main__":
    main() 