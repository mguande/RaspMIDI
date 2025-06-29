#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para copiar o banco de dados do Raspberry Pi via SSH
"""

import paramiko
import os
from getpass import getpass

def copy_database_from_raspberry():
    """Copia o banco de dados do Raspberry Pi"""
    
    print("=== COPIA DO BANCO DE DADOS DO RASPBERRY PI ===")
    
    # Configurações de conexão
    hostname = "192.168.15.8"
    username = "matheus"
    
    try:
        # Solicita senha
        password = getpass(f"Digite a senha para {username}@{hostname}: ")
        
        # Cria cliente SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"🔗 Conectando em {username}@{hostname}...")
        ssh.connect(hostname, username=username, password=password)
        
        # Caminho do banco no Raspberry Pi
        remote_path = "/home/matheus/RaspMIDI/data/raspmidi.db"
        local_path = "data/raspmidi.db"
        
        # Cria diretório local se não existir
        os.makedirs("data", exist_ok=True)
        
        print(f"📁 Copiando {remote_path} para {local_path}...")
        
        # Usa SFTP para copiar o arquivo
        sftp = ssh.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()
        
        # Verifica se o arquivo foi copiado
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            print(f"✅ Banco copiado com sucesso!")
            print(f"📁 Local: {local_path}")
            print(f"📊 Tamanho: {size} bytes")
        else:
            print("❌ Erro: arquivo não foi copiado")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Erro ao copiar banco: {e}")

if __name__ == "__main__":
    copy_database_from_raspberry() 