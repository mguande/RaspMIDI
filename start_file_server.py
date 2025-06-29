#!/usr/bin/env python3
"""
Servidor de arquivos simples para deploy
Execute este script no PC Windows para servir os arquivos
"""

import http.server
import socketserver
import os
import sys

# Configurações
PORT = 8000
DIRECTORY = r"C:\Projetos\MIDI\RaspMIDI"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Adiciona headers CORS para permitir acesso do Raspberry Pi
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def main():
    """Função principal"""
    print("🌐 Servidor de arquivos para deploy")
    print(f"📍 Diretório: {DIRECTORY}")
    print(f"📍 Porta: {PORT}")
    print(f"🌐 URL: http://localhost:{PORT}")
    print()
    print("📁 Arquivos disponíveis:")
    
    # Lista alguns arquivos importantes
    important_files = [
        "app/web/static/js/app.js",
        "app/main.py", 
        "run.py"
    ]
    
    for file in important_files:
        file_path = os.path.join(DIRECTORY, file)
        if os.path.exists(file_path):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (não encontrado)")
    
    print()
    print("🚀 Iniciando servidor...")
    print("💡 Pressione Ctrl+C para parar")
    print()
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Servidor rodando em http://localhost:{PORT}")
            print("⏳ Aguardando conexões...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 