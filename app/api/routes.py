# -*- coding: utf-8 -*-
"""
RaspMIDI - Rotas da API REST
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.database.database import get_db
import os

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/patches', methods=['GET'])
def get_patches():
    """Lista todos os patches"""
    try:
        cache_manager = current_app.cache_manager
        patches = cache_manager.get_patches()
        
        return jsonify({
            'success': True,
            'data': patches,
            'count': len(patches)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar patches: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches/<int:patch_id>', methods=['GET'])
def get_patch(patch_id):
    """Obtém um patch específico"""
    try:
        cache_manager = current_app.cache_manager
        patch = cache_manager.get_patch(patch_id)
        
        if not patch:
            return jsonify({
                'success': False,
                'error': 'Patch não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': patch
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter patch {patch_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches', methods=['POST'])
def create_patch():
    """Cria um novo patch"""
    try:
        logger.info("📝 Recebendo requisição para criar patch")
        
        data = request.get_json()
        logger.info(f"📋 Dados recebidos: {data}")
        
        if not data or 'name' not in data:
            logger.error("❌ Nome do patch é obrigatório")
            return jsonify({
                'success': False,
                'error': 'Nome do patch é obrigatório'
            }), 400
        
        logger.info(f"✅ Dados válidos, criando patch: {data['name']}")
        
        # Verificar se cache manager está disponível
        if not hasattr(current_app, 'cache_manager') or current_app.cache_manager is None:
            logger.error("❌ Cache manager não está disponível")
            return jsonify({
                'success': False,
                'error': 'Cache manager não está disponível'
            }), 500
        
        logger.info("🔧 Cache manager disponível, iniciando criação...")
        
        cache_manager = current_app.cache_manager
        patch_id = cache_manager.add_patch(data)
        
        logger.info(f"🔧 Resultado da criação: patch_id = {patch_id}")
        
        if patch_id:
            logger.info(f"✅ Patch criado com sucesso, ID: {patch_id}")
            return jsonify({
                'success': True,
                'data': {'id': patch_id},
                'message': 'Patch criado com sucesso'
            }), 201
        else:
            logger.error("❌ Falha ao criar patch no cache manager")
            return jsonify({
                'success': False,
                'error': 'Erro ao criar patch'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar patch: {str(e)}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches/<int:patch_id>', methods=['PUT'])
def update_patch(patch_id):
    """Atualiza um patch com validação completa e preservação de dados"""
    try:
        logger.info(f"📝 Recebendo requisição para atualizar patch {patch_id}")
        
        data = request.get_json()
        logger.info(f"📋 Dados recebidos: {data}")
        
        if not data:
            logger.error("❌ Dados do patch são obrigatórios")
            return jsonify({
                'success': False,
                'error': 'Dados do patch são obrigatórios'
            }), 400
        
        # Verificar se cache manager está disponível
        if not hasattr(current_app, 'cache_manager') or current_app.cache_manager is None:
            logger.error("❌ Cache manager não está disponível")
            return jsonify({
                'success': False,
                'error': 'Cache manager não está disponível'
            }), 500
        
        cache_manager = current_app.cache_manager
        
        # 1. Primeiro, busca o patch atual para preservar dados existentes
        current_patch = cache_manager.get_patch(patch_id)
        if not current_patch:
            logger.error(f"❌ Patch {patch_id} não encontrado")
            return jsonify({
                'success': False,
                'error': 'Patch não encontrado'
            }), 404
        
        logger.info(f"📋 Patch atual encontrado: {current_patch}")
        
        # 2. Cria um dicionário mesclado: dados atuais + novos dados
        # Isso garante que campos não enviados pelo frontend sejam preservados
        merged_data = current_patch.copy()
        
        # 3. Atualiza apenas os campos que foram enviados
        # Campos obrigatórios que devem ser sempre validados
        required_fields = ['name', 'input_device', 'output_device', 'command_type']
        
        for field in required_fields:
            if field in data:
                merged_data[field] = data[field]
                logger.info(f"✅ Campo {field} atualizado: {data[field]}")
            else:
                logger.warning(f"⚠️ Campo obrigatório {field} não enviado, mantendo valor atual: {merged_data.get(field)}")
        
        # 4. Campos opcionais que podem ser atualizados
        optional_fields = [
            'input_channel', 'zoom_bank', 'zoom_patch', 'program', 
            'cc', 'value', 'note', 'velocity', 'effects'
        ]
        
        for field in optional_fields:
            if field in data:
                # Validação de tipo para campos numéricos
                if field in ['input_channel', 'zoom_bank', 'zoom_patch', 'program', 'cc', 'value', 'note', 'velocity']:
                    try:
                        if data[field] is not None:
                            merged_data[field] = int(data[field])
                        else:
                            merged_data[field] = None
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ Campo {field} com valor inválido: {data[field]}, mantendo valor atual")
                        continue
                else:
                    merged_data[field] = data[field]
                logger.info(f"✅ Campo {field} atualizado: {data[field]}")
            else:
                logger.info(f"ℹ️ Campo {field} não enviado, mantendo valor atual: {merged_data.get(field)}")
        
        # 5. Validação final dos dados mesclados
        logger.info(f"📋 Dados mesclados finais: {merged_data}")
        
        # Adiciona o ID aos dados mesclados
        merged_data['id'] = patch_id
        
        # Validação de campos obrigatórios
        for field in required_fields:
            if not merged_data.get(field):
                logger.error(f"❌ Campo obrigatório {field} está vazio após mesclagem")
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório {field} não pode estar vazio'
                }), 400
        
        # 6. Validação de tipos de dados
        try:
            # Testa se consegue criar um objeto Patch válido
            from app.database.models import Patch
            test_patch = Patch.from_dict(merged_data)
            logger.info(f"✅ Objeto Patch criado com sucesso: {test_patch.name}")
        except Exception as e:
            logger.error(f"❌ Erro ao criar objeto Patch: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Dados do patch inválidos: {str(e)}'
            }), 400
        
        # 7. Atualiza o patch no cache e banco
        logger.info("🔧 Iniciando atualização no cache e banco...")
        success = cache_manager.update_patch(merged_data)
        
        if success:
            logger.info(f"✅ Patch {patch_id} atualizado com sucesso")
            
            # 8. Retorna o patch atualizado para confirmação
            updated_patch = cache_manager.get_patch(patch_id)
            
            return jsonify({
                'success': True,
                'message': 'Patch atualizado com sucesso',
                'data': updated_patch
            })
        else:
            logger.error(f"❌ Falha ao atualizar patch {patch_id} no cache/banco")
            return jsonify({
                'success': False,
                'error': 'Erro ao atualizar patch'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar patch {patch_id}: {str(e)}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches/<int:patch_id>', methods=['DELETE'])
def delete_patch(patch_id):
    """Deleta um patch"""
    try:
        cache_manager = current_app.cache_manager
        success = cache_manager.delete_patch(patch_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Patch deletado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao deletar patch'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao deletar patch {patch_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/effects', methods=['GET'])
def get_effects():
    """Lista todos os efeitos disponíveis"""
    try:
        cache_manager = current_app.cache_manager
        effects = cache_manager.get_effects()
        
        return jsonify({
            'success': True,
            'data': effects
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar efeitos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/config', methods=['GET'])
def get_config():
    """Obtém configurações do sistema"""
    try:
        cache_manager = current_app.cache_manager
        config = cache_manager.get_config()
        
        return jsonify({
            'success': True,
            'data': config
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter configurações: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/cache/reload', methods=['POST'])
def reload_cache():
    """Recarrega dados no cache"""
    try:
        cache_manager = current_app.cache_manager
        success = cache_manager.reload_data()
        
        if success:
            cache_info = cache_manager.get_cache_info()
            return jsonify({
                'success': True,
                'message': 'Cache recarregado com sucesso',
                'data': cache_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao recarregar cache'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao recarregar cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/cache/info', methods=['GET'])
def get_cache_info():
    """Obtém informações do cache"""
    try:
        cache_manager = current_app.cache_manager
        cache_info = cache_manager.get_cache_info()
        
        return jsonify({
            'success': True,
            'data': cache_info
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """Obtém status do sistema"""
    try:
        midi_controller = current_app.midi_controller
        cache_manager = current_app.cache_manager
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'midi': {
                'connected': midi_controller.is_connected(),
                'devices': midi_controller.get_device_status()
            },
            'cache': cache_manager.get_cache_info(),
            'version': '1.0.0'
        }
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status do sistema: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches/used_channels', methods=['GET'])
def get_used_channels():
    """Retorna lista de canais já utilizados em patches"""
    try:
        cache_manager = current_app.cache_manager
        patches = cache_manager.get_patches()
        
        used_channels = []
        for patch in patches:
            if patch.get('input_channel') is not None:
                # Verifica se é um número válido (0-127)
                try:
                    channel = int(patch['input_channel'])
                    if 0 <= channel <= 127:
                        used_channels.append(channel)
                except (ValueError, TypeError):
                    # Ignora valores que não são números válidos
                    continue
        
        return jsonify({
            'success': True,
            'data': used_channels
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter canais utilizados: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches/used_zoom_patches', methods=['GET'])
def get_used_zoom_patches():
    """Retorna lista de patches da Zoom G3X já utilizados (banco + patch local)"""
    try:
        cache_manager = current_app.cache_manager
        patches = cache_manager.get_patches()
        print(f'[DEBUG_BACKEND] Total de patches no sistema: {len(patches)}')
        print(f'[DEBUG_BACKEND] patches lidos do cache: {patches}')
        used_patches = []
        for patch in patches:
            if patch.get('zoom_bank') and patch.get('zoom_patch') is not None:
                try:
                    global_patch_number = int(patch['zoom_patch'])
                    bank_letter = patch['zoom_bank']
                    if 0 <= global_patch_number <= 99:
                        local_patch_number = global_patch_number % 10
                        used_patches.append({
                            'bank': bank_letter,
                            'patch': local_patch_number,
                            'global_patch': global_patch_number,
                            'combination': f"{bank_letter}{local_patch_number}"
                        })
                except (ValueError, TypeError):
                    continue
        print(f'[DEBUG_BACKEND] Patches usados da Zoom retornados: {used_patches}')
        return jsonify({
            'success': True,
            'data': used_patches
        })
    except Exception as e:
        logger.error(f"Erro ao obter patches Zoom utilizados: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches/by_channel/<int:channel>', methods=['GET'])
def get_patches_by_channel(channel):
    """Busca patches por canal do Chocolate MIDI"""
    try:
        logger.info(f"🔍 Buscando patches para canal {channel}")
        
        cache_manager = current_app.cache_manager
        patches = cache_manager.get_patches()
        
        # Filtra patches que usam o canal especificado
        matching_patches = []
        for patch in patches:
            if (patch.get('input_device') == 'Chocolate MIDI' and 
                patch.get('input_channel') == channel):
                matching_patches.append(patch)
        
        logger.info(f"✅ Encontrados {len(matching_patches)} patches para canal {channel}")
        
        return jsonify({
            'success': True,
            'data': matching_patches,
            'count': len(matching_patches),
            'channel': channel
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar patches por canal {channel}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/patches/active', methods=['GET'])
def get_active_patch():
    """Obtém o patch atualmente ativo no sistema"""
    try:
        logger.info("🔍 [PATCH_ACTIVE_DEBUG] Iniciando busca por patch ativo...")
        
        midi_controller = current_app.midi_controller
        last_command = None
        active_patch = None
        
        # Primeiro, verifica se há comandos MIDI recentes
        received_commands = midi_controller.get_received_commands()
        logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Comandos MIDI recebidos: {len(received_commands) if received_commands else 0}")
        
        if received_commands:
            for command in reversed(received_commands):
                if command.get('type') == 'program_change' and command.get('program') is not None:
                    last_command = command
                    logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Comando MIDI encontrado: {last_command}")
                    break
        
        # Se há comando MIDI recente, busca o patch correspondente
        if last_command and last_command.get('program') is not None:
            cache_manager = current_app.cache_manager
            patches = cache_manager.get_patches()
            logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Total de patches no cache: {len(patches)}")
            
            for patch in patches:
                if (patch.get('input_device') == 'Chocolate MIDI' and 
                    patch.get('program') == last_command['program']):
                    active_patch = patch
                    logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Patch encontrado via MIDI: {patch.get('name')}")
                    break
        
        # Se não encontrou via comando MIDI, usa o último patch ativado via API/disco
        if not active_patch:
            logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Verificando get_last_patch_activated...")
            patch_from_disk = midi_controller.get_last_patch_activated()
            if patch_from_disk:
                active_patch = patch_from_disk
                logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Patch encontrado via get_last_patch_activated: {active_patch.get('name')}")
            else:
                logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Nenhum patch ativo encontrado em memória ou disco")
        
        # Obtém o banco ativo apenas para informação (não é obrigatório)
        db_manager = current_app.db_manager
        active_bank = db_manager.get_active_bank()
        
        result = {
            'success': True,
            'data': {
                'bank': active_bank.to_dict() if active_bank else None,
                'active_patch': active_patch,
                'last_command': last_command
            }
        }
        
        logger.info(f"🔍 [PATCH_ACTIVE_DEBUG] Resultado final: active_patch = {active_patch.get('name') if active_patch else 'None'}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"❌ Erro ao obter patch ativo: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/checkup/log', methods=['GET'])
def checkup_log():
    """Retorna as últimas linhas do log do sistema (logs/app.log)"""
    try:
        lines = int(request.args.get('lines', 50))
        
        # Tenta diferentes caminhos para o arquivo de log
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'logs', 'app.log'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'logs', 'app.log'),
            '/home/matheus/RaspMIDI/logs/app.log',
            'logs/app.log',
            'app.log'
        ]
        
        log_path = None
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                log_path = abs_path
                break
        
        if not log_path:
            # Se não encontrar o arquivo, retorna um log de exemplo
            return jsonify({
                'success': True, 
                'log': f"Log do sistema - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nArquivo de log não encontrado nos caminhos:\n" + 
                       "\n".join([f"- {os.path.abspath(p)}" for p in possible_paths]) +
                       "\n\nSistema funcionando normalmente."
            })
        
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if lines > 0 else all_lines
        return jsonify({'success': True, 'log': ''.join(last_lines)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/checkup/connectivity', methods=['POST'])
def checkup_connectivity():
    """Testa conectividade dos dispositivos cadastrados (entrada/saída)"""
    try:
        midi_controller = current_app.midi_controller
        config = midi_controller.midi_config
        device_status = midi_controller.get_device_status()
        
        input_device = config.get('input_device')
        output_device = config.get('output_device')
        
        # Verifica status dos dispositivos específicos
        zoom_connected = device_status.get('zoom_g3x', {}).get('connected', False)
        chocolate_connected = device_status.get('chocolate', {}).get('connected', False)
        
        # Verifica conectividade geral
        overall_connected = midi_controller.is_connected()
        
        # Verifica se os dispositivos configurados estão disponíveis
        available_devices = midi_controller.get_available_devices()
        input_available = input_device in [d.get('name') for d in available_devices.get('usb', []) + available_devices.get('bluetooth', [])]
        output_available = output_device in [d.get('name') for d in available_devices.get('usb', []) + available_devices.get('bluetooth', [])]
        
        return jsonify({
            'success': True, 
            'input_device': input_device, 
            'input_available': input_available,
            'output_device': output_device, 
            'output_available': output_available,
            'zoom_g3x_connected': zoom_connected,
            'chocolate_connected': chocolate_connected,
            'overall_connected': overall_connected,
            'device_status': device_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/checkup/devices', methods=['GET'])
def checkup_devices():
    """Lista dispositivos MIDI conectados (entrada e saída)"""
    try:
        midi_controller = current_app.midi_controller
        
        # Escaneia dispositivos disponíveis
        scan_result = midi_controller.scan_devices()
        
        # Obtém dispositivos disponíveis
        available_devices = midi_controller.get_available_devices()
        
        # Obtém status detalhado dos dispositivos
        device_status = midi_controller.get_device_status()
        
        # Formata resposta
        devices = {
            'inputs': available_devices.get('usb', []) + available_devices.get('bluetooth', []),
            'outputs': available_devices.get('usb', []) + available_devices.get('bluetooth', []),
            'scan_result': scan_result,
            'device_status': device_status,
            'connected': midi_controller.is_connected()
        }
        
        return jsonify({'success': True, 'devices': devices})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/checkup/reconnect_input', methods=['POST'])
def checkup_reconnect_input():
    """Reconecta o dispositivo de entrada MIDI configurado"""
    try:
        midi_controller = current_app.midi_controller
        config = midi_controller.midi_config
        input_device = config.get('input_device')
        
        if not input_device:
            return jsonify({'success': False, 'error': 'Nenhum dispositivo de entrada configurado'})
        
        # Tenta reconectar usando os métodos disponíveis
        if 'chocolate' in input_device.lower():
            result = midi_controller.force_reconnect_chocolate()
        elif 'zoom' in input_device.lower():
            result = midi_controller.force_reconnect_zoom_g3x()
        else:
            # Reconexão genérica
            result = midi_controller._connect_input_device(input_device)
        
        return jsonify({'success': result, 'device': input_device})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/checkup/reconnect_output', methods=['POST'])
def checkup_reconnect_output():
    """Reconecta o dispositivo de saída MIDI configurado"""
    try:
        midi_controller = current_app.midi_controller
        config = midi_controller.midi_config
        output_device = config.get('output_device')
        
        if not output_device:
            return jsonify({'success': False, 'error': 'Nenhum dispositivo de saída configurado'})
        
        # Tenta reconectar usando os métodos disponíveis
        if 'zoom' in output_device.lower():
            result = midi_controller.force_reconnect_zoom_g3x()
        else:
            # Reconexão genérica
            result = midi_controller._connect_output_device(output_device)
        
        return jsonify({'success': result, 'device': output_device})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 