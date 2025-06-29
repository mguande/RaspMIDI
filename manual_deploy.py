#!/usr/bin/env python3
"""
Script para fazer deploy manual do arquivo controller.py
"""

import paramiko
import os

def manual_deploy():
    """Faz deploy manual do arquivo controller.py"""
    try:
        print("🚀 Deploy manual do controller.py...")
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
        
        # Faz upload do arquivo
        print("📋 Fazendo upload do arquivo...")
        sftp = client.open_sftp()
        
        # Lê o arquivo local
        local_file = 'app/midi/controller.py'
        if os.path.exists(local_file):
            with open(local_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Escreve o arquivo no Pi
            with sftp.file('app/midi/controller.py', 'w') as f:
                f.write(content)
            
            print("✅ Arquivo enviado com sucesso!")
        else:
            print(f"❌ Arquivo local não encontrado: {local_file}")
        
        sftp.close()
        
        # Verifica se o arquivo foi enviado
        print("\n📋 Verificando se o arquivo foi enviado:")
        stdin, stdout, stderr = client.exec_command('ls -la app/midi/controller.py', timeout=10)
        file_info = stdout.read().decode().strip()
        print(f"   {file_info}")
        
        # Verifica se tem aconnect
        print("\n📋 Verificando se tem aconnect:")
        stdin, stdout, stderr = client.exec_command('grep -n "aconnect" app/midi/controller.py', timeout=10)
        aconnect_lines = stdout.read().decode().strip()
        if aconnect_lines:
            print(f"   ✅ aconnect encontrado:")
            print(f"   {aconnect_lines}")
        else:
            print("   ❌ aconnect não encontrado")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    manual_deploy() 