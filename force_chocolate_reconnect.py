#!/usr/bin/env python3
"""
Script para forçar a reconexão do Chocolate
"""

import paramiko
import json

def force_chocolate_reconnect():
    """Força a reconexão do Chocolate"""
    try:
        print("🔄 Forçando reconexão do Chocolate...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Força reconexão via API
        print("📋 Forçando reconexão via API:")
        stdin, stdout, stderr = client.exec_command('curl -s -X POST http://localhost:5000/api/midi/devices/chocolate/reconnect', timeout=10)
        response = stdout.read().decode().strip()
        print(f"   Resposta: {response}")
        
        # Aguarda um pouco
        print("\n⏳ Aguardando 3 segundos...")
        stdin, stdout, stderr = client.exec_command('sleep 3', timeout=10)
        
        # Verifica status após reconexão
        print("\n📋 Verificando status após reconexão:")
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:5000/api/midi/devices/status', timeout=10)
        status = stdout.read().decode().strip()
        
        if status:
            try:
                data = json.loads(status)
                if data.get('success'):
                    chocolate_status = data.get('data', {}).get('chocolate', {})
                    print(f"   Status do Chocolate: {chocolate_status}")
                    
                    if chocolate_status.get('connected'):
                        print("   ✅ Chocolate agora está conectado!")
                    else:
                        print("   ❌ Chocolate ainda não está conectado")
                else:
                    print("❌ Erro na API")
            except json.JSONDecodeError:
                print(f"❌ Erro ao decodificar JSON: {status}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    force_chocolate_reconnect() 