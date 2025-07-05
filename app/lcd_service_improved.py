#!/usr/bin/env python3
"""
Serviço LCD melhorado para RaspMIDI
Replica a lógica da página do palco - faz polling na API e processa comandos MIDI
"""

import os
import sys
import time
import json
import threading
import signal
import logging
import struct
import requests
import random
import math
from PIL import Image, ImageDraw, ImageFont

# Configurações do LCD
LCD_WIDTH = 480
LCD_HEIGHT = 320
FRAMEBUFFER_DEVICE = "/dev/fb1"

# Configurações de cores (RGB565)
COLORS = {
    'background': 0x0000,      # Preto
    'text': 0xFFE0,            # Amarelo
    'accent': 0xFFFF,          # Branco
    'error': 0xF800,           # Vermelho
    'success': 0x07E0,         # Verde
    'gold': 0xFFA0,            # Dourado
}

class LCDServiceImproved:
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
        self.animation_frame = 0
        self.last_animation_time = 0
        self.system_active = False  # Controla se o sistema está funcionando
        self.last_display_data = {}  # Para controlar mudanças no display
        self.patch_activated = False  # Flag para indicar que um patch foi ativado
        
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
    
    def update_display(self):
        """Atualiza o display com as informações atuais"""
        try:
            # Se não recebeu comando ainda, não atualiza display normal
            if not self.patch_activated:
                return
                
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
            
            # Atualizar framebuffer
            self.update_framebuffer(image)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar display: {e}")
    
    def show_startup_screen(self):
        """Mostra tela de inicialização"""
        try:
            image = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Logo/título
            title = "RaspMIDI"
            draw.text((LCD_WIDTH//2 - 50, 120), title, fill=(255, 215, 0), font=self.font_large)
            
            # Status de inicialização
            status = "Inicializando..."
            draw.text((LCD_WIDTH//2 - 60, 200), status, fill=(255, 255, 255), font=self.font_large)
            
            self.update_framebuffer(image)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar tela de inicialização: {e}")
    
    def show_error_screen(self, error_msg):
        """Mostra tela de erro"""
        try:
            image = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            error_title = "ERRO"
            draw.text((LCD_WIDTH//2 - 30, 120), error_title, fill=(255, 0, 0), font=self.font_large)
            
            draw.text((20, 200), error_msg, fill=(255, 0, 0), font=self.font_large)
            
            self.update_framebuffer(image)
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar tela de erro: {e}")
    
    def show_connecting_screen(self):
        """Mostra tela estática de aguardando conexão com ícone de alerta"""
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
            
            # Atualizar framebuffer
            self.update_framebuffer(image)
            
        except Exception as e:
            self.logger.error(f"Erro na tela de conexão: {e}")
    
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
                    
                    # Atualiza status baseado na conexão (só se sistema não estiver ativo)
                    if not self.system_active:
                        if not self.chocolate_connected and not self.zoom_connected:
                            self.status = "Problema de conexão"
                            self.bank_name = "Dispositivos desconectados"
                        elif not self.chocolate_connected:
                            self.status = "Chocolate desconectado"
                            self.bank_name = "Aguardando Chocolate"
                        elif not self.zoom_connected:
                            self.status = "Zoom desconectada"
                            self.bank_name = "Aguardando Zoom"
                        else:
                            self.status = "Dispositivos conectados"
                            self.bank_name = "Aguardando Comando"
                        
        except Exception as e:
            self.logger.error(f"Erro ao verificar status dos dispositivos: {e}")
            self.status = "Erro de conexão"
            self.bank_name = "Erro no sistema"
    
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
    
    def get_active_patch_info(self):
        """Obtém informações do patch ativo"""
        try:
            # Busca patches para encontrar o ativo
            response = requests.get(f"{self.api_base_url}/patches", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    patches = data['data']
                    # Busca patch ativo (pode ser o último ativado)
                    for patch in patches:
                        if patch.get('active', False):
                            return patch
            return None
        except Exception as e:
            self.logger.error(f"Erro ao obter patch ativo: {e}")
            return None
    
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
                # Só reseta se o sistema não estiver ativo
                if not self.system_active:
                    self.bank_name = "Sem banco cadastrado"
                    self.zoom_bank = "-"
                    self.zoom_patch = "-"
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar patch por program: {e}")
            # Só reseta se o sistema não estiver ativo
            if not self.system_active:
                self.bank_name = "Aguardando Comando"
                self.zoom_bank = "-"
                self.zoom_patch = "-"
    
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
                    
                    # Define status estável e sistema ativo
                    self.status = "Sistema ativo"
                    self.system_active = True
                    self.patch_activated = True  # Marca que um patch foi ativado
                else:
                    self.logger.error(f"Erro ao ativar patch: {data.get('error')}")
                    self.status = "Erro ao ativar"
                    self.system_active = False
            else:
                self.logger.error(f"Erro HTTP ao ativar patch: {response.status_code}")
                self.status = "Erro HTTP"
                self.system_active = False
        except Exception as e:
            self.logger.error(f"Erro ao ativar patch: {e}")
            self.status = "Erro"
            self.system_active = False
    
    def poll_midi_commands(self):
        """Faz polling dos comandos MIDI (igual ao JavaScript)"""
        try:
            # Verifica se a API está funcionando
            if not self.check_api_health():
                self.status = "API indisponível"
                self.system_active = False
                return
            
            # Verifica status dos dispositivos periodicamente
            self.check_device_status()
            
            # Só verifica status dos dispositivos, sem tentar reconectar
            self.check_device_status()
            
            # Obtém comandos MIDI
            commands = self.get_midi_commands()
            
            if commands:
                # Processa novos comandos
                for command in commands:
                    if command not in self.last_commands:
                        self.process_midi_command(command)
                        self.last_commands.append(command)
                
                # Mantém apenas os últimos 10 comandos
                self.last_commands = self.last_commands[-10:]
            
            # NÃO altera status - mantém estável até receber comando
            pass
        except Exception as e:
            self.logger.error(f"Erro no polling MIDI: {e}")
            self.status = "Erro no polling"
            self.system_active = False
    
    def signal_handler(self, signum, frame):
        """Handler para sinais de shutdown"""
        self.logger.info(f"Recebido sinal {signum}, encerrando serviço...")
        self.running = False
    
    def run(self):
        """Executa o serviço principal"""
        self.logger.info("Iniciando serviço LCD melhorado...")
        self.running = True
        
        try:
            # Mostrar tela de inicialização
            self.show_startup_screen()
            time.sleep(2)
            
            # Aguardar um pouco para a API inicializar
            time.sleep(2)
            
            # Verificar se a API está funcionando
            if not self.check_api_health():
                self.logger.error("API não está funcionando. Saindo...")
                self.status = "API indisponível"
                self.bank_name = "Erro no sistema"
                self.update_display()
                time.sleep(5)
                return
            
            # Mostrar tela de conexão e aguardar comando
            self.show_connecting_screen()
            
            # Conectar aos dispositivos uma vez
            self.connect_devices()
            time.sleep(3)
            self.check_device_status()
            
            # Atualizar tela com status dos dispositivos
            self.show_connecting_screen()
            
            # Atualizar status final
            if not self.chocolate_connected and not self.zoom_connected:
                self.status = "Problema de conexão"
                self.bank_name = "Dispositivos desconectados"
            elif not self.chocolate_connected:
                self.status = "Chocolate desconectado"
                self.bank_name = "Aguardando Chocolate"
            elif not self.zoom_connected:
                self.status = "Zoom desconectada"
                self.bank_name = "Aguardando Zoom"
            else:
                self.status = "Dispositivos conectados"
                self.bank_name = "Aguardando Comando"
            
            # Loop principal
            while self.running:
                try:
                    # Faz polling dos comandos MIDI (igual ao JavaScript)
                    self.poll_midi_commands()
                    
                    # Só mostra tela de conexão até receber comando
                    if not self.patch_activated:
                        self.show_connecting_screen()
                        # Aguarda 500ms (igual ao JavaScript)
                        time.sleep(0.5)
                    else:
                        # Se recebeu comando, mostra tela normal
                        self.update_display()
                        # Aguarda 500ms (igual ao JavaScript)
                        time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"Erro no loop principal: {e}")
                    time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Erro fatal no serviço: {e}")
            self.show_error_screen(str(e))
            time.sleep(5)
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpeza ao encerrar"""
        try:
            # Fechar framebuffer
            if hasattr(self, 'fb'):
                self.fb.close()
            
            self.logger.info("Serviço LCD melhorado encerrado")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")

def main():
    """Função principal"""
    service = LCDServiceImproved()
    service.run()

if __name__ == "__main__":
    main() 