#!/usr/bin/env python3
"""
Script para configurar o display MPI3501 com Chromium em modo kiosk
"""

import paramiko
import time

# Configurações do Raspberry Pi
RASPBERRY_IP = "192.168.15.8"
RASPBERRY_USER = "matheus"
RASPBERRY_PASSWORD = "matheus"

def run_ssh_command(command, timeout=30):
    """Executa comando SSH no Raspberry Pi"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=timeout)
        
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        
        client.close()
        return exit_code, output, error
    except Exception as e:
        return -1, "", str(e)

def main():
    print("🖥️ Configurando display MPI3501 com Chromium...")
    print()
    
    # 1. Instalar Chromium
    print("1. Instalando Chromium...")
    exit_code, output, error = run_ssh_command("sudo apt update && sudo apt install -y chromium-browser")
    if exit_code == 0:
        print("✅ Chromium instalado")
    else:
        print(f"❌ Erro: {error}")
        return
    
    print()
    
    # 2. Criar diretório de autostart
    print("2. Criando diretório de autostart...")
    exit_code, output, error = run_ssh_command("mkdir -p ~/.config/autostart")
    if exit_code == 0:
        print("✅ Diretório criado")
    else:
        print(f"❌ Erro: {error}")
        return
    
    print()
    
    # 3. Criar arquivo de autostart para Chromium
    print("3. Criando arquivo de autostart...")
    autostart_content = """[Desktop Entry]
Type=Application
Name=RaspMIDI Display
Exec=chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/palco
Terminal=false
X-GNOME-Autostart-enabled=true
"""
    
    # Salva o conteúdo em um arquivo temporário
    with open("raspmidi-display.desktop", "w") as f:
        f.write(autostart_content)
    
    # Copia para o Raspberry Pi
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("raspmidi-display.desktop", "/tmp/raspmidi-display.desktop")
        sftp.close()
        client.close()
        
        # Move para o diretório correto
        exit_code, output, error = run_ssh_command("mv /tmp/raspmidi-display.desktop ~/.config/autostart/")
        if exit_code == 0:
            print("✅ Arquivo de autostart criado")
        else:
            print(f"❌ Erro: {error}")
            return
            
    except Exception as e:
        print(f"❌ Erro ao copiar arquivo: {e}")
        return
    
    print()
    
    # 4. Configurar para iniciar automaticamente no desktop
    print("4. Configurando para iniciar automaticamente...")
    exit_code, output, error = run_ssh_command("chmod +x ~/.config/autostart/raspmidi-display.desktop")
    if exit_code == 0:
        print("✅ Permissões configuradas")
    else:
        print(f"❌ Erro: {error}")
    
    print()
    
    # 5. Testar se o Chromium funciona
    print("5. Testando Chromium...")
    exit_code, output, error = run_ssh_command("chromium-browser --version")
    if exit_code == 0:
        print("✅ Chromium funcionando:")
        print(output)
    else:
        print(f"❌ Erro: {error}")
    
    print()
    
    # 6. Criar script de teste
    print("6. Criando script de teste...")
    test_script = """#!/bin/bash
# Script para testar o display
echo "Iniciando RaspMIDI Display..."
chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/display
"""
    
    with open("test_display.sh", "w") as f:
        f.write(test_script)
    
    # Copia e configura o script
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("test_display.sh", "/tmp/test_display.sh")
        sftp.close()
        client.close()
        
        exit_code, output, error = run_ssh_command("mv /tmp/test_display.sh ~/test_display.sh && chmod +x ~/test_display.sh")
        if exit_code == 0:
            print("✅ Script de teste criado")
        else:
            print(f"❌ Erro: {error}")
            
    except Exception as e:
        print(f"❌ Erro ao copiar script: {e}")
    
    print()
    print("🎉 Configuração concluída!")
    print()
    print("📋 Próximos passos:")
    print("1. Reinicie o Raspberry Pi")
    print("2. O Chromium deve abrir automaticamente em modo kiosk")
    print("3. Para testar manualmente: ~/test_display.sh")
    print("4. Para parar o modo kiosk: Alt+F4 ou Ctrl+Q")
    print()
    print("🔧 Comandos úteis:")
    print("- Testar display: ~/test_display.sh")
    print("- Ver logs: journalctl -u raspmidi.service -f")
    print("- Parar autostart: rm ~/.config/autostart/raspmidi-display.desktop")

if __name__ == "__main__":
    main() 