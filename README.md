# RaspMIDI 🎵

**Controlador MIDI para Zoom G3X e MVAVE Chocolate Plus**

Um sistema completo para controle MIDI de dispositivos de guitarra, permitindo gerenciamento de patches, efeitos e comandos MIDI através de uma interface web moderna.

## 🎸 Dispositivos Suportados

- **Zoom G3X** - Processador de efeitos para guitarra
- **MVAVE Chocolate Plus** - Controlador MIDI de pedal

## ✨ Funcionalidades

### 🎛️ Gerenciamento de Patches
- Criação e edição de patches MIDI
- Configuração de efeitos por patch
- Suporte a diferentes tipos de comandos (PC, CC, Note On/Off)
- Interface visual intuitiva

### 🔧 Controle de Efeitos
- Configuração individual de 6 efeitos
- Estados ligado/desligado por patch
- Visualização em tempo real

### 📡 Monitoramento MIDI
- Monitor em tempo real de comandos MIDI
- Log de comandos enviados
- Simulação de comandos para teste

### 🔌 Gerenciamento de Dispositivos
- Detecção automática de dispositivos
- Status de conexão em tempo real
- Reconexão automática
- Alertas de alimentação externa

### 🎚️ Comandos Especiais
- Comandos SysEx para Zoom G3X
- Afinador integrado
- Controle de blocos de efeitos
- Comandos personalizados

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip
- Git

### Passos de Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/mguande/RaspMIDI.git
   cd RaspMIDI
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure o banco de dados**
   ```bash
   python -c "from app.database.database import init_db; init_db()"
   ```

6. **Execute o aplicativo**
   ```bash
   python run.py
   ```

7. **Acesse a interface web**
   ```
   http://localhost:5000
   ```

## 📁 Estrutura do Projeto

```
RaspMIDI/
├── app/                    # Aplicação principal
│   ├── api/               # Rotas da API REST
│   ├── bluetooth/         # Controle Bluetooth
│   ├── cache/             # Gerenciamento de cache
│   ├── database/          # Banco de dados
│   ├── midi/              # Controle MIDI
│   └── web/               # Interface web
│       ├── static/        # CSS, JS, imagens
│       └── templates/     # Templates HTML
├── data/                  # Dados do sistema
├── logs/                  # Logs da aplicação
├── docs/                  # Documentação
└── requirements.txt       # Dependências Python
```

## 🎮 Como Usar

### 1. Configuração Inicial
- Conecte os dispositivos MIDI via USB
- Acesse a interface web
- Configure os dispositivos de entrada e saída

### 2. Criação de Patches
- Clique em "Novo Patch"
- Configure nome, dispositivos e parâmetros
- Para Zoom G3X: selecione banco e patch
- Para Chocolate: configure canal de entrada

### 3. Configuração de Efeitos
- Habilite "Configuração de Efeitos"
- Configure cada efeito individualmente
- Salve o patch

### 4. Monitoramento
- Use o monitor MIDI para ver comandos em tempo real
- Teste comandos com a simulação
- Verifique logs de comandos enviados

## 🔧 Configuração

### Arquivo de Configuração
Crie um arquivo `config.json` na raiz do projeto:

```json
{
  "midi": {
    "input_device": "Chocolate MIDI In",
    "output_device": "Zoom G3X MIDI Out"
  },
  "bluetooth": {
    "enabled": true
  },
  "cache": {
    "timeout": 300
  }
}
```

### Variáveis de Ambiente
- `FLASK_ENV`: Ambiente (development/production)
- `FLASK_DEBUG`: Modo debug (True/False)
- `DATABASE_PATH`: Caminho do banco de dados

## 🚀 Scripts de Deploy

O projeto inclui diversos scripts para facilitar o deploy e desenvolvimento no Raspberry Pi.

### 📋 Scripts Principais

#### `deploy_raspberry.py`
Script principal de deploy automatizado para Raspberry Pi.
```bash
python deploy_raspberry.py
```
**Funcionalidades:**
- Para o serviço atual
- Sincroniza código via rsync
- Reinicia o serviço
- Testa a API
- Verifica logs

#### `remote_dev.py`
Interface interativa para desenvolvimento remoto.
```bash
python remote_dev.py
```
**Opções disponíveis:**
1. Testar conexão SSH
2. Configurar chave SSH
3. Sincronizar código
4. Instalar dependências
5. Iniciar aplicação
6. Parar aplicação
7. Verificar status
8. Ver logs
9. Deploy completo

### 🔧 Scripts Especializados

#### Deploy Automatizado
- `deploy_auto.py` - Deploy completamente automatizado
- `deploy_complete.bat` - Script batch para Windows
- `deploy.ps1` - Script PowerShell
- `deploy.bat` - Script batch alternativo

#### Deploy Manual
- `manual_deploy.py` - Deploy com controle manual
- `manual_deploy_fix.py` - Deploy com correções específicas
- `create_dir_and_deploy.py` - Cria diretórios e faz deploy

#### Scripts de Shell
- `deploy_raspberry_commands.sh` - Comandos shell para deploy
- `deploy_raspberry_direct.py` - Deploy direto sem SSH
- `deploy_raspberry_no_sshpass.py` - Deploy sem sshpass
- `deploy_raspberry_simple.sh` - Deploy simplificado

#### Scripts PowerShell
- `deploy_raspberry_ps1.ps1` - Script PowerShell para deploy
- `deploy_simple.ps1` - Script PowerShell simplificado

### 🛠️ Scripts de Configuração

#### Setup do Raspberry
- `setup_raspberry.py` - Configuração inicial do Raspberry
- `setup_raspberry_fixed.py` - Configuração com correções
- `install.sh` - Script de instalação
- `install_midi_deps.py` - Instala dependências MIDI

#### Configuração de Serviço
- `raspmidi.service` - Arquivo de serviço systemd
- `start_raspberry.sh` - Script de inicialização

### 🔍 Scripts de Debug

#### Monitoramento
- `debug_start.py` - Debug da inicialização
- `debug_patches.py` - Debug de patches
- `debug_patch_activation.py` - Debug de ativação de patches
- `debug_patch_creation.py` - Debug de criação de patches
- `debug_patch_data.py` - Debug de dados de patches
- `debug_cache_init.py` - Debug de inicialização do cache
- `debug_cache_status.py` - Debug de status do cache
- `debug_chocolate.py` - Debug do Chocolate MIDI

#### Testes
- `test_palco_flow.py` - Teste do fluxo da tela do palco
- `test_palco_functionality.py` - Teste de funcionalidade do palco
- `test_palco_stability.py` - Teste de estabilidade do palco
- `test_patch_activation.py` - Teste de ativação de patches
- `test_displays.py` - Teste de displays
- `test_chocolate_patch_selection.py` - Teste de seleção de patches do Chocolate

### 🔄 Scripts de Manutenção

#### Banco de Dados
- `copy_db_from_raspberry.py` - Copia banco do Raspberry
- `download_db.py` - Download do banco
- `reset_patches.py` - Reset de patches
- `create_new_patches.py` - Cria novos patches
- `create_test_patches.py` - Cria patches de teste

#### Reinicialização
- `restart_alsa.py` - Reinicia ALSA
- `restart_pi.py` - Reinicia Raspberry Pi
- `restart_usb.py` - Reinicia dispositivos USB

#### Logs e Cache
- `add_debug_logs.js` - Adiciona logs de debug no frontend
- `check_patches_api.js` - Verifica API de patches
- `clear_patches_console.js` - Limpa console de patches
- `fix_infinite_loading.js` - Corrige carregamento infinito
- `fix_navigation.js` - Corrige navegação
- `fix_patch_loading.js` - Corrige carregamento de patches

### 📊 Scripts de Análise

#### Verificação
- `verify_file_update.py` - Verifica atualização de arquivos
- `force_chocolate_reconnect.py` - Força reconexão do Chocolate
- `send_test_file.py` - Envia arquivo de teste

### 🎯 Como Usar os Scripts

#### Deploy Inicial
```bash
# Configuração inicial
python setup_raspberry.py

# Deploy completo
python deploy_raspberry.py
```

#### Desenvolvimento Diário
```bash
# Interface interativa
python remote_dev.py

# Deploy rápido
python deploy_auto.py
```

#### Debug
```bash
# Debug específico
python debug_patches.py

# Teste de funcionalidade
python test_palco_flow.py
```

### ⚙️ Configuração de Deploy

#### Arquivo de Configuração
Crie `raspberry_config.json`:
```json
{
  "ip": "192.168.15.8",
  "user": "matheus",
  "password": "raspberry",
  "remote_dir": "/home/matheus/RaspMIDI",
  "exclude_patterns": [
    "venv/",
    "logs/",
    "__pycache__/",
    "*.pyc"
  ]
}
```

#### Variáveis de Ambiente
- `RASPBERRY_IP` - IP do Raspberry Pi
- `RASPBERRY_USER` - Usuário SSH
- `RASPBERRY_PASS` - Senha SSH (não recomendado)
- `RASPBERRY_DIR` - Diretório remoto

### 🔐 Segurança

#### SSH Keys (Recomendado)
```bash
# Gerar chave SSH
ssh-keygen -t rsa -b 4096 -C "raspmidi@example.com"

# Copiar para Raspberry
ssh-copy-id matheus@192.168.15.8
```

#### Senha (Alternativo)
- Use `sshpass` para automação com senha
- Configure no arquivo de configuração
- **⚠️ Não recomendado para produção**

## 🐛 Troubleshooting

### Problemas Comuns

1. **Dispositivo não detectado**
   - Verifique conexão USB
   - Reinicie o aplicativo
   - Verifique drivers MIDI

2. **Comandos não funcionam**
   - Verifique configuração de dispositivos
   - Teste com monitor MIDI
   - Verifique alimentação externa (Zoom G3X)

3. **Interface não carrega**
   - Verifique se o servidor está rodando
   - Verifique logs de erro
   - Limpe cache do navegador

4. **Problemas de Deploy**
   - Verifique conexão SSH
   - Confirme IP e usuário
   - Verifique permissões de arquivo
   - Use `remote_dev.py` para debug

## 📝 Logs

Os logs são salvos em `logs/` com formato:
```
raspmidi_YYYYMMDD_HHMMSS.log
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**mguande** - [GitHub](https://github.com/mguande)

## 🙏 Agradecimentos

- Comunidade MIDI
- Desenvolvedores das bibliotecas utilizadas
- Testadores e contribuidores

---

**RaspMIDI** - Transformando sua experiência MIDI! 🎵
