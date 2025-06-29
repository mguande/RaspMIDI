#!/usr/bin/env python3
"""
Script de deploy para executar diretamente no Raspberry Pi
"""

import os
import subprocess
import sys
import time
import requests
import json

# Configurações
RASPBERRY_PATH = "/home/matheus/RaspMIDI"
PC_IP = "192.168.15.7"  # IP do seu PC Windows
PC_PORT = 8000  # Porta para servir os arquivos

def create_simple_server():
    """Cria um servidor HTTP simples no PC para servir os arquivos"""
    server_script = f"""
import http.server
import socketserver
import os

os.chdir(r'C:\\Projetos\\MIDI\\RaspMIDI')

PORT = {PC_PORT}
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Servidor rodando em http://localhost:{{PORT}}")
    httpd.serve_forever()
"""
    
    with open("temp_server.py", "w") as f:
        f.write(server_script)
    
    print("📁 Servidor temporário criado: temp_server.py")
    print(f"🌐 Execute no PC: python temp_server.py")
    print(f"📍 Servidor estará em: http://{PC_IP}:{PC_PORT}")

def download_file(url, local_path):
    """Baixa um arquivo do servidor"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Cria o diretório se não existir
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"❌ Erro ao baixar {url}: {e}")
        return False

def restart_application():
    """Reinicia a aplicação"""
    print("🔄 Reiniciando aplicação...")
    
    # Para o processo atual
    try:
        subprocess.run(["pkill", "-f", "python run.py"], check=False)
        print("✅ Processo anterior finalizado")
    except:
        pass
    
    # Aguarda um pouco
    time.sleep(2)
    
    # Inicia a aplicação
    try:
        os.chdir(RASPBERRY_PATH)
        start_cmd = f"source venv/bin/activate && nohup python run.py > logs/app.log 2>&1 &"
        subprocess.run(start_cmd, shell=True, check=True)
        print("✅ Aplicação reiniciada com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao reiniciar aplicação: {e}")
        return False

def check_application_status():
    """Verifica o status da aplicação"""
    print("🔍 Verificando status da aplicação...")
    
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if "python run.py" in result.stdout:
            print("✅ Aplicação está rodando")
            return True
        else:
            print("❌ Aplicação não está rodando")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Deploy direto no Raspberry Pi")
    print(f"📍 PC IP: {PC_IP}")
    print(f"📍 Porta: {PC_PORT}")
    print()
    
    # Lista de arquivos para baixar
    files_to_download = [
        ("app/web/static/js/app.js", f"{RASPBERRY_PATH}/app/web/static/js/app.js"),
        ("app/main.py", f"{RASPBERRY_PATH}/app/main.py"),
        ("run.py", f"{RASPBERRY_PATH}/run.py"),
    ]
    
    print("📥 Baixando arquivos...")
    all_success = True
    
    for remote_path, local_path in files_to_download:
        url = f"http://{PC_IP}:{PC_PORT}/{remote_path}"
        print(f"📁 Baixando {remote_path}...")
        
        if download_file(url, local_path):
            print(f"✅ {remote_path} baixado com sucesso")
        else:
            print(f"❌ Erro ao baixar {remote_path}")
            all_success = False
    
    if all_success:
        # Reinicia a aplicação
        if restart_application():
            # Aguarda um pouco e verifica o status
            time.sleep(3)
            check_application_status()
            
            print("\n🎉 Deploy concluído!")
            print(f"🌐 Acesse: http://192.168.15.8:5000")
        else:
            print("\n❌ Erro ao reiniciar aplicação!")
    else:
        print("\n❌ Deploy falhou!")
    
    return all_success

if __name__ == "__main__":
    main() 