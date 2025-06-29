# Gerenciamento de Dispositivos MIDI - RaspMIDI

## Visão Geral

O RaspMIDI agora inclui um sistema completo de gerenciamento de dispositivos MIDI, permitindo:

- **Detecção automática** de dispositivos USB e Bluetooth
- **Configuração de entrada/saída** MIDI
- **Persistência de configurações** entre reinicializações
- **Interface visual** para gerenciamento de dispositivos

## Funcionalidades

### 1. Detecção de Dispositivos

O sistema automaticamente detecta e categoriza dispositivos MIDI:

- **Dispositivos USB**: Zoom G3X, Chocolate MIDI, etc.
- **Dispositivos Bluetooth**: Chocolate MIDI via Bluetooth, etc.

### 2. Configuração de Entrada/Saída

- **Dispositivo de Entrada**: Recebe comandos MIDI (ex: Chocolate)
- **Dispositivo de Saída**: Envia comandos MIDI (ex: Zoom G3X)

### 3. Interface Web

A interface web inclui uma nova seção "Dispositivos MIDI" com:

- Lista de dispositivos USB conectados
- Lista de dispositivos Bluetooth disponíveis
- Seletores para entrada e saída MIDI
- Botão para salvar configuração
- Status de conectividade em tempo real

## Como Usar

### 1. Acesse a Interface Web

Abra `http://seu-raspberry-pi:5000` no seu celular ou computador.

### 2. Configure os Dispositivos

1. **Conecte os dispositivos**:
   - Zoom G3X via USB
   - Chocolate MIDI via USB ou Bluetooth

2. **Escanee dispositivos**:
   - Clique em "Escanear Dispositivos" na barra de status
   - Ou clique em "Atualizar" na seção de dispositivos

3. **Configure entrada/saída**:
   - Selecione o dispositivo de entrada (ex: Chocolate)
   - Selecione o dispositivo de saída (ex: Zoom G3X)
   - Clique em "Salvar Configuração"

### 3. Use o Sistema

Após a configuração:

- **Patches** serão enviados para o dispositivo de saída configurado
- **Efeitos** serão controlados no dispositivo de saída
- **Comandos MIDI** serão enviados para o dispositivo correto

## API Endpoints

### Dispositivos

- `GET /api/midi/devices/list` - Lista dispositivos disponíveis
- `POST /api/midi/devices/scan` - Escaneia dispositivos
- `GET /api/midi/devices/status` - Status dos dispositivos

### Configuração

- `GET /api/midi/config` - Obtém configuração atual
- `PUT /api/midi/config` - Atualiza configuração

### Exemplo de Configuração

```json
{
  "input_device": "Chocolate MIDI",
  "output_device": "Zoom G3X",
  "auto_connect": true,
  "devices": {
    "usb": [
      {
        "name": "Zoom G3X",
        "type": "output",
        "connected": true
      },
      {
        "name": "Chocolate MIDI",
        "type": "input",
        "connected": true
      }
    ],
    "bluetooth": [
      {
        "name": "Chocolate MIDI BT",
        "type": "input",
        "connected": false
      }
    ]
  }
}
```

## Arquivos de Configuração

### midi_config.json

Localizado em `data/midi_config.json`, contém:

- Dispositivos de entrada/saída configurados
- Lista de dispositivos detectados
- Configurações de auto-conexão

### Estrutura do Arquivo

```json
{
  "input_device": "nome_do_dispositivo_entrada",
  "output_device": "nome_do_dispositivo_saida",
  "auto_connect": true,
  "devices": {
    "usb": [...],
    "bluetooth": [...]
  }
}
```

## Troubleshooting

### Dispositivo não detectado

1. Verifique se o dispositivo está conectado
2. Clique em "Escanear Dispositivos"
3. Verifique os logs em `logs/raspmidi_*.log`

### Erro de conexão

1. Verifique se o dispositivo está disponível
2. Tente desconectar e reconectar
3. Reinicie o serviço: `sudo systemctl restart raspmidi`

### Configuração não salva

1. Verifique permissões do diretório `data/`
2. Verifique se há espaço em disco
3. Verifique os logs para erros

## Logs

Os logs de dispositivos MIDI são salvos em:

- `logs/raspmidi_*.log` - Logs gerais
- Console - Logs em tempo real

### Exemplos de Logs

```
INFO - Dispositivos MIDI detectados: ['Zoom G3X', 'Chocolate MIDI']
INFO - Zoom G3X conectado na porta: Zoom G3X
INFO - Configuração MIDI salva
INFO - Dispositivo de saída configurado: Zoom G3X
```

## Desenvolvimento

### Adicionando Novos Dispositivos

1. Crie um controlador específico em `app/midi/`
2. Adicione detecção no método `_categorize_devices()`
3. Implemente métodos de conexão e envio

### Modificando Configurações

1. Edite `app/config.py` para configurações padrão
2. Modifique `app/midi/controller.py` para lógica de dispositivos
3. Atualize a interface web em `app/web/static/js/app.js`

## Suporte

Para problemas ou dúvidas:

1. Verifique os logs
2. Teste com dispositivos diferentes
3. Reinicie o serviço
4. Consulte a documentação completa no README.md 