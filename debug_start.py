#!/usr/bin/env python3
"""
Script para debugar o início da aplicação
"""

import paramiko

def debug_start():
    """Debuga o início da aplicação"""
    try:
        print("🔍 Debugando início da aplicação...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Verifica se o arquivo run.py existe
        print("📋 Verificando arquivo run.py:")
        stdin, stdout, stderr = client.exec_command('ls -la run.py', timeout=10)
        file_info = stdout.read().decode().strip()
        print(f"   {file_info}")
        
        # Tenta executar o run.py diretamente
        print("\n📋 Tentando executar run.py diretamente:")
        stdin, stdout, stderr = client.exec_command('cd /home/matheus/RaspMIDI && source venv/bin/activate && python run.py', timeout=10)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if output:
            print(f"   Output: {output}")
        if error:
            print(f"   Error: {error}")
        
        # Verifica se o controller.py foi atualizado
        print("\n📋 Verificando controller.py:")
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
    debug_start() 