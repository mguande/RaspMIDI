#!/usr/bin/env python3
"""
Serviço LCD simplificado para RaspMIDI
Usa framebuffer diretamente sem pygame
"""

import os
import sys
import time
import json
import threading
import signal
import logging
import struct
from PIL import Image, ImageDraw, ImageFont
import mido
from mido import Message

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
}

class LCDServiceSimple:
    def __init__(self):
        self.running = False
        self.current_bank = "A"
        self.current_patch = "001"
        self.zoom_bank = "A"
        self.zoom_patch = "001"
        self.chocolate_patch = "001"
        self.status = "Aguardando..."
        self.midi_devices = {}
        
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
        
        # Inicializar MIDI
        self.init_midi()
        
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
    
    def init_midi(self):
        """Inicializa conexões MIDI"""
        try:
            # Listar portas MIDI disponíveis
            input_ports = mido.get_input_names()
            output_ports = mido.get_output_names()
            
            self.logger.info(f"Portas MIDI de entrada: {input_ports}")
            self.logger.info(f"Portas MIDI de saída: {output_ports}")
            
            # Conectar aos dispositivos
            self.midi_inputs = {}
            self.midi_outputs = {}
            
            for port_name in input_ports:
                if 'chocolate' in port_name.lower() or 'zoom' in port_name.lower():
                    try:
                        port = mido.open_input(port_name)
                        port.callback = self.midi_callback
                        self.midi_inputs[port_name] = port
                        self.logger.info(f"Conectado à entrada MIDI: {port_name}")
                    except Exception as e:
                        self.logger.error(f"Erro ao conectar à entrada {port_name}: {e}")
            
            for port_name in output_ports:
                if 'chocolate' in port_name.lower() or 'zoom' in port_name.lower():
                    try:
                        port = mido.open_output(port_name)
                        self.midi_outputs[port_name] = port
                        self.logger.info(f"Conectado à saída MIDI: {port_name}")
                    except Exception as e:
                        self.logger.error(f"Erro ao conectar à saída {port_name}: {e}")
            
            if not self.midi_inputs:
                self.logger.warning("Nenhuma porta MIDI de entrada encontrada")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar MIDI: {e}")
    
    def midi_callback(self, msg):
        """Callback para mensagens MIDI recebidas"""
        try:
            if msg.type == 'program_change':
                # Mudança de patch
                patch_number = msg.program + 1
                if 'chocolate' in msg.port.name.lower():
                    self.chocolate_patch = f"{patch_number:03d}"
                    self.logger.info(f"Chocolate patch mudou para: {self.chocolate_patch}")
                elif 'zoom' in msg.port.name.lower():
                    self.zoom_patch = f"{patch_number:03d}"
                    self.logger.info(f"Zoom patch mudou para: {self.zoom_patch}")
                
                self.update_display()
            
            elif msg.type == 'control_change':
                # Mudança de banco (CC 0 ou 32)
                if msg.control in [0, 32]:
                    bank_number = msg.value
                    bank_letter = chr(ord('A') + bank_number)
                    
                    if 'chocolate' in msg.port.name.lower():
                        self.current_bank = bank_letter
                        self.logger.info(f"Chocolate banco mudou para: {self.current_bank}")
                    elif 'zoom' in msg.port.name.lower():
                        self.zoom_bank = bank_letter
                        self.logger.info(f"Zoom banco mudou para: {self.zoom_bank}")
                    
                    self.update_display()
            
            elif msg.type == 'sysex':
                # Mensagens SysEx podem conter informações de patch
                try:
                    self.logger.debug(f"SysEx recebida: {msg.data.hex()}")
                except AttributeError:
                    # Algumas versões do mido não têm .hex() em SysexData
                    self.logger.debug(f"SysEx recebida: {msg.data}")
                
        except Exception as e:
            self.logger.error(f"Erro no callback MIDI: {e}")
    
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
            # Criar imagem
            image = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Desenhar título
            title = "RaspMIDI"
            draw.text((LCD_WIDTH//2 - 50, 20), title, fill=(255, 215, 0), font=self.font_large)
            
            # Desenhar informações do banco atual
            y_pos = 80
            
            # Banco atual
            bank_text = f"BANCO: {self.current_bank}"
            draw.text((20, y_pos), bank_text, fill=(255, 255, 255), font=self.font_large)
            y_pos += 40
            
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
    
    def signal_handler(self, signum, frame):
        """Handler para sinais de shutdown"""
        self.logger.info(f"Recebido sinal {signum}, encerrando serviço...")
        self.running = False
    
    def run(self):
        """Executa o serviço principal"""
        self.logger.info("Iniciando serviço LCD simplificado...")
        self.running = True
        
        try:
            # Mostrar tela de inicialização
            self.show_startup_screen()
            time.sleep(2)
            
            # Atualizar status
            self.status = "Aguardando comandos..."
            
            # Loop principal
            while self.running:
                try:
                    # Atualizar display
                    self.update_display()
                    
                    # Aguardar um pouco
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
            # Fechar conexões MIDI
            for port in self.midi_inputs.values():
                port.close()
            for port in self.midi_outputs.values():
                port.close()
            
            # Fechar framebuffer
            if hasattr(self, 'fb'):
                self.fb.close()
            
            self.logger.info("Serviço LCD simplificado encerrado")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")

def main():
    """Função principal"""
    service = LCDServiceSimple()
    service.run()

if __name__ == "__main__":
    main() 