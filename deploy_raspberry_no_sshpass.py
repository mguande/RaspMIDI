#!/usr/bin/env python3
"""
Script para deploy automático no Raspberry Pi (sem sshpass)
"""

import os
import subprocess
import sys
import time

# Configurações do Raspberry Pi
RASPBERRY_IP = "192.168.15.8"
RASPBERRY_USER = "matheus"
RASPBERRY_PASSWORD = "matheus"
RASPBERRY_PATH = f"/home/{RASPBERRY_USER}/RaspMIDI"

def run_ssh_command(command):
    """Executa comando SSH no Raspberry Pi"""
    ssh_cmd = f'ssh -o StrictHostKeyChecking=no {RASPBERRY_USER}@{RASPBERRY_IP} "{command}"'
    
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def run_scp_command(local_file, remote_path):
    """Copia arquivo para o Raspberry Pi"""
    scp_cmd = f'scp -o StrictHostKeyChecking=no "{local_file}" {RASPBERRY_USER}@{RASPBERRY_IP}:{remote_path}'
    
    try:
        result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def deploy_file(local_file, remote_path):
    """Deploy de um arquivo específico"""
    print(f"📁 Deployando {local_file}...")
    success, stdout, stderr = run_scp_command(local_file, remote_path)
    
    if success:
        print(f"✅ {local_file} deployado com sucesso")
    else:
        print(f"❌ Erro ao deployar {local_file}: {stderr}")
    
    return success

def restart_application():
    """Reinicia a aplicação no Raspberry Pi"""
    print("🔄 Reiniciando aplicação...")
    
    # Para o processo atual
    success, stdout, stderr = run_ssh_command("pkill -f 'python run.py'")
    if success:
        print("✅ Processo anterior finalizado")
    
    # Aguarda um pouco
    time.sleep(2)
    
    # Inicia a aplicação
    start_cmd = f"cd {RASPBERRY_PATH} && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &"
    success, stdout, stderr = run_ssh_command(start_cmd)
    
    if success:
        print("✅ Aplicação reiniciada com sucesso")
        print(f"🌐 Acesse: http://{RASPBERRY_IP}:5000")
    else:
        print(f"❌ Erro ao reiniciar aplicação: {stderr}")
    
    return success

def check_application_status():
    """Verifica o status da aplicação"""
    print("🔍 Verificando status da aplicação...")
    
    success, stdout, stderr = run_ssh_command("ps aux | grep 'python run.py' | grep -v grep")
    
    if success and stdout.strip():
        print("✅ Aplicação está rodando")
        print("📋 Processos:")
        print(stdout)
    else:
        print("❌ Aplicação não está rodando")
    
    return success

def main():
    """Função principal"""
    print("🚀 Deploy automático para Raspberry Pi (sem sshpass)")
    print(f"📍 IP: {RASPBERRY_IP}")
    print(f"👤 Usuário: {RASPBERRY_USER}")
    print("⚠️ Você precisará digitar a senha manualmente para cada comando SSH")
    print()
    
    # Deploy dos arquivos principais
    files_to_deploy = [
        ("app/web/static/js/app.js", f"{RASPBERRY_PATH}/app/web/static/js/"),
        ("app/main.py", f"{RASPBERRY_PATH}/app/"),
        ("run.py", f"{RASPBERRY_PATH}/"),
    ]
    
    all_success = True
    for local_file, remote_path in files_to_deploy:
        if os.path.exists(local_file):
            if not deploy_file(local_file, remote_path):
                all_success = False
        else:
            print(f"⚠️ Arquivo não encontrado: {local_file}")
    
    if all_success:
        # Reinicia a aplicação
        restart_application()
        
        # Aguarda um pouco e verifica o status
        time.sleep(3)
        check_application_status()
        
        print("\n🎉 Deploy concluído!")
    else:
        print("\n❌ Deploy falhou!")
    
    return all_success

if __name__ == "__main__":
    main() 