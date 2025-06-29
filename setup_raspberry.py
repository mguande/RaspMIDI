#!/usr/bin/env python3
"""
Script completo para configurar o Raspberry Pi para o RaspMIDI
"""

import subprocess
import sys
import time

def run_ssh_command(command, description=""):
    """Executa comando SSH no Raspberry Pi"""
    host = "192.168.15.8"
    user = "matheus"
    
    if description:
        print(f"🔄 {description}")
    
    full_command = f"ssh {user}@{host} '{command}'"
    print(f"   Executando: {command}")
    
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Sucesso")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Erro: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def setup_system():
    """Configura o sistema do Raspberry Pi"""
    print("📦 Configurando sistema...")
    
    commands = [
        "sudo apt update",
        "sudo apt upgrade -y",
        "sudo apt install -y python3 python3-pip python3-venv git",
        "sudo apt install -y libasound2-dev libportmidi-dev",
        "sudo apt install -y aconnect",
        "sudo usermod -a -G audio matheus"
    ]
    
    for cmd in commands:
        if not run_ssh_command(cmd):
            print(f"⚠️ Comando falhou: {cmd}")
            # Continuar mesmo se alguns comandos falharem
    
    return True

def clone_repository():
    """Clona o repositório do GitHub"""
    print("📥 Clonando repositório...")
    
    commands = [
        "cd /home/matheus",
        "rm -rf RaspMIDI",
        "git clone https://github.com/mguande/RaspMIDI.git",
        "cd RaspMIDI"
    ]
    
    for cmd in commands:
        if not run_ssh_command(cmd):
            return False
    
    return True

def setup_python_environment():
    """Configura o ambiente Python"""
    print("🐍 Configurando ambiente Python...")
    
    commands = [
        "cd /home/matheus/RaspMIDI",
        "python3 -m venv venv",
        "source venv/bin/activate && pip install --upgrade pip",
        "source venv/bin/activate && pip install -r requirements.txt"
    ]
    
    for cmd in commands:
        if not run_ssh_command(cmd):
            return False
    
    return True

def setup_database():
    """Inicializa o banco de dados"""
    print("🗄️ Inicializando banco de dados...")
    
    cmd = "cd /home/matheus/RaspMIDI && source venv/bin/activate && python -c \"from app.database.database import init_db; init_db()\""
    
    return run_ssh_command(cmd)

def setup_config():
    """Configura arquivo de configuração"""
    print("⚙️ Configurando arquivo de configuração...")
    
    cmd = "cd /home/matheus/RaspMIDI && cp raspberry_config.json config.json"
    
    return run_ssh_command(cmd)

def setup_permissions():
    """Configura permissões"""
    print("🔐 Configurando permissões...")
    
    commands = [
        "sudo chmod 666 /dev/snd/* 2>/dev/null || true",
        "sudo chmod 666 /dev/snd/midi* 2>/dev/null || true",
        "chmod +x /home/matheus/RaspMIDI/start_raspberry.sh"
    ]
    
    for cmd in commands:
        run_ssh_command(cmd)
    
    return True

def test_installation():
    """Testa a instalação"""
    print("🧪 Testando instalação...")
    
    tests = [
        ("Verificar projeto", "cd /home/matheus/RaspMIDI && ls -la"),
        ("Verificar ambiente virtual", "cd /home/matheus/RaspMIDI && ls -la venv/"),
        ("Verificar Python", "cd /home/matheus/RaspMIDI && source venv/bin/activate && python --version"),
        ("Verificar dispositivos MIDI", "aconnect -l"),
        ("Verificar banco de dados", "cd /home/matheus/RaspMIDI && ls -la data/")
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, cmd in tests:
        print(f"\n   Testando: {test_name}")
        if run_ssh_command(cmd):
            passed += 1
        else:
            print(f"   ❌ {test_name} falhou")
    
    print(f"\n🎯 Testes: {passed}/{total} passaram")
    return passed == total

def start_application():
    """Inicia a aplicação"""
    print("🚀 Iniciando aplicação...")
    
    commands = [
        "cd /home/matheus/RaspMIDI",
        "pkill -f 'python.*run.py' 2>/dev/null || true",
        "sleep 2",
        "nohup source venv/bin/activate && python run.py > logs/raspmidi_$(date +%Y%m%d_%H%M%S).log 2>&1 &"
    ]
    
    for cmd in commands:
        if not run_ssh_command(cmd):
            return False
    
    # Aguardar um pouco e verificar se está rodando
    time.sleep(5)
    
    return run_ssh_command("ps aux | grep 'python.*run.py' | grep -v grep")

def main():
    """Função principal"""
    print("🍓 RaspMIDI - Setup Completo do Raspberry Pi")
    print("=" * 60)
    print("⚠️ IMPORTANTE: Digite a senha 'matheus' quando solicitado")
    print("=" * 60)
    
    steps = [
        ("Configuração do Sistema", setup_system),
        ("Clonar Repositório", clone_repository),
        ("Configurar Ambiente Python", setup_python_environment),
        ("Inicializar Banco de Dados", setup_database),
        ("Configurar Arquivo de Configuração", setup_config),
        ("Configurar Permissões", setup_permissions),
        ("Testar Instalação", test_installation),
        ("Iniciar Aplicação", start_application)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        print("-" * 40)
        
        if not step_func():
            print(f"❌ Falha em: {step_name}")
            print("⚠️ Continuando com os próximos passos...")
        else:
            print(f"✅ {step_name} concluído")
    
    print("\n🎉 Setup concluído!")
    print("\n📋 Próximos passos:")
    print("1. Acesse a aplicação: http://192.168.15.8:5000")
    print("2. Use 'python remote_dev.py' para desenvolvimento remoto")
    print("3. Ou conecte via SSH no Cursor: matheus@192.168.15.8")
    print("4. Para ver logs: ssh matheus@192.168.15.8 'tail -f /home/matheus/RaspMIDI/logs/raspmidi_*.log'")

if __name__ == "__main__":
    main() 