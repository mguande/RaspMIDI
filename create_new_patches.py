#!/usr/bin/env python3
import requests

def create_new_patches():
    base_url = "http://192.168.15.8:5000/api"
    
    # Primeiro, deleta todos os patches existentes
    print("=== Deletando patches existentes ===")
    response = requests.get(f"{base_url}/patches")
    data = response.json()
    
    for patch in data['data']:
        print(f"Deletando {patch['name']}...")
        delete_response = requests.delete(f"{base_url}/patches/{patch['id']}")
        print(f"  Status: {delete_response.status_code}")
    
    print("\n=== Criando novos patches ===")
    
    # Cria novos patches corretos
    new_patches = [
        {
            "name": "Clean Channel 1",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 1,
            "program": 0,
            "effects": {"compressor": {"enabled": True}}
        },
        {
            "name": "Crunch Channel 2",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 2,
            "program": 15,
            "effects": {"overdrive": {"enabled": True}}
        },
        {
            "name": "Lead Channel 3",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 3,
            "program": 30,
            "effects": {"distortion": {"enabled": True}}
        },
        {
            "name": "Acoustic Channel 4",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 4,
            "program": 45,
            "effects": {"reverb": {"enabled": True}}
        },
        {
            "name": "Metal Channel 5",
            "input_device": "Chocolate MIDI",
            "output_device": "ZOOM G Series",
            "command_type": "pc",
            "input_channel": 5,
            "program": 60,
            "effects": {"distortion": {"enabled": True}}
        }
    ]
    
    for patch_data in new_patches:
        print(f"Criando {patch_data['name']}...")
        response = requests.post(f"{base_url}/patches", json=patch_data)
        print(f"  Status: {response.status_code}")
        if response.status_code == 201:
            print(f"  ✅ Criado com sucesso")
        else:
            print(f"  ❌ Erro: {response.text}")
    
    print("\n=== Verificação final ===")
    response = requests.get(f"{base_url}/patches")
    data = response.json()
    
    chocolate_patches = [p for p in data['data'] if p.get('input_device') == 'Chocolate MIDI']
    print(f"Patches do Chocolate MIDI: {len(chocolate_patches)}")
    for patch in chocolate_patches:
        print(f"  {patch['name']} (Canal {patch.get('input_channel')})")

if __name__ == "__main__":
    create_new_patches() 