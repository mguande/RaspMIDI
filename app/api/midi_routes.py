# -*- coding: utf-8 -*-
"""
RaspMIDI - Rotas MIDI
"""

import logging
from flask import Blueprint, request, jsonify, current_app

midi_bp = Blueprint('midi', __name__)
logger = logging.getLogger(__name__)

@midi_bp.route('/send', methods=['POST'])
def send_midi_command():
    """Envia comando MIDI"""
    try:
        data = request.get_json()
        
        if not data or 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Tipo de comando MIDI é obrigatório'
            }), 400
        
        midi_controller = current_app.midi_controller
        success = midi_controller.send_midi_command(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Comando MIDI enviado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao enviar comando MIDI'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao enviar comando MIDI: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/patch/load', methods=['POST'])
def load_patch():
    """Carrega um patch no dispositivo configurado"""
    try:
        data = request.get_json()
        
        if not data or 'patch_id' not in data:
            return jsonify({
                'success': False,
                'error': 'ID do patch é obrigatório'
            }), 400
        
        patch_id = data['patch_id']
        cache_manager = current_app.cache_manager
        midi_controller = current_app.midi_controller
        
        # Obtém patch do cache
        patch = cache_manager.get_patch(patch_id)
        if not patch:
            return jsonify({
                'success': False,
                'error': 'Patch não encontrado'
            }), 404
        
        # Envia patch para o dispositivo configurado
        success = midi_controller.send_patch(patch)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Patch {patch["name"]} carregado com sucesso',
                'data': patch
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao carregar patch'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao carregar patch: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/effect/toggle', methods=['POST'])
def toggle_effect():
    """Liga/desliga um efeito"""
    try:
        data = request.get_json()
        
        if not data or 'effect_name' not in data or 'enabled' not in data:
            return jsonify({
                'success': False,
                'error': 'Nome do efeito e status são obrigatórios'
            }), 400
        
        effect_name = data['effect_name']
        enabled = data['enabled']
        
        midi_controller = current_app.midi_controller
        success = midi_controller.toggle_effect(effect_name, enabled)
        
        if success:
            status = "ligado" if enabled else "desligado"
            return jsonify({
                'success': True,
                'message': f'Efeito {effect_name} {status}',
                'data': {
                    'effect_name': effect_name,
                    'enabled': enabled
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao alternar efeito'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao alternar efeito: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/devices/scan', methods=['POST'])
def scan_devices():
    """Escaneia dispositivos MIDI"""
    try:
        midi_controller = current_app.midi_controller
        devices = midi_controller.scan_devices()
        
        return jsonify({
            'success': True,
            'data': devices
        })
        
    except Exception as e:
        logger.error(f"Erro ao escanear dispositivos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/devices/status', methods=['GET'])
def get_devices_status():
    """Obtém status dos dispositivos MIDI"""
    try:
        midi_controller = current_app.midi_controller
        status = midi_controller.get_device_status()
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status dos dispositivos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/devices/status_detailed', methods=['GET'])
def get_devices_status_detailed():
    """Retorna status detalhado dos dispositivos para o modo palco"""
    try:
        midi_controller = current_app.midi_controller
        devices = midi_controller.get_devices_status_detailed()
        return jsonify({'success': True, 'data': devices})
    except Exception as e:
        logger.error(f"Erro ao obter status detalhado dos dispositivos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@midi_bp.route('/devices/list', methods=['GET'])
def get_available_devices():
    """Lista dispositivos disponíveis categorizados"""
    try:
        midi_controller = current_app.midi_controller
        devices = midi_controller.get_available_devices()
        
        return jsonify({
            'success': True,
            'data': devices
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar dispositivos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/config', methods=['GET'])
def get_midi_config():
    """Obtém configuração MIDI atual"""
    try:
        midi_controller = current_app.midi_controller
        config = midi_controller.get_midi_config()
        
        return jsonify({
            'success': True,
            'data': config
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração MIDI: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/config', methods=['PUT'])
def update_midi_config():
    """Atualiza configuração MIDI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados de configuração são obrigatórios'
            }), 400
        
        midi_controller = current_app.midi_controller
        success = midi_controller.update_midi_config(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuração MIDI atualizada com sucesso',
                'data': midi_controller.get_midi_config()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao atualizar configuração MIDI'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração MIDI: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/cc', methods=['POST'])
def send_cc():
    """Envia mensagem Control Change"""
    try:
        data = request.get_json()
        
        if not data or 'cc' not in data or 'value' not in data:
            return jsonify({
                'success': False,
                'error': 'CC e valor são obrigatórios'
            }), 400
        
        cc = data['cc']
        value = data['value']
        device = data.get('device')  # Dispositivo opcional
        
        midi_controller = current_app.midi_controller
        
        # Se dispositivo especificado, usa ele; senão usa o configurado
        if device:
            success = midi_controller._send_cc_to_device(0, cc, value, device)
        else:
            success = midi_controller._send_cc(0, cc, value)
        
        if success:
            device_info = f" para {device}" if device else ""
            return jsonify({
                'success': True,
                'message': f'CC {cc} = {value} enviado{device_info}',
                'data': {
                    'channel': 0,
                    'cc': cc,
                    'value': value,
                    'device': device
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao enviar CC'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao enviar CC: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/pc', methods=['POST'])
def send_pc():
    """Envia mensagem Program Change"""
    try:
        data = request.get_json()
        
        if not data or 'program' not in data:
            return jsonify({
                'success': False,
                'error': 'Programa é obrigatório'
            }), 400
        
        program = data['program']
        device = data.get('device')  # Dispositivo opcional
        
        midi_controller = current_app.midi_controller
        
        # Se dispositivo especificado, usa ele; senão usa o configurado
        if device:
            success = midi_controller._send_pc_to_device(0, program, device)
        else:
            success = midi_controller._send_pc(0, program)
        
        if success:
            device_info = f" para {device}" if device else ""
            return jsonify({
                'success': True,
                'message': f'Program Change {program} enviado{device_info}',
                'data': {
                    'channel': 0,
                    'program': program,
                    'device': device
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao enviar Program Change'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao enviar Program Change: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/note', methods=['POST'])
def send_note():
    """Envia mensagem Note On/Off"""
    try:
        data = request.get_json()
        
        if not data or 'note' not in data or 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Nota e tipo são obrigatórios'
            }), 400
        
        note = data['note']
        note_type = data['type']  # 'on' ou 'off'
        velocity = data.get('velocity', 64)
        device = data.get('device')  # Dispositivo opcional
        
        midi_controller = current_app.midi_controller
        
        # Se dispositivo especificado, usa ele; senão usa o configurado
        if device:
            if note_type == 'on':
                success = midi_controller._send_note_on_to_device(0, note, velocity, device)
            elif note_type == 'off':
                success = midi_controller._send_note_off_to_device(0, note, device)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Tipo deve ser "on" ou "off"'
                }), 400
        else:
            if note_type == 'on':
                success = midi_controller._send_note_on(0, note, velocity)
            elif note_type == 'off':
                success = midi_controller._send_note_off(0, note)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Tipo deve ser "on" ou "off"'
                }), 400
        
        if success:
            device_info = f" para {device}" if device else ""
            return jsonify({
                'success': True,
                'message': f'Note {note_type}: {note}{device_info}',
                'data': {
                    'channel': 0,
                    'note': note,
                    'type': note_type,
                    'velocity': velocity if note_type == 'on' else None,
                    'device': device
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao enviar nota'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao enviar nota: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/commands/received', methods=['GET'])
def get_received_commands():
    """Lista comandos MIDI recebidos"""
    try:
        midi_controller = current_app.midi_controller
        commands = midi_controller.get_received_commands()
        
        # Log de debug
        if commands:
            logger.info(f"Retornando {len(commands)} comandos MIDI recebidos")
        
        return jsonify({
            'success': True,
            'commands': commands
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter comandos recebidos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/commands/clear', methods=['POST'])
def clear_received_commands():
    """Limpa lista de comandos MIDI recebidos"""
    try:
        midi_controller = current_app.midi_controller
        midi_controller.clear_received_commands()
        
        return jsonify({
            'success': True,
            'message': 'Comandos MIDI recebidos limpos'
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar comandos recebidos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/commands/simulate', methods=['POST'])
def simulate_midi_command():
    """Simula recebimento de comando MIDI para teste"""
    try:
        midi_controller = current_app.midi_controller
        
        # Simula diferentes tipos de comandos
        import random
        import time
        
        command_types = ['cc', 'pc', 'note_on', 'note_off']
        command_type = random.choice(command_types)
        
        command = {
            'type': command_type,
            'channel': random.randint(0, 15),
            'timestamp': time.time()
        }
        
        # Adiciona dados específicos do tipo de comando
        if command_type == 'cc':
            command['cc'] = random.randint(0, 127)
            command['value'] = random.randint(0, 127)
        elif command_type == 'pc':
            command['program'] = random.randint(0, 127)
        elif command_type in ['note_on', 'note_off']:
            command['note'] = random.randint(21, 108)  # A0 a C8
            if command_type == 'note_on':
                command['velocity'] = random.randint(1, 127)
        
        midi_controller.add_received_command(command)
        
        return jsonify({
            'success': True,
            'message': f'Comando {command_type.upper()} simulado',
            'command': command
        })
        
    except Exception as e:
        logger.error(f"Erro ao simular comando MIDI: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/monitor/start', methods=['POST'])
def start_midi_monitoring():
    """Inicia monitoramento de entrada MIDI"""
    try:
        data = request.get_json() or {}
        device = data.get('device')  # Dispositivo opcional
        
        midi_controller = current_app.midi_controller
        success = midi_controller.start_midi_input_monitoring(device)
        
        if success:
            message = 'Monitoramento MIDI iniciado'
            if device:
                message += f' no dispositivo: {device}'
            
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha ao iniciar monitoramento MIDI'
            }), 400
        
    except Exception as e:
        logger.error(f"Erro ao iniciar monitoramento MIDI: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/monitor/stop', methods=['POST'])
def stop_midi_monitoring():
    """Para monitoramento de entrada MIDI"""
    try:
        midi_controller = current_app.midi_controller
        success = midi_controller.stop_midi_input_monitoring()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Monitoramento MIDI parado'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha ao parar monitoramento MIDI'
            }), 400
        
    except Exception as e:
        logger.error(f"Erro ao parar monitoramento MIDI: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/monitor/status', methods=['GET'])
def get_midi_monitoring_status():
    """Retorna status do monitoramento MIDI"""
    try:
        midi_controller = current_app.midi_controller
        status = midi_controller.get_monitoring_status()
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status do monitoramento: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/sysex/tuner', methods=['POST'])
def sysex_tuner():
    device = request.json.get('device')
    try:
        # Afinador: F0 52 00 6E 64 0B F7
        sysex = [0x52, 0x00, 0x6E, 0x64, 0x0B]
        midi_controller.send_sysex(sysex, device)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@midi_bp.route('/sysex/effect', methods=['POST'])
def sysex_effect():
    device = request.json.get('device')
    block = int(request.json.get('block'))
    state = int(request.json.get('state'))  # 0=off, 1=on
    try:
        # Ligar/desligar efeito: F0 52 00 6E 64 03 00 bb 00 00 ss F7
        sysex = [0x52, 0x00, 0x6E, 0x64, 0x03, 0x00, block, 0x00, 0x00, state]
        midi_controller.send_sysex(sysex, device)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@midi_bp.route('/sysex/patch', methods=['POST'])
def sysex_patch():
    """Envia comando SysEx para selecionar patch"""
    try:
        data = request.get_json()
        
        if not data or 'patch_number' not in data:
            return jsonify({
                'success': False,
                'error': 'Número do patch é obrigatório'
            }), 400
        
        patch_number = data['patch_number']
        device = data.get('device', 'Zoom G3X')
        
        midi_controller = current_app.midi_controller
        success = midi_controller.send_sysex_patch(patch_number, device)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Patch {patch_number} selecionado no {device}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao selecionar patch'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao selecionar patch: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rotas para Bancos
@midi_bp.route('/banks', methods=['GET'])
def get_banks():
    """Lista todos os bancos"""
    try:
        db_manager = current_app.db_manager
        banks = db_manager.get_all_banks()
        
        return jsonify({
            'success': True,
            'data': [bank.to_dict() for bank in banks]
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar bancos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/banks/<int:bank_id>', methods=['GET'])
def get_bank(bank_id):
    """Obtém um banco específico"""
    try:
        db_manager = current_app.db_manager
        bank = db_manager.get_bank(bank_id)
        
        if not bank:
            return jsonify({
                'success': False,
                'error': 'Banco não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': bank.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter banco: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/banks', methods=['POST'])
def create_bank():
    """Cria um novo banco"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'Nome do banco é obrigatório'
            }), 400
        
        from app.database.models import Bank, BankMapping
        
        # Cria o banco
        bank = Bank(
            name=data['name'],
            description=data.get('description', ''),
            active=data.get('active', False)
        )
        
        # Adiciona mapeamentos se existirem
        if 'mappings' in data:
            for mapping_data in data['mappings']:
                mapping = BankMapping(
                    input_type=mapping_data.get('input_type', ''),
                    input_channel=mapping_data.get('input_channel', 0),
                    input_control=mapping_data.get('input_control'),
                    input_value=mapping_data.get('input_value'),
                    output_device=mapping_data.get('output_device', ''),
                    output_type=mapping_data.get('output_type', ''),
                    output_channel=mapping_data.get('output_channel', 0),
                    output_control=mapping_data.get('output_control'),
                    output_value=mapping_data.get('output_value'),
                    output_program=mapping_data.get('output_program'),
                    description=mapping_data.get('description', '')
                )
                bank.mappings.append(mapping)
        
        db_manager = current_app.db_manager
        bank_id = db_manager.create_bank(bank)
        
        return jsonify({
            'success': True,
            'message': 'Banco criado com sucesso',
            'data': {'id': bank_id}
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar banco: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/banks/<int:bank_id>', methods=['PUT'])
def update_bank(bank_id):
    """Atualiza um banco"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados do banco são obrigatórios'
            }), 400
        
        db_manager = current_app.db_manager
        bank = db_manager.get_bank(bank_id)
        
        if not bank:
            return jsonify({
                'success': False,
                'error': 'Banco não encontrado'
            }), 404
        
        # Atualiza campos
        if 'name' in data:
            bank.name = data['name']
        if 'description' in data:
            bank.description = data['description']
        if 'active' in data:
            bank.active = data['active']
        
        # Atualiza mapeamentos se fornecidos
        if 'mappings' in data:
            # Remove mapeamentos existentes
            for mapping in bank.mappings:
                db_manager.delete_bank_mapping(mapping.id)
            
            # Adiciona novos mapeamentos
            bank.mappings = []
            for mapping_data in data['mappings']:
                from app.database.models import BankMapping
                mapping = BankMapping(
                    bank_id=bank_id,
                    input_type=mapping_data.get('input_type', ''),
                    input_channel=mapping_data.get('input_channel', 0),
                    input_control=mapping_data.get('input_control'),
                    input_value=mapping_data.get('input_value'),
                    output_device=mapping_data.get('output_device', ''),
                    output_type=mapping_data.get('output_type', ''),
                    output_channel=mapping_data.get('output_channel', 0),
                    output_control=mapping_data.get('output_control'),
                    output_value=mapping_data.get('output_value'),
                    output_program=mapping_data.get('output_program'),
                    description=mapping_data.get('description', '')
                )
                db_manager.create_bank_mapping(mapping)
                bank.mappings.append(mapping)
        
        success = db_manager.update_bank(bank)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Banco atualizado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao atualizar banco'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao atualizar banco: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/banks/<int:bank_id>', methods=['DELETE'])
def delete_bank(bank_id):
    """Deleta um banco"""
    try:
        db_manager = current_app.db_manager
        success = db_manager.delete_bank(bank_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Banco deletado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Banco não encontrado'
            }), 404
        
    except Exception as e:
        logger.error(f"Erro ao deletar banco: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/banks/<int:bank_id>/activate', methods=['POST'])
def activate_bank(bank_id):
    """Ativa um banco (desativa outros)"""
    try:
        db_manager = current_app.db_manager
        success = db_manager.set_active_bank(bank_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Banco ativado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Banco não encontrado'
            }), 404
        
    except Exception as e:
        logger.error(f"Erro ao ativar banco: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/banks/active', methods=['GET'])
def get_active_bank():
    """Obtém o banco ativo"""
    try:
        db_manager = current_app.db_manager
        bank = db_manager.get_active_bank()
        
        if bank:
            return jsonify({
                'success': True,
                'data': bank.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'data': None
            })
        
    except Exception as e:
        logger.error(f"Erro ao obter banco ativo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/devices/power_status', methods=['GET'])
def get_power_status():
    """Verifica status de alimentação dos dispositivos MIDI"""
    try:
        midi_controller = current_app.midi_controller
        
        # Força verificação de alimentação
        midi_controller._check_power_status()
        
        # Obtém status dos dispositivos
        status = midi_controller.get_device_status()
        
        return jsonify({
            'success': True,
            'data': status,
            'message': 'Status de alimentação verificado'
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status de alimentação: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/devices/test_connection', methods=['POST'])
def test_device_connection():
    """Testa conexão com dispositivo específico"""
    try:
        data = request.get_json()
        
        if not data or 'device_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Nome do dispositivo é obrigatório'
            }), 400
        
        device_name = data['device_name']
        midi_controller = current_app.midi_controller
        
        # Testa conexão com o dispositivo
        try:
            import mido
            
            # Tenta abrir a porta e enviar uma mensagem de teste
            with mido.open_output(device_name) as port:
                test_msg = mido.Message('program_change', channel=0, program=0)
                port.send(test_msg)
                
                return jsonify({
                    'success': True,
                    'message': f'Dispositivo {device_name} está respondendo corretamente',
                    'data': {
                        'device_name': device_name,
                        'status': 'connected',
                        'test_result': 'success'
                    }
                })
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Verifica se é problema de alimentação
            if any(keyword in error_msg for keyword in ['timeout', 'not responding', 'no response']):
                return jsonify({
                    'success': False,
                    'error': f'Dispositivo {device_name} não está respondendo',
                    'suggestion': 'Verifique se o dispositivo está conectado à alimentação externa',
                    'data': {
                        'device_name': device_name,
                        'status': 'no_response',
                        'test_result': 'power_issue'
                    }
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': f'Erro ao conectar com {device_name}: {str(e)}',
                    'data': {
                        'device_name': device_name,
                        'status': 'error',
                        'test_result': 'connection_failed'
                    }
                }), 500
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão com dispositivo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/devices/chocolate/reconnect', methods=['POST'])
def reconnect_chocolate():
    """Força reconexão do Chocolate"""
    try:
        midi_controller = current_app.midi_controller
        success = midi_controller.force_reconnect_chocolate()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Chocolate reconectado com sucesso',
                'data': {
                    'device': 'chocolate',
                    'status': 'reconnected'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha ao reconectar Chocolate',
                'data': {
                    'device': 'chocolate',
                    'status': 'reconnection_failed'
                }
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao reconectar Chocolate: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/devices/zoom_g3x/reconnect', methods=['POST'])
def reconnect_zoom_g3x():
    """Força reconexão do Zoom G3X"""
    try:
        midi_controller = current_app.midi_controller
        success = midi_controller.force_reconnect_zoom_g3x()
        return jsonify({
            'success': success,
            'message': 'Zoom G3X reconectado com sucesso' if success else 'Falha ao reconectar Zoom G3X'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao reconectar Zoom G3X: {str(e)}'
        }), 500

@midi_bp.route('/zoom/patches/<bank_letter>', methods=['GET'])
def get_zoom_patches(bank_letter):
    """Tenta importar patches da Zoom G3X para um banco específico"""
    try:
        # Converte letra do banco para número (A=0, B=1, C=2, etc.)
        bank_mapping = {
            'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4,
            'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9
        }
        
        if bank_letter not in bank_mapping:
            return jsonify({
                'success': False,
                'error': 'Letra de banco inválida (A-J)'
            }), 400
        
        bank_number = bank_mapping[bank_letter]
        midi_controller = current_app.midi_controller
        
        # Tenta importar patches da Zoom G3X
        if midi_controller.zoom_g3x and midi_controller.device_status['zoom_g3x']['connected']:
            patches = midi_controller.zoom_g3x.get_bank_patches(bank_number)
            if patches:
                return jsonify({
                    'success': True,
                    'data': patches
                })
        
        # Fallback: patches padrão
        default_patches = []
        
        for i in range(10):
            patch_number = bank_number * 10 + i
            default_patches.append({
                'number': patch_number,
                'name': f"Patch {patch_number}",
                'bank': bank_letter
            })
        
        return jsonify({
            'success': True,
            'data': default_patches
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter patches da Zoom: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@midi_bp.route('/zoom/test-patch-names/<bank_letter>', methods=['GET'])
def test_zoom_patch_names(bank_letter):
    """Testa especificamente a leitura de nomes de patches da Zoom G3X com logs detalhados"""
    try:
        # Converte letra do banco para número
        bank_mapping = {
            'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4,
            'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9
        }
        
        if bank_letter not in bank_mapping:
            return jsonify({
                'success': False,
                'error': 'Letra de banco inválida (A-J)'
            }), 400
        
        bank_number = bank_mapping[bank_letter]
        midi_controller = current_app.midi_controller
        
        if not midi_controller.zoom_g3x:
            return jsonify({
                'success': False,
                'error': 'Controlador Zoom G3X não inicializado'
            }), 500
        
        if not midi_controller.device_status['zoom_g3x']['connected']:
            return jsonify({
                'success': False,
                'error': 'Zoom G3X não está conectado'
            }), 500
        
        # Testa a leitura de patches com logs detalhados
        logger.info(f"Iniciando teste detalhado de nomes de patches para banco {bank_letter}")
        
        patches = midi_controller.zoom_g3x.get_bank_patches(bank_number)
        
        if patches:
            # Analisa os resultados
            generic_names = [p for p in patches if p['name'].startswith('Patch ')]
            real_names = [p for p in patches if not p['name'].startswith('Patch ')]
            
            result = {
                'success': True,
                'bank': bank_letter,
                'total_patches': len(patches),
                'real_names_count': len(real_names),
                'generic_names_count': len(generic_names),
                'patches': patches,
                'real_names': real_names,
                'generic_names': generic_names
            }
            
            logger.info(f"Teste concluído: {len(real_names)} nomes reais, {len(generic_names)} genéricos")
            
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': 'Não foi possível ler patches do banco'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro no teste de nomes de patches: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 