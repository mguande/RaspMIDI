#!/usr/bin/env python3
"""
Script para reiniciar ALSA e verificar portas MIDI
"""

import paramiko
import time

def restart_alsa():
    """Reinicia ALSA e verifica portas MIDI"""
    try:
        print("🔄 Reiniciando ALSA...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Reinicia ALSA
        print("📋 Reiniciando serviço ALSA...")
        stdin, stdout, stderr = client.exec_command('sudo systemctl restart alsa-utils', timeout=10)
        time.sleep(3)
        
        # Verifica se as portas MIDI aparecem agora
        print("\n📋 Verificando portas MIDI após reinicialização:")
        stdin, stdout, stderr = client.exec_command('cd /home/matheus/RaspMIDI && source venv/bin/activate && python3 -c "import mido; print(\"Inputs:\", mido.get_input_names()); print(\"Outputs:\", mido.get_output_names())"', timeout=10)
        midi_ports = stdout.read().decode().strip()
        print(f"   {midi_ports}")
        
        # Verifica se o Chocolate e Zoom aparecem
        if 'sinco' in midi_ports.lower():
            print("\n✅ Chocolate detectado nas portas MIDI!")
        else:
            print("\n❌ Chocolate ainda não detectado")
            
        if 'zoom' in midi_ports.lower():
            print("✅ Zoom detectado nas portas MIDI!")
        else:
            print("❌ Zoom ainda não detectado")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    restart_alsa() 