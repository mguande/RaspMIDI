#!/usr/bin/env python3
"""
Script de deploy para Raspberry Pi
Configura o ambiente e instala as dependências necessárias
"""

import os
import sys
import subprocess
import json
import platform

def run_command(command, description=""):
    """Executa um comando e retorna o resultado"""
    print(f"🔄 {description}")
    print(f"   Executando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Sucesso")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"   ❌ Erro: {result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"   ❌ Exceção: {e}")
        return False

def check_raspberry_pi():
    """Verifica se está rodando no Raspberry Pi"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_info = f.read()
            return 'Raspberry Pi' in cpu_info
    except:
        return False

def install_system_dependencies():
    """Instala dependências do sistema"""
    print("📦 Instalando dependências do sistema...")
    
    # Atualizar sistema
    run_command("sudo apt update", "Atualizando repositórios")
    run_command("sudo apt upgrade -y", "Atualizando sistema")
    
    # Instalar dependências Python
    run_command("sudo apt install -y python3 python3-pip python3-venv", "Instalando Python")
    run_command("sudo apt install -y git", "Instalando Git")
    
    # Instalar dependências MIDI
    run_command("sudo apt install -y libasound2-dev", "Instalando ALSA")
    run_command("sudo apt install -y libportmidi-dev", "Instalando PortMidi")
    
    # Instalar dependências de rede
    run_command("sudo apt install -y hostapd dnsmasq", "Instalando servidor WiFi")
    
    return True

def setup_python_environment():
    """Configura ambiente Python"""
    print("🐍 Configurando ambiente Python...")
    
    # Criar ambiente virtual
    if not os.path.exists('venv'):
        run_command("python3 -m venv venv", "Criando ambiente virtual")
    
    # Ativar ambiente virtual
    activate_cmd = "source venv/bin/activate"
    run_command(f"{activate_cmd} && pip install --upgrade pip", "Atualizando pip")
    
    # Instalar dependências
    run_command(f"{activate_cmd} && pip install -r requirements.txt", "Instalando dependências Python")
    
    return True

def setup_midi_permissions():
    """Configura permissões MIDI"""
    print("🎵 Configurando permissões MIDI...")
    
    # Adicionar usuário ao grupo audio
    run_command("sudo usermod -a -G audio matheus", "Adicionando usuário ao grupo audio")
    
    # Configurar permissões para dispositivos MIDI
    run_command("sudo chmod 666 /dev/snd/*", "Configurando permissões de áudio")
    
    return True

def setup_autostart():
    """Configura inicialização automática"""
    print("🚀 Configurando inicialização automática...")
    
    # Criar arquivo de serviço systemd
    service_content = """[Unit]
Description=RaspMIDI Controller
After=network.target

[Service]
Type=simple
User=matheus
WorkingDirectory=/home/matheus/RaspMIDI
Environment=PATH=/home/matheus/RaspMIDI/venv/bin
ExecStart=/home/matheus/RaspMIDI/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('/tmp/raspmidi.service', 'w') as f:
        f.write(service_content)
    
    # Instalar serviço
    run_command("sudo cp /tmp/raspmidi.service /etc/systemd/system/", "Instalando serviço systemd")
    run_command("sudo systemctl daemon-reload", "Recarregando systemd")
    run_command("sudo systemctl enable raspmidi", "Habilitando inicialização automática")
    
    return True

def setup_wifi_hotspot():
    """Configura hotspot WiFi"""
    print("📶 Configurando hotspot WiFi...")
    
    # Configurar hostapd
    hostapd_config = """interface=wlan0
driver=nl80211
ssid=RaspMIDI
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=raspmidi123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
    
    with open('/tmp/hostapd.conf', 'w') as f:
        f.write(hostapd_config)
    
    run_command("sudo cp /tmp/hostapd.conf /etc/hostapd/hostapd.conf", "Configurando hostapd")
    run_command("sudo systemctl enable hostapd", "Habilitando hostapd")
    
    # Configurar dnsmasq
    dnsmasq_config = """interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
"""
    
    with open('/tmp/dnsmasq.conf', 'w') as f:
        f.write(dnsmasq_config)
    
    run_command("sudo cp /tmp/dnsmasq.conf /etc/dnsmasq.conf", "Configurando dnsmasq")
    run_command("sudo systemctl enable dnsmasq", "Habilitando dnsmasq")
    
    return True

def create_config_file():
    """Cria arquivo de configuração padrão"""
    print("⚙️ Criando arquivo de configuração...")
    
    config = {
        "midi": {
            "input_device": "Chocolate MIDI In",
            "output_device": "Zoom G3X MIDI Out"
        },
        "bluetooth": {
            "enabled": False
        },
        "cache": {
            "timeout": 300
        },
        "raspberry_pi": {
            "wifi_hotspot": True,
            "autostart": True,
            "host": "0.0.0.0",
            "port": 5000
        }
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("   ✅ Arquivo config.json criado")
    return True

def main():
    """Função principal"""
    print("🍓 RaspMIDI - Deploy para Raspberry Pi")
    print("=" * 50)
    
    # Verificar se está no Raspberry Pi
    if not check_raspberry_pi():
        print("⚠️  Este script deve ser executado no Raspberry Pi")
        print("   Para desenvolvimento remoto, use SSH ou configure sincronização")
        return False
    
    print("✅ Detectado Raspberry Pi")
    
    # Instalar dependências do sistema
    if not install_system_dependencies():
        print("❌ Falha ao instalar dependências do sistema")
        return False
    
    # Configurar ambiente Python
    if not setup_python_environment():
        print("❌ Falha ao configurar ambiente Python")
        return False
    
    # Configurar permissões MIDI
    if not setup_midi_permissions():
        print("❌ Falha ao configurar permissões MIDI")
        return False
    
    # Criar arquivo de configuração
    if not create_config_file():
        print("❌ Falha ao criar arquivo de configuração")
        return False
    
    # Configurar autostart
    if not setup_autostart():
        print("❌ Falha ao configurar inicialização automática")
        return False
    
    # Configurar hotspot WiFi
    if not setup_wifi_hotspot():
        print("❌ Falha ao configurar hotspot WiFi")
        return False
    
    print("\n🎉 Deploy concluído com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Reinicie o Raspberry Pi: sudo reboot")
    print("2. Conecte-se ao WiFi 'RaspMIDI' (senha: raspmidi123)")
    print("3. Acesse: http://192.168.4.1:5000")
    print("4. Para desenvolvimento remoto, conecte via SSH:")
    print("   ssh matheus@192.168.15.8")
    
    return True

if __name__ == "__main__":
    main() 