#!/usr/bin/env python3
"""
Script para debugar o problema do Chocolate
"""

import paramiko
import json

def debug_chocolate():
    """Debuga o problema do Chocolate"""
    try:
        print("🔍 Debugando problema do Chocolate...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Verifica entradas MIDI
        print("📋 Verificando entradas MIDI:")
        stdin, stdout, stderr = client.exec_command('python3 -c "import mido; print(\"Inputs:\", mido.get_input_names())"', timeout=10)
        inputs = stdout.read().decode().strip()
        print(f"   {inputs}")
        
        # Verifica configuração atual
        print("\n📋 Verificando configuração atual:")
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:5000/api/midi/devices', timeout=10)
        devices = stdout.read().decode().strip()
        
        if devices:
            try:
                data = json.loads(devices)
                if data.get('success'):
                    inputs = data.get('data', {}).get('inputs', [])
                    print("   Dispositivos de entrada configurados:")
                    for device in inputs:
                        print(f"      - {device}")
                        
                        # Verifica se é o Chocolate
                        if 'sinco' in device.get('name', '').lower():
                            print(f"         ✅ Este é o Chocolate!")
                            print(f"         Nome: {device.get('name')}")
                            print(f"         Nome real: {device.get('real_name')}")
                            print(f"         Tipo: {device.get('type')}")
                else:
                    print("❌ Erro na API")
            except json.JSONDecodeError:
                print(f"❌ Erro ao decodificar JSON: {devices}")
        
        # Verifica status do device_status
        print("\n📋 Verificando device_status:")
        stdin, stdout, stderr = client.exec_command('curl -s http://localhost:5000/api/midi/devices/status', timeout=10)
        status = stdout.read().decode().strip()
        
        if status:
            try:
                data = json.loads(status)
                if data.get('success'):
                    chocolate_status = data.get('data', {}).get('chocolate', {})
                    print(f"   Status do Chocolate: {chocolate_status}")
                else:
                    print("❌ Erro na API de status")
            except json.JSONDecodeError:
                print(f"❌ Erro ao decodificar JSON: {status}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    debug_chocolate() 