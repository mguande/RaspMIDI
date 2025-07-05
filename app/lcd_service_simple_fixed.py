#!/usr/bin/env python3
"""
Serviço LCD simplificado e corrigido para RaspMIDI
Versão que resolve o problema de piscadas
"""

import os
import sys
import time
import json
import signal
import logging
import struct
import requests
from PIL import Image, ImageDraw, ImageFont
import hashlib

# Configurações do LCD
LCD_WIDTH = 480
LCD_HEIGHT = 320
FRAMEBUFFER_DEVICE = "/dev/fb1"

class LCDServiceSimpleFixed:
    def __init__(self):
        self.running = False
        self.current_bank = "A"
        self.current_patch = "001"
        self.zoom_bank = "A"
        self.zoom_patch = "001"
        self.chocolate_patch = "001"
        self.status = "Inicializando..."
        self.bank_name = "Inicializando..."
        self.last_commands = []
        self.api_base_url = "http://localhost:5000/api"
        self.chocolate_connected = False
        self.zoom_connected = False
        self.patch_activated = False  # Flag para indicar que um patch foi ativado
        self.last_screen_hash = None  # Para evitar flicker
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/matheus/RaspMIDI/logs/lcd_service.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Inicializar framebuffer
        self.init_framebuffer()
        
        # Carregar fontes
        self.load_fonts()
        
        # Configurar sinais para graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def init_framebuffer(self):
        """Inicializa o framebuffer"""
        try:
            self.fb = open(FRAMEBUFFER_DEVICE, 'wb')
            self.logger.info(f"Framebuffer {FRAMEBUFFER_DEVICE} aberto")
        except Exception as e:
            self.logger.error(f"Erro ao abrir framebuffer: {e}")
            raise
    
    def load_fonts(self):
        """Carrega as fontes para o display"""
        try:
            # Usar fonte padrão do sistema
            self.font_large = ImageFont.load_default()
            self.logger.info("Fontes carregadas (padrão)")
        except Exception as e:
            self.logger.error(f"Erro ao carregar fontes: {e}")
            self.font_large = ImageFont.load_default()
    
    def rgb888_to_rgb565(self, r, g, b):
        """Converte RGB888 para RGB565"""
        r = (r >> 3) & 0x1F
        g = (g >> 2) & 0x3F
        b = (b >> 3) & 0x1F
        return (r << 11) | (g << 5) | b
    
    def update_framebuffer(self, image):
        """Atualiza o framebuffer com a imagem"""
        try:
            # Converter imagem para RGB565
            rgb_image = image.convert('RGB')
            pixels = rgb_image.load()
            
            # Preparar dados do framebuffer
            fb_data = bytearray()
            
            for y in range(LCD_HEIGHT):
                for x in range(LCD_WIDTH):
                    r, g, b = pixels[x, y]
                    rgb565 = self.rgb888_to_rgb565(r, g, b)
                    fb_data.extend(struct.pack('<H', rgb565))
            
            # Escrever no framebuffer
            self.fb.seek(0)
            self.fb.write(fb_data)
            self.fb.flush()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar framebuffer: {e}")
    
    def get_screen_hash(self, image):
        """Gera um hash da imagem para comparar mudanças"""
        return hashlib.md5(image.tobytes()).hexdigest()
    
    def show_connecting_screen(self, force=False):
        """Mostra tela estática de aguardando conexão com ícone de alerta, só atualiza se mudar ou se force=True"""
        try:
            # Criar imagem com fundo preto
            image = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Desenhar ícone de alerta grande (triângulo)
            center_x = LCD_WIDTH // 2
            center_y = LCD_HEIGHT // 2 - 60
            
            # Triângulo de alerta grande (amarelo)
            triangle_size = 60
            triangle_points = [
                (center_x, center_y - triangle_size),  # Topo
                (center_x - triangle_size, center_y + triangle_size),  # Esquerda
                (center_x + triangle_size, center_y + triangle_size)   # Direita
            ]
            draw.polygon(triangle_points, fill=(255, 255, 0))
            
            # Ponto de exclamação no centro do triângulo
            exclamation_width = 8
            exclamation_height = 40
            exclamation_x = center_x - exclamation_width // 2
            exclamation_y = center_y - exclamation_height // 2
            
            # Ponto superior
            draw.rectangle([exclamation_x, exclamation_y, 
                           exclamation_x + exclamation_width, exclamation_y + 20], 
                          fill=(0, 0, 0))
            # Ponto inferior
            draw.rectangle([exclamation_x, exclamation_y + 30, 
                           exclamation_x + exclamation_width, exclamation_y + exclamation_height], 
                          fill=(0, 0, 0))
            
            # Texto "AGUARDANDO CONEXÃO" grande e centralizado
            text = "AGUARDANDO CONEXÃO"
            char_width = 15
            text_width = len(text) * char_width
            text_x = center_x - text_width // 2
            text_y = center_y + triangle_size + 30
            
            draw.text((text_x, text_y), text, fill=(255, 255, 0), font=self.font_large)
            
            # Status do dispositivo de entrada
            input_device = "Chocolate MIDI In"
            input_status = "CONECTADO" if self.chocolate_connected else "DESCONECTADO"
            input_color = (0, 255, 0) if self.chocolate_connected else (255, 0, 0)
            
            input_text = f"ENTRADA: {input_device} - {input_status}"
            input_x = 20
            input_y = text_y + 50
            
            draw.text((input_x, input_y), input_text, fill=input_color, font=self.font_large)
            
            # Status do dispositivo de saída
            output_device = "Zoom G3X MIDI Out"
            output_status = "CONECTADO" if self.zoom_connected else "DESCONECTADO"
            output_color = (0, 255, 0) if self.zoom_connected else (255, 0, 0)
            
            output_text = f"SAÍDA: {output_device} - {output_status}"
            output_x = 20
            output_y = input_y + 40
            
            draw.text((output_x, output_y), output_text, fill=output_color, font=self.font_large)
            
            # Atualizar framebuffer só se mudou
            screen_hash = self.get_screen_hash(image)
            if force or screen_hash != self.last_screen_hash:
                self.update_framebuffer(image)
                self.last_screen_hash = screen_hash
            
        except Exception as e:
            self.logger.error(f"Erro na tela de conexão: {e}")
    
    def update_display(self, force=False):
        """Atualiza o display com as informações atuais, só se mudar ou se force=True"""
        try:
            # Criar imagem
            image = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Desenhar título
            title = "RaspMIDI"
            draw.text((LCD_WIDTH//2 - 50, 20), title, fill=(255, 215, 0), font=self.font_large)
            
            # Desenhar nome do banco
            bank_text = f"BANCO: {self.bank_name}"
            draw.text((20, 70), bank_text, fill=(255, 255, 255), font=self.font_large)
            
            # Desenhar informações do patch atual
            y_pos = 120
            
            # Patch Chocolate
            chocolate_text = f"CHOCOLATE: {self.chocolate_patch}"
            draw.text((20, y_pos), chocolate_text, fill=(255, 215, 0), font=self.font_large)
            y_pos += 40
            
            # Banco Zoom
            zoom_bank_text = f"ZOOM BANCO: {self.zoom_bank}"
            draw.text((20, y_pos), zoom_bank_text, fill=(255, 215, 0), font=self.font_large)
            y_pos += 40
            
            # Patch Zoom
            zoom_patch_text = f"ZOOM PATCH: {self.zoom_patch}"
            draw.text((20, y_pos), zoom_patch_text, fill=(255, 215, 0), font=self.font_large)
            y_pos += 50
            
            # Status
            status_text = f"STATUS: {self.status}"
            draw.text((20, y_pos), status_text, fill=(0, 255, 0), font=self.font_large)
            
            # Atualizar framebuffer só se mudou
            screen_hash = self.get_screen_hash(image)
            if force or screen_hash != self.last_screen_hash:
                self.update_framebuffer(image)
                self.last_screen_hash = screen_hash
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar display: {e}")
    
    def check_api_health(self):
        """Verifica se a API está funcionando"""
        try:
            response = requests.get(f"{self.api_base_url}/midi/devices/list", timeout=2)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Erro ao verificar API: {e}")
            return False
    
    def connect_devices(self):
        """Conecta aos dispositivos configurados no sistema"""
        try:
            self.logger.info("Conectando aos dispositivos MIDI...")
            
            # 1. Ativar monitoramento MIDI
            try:
                response = requests.post(
                    f"{self.api_base_url}/midi/monitor/start",
                    headers={"Content-Type": "application/json"},
                    json={},
                    timeout=2
                )
                if response.status_code == 200:
                    self.logger.info("Monitoramento MIDI ativado")
                else:
                    self.logger.error(f"Erro ao ativar monitoramento: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Erro ao ativar monitoramento MIDI: {e}")
            
            # 2. Reconectar Chocolate
            try:
                response = requests.post(
                    f"{self.api_base_url}/midi/devices/chocolate/reconnect",
                    headers={"Content-Type": "application/json"},
                    json={},
                    timeout=2
                )
                if response.status_code == 200:
                    self.logger.info("Tentativa de reconexão do Chocolate realizada")
                else:
                    self.logger.error(f"Erro ao reconectar Chocolate: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Erro ao reconectar Chocolate: {e}")
            
            # 3. Reconectar Zoom
            try:
                response = requests.post(
                    f"{self.api_base_url}/midi/devices/zoom_g3x/reconnect",
                    headers={"Content-Type": "application/json"},
                    json={},
                    timeout=2
                )
                if response.status_code == 200:
                    self.logger.info("Tentativa de reconexão da Zoom realizada")
                else:
                    self.logger.error(f"Erro ao reconectar Zoom: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Erro ao reconectar Zoom: {e}")
            
            # 4. Verificar status dos dispositivos
            self.check_device_status()
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar dispositivos: {e}")
    
    def check_device_status(self):
        """Verifica status dos dispositivos e atualiza variáveis"""
        try:
            response = requests.get(f"{self.api_base_url}/midi/devices/status_detailed", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    devices = data['data']
                    
                    for device in devices:
                        if device.get('type') == 'chocolate':
                            self.chocolate_connected = device.get('connected', False)
                            if not self.chocolate_connected:
                                self.logger.warning("Chocolate não está conectado")
                        elif device.get('type') == 'zoom_g3x':
                            self.zoom_connected = device.get('connected', False)
                            if not self.zoom_connected:
                                self.logger.warning("Zoom não está conectada")
                        
        except Exception as e:
            self.logger.error(f"Erro ao verificar status dos dispositivos: {e}")
    
    def get_midi_commands(self):
        """Obtém comandos MIDI recebidos da API"""
        try:
            response = requests.get(f"{self.api_base_url}/midi/commands/received", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('commands'):
                    return data['commands']
            return []
        except Exception as e:
            self.logger.error(f"Erro ao obter comandos MIDI: {e}")
            return []
    
    def process_midi_command(self, command):
        """Processa comando MIDI igual ao JavaScript da página do palco"""
        try:
            self.logger.info(f"Processando comando MIDI: {command}")
            
            # Se for um Program Change do Chocolate
            if command.get('type') == 'program_change' and command.get('program') is not None:
                program = command['program']
                self.logger.info(f"Program Change detectado: program={program}")
                
                # Atualiza o display do Chocolate
                self.chocolate_patch = f"{program:03d}"
                
                # Busca e ativa o patch correspondente
                self.find_and_activate_patch_by_program(program)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar comando MIDI: {e}")
    
    def find_and_activate_patch_by_program(self, program):
        """Busca e ativa patch por program number (igual ao JavaScript)"""
        try:
            self.logger.info(f"Buscando patch com program {program}...")
            
            # 1. Busca configuração MIDI
            config_response = requests.get(f"{self.api_base_url}/midi/config", timeout=2)
            if config_response.status_code != 200:
                self.logger.error("Erro ao buscar configuração MIDI")
                return
            
            config_data = config_response.json()
            if not config_data.get('success') or not config_data.get('data'):
                self.logger.error("Erro na configuração MIDI")
                return
            
            input_device = config_data['data'].get('input_device')
            self.logger.info(f"Dispositivo de entrada: {input_device}")
            
            # 2. Busca todos os patches
            patches_response = requests.get(f"{self.api_base_url}/patches", timeout=2)
            if patches_response.status_code != 200:
                self.logger.error("Erro ao buscar patches")
                return
            
            patches_data = patches_response.json()
            if not patches_data.get('success') or not patches_data.get('data'):
                self.logger.error("Erro na resposta de patches")
                return
            
            patches = patches_data['data']
            self.logger.info(f"Total de patches: {len(patches)}")
            
            # 3. Filtra patches que usam o dispositivo de entrada configurado
            input_patches = [p for p in patches if p.get('input_device') == input_device]
            self.logger.info(f"Patches com dispositivo {input_device}: {len(input_patches)}")
            
            # 4. Busca patch com input_channel específico
            matching_patches = [p for p in input_patches if p.get('input_channel') == program]
            self.logger.info(f"Patches com input_channel {program}: {len(matching_patches)}")
            
            if matching_patches:
                patch = matching_patches[0]
                self.logger.info(f"Patch encontrado: {patch.get('name')}")
                
                # Ativa o patch
                self.activate_patch(patch)
            else:
                self.logger.warning(f"Nenhum patch encontrado para program {program}")
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar patch por program: {e}")
    
    def activate_patch(self, patch):
        """Ativa um patch (igual ao JavaScript)"""
        try:
            self.logger.info(f"Ativando patch: {patch.get('name')}")
            # Ativa o patch via API
            response = requests.post(
                f"{self.api_base_url}/midi/patch/load",
                json={"patch_id": patch["id"]},
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.logger.info("Patch ativado com sucesso")
                    # Atualiza informações do display
                    self.bank_name = patch.get('name', 'Desconhecido')
                    # Atualiza informações do Chocolate
                    if patch.get('input_device') == 'Chocolate MIDI In' and patch.get('input_channel') is not None:
                        bank_number = int(patch['input_channel'])
                        self.chocolate_patch = f"{bank_number:03d}"
                    # Atualiza informações da Zoom
                    if patch.get('zoom_bank') is not None and patch.get('zoom_patch') is not None:
                        self.zoom_bank = patch.get('zoom_bank_letter', str(patch['zoom_bank']))
                        self.zoom_patch = f"{patch['zoom_patch']:03d}"
                    # Define status estável e marca como ativado
                    self.status = "Sistema ativo"
                    # Só marca como ativado se for realmente novo
                    if not self.patch_activated:
                        self.patch_activated = True
                        self.logger.info("Sistema marcado como ativo - mudando para tela normal")
                else:
                    self.logger.error(f"Erro ao ativar patch: {data.get('error')}")
                    self.status = "Erro ao ativar"
            else:
                self.logger.error(f"Erro HTTP ao ativar patch: {response.status_code}")
                self.status = "Erro HTTP"
        except Exception as e:
            self.logger.error(f"Erro ao ativar patch: {e}")
            self.status = "Erro"
    
    def poll_midi_commands(self):
        """Faz polling dos comandos MIDI (igual ao JavaScript)"""
        try:
            # Verifica se a API está funcionando
            if not self.check_api_health():
                self.status = "API indisponível"
                return
            # Verifica status dos dispositivos
            self.check_device_status()
            # Obtém comandos MIDI
            commands = self.get_midi_commands()
            if commands:
                # Processa apenas comandos realmente novos (timestamp > self.init_timestamp)
                new_commands = [c for c in commands if c.get('timestamp', 0) > self.init_timestamp and c not in self.last_commands]
                for command in new_commands:
                    self.process_midi_command(command)
                    self.last_commands.append(command)
                # Mantém apenas os últimos 10 comandos
                self.last_commands = self.last_commands[-10:]
        except Exception as e:
            self.logger.error(f"Erro no polling MIDI: {e}")
            self.status = "Erro no polling"
    
    def signal_handler(self, signum, frame):
        """Handler para sinais de shutdown"""
        self.logger.info(f"Recebido sinal {signum}, encerrando serviço...")
        self.running = False
    
    def run(self):
        """Executa o serviço principal"""
        self.logger.info("Iniciando serviço LCD simplificado e corrigido...")
        self.running = True
        self.last_screen_hash = None  # Para evitar flicker
        self.patch_activated = False  # Garante que sempre inicia como False
        self.init_timestamp = 0  # Timestamp de referência para comandos novos
        try:
            # Aguardar um pouco para a API inicializar
            time.sleep(2)
            # Verificar se a API está funcionando
            if not self.check_api_health():
                self.logger.error("API não está funcionando. Saindo...")
                return
            # Conectar aos dispositivos uma vez
            self.connect_devices()
            time.sleep(3)
            self.check_device_status()
            # Limpar buffer de comandos recebidos na inicialização e registrar maior timestamp
            initial_commands = self.get_midi_commands() or []
            self.last_commands = initial_commands
            if initial_commands:
                self.init_timestamp = max(cmd.get('timestamp', 0) for cmd in initial_commands)
            else:
                self.init_timestamp = time.time()
            # Mostrar tela de conexão inicial
            self.show_connecting_screen(force=True)
            self.logger.info("Tela de conexão exibida - aguardando comando MIDI...")
            while self.running:
                try:
                    self.poll_midi_commands()
                    if not self.patch_activated:
                        self.show_connecting_screen()
                    else:
                        self.update_display()
                    time.sleep(1)  # Reduzido para 1 segundo
                except Exception as e:
                    self.logger.error(f"Erro no loop principal: {e}")
                    time.sleep(1)
        except Exception as e:
            self.logger.error(f"Erro fatal no serviço: {e}")
            time.sleep(5)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpeza ao encerrar"""
        try:
            # Fechar framebuffer
            if hasattr(self, 'fb'):
                self.fb.close()
            
            self.logger.info("Serviço LCD simplificado encerrado")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")

def main():
    """Função principal"""
    service = LCDServiceSimpleFixed()
    service.run()

if __name__ == "__main__":
    main() 