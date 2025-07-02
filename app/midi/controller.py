# -*- coding: utf-8 -*-
"""
RaspMIDI - Controlador MIDI Principal
"""

import logging
import threading
import time
import json
import os
import atexit
from typing import Dict, List, Optional
import mido

from app.config import Config
from app.midi.zoom_g3x import ZoomG3XController
from app.midi.chocolate import ChocolateController

class MIDIController:
    """Controlador principal MIDI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._connected = False
        self._devices = {}
        
        # Controladores específicos
        self.zoom_g3x = None
        self.chocolate = None
        
        # Status dos dispositivos
        self.device_status = {
            'zoom_g3x': {'connected': False, 'port': None, 'last_pc': None},
            'chocolate': {'connected': False, 'port': None, 'last_pc': None}
        }
        
        # Configurações de entrada/saída
        self.midi_config = self._load_midi_config()
        
        self._last_patch_activated = None
        
        self.chocolate_patches = []
        
        # Pool de conexões MIDI para evitar múltiplas aberturas
        self._midi_connections = {}
        self._connection_lock = threading.Lock()
        
        # Registra cleanup automático
        atexit.register(self.cleanup)
        
        self.logger.info("Controlador MIDI inicializado")
    
    def cleanup(self):
        """Cleanup automático de recursos MIDI"""
        try:
            self.logger.info("Executando cleanup de recursos MIDI...")
            
            # Para monitoramento
            self.stop_midi_input_monitoring()
            
            # Desconecta controladores específicos
            if self.zoom_g3x:
                self.zoom_g3x.disconnect()
            if self.chocolate:
                self.chocolate.disconnect()
            
            # Fecha todas as conexões do pool
            with self._connection_lock:
                for port_name, port in self._midi_connections.items():
                    try:
                        if port and hasattr(port, 'close'):
                            port.close()
                            self.logger.debug(f"Porta MIDI fechada: {port_name}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao fechar porta {port_name}: {e}")
                self._midi_connections.clear()
            
            # Força liberação de recursos ALSA
            try:
                import mido
                # Fecha todas as portas abertas pelo mido
                for port in mido.get_input_names():
                    try:
                        temp_port = mido.open_input(port)
                        temp_port.close()
                    except:
                        pass
                for port in mido.get_output_names():
                    try:
                        temp_port = mido.open_output(port)
                        temp_port.close()
                    except:
                        pass
            except Exception as e:
                self.logger.warning(f"Erro ao limpar portas mido: {e}")
            
            self.logger.info("Cleanup de recursos MIDI concluído")
            
        except Exception as e:
            self.logger.error(f"Erro durante cleanup: {e}")
    
    def _get_midi_connection(self, port_name: str, port_type: str = 'output'):
        """Obtém conexão MIDI do pool ou cria nova"""
        connection_key = f"{port_type}_{port_name}"
        
        with self._connection_lock:
            if connection_key in self._midi_connections:
                port = self._midi_connections[connection_key]
                if port and hasattr(port, 'closed') and not port.closed:
                    return port
                else:
                    # Remove conexão inválida
                    del self._midi_connections[connection_key]
            
            # Cria nova conexão
            try:
                if port_type == 'input':
                    port = mido.open_input(port_name)
                else:
                    port = mido.open_output(port_name)
                
                self._midi_connections[connection_key] = port
                self.logger.debug(f"Nova conexão MIDI criada: {connection_key}")
                return port
                
            except Exception as e:
                self.logger.error(f"Erro ao criar conexão MIDI {connection_key}: {e}")
                return None
    
    def _close_midi_connection(self, port_name: str, port_type: str = 'output'):
        """Fecha conexão MIDI específica"""
        connection_key = f"{port_type}_{port_name}"
        
        with self._connection_lock:
            if connection_key in self._midi_connections:
                port = self._midi_connections[connection_key]
                try:
                    if port and hasattr(port, 'close'):
                        port.close()
                        self.logger.debug(f"Conexão MIDI fechada: {connection_key}")
                except Exception as e:
                    self.logger.warning(f"Erro ao fechar conexão {connection_key}: {e}")
                finally:
                    del self._midi_connections[connection_key]
    
    def _send_midi_with_connection_pool(self, message, port_name: str, port_type: str = 'output'):
        """Envia mensagem MIDI usando pool de conexões"""
        try:
            port = self._get_midi_connection(port_name, port_type)
            if port:
                port.send(message)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem MIDI: {e}")
            # Remove conexão problemática
            self._close_midi_connection(port_name, port_type)
            return False
    
    def _load_midi_config(self) -> Dict:
        """Carrega configurações MIDI do arquivo"""
        config_path = os.path.join(Config.BASE_DIR, 'data', 'midi_config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração MIDI: {str(e)}")
        
        # Configuração padrão
        return {
            'input_device': None,
            'output_device': None,
            'auto_connect': True,
            'devices': {
                'usb': [],
                'bluetooth': []
            }
        }
    
    def _save_midi_config(self):
        """Salva configurações MIDI no arquivo"""
        config_path = os.path.join(Config.BASE_DIR, 'data', 'midi_config.json')
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.midi_config, f, indent=2, ensure_ascii=False)
            self.logger.info("Configuração MIDI salva")
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração MIDI: {str(e)}")
    
    def initialize(self) -> bool:
        """Inicializa o controlador MIDI"""
        try:
            self.logger.info("Inicializando controlador MIDI...")
            
            # Lista portas MIDI disponíveis
            self._list_midi_ports()
            
            # Inicializa controladores específicos
            self._init_zoom_g3x()
            self._init_chocolate()
            
            # Conecta dispositivos configurados
            if self.midi_config['auto_connect']:
                self._connect_configured_devices()
            
            # Verifica conectividade
            self._check_connectivity()
            
            self.logger.info("Controlador MIDI inicializado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar controlador MIDI: {str(e)}")
            return False
    
    def _list_midi_ports(self):
        """Lista portas MIDI disponíveis"""
        try:
            import mido
            
            # Lista portas disponíveis
            input_names = mido.get_input_names()
            output_names = mido.get_output_names()
            
            self._available_ports = {
                'inputs': input_names,
                'outputs': output_names
            }
            
            self.logger.info(f"Portas MIDI encontradas:")
            self.logger.info(f"  Entradas: {input_names}")
            self.logger.info(f"  Saídas: {output_names}")
            
            # Categoriza dispositivos
            self._categorize_devices()
            
        except ImportError:
            self.logger.warning("Módulo mido não disponível, usando simulação")
            self._available_ports = {
                'inputs': ['Chocolate MIDI In', 'Zoom G3X MIDI In'],
                'outputs': ['Chocolate MIDI Out', 'Zoom G3X MIDI Out']
            }
        except Exception as e:
            self.logger.error(f"Erro ao listar portas MIDI: {str(e)}")
            self._available_ports = {
                'inputs': [],
                'outputs': []
            }
    
    def _categorize_devices(self):
        """Categoriza dispositivos MIDI detectados"""
        try:
            inputs = self._available_ports.get('inputs', [])
            outputs = self._available_ports.get('outputs', [])
            
            # Mapeia dispositivos reais para nomes esperados
            devices = {
                'inputs': [],
                'outputs': []
            }
            
            # Mapeia entradas
            for input_name in inputs:
                if 'zoom' in input_name.lower() or 'g series' in input_name.lower():
                    devices['inputs'].append({
                        'name': 'Zoom G3X MIDI In',
                        'real_name': input_name,
                        'type': 'zoom_g3x'
                    })
                elif 'sinco' in input_name.lower() or 'footctrl' in input_name.lower() or 'chocolate' in input_name.lower():
                    devices['inputs'].append({
                        'name': 'Chocolate MIDI In',
                        'real_name': input_name,
                        'type': 'chocolate'
                    })
                else:
                    devices['inputs'].append({
                        'name': input_name,
                        'real_name': input_name,
                        'type': 'generic'
                    })
            
            # Mapeia saídas
            for output_name in outputs:
                if 'zoom' in output_name.lower() or 'g series' in output_name.lower():
                    devices['outputs'].append({
                        'name': 'Zoom G3X MIDI Out',
                        'real_name': output_name,
                        'type': 'zoom_g3x'
                    })
                elif 'sinco' in output_name.lower() or 'footctrl' in output_name.lower() or 'chocolate' in output_name.lower():
                    devices['outputs'].append({
                        'name': 'Chocolate MIDI Out',
                        'real_name': output_name,
                        'type': 'chocolate'
                    })
                else:
                    devices['outputs'].append({
                        'name': output_name,
                        'real_name': output_name,
                        'type': 'generic'
                    })
            
            # Atualiza configuração MIDI
            self.midi_config['devices'] = devices
            
            # Se não há dispositivo configurado, usa o primeiro disponível (ignorando Midi Through)
            if not self.midi_config.get('input_device') and devices['inputs']:
                # Procura primeiro dispositivo que não seja "Midi Through"
                selected_input = None
                for device in devices['inputs']:
                    if 'midi through' not in device['name'].lower():
                        selected_input = device['name']
                        break
                
                # Se não encontrou nenhum, usa o primeiro disponível
                if not selected_input and devices['inputs']:
                    selected_input = devices['inputs'][0]['name']
                
                if selected_input:
                    self.midi_config['input_device'] = selected_input
                    self.logger.info(f"Dispositivo de entrada padrão: {selected_input}")
            
            if not self.midi_config.get('output_device') and devices['outputs']:
                # Procura primeiro dispositivo que não seja "Midi Through"
                selected_output = None
                for device in devices['outputs']:
                    if 'midi through' not in device['name'].lower():
                        selected_output = device['name']
                        break
                
                # Se não encontrou nenhum, usa o primeiro disponível
                if not selected_output and devices['outputs']:
                    selected_output = devices['outputs'][0]['name']
                
                if selected_output:
                    self.midi_config['output_device'] = selected_output
                    self.logger.info(f"Dispositivo de saída padrão: {selected_output}")
            
            self._save_midi_config()
            
        except Exception as e:
            self.logger.error(f"Erro ao categorizar dispositivos: {str(e)}")
    
    def _connect_configured_devices(self):
        """Conecta dispositivos configurados"""
        try:
            # Desconecta controladores existentes
            if self.zoom_g3x:
                self.zoom_g3x.disconnect()
                self.device_status['zoom_g3x']['connected'] = False
                self.device_status['zoom_g3x']['port'] = None
            
            if self.chocolate:
                self.chocolate.disconnect()
                self.device_status['chocolate']['connected'] = False
                self.device_status['chocolate']['port'] = None
            
            # Reconecta dispositivos de entrada
            if self.midi_config['input_device']:
                self._connect_input_device(self.midi_config['input_device'])
            
            # Reconecta dispositivos de saída
            if self.midi_config['output_device']:
                self._connect_output_device(self.midi_config['output_device'])
            
            # Reconecta controladores específicos baseado na configuração
            self._reconnect_specific_controllers()
            
            # Verifica conectividade
            self._check_connectivity()
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar dispositivos configurados: {str(e)}")
    
    def _reconnect_specific_controllers(self):
        """Reconecta controladores específicos baseado na configuração atual"""
        try:
            # Reconecta Zoom G3X se for o dispositivo de saída configurado
            output_device = self.midi_config.get('output_device', '')
            if 'zoom' in output_device.lower() or 'g3x' in output_device.lower():
                if not self.zoom_g3x:
                    self._init_zoom_g3x()
                else:
                    # Procura porta do Zoom G3X usando a configuração MIDI
                    zoom_port = None
                    for device in self.midi_config.get('devices', {}).get('outputs', []):
                        if device['type'] == 'zoom_g3x':
                            zoom_port = device['real_name']
                            break
                    
                    if zoom_port:
                        try:
                            import mido
                            available_outputs = mido.get_output_names()
                            if zoom_port in available_outputs:
                                self.zoom_g3x.connect(zoom_port)
                                self.device_status['zoom_g3x']['connected'] = True
                                self.device_status['zoom_g3x']['port'] = zoom_port
                                self.logger.info(f"Zoom G3X reconectado na porta: {zoom_port}")
                        except ImportError:
                            self.logger.warning("Módulo mido não disponível")
            
            # Reconecta Chocolate se for o dispositivo de saída configurado
            if 'chocolate' in output_device.lower():
                if not self.chocolate:
                    self._init_chocolate()
                else:
                    # Procura porta do Chocolate usando a configuração MIDI
                    chocolate_port = None
                    for device in self.midi_config.get('devices', {}).get('outputs', []):
                        if device['type'] == 'chocolate':
                            chocolate_port = device['real_name']
                            break
                    
                    if chocolate_port:
                        try:
                            import mido
                            available_outputs = mido.get_output_names()
                            if chocolate_port in available_outputs:
                                self.chocolate.connect(chocolate_port)
                                self.device_status['chocolate']['connected'] = True
                                self.device_status['chocolate']['port'] = chocolate_port
                                self.logger.info(f"Chocolate reconectado na porta: {chocolate_port}")
                        except ImportError:
                            self.logger.warning("Módulo mido não disponível")
            
        except Exception as e:
            self.logger.error(f"Erro ao reconectar controladores específicos: {str(e)}")
    
    def _connect_input_device(self, device_name: str):
        """Conecta dispositivo de entrada"""
        try:
            # Busca o nome real correspondente ao nome mapeado
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('inputs', []):
                if device['name'] == device_name:
                    real_device_name = device['real_name']
                    break
            if not real_device_name:
                self.logger.error(f"Dispositivo de entrada {device_name} não encontrado na configuração")
                return False
            if real_device_name in self._available_ports['inputs']:
                self.logger.info(f"Dispositivo de entrada conectado: {device_name} (porta real: {real_device_name})")
                return True
            else:
                self.logger.error(f"Porta real {real_device_name} não encontrada entre as disponíveis: {self._available_ports['inputs']}")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao conectar dispositivo de entrada: {str(e)}")
        return False
    
    def _connect_output_device(self, device_name: str):
        """Conecta dispositivo de saída"""
        try:
            # Busca o nome real correspondente ao nome mapeado
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == device_name:
                    real_device_name = device['real_name']
                    break
            
            if not real_device_name:
                self.logger.error(f"Dispositivo de saída {device_name} não encontrado na configuração")
                return False
                
            if real_device_name in self._available_ports['outputs']:
                # Conecta Zoom G3X ou Chocolate baseado no tipo
                device_type = None
                for device in self.midi_config.get('devices', {}).get('outputs', []):
                    if device['name'] == device_name:
                        device_type = device['type']
                        break
                
                if device_type == 'zoom_g3x':
                    if self.zoom_g3x:
                        if self.zoom_g3x.connect(real_device_name):
                            self.device_status['zoom_g3x']['connected'] = True
                            self.device_status['zoom_g3x']['port'] = real_device_name
                            self.logger.info(f"Zoom G3X conectado na porta: {real_device_name}")
                elif device_type == 'chocolate':
                    if self.chocolate:
                        if self.chocolate.connect(real_device_name):
                            self.device_status['chocolate']['connected'] = True
                            self.device_status['chocolate']['port'] = real_device_name
                            self.logger.info(f"Chocolate conectado na porta: {real_device_name}")
                
                self.logger.info(f"Dispositivo de saída conectado: {device_name} (porta real: {real_device_name})")
                return True
            else:
                self.logger.error(f"Porta real {real_device_name} não encontrada entre as disponíveis: {self._available_ports['outputs']}")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao conectar dispositivo de saída: {str(e)}")
            return False
    
    def _init_zoom_g3x(self):
        """Inicializa controlador do Zoom G3X"""
        try:
            self.zoom_g3x = ZoomG3XController()
            
            # Procura porta do Zoom G3X usando a configuração MIDI
            zoom_port = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['type'] == 'zoom_g3x':
                    zoom_port = device['real_name']
                    break
            
            if zoom_port:
                # Verifica se a porta ainda existe
                try:
                    import mido
                    available_outputs = mido.get_output_names()
                    if zoom_port in available_outputs:
                        # Tenta conectar e verifica se foi bem-sucedido
                        if self.zoom_g3x.connect(zoom_port):
                            self.device_status['zoom_g3x']['connected'] = True
                            self.device_status['zoom_g3x']['port'] = zoom_port
                            self.logger.info(f"Zoom G3X conectado na porta: {zoom_port}")
                        else:
                            # Tenta método alternativo se a conexão falhou
                            self.logger.info("Tentando método alternativo de conexão...")
                            if self._try_alternative_zoom_connection(zoom_port):
                                self.device_status['zoom_g3x']['connected'] = True
                                self.device_status['zoom_g3x']['port'] = zoom_port
                                self.logger.info(f"Zoom G3X conectado via método alternativo: {zoom_port}")
                            else:
                                self.device_status['zoom_g3x']['connected'] = False
                                self.device_status['zoom_g3x']['port'] = None
                                self.logger.warning(f"Falha ao conectar Zoom G3X na porta: {zoom_port}")
                                self.logger.warning("⚠ O Zoom G3X pode precisar de alimentação externa para funcionar via MIDI")
                    else:
                        self.device_status['zoom_g3x']['connected'] = False
                        self.device_status['zoom_g3x']['port'] = None
                        self.logger.warning("Porta Zoom G3X não encontrada")
                except ImportError:
                    self.device_status['zoom_g3x']['connected'] = False
                    self.device_status['zoom_g3x']['port'] = None
                    self.logger.warning("Módulo mido não disponível")
            else:
                self.device_status['zoom_g3x']['connected'] = False
                self.device_status['zoom_g3x']['port'] = None
                self.logger.warning("Zoom G3X não configurado")
                
        except Exception as e:
            self.device_status['zoom_g3x']['connected'] = False
            self.device_status['zoom_g3x']['port'] = None
            self.logger.error(f"Erro ao inicializar Zoom G3X: {str(e)}")
    
    def _try_alternative_zoom_connection(self, port_name: str) -> bool:
        """Tenta métodos alternativos de conexão com o Zoom G3X"""
        try:
            import mido
            import time
            
            # Método 1: Conexão direta sem context manager
            try:
                self.logger.info("Tentando método 1: Conexão direta...")
                port = mido.open_output(port_name)
                test_msg = mido.Message('program_change', channel=0, program=0)
                port.send(test_msg)
                port.close()
                self.logger.info("Método 1 funcionou!")
                return True
            except Exception as e1:
                self.logger.warning(f"Método 1 falhou: {e1}")
            
            # Método 2: Com delay
            try:
                self.logger.info("Tentando método 2: Com delay...")
                time.sleep(1)
                with mido.open_output(port_name) as port:
                    time.sleep(0.5)
                    test_msg = mido.Message('program_change', channel=0, program=1)
                    port.send(test_msg)
                self.logger.info("Método 2 funcionou!")
                return True
            except Exception as e2:
                self.logger.warning(f"Método 2 falhou: {e2}")
            
            # Método 3: Tenta reconectar o controlador
            try:
                self.logger.info("Tentando método 3: Reinicialização do controlador...")
                self.zoom_g3x.disconnect()
                time.sleep(1)
                if self.zoom_g3x.connect(port_name):
                    self.logger.info("Método 3 funcionou!")
                    return True
            except Exception as e3:
                self.logger.warning(f"Método 3 falhou: {e3}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro nos métodos alternativos: {str(e)}")
            return False
    
    def _init_chocolate(self):
        """Inicializa controlador do Chocolate (considera conectado se detectado via USB usando aconnect)"""
        try:
            self.chocolate = ChocolateController()
            chocolate_port = None
            
            # Procura em entradas (Chocolate é um dispositivo de entrada)
            for device in self.midi_config.get('devices', {}).get('inputs', []):
                if device['type'] == 'chocolate':
                    chocolate_port = device['real_name']
                    break
            
            self.logger.info(f"🔍 Procurando porta do Chocolate: {chocolate_port}")
            
            if chocolate_port:
                # Se encontrou a porta na configuração, considera conectado
                self.device_status['chocolate']['connected'] = True
                self.device_status['chocolate']['port'] = chocolate_port
                self.logger.info(f"✅ Chocolate detectado via USB e configurado: {chocolate_port}")
            else:
                # Se não encontrou na configuração, verifica se está disponível via aconnect
                try:
                    import subprocess
                    result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        aconnect_output = result.stdout
                        self.logger.info(f"📋 Saída do aconnect: {aconnect_output}")
                        
                        # Procura por SINCO na saída do aconnect
                        if 'sinco' in aconnect_output.lower():
                            # Extrai o nome da porta do SINCO
                            lines = aconnect_output.split('\n')
                            for line in lines:
                                if 'sinco' in line.lower():
                                    # Extrai o nome da porta (ex: "SINCO MIDI 1")
                                    if 'SINCO MIDI' in line:
                                        chocolate_port = f"SINCO:SINCO MIDI 1"
                                        break
                            
                            if chocolate_port:
                                self.device_status['chocolate']['connected'] = True
                                self.device_status['chocolate']['port'] = chocolate_port
                                self.logger.info(f"✅ Chocolate detectado via USB (aconnect): {chocolate_port}")
                            else:
                                self.device_status['chocolate']['connected'] = False
                                self.device_status['chocolate']['port'] = None
                                self.logger.warning(f"❌ Chocolate não detectado via USB (aconnect)")
                        else:
                            self.device_status['chocolate']['connected'] = False
                            self.device_status['chocolate']['port'] = None
                            self.logger.warning(f"❌ Chocolate não detectado via USB (aconnect)")
                    else:
                        self.device_status['chocolate']['connected'] = False
                        self.device_status['chocolate']['port'] = None
                        self.logger.warning(f"❌ Erro ao executar aconnect: {result.stderr}")
                        
                except Exception as e:
                    self.device_status['chocolate']['connected'] = False
                    self.device_status['chocolate']['port'] = None
                    self.logger.error(f"❌ Erro ao verificar porta Chocolate via aconnect: {str(e)}")
                
        except Exception as e:
            self.device_status['chocolate']['connected'] = False
            self.device_status['chocolate']['port'] = None
            self.logger.error(f"❌ Erro ao inicializar Chocolate: {str(e)}")
    
    def _find_device_port(self, device_name: str) -> Optional[str]:
        """Encontra porta de um dispositivo específico"""
        try:
            # Procura em inputs e outputs
            for port in self._available_ports.get('inputs', []):
                if device_name.lower() in port.lower():
                    return port
            
            for port in self._available_ports.get('outputs', []):
                if device_name.lower() in port.lower():
                    return port
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao procurar porta do dispositivo {device_name}: {str(e)}")
            return None
    
    def _check_connectivity(self):
        """Verifica conectividade dos dispositivos"""
        try:
            # Verifica se pelo menos um dispositivo está conectado
            connected_devices = []
            
            if self.device_status['zoom_g3x']['connected']:
                connected_devices.append('Zoom G3X')
            if self.device_status['chocolate']['connected']:
                connected_devices.append('Chocolate')
            
            if connected_devices:
                self._connected = True
                self.logger.info(f"Pelo menos um dispositivo MIDI está conectado: {', '.join(connected_devices)}")
            else:
                self._connected = False
                self.logger.warning("Nenhum dispositivo MIDI conectado")
                
            # Verifica alimentação dos dispositivos
            self._check_power_status()
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar conectividade: {str(e)}")
    
    def _check_power_status(self):
        """Verifica status de alimentação dos dispositivos MIDI"""
        try:
            import mido
            
            # Lista de dispositivos que precisam de alimentação externa
            external_power_devices = [
                'zoom g3x', 'zoom g series', 'zoom g1', 'zoom g3', 'zoom g5',
                'footctrl', 'chocolate', 'midi controller'
            ]
            
            available_outputs = mido.get_output_names()
            
            for device_name in available_outputs:
                device_lower = device_name.lower()
                
                # Verifica se é um dispositivo que precisa de alimentação externa
                needs_external_power = any(keyword in device_lower for keyword in external_power_devices)
                
                if needs_external_power:
                    # Tenta abrir a porta para verificar se está respondendo
                    try:
                        with mido.open_output(device_name) as port:
                            # Tenta enviar uma mensagem de teste
                            test_msg = mido.Message('program_change', channel=0, program=0)
                            port.send(test_msg)
                            self.logger.info(f"✓ {device_name} está respondendo corretamente")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ['timeout', 'not responding', 'no response', 'error']):
                            self.logger.warning(f"⚠ {device_name} pode precisar de alimentação externa. Erro: {str(e)}")
                            self.logger.info(f"💡 Dica: Conecte a alimentação externa do {device_name} e tente novamente")
                        else:
                            self.logger.error(f"✗ Erro ao testar {device_name}: {str(e)}")
                            
        except Exception as e:
            self.logger.error(f"Erro ao verificar status de alimentação: {str(e)}")
    
    def is_connected(self) -> bool:
        """Verifica se há dispositivos conectados"""
        return self._connected
    
    def get_device_status(self) -> Dict:
        """Retorna status dos dispositivos"""
        return self.device_status.copy()
    
    def get_available_devices(self) -> Dict:
        """Retorna dispositivos disponíveis categorizados"""
        return self.midi_config['devices'].copy()
    
    def get_midi_config(self) -> Dict:
        """Retorna configuração MIDI atual"""
        return self.midi_config.copy()
    
    def update_midi_config(self, config: Dict) -> bool:
        """Atualiza a configuração MIDI"""
        with self._lock:
            # Atualiza apenas as chaves permitidas
            allowed_keys = ['input_device', 'output_device', 'auto_connect']
            for key in allowed_keys:
                if key in config:
                    self.midi_config[key] = config[key]
            
            self.logger.info(f"Configuração MIDI atualizada: {self.midi_config}")
            self._save_midi_config()
            
            # Reconecta dispositivos com a nova configuração
            self._connect_configured_devices()
            
            return True
    
    def send_patch(self, patch_data: Dict) -> bool:
        """Envia os comandos de um patch para o dispositivo de saída configurado"""
        with self._lock:
            try:
                command_type = patch_data.get('command_type')
                device_name = patch_data.get('output_device')
                self.logger.info(f"[PATCH DEBUG] Dados completos do patch recebido: {patch_data}")
                self.logger.info(f"Enviando patch '{patch_data.get('name')}' para {device_name} (tipo: {command_type})")
                if not device_name:
                    self.logger.error("Dispositivo de saída não definido no patch")
                    return False
                # Delega para o controlador Zoom G3X se for o caso
                if self.zoom_g3x and getattr(self.zoom_g3x, 'connected', False) and ('zoom' in device_name.lower() or 'g3x' in device_name.lower()):
                    self.logger.info(f"[PATCH DEBUG] Enviando para Zoom G3X: {patch_data}")
                    return self.zoom_g3x.load_patch(patch_data)
                # Lógica para comandos MIDI genéricos
                if command_type == 'pc':
                    program = patch_data.get('program')
                    channel = patch_data.get('channel', 1) # Canal padrão 1
                    self.logger.info(f"[PATCH DEBUG] Montando comando PC: channel={channel}, program={program}, device={device_name}")
                    if program is not None:
                        return self._send_pc_to_device(channel, program, device_name)
                elif command_type == 'cc':
                    cc = patch_data.get('cc')
                    value = patch_data.get('value')
                    channel = patch_data.get('channel', 1) # Canal padrão 1
                    self.logger.info(f"[PATCH DEBUG] Montando comando CC: channel={channel}, cc={cc}, value={value}, device={device_name}")
                    if cc is not None and value is not None:
                        return self._send_cc_to_device(channel, cc, value, device_name)
                elif command_type == 'note_on':
                    note = patch_data.get('note')
                    velocity = patch_data.get('velocity', 127) # Velocidade padrão
                    channel = patch_data.get('channel', 1) # Canal padrão 1
                    self.logger.info(f"[PATCH DEBUG] Montando comando Note On: channel={channel}, note={note}, velocity={velocity}, device={device_name}")
                    if note is not None:
                        return self._send_note_on_to_device(channel, note, velocity, device_name)
                elif command_type == 'note_off':
                    note = patch_data.get('note')
                    channel = patch_data.get('channel', 1) # Canal padrão 1
                    self.logger.info(f"[PATCH DEBUG] Montando comando Note Off: channel={channel}, note={note}, device={device_name}")
                    if note is not None:
                        return self._send_note_off_to_device(channel, note, device_name)
                self.logger.warning(f"Tipo de comando '{command_type}' não suportado ou dados insuficientes para o patch.")
                return False
            except Exception as e:
                self.logger.error(f"Erro ao enviar patch: {str(e)}")
                return False
    
    def toggle_effect(self, effect_name: str, enabled: bool) -> bool:
        """Liga/desliga um efeito no dispositivo configurado"""
        try:
            output_device = self.midi_config.get('output_device')
            
            if not output_device:
                self.logger.error("Nenhum dispositivo de saída configurado")
                return False
            
            # Envia para o dispositivo apropriado
            if 'zoom' in output_device.lower() or 'g3x' in output_device.lower():
                if not self.zoom_g3x or not self.device_status['zoom_g3x']['connected']:
                    self.logger.error("Zoom G3X não está conectado")
                    return False
                success = self.zoom_g3x.toggle_effect(effect_name, enabled)
            else:
                self.logger.error(f"Dispositivo de saída não suporta efeitos: {output_device}")
                return False
            
            if success:
                status = "ligado" if enabled else "desligado"
                self.logger.info(f"Efeito {effect_name} {status}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao alternar efeito: {str(e)}")
            return False
    
    def send_midi_command(self, command: Dict) -> bool:
        """Envia comando MIDI para o dispositivo de saída configurado"""
        try:
            output_device = self.midi_config.get('output_device')
            
            if not output_device:
                self.logger.error("Nenhum dispositivo de saída configurado")
                return False
            
            command_type = command.get('type')
            channel = command.get('channel', 0)
            
            if command_type == 'cc':
                cc = command.get('cc')
                value = command.get('value', 0)
                return self._send_cc(channel, cc, value)
            
            elif command_type == 'pc':
                program = command.get('program', 0)
                return self._send_pc(channel, program)
            
            elif command_type == 'note_on':
                note = command.get('note', 60)
                velocity = command.get('velocity', 64)
                return self._send_note_on(channel, note, velocity)
            
            elif command_type == 'note_off':
                note = command.get('note', 60)
                return self._send_note_off(channel, note)
            
            else:
                self.logger.error(f"Tipo de comando MIDI não suportado: {command_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar comando MIDI: {str(e)}")
            return False
    
    def _send_cc(self, channel: int, cc: int, value: int) -> bool:
        """Envia mensagem Control Change"""
        try:
            output_device = self.midi_config.get('output_device')
            
            if 'zoom' in output_device.lower() or 'g3x' in output_device.lower():
                if self.zoom_g3x and self.device_status['zoom_g3x']['connected']:
                    return self.zoom_g3x.send_cc(channel, cc, value)
            elif 'chocolate' in output_device.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    return self.chocolate.send_cc(channel, cc, value)
            
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar CC: {str(e)}")
            return False
    
    def _send_pc(self, channel: int, program: int) -> bool:
        """Envia mensagem Program Change"""
        try:
            output_device = self.midi_config.get('output_device')
            
            if 'zoom' in output_device.lower() or 'g3x' in output_device.lower():
                if self.zoom_g3x and self.device_status['zoom_g3x']['connected']:
                    result = self.zoom_g3x.send_pc(channel, program)
                    if result:
                        self.device_status['zoom_g3x']['last_pc'] = program
                    return result
            elif 'chocolate' in output_device.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    result = self.chocolate.send_pc(channel, program)
                    if result:
                        self.device_status['chocolate']['last_pc'] = program
                    return result
            
            # Se não conseguiu via controlador, tenta enviar diretamente via mido
            result = self._send_midi_via_mido('program_change', output_device, channel=channel, program=program)
            # Atualiza last_pc se sucesso
            if result:
                if 'zoom' in output_device.lower() or 'g3x' in output_device.lower():
                    self.device_status['zoom_g3x']['last_pc'] = program
                elif 'chocolate' in output_device.lower():
                    self.device_status['chocolate']['last_pc'] = program
            return result
        except Exception as e:
            self.logger.error(f"Erro ao enviar PC: {str(e)}")
            return False
    
    def _send_note_on(self, channel: int, note: int, velocity: int) -> bool:
        """Envia mensagem Note On"""
        try:
            output_device = self.midi_config.get('output_device')
            
            if 'chocolate' in output_device.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    return self.chocolate.send_note_on(channel, note, velocity)
            
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar Note On: {str(e)}")
            return False
    
    def _send_note_off(self, channel: int, note: int) -> bool:
        """Envia mensagem Note Off"""
        try:
            output_device = self.midi_config.get('output_device')
            
            if 'chocolate' in output_device.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    return self.chocolate.send_note_off(channel, note)
            
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar Note Off: {str(e)}")
            return False
    
    def _send_cc_to_device(self, channel: int, cc: int, value: int, device_name: str) -> bool:
        """Envia Control Change para dispositivo específico"""
        try:
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == device_name:
                    real_device_name = device['real_name']
                    break
            
            if not real_device_name:
                self.logger.error(f"Dispositivo {device_name} não encontrado")
                return False
            
            # Tenta enviar via controlador específico primeiro
            if 'zoom' in device_name.lower() or 'g3x' in device_name.lower():
                if self.zoom_g3x and self.device_status['zoom_g3x']['connected']:
                    return self.zoom_g3x.send_cc(channel, cc, value)
            elif 'chocolate' in device_name.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    return self.chocolate.send_cc(channel, cc, value)
            
            # Se não conseguiu via controlador, tenta enviar diretamente via mido
            return self._send_midi_via_mido('control_change', real_device_name, channel=channel, control=cc, value=value)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar CC para {device_name}: {str(e)}")
            return False
    
    def _send_note_on_to_device(self, channel: int, note: int, velocity: int, device_name: str) -> bool:
        """Envia Note On para dispositivo específico"""
        try:
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == device_name:
                    real_device_name = device['real_name']
                    break
            
            if not real_device_name:
                self.logger.error(f"Dispositivo {device_name} não encontrado")
                return False
            
            # Tenta enviar via controlador específico primeiro
            if 'zoom' in device_name.lower() or 'g3x' in device_name.lower():
                if self.zoom_g3x and self.device_status['zoom_g3x']['connected']:
                    return self.zoom_g3x.send_note_on(channel, note, velocity)
            elif 'chocolate' in device_name.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    return self.chocolate.send_note_on(channel, note, velocity)
            
            # Se não conseguiu via controlador, tenta enviar diretamente via mido
            return self._send_midi_via_mido('note_on', real_device_name, channel=channel, note=note, velocity=velocity)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar Note On para {device_name}: {str(e)}")
            return False
    
    def _send_note_off_to_device(self, channel: int, note: int, device_name: str) -> bool:
        """Envia Note Off para dispositivo específico"""
        try:
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == device_name:
                    real_device_name = device['real_name']
                    break
            
            if not real_device_name:
                self.logger.error(f"Dispositivo {device_name} não encontrado")
                return False
            
            # Tenta enviar via controlador específico primeiro
            if 'zoom' in device_name.lower() or 'g3x' in device_name.lower():
                if self.zoom_g3x and self.device_status['zoom_g3x']['connected']:
                    return self.zoom_g3x.send_note_off(channel, note)
            elif 'chocolate' in device_name.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    return self.chocolate.send_note_off(channel, note)
            
            # Se não conseguiu via controlador, tenta enviar diretamente via mido
            return self._send_midi_via_mido('note_off', real_device_name, channel=channel, note=note, velocity=0)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar Note Off para {device_name}: {str(e)}")
            return False
    
    def _send_midi_via_mido(self, message_type: str, device_name: str, **kwargs) -> bool:
        """Envia mensagem MIDI via mido usando pool de conexões"""
        try:
            import mido
            
            # Cria mensagem MIDI
            if message_type == 'program_change':
                message = mido.Message('program_change', channel=kwargs.get('channel', 0), program=kwargs.get('program', 0))
            elif message_type == 'control_change':
                message = mido.Message('control_change', channel=kwargs.get('channel', 0), control=kwargs.get('control', 0), value=kwargs.get('value', 0))
            elif message_type == 'note_on':
                message = mido.Message('note_on', channel=kwargs.get('channel', 0), note=kwargs.get('note', 0), velocity=kwargs.get('velocity', 64))
            elif message_type == 'note_off':
                message = mido.Message('note_off', channel=kwargs.get('channel', 0), note=kwargs.get('note', 0))
            else:
                self.logger.error(f"Tipo de mensagem não suportado: {message_type}")
                return False
            
            # Envia usando pool de conexões
            return self._send_midi_with_connection_pool(message, device_name, 'output')
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem MIDI: {str(e)}")
            return False
    
    def _send_midi_strategy_1(self, mido, message_type: str, device_name: str, **kwargs) -> bool:
        """Estratégia 1: Conexão temporária com context manager"""
        try:
            with mido.open_output(device_name) as port:
                msg = mido.Message(message_type, **kwargs)
                port.send(msg)
                return True
        except Exception as e:
            raise e
    
    def _send_midi_strategy_2(self, mido, message_type: str, device_name: str, **kwargs) -> bool:
        """Estratégia 2: Conexão persistente"""
        try:
            port = mido.open_output(device_name)
            msg = mido.Message(message_type, **kwargs)
            port.send(msg)
            port.close()
            return True
        except Exception as e:
            raise e
    
    def _send_midi_strategy_3(self, mido, message_type: str, device_name: str, **kwargs) -> bool:
        """Estratégia 3: Usando backend específico"""
        try:
            # Tenta com backend específico para Windows
            port = mido.open_output(device_name, backend='mido.backends.rtmidi')
            msg = mido.Message(message_type, **kwargs)
            port.send(msg)
            port.close()
            return True
        except Exception as e:
            raise e
    
    def scan_devices(self) -> Dict:
        """Escaneia dispositivos MIDI disponíveis"""
        try:
            self._list_midi_ports()
            self._check_connectivity()
            
            return {
                'available_ports': self._available_ports,
                'device_status': self.device_status,
                'connected': self._connected,
                'devices': self.midi_config['devices']
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao escanear dispositivos: {str(e)}")
            return {}
    
    def get_received_commands(self) -> List[Dict]:
        """Retorna lista de comandos MIDI recebidos"""
        commands = getattr(self, '_received_commands', [])
        # Retorna apenas comandos que ainda não foram enviados
        new_commands = commands[getattr(self, '_last_sent_index', 0):]
        self._last_sent_index = len(commands)
        return new_commands
    
    def clear_received_commands(self):
        """Limpa lista de comandos MIDI recebidos"""
        self._received_commands = []
        self._last_sent_index = 0
        self.logger.info("Comandos MIDI recebidos limpos")
    
    def add_received_command(self, command: Dict):
        """Adiciona comando MIDI recebido à lista"""
        if not hasattr(self, '_received_commands'):
            self._received_commands = []
        
        # Adiciona timestamp
        command['timestamp'] = time.time()
        
        # Limita a 100 comandos
        if len(self._received_commands) >= 100:
            self._received_commands = self._received_commands[-99:]
        
        self._received_commands.append(command)
        self.logger.debug(f"Comando MIDI recebido: {command}")
    
    def start_midi_input_monitoring(self, device_name: str = None):
        """Inicia monitoramento de entrada MIDI usando pool de conexões"""
        try:
            # Usa dispositivo especificado ou o configurado
            input_device = device_name or self.midi_config.get('input_device')
            if not input_device:
                self.logger.warning("Nenhum dispositivo de entrada configurado")
                return False
            
            # Inicializa lista de comandos se não existir
            if not hasattr(self, '_received_commands'):
                self._received_commands = []
                self._last_sent_index = 0
            
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('inputs', []):
                if device['name'] == input_device:
                    real_device_name = device['real_name']
                    break
            
            if not real_device_name:
                self.logger.error(f"Dispositivo {input_device} não encontrado na configuração")
                return False
            
            # Tenta conectar ao dispositivo de entrada usando pool de conexões
            try:
                if real_device_name in self._available_ports.get('inputs', []):
                    # Usa pool de conexões para entrada MIDI
                    port = self._get_midi_connection(real_device_name, 'input')
                    if port:
                        # Configura callback para mensagens recebidas
                        port.callback = self._on_midi_message
                        self._midi_input = port
                        self.logger.info(f"Monitoramento MIDI iniciado para: {real_device_name}")
                        self._input_monitoring_active = True
                        self._monitoring_device = input_device
                        self._monitoring_mode = "REAL"
                        return True
                    else:
                        self.logger.error(f"Falha ao abrir porta de entrada: {real_device_name}")
                        return False
                else:
                    self.logger.warning(f"Dispositivo de entrada {real_device_name} não encontrado")
                    self.logger.info(f"Dispositivos disponíveis: {self._available_ports.get('inputs', [])}")
                    
                    # Fallback para modo simulado
                    self.logger.info("Iniciando monitoramento em modo SIMULADO")
                    self._input_monitoring_active = True
                    self._monitoring_device = input_device
                    self._monitoring_mode = "SIMULATED"
                    return True
                    
            except Exception as e:
                self.logger.error(f"Erro ao conectar ao dispositivo de entrada: {str(e)}")
                return False
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar monitoramento MIDI: {str(e)}")
            return False
    
    def stop_midi_input_monitoring(self):
        """Para monitoramento de entrada MIDI usando pool de conexões"""
        try:
            self._input_monitoring_active = False
            
            # Remove callback da porta
            if hasattr(self, '_midi_input') and self._midi_input:
                try:
                    self._midi_input.callback = None
                    self._midi_input = None
                except:
                    pass
            
            self.logger.info("Monitoramento MIDI parado")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao parar monitoramento MIDI: {str(e)}")
            return False
    
    def get_monitoring_status(self) -> Dict:
        """Retorna status do monitoramento MIDI"""
        return {
            'active': getattr(self, '_input_monitoring_active', False),
            'device': getattr(self, '_monitoring_device', None),
            'mode': getattr(self, '_monitoring_mode', 'DISCONNECTED'),
            'command_count': len(getattr(self, '_received_commands', []))
        }
    
    def _on_midi_message(self, message):
        """Callback para mensagens MIDI recebidas"""
        try:
            # Converte mensagem para formato padrão
            command = {
                'type': message.type,
                'channel': getattr(message, 'channel', 0),
                'timestamp': time.time()
            }
            
            # Adiciona dados específicos do tipo de mensagem
            if message.type == 'note_on':
                command['note'] = message.note
                command['velocity'] = message.velocity
            elif message.type == 'note_off':
                command['note'] = message.note
                command['velocity'] = getattr(message, 'velocity', 0)
            elif message.type == 'control_change':
                command['cc'] = message.control
                command['value'] = message.value
            elif message.type == 'program_change':
                command['program'] = message.program
            
            # LOG DETALHADO: Comando MIDI recebido
            self.logger.info(f"[CHOCOLATE DEBUG] Comando MIDI recebido: {command}")
            
            # Adiciona à lista de comandos recebidos
            self.add_received_command(command)
            
            # Se for Program Change, ativa o patch correspondente do Chocolate
            if message.type == 'program_change':
                try:
                    # LOG DETALHADO: Busca de patch
                    self.logger.info(f"[CHOCOLATE DEBUG] Program Change detectado: program={command['program']}")
                    self.logger.info(f"[CHOCOLATE DEBUG] Total de patches do Chocolate: {len(self.chocolate_patches)}")
                    
                    # Lista todos os patches do Chocolate para debug
                    for i, patch in enumerate(self.chocolate_patches):
                        self.logger.info(f"[CHOCOLATE DEBUG] Patch {i+1}: id={patch.get('id')}, name={patch.get('name')}, input_channel={patch.get('input_channel')}, program={patch.get('program')}, zoom_patch={patch.get('zoom_patch')}")
                    
                    # Busca o patch correspondente
                    patch_encontrado = None
                    for patch in self.chocolate_patches:
                        if int(patch.get('input_channel', -1)) == int(command['program']):
                            patch_encontrado = patch
                            self.logger.info(f"[CHOCOLATE DEBUG] ✅ Patch encontrado por input_channel: {patch['name']}")
                            break
                    
                    # Se não encontrou por input_channel, tenta por program
                    if not patch_encontrado:
                        for patch in self.chocolate_patches:
                            if int(patch.get('program', -1)) == int(command['program']):
                                patch_encontrado = patch
                                self.logger.info(f"[CHOCOLATE DEBUG] ✅ Patch encontrado por program: {patch['name']}")
                                break
                    
                    if patch_encontrado:
                        self.logger.info(f"[CHOCOLATE DEBUG] Ativando patch: id={patch_encontrado['id']}, name={patch_encontrado['name']}, zoom_patch={patch_encontrado.get('zoom_patch')}")
                        try:
                            import requests
                            response = requests.post(
                                "http://localhost:5000/api/midi/patch/load",
                                json={"patch_id": patch_encontrado["id"]}, timeout=2
                            )
                            if response.status_code == 200:
                                self.logger.info(f"[CHOCOLATE DEBUG] ✅ Patch ativado com sucesso via HTTP")
                            else:
                                self.logger.error(f"[CHOCOLATE DEBUG] ❌ Erro HTTP ao ativar patch: {response.status_code} - {response.text}")
                        except Exception as e:
                            self.logger.error(f"[CHOCOLATE DEBUG] ❌ Erro ao ativar patch via HTTP: {e}")
                        self._last_patch_activated = patch_encontrado
                    else:
                        self.logger.warning(f"[CHOCOLATE DEBUG] ⚠️ Nenhum patch encontrado para program {command['program']}")
                except Exception as e:
                    self.logger.error(f"[CHOCOLATE DEBUG] ❌ Erro ao ativar patch via Program Change: {str(e)}")
            
            # Processa mapeamentos de banco se ativo
            self._process_bank_mappings(command)
            
            self.logger.debug(f"Mensagem MIDI recebida: {command}")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem MIDI: {str(e)}")
    
    def _process_bank_mappings(self, input_command: Dict):
        """Processa mapeamentos de banco para comandos de entrada"""
        try:
            # Obtém o banco ativo
            from app.database.models import DatabaseManager
            db_path = os.path.join(Config.BASE_DIR, 'data', 'raspmidi.db')
            db_manager = DatabaseManager(db_path)
            active_bank = db_manager.get_active_bank()
            
            if not active_bank:
                return
            
            # Procura por mapeamentos que correspondem ao comando de entrada
            for mapping in active_bank.mappings:
                if self._matches_input_command(input_command, mapping):
                    self._execute_output_command(mapping)
                    self.logger.info(f"Mapeamento executado: {mapping.description}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Erro ao processar mapeamentos de banco: {str(e)}")
    
    def _matches_input_command(self, input_command: Dict, mapping) -> bool:
        """Verifica se um comando de entrada corresponde a um mapeamento"""
        try:
            # Verifica tipo de comando
            if mapping.input_type != input_command['type']:
                return False
            
            # Verifica canal
            if mapping.input_channel != input_command.get('channel', 0):
                return False
            
            # Verifica controle específico
            if mapping.input_type == 'control_change':
                if mapping.input_control != input_command.get('cc'):
                    return False
            elif mapping.input_type in ['note_on', 'note_off']:
                if mapping.input_control != input_command.get('note'):
                    return False
            elif mapping.input_type == 'program_change':
                if mapping.input_control != input_command.get('program'):
                    return False
            
            # Verifica valor específico se definido
            if mapping.input_value is not None:
                if mapping.input_type == 'control_change':
                    if mapping.input_value != input_command.get('value'):
                        return False
                elif mapping.input_type in ['note_on', 'note_off']:
                    if mapping.input_value != input_command.get('velocity'):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar correspondência de comando: {str(e)}")
            return False
    
    def _execute_output_command(self, mapping):
        """Executa comando de saída baseado no mapeamento"""
        try:
            if mapping.output_type == 'control_change':
                self._send_cc_to_device(
                    mapping.output_channel,
                    mapping.output_control,
                    mapping.output_value,
                    mapping.output_device
                )
            elif mapping.output_type == 'program_change':
                self._send_pc_to_device(
                    mapping.output_channel,
                    mapping.output_program,
                    mapping.output_device
                )
            elif mapping.output_type == 'note_on':
                self._send_note_on_to_device(
                    mapping.output_channel,
                    mapping.output_control,
                    mapping.output_value,
                    mapping.output_device
                )
            elif mapping.output_type == 'note_off':
                self._send_note_off_to_device(
                    mapping.output_channel,
                    mapping.output_control,
                    mapping.output_device
                )
            
            self.logger.info(f"Comando de saída executado: {mapping.output_type} para {mapping.output_device}")
            
        except Exception as e:
            self.logger.error(f"Erro ao executar comando de saída: {str(e)}")
    
    def disconnect(self):
        """Desconecta todos os dispositivos e executa cleanup completo"""
        try:
            # Para monitoramento
            self.stop_midi_input_monitoring()
            
            # Desconecta controladores específicos
            if self.zoom_g3x:
                self.zoom_g3x.disconnect()
            
            if self.chocolate:
                self.chocolate.disconnect()
            
            # Executa cleanup completo
            self.cleanup()
            
            self._connected = False
            self.device_status = {
                'zoom_g3x': {'connected': False, 'port': None, 'last_pc': None},
                'chocolate': {'connected': False, 'port': None, 'last_pc': None}
            }
            
            self.logger.info("Todos os dispositivos MIDI desconectados e cleanup executado")
            
        except Exception as e:
            self.logger.error(f"Erro ao desconectar dispositivos: {str(e)}")
    
    def send_sysex(self, data: list, device_name: str = None, output_channel: int = 0) -> bool:
        """Envia mensagem SysEx para o dispositivo de saída ou nome especificado, aceita canal de saída para referência/log."""
        try:
            output_device = device_name or self.midi_config.get('output_device')
            if not output_device:
                self.logger.error("Nenhum dispositivo de saída configurado")
                return False
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == output_device or device['real_name'] == output_device:
                    real_device_name = device['real_name']
                    break
            if not real_device_name:
                self.logger.error(f"Dispositivo {output_device} não encontrado")
                return False
            import mido
            sysex_data = [0xF0] + data + [0xF7]
            # Canal de saída não é usado diretamente em SysEx, mas pode ser incluído no log
            msg = mido.Message('sysex', data=sysex_data[1:-1])
            with mido.open_output(real_device_name) as port:
                port.send(msg)
            self.logger.info(f"SysEx enviado para {real_device_name} (canal de saída {output_channel}): {sysex_data}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar SysEx: {str(e)}")
            return False

    def send_sysex_patch(self, patch_number: int, device_name: str = None) -> bool:
        """Envia comando SysEx para selecionar patch específico"""
        try:
            output_device = device_name or self.midi_config.get('output_device')
            if not output_device:
                self.logger.error("Nenhum dispositivo de saída configurado")
                return False
            
            # Se for Zoom G3X, usa o controlador específico
            if 'zoom' in output_device.lower() or 'g3x' in output_device.lower():
                if self.zoom_g3x and hasattr(self.zoom_g3x, 'send_sysex_patch'):
                    return self.zoom_g3x.send_sysex_patch(patch_number)
                else:
                    self.logger.error("Controlador Zoom G3X não está disponível")
                    return False
            
            # Para outros dispositivos, usa comando SysEx genérico
            # Comando SysEx para selecionar patch: F0 52 00 5A 09 00 00 <patch> F7
            sysex_data = [0x52, 0x00, 0x5A, 0x09, 0x00, 0x00, patch_number]
            return self.send_sysex(sysex_data, output_device)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar SysEx patch selection: {str(e)}")
            return False

    def send_patch_select(self, ff: int, ss: int, device_name: str = None) -> bool:
        """Envia comando para selecionar patch (B0 20 ff C0 ss)"""
        try:
            output_device = device_name or self.midi_config.get('output_device')
            if not output_device:
                self.logger.error("Nenhum dispositivo de saída configurado")
                return False
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == output_device or device['real_name'] == output_device:
                    real_device_name = device['real_name']
                    break
            if not real_device_name:
                self.logger.error(f"Dispositivo {output_device} não encontrado")
                return False
            import mido
            # B0 20 ff
            msg1 = mido.Message('control_change', channel=0, control=32, value=ff)
            # C0 ss
            msg2 = mido.Message('program_change', channel=0, program=ss)
            with mido.open_output(real_device_name) as port:
                port.send(msg1)
                port.send(msg2)
            self.logger.info(f"Patch select enviado para {real_device_name}: ff={ff}, ss={ss}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar Patch Select: {str(e)}")
            return False

    def get_devices_status_detailed(self) -> list:
        """Retorna status detalhado dos dispositivos para o modo palco"""
        try:
            devices = []
            
            # Zoom G3X
            zoom_status = {
                'name': 'Zoom G3X',
                'type': 'zoom_g3x',
                'connected': self.device_status['zoom_g3x']['connected'],
                'port': self.device_status['zoom_g3x']['port'],
                'last_pc': self.device_status['zoom_g3x'].get('last_pc'),
                'status_details': 'Dispositivo detectado mas não conectado'
            }
            
            # Verifica se o Zoom G3X está realmente conectado
            if self.zoom_g3x and hasattr(self.zoom_g3x, 'connected'):
                zoom_status['connected'] = self.zoom_g3x.connected
                if self.zoom_g3x.connected:
                    zoom_status['status_details'] = 'Conectado e funcionando'
                else:
                    zoom_status['status_details'] = 'Porta detectada mas conexão falhou - pode precisar de alimentação externa'
            else:
                zoom_status['status_details'] = 'Controlador não inicializado'
            
            # Verifica se a porta do Zoom G3X está disponível
            try:
                import mido
                available_outputs = mido.get_output_names()
                zoom_port = self.device_status['zoom_g3x']['port']
                if zoom_port and zoom_port in available_outputs:
                    zoom_status['port_available'] = True
                    zoom_status['status_details'] += ' - Porta disponível no sistema'
                else:
                    zoom_status['port_available'] = False
                    zoom_status['status_details'] += ' - Porta não encontrada'
            except:
                zoom_status['port_available'] = False
            
            devices.append(zoom_status)
            
            # Chocolate (dispositivo de entrada)
            chocolate_status = {
                'name': 'Chocolate',
                'type': 'chocolate',
                'connected': self.device_status['chocolate']['connected'],
                'port': self.device_status['chocolate']['port'],
                'last_pc': self.device_status['chocolate'].get('last_pc'),
                'status_details': 'Dispositivo detectado mas não conectado'
            }
            
            # Para o Chocolate, se está detectado via USB, considera conectado
            if self.device_status['chocolate']['connected']:
                chocolate_status['connected'] = True
                chocolate_status['status_details'] = 'Conectado e funcionando - Dispositivo de entrada detectado via USB'
            else:
                chocolate_status['connected'] = False
                chocolate_status['status_details'] = 'Dispositivo de entrada não detectado via USB'
            
            # Verifica se a porta do Chocolate está disponível nas entradas
            try:
                import mido
                available_inputs = mido.get_input_names()
                chocolate_port = self.device_status['chocolate']['port']
                if chocolate_port and chocolate_port in available_inputs:
                    chocolate_status['port_available'] = True
                    chocolate_status['status_details'] += ' - Porta disponível no sistema'
                else:
                    chocolate_status['port_available'] = False
                    chocolate_status['status_details'] += ' - Porta não encontrada'
            except:
                chocolate_status['port_available'] = False
            
            devices.append(chocolate_status)
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status detalhado dos dispositivos: {str(e)}")
            return []
    
    def force_reconnect_chocolate(self) -> bool:
        """Força reconexão do Chocolate"""
        try:
            self.logger.info("Forçando reconexão do Chocolate...")
            
            # Desconecta se estiver conectado
            if self.chocolate:
                self.chocolate.disconnect()
                self.device_status['chocolate']['connected'] = False
                self.device_status['chocolate']['port'] = None
            
            # Reinicializa o Chocolate
            self._init_chocolate()
            
            # Verifica se conseguiu conectar
            if self.device_status['chocolate']['connected']:
                self.logger.info("Chocolate reconectado com sucesso")
                return True
            else:
                self.logger.warning("Falha ao reconectar Chocolate")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao forçar reconexão do Chocolate: {str(e)}")
            return False

    def force_reconnect_zoom_g3x(self) -> bool:
        """Força reconexão do Zoom G3X"""
        try:
            self.logger.info("Forçando reconexão do Zoom G3X...")
            
            # Desconecta se estiver conectado
            if self.zoom_g3x:
                self.zoom_g3x.disconnect()
                self.device_status['zoom_g3x']['connected'] = False
                self.device_status['zoom_g3x']['port'] = None
            
            # Reinicializa o Zoom G3X
            self._init_zoom_g3x()
            
            # Verifica se conseguiu conectar
            if self.device_status['zoom_g3x']['connected']:
                self.logger.info("Zoom G3X reconectado com sucesso")
                return True
            else:
                self.logger.warning("Falha ao reconectar Zoom G3X")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao forçar reconexão do Zoom G3X: {str(e)}")
            return False

    def _send_pc_to_device(self, channel: int, program: int, device_name: str) -> bool:
        """Envia mensagem Program Change para um dispositivo específico"""
        try:
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == device_name or device['real_name'] == device_name:
                    real_device_name = device['real_name']
                    break
            
            if not real_device_name:
                self.logger.error(f"Dispositivo {device_name} não encontrado")
                return False
            
            # Tenta enviar via controlador específico primeiro
            if 'zoom' in device_name.lower() or 'g3x' in device_name.lower():
                if self.zoom_g3x and self.device_status['zoom_g3x']['connected']:
                    try:
                        result = self.zoom_g3x.send_pc(channel, program)
                        if result:
                            self.device_status['zoom_g3x']['last_pc'] = program
                            return result
                    except Exception as e:
                        self.logger.warning(f"Erro ao enviar via controlador Zoom G3X: {str(e)}, tentando via mido")
            elif 'chocolate' in device_name.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    try:
                        result = self.chocolate.send_pc(channel, program)
                        if result:
                            self.device_status['chocolate']['last_pc'] = program
                            return result
                    except Exception as e:
                        self.logger.warning(f"Erro ao enviar via controlador Chocolate: {str(e)}, tentando via mido")
            
            # Sempre tenta enviar diretamente via mido como fallback
            self.logger.info(f"Tentando enviar PC via mido para {real_device_name}")
            result = self._send_midi_via_mido('program_change', real_device_name, channel=channel, program=program)
            
            # Atualiza last_pc se sucesso
            if result:
                if 'zoom' in device_name.lower() or 'g3x' in device_name.lower():
                    self.device_status['zoom_g3x']['last_pc'] = program
                elif 'chocolate' in device_name.lower():
                    self.device_status['chocolate']['last_pc'] = program
                self.logger.info(f"PC {program} enviado com sucesso para {real_device_name}")
            else:
                self.logger.error(f"Falha ao enviar PC {program} para {real_device_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar PC para dispositivo {device_name}: {str(e)}")
            return False

    def activate_patch(self, patch_data: Dict) -> bool:
        """Ativa um patch enviando para o dispositivo e marcando como ativo"""
        try:
            self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] Iniciando ativação do patch: {patch_data.get('name')}")
            
            # Envia o patch para o dispositivo
            success = self.send_patch(patch_data)
            
            if success:
                # Marca como último patch ativado
                self._last_patch_activated = patch_data
                self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] Patch '{patch_data.get('name')}' ativado e marcado como ativo")
                self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] _last_patch_activated definido: {self._last_patch_activated.get('name') if self._last_patch_activated else 'None'}")
                # Salva em disco
                try:
                    with open(os.path.join('data', 'active_patch.json'), 'w', encoding='utf-8') as f:
                        json.dump(patch_data, f, ensure_ascii=False, indent=2)
                    self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] Patch ativo salvo em data/active_patch.json")
                except Exception as e:
                    self.logger.error(f"🎹 [ACTIVATE_PATCH_DEBUG] Erro ao salvar patch ativo em disco: {str(e)}")
            else:
                self.logger.error(f"🎹 [ACTIVATE_PATCH_DEBUG] Falha ao enviar patch para dispositivo")
            
            return success
        except Exception as e:
            self.logger.error(f"🎹 [ACTIVATE_PATCH_DEBUG] Erro ao ativar patch: {str(e)}")
            return False

    def get_last_patch_activated(self):
        """Retorna o último patch ativado, da memória ou do disco"""
        if hasattr(self, '_last_patch_activated') and self._last_patch_activated:
            return self._last_patch_activated
        # Tenta ler do disco
        try:
            path = os.path.join('data', 'active_patch.json')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    patch = json.load(f)
                    self._last_patch_activated = patch
                    return patch
        except Exception as e:
            self.logger.error(f"🎹 [ACTIVATE_PATCH_DEBUG] Erro ao ler patch ativo do disco: {str(e)}")
        return None

    def atualizar_patches_chocolate(self, patches):
        self.chocolate_patches = [p for p in patches if p.get('input_device') == 'Chocolate MIDI']

    def send_patch_select(self, ff: int, ss: int, device_name: str = None) -> bool:
        """Envia comando para selecionar patch (B0 20 ff C0 ss)"""
        try:
            output_device = device_name or self.midi_config.get('output_device')
            if not output_device:
                self.logger.error("Nenhum dispositivo de saída configurado")
                return False
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == output_device or device['real_name'] == output_device:
                    real_device_name = device['real_name']
                    break
            if not real_device_name:
                self.logger.error(f"Dispositivo {output_device} não encontrado")
                return False
            import mido
            # B0 20 ff
            msg1 = mido.Message('control_change', channel=0, control=32, value=ff)
            # C0 ss
            msg2 = mido.Message('program_change', channel=0, program=ss)
            with mido.open_output(real_device_name) as port:
                port.send(msg1)
                port.send(msg2)
            self.logger.info(f"Patch select enviado para {real_device_name}: ff={ff}, ss={ss}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar Patch Select: {str(e)}")
            return False

    def get_devices_status_detailed(self) -> list:
        """Retorna status detalhado dos dispositivos para o modo palco"""
        try:
            devices = []
            
            # Zoom G3X
            zoom_status = {
                'name': 'Zoom G3X',
                'type': 'zoom_g3x',
                'connected': self.device_status['zoom_g3x']['connected'],
                'port': self.device_status['zoom_g3x']['port'],
                'last_pc': self.device_status['zoom_g3x'].get('last_pc'),
                'status_details': 'Dispositivo detectado mas não conectado'
            }
            
            # Verifica se o Zoom G3X está realmente conectado
            if self.zoom_g3x and hasattr(self.zoom_g3x, 'connected'):
                zoom_status['connected'] = self.zoom_g3x.connected
                if self.zoom_g3x.connected:
                    zoom_status['status_details'] = 'Conectado e funcionando'
                else:
                    zoom_status['status_details'] = 'Porta detectada mas conexão falhou - pode precisar de alimentação externa'
            else:
                zoom_status['status_details'] = 'Controlador não inicializado'
            
            # Verifica se a porta do Zoom G3X está disponível
            try:
                import mido
                available_outputs = mido.get_output_names()
                zoom_port = self.device_status['zoom_g3x']['port']
                if zoom_port and zoom_port in available_outputs:
                    zoom_status['port_available'] = True
                    zoom_status['status_details'] += ' - Porta disponível no sistema'
                else:
                    zoom_status['port_available'] = False
                    zoom_status['status_details'] += ' - Porta não encontrada'
            except:
                zoom_status['port_available'] = False
            
            devices.append(zoom_status)
            
            # Chocolate (dispositivo de entrada)
            chocolate_status = {
                'name': 'Chocolate',
                'type': 'chocolate',
                'connected': self.device_status['chocolate']['connected'],
                'port': self.device_status['chocolate']['port'],
                'last_pc': self.device_status['chocolate'].get('last_pc'),
                'status_details': 'Dispositivo detectado mas não conectado'
            }
            
            # Para o Chocolate, se está detectado via USB, considera conectado
            if self.device_status['chocolate']['connected']:
                chocolate_status['connected'] = True
                chocolate_status['status_details'] = 'Conectado e funcionando - Dispositivo de entrada detectado via USB'
            else:
                chocolate_status['connected'] = False
                chocolate_status['status_details'] = 'Dispositivo de entrada não detectado via USB'
            
            # Verifica se a porta do Chocolate está disponível nas entradas
            try:
                import mido
                available_inputs = mido.get_input_names()
                chocolate_port = self.device_status['chocolate']['port']
                if chocolate_port and chocolate_port in available_inputs:
                    chocolate_status['port_available'] = True
                    chocolate_status['status_details'] += ' - Porta disponível no sistema'
                else:
                    chocolate_status['port_available'] = False
                    chocolate_status['status_details'] += ' - Porta não encontrada'
            except:
                chocolate_status['port_available'] = False
            
            devices.append(chocolate_status)
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Erro ao obter status detalhado dos dispositivos: {str(e)}")
            return []
    
    def force_reconnect_chocolate(self) -> bool:
        """Força reconexão do Chocolate"""
        try:
            self.logger.info("Forçando reconexão do Chocolate...")
            
            # Desconecta se estiver conectado
            if self.chocolate:
                self.chocolate.disconnect()
                self.device_status['chocolate']['connected'] = False
                self.device_status['chocolate']['port'] = None
            
            # Reinicializa o Chocolate
            self._init_chocolate()
            
            # Verifica se conseguiu conectar
            if self.device_status['chocolate']['connected']:
                self.logger.info("Chocolate reconectado com sucesso")
                return True
            else:
                self.logger.warning("Falha ao reconectar Chocolate")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao forçar reconexão do Chocolate: {str(e)}")
            return False

    def force_reconnect_zoom_g3x(self) -> bool:
        """Força reconexão do Zoom G3X"""
        try:
            self.logger.info("Forçando reconexão do Zoom G3X...")
            
            # Desconecta se estiver conectado
            if self.zoom_g3x:
                self.zoom_g3x.disconnect()
                self.device_status['zoom_g3x']['connected'] = False
                self.device_status['zoom_g3x']['port'] = None
            
            # Reinicializa o Zoom G3X
            self._init_zoom_g3x()
            
            # Verifica se conseguiu conectar
            if self.device_status['zoom_g3x']['connected']:
                self.logger.info("Zoom G3X reconectado com sucesso")
                return True
            else:
                self.logger.warning("Falha ao reconectar Zoom G3X")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao forçar reconexão do Zoom G3X: {str(e)}")
            return False

    def _send_pc_to_device(self, channel: int, program: int, device_name: str) -> bool:
        """Envia mensagem Program Change para um dispositivo específico"""
        try:
            # Encontra o nome real do dispositivo
            real_device_name = None
            for device in self.midi_config.get('devices', {}).get('outputs', []):
                if device['name'] == device_name or device['real_name'] == device_name:
                    real_device_name = device['real_name']
                    break
            
            if not real_device_name:
                self.logger.error(f"Dispositivo {device_name} não encontrado")
                return False
            
            # Tenta enviar via controlador específico primeiro
            if 'zoom' in device_name.lower() or 'g3x' in device_name.lower():
                if self.zoom_g3x and self.device_status['zoom_g3x']['connected']:
                    try:
                        result = self.zoom_g3x.send_pc(channel, program)
                        if result:
                            self.device_status['zoom_g3x']['last_pc'] = program
                            return result
                    except Exception as e:
                        self.logger.warning(f"Erro ao enviar via controlador Zoom G3X: {str(e)}, tentando via mido")
            elif 'chocolate' in device_name.lower():
                if self.chocolate and self.device_status['chocolate']['connected']:
                    try:
                        result = self.chocolate.send_pc(channel, program)
                        if result:
                            self.device_status['chocolate']['last_pc'] = program
                            return result
                    except Exception as e:
                        self.logger.warning(f"Erro ao enviar via controlador Chocolate: {str(e)}, tentando via mido")
            
            # Sempre tenta enviar diretamente via mido como fallback
            self.logger.info(f"Tentando enviar PC via mido para {real_device_name}")
            result = self._send_midi_via_mido('program_change', real_device_name, channel=channel, program=program)
            
            # Atualiza last_pc se sucesso
            if result:
                if 'zoom' in device_name.lower() or 'g3x' in device_name.lower():
                    self.device_status['zoom_g3x']['last_pc'] = program
                elif 'chocolate' in device_name.lower():
                    self.device_status['chocolate']['last_pc'] = program
                self.logger.info(f"PC {program} enviado com sucesso para {real_device_name}")
            else:
                self.logger.error(f"Falha ao enviar PC {program} para {real_device_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar PC para dispositivo {device_name}: {str(e)}")
            return False

    def activate_patch(self, patch_data: Dict) -> bool:
        """Ativa um patch enviando para o dispositivo e marcando como ativo"""
        try:
            self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] Iniciando ativação do patch: {patch_data.get('name')}")
            
            # Envia o patch para o dispositivo
            success = self.send_patch(patch_data)
            
            if success:
                # Marca como último patch ativado
                self._last_patch_activated = patch_data
                self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] Patch '{patch_data.get('name')}' ativado e marcado como ativo")
                self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] _last_patch_activated definido: {self._last_patch_activated.get('name') if self._last_patch_activated else 'None'}")
                # Salva em disco
                try:
                    with open(os.path.join('data', 'active_patch.json'), 'w', encoding='utf-8') as f:
                        json.dump(patch_data, f, ensure_ascii=False, indent=2)
                    self.logger.info(f"🎹 [ACTIVATE_PATCH_DEBUG] Patch ativo salvo em data/active_patch.json")
                except Exception as e:
                    self.logger.error(f"🎹 [ACTIVATE_PATCH_DEBUG] Erro ao salvar patch ativo em disco: {str(e)}")
            else:
                self.logger.error(f"🎹 [ACTIVATE_PATCH_DEBUG] Falha ao enviar patch para dispositivo")
            
            return success
        except Exception as e:
            self.logger.error(f"🎹 [ACTIVATE_PATCH_DEBUG] Erro ao ativar patch: {str(e)}")
            return False
 