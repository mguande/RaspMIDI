#!/usr/bin/env python3
"""
Script para reiniciar serviços USB
"""

import paramiko

def restart_usb():
    """Reinicia serviços USB"""
    try:
        print("🔌 Reiniciando serviços USB...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Reinicia serviços USB
        print("🔄 Reiniciando módulos USB...")
        stdin, stdout, stderr = client.exec_command('sudo modprobe -r usbhid && sudo modprobe usbhid', timeout=10)
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(result)
        if error:
            print(f"Erros: {error}")
        
        # Reinicia udev
        print("🔄 Reiniciando udev...")
        stdin, stdout, stderr = client.exec_command('sudo udevadm trigger', timeout=10)
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(result)
        if error:
            print(f"Erros: {error}")
        
        # Aguarda um pouco
        import time
        time.sleep(3)
        
        # Verifica dispositivos USB novamente
        print("🔍 Verificando dispositivos USB...")
        stdin, stdout, stderr = client.exec_command('lsusb', timeout=10)
        usb_devices = stdout.read().decode().strip()
        print(usb_devices)
        
        # Verifica dispositivos MIDI
        print("🎵 Verificando dispositivos MIDI...")
        test_script = '''
import mido
print("Entradas:", mido.get_input_names())
print("Saídas:", mido.get_output_names())
'''
        stdin, stdout, stderr = client.exec_command('cd /home/matheus/RaspMIDI && source venv/bin/activate && python3 -c "' + test_script + '"', timeout=10)
        midi_result = stdout.read().decode().strip()
        print(midi_result)
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    restart_usb() 