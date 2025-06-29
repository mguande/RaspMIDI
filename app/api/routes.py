# -*- coding: utf-8 -*-
"""
RaspMIDI - Rotas da API REST
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.database.database import get_db

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
    """Atualiza um patch"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados do patch são obrigatórios'
            }), 400
        
        data['id'] = patch_id
        cache_manager = current_app.cache_manager
        success = cache_manager.update_patch(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Patch atualizado com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao atualizar patch'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao atualizar patch {patch_id}: {str(e)}")
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
    """Retorna lista de patches da Zoom G3X já utilizados"""
    try:
        cache_manager = current_app.cache_manager
        patches = cache_manager.get_patches()
        
        used_patches = []
        for patch in patches:
            if patch.get('zoom_bank') and patch.get('zoom_patch') is not None:
                # Verifica se é um patch válido
                try:
                    patch_number = int(patch['zoom_patch'])
                    if 0 <= patch_number <= 99:  # Zoom G3X tem 100 patches (0-99)
                        used_patches.append(patch_number)
                except (ValueError, TypeError):
                    # Ignora valores que não são números válidos
                    continue
        
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