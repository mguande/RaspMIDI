#!/usr/bin/env python3
"""
Serviço LCD dedicado para RaspMIDI
Monitora MIDI e exibe informações diretamente no LCD usando framebuffer
"""

import os
import sys
import time
import json
import threading
from PIL import Image, ImageDraw, ImageFont
import mido
from mido import Message
import pygame
from pygame import gfxdraw
import signal
import logging

# Configurações do LCD
LCD_WIDTH = 480
LCD_HEIGHT = 320
FRAMEBUFFER_DEVICE = "/dev/fb1"

# Configurações de cores (RGB)
COLORS = {
    'background': (0, 0, 0),      # Preto
    'text': (255, 215, 0),        # Dourado
    'accent': (255, 255, 255),    # Branco
    'error': (255, 0, 0),         # Vermelho
    'success': (0, 255, 0),       # Verde
}

class LCDService:
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
        
        # Inicializar pygame para framebuffer
        os.environ['SDL_FBDEV'] = FRAMEBUFFER_DEVICE
        os.environ['SDL_NOMOUSE'] = '1'
        pygame.init()
        
        # Configurar display
        self.screen = pygame.display.set_mode((LCD_WIDTH, LCD_HEIGHT), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
        
        # Carregar fontes
        self.load_fonts()
        
        # Inicializar MIDI
        self.init_midi()
        
        # Configurar sinais para graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_fonts(self):
        """Carrega as fontes para o display"""
        try:
            # Fonte principal (digital)
            self.font_large = pygame.font.Font("/home/matheus/RaspMIDI/app/web/static/fonts/DS-DIGI.TTF", 48)
            self.font_medium = pygame.font.Font("/home/matheus/RaspMIDI/app/web/static/fonts/DS-DIGI.TTF", 32)
            self.font_small = pygame.font.Font("/home/matheus/RaspMIDI/app/web/static/fonts/DS-DIGI.TTF", 24)
            self.font_tiny = pygame.font.Font("/home/matheus/RaspMIDI/app/web/static/fonts/DS-DIGI.TTF", 18)
        except Exception as e:
            self.logger.error(f"Erro ao carregar fontes: {e}")
            # Fallback para fontes padrão
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
            self.font_tiny = pygame.font.Font(None, 18)
    
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
                self.logger.debug(f"SysEx recebida: {msg.data.hex()}")
                
        except Exception as e:
            self.logger.error(f"Erro no callback MIDI: {e}")
    
    def update_display(self):
        """Atualiza o display com as informações atuais"""
        try:
            # Limpar tela
            self.screen.fill(COLORS['background'])
            
            # Desenhar título
            title = self.font_large.render("RaspMIDI", True, COLORS['text'])
            title_rect = title.get_rect(center=(LCD_WIDTH//2, 40))
            self.screen.blit(title, title_rect)
            
            # Desenhar informações do banco atual
            y_pos = 100
            
            # Banco atual
            bank_text = f"BANCO: {self.current_bank}"
            bank_surface = self.font_medium.render(bank_text, True, COLORS['accent'])
            bank_rect = bank_surface.get_rect(center=(LCD_WIDTH//2, y_pos))
            self.screen.blit(bank_surface, bank_rect)
            y_pos += 50
            
            # Patch Chocolate
            chocolate_text = f"CHOCOLATE: {self.chocolate_patch}"
            chocolate_surface = self.font_medium.render(chocolate_text, True, COLORS['text'])
            chocolate_rect = chocolate_surface.get_rect(center=(LCD_WIDTH//2, y_pos))
            self.screen.blit(chocolate_surface, chocolate_rect)
            y_pos += 50
            
            # Banco Zoom
            zoom_bank_text = f"ZOOM BANCO: {self.zoom_bank}"
            zoom_bank_surface = self.font_medium.render(zoom_bank_text, True, COLORS['text'])
            zoom_bank_rect = zoom_bank_surface.get_rect(center=(LCD_WIDTH//2, y_pos))
            self.screen.blit(zoom_bank_surface, zoom_bank_rect)
            y_pos += 50
            
            # Patch Zoom
            zoom_patch_text = f"ZOOM PATCH: {self.zoom_patch}"
            zoom_patch_surface = self.font_medium.render(zoom_patch_text, True, COLORS['text'])
            zoom_patch_rect = zoom_patch_surface.get_rect(center=(LCD_WIDTH//2, y_pos))
            self.screen.blit(zoom_patch_surface, zoom_patch_rect)
            y_pos += 60
            
            # Status
            status_text = f"STATUS: {self.status}"
            status_surface = self.font_small.render(status_text, True, COLORS['success'])
            status_rect = status_surface.get_rect(center=(LCD_WIDTH//2, y_pos))
            self.screen.blit(status_surface, status_rect)
            
            # Atualizar display
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar display: {e}")
    
    def show_startup_screen(self):
        """Mostra tela de inicialização"""
        try:
            self.screen.fill(COLORS['background'])
            
            # Logo/título
            title = self.font_large.render("RaspMIDI", True, COLORS['text'])
            title_rect = title.get_rect(center=(LCD_WIDTH//2, 120))
            self.screen.blit(title, title_rect)
            
            # Status de inicialização
            status = self.font_medium.render("Inicializando...", True, COLORS['accent'])
            status_rect = status.get_rect(center=(LCD_WIDTH//2, 200))
            self.screen.blit(status, status_rect)
            
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar tela de inicialização: {e}")
    
    def show_error_screen(self, error_msg):
        """Mostra tela de erro"""
        try:
            self.screen.fill(COLORS['background'])
            
            error_title = self.font_medium.render("ERRO", True, COLORS['error'])
            error_title_rect = error_title.get_rect(center=(LCD_WIDTH//2, 120))
            self.screen.blit(error_title, error_title_rect)
            
            error_text = self.font_small.render(error_msg, True, COLORS['error'])
            error_rect = error_text.get_rect(center=(LCD_WIDTH//2, 200))
            self.screen.blit(error_text, error_rect)
            
            pygame.display.flip()
            
        except Exception as e:
            self.logger.error(f"Erro ao mostrar tela de erro: {e}")
    
    def signal_handler(self, signum, frame):
        """Handler para sinais de shutdown"""
        self.logger.info(f"Recebido sinal {signum}, encerrando serviço...")
        self.running = False
    
    def run(self):
        """Executa o serviço principal"""
        self.logger.info("Iniciando serviço LCD...")
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
                    
                    # Processar eventos pygame
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                    
                    # Aguardar um pouco
                    time.sleep(0.1)
                    
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
            
            # Encerrar pygame
            pygame.quit()
            
            self.logger.info("Serviço LCD encerrado")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {e}")

def main():
    """Função principal"""
    service = LCDService()
    service.run()

if __name__ == "__main__":
    main() 