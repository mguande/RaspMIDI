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
from logging.handlers import TimedRotatingFileHandler

# Adiciona o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.main import create_app
from app.config import Config

def setup_logging():
    """Configura o sistema de logs"""
    # Configuração de logging rotativo diário
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_filename = os.path.join(log_dir, f'raspmidi_{datetime.now().strftime("%Y-%m-%d")}.log')
    handler = TimedRotatingFileHandler(log_filename, when='midnight', interval=1, backupCount=30, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

def main():
    """Função principal"""
    print("🎵 Iniciando RaspMIDI...")
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Sistema RaspMIDI iniciando...")

    try:
        app = create_app()
        host = getattr(Config, 'HOST', '0.0.0.0')
        port = getattr(Config, 'PORT', 5000)
        debug = getattr(Config, 'DEBUG', False)

        logger.info(f"Servidor iniciando em http://{host}:{port}")
        print(f"🌐 Interface web disponível em: http://{host}:{port}")
        print("📱 Acesse pelo celular para controle remoto")
        print("🎛️  Sistema MIDI pronto para uso")

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