#!/usr/bin/env python3
"""
Script para tornar a configuração do LCD permanente
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
    print("🔧 Tornando configuração do LCD permanente...")
    print()
    
    # 1. Adiciona o comando ao rc.local
    print("1. Adicionando comando ao rc.local...")
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"sleep 5\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Aguardo adicionado")
    else:
        print(f"❌ Erro: {error}")
    
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"con2fbmap 1 1\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Comando con2fbmap adicionado")
    else:
        print(f"❌ Erro: {error}")
    
    print()
    
    # 2. Verifica o rc.local
    print("2. Verificando rc.local...")
    exit_code, output, error = run_ssh_command("cat /etc/rc.local")
    if exit_code == 0:
        print("✅ Conteúdo do rc.local:")
        print(output)
    else:
        print("❌ Erro ao ler rc.local")
    
    print()
    
    # 3. Cria um script de inicialização mais robusto
    print("3. Criando script de inicialização...")
    startup_script = """#!/bin/bash
# Script para configurar LCD MPI3501
sleep 10
con2fbmap 1 1
sleep 2
export DISPLAY=:0
nohup chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/palco > /tmp/chromium.log 2>&1 &
"""
    
    # Salva o script
    with open("lcd_startup.sh", "w") as f:
        f.write(startup_script)
    
    # Copia para o Raspberry Pi
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("lcd_startup.sh", "/tmp/lcd_startup.sh")
        sftp.close()
        client.close()
        
        # Move e configura o script
        exit_code, output, error = run_ssh_command("sudo mv /tmp/lcd_startup.sh /usr/local/bin/ && sudo chmod +x /usr/local/bin/lcd_startup.sh")
        if exit_code == 0:
            print("✅ Script de inicialização criado")
        else:
            print(f"❌ Erro ao criar script: {error}")
            
    except Exception as e:
        print(f"❌ Erro ao copiar script: {e}")
    
    print()
    
    # 4. Atualiza o autostart para usar o novo script
    print("4. Atualizando autostart...")
    autostart_content = """[Desktop Entry]
Type=Application
Name=RaspMIDI Display
Exec=/usr/local/bin/lcd_startup.sh
Terminal=false
X-GNOME-Autostart-enabled=true
"""
    
    # Salva o conteúdo
    with open("raspmidi-display-new.desktop", "w") as f:
        f.write(autostart_content)
    
    # Copia para o Raspberry Pi
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("raspmidi-display-new.desktop", "/tmp/raspmidi-display-new.desktop")
        sftp.close()
        client.close()
        
        # Substitui o arquivo de autostart
        exit_code, output, error = run_ssh_command("mv /tmp/raspmidi-display-new.desktop ~/.config/autostart/raspmidi-display.desktop")
        if exit_code == 0:
            print("✅ Autostart atualizado")
        else:
            print(f"❌ Erro ao atualizar autostart: {error}")
            
    except Exception as e:
        print(f"❌ Erro ao copiar autostart: {e}")
    
    print()
    print("🎉 Configuração permanente concluída!")
    print()
    print("📋 Agora quando o Raspberry Pi reiniciar:")
    print("1. O LCD será configurado automaticamente")
    print("2. O Chromium iniciará em modo kiosk")
    print("3. A página de display será exibida no LCD")
    print()
    print("🔧 Para testar agora:")
    print("sudo /usr/local/bin/lcd_startup.sh")

if __name__ == "__main__":
    main() 