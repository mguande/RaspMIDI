#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para baixar o banco de dados do Raspberry Pi
"""

import requests
import os

def download_database():
    """Baixa o banco de dados do Raspberry Pi"""
    
    # URL do servidor de arquivos no Windows
    base_url = "http://192.168.15.100:8000"
    
    print("=== DOWNLOAD DO BANCO DE DADOS ===")
    print(f"🌐 Conectando em: {base_url}")
    
    try:
        # Tenta baixar o banco
        response = requests.get(f"{base_url}/data/raspmidi.db")
        
        if response.status_code == 200:
            # Cria diretório se não existir
            os.makedirs("data", exist_ok=True)
            
            # Salva o arquivo
            with open("data/raspmidi.db", "wb") as f:
                f.write(response.content)
            
            print("✅ Banco de dados baixado com sucesso!")
            print(f"📁 Salvo em: data/raspmidi.db")
            print(f"📊 Tamanho: {len(response.content)} bytes")
            
            return True
        else:
            print(f"❌ Erro ao baixar banco: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    download_database() 