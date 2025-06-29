#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Patch Activation - Testa ativação de patches e monitoramento MIDI
"""

import requests
import json
import time

def test_patch_activation():
    """Testa ativação de patches e monitoramento"""
    base_url = "http://192.168.4.1:5000"
    
    print("🔍 Testando ativação de patches...")
    
    # 1. Verifica status dos dispositivos
    print("\n1. Status dos dispositivos:")
    try:
        response = requests.get(f"{base_url}/api/midi/devices/status_detailed")
        if response.status_code == 200:
            devices = response.json()['data']
            for device in devices:
                print(f"   {device['name']}: {'✅ Conectado' if device['connected'] else '❌ Desconectado'}")
                if device['connected']:
                    print(f"      Porta: {device['port']}")
                    print(f"      Último PC: {device.get('last_pc', 'N/A')}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 2. Verifica patches disponíveis
    print("\n2. Patches disponíveis:")
    try:
        response = requests.get(f"{base_url}/api/patches")
        if response.status_code == 200:
            patches = response.json()['data']
            print(f"   Total de patches: {len(patches)}")
            for patch in patches[:5]:  # Mostra apenas os primeiros 5
                print(f"   - {patch['name']} (ID: {patch['id']})")
                print(f"     Chocolate: {patch.get('input_channel', 'N/A')}")
                print(f"     Zoom: {patch.get('zoom_bank', 'N/A')}/{patch.get('zoom_patch', 'N/A')}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 3. Verifica patch ativo
    print("\n3. Patch ativo:")
    try:
        response = requests.get(f"{base_url}/api/patches/active")
        if response.status_code == 200:
            data = response.json()['data']
            active_patch = data.get('active_patch')
            last_command = data.get('last_command')
            
            if active_patch:
                print(f"   ✅ Patch ativo: {active_patch['name']}")
                print(f"      Chocolate: {active_patch.get('input_channel', 'N/A')}")
                print(f"      Zoom: {active_patch.get('zoom_bank', 'N/A')}/{active_patch.get('zoom_patch', 'N/A')}")
            else:
                print("   ❌ Nenhum patch ativo")
            
            if last_command:
                print(f"   📡 Último comando: {last_command['type']} - {last_command}")
            else:
                print("   📡 Nenhum comando recente")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 4. Verifica monitoramento MIDI
    print("\n4. Status do monitoramento MIDI:")
    try:
        response = requests.get(f"{base_url}/api/midi/monitor/status")
        if response.status_code == 200:
            status = response.json()['data']
            print(f"   Ativo: {'✅ Sim' if status['active'] else '❌ Não'}")
            print(f"   Dispositivo: {status.get('device', 'N/A')}")
            print(f"   Modo: {status.get('mode', 'N/A')}")
            print(f"   Comandos recebidos: {status.get('command_count', 0)}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
    
    # 5. Verifica comandos recebidos
    print("\n5. Comandos MIDI recebidos:")
    try:
        response = requests.get(f"{base_url}/api/midi/commands/received")
        if response.status_code == 200:
            commands = response.json()['data']
            print(f"   Total de comandos: {len(commands)}")
            for cmd in commands[-5:]:  # Mostra apenas os últimos 5
                print(f"   - {cmd['type']}: {cmd}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")

def test_patch_selection(channel):
    """Testa seleção de patch por canal"""
    base_url = "http://192.168.4.1:5000"
    
    print(f"\n🎹 Testando seleção de patch para canal {channel}...")
    
    # 1. Busca patches para o canal
    try:
        response = requests.get(f"{base_url}/api/patches/by_channel/{channel}")
        if response.status_code == 200:
            data = response.json()
            patches = data['data']
            print(f"   Patches encontrados: {len(patches)}")
            
            if patches:
                patch = patches[0]
                print(f"   Patch selecionado: {patch['name']}")
                print(f"      Chocolate: {patch.get('input_channel', 'N/A')}")
                print(f"      Zoom: {patch.get('zoom_bank', 'N/A')}/{patch.get('zoom_patch', 'N/A')}")
                
                # 2. Ativa o patch
                print(f"   Ativando patch...")
                response = requests.post(f"{base_url}/api/midi/chocolate/channel/{channel}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Patch ativado: {result['message']}")
                    
                    # 3. Aguarda um pouco e verifica se ficou ativo
                    time.sleep(1)
                    response = requests.get(f"{base_url}/api/patches/active")
                    if response.status_code == 200:
                        data = response.json()['data']
                        active_patch = data.get('active_patch')
                        if active_patch and active_patch['id'] == patch['id']:
                            print(f"   ✅ Patch permanece ativo na verificação")
                        else:
                            print(f"   ❌ Patch não está ativo na verificação")
                            if active_patch:
                                print(f"      Patch ativo atual: {active_patch['name']}")
                            else:
                                print(f"      Nenhum patch ativo")
                else:
                    print(f"   ❌ Erro ao ativar: {response.status_code}")
                    print(f"      {response.text}")
            else:
                print(f"   ❌ Nenhum patch encontrado para canal {channel}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")

def test_midi_monitoring():
    """Testa monitoramento MIDI"""
    base_url = "http://192.168.4.1:5000"
    
    print("\n📡 Testando monitoramento MIDI...")
    
    # 1. Inicia monitoramento
    try:
        response = requests.post(f"{base_url}/api/midi/monitor/start")
        if response.status_code == 200:
            print("   ✅ Monitoramento iniciado")
            
            # 2. Aguarda um pouco
            time.sleep(2)
            
            # 3. Verifica status
            response = requests.get(f"{base_url}/api/midi/monitor/status")
            if response.status_code == 200:
                status = response.json()['data']
                print(f"   Status: {status}")
            
            # 4. Simula comando MIDI
            print("   Simulando comando Program Change...")
            response = requests.post(f"{base_url}/api/midi/commands/simulate", json={
                'type': 'program_change',
                'channel': 0,
                'program': 5
            })
            if response.status_code == 200:
                print("   ✅ Comando simulado enviado")
                
                # 5. Aguarda e verifica se foi capturado
                time.sleep(1)
                response = requests.get(f"{base_url}/api/midi/commands/received")
                if response.status_code == 200:
                    commands = response.json()['data']
                    if commands:
                        print(f"   ✅ Comando capturado: {commands[-1]}")
                    else:
                        print("   ❌ Comando não foi capturado")
                else:
                    print(f"   ❌ Erro ao verificar comandos: {response.status_code}")
            else:
                print(f"   ❌ Erro ao simular comando: {response.status_code}")
        else:
            print(f"   ❌ Erro ao iniciar monitoramento: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")

if __name__ == "__main__":
    print("🔧 Debug Patch Activation")
    print("=" * 50)
    
    # Testa status geral
    test_patch_activation()
    
    # Testa seleção de patch para canal 5
    test_patch_selection(5)
    
    # Testa monitoramento MIDI
    test_midi_monitoring()
    
    print("\n" + "=" * 50)
    print("✅ Teste concluído") 