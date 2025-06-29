# -*- coding: utf-8 -*-
"""
RaspMIDI - Configurações do Sistema
"""

import os
from pathlib import Path

class Config:
    """Configurações principais do sistema"""
    
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'raspmidi-secret-key-2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configurações do servidor
    HOST = os.environ.get('HOST', '0.0.0.0')  # 0.0.0.0 para aceitar conexões externas
    PORT = int(os.environ.get('PORT', 5000))
    
    # Configurações do banco de dados
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    DATABASE_PATH = DATA_DIR / 'raspmidi.db'
    
    # Configurações MIDI
    MIDI_INPUTS = {
        'zoom_g3x': 'Zoom G3X',
        'chocolate': 'Chocolate MIDI'
    }
    
    MIDI_OUTPUTS = {
        'zoom_g3x': 'Zoom G3X',
        'chocolate': 'Chocolate MIDI'
    }
    
    # Configurações Bluetooth
    BLUETOOTH_ENABLED = True
    CHOCOLATE_BT_NAME = 'Chocolate MIDI'
    CHOCOLATE_BT_ADDRESS = None  # Será descoberto automaticamente
    
    # Configurações de cache
    CACHE_ENABLED = True
    CACHE_TIMEOUT = 300  # 5 minutos
    
    # Configurações de patches
    MAX_PATCHES = 100
    DEFAULT_PATCH_NAME = 'Novo Patch'
    
    # Configurações de efeitos (Zoom G3X)
    ZOOM_EFFECTS = {
        'effect_1': {'cc': 0, 'name': 'Efeito 1'},
        'effect_2': {'cc': 1, 'name': 'Efeito 2'},
        'effect_3': {'cc': 2, 'name': 'Efeito 3'},
        'effect_4': {'cc': 3, 'name': 'Efeito 4'},
        'effect_5': {'cc': 4, 'name': 'Efeito 5'},
        'effect_6': {'cc': 5, 'name': 'Efeito 6'}
    }
    
    # Configurações de logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def init_app(cls, app):
        """Inicializa configurações específicas da aplicação"""
        # Cria diretórios necessários
        cls.DATA_DIR.mkdir(exist_ok=True)
        
        # Configura logging
        import logging
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=cls.LOG_FORMAT
        )

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    HOST = '0.0.0.0'

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    HOST = '0.0.0.0'

class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    DATABASE_PATH = ':memory:'

# Configuração por ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 