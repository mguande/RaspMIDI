# -*- coding: utf-8 -*-
"""
RaspMIDI - Controlador Zoom G3X
"""

import logging
import mido
from typing import Dict, Optional

from app.config import Config

class ZoomG3XController:
    """Controlador específico para Zoom G3X"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.port = None
        self.connected = False
        self.effects = Config.ZOOM_EFFECTS
        
        self.logger.info("Controlador Zoom G3X inicializado")
    
    def connect(self, port_name: str) -> bool:
        """Conecta ao Zoom G3X"""
        try:
            self.logger.info(f"Tentando conectar ao Zoom G3X na porta: {port_name}")
            
            # Tenta abrir a porta com timeout
            self.port = mido.open_output(port_name)
            self.connected = True
            self.logger.info(f"Zoom G3X conectado na porta: {port_name}")
            
            # Testa se a conexão está funcionando
            try:
                test_msg = mido.Message('program_change', channel=0, program=0)
                self.port.send(test_msg)
                self.logger.info("Teste de conexão bem-sucedido")
                return True
            except Exception as test_error:
                self.logger.warning(f"Porta aberta mas teste falhou: {test_error}")
                # Ainda considera conectado, mas com aviso
                return True
            
        except Exception as e:
            error_msg = str(e).lower()
            self.logger.error(f"Erro ao conectar Zoom G3X: {str(e)}")
            
            # Análise específica do erro
            if 'error creating windows mm midi output port' in error_msg:
                self.logger.warning("⚠ ZOOM G Series 3 pode precisar de alimentação externa. Erro: MidiOutWinMM::openPort: error creating Windows MM MIDI output port.")
                self.logger.info("💡 Dica: Conecte a alimentação externa do ZOOM G Series 3 e tente novamente")
            elif 'timeout' in error_msg:
                self.logger.warning("⚠ Timeout na conexão - dispositivo pode estar ocupado")
            elif 'permission' in error_msg:
                self.logger.warning("⚠ Erro de permissão - tente executar como administrador")
            elif 'not found' in error_msg:
                self.logger.warning("⚠ Porta não encontrada - verifique se o dispositivo está conectado")
            else:
                self.logger.warning("⚠ Erro desconhecido - verifique drivers e conexão física")
            
            return False
    
    def disconnect(self):
        """Desconecta do Zoom G3X"""
        try:
            if self.port:
                self.port.close()
                self.port = None
                self.connected = False
                self.logger.info("Zoom G3X desconectado")
                
        except Exception as e:
            self.logger.error(f"Erro ao desconectar Zoom G3X: {str(e)}")
    
    def load_patch(self, patch_data: Dict) -> bool:
        """Carrega um patch no Zoom G3X"""
        try:
            if not self.connected:
                self.logger.error("Zoom G3X não está conectado")
                return False
            
            effects = patch_data.get('effects', {})
            
            # Aplica cada efeito do patch
            for effect_name, effect_params in effects.items():
                if effect_name in self.effects:
                    cc_number = self.effects[effect_name]['cc']
                    enabled = effect_params.get('enabled', False)
                    
                    # Envia CC para ligar/desligar efeito
                    value = 127 if enabled else 0
                    self.send_cc(0, cc_number, value)
                    
                    # Envia parâmetros específicos do efeito
                    self._send_effect_parameters(effect_name, effect_params)
            
            self.logger.info(f"Patch {patch_data.get('name', 'Unknown')} carregado")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar patch: {str(e)}")
            return False
    
    def toggle_effect(self, effect_name: str, enabled: bool) -> bool:
        """Liga/desliga um efeito específico"""
        try:
            if not self.connected:
                self.logger.error("Zoom G3X não está conectado")
                return False
            
            if effect_name not in self.effects:
                self.logger.error(f"Efeito {effect_name} não encontrado")
                return False
            
            cc_number = self.effects[effect_name]['cc']
            value = 127 if enabled else 0
            
            success = self.send_cc(0, cc_number, value)
            if success:
                status = "ligado" if enabled else "desligado"
                self.logger.info(f"Efeito {effect_name} {status}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao alternar efeito: {str(e)}")
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
    
    def _send_effect_parameters(self, effect_name: str, effect_params: Dict):
        """Envia parâmetros específicos de um efeito"""
        try:
            # Mapeamento de parâmetros por efeito
            param_mapping = {
                'compressor': {
                    'level': 1,
                    'sensitivity': 2
                },
                'overdrive': {
                    'drive': 1,
                    'level': 2,
                    'tone': 3
                },
                'distortion': {
                    'drive': 1,
                    'level': 2,
                    'tone': 3
                },
                'eq': {
                    'bass': 1,
                    'mid': 2,
                    'treble': 3
                },
                'chorus': {
                    'rate': 1,
                    'depth': 2,
                    'level': 3
                },
                'delay': {
                    'time': 1,
                    'feedback': 2,
                    'level': 3
                },
                'reverb': {
                    'decay': 1,
                    'level': 2,
                    'pre_delay': 3
                }
            }
            
            if effect_name in param_mapping:
                mapping = param_mapping[effect_name]
                base_cc = self.effects[effect_name]['cc']
                
                for param_name, param_cc_offset in mapping.items():
                    if param_name in effect_params:
                        value = effect_params[param_name]
                        # Normaliza valor para 0-127
                        if isinstance(value, (int, float)):
                            if value <= 100:  # Assume que está em 0-100
                                value = int((value / 100) * 127)
                            value = max(0, min(127, value))
                            
                            cc_number = base_cc + param_cc_offset
                            self.send_cc(0, cc_number, value)
                            
        except Exception as e:
            self.logger.error(f"Erro ao enviar parâmetros do efeito {effect_name}: {str(e)}")
    
    def get_effect_status(self) -> Dict:
        """Retorna status dos efeitos"""
        return {
            'connected': self.connected,
            'effects': self.effects,
            'port': self.port.name if self.port else None
        }
    
    def get_bank_patches(self, bank_number: int) -> Optional[list]:
        """Tenta importar patches de um banco específico da Zoom G3X"""
        try:
            if not self.connected:
                self.logger.warning("Zoom G3X não está conectado para importar patches")
                return None
            
            if bank_number < 0 or bank_number > 9:
                self.logger.error(f"Número de banco inválido: {bank_number}")
                return None
            
            patches = []
            
            # Tenta ler patches do banco selecionado
            # Nota: A Zoom G3X pode não suportar leitura de nomes via MIDI
            # Neste caso, retornamos patches padrão
            for i in range(10):
                patch_number = bank_number * 10 + i
                patch_name = f"Patch {patch_number}"
                
                patches.append({
                    'number': patch_number,
                    'name': patch_name,
                    'bank': bank_number
                })
            
            self.logger.info(f"Patches do banco {bank_number} carregados: {len(patches)} patches")
            return patches
            
        except Exception as e:
            self.logger.error(f"Erro ao importar patches do banco {bank_number}: {str(e)}")
            return None 