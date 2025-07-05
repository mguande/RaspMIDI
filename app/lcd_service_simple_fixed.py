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
    
    def draw_smiley(self, draw, x, y, radius, happy=True, color=(0,255,0)):
        """Desenha um smiley feliz ou triste"""
        # Face
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline=(0,0,0), width=4)
        # Olhos
        eye_y = y - radius//3
        draw.ellipse([x-radius//2-10, eye_y, x-radius//2+10, eye_y+20], fill=(0,0,0))
        draw.ellipse([x+radius//2-10, eye_y, x+radius//2+10, eye_y+20], fill=(0,0,0))
        # Boca
        mouth_y = y+radius//3
        if happy:
            draw.arc([x-radius//2, mouth_y-10, x+radius//2, mouth_y+30], start=0, end=180, fill=(0,0,0), width=6)
        else:
            draw.arc([x-radius//2, mouth_y, x+radius//2, mouth_y+40], start=180, end=360, fill=(0,0,0), width=6)

    def measure_text(self, draw, text, font):
        try:
            bbox = draw.textbbox((0,0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            return w, h
        except Exception:
            try:
                w, h = draw.textsize(text, font=font)
                return w, h
            except Exception:
                return font.getsize(text)

    def show_connecting_screen(self, force=False):
        """Mostra tela de status de conexão com smiley e texto grande"""
        try:
            image = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            center_x = LCD_WIDTH // 2
            center_y = LCD_HEIGHT // 2
            all_connected = self.chocolate_connected and self.zoom_connected
            if all_connected:
                self.draw_smiley(draw, center_x, center_y-40, 70, happy=True, color=(0,255,0))
                msg = "DISPOSITIVOS CONECTADOS"
                color_txt = (0,255,0)
            else:
                self.draw_smiley(draw, center_x, center_y-40, 70, happy=False, color=(255,0,0))
                msg = "DISPOSITIVOS DESCONECTADOS"
                color_txt = (255,0,0)
            font_msg = self.font_large.font_variant(size=38) if hasattr(self.font_large, 'font_variant') else self.font_large
            w_msg, h_msg = self.measure_text(draw, msg, font_msg)
            draw.text((center_x-w_msg//2, center_y+60), msg, fill=color_txt, font=font_msg)
            screen_hash = self.get_screen_hash(image)
            if force or screen_hash != self.last_screen_hash:
                self.update_framebuffer(image)
                self.last_screen_hash = screen_hash
        except Exception as e:
            self.logger.error(f"Erro na tela de conexão: {e}")
    
    def draw_chocolate_icon(self, draw, x, y):
        """Desenha o ícone do Chocolate (vetorial, estilo da imagem)"""
        # Caixa principal
        draw.rectangle([x, y, x+60, y+30], outline=(150, 150, 150), width=3, fill=(30, 30, 30))
        # LEDs verdes
        for i in range(4):
            draw.rectangle([x+5+i*14, y+5, x+15+i*14, y+15], fill=(80, 255, 80), outline=(0, 0, 0))
        # Lado direito marrom
        draw.rectangle([x+50, y, x+60, y+30], fill=(80, 50, 20))
        # LEDs inferiores
        for i in range(4):
            draw.ellipse([x+5+i*14, y+20, x+13+i*14, y+28], fill=(40, 40, 40), outline=(0, 0, 0))

    def draw_zoom_icon(self, draw, x, y):
        """Desenha o ícone do Zoom (vetorial, estilo da imagem)"""
        # Caixa principal
        draw.rectangle([x, y, x+70, y+22], outline=(150, 150, 150), width=3, fill=(30, 30, 30))
        # LEDs cinza
        for i in range(5):
            draw.ellipse([x+7+i*13, y+6, x+15+i*13, y+14], fill=(180, 180, 180), outline=(0, 0, 0))
        # LED azul
        draw.ellipse([x+33, y+6, x+41, y+14], fill=(40, 60, 180), outline=(0, 0, 0))

    def update_display(self, force=False):
        """Atualiza o display com o layout igual à imagem enviada"""
        try:
            image = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            title = self.bank_name or "Nome do banco"
            font_title = self.font_large.font_variant(size=48) if hasattr(self.font_large, 'font_variant') else self.font_large
            w_title, h_title = self.measure_text(draw, title, font_title)
            draw.text(((LCD_WIDTH-w_title)//2, 40), title, fill=(255, 215, 0), font=font_title)
            icon_y = 120
            choc_x = 60
            zoom_x = LCD_WIDTH - 60 - 70
            self.draw_chocolate_icon(draw, choc_x, icon_y)
            self.draw_zoom_icon(draw, zoom_x, icon_y)
            label_font = self.font_large.font_variant(size=28) if hasattr(self.font_large, 'font_variant') else self.font_large
            choc_label = f"{self.zoom_bank or 'A'}-{int(self.chocolate_patch) if self.chocolate_patch else '1'}"
            zoom_label = f"{self.zoom_patch or '001'}"
            w_choc, _ = self.measure_text(draw, choc_label, label_font)
            w_zoom, _ = self.measure_text(draw, zoom_label, label_font)
            draw.text((choc_x+30-w_choc//2, icon_y+40), choc_label, fill=(255, 215, 0), font=label_font)
            draw.text((zoom_x+35-w_zoom//2, icon_y+40), zoom_label, fill=(255, 215, 0), font=label_font)
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
                        # Verifica se zoom_patch é um número válido
                        zoom_patch_value = patch.get('zoom_patch')
                        self.logger.info(f"Zoom patch value: {zoom_patch_value} (type: {type(zoom_patch_value)})")
                        if zoom_patch_value is not None and str(zoom_patch_value).isdigit():
                            self.zoom_patch = f"{int(zoom_patch_value):03d}"
                        else:
                            self.zoom_patch = "001"
                        self.logger.info(f"Zoom patch final: {self.zoom_patch}")
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