#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Patches - Debuga os patches para verificar a estrutura dos dados
"""

import requests
import json

def debug_patches():
    """Debuga os patches para verificar a estrutura dos dados"""
    base_url = "http://192.168.4.1:5000"
    
    print("🔍 Debugando patches...")
    print("=" * 60)
    
    # 1. Busca todos os patches
    print("\n1. Buscando todos os patches:")
    try:
        response = requests.get(f"{base_url}/api/patches")
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['data']:
                patches = data['data']
                print(f"   ✅ Total de patches: {len(patches)}")
                
                # Filtra patches do Chocolate
                chocolate_patches = [p for p in patches if p.get('input_device') == 'Chocolate MIDI']
                print(f"   🎹 Patches do Chocolate: {len(chocolate_patches)}")
                
                # Mostra estrutura de cada patch do Chocolate
                for i, patch in enumerate(chocolate_patches):
                    print(f"\n   Patch {i + 1}: {patch.get('name', 'Sem nome')}")
                    print(f"      ID: {patch.get('id')}")
                    print(f"      Input Device: {patch.get('input_device')}")
                    print(f"      Input Channel: {patch.get('input_channel')}")
                    print(f"      Program: {patch.get('program')}")
                    print(f"      Zoom Bank: {patch.get('zoom_bank')}")
                    print(f"      Zoom Patch: {patch.get('zoom_patch')}")
                    print(f"      Command Type: {patch.get('command_type')}")
                    
                    # Verifica se tem os campos necessários
                    has_program = patch.get('program') is not None
                    has_channel = patch.get('input_channel') is not None
                    has_zoom_config = patch.get('zoom_bank') is not None and patch.get('zoom_patch') is not None
                    
                    print(f"      ✅ Tem program: {has_program}")
                    print(f"      ✅ Tem input_channel: {has_channel}")
                    print(f"      ✅ Tem config Zoom: {has_zoom_config}")
            else:
                print(f"   ❌ Erro na resposta: {data.get('success', 'N/A')}")
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 2. Testa busca específica por program
    print("\n2. Testando busca por program:")
    test_programs = [0, 1, 2, 3]
    
    for program in test_programs:
        print(f"\n   Program {program}:")
        try:
            response = requests.get(f"{base_url}/api/patches")
            if response.status_code == 200:
                data = response.json()
                if data['success'] and data['data']:
                    patches = data['data']
                    
                    # Busca por program
                    by_program = [p for p in patches if p.get('input_device') == 'Chocolate MIDI' and p.get('program') == program]
                    print(f"      Por program: {len(by_program)} patches")
                    
                    # Busca por input_channel
                    by_channel = [p for p in patches if p.get('input_device') == 'Chocolate MIDI' and p.get('input_channel') == program]
                    print(f"      Por input_channel: {len(by_channel)} patches")
                    
                    if by_program:
                        print(f"      ✅ Encontrado por program: {by_program[0].get('name')}")
                    elif by_channel:
                        print(f"      ✅ Encontrado por input_channel: {by_channel[0].get('name')}")
                    else:
                        print(f"      ❌ Não encontrado")
                else:
                    print(f"      ❌ Erro na resposta")
            else:
                print(f"      ❌ Erro HTTP: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Erro: {str(e)}")
    
    # 3. Verifica patch ativo
    print("\n3. Patch ativo atual:")
    try:
        response = requests.get(f"{base_url}/api/patches/active")
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['data']:
                active_patch = data['data'].get('active_patch')
                if active_patch:
                    print(f"   ✅ Patch ativo: {active_patch.get('name')}")
                    print(f"      Program: {active_patch.get('program')}")
                    print(f"      Input Channel: {active_patch.get('input_channel')}")
                else:
                    print(f"   ⚠️ Nenhum patch ativo")
            else:
                print(f"   ❌ Erro na resposta")
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Debug concluído")

if __name__ == "__main__":
    debug_patches() 