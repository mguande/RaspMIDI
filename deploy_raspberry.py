#!/usr/bin/env python3
"""
Script de deploy para Raspberry Pi
"""

import os
import subprocess
import sys
import time

# Configuração
RASPBERRY_IP = "192.168.15.8"
RASPBERRY_USER = "matheus"
RASPBERRY_PASS = "raspberry"
PROJECT_DIR = "/home/matheus/RaspMIDI"

def run_command(command, description):
    """Executa um comando e mostra o resultado"""
    print(f"\n🔧 {description}")
    print(f"📝 Comando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print("✅ Saída:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️ Erros:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Comando falhou com código {result.returncode}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar comando: {e}")
        return False

def deploy():
    """Executa o deploy completo"""
    print("🚀 Iniciando deploy para Raspberry Pi...")
    print(f"📍 IP: {RASPBERRY_IP}")
    print(f"👤 Usuário: {RASPBERRY_USER}")
    print(f"📁 Diretório: {PROJECT_DIR}")
    
    # 1. Para o serviço
    print("\n" + "="*50)
    print("🛑 PARANDO SERVIÇO")
    print("="*50)
    
    stop_cmd = f'sshpass -p "{RASPBERRY_PASS}" ssh -o StrictHostKeyChecking=no {RASPBERRY_USER}@{RASPBERRY_IP} "sudo systemctl stop raspmidi.service"'
    if not run_command(stop_cmd, "Parando serviço raspmidi"):
        print("⚠️ Aviso: Não foi possível parar o serviço")
    
    # 2. Atualiza o código
    print("\n" + "="*50)
    print("📥 ATUALIZANDO CÓDIGO")
    print("="*50)
    
    update_cmd = f'sshpass -p "{RASPBERRY_PASS}" ssh -o StrictHostKeyChecking=no {RASPBERRY_USER}@{RASPBERRY_IP} "cd {PROJECT_DIR} && git pull origin main"'
    if not run_command(update_cmd, "Atualizando código via git"):
        print("❌ Falha ao atualizar código")
        return False
    
    # 3. Instala dependências
    print("\n" + "="*50)
    print("📦 INSTALANDO DEPENDÊNCIAS")
    print("="*50)
    
    deps_cmd = f'sshpass -p "{RASPBERRY_PASS}" ssh -o StrictHostKeyChecking=no {RASPBERRY_USER}@{RASPBERRY_IP} "cd {PROJECT_DIR} && source venv/bin/activate && pip install -r requirements.txt"'
    if not run_command(deps_cmd, "Instalando dependências Python"):
        print("❌ Falha ao instalar dependências")
        return False
    
    # 4. Reinicia o serviço
    print("\n" + "="*50)
    print("🔄 REINICIANDO SERVIÇO")
    print("="*50)
    
    start_cmd = f'sshpass -p "{RASPBERRY_PASS}" ssh -o StrictHostKeyChecking=no {RASPBERRY_USER}@{RASPBERRY_IP} "sudo systemctl start raspmidi.service"'
    if not run_command(start_cmd, "Reiniciando serviço raspmidi"):
        print("❌ Falha ao reiniciar serviço")
        return False
    
    # 5. Verifica status
    print("\n" + "="*50)
    print("✅ VERIFICANDO STATUS")
    print("="*50)
    
    status_cmd = f'sshpass -p "{RASPBERRY_PASS}" ssh -o StrictHostKeyChecking=no {RASPBERRY_USER}@{RASPBERRY_IP} "sudo systemctl status raspmidi.service"'
    run_command(status_cmd, "Verificando status do serviço")
    
    # 6. Testa conectividade
    print("\n" + "="*50)
    print("🌐 TESTANDO CONECTIVIDADE")
    print("="*50)
    
    print("⏳ Aguardando 5 segundos para o serviço inicializar...")
    time.sleep(5)
    
    test_cmd = f'curl -s http://{RASPBERRY_IP}:5000/api/status'
    if run_command(test_cmd, "Testando API"):
        print("✅ API está respondendo!")
    else:
        print("❌ API não está respondendo")
    
    print("\n" + "="*50)
    print("🎉 DEPLOY CONCLUÍDO!")
    print("="*50)
    print(f"🌐 Acesse: http://{RASPBERRY_IP}:5000")
    
    return True

if __name__ == "__main__":
    try:
        success = deploy()
        if success:
            print("\n✅ Deploy realizado com sucesso!")
            sys.exit(0)
        else:
            print("\n❌ Deploy falhou!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Deploy interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1) 