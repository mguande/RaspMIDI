# -*- coding: utf-8 -*-
"""
RaspMIDI - Gerenciador de Cache
"""

import logging
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.database.database import get_db
from app.database.models import Patch, Effect

class CacheManager:
    """Gerenciador de cache para pré-carregamento de dados"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cache = {}
        self._cache_timestamps = {}
        self._lock = threading.Lock()
        self._loaded = False
        self._last_load_time = None
        
        # Configurações de cache
        self.cache_timeout = 300  # 5 minutos
        self.auto_reload = True
        
        self.logger.info("Cache Manager inicializado")
    
    def is_loaded(self) -> bool:
        """Verifica se o cache está carregado"""
        return self._loaded
    
    def get_last_load_time(self) -> Optional[datetime]:
        """Retorna o horário do último carregamento"""
        return self._last_load_time
    
    def load_all_data(self) -> bool:
        """Carrega todos os dados no cache"""
        try:
            self.logger.info("Carregando dados no cache...")
            with self._lock:
                db = get_db()
                if not db:
                    self.logger.error("Banco de dados não inicializado")
                    return False
                # Carrega patches
                patches = db.get_all_patches()
                self._cache['patches'] = [patch.to_dict() for patch in patches]
                self._cache_timestamps['patches'] = datetime.now()
                # Carrega patches da Zoom
                zoom_patches = {}
                for bank_letter in ['A','B','C','D','E','F','G','H','I','J']:
                    zoom_patches[bank_letter] = db.get_zoom_patches_by_bank(bank_letter)
                self._cache['zoom_patches'] = zoom_patches
                self._cache_timestamps['zoom_patches'] = datetime.now()
                # Carrega efeitos padrão do Zoom G3X
                from app.config import Config
                self._cache['effects'] = Config.ZOOM_EFFECTS
                self._cache_timestamps['effects'] = datetime.now()
                # Carrega configurações
                self._cache['config'] = {
                    'max_patches': Config.MAX_PATCHES,
                    'default_patch_name': Config.DEFAULT_PATCH_NAME,
                    'bluetooth_enabled': Config.BLUETOOTH_ENABLED
                }
                self._cache_timestamps['config'] = datetime.now()
                self._loaded = True
                self._last_load_time = datetime.now()
                self.logger.info(f"Cache carregado com {len(patches)} patches e patches da Zoom para {len(zoom_patches)} bancos")
                # Nota: MIDIController será atualizado quando necessário, não aqui para evitar recursão
                return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar cache: {str(e)}")
            return False
    
    def reload_data(self) -> bool:
        """Recarrega todos os dados no cache"""
        self.logger.info("Recarregando dados no cache...")
        return self.load_all_data()
    
    def get_patches(self) -> List[Dict]:
        """Obtém todos os patches do cache"""
        # Remover lock problemático temporariamente
        if not self._is_cache_valid('patches'):
            self._load_patches()
        return self._cache.get('patches', [])
    
    def get_patch(self, patch_id: int) -> Optional[Dict]:
        """Obtém um patch específico do cache"""
        patches = self.get_patches()
        for patch in patches:
            if patch['id'] == patch_id:
                return patch
        return None
    
    def get_effects(self) -> Dict:
        """Obtém os efeitos do cache"""
        with self._lock:
            if not self._is_cache_valid('effects'):
                self._load_effects()
            return self._cache.get('effects', {})
    
    def get_config(self) -> Dict:
        """Obtém as configurações do cache"""
        with self._lock:
            if not self._is_cache_valid('config'):
                self._load_config()
            return self._cache.get('config', {})
    
    def update_patch(self, patch_data: Dict) -> bool:
        """Atualiza um patch no cache e no banco com preservação completa de dados e logs detalhados"""
        try:
            self.logger.info(f"🔧 [CACHE] Iniciando atualização de patch: {patch_data.get('name', 'Sem nome')}")
            
            # Garante que o ID está presente
            if 'id' not in patch_data:
                self.logger.error("❌ [CACHE] ID do patch não encontrado nos dados")
                return False
            
            patch_id = patch_data['id']
            self.logger.info(f"🆔 [CACHE] Atualizando patch ID: {patch_id}")
            
            with self._lock:
                db = get_db()
                if not db:
                    self.logger.error("❌ [CACHE] Banco de dados não disponível")
                    return False
                
                # Busca o patch atual no banco para garantir que existe
                current_patch = db.get_patch(patch_id)
                if not current_patch:
                    self.logger.error(f"❌ [CACHE] Patch {patch_id} não encontrado no banco")
                    return False
                
                self.logger.info(f"📋 [CACHE] Patch atual encontrado: {current_patch.to_dict()}")
                
                # Atualiza no banco usando merge (passando dados parciais)
                from app.database.models import Patch
                patch_obj = Patch.from_dict(patch_data)
                success = db.update_patch(patch_obj, partial_data=patch_data)
                
                if success:
                    # Atualiza no cache
                    patches = self.get_patches()
                    for i, cached_patch in enumerate(patches):
                        if cached_patch['id'] == patch_id:
                            # Atualiza com os dados completos do objeto Patch
                            updated_patch_dict = db.get_patch(patch_id).to_dict()
                            patches[i] = updated_patch_dict
                            self._cache_timestamps['patches'] = datetime.now()
                            self.logger.info(f"✅ [CACHE] Patch {patch_id} atualizado no cache e banco")
                            self.logger.debug(f"📋 [CACHE] Dados atualizados: {updated_patch_dict}")
                            return True
                    
                    # Se não encontrou no cache, adiciona
                    self.logger.warning(f"⚠️ [CACHE] Patch {patch_id} não encontrado no cache, adicionando")
                    patches.append(db.get_patch(patch_id).to_dict())
                    self._cache_timestamps['patches'] = datetime.now()
                    return True
                else:
                    self.logger.error(f"❌ [CACHE] Falha ao atualizar patch {patch_id} no banco")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ [CACHE] Erro ao atualizar patch: {str(e)}")
            import traceback
            self.logger.error(f"📋 [CACHE] Traceback: {traceback.format_exc()}")
            return False
    
    def add_patch(self, patch_data: Dict) -> Optional[int]:
        """Adiciona um novo patch ao cache e ao banco"""
        try:
            self.logger.info(f"🔧 Iniciando adição de patch: {patch_data.get('name', 'Sem nome')}")
            
            # Remover lock problemático - usar timeout se necessário
            db = get_db()
            if not db:
                self.logger.error("❌ Banco de dados não disponível")
                return None
            
            self.logger.info("✅ Banco de dados disponível, criando objeto Patch")
            
            # Adiciona no banco
            patch = Patch.from_dict(patch_data)
            self.logger.info(f"✅ Objeto Patch criado: {patch.name}")
            
            patch_id = db.create_patch(patch)
            self.logger.info(f"🔧 Resultado da criação no banco: patch_id = {patch_id}")
            
            if patch_id:
                # Adiciona no cache sem lock
                patch.id = patch_id
                with self._lock:
                    patches = self.get_patches()
                    patches.append(patch.to_dict())
                    self._cache_timestamps['patches'] = datetime.now()
                
                self.logger.info(f"✅ Patch {patch.name} criado com ID {patch_id}")
                self.logger.info(f"📊 Total de patches no cache: {len(patches)}")
                return patch_id
            else:
                self.logger.error("❌ Falha ao criar patch no banco de dados")
                return None
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao adicionar patch: {str(e)}")
            import traceback
            self.logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return None
    
    def delete_patch(self, patch_id: int) -> bool:
        """Deleta um patch do cache e do banco"""
        try:
            with self._lock:
                db = get_db()
                if not db:
                    return False
                
                # Deleta do banco
                success = db.delete_patch(patch_id)
                
                if success:
                    # Remove do cache
                    patches = self.get_patches()
                    patches[:] = [p for p in patches if p['id'] != patch_id]
                    self._cache_timestamps['patches'] = datetime.now()
                    
                    self.logger.info(f"Patch {patch_id} deletado")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao deletar patch: {str(e)}")
            return False
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica se o cache para uma chave é válido"""
        if key not in self._cache_timestamps:
            return False
        
        timestamp = self._cache_timestamps[key]
        return datetime.now() - timestamp < timedelta(seconds=self.cache_timeout)
    
    def _load_patches(self):
        """Carrega patches no cache"""
        db = get_db()
        if db:
            patches = db.get_all_patches()
            self._cache['patches'] = [patch.to_dict() for patch in patches]
            self._cache_timestamps['patches'] = datetime.now()
    
    def _load_effects(self):
        """Carrega efeitos no cache"""
        from app.config import Config
        self._cache['effects'] = Config.ZOOM_EFFECTS
        self._cache_timestamps['effects'] = datetime.now()
    
    def _load_config(self):
        """Carrega configurações no cache"""
        from app.config import Config
        self._cache['config'] = {
            'max_patches': Config.MAX_PATCHES,
            'default_patch_name': Config.DEFAULT_PATCH_NAME,
            'bluetooth_enabled': Config.BLUETOOTH_ENABLED
        }
        self._cache_timestamps['config'] = datetime.now()
    
    def get_cache_info(self) -> Dict:
        """Retorna informações sobre o cache"""
        return {
            'loaded': self._loaded,
            'last_load_time': self._last_load_time.isoformat() if self._last_load_time else None,
            'cache_size': len(self._cache),
            'patches_count': len(self._cache.get('patches', [])),
            'effects_count': len(self._cache.get('effects', {})),
            'cache_timeout': self.cache_timeout
        }

    def set_active_patch(self, patch_id: int):
        """Marca o patch como ativo no sistema (apenas em memória)"""
        self._active_patch_id = patch_id
        self.logger.info(f"Patch ativo definido: {patch_id}")

    def get_active_patch(self) -> int:
        """Retorna o ID do patch ativo (ou None)"""
        return getattr(self, '_active_patch_id', None)

    def get_zoom_patches_by_bank(self, bank_letter: str) -> list:
        """Obtém patches da Zoom do cache para um banco"""
        if not self._is_cache_valid('zoom_patches'):
            self._load_zoom_patches()
        return self._cache.get('zoom_patches', {}).get(bank_letter, [])

    def _load_zoom_patches(self):
        """Recarrega patches da Zoom do banco para o cache"""
        db = get_db()
        if not db:
            self.logger.error("Banco de dados não disponível para recarregar zoom_patches")
            return
        zoom_patches = {}
        for bank_letter in ['A','B','C','D','E','F','G','H','I','J']:
            zoom_patches[bank_letter] = db.get_zoom_patches_by_bank(bank_letter)
        self._cache['zoom_patches'] = zoom_patches
        self._cache_timestamps['zoom_patches'] = datetime.now()
        self.logger.info("Patches da Zoom recarregados no cache")

    def update_zoom_patches_cache(self):
        """Atualiza o cache dos patches da Zoom (deve ser chamado após atualizar o banco)"""
        with self._lock:
            self._load_zoom_patches() 