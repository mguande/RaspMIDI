# -*- coding: utf-8 -*-
"""
RaspMIDI - Inicialização do Banco de Dados
"""

import os
import logging
from app.config import Config
from app.database.models import DatabaseManager, Patch

# Instância global do gerenciador de banco
db_manager = None

def init_db():
    """Inicializa o banco de dados"""
    global db_manager
    
    logger = logging.getLogger(__name__)
    
    try:
        # Cria diretório de dados se não existir
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
        
        # Inicializa gerenciador de banco
        db_manager = DatabaseManager(str(Config.DATABASE_PATH))
        
        # NÃO criar patches padrão automaticamente
        # create_default_patches()
        
        logger.info(f"Banco de dados inicializado: {Config.DATABASE_PATH}")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise

def get_db():
    """Retorna a instância do gerenciador de banco"""
    return db_manager 