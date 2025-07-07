#!/usr/bin/env python3
"""
Script para iniciar o display manualmente
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
    print("🖥️ Iniciando display manualmente...")
    print()
    
    # 1. Verifica se o desktop está rodando
    print("1. Verificando desktop...")
    exit_code, output, error = run_ssh_command("ps aux | grep -E '(lightdm|lxdm|gdm|startx)' | grep -v grep")
    if exit_code == 0 and output:
        print("✅ Desktop manager rodando:")
        print(output)
    else:
        print("❌ Desktop manager não está rodando")
        print("🔄 Tentando iniciar desktop...")
        
        # Tenta iniciar o desktop
        exit_code2, output2, error2 = run_ssh_command("sudo systemctl start lightdm")
        if exit_code2 == 0:
            print("✅ Desktop iniciado")
            time.sleep(5)
        else:
            print(f"❌ Erro ao iniciar desktop: {error2}")
    
    print()
    
    # 2. Verifica se há sessão X11 ativa
    print("2. Verificando sessão X11...")
    exit_code, output, error = run_ssh_command("echo $DISPLAY")
    if exit_code == 0 and output:
        print(f"✅ Display X11: {output}")
    else:
        print("❌ Display X11 não configurado")
        # Tenta configurar
        run_ssh_command("export DISPLAY=:0")
    
    print()
    
    # 3. Para qualquer processo Chromium existente
    print("3. Parando processos Chromium existentes...")
    run_ssh_command("pkill -f chromium")
    time.sleep(2)
    
    print()
    
    # 4. Inicia o Chromium em modo kiosk
    print("4. Iniciando Chromium em modo kiosk...")
    start_command = "nohup chromium-browser --kiosk --disable-web-security --user-data-dir=/tmp/chrome-display http://localhost:5000/display > /tmp/chromium.log 2>&1 &"
    exit_code, output, error = run_ssh_command(start_command)
    
    if exit_code == 0:
        print("✅ Chromium iniciado")
        time.sleep(3)
        
        # Verifica se está rodando
        exit_code2, output2, error2 = run_ssh_command("ps aux | grep chromium | grep -v grep")
        if exit_code2 == 0 and output2:
            print("✅ Chromium rodando:")
            print(output2)
        else:
            print("❌ Chromium não está rodando")
            
            # Verifica logs
            print("📄 Verificando logs do Chromium:")
            exit_code3, output3, error3 = run_ssh_command("cat /tmp/chromium.log")
            if exit_code3 == 0 and output3:
                print(output3)
            else:
                print("❌ Sem logs disponíveis")
    else:
        print(f"❌ Erro ao iniciar Chromium: {error}")
    
    print()
    
    # 5. Verifica se a página está acessível
    print("5. Testando página de display...")
    exit_code, output, error = run_ssh_command("curl -s http://localhost:5000/display | grep -o '<title>.*</title>'")
    if exit_code == 0 and output:
        print(f"✅ Página acessível: {output}")
    else:
        print("❌ Página não acessível")
    
    print()
    
    # 6. Verifica se há erros no sistema
    print("6. Verificando erros do sistema...")
    exit_code, output, error = run_ssh_command("journalctl -n 5 --no-pager | grep -i error")
    if exit_code == 0 and output:
        print("⚠️ Erros encontrados:")
        print(output)
    else:
        print("✅ Sem erros críticos")
    
    print()
    print("🎯 Comandos para debug:")
    print("- Ver logs do Chromium: cat /tmp/chromium.log")
    print("- Ver processos: ps aux | grep chromium")
    print("- Matar Chromium: pkill -f chromium")
    print("- Iniciar manualmente: ~/test_display.sh")

if __name__ == "__main__":
    main() 