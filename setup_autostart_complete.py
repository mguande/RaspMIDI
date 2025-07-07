#!/usr/bin/env python3
"""
Script completo para configurar autostart do LCD após serviço RaspMIDI
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
    print("🔧 Configurando autostart completo do LCD...")
    print()
    
    # 1. Cria script de inicialização que aguarda o serviço RaspMIDI
    print("1. Criando script de inicialização inteligente...")
    startup_script = """#!/bin/bash
# Script para aguardar RaspMIDI e iniciar LCD
echo "🖥️ Iniciando configuração do LCD..."

# Aguarda o sistema inicializar
sleep 15

# Configura o LCD
echo "📱 Configurando LCD..."
con2fbmap 1 1
sleep 2

# Aguarda o serviço RaspMIDI estar pronto
echo "⏳ Aguardando serviço RaspMIDI..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ Serviço RaspMIDI está pronto!"
        break
    fi
    
    echo "⏳ Tentativa $((attempt + 1))/$max_attempts - Aguardando RaspMIDI..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Timeout aguardando RaspMIDI"
    exit 1
fi

# Aguarda mais um pouco para garantir que tudo está estável
sleep 5

# Configura display X11
export DISPLAY=:0

# Para qualquer Chromium existente
pkill -f chromium 2>/dev/null
sleep 2

# Inicia Chromium em modo kiosk na página do palco
echo "🌐 Iniciando Chromium no LCD..."
nohup chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/palco > /tmp/chromium.log 2>&1 &

echo "✅ LCD configurado e Chromium iniciado!"
"""
    
    # Salva o script
    with open("lcd_complete_startup.sh", "w", encoding="utf-8") as f:
        f.write(startup_script)
    
    # Copia para o Raspberry Pi
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("lcd_complete_startup.sh", "/tmp/lcd_complete_startup.sh")
        sftp.close()
        client.close()
        
        # Move e configura o script
        exit_code, output, error = run_ssh_command("sudo mv /tmp/lcd_complete_startup.sh /usr/local/bin/ && sudo chmod +x /usr/local/bin/lcd_complete_startup.sh")
        if exit_code == 0:
            print("✅ Script de inicialização completo criado")
        else:
            print(f"❌ Erro ao criar script: {error}")
            
    except Exception as e:
        print(f"❌ Erro ao copiar script: {e}")
    
    print()
    
    # 2. Atualiza o autostart para usar o novo script
    print("2. Atualizando autostart...")
    autostart_content = """[Desktop Entry]
Type=Application
Name=RaspMIDI LCD Display
Exec=/usr/local/bin/lcd_complete_startup.sh
Terminal=false
X-GNOME-Autostart-enabled=true
"""
    
    # Salva o conteúdo
    with open("raspmidi-lcd-complete.desktop", "w", encoding="utf-8") as f:
        f.write(autostart_content)
    
    # Copia para o Raspberry Pi
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("raspmidi-lcd-complete.desktop", "/tmp/raspmidi-lcd-complete.desktop")
        sftp.close()
        client.close()
        
        # Substitui o arquivo de autostart
        exit_code, output, error = run_ssh_command("mv /tmp/raspmidi-lcd-complete.desktop ~/.config/autostart/raspmidi-display.desktop")
        if exit_code == 0:
            print("✅ Autostart atualizado")
        else:
            print(f"❌ Erro ao atualizar autostart: {error}")
            
    except Exception as e:
        print(f"❌ Erro ao copiar autostart: {e}")
    
    print()
    
    # 3. Adiciona comando ao rc.local para garantir que o LCD seja configurado
    print("3. Configurando rc.local...")
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"# Configuração do LCD MPI3501\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Comentário adicionado ao rc.local")
    
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"sleep 10\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Aguardo adicionado ao rc.local")
    
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"con2fbmap 1 1\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Comando con2fbmap adicionado ao rc.local")
    
    print()
    
    # 4. Verifica o rc.local
    print("4. Verificando rc.local...")
    exit_code, output, error = run_ssh_command("cat /etc/rc.local")
    if exit_code == 0:
        print("✅ Conteúdo do rc.local:")
        print(output)
    else:
        print("❌ Erro ao ler rc.local")
    
    print()
    
    # 5. Cria um script de teste
    print("5. Criando script de teste...")
    test_script = """#!/bin/bash
# Script para testar o LCD manualmente
echo "🧪 Testando LCD manualmente..."

# Configura LCD
con2fbmap 1 1
sleep 2

# Verifica se RaspMIDI está rodando
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ RaspMIDI está rodando"
    
    # Para Chromium existente
    pkill -f chromium 2>/dev/null
    sleep 2
    
    # Inicia Chromium
    export DISPLAY=:0
    nohup chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/palco > /tmp/chromium.log 2>&1 &
    
    echo "✅ Chromium iniciado no LCD"
else
    echo "❌ RaspMIDI não está rodando"
fi
"""
    
    # Salva o script de teste
    with open("test_lcd.sh", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    # Copia para o Raspberry Pi
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("test_lcd.sh", "/tmp/test_lcd.sh")
        sftp.close()
        client.close()
        
        # Move e configura o script de teste
        exit_code, output, error = run_ssh_command("mv /tmp/test_lcd.sh ~/test_lcd.sh && chmod +x ~/test_lcd.sh")
        if exit_code == 0:
            print("✅ Script de teste criado")
        else:
            print(f"❌ Erro ao criar script de teste: {error}")
            
    except Exception as e:
        print(f"❌ Erro ao copiar script de teste: {e}")
    
    print()
    print("🎉 Configuração completa concluída!")
    print()
    print("📋 Sequência de inicialização após reiniciar:")
    print("1. Sistema inicia")
    print("2. rc.local executa con2fbmap 1 1 (configura LCD)")
    print("3. Serviço raspmidi.service inicia")
    print("4. Autostart executa lcd_complete_startup.sh")
    print("5. Script aguarda RaspMIDI estar pronto")
    print("6. Chromium inicia em modo kiosk na página /palco")
    print("7. LCD mostra as informações do palco")
    print()
    print("🔧 Comandos úteis:")
    print("- Testar agora: ~/test_lcd.sh")
    print("- Ver logs do Chromium: cat /tmp/chromium.log")
    print("- Ver status do serviço: sudo systemctl status raspmidi.service")
    print("- Reiniciar para testar: sudo reboot")

if __name__ == "__main__":
    main() 