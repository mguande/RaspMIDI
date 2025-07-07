#!/usr/bin/env python3
"""
Deploy rápido do LCD service melhorado
"""

import os
import subprocess
import sys

# Configurações
RASPBERRY_IP = "192.168.1.100"
RASPBERRY_USER = "pi"
RASPBERRY_PASS = "raspberry"
REMOTE_PATH = "/home/pi/RaspMIDI"

def run_ssh_command(command):
    """Executa comando SSH"""
    ssh_cmd = f'sshpass -p "{RASPBERRY_PASS}" ssh -o StrictHostKeyChecking=no {RASPBERRY_USER}@{RASPBERRY_IP} "{command}"'
    print(f"Executando: {command}")
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro: {result.stderr}")
        return False
    print(f"Sucesso: {result.stdout}")
    return True

def run_scp_command(local_file, remote_file):
    """Executa comando SCP"""
    scp_cmd = f'sshpass -p "{RASPBERRY_PASS}" scp -o StrictHostKeyChecking=no "{local_file}" {RASPBERRY_USER}@{RASPBERRY_IP}:{remote_file}'
    print(f"Enviando: {local_file} -> {remote_file}")
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro: {result.stderr}")
        return False
    print("Arquivo enviado com sucesso")
    return True

def main():
    print("=== Deploy Rápido LCD Service ===")
    
    # 1. Enviar arquivo LCD modificado
    local_file = "app/lcd_service_improved.py"
    remote_file = f"{REMOTE_PATH}/app/lcd_service_improved.py"
    
    if not os.path.exists(local_file):
        print(f"Erro: Arquivo {local_file} não encontrado")
        return False
    
    if not run_scp_command(local_file, remote_file):
        return False
    
    # 2. Reiniciar o serviço LCD
    print("\n=== Reiniciando serviço LCD ===")
    if not run_ssh_command("sudo systemctl restart raspmidi-lcd-improved.service"):
        return False
    
    # 3. Verificar status
    print("\n=== Verificando status ===")
    if not run_ssh_command("sudo systemctl status raspmidi-lcd-improved.service"):
        return False
    
    print("\n=== Deploy concluído! ===")
    print("Para ver logs em tempo real:")
    print("sudo journalctl -u raspmidi-lcd-improved.service -f")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 