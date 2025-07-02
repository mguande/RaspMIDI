# -*- coding: utf-8 -*-
"""
RaspMIDI - Aplicação Principal Flask
"""

import os
import logging
from flask import Flask, render_template
from flask_cors import CORS

from app.config import config
from app.database.database import init_db
from app.cache.cache_manager import CacheManager
from app.midi.controller import MIDIController

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    
    # Determina a configuração
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__, 
                template_folder='web/templates', 
                static_folder='web/static')
    
    # Carrega configurações
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configura CORS para permitir acesso via celular
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Inicializa componentes
    with app.app_context():
        # Inicializa banco de dados
        init_db()
        
        # Inicializa gerenciador do banco
        from app.database.models import DatabaseManager
        db_path = os.path.join(config[config_name].BASE_DIR, 'data', 'raspmidi.db')
        db_manager = DatabaseManager(db_path)
        app.db_manager = db_manager
        
        # Inicializa cache
        cache_manager = CacheManager()
        app.cache_manager = cache_manager
        
        # Inicializa controlador MIDI
        midi_controller = MIDIController()
        app.midi_controller = midi_controller
        
        # Inicializa controlador MIDI
        midi_controller.initialize()
        
        # Carrega dados iniciais no cache
        cache_manager.load_all_data()
        
        # Registra blueprints
        from app.api.routes import api_bp
        from app.api.midi_routes import midi_bp
        
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(midi_bp, url_prefix='/api/midi')
        
        # Rota principal
        @app.route('/')
        def home():
            return render_template('home.html')
        
        # Rota de edição
        @app.route('/edicao')
        def edicao():
            return render_template('edicao.html')
        
        # Rota de palco
        @app.route('/palco')
        def palco():
            return render_template('palco.html')
        
        # Rota de verificação do sistema
        @app.route('/verificacao')
        def verificacao():
            return render_template('verificacao.html')
        
        # Rota de status
        @app.route('/status')
        def status():
            return {
                'status': 'online',
                'version': '1.0.0',
                'midi_connected': midi_controller.is_connected(),
                'cache_loaded': cache_manager.is_loaded()
            }
        
        # Rota de health check
        @app.route('/health')
        def health():
            return {'status': 'healthy'}
        
        # Rota de checkup/reparos
        @app.route('/checkup')
        def checkup():
            return render_template('checkup.html')
    
    # Configura logging
    logger = logging.getLogger(__name__)
    logger.info(f"Aplicação RaspMIDI criada com configuração: {config_name}")
    
    return app 