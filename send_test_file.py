#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simples para enviar arquivo de teste para Raspberry Pi
"""

import subprocess
import os

def send_test_file():
    """Envia arquivo de teste para Raspberry Pi"""
    
    # Configurações
    host = "192.168.15.8"
    user = "matheus"
    remote_path = "/home/matheus/RaspMIDI/"
    local_file = "test_zoom_raspberry.py"
    
    if not os.path.exists(local_file):
        print(f"❌ Arquivo {local_file} não encontrado!")
        return
    
    print(f"📁 Enviando {local_file} para {user}@{host}:{remote_path}")
    
    # Comando scp
    scp_cmd = f"scp {local_file} {user}@{host}:{remote_path}"
    
    try:
        result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {local_file} enviado com sucesso!")
            
            # Comando para executar o teste
            print("🚀 Executando teste no Raspberry Pi...")
            ssh_cmd = f"ssh {user}@{host} cd {remote_path} && python3 {local_file}"
            
            result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Teste executado com sucesso!")
                print("📋 Resultado:")
                print(result.stdout)
            else:
                print("❌ Erro ao executar teste:")
                print(result.stderr)
                
        else:
            print(f"❌ Erro ao enviar arquivo:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    send_test_file() 