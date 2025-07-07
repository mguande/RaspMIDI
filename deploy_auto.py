#!/usr/bin/env python3
"""
Script para deploy automático no Raspberry Pi
"""

import os
import subprocess
import sys
import time
import paramiko
import glob

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
        return exit_code, output, error
    except Exception as e:
        return -1, "", str(e)

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
    """Reinicia a aplicação no Raspberry Pi usando systemd"""
    print("🔄 Reiniciando aplicação via systemd...")
    
    # Para o processo manual se estiver rodando
    print("  - Finalizando processo manual (se houver)...")
    exit_code, output, error = run_ssh_command("pkill -f 'python run.py'")
    if exit_code == 0:
        print("    ✅ Processo manual finalizado.")
    elif exit_code == 1:
        print("    ℹ️  Nenhum processo manual em execução.")
    else:
        print(f"    ⚠️  Erro ao tentar finalizar processo manual: {error}")
    
    # Aguarda um pouco
    time.sleep(2)
    
    # Reinicia o serviço systemd
    print("  - Reiniciando serviço systemd...")
    exit_code, output, error = run_ssh_command("sudo systemctl restart raspmidi.service")
    
    if exit_code == 0:
        print("    ✅ Serviço systemd reiniciado com sucesso.")
    else:
        print(f"    ❌ Erro ao reiniciar serviço systemd: {error}")
        return False

    return True

def check_application_status():
    """Verifica o status da aplicação"""
    print("🔍 Verificando status da aplicação...")
    
    # Verifica o status do serviço systemd
    exit_code, output, error = run_ssh_command("sudo systemctl is-active raspmidi.service")
    
    if exit_code == 0 and "active" in output:
        print("✅ Serviço systemd está ativo")
        
        # Verifica se o processo Python está rodando
        exit_code2, output2, error2 = run_ssh_command("ps aux | grep 'python run.py' | grep -v grep")
        
        if exit_code2 == 0 and output2:
            print("✅ Processo Python está rodando")
            print("📋 Processos:")
            for line in output2.split('\n'):
                if line.strip():
                    print(f"   {line}")
            return True
        else:
            print("❌ Processo Python não está rodando")
            return False
    else:
        print("❌ Serviço systemd não está ativo")
        print(f"Status: {output}")
        return False

def test_api():
    """Testa se a API está funcionando"""
    print("🔍 Testando API...")
    
    exit_code, output, error = run_ssh_command("curl -s http://localhost:5000/api/midi/devices/list")
    
    if exit_code == 0 and output and 'success' in output:
        print("✅ API está funcionando!")
        print("📋 Resposta da API:")
        print(output[:200] + "..." if len(output) > 200 else output)
        return True
    else:
        print("❌ API não está respondendo")
        print(f"Resposta: {output}")
        return False

def read_remote_logs():
    """Lê as últimas 50 linhas do log remoto"""
    print("📄 Lendo logs remotos...")
    command = "tail -n 50 /home/matheus/RaspMIDI/logs/app.log"
    exit_code, output, error = run_ssh_command(command)
    
    if exit_code == 0:
        print("✅ Logs recebidos:")
        print("="*50)
        print(output)
        print("="*50)
    else:
        print(f"❌ Erro ao ler logs: {error}")

def stop_systemd_service():
    print('🔄 Parando serviço systemd raspmidi.service (se estiver rodando)...')
    try:
        subprocess.run(['sudo', 'systemctl', 'stop', 'raspmidi.service'], check=False)
        print('✅ Serviço systemd parado.')
    except Exception as e:
        print(f'⚠️  Falha ao parar serviço systemd: {e}')

def start_systemd_service():
    print('🔄 Iniciando serviço systemd raspmidi.service...')
    try:
        subprocess.run(['sudo', 'systemctl', 'start', 'raspmidi.service'], check=False)
        print('✅ Serviço systemd iniciado.')
    except Exception as e:
        print(f'⚠️  Falha ao iniciar serviço systemd: {e}')

def main():
    """Função principal"""
    print("🚀 Deploy automático para Raspberry Pi")
    print(f"📍 IP: {RASPBERRY_IP}")
    print(f"👤 Usuário: {RASPBERRY_USER}")
    print()
    
    stop_systemd_service()
    
    # Deploy dos arquivos principais e todos os .py relevantes
    files_to_deploy = [
        ("app/web/static/js/app.js", f"{RASPBERRY_PATH}/app/web/static/js/"),
        ("app/web/static/css/style.css", f"{RASPBERRY_PATH}/app/web/static/css/"),
        ("app/web/templates/index.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/web/templates/home.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/web/templates/verificacao.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/web/templates/edicao.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/web/templates/palco.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/web/templates/checkup.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("app/web/templates/palco-display.html", f"{RASPBERRY_PATH}/app/web/templates/"),
        ("run.py", f"{RASPBERRY_PATH}/"),
        ("app/main.py", f"{RASPBERRY_PATH}/app/"),
        ("lcd_complete_startup.sh", f"{RASPBERRY_PATH}/"),
        ("test_lcd.sh", f"{RASPBERRY_PATH}/"),
        ("raspmidi-lcd-complete.desktop", f"{RASPBERRY_PATH}/"),
        ("app/lcd_service_simple_fixed.py", f"{RASPBERRY_PATH}/app/"),
        ("raspmidi-lcd.service", f"{RASPBERRY_PATH}/"),
        ("setup_lcd_service.py", f"{RASPBERRY_PATH}/"),
        ("raspmidi-lcd-simple.service", f"{RASPBERRY_PATH}/"),
        ("raspmidi-lcd-improved.service", f"{RASPBERRY_PATH}/"),
    ]
    # Adiciona todos os .py das pastas backend
    for folder in ["app/database", "app/cache", "app/api", "app/midi"]:
        for pyfile in glob.glob(f"{folder}/*.py"):
            files_to_deploy.append((pyfile, f"{RASPBERRY_PATH}/{folder.replace('app/', 'app/')}/"))

    # Adiciona todos os arquivos da pasta de fontes (não só .ttf)
    for fontfile in glob.glob("app/web/static/fonts/*"):
        files_to_deploy.append((fontfile, f"{RASPBERRY_PATH}/app/web/static/fonts/"))
    
    all_success = True
    for local_file, remote_path in files_to_deploy:
        if not copy_file_to_raspberry(local_file, remote_path):
            all_success = False
    
    if all_success:
        # Reinicia a aplicação
        restart_application()
        
        # Aguarda um pouco e verifica o status
        time.sleep(3)
        if not check_application_status():
            all_success = False
        
        # Testa a API
        if not test_api():
            all_success = False
        
        if all_success:
            print("\n🎉 Deploy concluído com sucesso!")
        else:
            print("\n❌ Deploy concluído com falhas.")
    else:
        print("\n❌ Deploy falhou na cópia de arquivos!")



    return all_success

if __name__ == "__main__":
    main() 