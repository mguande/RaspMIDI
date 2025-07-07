#!/usr/bin/env python3
"""
Script para configurar o serviço LCD no Raspberry Pi
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
    print("🔧 Configurando serviço LCD...")
    print()
    
    # 1. Instalar dependências Python
    print("1. Instalando dependências Python...")
    dependencies = [
        "pygame",
        "pillow",
        "mido",
        "python-rtmidi"
    ]
    
    for dep in dependencies:
        print(f"  - Instalando {dep}...")
        exit_code, output, error = run_ssh_command(f"source ~/RaspMIDI/venv/bin/activate && pip install {dep}")
        if exit_code == 0:
            print(f"    ✅ {dep} instalado")
        else:
            print(f"    ❌ Erro ao instalar {dep}: {error}")
    
    print()
    
    # 2. Configurar framebuffer
    print("2. Configurando framebuffer...")
    exit_code, output, error = run_ssh_command("sudo modprobe fbtft_device name=mpi3501 gpios=reset:25,dc:24,led:18 speed=32000000 rotate=90")
    if exit_code == 0:
        print("✅ Driver LCD carregado")
    else:
        print(f"❌ Erro ao carregar driver: {error}")
    
    # Mapear console para fb1
    exit_code, output, error = run_ssh_command("sudo con2fbmap 1 1")
    if exit_code == 0:
        print("✅ Console mapeado para fb1")
    else:
        print(f"❌ Erro ao mapear console: {error}")
    
    print()
    
    # 3. Configurar permissões
    print("3. Configurando permissões...")
    exit_code, output, error = run_ssh_command("sudo chmod 666 /dev/fb1")
    if exit_code == 0:
        print("✅ Permissões do framebuffer configuradas")
    else:
        print(f"❌ Erro ao configurar permissões: {error}")
    
    # Adicionar usuário ao grupo video
    exit_code, output, error = run_ssh_command("sudo usermod -a -G video matheus")
    if exit_code == 0:
        print("✅ Usuário adicionado ao grupo video")
    else:
        print(f"❌ Erro ao adicionar ao grupo: {error}")
    
    print()
    
    # 4. Instalar serviço systemd
    print("4. Instalando serviço systemd...")
    exit_code, output, error = run_ssh_command("sudo cp ~/RaspMIDI/raspmidi-lcd.service /etc/systemd/system/")
    if exit_code == 0:
        print("✅ Arquivo de serviço copiado")
    else:
        print(f"❌ Erro ao copiar serviço: {error}")
    
    # Recarregar systemd
    exit_code, output, error = run_ssh_command("sudo systemctl daemon-reload")
    if exit_code == 0:
        print("✅ Systemd recarregado")
    else:
        print(f"❌ Erro ao recarregar systemd: {error}")
    
    # Habilitar serviço
    exit_code, output, error = run_ssh_command("sudo systemctl enable raspmidi-lcd.service")
    if exit_code == 0:
        print("✅ Serviço habilitado")
    else:
        print(f"❌ Erro ao habilitar serviço: {error}")
    
    print()
    
    # 5. Configurar rc.local para garantir framebuffer
    print("5. Configurando rc.local...")
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"# Configuração LCD MPI3501\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Comentário adicionado ao rc.local")
    
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"modprobe fbtft_device name=mpi3501 gpios=reset:25,dc:24,led:18 speed=32000000 rotate=90\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Driver LCD adicionado ao rc.local")
    
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"sleep 5\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Aguardo adicionado ao rc.local")
    
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"con2fbmap 1 1\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Mapeamento de console adicionado ao rc.local")
    
    exit_code, output, error = run_ssh_command("sudo sh -c 'echo \"chmod 666 /dev/fb1\" >> /etc/rc.local'")
    if exit_code == 0:
        print("✅ Permissões adicionadas ao rc.local")
    
    print()
    
    # 6. Criar script de teste
    print("6. Criando script de teste...")
    test_script = """#!/bin/bash
# Script para testar o serviço LCD
echo "🧪 Testando serviço LCD..."

# Verificar se o framebuffer está disponível
if [ -e /dev/fb1 ]; then
    echo "✅ Framebuffer /dev/fb1 disponível"
else
    echo "❌ Framebuffer /dev/fb1 não encontrado"
    exit 1
fi

# Verificar se o serviço está rodando
if sudo systemctl is-active --quiet raspmidi-lcd.service; then
    echo "✅ Serviço LCD está rodando"
else
    echo "❌ Serviço LCD não está rodando"
    echo "Iniciando serviço..."
    sudo systemctl start raspmidi-lcd.service
    sleep 3
    
    if sudo systemctl is-active --quiet raspmidi-lcd.service; then
        echo "✅ Serviço LCD iniciado com sucesso"
    else
        echo "❌ Falha ao iniciar serviço LCD"
        sudo systemctl status raspmidi-lcd.service
    fi
fi

# Verificar logs
echo "📋 Últimos logs do serviço LCD:"
sudo journalctl -u raspmidi-lcd.service -n 10 --no-pager
"""
    
    # Salva o script de teste
    with open("test_lcd_service.sh", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    # Copia para o Raspberry Pi
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        sftp.put("test_lcd_service.sh", "/tmp/test_lcd_service.sh")
        sftp.close()
        client.close()
        
        # Move e configura o script de teste
        exit_code, output, error = run_ssh_command("mv /tmp/test_lcd_service.sh ~/test_lcd_service.sh && chmod +x ~/test_lcd_service.sh")
        if exit_code == 0:
            print("✅ Script de teste criado")
        else:
            print(f"❌ Erro ao criar script de teste: {error}")
            
    except Exception as e:
        print(f"❌ Erro ao copiar script de teste: {e}")
    
    print()
    print("🎉 Configuração do serviço LCD concluída!")
    print()
    print("📋 Sequência de inicialização após reiniciar:")
    print("1. Sistema inicia")
    print("2. rc.local carrega driver LCD e configura framebuffer")
    print("3. Serviço raspmidi.service inicia")
    print("4. Serviço raspmidi-lcd.service inicia")
    print("5. LCD mostra informações em tempo real")
    print()
    print("🔧 Comandos úteis:")
    print("- Testar agora: ~/test_lcd_service.sh")
    print("- Ver logs: sudo journalctl -u raspmidi-lcd.service -f")
    print("- Reiniciar serviço: sudo systemctl restart raspmidi-lcd.service")
    print("- Ver status: sudo systemctl status raspmidi-lcd.service")
    print("- Reiniciar para testar: sudo reboot")

if __name__ == "__main__":
    main() 