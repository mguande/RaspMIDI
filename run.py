#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RaspMIDI - Sistema Principal
Arquivo de inicialização do sistema RaspMIDI
"""

import os
import sys
import logging
from datetime import datetime

# Adiciona o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.main import create_app
from app.config import Config

def setup_logging():
    """Configura o sistema de logs"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_filename = f"logs/raspmidi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Função principal"""
    print("🎵 Iniciando RaspMIDI...")
    
    # Configura logs
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Sistema RaspMIDI iniciando...")
    
    try:
        # Cria a aplicação Flask
        app = create_app()
        import app.main
        app.main._app_instance = app  # Torna acessível globalmente
        
        # Configurações
        host = Config.HOST
        port = Config.PORT
        debug = Config.DEBUG
        
        logger.info(f"Servidor iniciando em http://{host}:{port}")
        print(f"🌐 Interface web disponível em: http://{host}:{port}")
        print("📱 Acesse pelo celular para controle remoto")
        print("🎛️  Sistema MIDI pronto para uso")
        
        # Inicia o servidor
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Erro ao iniciar o sistema: {str(e)}")
        print(f"❌ Erro ao iniciar o sistema: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 