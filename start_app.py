#!/usr/bin/env python3
"""
Script para iniciar a aplicação manualmente
"""

import paramiko
import time

def start_app():
    """Inicia a aplicação manualmente"""
    try:
        print("🚀 Iniciando aplicação manualmente...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Verifica se há processos rodando
        print("📋 Verificando processos:")
        stdin, stdout, stderr = client.exec_command('ps aux | grep "python run.py" | grep -v grep', timeout=10)
        processes = stdout.read().decode().strip()
        if processes:
            print("   Processos encontrados:")
            print(f"   {processes}")
        else:
            print("   Nenhum processo encontrado")
        
        # Inicia a aplicação
        print("\n📋 Iniciando aplicação...")
        start_cmd = 'cd /home/matheus/RaspMIDI && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &'
        stdin, stdout, stderr = client.exec_command(start_cmd, timeout=10)
        
        # Aguarda um pouco
        print("⏳ Aguardando 5 segundos...")
        time.sleep(5)
        
        # Verifica se iniciou
        print("\n📋 Verificando se iniciou:")
        stdin, stdout, stderr = client.exec_command('ps aux | grep "python run.py" | grep -v grep', timeout=10)
        processes = stdout.read().decode().strip()
        if processes:
            print("✅ Aplicação iniciada!")
            print(f"   {processes}")
        else:
            print("❌ Aplicação não iniciou")
        
        # Verifica logs
        print("\n📋 Verificando logs:")
        stdin, stdout, stderr = client.exec_command('tail -10 logs/app.log', timeout=10)
        logs = stdout.read().decode().strip()
        if logs:
            print(f"   {logs}")
        else:
            print("   Nenhum log encontrado")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    start_app() 