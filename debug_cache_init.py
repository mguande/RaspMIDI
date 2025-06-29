#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug da inicialização do cache
Para identificar onde os dados são corrompidos durante o carregamento
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.cache.cache_manager import CacheManager
from app.database.database import get_db, init_db
import json

def debug_cache_initialization():
    """Debuga o processo de inicialização do cache"""
    
    print("=== DEBUG DA INICIALIZAÇÃO DO CACHE ===")
    print()
    
    # Inicializa o banco de dados primeiro
    print("--- 0. INICIALIZAÇÃO DO BANCO ---")
    try:
        init_db()
        print("✅ Banco de dados inicializado")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return
    
    # 1. Verifica dados direto no banco antes do cache
    print("--- 1. DADOS NO BANCO ANTES DO CACHE ---")
    try:
        db = get_db()
        if not db:
            print("❌ Banco de dados não disponível")
            return
        
        # Usa o método get_all_patches do DatabaseManager
        patches_from_db = db.get_all_patches()
        
        print(f"📊 Total de patches no banco: {len(patches_from_db)}")
        
        for i, patch in enumerate(patches_from_db, 1):
            print(f"  {i}. ID: {patch.id}")
            print(f"     Nome: {patch.name}")
            print(f"     Effects: {patch.effects}")
            print(f"     Input Device: {patch.input_device}")
            print(f"     Input Channel: {patch.input_channel}")
            print(f"     Output Device: {patch.output_device}")
            print(f"     Command Type: {patch.command_type}")
            print(f"     Zoom Bank: {patch.zoom_bank}")
            print(f"     Zoom Patch: {patch.zoom_patch}")
            print(f"     Program: {patch.program}")
            print(f"     CC: {patch.cc}")
            print(f"     Value: {patch.value}")
            print(f"     Note: {patch.note}")
            print(f"     Velocity: {patch.velocity}")
            print(f"     Created: {patch.created_at}")
            print(f"     Updated: {patch.updated_at}")
            print()
        
    except Exception as e:
        print(f"❌ Erro ao acessar banco: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Inicializa o cache e verifica os dados
    print("--- 2. INICIALIZAÇÃO DO CACHE ---")
    try:
        cache_manager = CacheManager()
        
        # Força recarregamento do cache
        print("🔄 Recarregando cache...")
        cache_manager.reload_data()
        
        # Verifica dados no cache
        print("📋 Dados no cache após inicialização:")
        patches = cache_manager.get_patches()
        
        for i, patch in enumerate(patches, 1):
            print(f"  {i}. ID: {patch.get('id')}")
            print(f"     Nome: {patch.get('name')}")
            print(f"     Effects: {patch.get('effects')}")
            print(f"     Input Device: {patch.get('input_device')}")
            print(f"     Input Channel: {patch.get('input_channel')}")
            print(f"     Output Device: {patch.get('output_device')}")
            print(f"     Command Type: {patch.get('command_type')}")
            print(f"     Zoom Bank: {patch.get('zoom_bank')}")
            print(f"     Zoom Patch: {patch.get('zoom_patch')}")
            print(f"     Program: {patch.get('program')}")
            print(f"     CC: {patch.get('cc')}")
            print(f"     Value: {patch.get('value')}")
            print(f"     Note: {patch.get('note')}")
            print(f"     Velocity: {patch.get('velocity')}")
            print(f"     Created: {patch.get('created_at')}")
            print(f"     Updated: {patch.get('updated_at')}")
            print()
        
    except Exception as e:
        print(f"❌ Erro na inicialização do cache: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Verifica se há diferenças entre banco e cache
    print("--- 3. COMPARAÇÃO BANCO vs CACHE ---")
    try:
        # Dados do banco
        db = get_db()
        if not db:
            print("❌ Banco de dados não disponível")
            return
            
        patches_from_db = db.get_all_patches()
        
        # Dados do cache
        cache_manager = CacheManager()
        cache_patches = cache_manager.get_patches()
        
        print(f"📊 Banco: {len(patches_from_db)} patches")
        print(f"📊 Cache: {len(cache_patches)} patches")
        
        if len(patches_from_db) != len(cache_patches):
            print("❌ DIFERENÇA: Número de patches diferente entre banco e cache")
        
        # Compara cada patch
        for i in range(min(len(patches_from_db), len(cache_patches))):
            db_patch = patches_from_db[i]
            cache_patch = cache_patches[i]
            
            differences = []
            
            if str(db_patch.name) != str(cache_patch.get('name', '')):
                differences.append(f"Nome: '{db_patch.name}' vs '{cache_patch.get('name', '')}'")
            
            if str(db_patch.input_device) != str(cache_patch.get('input_device', '')):
                differences.append(f"Input Device: '{db_patch.input_device}' vs '{cache_patch.get('input_device', '')}'")
            
            if str(db_patch.output_device) != str(cache_patch.get('output_device', '')):
                differences.append(f"Output Device: '{db_patch.output_device}' vs '{cache_patch.get('output_device', '')}'")
            
            if str(db_patch.command_type) != str(cache_patch.get('command_type', '')):
                differences.append(f"Command Type: '{db_patch.command_type}' vs '{cache_patch.get('command_type', '')}'")
            
            if differences:
                print(f"❌ Patch {i+1} (ID: {db_patch.id}) tem diferenças:")
                for diff in differences:
                    print(f"   - {diff}")
                print()
        
    except Exception as e:
        print(f"❌ Erro na comparação: {e}")
        import traceback
        traceback.print_exc()
    
    print("=== DEBUG CONCLUÍDO ===")

if __name__ == "__main__":
    debug_cache_initialization() 