#!/usr/bin/env python3
"""
Script para fazer deploy manual corrigindo os diretórios
"""

import paramiko
import os

def manual_deploy_fix():
    """Faz deploy manual corrigindo os diretórios"""
    try:
        print("🔧 Deploy manual corrigindo diretórios...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Cria os diretórios
        print("📋 Criando diretórios...")
        stdin, stdout, stderr = client.exec_command('mkdir -p app/midi/', timeout=10)
        print("   Diretórios criados")
        
        # Verifica se foram criados
        print("\n📋 Verificando diretórios:")
        stdin, stdout, stderr = client.exec_command('ls -la app/midi/', timeout=10)
        dir_info = stdout.read().decode().strip()
        print(f"   {dir_info}")
        
        # Faz upload do arquivo
        print("\n📋 Fazendo upload do arquivo...")
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
    manual_deploy_fix() 