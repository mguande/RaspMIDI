#!/usr/bin/env python3
"""
Script para configurar o serviço systemd no Raspberry Pi
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

def copy_service_file():
    """Copia o arquivo de serviço para o Raspberry Pi"""
    try:
        print("📁 Copiando arquivo de serviço...")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(RASPBERRY_IP, username=RASPBERRY_USER, password=RASPBERRY_PASSWORD, timeout=10)
        
        sftp = client.open_sftp()
        
        # Copia o arquivo de serviço
        sftp.put("raspmidi.service", "/tmp/raspmidi.service")
        
        sftp.close()
        client.close()
        
        print("✅ Arquivo copiado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao copiar arquivo: {e}")
        return False

def main():
    print("🔧 Configurando serviço systemd no Raspberry Pi...")
    print()
    
    # Copia o arquivo de serviço
    if not copy_service_file():
        return
    
    # Move o arquivo para o local correto
    print("1. Instalando arquivo de serviço...")
    exit_code, output, error = run_ssh_command("sudo mv /tmp/raspmidi.service /etc/systemd/system/")
    if exit_code == 0:
        print("✅ Arquivo movido para /etc/systemd/system/")
    else:
        print(f"❌ Erro: {error}")
        return
    
    print()
    
    # Recarrega o systemd
    print("2. Recarregando systemd...")
    exit_code, output, error = run_ssh_command("sudo systemctl daemon-reload")
    if exit_code == 0:
        print("✅ systemd recarregado")
    else:
        print(f"❌ Erro: {error}")
        return
    
    print()
    
    # Habilita o serviço para iniciar automaticamente
    print("3. Habilitando serviço para iniciar automaticamente...")
    exit_code, output, error = run_ssh_command("sudo systemctl enable raspmidi.service")
    if exit_code == 0:
        print("✅ Serviço habilitado para iniciar automaticamente")
    else:
        print(f"❌ Erro: {error}")
        return
    
    print()
    
    # Inicia o serviço
    print("4. Iniciando serviço...")
    exit_code, output, error = run_ssh_command("sudo systemctl start raspmidi.service")
    if exit_code == 0:
        print("✅ Serviço iniciado")
    else:
        print(f"❌ Erro: {error}")
        return
    
    print()
    
    # Verifica o status
    print("5. Verificando status do serviço...")
    exit_code, output, error = run_ssh_command("sudo systemctl status raspmidi.service")
    if exit_code == 0:
        print("✅ Status do serviço:")
        print(output)
    else:
        print(f"❌ Erro ao verificar status: {error}")
    
    print()
    
    # Verifica se está configurado para iniciar automaticamente
    print("6. Verificando se está habilitado para iniciar automaticamente...")
    exit_code, output, error = run_ssh_command("sudo systemctl is-enabled raspmidi.service")
    if exit_code == 0 and "enabled" in output:
        print("✅ Serviço configurado para iniciar automaticamente!")
        print("🔄 Agora quando o Raspberry Pi ligar, a aplicação iniciará automaticamente.")
    else:
        print("❌ Serviço não está habilitado para iniciar automaticamente")

if __name__ == "__main__":
    main() 