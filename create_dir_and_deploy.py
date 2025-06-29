#!/usr/bin/env python3
"""
Script para criar o diretório e fazer deploy
"""

import paramiko

def create_dir_and_deploy():
    """Cria o diretório e faz deploy"""
    try:
        print("🔍 Criando diretório e fazendo deploy...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Verifica se o diretório existe
        print("📋 Verificando diretório:")
        stdin, stdout, stderr = client.exec_command('ls -la app/midi/', timeout=10)
        dir_info = stdout.read().decode().strip()
        print(f"   {dir_info}")
        
        # Cria o diretório se não existir
        if 'No such file' in dir_info:
            print("📋 Criando diretório...")
            stdin, stdout, stderr = client.exec_command('mkdir -p app/midi/', timeout=10)
            print("   Diretório criado")
        
        # Verifica novamente
        print("\n📋 Verificando diretório novamente:")
        stdin, stdout, stderr = client.exec_command('ls -la app/midi/', timeout=10)
        dir_info = stdout.read().decode().strip()
        print(f"   {dir_info}")
        
        client.close()
        
        # Faz deploy
        print("\n📋 Fazendo deploy...")
        import subprocess
        result = subprocess.run(['python', 'deploy_auto.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Erro: {result.stderr}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    create_dir_and_deploy() 