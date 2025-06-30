#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug da criação de patch
"""

import requests
import json

def debug_patch_creation():
    """Debug da criação de patch"""
    
    base_url = "http://192.168.15.8:5000"
    
    print("🐛 Debug da criação de patch...")
    
    # Dados de teste
    patch_data = {
        "name": "Teste Debug",
        "input_device": "Chocolate MIDI",
        "input_channel": 0,
        "output_device": "Zoom G3X",
        "zoom_bank": "A",
        "zoom_patch": 5,
        "zoom_bank_letter": "A",
        "command_type": "pc",
        "program": 5
    }
    
    print("📤 Dados que serão enviados:")
    print(json.dumps(patch_data, indent=2))
    
    try:
        # 1. Testar criação
        print("\n1️⃣ Testando criação de patch...")
        
        response = requests.post(f"{base_url}/api/patches", json=patch_data)
        print(f"📥 Status da resposta: {response.status_code}")
        
        data = response.json()
        print(f"📋 Resposta completa:")
        print(json.dumps(data, indent=2))
        
        if data['success']:
            patch_id = data['data']['id']
            print(f"✅ Patch criado com ID: {patch_id}")
            
            # 2. Verificar patch criado
            print("\n2️⃣ Verificando patch criado...")
            
            response = requests.get(f"{base_url}/api/patches/{patch_id}")
            data = response.json()
            
            if data['success']:
                patch = data['data']
                print(f"📋 Patch recuperado:")
                print(json.dumps(patch, indent=2))
                
                # 3. Verificar se os campos estão corretos
                print("\n3️⃣ Verificando campos...")
                print(f"   zoom_bank: {patch.get('zoom_bank')} (tipo: {type(patch.get('zoom_bank'))})")
                print(f"   zoom_patch: {patch.get('zoom_patch')} (tipo: {type(patch.get('zoom_patch'))})")
                print(f"   zoom_bank_letter: {patch.get('zoom_bank_letter')} (tipo: {type(patch.get('zoom_bank_letter'))})")
                print(f"   program: {patch.get('program')} (tipo: {type(patch.get('program'))})")
                
            else:
                print(f"❌ Erro ao recuperar patch: {data['error']}")
                
        else:
            print(f"❌ Erro na criação: {data['error']}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    debug_patch_creation() 