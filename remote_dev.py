#!/usr/bin/env python3
"""
Script para desenvolvimento remoto no Raspberry Pi
Permite sincronizar código e executar comandos remotamente
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

class RemoteDev:
    def __init__(self, host="192.168.15.8", user="matheus", project_path="/home/matheus/RaspMIDI"):
        self.host = host
        self.user = user
        self.project_path = project_path
        self.ssh_base = f"ssh {user}@{host}"
        self.scp_base = f"scp"
    
    def test_connection(self):
        """Testa conexão SSH"""
        print(f"🔍 Testando conexão com {self.user}@{self.host}...")
        
        result = subprocess.run(
            f"{self.ssh_base} 'echo Connection OK'",
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("✅ Conexão SSH estabelecida")
            return True
        else:
            print(f"❌ Falha na conexão SSH: {result.stderr}")
            return False
    
    def sync_code(self, local_path=".", exclude_patterns=None):
        """Sincroniza código local com o Raspberry Pi"""
        if exclude_patterns is None:
            exclude_patterns = [
                "venv/", "__pycache__/", "*.pyc", "logs/", "*.log",
                "*.db", ".git/", "node_modules/", ".vscode/"
            ]
        
        print("📤 Sincronizando código...")
        
        # Construir comando rsync
        exclude_args = " ".join([f"--exclude='{pattern}'" for pattern in exclude_patterns])
        
        cmd = f"rsync -avz --delete {exclude_args} {local_path}/ {self.user}@{self.host}:{self.project_path}/"
        
        print(f"   Executando: {cmd}")
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print("✅ Código sincronizado")
            return True
        else:
            print("❌ Falha na sincronização")
            return False
    
    def run_remote_command(self, command, description=""):
        """Executa comando remoto"""
        if description:
            print(f"🔄 {description}")
        
        full_command = f"{self.ssh_base} 'cd {self.project_path} && {command}'"
        print(f"   Executando: {command}")
        
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Comando executado com sucesso")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Erro: {result.stderr.strip()}")
            return False
    
    def install_dependencies(self):
        """Instala dependências no Raspberry Pi"""
        print("📦 Instalando dependências...")
        
        commands = [
            "source venv/bin/activate && pip install -r requirements.txt",
            "python -c \"from app.database.database import init_db; init_db()\""
        ]
        
        for cmd in commands:
            if not self.run_remote_command(cmd):
                return False
        
        return True
    
    def start_app(self):
        """Inicia a aplicação no Raspberry Pi"""
        print("🚀 Iniciando aplicação...")
        
        # Parar aplicação se estiver rodando
        self.run_remote_command("pkill -f 'python.*run.py'", "Parando aplicação anterior")
        time.sleep(2)
        
        # Iniciar em background
        cmd = "nohup source venv/bin/activate && python run.py > app.log 2>&1 &"
        return self.run_remote_command(cmd, "Iniciando aplicação")
    
    def stop_app(self):
        """Para a aplicação no Raspberry Pi"""
        print("🛑 Parando aplicação...")
        return self.run_remote_command("pkill -f 'python.*run.py'")
    
    def get_logs(self, lines=50):
        """Obtém logs da aplicação"""
        print(f"📋 Obtendo últimos {lines} linhas do log...")
        
        cmd = f"tail -n {lines} app.log"
        result = subprocess.run(
            f"{self.ssh_base} 'cd {self.project_path} && {cmd}'",
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("📄 Logs da aplicação:")
            print("-" * 50)
            print(result.stdout)
            print("-" * 50)
        else:
            print("❌ Erro ao obter logs")
    
    def check_status(self):
        """Verifica status da aplicação"""
        print("📊 Verificando status...")
        
        # Verificar se está rodando
        cmd = "ps aux | grep 'python.*run.py' | grep -v grep"
        result = subprocess.run(
            f"{self.ssh_base} 'cd {self.project_path} && {cmd}'",
            shell=True, capture_output=True, text=True
        )
        
        if result.stdout.strip():
            print("✅ Aplicação está rodando")
            print(f"   Processos: {result.stdout.strip()}")
        else:
            print("❌ Aplicação não está rodando")
        
        # Verificar portas
        cmd = "netstat -tlnp | grep :5000"
        result = subprocess.run(
            f"{self.ssh_base} '{cmd}'",
            shell=True, capture_output=True, text=True
        )
        
        if result.stdout.strip():
            print("✅ Porta 5000 está ativa")
        else:
            print("❌ Porta 5000 não está ativa")
    
    def setup_ssh_key(self):
        """Configura chave SSH para acesso sem senha"""
        print("🔑 Configurando chave SSH...")
        
        # Verificar se já existe chave
        if os.path.exists(os.path.expanduser("~/.ssh/id_rsa.pub")):
            print("   Chave SSH já existe")
            
            # Copiar chave para Raspberry Pi
            cmd = f"ssh-copy-id {self.user}@{self.host}"
            result = subprocess.run(cmd, shell=True)
            
            if result.returncode == 0:
                print("✅ Chave SSH configurada")
                return True
            else:
                print("❌ Falha ao configurar chave SSH")
                return False
        else:
            print("   Gerando nova chave SSH...")
            cmd = "ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ''"
            result = subprocess.run(cmd, shell=True)
            
            if result.returncode == 0:
                return self.setup_ssh_key()
            else:
                print("❌ Falha ao gerar chave SSH")
                return False

def main():
    """Função principal"""
    print("🍓 RaspMIDI - Desenvolvimento Remoto")
    print("=" * 50)
    
    # Configuração
    host = input("IP do Raspberry Pi (192.168.15.8): ").strip() or "192.168.15.8"
    user = input("Usuário (matheus): ").strip() or "matheus"
    
    dev = RemoteDev(host, user)
    
    # Menu de opções
    while True:
        print("\n📋 Opções:")
        print("1. Testar conexão")
        print("2. Configurar chave SSH")
        print("3. Sincronizar código")
        print("4. Instalar dependências")
        print("5. Iniciar aplicação")
        print("6. Parar aplicação")
        print("7. Verificar status")
        print("8. Ver logs")
        print("9. Deploy completo")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            dev.test_connection()
        elif choice == "2":
            dev.setup_ssh_key()
        elif choice == "3":
            dev.sync_code()
        elif choice == "4":
            dev.install_dependencies()
        elif choice == "5":
            dev.start_app()
        elif choice == "6":
            dev.stop_app()
        elif choice == "7":
            dev.check_status()
        elif choice == "8":
            lines = input("Número de linhas (50): ").strip() or "50"
            dev.get_logs(int(lines))
        elif choice == "9":
            print("🚀 Deploy completo...")
            if dev.test_connection():
                dev.sync_code()
                dev.install_dependencies()
                dev.start_app()
                dev.check_status()
        elif choice == "0":
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main() 