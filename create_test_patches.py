#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cria patches de teste para diferentes canais do Chocolate MIDI
Para demonstrar a funcionalidade da tela de palco
"""

import requests
import json

def create_test_patches():
    """Cria patches de teste para diferentes canais"""
    
    base_url = "http://192.168.15.8:5000/api"
    
    print("=== Criando Patches de Teste ===")
    print(f"URL base: {base_url}")
    print()
    
    # Patches de teste para diferentes canais
    test_patches = [
        {
            "name": "Clean Channel 1",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 1,
            "program": 0,
            "effects": {
                "compressor": {"enabled": True},
                "reverb": {"enabled": False}
            }
        },
        {
            "name": "Crunch Channel 2",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 2,
            "program": 15,
            "effects": {
                "overdrive": {"enabled": True},
                "delay": {"enabled": True}
            }
        },
        {
            "name": "Lead Channel 3",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 3,
            "program": 30,
            "effects": {
                "distortion": {"enabled": True},
                "chorus": {"enabled": True},
                "delay": {"enabled": True}
            }
        },
        {
            "name": "Acoustic Channel 4",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 4,
            "program": 45,
            "effects": {
                "compressor": {"enabled": True},
                "reverb": {"enabled": True}
            }
        },
        {
            "name": "Metal Channel 5",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 5,
            "program": 60,
            "effects": {
                "distortion": {"enabled": True},
                "noise_gate": {"enabled": True}
            }
        },
        {
            "name": "Jazz Channel 6",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 6,
            "program": 75,
            "effects": {
                "compressor": {"enabled": True},
                "chorus": {"enabled": True},
                "reverb": {"enabled": True}
            }
        }
    ]
    
    created_patches = []
    
    for i, patch_data in enumerate(test_patches, 1):
        print(f"📝 Criando patch {i}/{len(test_patches)}: {patch_data['name']}")
        
        try:
            response = requests.post(f"{base_url}/patches", json=patch_data)
            
            if response.status_code == 201:
                data = response.json()
                if data['success']:
                    patch_id = data['data']['id']
                    created_patches.append({
                        'id': patch_id,
                        'name': patch_data['name'],
                        'channel': patch_data['input_channel']
                    })
                    print(f"✅ Patch criado com ID: {patch_id}")
                else:
                    print(f"❌ Erro ao criar patch: {data.get('error', 'Erro desconhecido')}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Erro ao criar patch: {e}")
    
    print()
    print("=== Resumo dos Patches Criados ===")
    
    if created_patches:
        for patch in created_patches:
            print(f"🎸 {patch['name']} (Canal {patch['channel']}) - ID: {patch['id']}")
        
        print()
        print("✅ Patches criados com sucesso!")
        print("🎹 Agora você pode testar a seleção de canais no Chocolate MIDI")
        print("📱 Acesse a tela de palco para ver as mudanças")
    else:
        print("❌ Nenhum patch foi criado")
    
    return created_patches

if __name__ == "__main__":
    create_test_patches() 