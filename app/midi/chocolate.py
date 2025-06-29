# -*- coding: utf-8 -*-
"""
RaspMIDI - Controlador Chocolate MIDI
"""

import logging
import mido
from typing import Dict, Optional

class ChocolateController:
    """Controlador específico para Chocolate MIDI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.port = None
        self.connected = False
        
        self.logger.info("Controlador Chocolate MIDI inicializado")
    
    def connect(self, port_name: str) -> bool:
        """Conecta ao Chocolate MIDI"""
        try:
            self.port = mido.open_output(port_name)
            self.connected = True
            self.logger.info(f"Chocolate MIDI conectado na porta: {port_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar Chocolate MIDI: {str(e)}")
            return False
    
    def disconnect(self):
        """Desconecta do Chocolate MIDI"""
        try:
            if self.port:
                self.port.close()
                self.port = None
                self.connected = False
                self.logger.info("Chocolate MIDI desconectado")
                
        except Exception as e:
            self.logger.error(f"Erro ao desconectar Chocolate MIDI: {str(e)}")
    
    def send_note_on(self, channel: int, note: int, velocity: int = 64) -> bool:
        """Envia mensagem Note On"""
        try:
            if not self.connected:
                return False
            
            message = mido.Message('note_on', channel=channel, note=note, velocity=velocity)
            self.port.send(message)
            
            self.logger.debug(f"Note On enviado: Channel={channel}, Note={note}, Velocity={velocity}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar Note On: {str(e)}")
            return False
    
    def send_note_off(self, channel: int, note: int) -> bool:
        """Envia mensagem Note Off"""
        try:
            if not self.connected:
                return False
            
            message = mido.Message('note_off', channel=channel, note=note)
            self.port.send(message)
            
            self.logger.debug(f"Note Off enviado: Channel={channel}, Note={note}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar Note Off: {str(e)}")
            return False
    
    def send_cc(self, channel: int, cc: int, value: int) -> bool:
        """Envia mensagem Control Change"""
        try:
            if not self.connected:
                return False
            
            message = mido.Message('control_change', channel=channel, control=cc, value=value)
            self.port.send(message)
            
            self.logger.debug(f"CC enviado: Channel={channel}, CC={cc}, Value={value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar CC: {str(e)}")
            return False
    
    def send_pc(self, channel: int, program: int) -> bool:
        """Envia mensagem Program Change"""
        try:
            if not self.connected:
                return False
            
            message = mido.Message('program_change', channel=channel, program=program)
            self.port.send(message)
            
            self.logger.debug(f"PC enviado: Channel={channel}, Program={program}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar PC: {str(e)}")
            return False
    
    def send_sysex(self, data: list) -> bool:
        """Envia mensagem SysEx"""
        try:
            if not self.connected:
                return False
            
            message = mido.Message('sysex', data=data)
            self.port.send(message)
            
            self.logger.debug(f"SysEx enviado: {data}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar SysEx: {str(e)}")
            return False
    
    def send_chord(self, channel: int, notes: list, velocity: int = 64) -> bool:
        """Envia um acorde (múltiplas notas)"""
        try:
            if not self.connected:
                return False
            
            success = True
            for note in notes:
                if not self.send_note_on(channel, note, velocity):
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar acorde: {str(e)}")
            return False
    
    def send_arpeggio(self, channel: int, notes: list, pattern: str = 'up', 
                     velocity: int = 64, duration: float = 0.1) -> bool:
        """Envia um arpejo"""
        try:
            if not self.connected:
                return False
            
            import time
            
            if pattern == 'up':
                note_sequence = notes
            elif pattern == 'down':
                note_sequence = notes[::-1]
            elif pattern == 'updown':
                note_sequence = notes + notes[-2:0:-1]
            else:
                self.logger.error(f"Padrão de arpejo não suportado: {pattern}")
                return False
            
            success = True
            for note in note_sequence:
                if not self.send_note_on(channel, note, velocity):
                    success = False
                time.sleep(duration)
                if not self.send_note_off(channel, note):
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar arpejo: {str(e)}")
            return False
    
    def get_status(self) -> Dict:
        """Retorna status do Chocolate MIDI"""
        return {
            'connected': self.connected,
            'port': self.port.name if self.port else None
        } 