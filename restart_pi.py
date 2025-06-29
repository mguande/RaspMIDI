#!/usr/bin/env python3
"""
Script para reiniciar o Raspberry Pi
"""

import paramiko
import time

def restart_pi():
    """Reinicia o Raspberry Pi"""
    try:
        print("🔄 Reiniciando Raspberry Pi...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Envia comando de reinicialização
        print("📡 Enviando comando de reinicialização...")
        stdin, stdout, stderr = client.exec_command('sudo reboot', timeout=10)
        
        print("✅ Comando de reinicialização enviado!")
        print("⏳ Aguardando o Raspberry Pi reiniciar...")
        print("💡 O Pi deve estar online novamente em 1-2 minutos")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    restart_pi() 