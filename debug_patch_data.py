#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug dos dados dos patches após reinicialização
Para identificar onde os dados estão sendo corrompidos
"""

import requests
import json
import sqlite3
import os
from datetime import datetime

def debug_patch_data():
    """Verifica os dados dos patches em diferentes níveis"""
    
    base_url = "http://192.168.15.8:5000/api"
    
    print("=== DEBUG DOS DADOS DOS PATCHES ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # 1. Verifica dados via API
    print("--- 1. DADOS VIA API ---")
    try:
        response = requests.get(f"{base_url}/patches")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {response.status_code}")
            print(f"📊 Total de patches: {data.get('count', 0)}")
            
            if data.get('success') and data.get('data'):
                print("\n📋 Patches via API:")
                for i, patch in enumerate(data['data'], 1):
                    print(f"  {i}. {patch.get('name', 'Sem nome')}")
                    print(f"     ID: {patch.get('id')}")
                    print(f"     Input Device: {patch.get('input_device')}")
                    print(f"     Output Device: {patch.get('output_device')}")
                    print(f"     Command Type: {patch.get('command_type')}")
                    print(f"     Input Channel: {patch.get('input_channel')}")
                    print(f"     Program: {patch.get('program')}")
                    print(f"     Effects: {patch.get('effects')}")
                    print(f"     Created: {patch.get('created_at')}")
                    print(f"     Updated: {patch.get('updated_at')}")
                    print()
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao acessar API: {e}")
    
    # 2. Verifica dados direto no banco SQLite
    print("--- 2. DADOS DIRETO NO BANCO ---")
    try:
        db_path = "data/raspmidi.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM patches ORDER BY id")
            rows = cursor.fetchall()
            
            print(f"✅ Banco encontrado: {db_path}")
            print(f"📊 Total de patches no banco: {len(rows)}")
            
            # Mostra estrutura da tabela
            cursor.execute("PRAGMA table_info(patches)")
            columns = cursor.fetchall()
            print(f"📋 Estrutura da tabela patches:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            print()
            
            # Mostra dados brutos
            print("📋 Dados brutos do banco:")
            for i, row in enumerate(rows, 1):
                print(f"  {i}. ID: {row[0]}")
                print(f"     Nome: {row[1]}")
                print(f"     Effects (JSON): {row[2]}")
                print(f"     Input Device: {row[3]}")
                print(f"     Input Channel: {row[4]}")
                print(f"     Output Device: {row[5]}")
                print(f"     Command Type: {row[6]}")
                print(f"     Zoom Bank: {row[7]}")
                print(f"     Zoom Patch: {row[8]}")
                print(f"     Program: {row[9]}")
                print(f"     CC: {row[10]}")
                print(f"     Value: {row[11]}")
                print(f"     Note: {row[12]}")
                print(f"     Velocity: {row[13]}")
                print(f"     Created: {row[14]}")
                print(f"     Updated: {row[15]}")
                print()
            
            conn.close()
        else:
            print(f"❌ Banco não encontrado: {db_path}")
    except Exception as e:
        print(f"❌ Erro ao acessar banco: {e}")
    
    # 3. Verifica cache
    print("--- 3. DADOS DO CACHE ---")
    try:
        response = requests.get(f"{base_url}/cache/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cache Info: {response.status_code}")
            if data.get('success'):
                cache_info = data.get('data', {})
                print(f"📊 Cache Info: {json.dumps(cache_info, indent=2)}")
            else:
                print(f"❌ Cache Error: {data.get('error')}")
        else:
            print(f"❌ Cache API Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao acessar cache: {e}")
    
    # 4. Verifica status dos dispositivos
    print("--- 4. STATUS DOS DISPOSITIVOS ---")
    try:
        response = requests.get(f"{base_url}/midi/devices/status_detailed")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Devices Status: {response.status_code}")
            if data.get('success') and data.get('data'):
                for device in data['data']:
                    print(f"📱 {device.get('name')}: {device.get('connected', False)}")
                    print(f"   Tipo: {device.get('type')}")
                    print(f"   Banco: {device.get('bank')}")
                    print(f"   Last PC: {device.get('last_pc')}")
                    print()
        else:
            print(f"❌ Devices API Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao acessar dispositivos: {e}")
    
    # 5. Verifica se há patches corrompidos
    print("--- 5. VERIFICAÇÃO DE CORRUPÇÃO ---")
    try:
        response = requests.get(f"{base_url}/patches")
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                corrupted_patches = []
                for patch in data['data']:
                    # Verifica se campos obrigatórios estão vazios ou incorretos
                    if not patch.get('name') or patch.get('name') == '':
                        corrupted_patches.append(f"Patch {patch.get('id')}: Nome vazio")
                    if not patch.get('input_device') or patch.get('input_device') == '':
                        corrupted_patches.append(f"Patch {patch.get('id')}: Input device vazio")
                    if not patch.get('output_device') or patch.get('output_device') == '':
                        corrupted_patches.append(f"Patch {patch.get('id')}: Output device vazio")
                    if not patch.get('command_type') or patch.get('command_type') == '':
                        corrupted_patches.append(f"Patch {patch.get('id')}: Command type vazio")
                
                if corrupted_patches:
                    print("❌ Patches corrompidos encontrados:")
                    for corruption in corrupted_patches:
                        print(f"   - {corruption}")
                else:
                    print("✅ Nenhum patch corrompido detectado")
    except Exception as e:
        print(f"❌ Erro na verificação de corrupção: {e}")
    
    print("\n=== DEBUG CONCLUÍDO ===")

if __name__ == "__main__":
    debug_patch_data() 