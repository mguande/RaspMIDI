# -*- coding: utf-8 -*-
"""
RaspMIDI - Modelos do Banco de Dados
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

class Patch:
    """Modelo para patches do Zoom G3X"""
    
    def __init__(self, id: Optional[int] = None, name: str = "", effects: Optional[Dict] = None, 
                 input_device: str = "", input_channel: Optional[int] = None,
                 output_device: str = "", command_type: str = "",
                 zoom_bank: Optional[int] = None, zoom_patch: Optional[int] = None,
                 zoom_bank_letter: Optional[str] = None, program: Optional[int] = None, 
                 cc: Optional[int] = None, value: Optional[int] = None,
                 note: Optional[int] = None, velocity: Optional[int] = None,
                 created_at: Optional[str] = None, updated_at: Optional[str] = None):
        self.id = id
        self.name = name
        self.effects = effects or {}
        self.input_device = input_device
        self.input_channel = input_channel
        self.output_device = output_device
        self.command_type = command_type
        self.zoom_bank = zoom_bank
        self.zoom_patch = zoom_patch
        self.zoom_bank_letter = zoom_bank_letter
        self.program = program
        self.cc = cc
        self.value = value
        self.note = note
        self.velocity = velocity
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'effects': self.effects,
            'input_device': self.input_device,
            'input_channel': self.input_channel,
            'output_device': self.output_device,
            'command_type': self.command_type,
            'zoom_bank': self.zoom_bank,
            'zoom_patch': self.zoom_patch,
            'zoom_bank_letter': self.zoom_bank_letter,
            'program': self.program,
            'cc': self.cc,
            'value': self.value,
            'note': self.note,
            'velocity': self.velocity,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Patch':
        """Cria instância a partir de dicionário"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            effects=data.get('effects', {}),
            input_device=data.get('input_device', ''),
            input_channel=data.get('input_channel'),
            output_device=data.get('output_device', ''),
            command_type=data.get('command_type', ''),
            zoom_bank=data.get('zoom_bank'),
            zoom_patch=data.get('zoom_patch'),
            zoom_bank_letter=data.get('zoom_bank_letter'),
            program=data.get('program'),
            cc=data.get('cc'),
            value=data.get('value'),
            note=data.get('note'),
            velocity=data.get('velocity'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

class Effect:
    """Modelo para efeitos individuais"""
    
    def __init__(self, id: int = None, name: str = "", cc_number: int = 0, 
                 enabled: bool = False, parameters: Dict = None):
        self.id = id
        self.name = name
        self.cc_number = cc_number
        self.enabled = enabled
        self.parameters = parameters or {}
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'cc_number': self.cc_number,
            'enabled': self.enabled,
            'parameters': self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Effect':
        """Cria instância a partir de dicionário"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            cc_number=data.get('cc_number', 0),
            enabled=data.get('enabled', False),
            parameters=data.get('parameters', {})
        )

class MIDICommand:
    """Modelo para comandos MIDI"""
    
    def __init__(self, id: int = None, type: str = "", channel: int = 0, 
                 note: int = None, cc: int = None, value: int = 0, 
                 timestamp: str = None):
        self.id = id
        self.type = type  # 'note_on', 'note_off', 'cc', 'pc'
        self.channel = channel
        self.note = note
        self.cc = cc
        self.value = value
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'type': self.type,
            'channel': self.channel,
            'note': self.note,
            'cc': self.cc,
            'value': self.value,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MIDICommand':
        """Cria instância a partir de dicionário"""
        return cls(
            id=data.get('id'),
            type=data.get('type', ''),
            channel=data.get('channel', 0),
            note=data.get('note'),
            cc=data.get('cc'),
            value=data.get('value', 0),
            timestamp=data.get('timestamp')
        )

class BankMapping:
    """Modelo para mapeamento de entrada para saída em um banco"""
    
    def __init__(self, id: int = None, bank_id: int = None, 
                 input_type: str = "", input_channel: int = 0, input_control: int = None,
                 input_value: int = None, output_device: str = "", output_type: str = "",
                 output_channel: int = 0, output_control: int = None, output_value: int = None,
                 output_program: int = None, description: str = ""):
        self.id = id
        self.bank_id = bank_id
        self.input_type = input_type  # 'cc', 'pc', 'note_on', 'note_off'
        self.input_channel = input_channel
        self.input_control = input_control  # CC number ou note
        self.input_value = input_value  # Valor específico para trigger (opcional)
        self.output_device = output_device
        self.output_type = output_type  # 'cc', 'pc', 'note_on', 'note_off'
        self.output_channel = output_channel
        self.output_control = output_control  # CC number ou note
        self.output_value = output_value
        self.output_program = output_program  # Para PC
        self.description = description
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'bank_id': self.bank_id,
            'input_type': self.input_type,
            'input_channel': self.input_channel,
            'input_control': self.input_control,
            'input_value': self.input_value,
            'output_device': self.output_device,
            'output_type': self.output_type,
            'output_channel': self.output_channel,
            'output_control': self.output_control,
            'output_value': self.output_value,
            'output_program': self.output_program,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BankMapping':
        """Cria instância a partir de dicionário"""
        return cls(
            id=data.get('id'),
            bank_id=data.get('bank_id'),
            input_type=data.get('input_type', ''),
            input_channel=data.get('input_channel', 0),
            input_control=data.get('input_control'),
            input_value=data.get('input_value'),
            output_device=data.get('output_device', ''),
            output_type=data.get('output_type', ''),
            output_channel=data.get('output_channel', 0),
            output_control=data.get('output_control'),
            output_value=data.get('output_value'),
            output_program=data.get('output_program'),
            description=data.get('description', '')
        )

class Bank:
    """Modelo para bancos de mapeamento MIDI"""
    
    def __init__(self, id: int = None, name: str = "", description: str = "",
                 active: bool = False, created_at: str = None, updated_at: str = None):
        self.id = id
        self.name = name
        self.description = description
        self.active = active
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.mappings = []  # Lista de BankMapping
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'active': self.active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'mappings': [mapping.to_dict() for mapping in self.mappings]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Bank':
        """Cria instância a partir de dicionário"""
        bank = cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            active=data.get('active', False),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
        
        # Adiciona mapeamentos se existirem
        if 'mappings' in data:
            bank.mappings = [BankMapping.from_dict(m) for m in data['mappings']]
        
        return bank

class DatabaseManager:
    """Gerenciador do banco de dados"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Inicializa as tabelas do banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de patches
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    effects TEXT NOT NULL,
                    input_device TEXT,
                    input_channel INTEGER,
                    output_device TEXT,
                    command_type TEXT,
                    zoom_bank TEXT,
                    zoom_patch INTEGER,
                    zoom_bank_letter TEXT,
                    program INTEGER,
                    cc INTEGER,
                    value INTEGER,
                    note INTEGER,
                    velocity INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Tabela de efeitos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS effects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cc_number INTEGER NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT 0,
                    parameters TEXT NOT NULL
                )
            ''')
            
            # Tabela de comandos MIDI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS midi_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    channel INTEGER NOT NULL DEFAULT 0,
                    note INTEGER,
                    cc INTEGER,
                    value INTEGER NOT NULL DEFAULT 0,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Tabela de bancos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    active BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Tabela de mapeamentos de bancos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_id INTEGER NOT NULL,
                    input_type TEXT NOT NULL,
                    input_channel INTEGER NOT NULL DEFAULT 0,
                    input_control INTEGER,
                    input_value INTEGER,
                    output_device TEXT NOT NULL,
                    output_type TEXT NOT NULL,
                    output_channel INTEGER NOT NULL DEFAULT 0,
                    output_control INTEGER,
                    output_value INTEGER,
                    output_program INTEGER,
                    description TEXT,
                    FOREIGN KEY (bank_id) REFERENCES banks (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def create_patch(self, patch: Patch) -> int:
        """Cria um novo patch"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patches (
                    name, effects, input_device, input_channel, output_device, 
                    command_type, zoom_bank, zoom_patch, zoom_bank_letter, program, cc, value, 
                    note, velocity, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patch.name, json.dumps(patch.effects), patch.input_device, 
                patch.input_channel, patch.output_device, patch.command_type,
                patch.zoom_bank, patch.zoom_patch, patch.zoom_bank_letter, patch.program,
                patch.cc, patch.value, patch.note, patch.velocity,
                patch.created_at, patch.updated_at
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_patch(self, patch_id: int) -> Optional[Patch]:
        """Obtém um patch por ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM patches WHERE id = ?', (patch_id,))
            row = cursor.fetchone()
            
            if row:
                return Patch(
                    id=row[0],
                    name=row[1],
                    effects=json.loads(row[2]),
                    input_device=row[3],
                    input_channel=row[4],
                    output_device=row[5],
                    command_type=row[6],
                    zoom_bank=row[7],
                    zoom_patch=row[8],
                    zoom_bank_letter=row[9],
                    program=row[10],
                    cc=row[11],
                    value=row[12],
                    note=row[13],
                    velocity=row[14],
                    created_at=row[15],
                    updated_at=row[16]
                )
            return None
    
    def get_all_patches(self) -> List[Patch]:
        """Obtém todos os patches"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM patches ORDER BY name')
            rows = cursor.fetchall()
            
            patches = []
            for row in rows:
                patches.append(Patch(
                    id=row[0],
                    name=row[1],
                    effects=json.loads(row[2]),
                    input_device=row[3],
                    input_channel=row[4],
                    output_device=row[5],
                    command_type=row[6],
                    zoom_bank=row[7],
                    zoom_patch=row[8],
                    zoom_bank_letter=row[9],
                    program=row[10],
                    cc=row[11],
                    value=row[12],
                    note=row[13],
                    velocity=row[14],
                    created_at=row[15],
                    updated_at=row[16]
                ))
            return patches
    
    def update_patch(self, patch: Patch, partial_data: dict = None) -> bool:
        """Atualiza um patch, preservando campos não enviados (merge). Adiciona logs detalhados."""
        logger = logging.getLogger(__name__)
        try:
            logger.info(f"🔧 [DB] Iniciando atualização do patch ID {patch.id}")
            if partial_data:
                logger.info(f"📋 [DB] Dados recebidos para atualização: {partial_data}")
            else:
                logger.info(f"📋 [DB] Atualização completa do patch: {patch.to_dict()}")

            # Busca o patch atual do banco
            current_patch = self.get_patch(patch.id)
            if not current_patch:
                logger.error(f"❌ [DB] Patch {patch.id} não encontrado para atualização!")
                return False
            logger.info(f"📋 [DB] Patch atual no banco: {current_patch.to_dict()}")

            # Merge dos dados: campos do patch recebido sobrescrevem os do atual
            merged_dict = current_patch.to_dict()
            if partial_data:
                merged_dict.update(partial_data)
            else:
                merged_dict.update(patch.to_dict())
            logger.info(f"📋 [DB] Dados finais para atualização: {merged_dict}")

            # Cria novo objeto Patch com os dados mesclados
            merged_patch = Patch.from_dict(merged_dict)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE patches 
                    SET name = ?, effects = ?, input_device = ?, input_channel = ?,
                        output_device = ?, command_type = ?, zoom_bank = ?, zoom_patch = ?,
                        zoom_bank_letter = ?, program = ?, cc = ?, value = ?, note = ?, velocity = ?, updated_at = ?
                    WHERE id = ?
                ''', (
                    merged_patch.name, json.dumps(merged_patch.effects), merged_patch.input_device, 
                    merged_patch.input_channel, merged_patch.output_device, merged_patch.command_type,
                    merged_patch.zoom_bank, merged_patch.zoom_patch, merged_patch.zoom_bank_letter,
                    merged_patch.program, merged_patch.cc, merged_patch.value, merged_patch.note,
                    merged_patch.velocity, datetime.now().isoformat(), merged_patch.id
                ))
                conn.commit()
                logger.info(f"✅ [DB] Patch {merged_patch.id} atualizado com sucesso!")
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ [DB] Erro ao atualizar patch: {str(e)}")
            import traceback
            logger.error(f"📋 [DB] Traceback: {traceback.format_exc()}")
            return False
    
    def delete_patch(self, patch_id: int) -> bool:
        """Deleta um patch"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM patches WHERE id = ?', (patch_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def save_midi_command(self, command: MIDICommand) -> int:
        """Salva um comando MIDI"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO midi_commands (type, channel, note, cc, value, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (command.type, command.channel, command.note, 
                  command.cc, command.value, command.timestamp))
            conn.commit()
            return cursor.lastrowid
    
    # Métodos para Bancos
    def create_bank(self, bank: Bank) -> int:
        """Cria um novo banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO banks (name, description, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (bank.name, bank.description, bank.active, 
                  bank.created_at, bank.updated_at))
            bank_id = cursor.lastrowid
            
            # Salva os mapeamentos se existirem
            if bank.mappings:
                for mapping in bank.mappings:
                    mapping.bank_id = bank_id
                    self.create_bank_mapping(mapping)
            
            conn.commit()
            return bank_id
    
    def get_bank(self, bank_id: int) -> Optional[Bank]:
        """Obtém um banco por ID com seus mapeamentos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM banks WHERE id = ?', (bank_id,))
            row = cursor.fetchone()
            
            if row:
                bank = Bank(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    active=bool(row[3]),
                    created_at=row[4],
                    updated_at=row[5]
                )
                
                # Carrega os mapeamentos
                bank.mappings = self.get_bank_mappings(bank_id)
                return bank
            return None
    
    def get_all_banks(self) -> List[Bank]:
        """Obtém todos os bancos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM banks ORDER BY name')
            rows = cursor.fetchall()
            
            banks = []
            for row in rows:
                bank = Bank(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    active=bool(row[3]),
                    created_at=row[4],
                    updated_at=row[5]
                )
                # Carrega os mapeamentos
                bank.mappings = self.get_bank_mappings(bank.id)
                banks.append(bank)
            return banks
    
    def get_active_bank(self) -> Optional[Bank]:
        """Obtém o banco ativo"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM banks WHERE active = 1 LIMIT 1')
            row = cursor.fetchone()
            
            if row:
                bank = Bank(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    active=bool(row[3]),
                    created_at=row[4],
                    updated_at=row[5]
                )
                # Carrega os mapeamentos
                bank.mappings = self.get_bank_mappings(bank.id)
                return bank
            return None
    
    def update_bank(self, bank: Bank) -> bool:
        """Atualiza um banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE banks 
                SET name = ?, description = ?, active = ?, updated_at = ?
                WHERE id = ?
            ''', (bank.name, bank.description, bank.active, 
                  datetime.now().isoformat(), bank.id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_bank(self, bank_id: int) -> bool:
        """Deleta um banco e seus mapeamentos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Deleta mapeamentos primeiro (cascade)
            cursor.execute('DELETE FROM bank_mappings WHERE bank_id = ?', (bank_id,))
            # Deleta o banco
            cursor.execute('DELETE FROM banks WHERE id = ?', (bank_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def set_active_bank(self, bank_id: int) -> bool:
        """Define um banco como ativo (desativa outros)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Desativa todos os bancos
            cursor.execute('UPDATE banks SET active = 0')
            # Ativa o banco especificado
            cursor.execute('UPDATE banks SET active = 1 WHERE id = ?', (bank_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Métodos para Mapeamentos de Banco
    def create_bank_mapping(self, mapping: BankMapping) -> int:
        """Cria um novo mapeamento de banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bank_mappings (
                    bank_id, input_type, input_channel, input_control, input_value,
                    output_device, output_type, output_channel, output_control, 
                    output_value, output_program, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (mapping.bank_id, mapping.input_type, mapping.input_channel,
                  mapping.input_control, mapping.input_value, mapping.output_device,
                  mapping.output_type, mapping.output_channel, mapping.output_control,
                  mapping.output_value, mapping.output_program, mapping.description))
            conn.commit()
            return cursor.lastrowid
    
    def get_bank_mappings(self, bank_id: int) -> List[BankMapping]:
        """Obtém todos os mapeamentos de um banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bank_mappings WHERE bank_id = ? ORDER BY id', (bank_id,))
            rows = cursor.fetchall()
            
            mappings = []
            for row in rows:
                mappings.append(BankMapping(
                    id=row[0],
                    bank_id=row[1],
                    input_type=row[2],
                    input_channel=row[3],
                    input_control=row[4],
                    input_value=row[5],
                    output_device=row[6],
                    output_type=row[7],
                    output_channel=row[8],
                    output_control=row[9],
                    output_value=row[10],
                    output_program=row[11],
                    description=row[12]
                ))
            return mappings
    
    def update_bank_mapping(self, mapping: BankMapping) -> bool:
        """Atualiza um mapeamento de banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bank_mappings 
                SET input_type = ?, input_channel = ?, input_control = ?, input_value = ?,
                    output_device = ?, output_type = ?, output_channel = ?, output_control = ?,
                    output_value = ?, output_program = ?, description = ?
                WHERE id = ?
            ''', (mapping.input_type, mapping.input_channel, mapping.input_control,
                  mapping.input_value, mapping.output_device, mapping.output_type,
                  mapping.output_channel, mapping.output_control, mapping.output_value,
                  mapping.output_program, mapping.description, mapping.id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_bank_mapping(self, mapping_id: int) -> bool:
        """Deleta um mapeamento de banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bank_mappings WHERE id = ?', (mapping_id,))
            conn.commit()
            return cursor.rowcount > 0 