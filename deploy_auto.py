#!/usr/bin/env python3
"""
Script para deploy automático no Raspberry Pi
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

def run_ssh_command(command, timeout=30):
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
        return exit_code == 0, output, error
    except Exception as e:
        return False, "", str(e)

def copy_file_to_raspberry(local_file, remote_path):
    """Copia arquivo para o Raspberry Pi usando paramiko"""
    try:
        print(f"📁 Deployando {local_file}...")
        
        if not os.path.exists(local_file):
            print(f"⚠️ Arquivo não encontrado: {local_file}")
            return False
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD)
        
        sftp = client.open_sftp()
        
        # Cria o diretório se não existir
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            run_ssh_command(f"mkdir -p {remote_path}")
        
        # Copia o arquivo
        remote_file = f"{remote_path}/{os.path.basename(local_file)}"
        sftp.put(local_file, remote_file)
        
        sftp.close()
        client.close()
        
        print(f"✅ {local_file} deployado com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao deployar {local_file}: {e}")
        return False

def restart_application():
    """Reinicia a aplicação no Raspberry Pi"""
    print("🔄 Reiniciando aplicação...")
    
    # Para o processo atual
    success, output, error = run_ssh_command("pkill -f 'python run.py'")
    if success:
        print("✅ Processo anterior finalizado")
    
    # Aguarda um pouco
    time.sleep(2)
    
    # Inicia a aplicação
    start_cmd = f"cd {RASPBERRY_PATH} && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &"
    success, output, error = run_ssh_command(start_cmd)
    
    if success:
        print("✅ Aplicação reiniciada com sucesso")
        print(f"🌐 Acesse: http://{RASPBERRY_IP}:5000")
    else:
        print(f"❌ Erro ao reiniciar aplicação: {error}")
    
    return success

def check_application_status():
    """Verifica o status da aplicação"""
    print("🔍 Verificando status da aplicação...")
    
    success, output, error = run_ssh_command("ps aux | grep 'python run.py' | grep -v grep")
    
    if success and output:
        print("✅ Aplicação está rodando")
        print("📋 Processos:")
        for line in output.split('\n'):
            if line.strip():
                print(f"   {line}")
    else:
        print("❌ Aplicação não está rodando")
    
    return success

def test_api():
    """Testa se a API está funcionando"""
    print("🔍 Testando API...")
    
    success, output, error = run_ssh_command("curl -s http://localhost:5000/api/midi/devices/list")
    
    if success and output and 'success' in output:
        print("✅ API está funcionando!")
        print("📋 Resposta da API:")
        print(output[:200] + "..." if len(output) > 200 else output)
        return True
    else:
        print("❌ API não está respondendo")
        print(f"Resposta: {output}")
        return False

def main():
    """Função principal"""
    print("🚀 Deploy automático para Raspberry Pi")
    print(f"📍 IP: {RASPBERRY_IP}")
    print(f"👤 Usuário: {RASPBERRY_USER}")
    print()
    
    # Deploy dos arquivos principais
    files_to_deploy = [
        ("app/web/static/js/app.js", f"{RASPBERRY_PATH}/app/web/static/js/"),
        ("app/web/static/css/style.css", f"{RASPBERRY_PATH}/app/web/static/css/"),
        ("app/main.py", f"{RASPBERRY_PATH}/app/"),
        ("app/midi/controller.py", f"{RASPBERRY_PATH}/app/midi/"),
        ("run.py", f"{RASPBERRY_PATH}/"),
    ]
    
    all_success = True
    for local_file, remote_path in files_to_deploy:
        if not copy_file_to_raspberry(local_file, remote_path):
            all_success = False
    
    if all_success:
        # Reinicia a aplicação
        restart_application()
        
        # Aguarda um pouco e verifica o status
        time.sleep(3)
        check_application_status()
        
        # Testa a API
        test_api()
        
        print("\n🎉 Deploy concluído!")
    else:
        print("\n❌ Deploy falhou!")
    
    return all_success

if __name__ == "__main__":
    main() 