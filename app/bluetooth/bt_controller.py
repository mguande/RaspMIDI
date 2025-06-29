# -*- coding: utf-8 -*-
"""
RaspMIDI - Controlador Bluetooth
"""

import logging
import asyncio
import threading
from typing import Dict, List, Optional, Callable
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

from app.config import Config

class BluetoothController:
    """Controlador Bluetooth para Chocolate MIDI"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.device = None
        self.connected = False
        self.scanning = False
        
        # Callbacks
        self.on_connect = None
        self.on_disconnect = None
        self.on_data_received = None
        
        # Configurações
        self.device_name = Config.CHOCOLATE_BT_NAME
        self.device_address = Config.CHOCOLATE_BT_ADDRESS
        
        # Thread para operações assíncronas
        self._loop = None
        self._thread = None
        
        self.logger.info("Controlador Bluetooth inicializado")
    
    def start(self):
        """Inicia o controlador Bluetooth"""
        try:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
                self._thread.start()
                self.logger.info("Controlador Bluetooth iniciado")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar controlador Bluetooth: {str(e)}")
    
    def stop(self):
        """Para o controlador Bluetooth"""
        try:
            if self._loop:
                asyncio.run_coroutine_threadsafe(self._stop_async(), self._loop)
            
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
            
            self.logger.info("Controlador Bluetooth parado")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar controlador Bluetooth: {str(e)}")
    
    def _run_async_loop(self):
        """Executa loop assíncrono em thread separada"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    async def _stop_async(self):
        """Para o loop assíncrono"""
        if self._loop:
            self._loop.stop()
    
    def scan_devices(self, callback: Callable = None) -> List[Dict]:
        """Escaneia dispositivos Bluetooth"""
        try:
            if not self._loop:
                self.logger.error("Loop assíncrono não inicializado")
                return []
            
            future = asyncio.run_coroutine_threadsafe(self._scan_async(), self._loop)
            devices = future.result(timeout=30)
            
            if callback:
                callback(devices)
            
            return devices
            
        except Exception as e:
            self.logger.error(f"Erro ao escanear dispositivos: {str(e)}")
            return []
    
    async def _scan_async(self) -> List[Dict]:
        """Escaneia dispositivos Bluetooth de forma assíncrona"""
        try:
            self.scanning = True
            self.logger.info("Escaneando dispositivos Bluetooth...")
            
            devices = await BleakScanner.discover(timeout=10.0)
            
            device_list = []
            for device in devices:
                device_info = {
                    'name': device.name or 'Unknown',
                    'address': device.address,
                    'rssi': device.rssi,
                    'metadata': device.metadata
                }
                device_list.append(device_info)
                
                if device.name and self.device_name.lower() in device.name.lower():
                    self.logger.info(f"Chocolate MIDI encontrado: {device.name} ({device.address})")
            
            self.scanning = False
            self.logger.info(f"Escaneamento concluído. {len(device_list)} dispositivos encontrados")
            
            return device_list
            
        except Exception as e:
            self.scanning = False
            self.logger.error(f"Erro no escaneamento assíncrono: {str(e)}")
            return []
    
    def connect_to_device(self, device_address: str = None, callback: Callable = None) -> bool:
        """Conecta a um dispositivo Bluetooth"""
        try:
            if not self._loop:
                self.logger.error("Loop assíncrono não inicializado")
                return False
            
            address = device_address or self.device_address
            if not address:
                self.logger.error("Endereço do dispositivo não especificado")
                return False
            
            future = asyncio.run_coroutine_threadsafe(
                self._connect_async(address), self._loop
            )
            success = future.result(timeout=30)
            
            if callback:
                callback(success)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar dispositivo: {str(e)}")
            return False
    
    async def _connect_async(self, device_address: str) -> bool:
        """Conecta a um dispositivo de forma assíncrona"""
        try:
            self.logger.info(f"Conectando ao dispositivo: {device_address}")
            
            self.client = BleakClient(device_address)
            await self.client.connect()
            
            if self.client.is_connected:
                self.connected = True
                self.device_address = device_address
                
                # Configura notificações
                await self._setup_notifications()
                
                self.logger.info("Dispositivo Bluetooth conectado")
                
                if self.on_connect:
                    self.on_connect(device_address)
                
                return True
            else:
                self.logger.error("Falha ao conectar dispositivo")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na conexão assíncrona: {str(e)}")
            return False
    
    def disconnect(self):
        """Desconecta do dispositivo Bluetooth"""
        try:
            if self._loop and self.client:
                asyncio.run_coroutine_threadsafe(self._disconnect_async(), self._loop)
                
        except Exception as e:
            self.logger.error(f"Erro ao desconectar: {str(e)}")
    
    async def _disconnect_async(self):
        """Desconecta de forma assíncrona"""
        try:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                self.connected = False
                self.client = None
                
                self.logger.info("Dispositivo Bluetooth desconectado")
                
                if self.on_disconnect:
                    self.on_disconnect()
                    
        except Exception as e:
            self.logger.error(f"Erro na desconexão assíncrona: {str(e)}")
    
    async def _setup_notifications(self):
        """Configura notificações do dispositivo"""
        try:
            if not self.client or not self.client.is_connected:
                return
            
            # Procura por características MIDI
            services = await self.client.get_services()
            
            for service in services:
                for char in service.characteristics:
                    if char.properties.notify or char.properties.indicate:
                        await self.client.start_notify(char.uuid, self._notification_handler)
                        self.logger.info(f"Notificação configurada para: {char.uuid}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao configurar notificações: {str(e)}")
    
    def _notification_handler(self, sender, data):
        """Handler para notificações recebidas"""
        try:
            self.logger.debug(f"Dados recebidos: {data.hex()}")
            
            if self.on_data_received:
                self.on_data_received(data)
                
        except Exception as e:
            self.logger.error(f"Erro no handler de notificação: {str(e)}")
    
    def send_data(self, data: bytes) -> bool:
        """Envia dados via Bluetooth"""
        try:
            if not self._loop or not self.client or not self.connected:
                return False
            
            future = asyncio.run_coroutine_threadsafe(
                self._send_data_async(data), self._loop
            )
            return future.result(timeout=10)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar dados: {str(e)}")
            return False
    
    async def _send_data_async(self, data: bytes) -> bool:
        """Envia dados de forma assíncrona"""
        try:
            if not self.client or not self.client.is_connected:
                return False
            
            # Procura por característica de escrita
            services = await self.client.get_services()
            
            for service in services:
                for char in service.characteristics:
                    if char.properties.write or char.properties.write_without_response:
                        await self.client.write_gatt_char(char.uuid, data)
                        self.logger.debug(f"Dados enviados: {data.hex()}")
                        return True
            
            self.logger.error("Característica de escrita não encontrada")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no envio assíncrono: {str(e)}")
            return False
    
    def get_status(self) -> Dict:
        """Retorna status do controlador Bluetooth"""
        return {
            'connected': self.connected,
            'scanning': self.scanning,
            'device_address': self.device_address,
            'device_name': self.device_name
        }
    
    def set_callbacks(self, on_connect: Callable = None, on_disconnect: Callable = None, 
                     on_data_received: Callable = None):
        """Define callbacks para eventos"""
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_data_received = on_data_received 