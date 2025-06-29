#!/usr/bin/env python3
"""
Script para instalar dependências MIDI
"""

import paramiko

def install_midi_deps():
    """Instala dependências MIDI necessárias"""
    try:
        print("🔧 Instalando dependências MIDI...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('192.168.15.8', username='matheus', password='matheus', timeout=10)
        
        # Ativa o ambiente virtual
        print("📦 Ativando ambiente virtual...")
        stdin, stdout, stderr = client.exec_command('cd /home/matheus/RaspMIDI && source venv/bin/activate', timeout=10)
        
        # Instala dependências do sistema
        print("🔧 Instalando dependências do sistema...")
        stdin, stdout, stderr = client.exec_command('sudo apt-get update && sudo apt-get install -y python3-rtmidi python3-mido libasound2-dev', timeout=60)
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(result)
        if error:
            print(f"Erros: {error}")
        
        # Instala dependências Python
        print("🐍 Instalando dependências Python...")
        stdin, stdout, stderr = client.exec_command('cd /home/matheus/RaspMIDI && source venv/bin/activate && pip install rtmidi python-rtmidi', timeout=60)
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        print(result)
        if error:
            print(f"Erros: {error}")
        
        # Testa se mido está funcionando
        print("🧪 Testando mido...")
        test_script = '''
import mido
print("Mido funcionando!")
print("Backend:", mido.backend.name)
print("Entradas:", mido.get_input_names())
print("Saídas:", mido.get_output_names())
'''
        
        stdin, stdout, stderr = client.exec_command('cd /home/matheus/RaspMIDI && source venv/bin/activate && python3 -c "' + test_script + '"', timeout=30)
        result = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        print("Resultado do teste:")
        print(result)
        if error:
            print(f"Erros: {error}")
        
        # Reinicia a aplicação
        print("🔄 Reiniciando aplicação...")
        stdin, stdout, stderr = client.exec_command('pkill -f "python run.py"', timeout=10)
        import time
        time.sleep(2)
        
        stdin, stdout, stderr = client.exec_command('cd /home/matheus/RaspMIDI && source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &', timeout=10)
        
        print("✅ Dependências instaladas e aplicação reiniciada!")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    install_midi_deps() 