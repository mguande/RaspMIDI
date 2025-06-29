#!/usr/bin/env python3
"""
Script para verificar se o arquivo foi realmente atualizado no Pi
"""

import paramiko

def verify_file_update():
    """Verifica se o arquivo foi realmente atualizado no Pi"""
    try:
        print("🔍 Verificando se o arquivo foi atualizado...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Verifica se o arquivo existe
        print("📋 Verificando arquivo:")
        stdin, stdout, stderr = client.exec_command('ls -la app/midi/controller.py', timeout=10)
        file_info = stdout.read().decode().strip()
        print(f"   {file_info}")
        
        # Verifica se tem aconnect
        print("\n📋 Verificando aconnect:")
        stdin, stdout, stderr = client.exec_command('grep -n "aconnect" app/midi/controller.py', timeout=10)
        aconnect_lines = stdout.read().decode().strip()
        if aconnect_lines:
            print(f"   ✅ aconnect encontrado:")
            print(f"   {aconnect_lines}")
        else:
            print("   ❌ aconnect não encontrado")
        
        # Verifica se tem subprocess
        print("\n📋 Verificando subprocess:")
        stdin, stdout, stderr = client.exec_command('grep -n "subprocess" app/midi/controller.py', timeout=10)
        subprocess_lines = stdout.read().decode().strip()
        if subprocess_lines:
            print(f"   ✅ subprocess encontrado:")
            print(f"   {subprocess_lines}")
        else:
            print("   ❌ subprocess não encontrado")
        
        # Verifica se tem SINCO
        print("\n📋 Verificando SINCO:")
        stdin, stdout, stderr = client.exec_command('grep -n "sinco" app/midi/controller.py', timeout=10)
        sinco_lines = stdout.read().decode().strip()
        if sinco_lines:
            print(f"   ✅ SINCO encontrado:")
            print(f"   {sinco_lines}")
        else:
            print("   ❌ SINCO não encontrado")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    verify_file_update() 