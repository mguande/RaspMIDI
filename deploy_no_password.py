#!/usr/bin/env python3
"""
Deploy sem senha usando paramiko (como no manual_deploy.py)
"""

import paramiko
import os
import time

# Configurações do Raspberry Pi
RASPBERRY_IP = "192.168.15.8"
RASPBERRY_USER = "matheus"
RASPBERRY_PASSWORD = "matheus"
RASPBERRY_PATH = f"/home/{RASPBERRY_USER}/RaspMIDI"

def run_ssh_command(client, command):
    """Executa comando SSH usando paramiko"""
    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if stdout.channel.recv_exit_status() == 0:
            print(f"✅ Comando executado com sucesso: {command}")
            if output:
                print(output)
            return True
        else:
            print(f"❌ Erro ao executar comando: {command}")
            if error:
                print(f"Erro: {error}")
            return False
    except Exception as e:
        print(f"❌ Exceção ao executar comando: {e}")
        return False

def deploy_file(client, local_file, remote_path):
    """Deploy de um arquivo usando paramiko"""
    try:
        print(f"📤 Enviando {local_file}...")
        
        if not os.path.exists(local_file):
            print(f"⚠️ Arquivo não encontrado: {local_file}")
            return False
        
        sftp = client.open_sftp()
        
        # Lê o arquivo local
        with open(local_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Escreve o arquivo no Pi
        with sftp.file(remote_path, 'w') as f:
            f.write(content)
        
        sftp.close()
        print(f"✅ {local_file} enviado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar {local_file}: {e}")
        return False

def deploy_files():
    """Deploy dos arquivos principais"""
    print("🚀 Iniciando deploy sem senha usando paramiko...")
    
    try:
        # Conecta ao Raspberry Pi
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        print("✅ Conectado ao Raspberry Pi!")
        
        # Lista de arquivos para deploy
        files_to_deploy = [
            ('app/midi/zoom_g3x.py', f'{RASPBERRY_PATH}/app/midi/zoom_g3x.py'),
            ('app/web/static/js/app.js', f'{RASPBERRY_PATH}/app/web/static/js/app.js'),
            ('app/api/midi_routes.py', f'{RASPBERRY_PATH}/app/api/midi_routes.py'),
            ('app/web/templates/verificacao.html', f'{RASPBERRY_PATH}/app/web/templates/verificacao.html')
        ]
        
        # Deploy dos arquivos
        for local_file, remote_file in files_to_deploy:
            if not deploy_file(client, local_file, remote_file):
                print(f"❌ Falha no deploy de {local_file}")
                client.close()
                return False
        
        # Reinicia o aplicativo
        print("🔄 Reiniciando aplicativo...")
        
        # Mata qualquer processo rodando python run.py
        print("📋 Matando processos antigos de python run.py...")
        run_ssh_command(client, "pkill -f 'python run.py' || true")
        
        # Garante que a porta 5000 está livre
        print("📋 Garantindo que a porta 5000 está livre...")
        run_ssh_command(client, "fuser -k 5000/tcp || true")
        
        # Aguarda um pouco
        print("⏳ Aguardando 2 segundos...")
        run_ssh_command(client, "sleep 2")
        
        # Inicia a aplicação
        print("🚀 Iniciando aplicação...")
        
        # Comando simplificado - primeiro navega para o diretório
        if not run_ssh_command(client, f"cd {RASPBERRY_PATH}"):
            print(f"❌ Falha ao navegar para o diretório")
            client.close()
            return False
            
        # Ativa o ambiente virtual
        if not run_ssh_command(client, "source venv/bin/activate"):
            print(f"❌ Falha ao ativar ambiente virtual")
            client.close()
            return False
            
        # Inicia o aplicativo em background
        if not run_ssh_command(client, "nohup python run.py > logs/app.log 2>&1 &"):
            print(f"❌ Falha ao iniciar aplicação")
            client.close()
            return False
        
        # Aguarda um pouco e verifica o status
        time.sleep(3)
        print("🔍 Verificando status da aplicação...")
        run_ssh_command(client, "ps aux | grep 'python run.py' | grep -v grep")
        
        client.close()
        
        print("✅ Deploy concluído com sucesso!")
        print(f"🌐 Acesse: http://{RASPBERRY_IP}:5000")
        return True
        
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

if __name__ == "__main__":
    deploy_files() 