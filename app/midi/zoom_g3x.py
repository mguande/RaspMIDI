# -*- coding: utf-8 -*-
"""
RaspMIDI - Controlador Zoom G3X
Baseado na documentação do zoom-explorer para MS-50G+ (device ID 6E)
"""

import logging
import mido
import time
from typing import Dict, Optional, List

from app.config import Config

class ZoomG3XController:
    """Controlador específico para Zoom G3X usando comandos SysEx documentados"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.port = None
        self.connected = False
        self.effects = Config.ZOOM_EFFECTS
        self.device_name = None  # Adicionado para compatibilidade com controller.py
        
        # Device ID para Zoom G3X (baseado na documentação MS-50G+)
        self.device_id = 0x6E
        
        # Comandos SysEx documentados
        self.sysex_commands = {
            'identity_request': [0x7E, 0x7F, 0x06, 0x01],  # MIDI Identity Request
            'get_patch_info': [0x52, 0x00, 0x6E, 0x06],    # Get patch info (MS-50G+ command)
            'get_patch_name': [0x52, 0x00, 0x6E, 0x09],    # Get patch name (MS-50G+ command)
            'get_current_patch': [0x52, 0x00, 0x6E, 0x29], # Get current patch (MS-50G+ command)
            'get_bank_patch': [0x52, 0x00, 0x6E, 0x08],    # Get bank patch (MS-50G+ command)
        }
        
        self.logger.info("Controlador Zoom G3X inicializado com comandos SysEx documentados")
    
    def connect(self, port_name: str) -> bool:
        """Conecta ao Zoom G3X"""
        try:
            self.logger.info(f"Tentando conectar ao Zoom G3X na porta: {port_name}")
            
            # Tenta abrir a porta com timeout
            self.port = mido.open_output(port_name)
            self.connected = True
            self.device_name = port_name  # Salva o nome da porta conectada
            self.logger.info(f"Zoom G3X conectado na porta: {port_name}")
            
            # Testa se a conexão está funcionando com Identity Request
            try:
                identity_response = self._send_identity_request()
                if identity_response:
                    self.logger.info(f"Identity Response: {identity_response}")
                else:
                    self.logger.warning("Identity Request não retornou resposta")
                
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
    
    def _send_identity_request(self) -> Optional[str]:
        """Envia MIDI Identity Request e retorna a resposta"""
        try:
            if not self.port:
                return None
            
            # MIDI Identity Request: F0 7E 7F 06 01 F7
            sysex_data = self.sysex_commands['identity_request']
            sysex_msg = mido.Message('sysex', data=sysex_data)
            self.port.send(sysex_msg)
            
            self.logger.debug(f"Identity Request enviado: {sysex_data}")
            
            # Aguarda resposta
            time.sleep(0.2)
            
            # Tenta ler resposta (se disponível)
            for msg in getattr(self.port, 'iter_pending', lambda: [])():
                if msg.type == 'sysex' and len(msg.data) >= 7:
                    # Resposta esperada: F0 7E 00 06 02 52 6E 00 23 00 31 2E 31 30 F7
                    if msg.data[0] == 0x7E and msg.data[2] == 0x06 and msg.data[3] == 0x02:
                        manufacturer = msg.data[4]
                        family_code = msg.data[5:7]
                        model = msg.data[7:9]
                        version = msg.data[9:]
                        
                        response_info = {
                            'manufacturer': f"0x{manufacturer:02X}",
                            'family_code': f"0x{family_code[0]:02X}{family_code[1]:02X}",
                            'model': f"0x{model[0]:02X}{model[1]:02X}",
                            'version': bytes(version).decode('ascii', errors='ignore')
                        }
                        
                        self.logger.info(f"Identity Response: {response_info}")
                        return str(response_info)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar Identity Request: {str(e)}")
            return None

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
        """Carrega um patch no Zoom G3X, enviando PC e configurando efeitos."""
        try:
            if not self.connected:
                self.logger.error("Zoom G3X não está conectado")
                return False

            command_type = patch_data.get('command_type', 'pc')
            self.logger.info(f"[ZOOM DEBUG] Carregando patch '{patch_data.get('name')}' (Tipo: {command_type})")
            self.logger.info(f"[ZOOM DEBUG] Dados completos do patch: {patch_data}")

            # 1. Usa 'zoom_patch' como a fonte definitiva para o número do programa global
            program_number = patch_data.get('zoom_patch')

            if program_number is None:
                self.logger.error("[ZOOM DEBUG] Patch da Zoom não contém a chave 'zoom_patch' com o número global.")
                return False

            self.logger.info(f"[ZOOM DEBUG] Enviando Program Change para Zoom: channel=0, program={program_number}")

            # Envia o comando PC
            if not self.send_pc(0, int(program_number)):
                self.logger.error(f"[ZOOM DEBUG] Falha ao enviar Program Change {program_number}")
                return False
            
            # Pequena pausa para o pedal processar a mudança de patch
            time.sleep(0.1)

            # 2. Configura os efeitos (ligado/desligado)
            effects = patch_data.get('effects', {})
            if effects:
                self.logger.info("Configurando efeitos...")
                for effect_name, effect_params in effects.items():
                    if effect_name in self.effects and 'enabled' in effect_params:
                        cc_number = self.effects[effect_name]['cc']
                        value = 127 if effect_params['enabled'] else 0
                        self.send_cc(0, cc_number, value)
                        time.sleep(0.05)  # Pequena pausa entre comandos CC
            
            self.logger.info(f"Patch '{patch_data.get('name', 'Unknown')}' carregado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar patch: {str(e)}", exc_info=True)
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
            if not self.connected or self.port is None:
                return False

            message = mido.Message('control_change', channel=channel, control=cc, value=int(value))
            self.port.send(message)

            self.logger.debug(f"CC enviado: Channel={channel}, CC={cc}, Value={value}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar CC: {str(e)}")
            return False
    
    def send_pc(self, channel: int, program: int) -> bool:
        """Envia mensagem Program Change"""
        try:
            if not self.connected or self.port is None:
                self.logger.error(f"[ZOOM DEBUG] Não conectado ou porta não disponível para enviar PC: channel={channel}, program={program}")
                return False

            message = mido.Message('program_change', channel=channel, program=program)
            self.port.send(message)

            self.logger.info(f"[ZOOM DEBUG] ✅ PC enviado com sucesso: Channel={channel}, Program={program}")
            return True

        except Exception as e:
            self.logger.error(f"[ZOOM DEBUG] ❌ Erro ao enviar PC: {str(e)}")
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
                            value = max(0, min(127, int(value)))
                            cc_number = base_cc + param_cc_offset
                            self.send_cc(0, cc_number, int(value))
        except Exception as e:
            self.logger.error(f"Erro ao enviar parâmetros do efeito {effect_name}: {str(e)}")
    
    def get_effect_status(self) -> Dict:
        """Retorna status dos efeitos"""
        return {
            'connected': self.connected,
            'effects': self.effects,
            'port': self.port.name if self.port else None
        }
    
    def get_bank_patches(self, bank_number: int) -> Optional[List[Dict]]:
        """Tenta importar patches de um banco específico da Zoom G3X usando comandos SysEx documentados."""
        try:
            if not self.connected or self.port is None:
                self.logger.warning("Zoom G3X não está conectado para importar patches")
                return None

            if bank_number < 0 or bank_number > 9:
                self.logger.error(f"Número de banco inválido: {bank_number}")
                return None

            patches = []
            self.logger.info(f"Tentando ler patches do banco {bank_number} da Zoom G3X...")

            for i in range(10):
                # Usa número local (0-9) em vez de global
                patch_number_local = i
                patch_number_global = bank_number * 10 + i
                patch_name = f"Patch {patch_number_local}"

                # Tenta diferentes métodos para ler o nome do patch
                patch_name = self._try_read_patch_name_documented(patch_number_global, bank_number)

                patches.append({
                    'number': patch_number_local,  # Número local (0-9)
                    'name': patch_name,
                    'bank': bank_number
                })

            self.logger.info(f"Patches do banco {bank_number} carregados: {len(patches)} patches")
            return patches

        except Exception as e:
            self.logger.error(f"Erro ao importar patches do banco {bank_number}: {str(e)}")
            return None

    def _try_read_patch_name_documented(self, patch_number: int, bank_number: int) -> str:
        """Tenta ler o nome de um patch usando comandos SysEx documentados."""
        # Calcula o número local (0-9) para o nome padrão
        local_patch_number = patch_number % 10
        default_name = f"Patch {local_patch_number}"
        
        if not self.port:
            return default_name

        # Método 1: Comando SysEx para ler patch específico (MS-50G+ command 09)
        try:
            # F0 52 00 6E 09 00 00 <patch_number> F7
            sysex_data = self.sysex_commands['get_patch_name'] + [0x00, 0x00, patch_number]
            sysex_msg = mido.Message('sysex', data=sysex_data)
            self.port.send(sysex_msg)
            self.logger.debug(f"Enviado SysEx get_patch_name para patch {patch_number}: {sysex_data}")
            
            # Aguarda resposta
            time.sleep(0.2)
            
            # Tenta ler resposta
            for msg in getattr(self.port, 'iter_pending', lambda: [])():
                if msg.type == 'sysex' and len(msg.data) > 7:
                    try:
                        # Resposta esperada: F0 52 00 6E 08 00 00 <patch_number> <length LSB> <length MSB> <patch_data> F7
                        if msg.data[0:4] == [0x52, 0x00, 0x6E, 0x08]:
                            # Extrai dados do patch
                            patch_data = msg.data[8:]  # Remove cabeçalho
                            # Procura por string ASCII no patch data
                            name = self._extract_ascii_string(patch_data)
                            if name and name != '':
                                self.logger.info(f"Patch {patch_number} nome lido via get_patch_name: '{name}'")
                                return name
                    except Exception as e:
                        self.logger.debug(f"Erro ao decodificar resposta get_patch_name do patch {patch_number}: {e}")
        except Exception as e:
            self.logger.debug(f"Método get_patch_name falhou para patch {patch_number}: {e}")

        # Método 2: Comando SysEx para ler patch do banco (MS-50G+ command 08)
        try:
            # F0 52 00 6E 08 00 00 <patch_number> F7
            sysex_data = self.sysex_commands['get_bank_patch'] + [0x00, 0x00, patch_number]
            sysex_msg = mido.Message('sysex', data=sysex_data)
            self.port.send(sysex_msg)
            self.logger.debug(f"Enviado SysEx get_bank_patch para patch {patch_number}: {sysex_data}")
            
            time.sleep(0.2)
            
            for msg in getattr(self.port, 'iter_pending', lambda: [])():
                if msg.type == 'sysex' and len(msg.data) > 7:
                    try:
                        if msg.data[0:4] == [0x52, 0x00, 0x6E, 0x08]:
                            patch_data = msg.data[8:]
                            name = self._extract_ascii_string(patch_data)
                            if name and name != '':
                                self.logger.info(f"Patch {patch_number} nome lido via get_bank_patch: '{name}'")
                                return name
                    except Exception as e:
                        self.logger.debug(f"Erro ao decodificar resposta get_bank_patch do patch {patch_number}: {e}")
        except Exception as e:
            self.logger.debug(f"Método get_bank_patch falhou para patch {patch_number}: {e}")

        # Método 3: Comando SysEx para ler patch atual (MS-50G+ command 29)
        try:
            # F0 52 00 6E 29 F7
            sysex_data = self.sysex_commands['get_current_patch']
            sysex_msg = mido.Message('sysex', data=sysex_data)
            self.port.send(sysex_msg)
            self.logger.debug(f"Enviado SysEx get_current_patch: {sysex_data}")
            
            time.sleep(0.2)
            
            for msg in getattr(self.port, 'iter_pending', lambda: [])():
                if msg.type == 'sysex' and len(msg.data) > 3:
                    try:
                        # Resposta esperada: F0 52 00 6E 28 <patch_data> F7
                        if msg.data[0:4] == [0x52, 0x00, 0x6E, 0x28]:
                            patch_data = msg.data[4:]
                            name = self._extract_ascii_string(patch_data)
                            if name and name != '':
                                self.logger.info(f"Patch atual nome lido via get_current_patch: '{name}'")
                                return name
                    except Exception as e:
                        self.logger.debug(f"Erro ao decodificar resposta get_current_patch: {e}")
        except Exception as e:
            self.logger.debug(f"Método get_current_patch falhou: {e}")

        # Método 4: Program Change + tentativa de leitura
        try:
            # Envia Program Change para o patch
            pc_msg = mido.Message('program_change', channel=0, program=patch_number)
            self.port.send(pc_msg)
            self.logger.debug(f"Enviado PC {patch_number}")
            
            time.sleep(0.1)
            
            # Tenta ler qualquer resposta SysEx
            for msg in getattr(self.port, 'iter_pending', lambda: [])():
                if msg.type == 'sysex':
                    self.logger.debug(f"Resposta SysEx recebida para PC {patch_number}: {msg.data}")
                    if len(msg.data) > 3:
                        try:
                            name = self._extract_ascii_string(msg.data)
                            if name and name != '':
                                self.logger.info(f"Patch {patch_number} nome lido via PC: '{name}'")
                                return name
                        except Exception as e:
                            self.logger.debug(f"Erro ao decodificar resposta PC do patch {patch_number}: {e}")
        except Exception as e:
            self.logger.debug(f"Método PC falhou para patch {patch_number}: {e}")

        # Se nenhum método funcionou, retorna nome padrão
        self.logger.debug(f"Nenhum método funcionou para patch {patch_number}, usando nome padrão")
        # Usa número local (0-9) para o nome padrão
        local_patch_number = patch_number % 10
        return f"Patch {local_patch_number}"

    def _extract_ascii_string(self, data: List[int]) -> str:
        """Extrai string ASCII válida dos dados SysEx"""
        try:
            # Converte para bytes e procura por strings ASCII válidas
            byte_data = bytes(data)
            
            # Procura por sequências de caracteres ASCII imprimíveis
            strings = []
            current_string = ""
            
            for byte in byte_data:
                if 32 <= byte <= 126:  # Caracteres ASCII imprimíveis
                    current_string += chr(byte)
                else:
                    if len(current_string) >= 2:  # Mínimo 2 caracteres
                        strings.append(current_string)
                    current_string = ""
            
            # Adiciona última string se válida
            if len(current_string) >= 2:
                strings.append(current_string)
            
            # Retorna a string mais longa encontrada
            if strings:
                return max(strings, key=len).strip()
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Erro ao extrair string ASCII: {e}")
            return "" 