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
        self.last_connection_attempt = 0  # Timestamp da última tentativa de conexão
        self.connection_interval = 10  # Intervalo em segundos entre tentativas
        
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
            
            # Status dos dispositivos
            choc_status = "✅" if self.chocolate_connected else "❌"
            zoom_status = "✅" if self.zoom_connected else "❌"
            
            all_connected = self.chocolate_connected and self.zoom_connected
            
            if all_connected:
                self.draw_smiley(draw, center_x, center_y-60, 60, happy=True, color=(0,255,0))
                msg = "DISPOSITIVOS CONECTADOS"
                color_txt = (0,255,0)
                status_msg = "Sistema pronto!"
            else:
                self.draw_smiley(draw, center_x, center_y-60, 60, happy=False, color=(255,0,0))
                msg = "CONECTANDO DISPOSITIVOS"
                color_txt = (255,255,0)  # Amarelo para indicar processo
                status_msg = f"Chocolate: {choc_status} Zoom: {zoom_status}"
            
            # Texto principal
            font_msg = self.font_large.font_variant(size=32) if hasattr(self.font_large, 'font_variant') else self.font_large
            w_msg, h_msg = self.measure_text(draw, msg, font_msg)
            draw.text((center_x-w_msg//2, center_y+20), msg, fill=color_txt, font=font_msg)
            
            # Status detalhado
            font_status = self.font_large.font_variant(size=24) if hasattr(self.font_large, 'font_variant') else self.font_large
            w_status, h_status = self.measure_text(draw, status_msg, font_status)
            draw.text((center_x-w_status//2, center_y+70), status_msg, fill=(255,255,255), font=font_status)
            
            # Contador de tentativas (se não conectado)
            if not all_connected:
                current_time = time.time()
                if self.last_connection_attempt > 0:
                    next_attempt = self.last_connection_attempt + self.connection_interval - current_time
                    if next_attempt > 0:
                        countdown = f"Próxima tentativa: {int(next_attempt)}s"
                        w_count, h_count = self.measure_text(draw, countdown, font_status)
                        draw.text((center_x-w_count//2, center_y+100), countdown, fill=(150,150,150), font=font_status)
            
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
            # Fonte dos nomes dos dispositivos: metade do tamanho do título
            if hasattr(font_title, 'font_variant'):
                device_font = font_title.font_variant(size=max(12, font_title.size // 2))
            else:
                device_font = self.font_large
            # Nome do Chocolate
            choc_name = "Chocolate MIDI"
            w_choc_name, h_choc_name = self.measure_text(draw, choc_name, device_font)
            draw.text((choc_x+30-w_choc_name//2, icon_y), choc_name, fill=(180, 255, 180), font=device_font)
            # Nome do Zoom
            zoom_name = "Zoom G3X"
            w_zoom_name, h_zoom_name = self.measure_text(draw, zoom_name, device_font)
            draw.text((zoom_x+35-w_zoom_name//2, icon_y), zoom_name, fill=(180, 200, 255), font=device_font)
            # Fonte dos labels dos patches: metade do tamanho do título
            if hasattr(font_title, 'font_variant'):
                patch_font = font_title.font_variant(size=max(12, font_title.size // 2))
            else:
                patch_font = self.font_large
            # Labels dos patches (agora com o mesmo tamanho do título)
            choc_label = f"{self.chocolate_patch}" if self.chocolate_patch else "001"
            try:
                zoom_patch_num = int(self.zoom_patch)
            except Exception:
                zoom_patch_num = 1
            zoom_label = f"{self.zoom_bank}-{zoom_patch_num:02d}"
            self.logger.info(f"[LCD] chocolate_patch={self.chocolate_patch}, choc_label={choc_label}, zoom_bank={self.zoom_bank}, zoom_patch={self.zoom_patch}, zoom_label={zoom_label}")
            w_choc, _ = self.measure_text(draw, choc_label, font_title)
            w_zoom, _ = self.measure_text(draw, zoom_label, font_title)
            draw.text((choc_x+30-w_choc//2, icon_y+40), choc_label, fill=(255, 215, 0), font=font_title)
            draw.text((zoom_x+35-w_zoom//2, icon_y+40), zoom_label, fill=(255, 215, 0), font=font_title)
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

    def should_attempt_connection(self):
        """Verifica se deve tentar conectar aos dispositivos"""
        current_time = time.time()
        return current_time - self.last_connection_attempt >= self.connection_interval

    def attempt_auto_connection(self):
        """Tenta conectar automaticamente aos dispositivos se necessário"""
        try:
            # Verifica se ambos os dispositivos estão conectados
            if self.chocolate_connected and self.zoom_connected:
                return True  # Ambos conectados, não precisa tentar
            
            # Verifica se é hora de tentar novamente
            if not self.should_attempt_connection():
                return False
            
            self.logger.info("Tentando reconexão automática aos dispositivos...")
            self.last_connection_attempt = time.time()
            
            # 1. Primeiro, atualiza a lista de dispositivos disponíveis
            self.logger.info("Atualizando lista de dispositivos...")
            try:
                response = requests.post(
                    f"{self.api_base_url}/midi/devices/scan",
                    headers={"Content-Type": "application/json"},
                    json={},
                    timeout=5
                )
                if response.status_code == 200:
                    self.logger.info("Lista de dispositivos atualizada")
                else:
                    self.logger.warning(f"Erro ao atualizar lista: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Erro ao atualizar lista de dispositivos: {e}")
            
            # Aguarda um pouco para o sistema processar
            time.sleep(1)
            
            # 2. Lista todos os dispositivos disponíveis
            try:
                response = requests.get(f"{self.api_base_url}/midi/devices/list", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('data'):
                        devices = data['data']
                        self.logger.info(f"Dispositivos disponíveis: {len(devices)}")
                        for device in devices:
                            self.logger.info(f"  - {device.get('name', 'Desconhecido')} ({device.get('type', 'N/A')})")
            except Exception as e:
                self.logger.error(f"Erro ao listar dispositivos: {e}")
            
            # 3. Tenta conectar aos dispositivos
            self.connect_devices()
            
            # 4. Aguarda um pouco para os dispositivos se conectarem
            time.sleep(3)
            
            # 5. Verifica o status novamente
            self.check_device_status()
            
            if self.chocolate_connected and self.zoom_connected:
                self.logger.info("✅ Ambos os dispositivos conectados com sucesso!")
                return True
            else:
                self.logger.warning("❌ Ainda há dispositivos desconectados")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na tentativa de conexão automática: {e}")
            return False
    
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
            self.logger.info(f"[PATCH DEBUG] Patch recebido: {patch}")
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
                        # Usar apenas o campo correto para a letra do banco
                        self.zoom_bank = patch.get('zoom_bank', 'A')
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
                    # Verifica se a API está funcionando
                    if not self.check_api_health():
                        self.status = "API indisponível"
                        self.show_connecting_screen()
                        time.sleep(5)
                        continue
                    
                    # Verifica status dos dispositivos
                    self.check_device_status()
                    
                    # Se não estão conectados, tenta reconexão automática
                    if not (self.chocolate_connected and self.zoom_connected):
                        self.attempt_auto_connection()
                        self.show_connecting_screen()
                        time.sleep(1)
                        continue
                    
                    # Se estão conectados, processa comandos MIDI
                    self.poll_midi_commands()
                    
                    if not self.patch_activated:
                        self.show_connecting_screen()
                    else:
                        self.update_display()
                    
                    time.sleep(0.3)
                    
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