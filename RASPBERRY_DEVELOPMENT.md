# 🍓 Desenvolvimento Remoto no Raspberry Pi

Este guia explica como configurar e usar o desenvolvimento remoto para o RaspMIDI no Raspberry Pi.

## 📋 Pré-requisitos

### No seu computador (Windows/Mac/Linux):
- Python 3.8+
- Git
- SSH client
- Cursor IDE (ou VS Code)

### No Raspberry Pi:
- Raspberry Pi OS (Raspbian)
- Python 3.8+
- Conexão de rede (WiFi ou Ethernet)

## 🚀 Configuração Inicial

### 1. Preparar o Raspberry Pi

```bash
# Conectar ao Raspberry Pi via SSH
ssh pi@192.168.4.1

# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-pip python3-venv git

# Clonar o repositório
cd /home/pi
git clone https://github.com/mguande/RaspMIDI.git
cd RaspMIDI

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar SSH sem senha

```bash
# No seu computador, gerar chave SSH (se não existir)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Copiar chave para o Raspberry Pi
ssh-copy-id pi@192.168.4.1
```

### 3. Configurar hotspot WiFi (opcional)

```bash
# No Raspberry Pi
sudo raspi-config
# Interface Options > WiFi > Configure Hotspot
```

## 🔧 Métodos de Desenvolvimento Remoto

### Método 1: SSH Remoto no Cursor

1. **Abrir Cursor**
2. **Instalar extensão "Remote - SSH"**
3. **Conectar ao Raspberry Pi:**
   - `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
   - `pi@192.168.4.1`
4. **Abrir pasta do projeto:**
   - `/home/pi/RaspMIDI`

### Método 2: Sincronização via Script

Use o script `remote_dev.py` para sincronizar código:

```bash
# No seu computador
python remote_dev.py
```

### Método 3: Sincronização via Git

```bash
# Desenvolvimento local
# Fazer alterações no código
git add .
git commit -m "Nova funcionalidade"
git push origin main

# No Raspberry Pi
git pull origin main
```

### Método 4: Sincronização via RSYNC

```bash
# Sincronizar automaticamente
rsync -avz --exclude='venv/' --exclude='__pycache__/' \
  --exclude='*.pyc' --exclude='logs/' \
  ./ pi@192.168.4.1:/home/pi/RaspMIDI/
```

## 🎯 Workflow de Desenvolvimento

### 1. Desenvolvimento Local
```bash
# Fazer alterações no código
# Testar localmente
python run.py
```

### 2. Deploy no Raspberry Pi
```bash
# Usar script de deploy
python remote_dev.py
# Escolher opção 9 (Deploy completo)
```

### 3. Teste Remoto
```bash
# Acessar interface web
http://192.168.4.1:5000

# Verificar logs
ssh pi@192.168.4.1 "tail -f /home/pi/RaspMIDI/logs/raspmidi_*.log"
```

### 4. Debug Remoto
```bash
# Conectar via SSH e verificar status
ssh pi@192.168.4.1
cd /home/pi/RaspMIDI
./start_raspberry.sh
```

## 🐛 Debugging

### Logs em Tempo Real
```bash
# Ver logs da aplicação
ssh pi@192.168.4.1 "tail -f /home/pi/RaspMIDI/logs/raspmidi_*.log"

# Ver logs do sistema
ssh pi@192.168.4.1 "journalctl -u raspmidi -f"
```

### Verificar Status
```bash
# Status da aplicação
ssh pi@192.168.4.1 "cd /home/pi/RaspMIDI && ./start_raspberry.sh --status"

# Verificar dispositivos MIDI
ssh pi@192.168.4.1 "aconnect -l"
```

### Reiniciar Aplicação
```bash
# Parar aplicação
ssh pi@192.168.4.1 "pkill -f 'python.*run.py'"

# Iniciar aplicação
ssh pi@192.168.4.1 "cd /home/pi/RaspMIDI && ./start_raspberry.sh"
```

## 🔄 Automação

### Script de Deploy Automático
```bash
# Criar script de deploy
cat > deploy.sh << 'EOF'
#!/bin/bash
echo "🔄 Deploying to Raspberry Pi..."
rsync -avz --exclude='venv/' --exclude='__pycache__/' \
  --exclude='*.pyc' --exclude='logs/' \
  ./ pi@192.168.4.1:/home/pi/RaspMIDI/
ssh pi@192.168.4.1 "cd /home/pi/RaspMIDI && \
  source venv/bin/activate && \
  pip install -r requirements.txt && \
  pkill -f 'python.*run.py' && \
  nohup python run.py > logs/raspmidi_\$(date +%Y%m%d_%H%M%S).log 2>&1 &"
echo "✅ Deploy completed!"
EOF

chmod +x deploy.sh
```

### Git Hooks
```bash
# Criar hook para deploy automático
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
echo "🔄 Auto-deploying to Raspberry Pi..."
./deploy.sh
EOF

chmod +x .git/hooks/post-commit
```

## 📱 Acesso Remoto

### Via WiFi Hotspot
1. Conectar ao WiFi "RaspMIDI" (senha: raspmidi123)
2. Acessar: `http://192.168.4.1:5000`

### Via Rede Local
1. Conectar Raspberry Pi à rede WiFi
2. Descobrir IP: `ssh pi@192.168.4.1 "hostname -I"`
3. Acessar: `http://[IP_DO_RASPBERRY]:5000`

### Via Internet (com port forwarding)
1. Configurar port forwarding no roteador
2. Acessar: `http://[IP_PUBLICO]:5000`

## 🔧 Configurações Avançadas

### Configurar Inicialização Automática
```bash
# Criar serviço systemd
sudo tee /etc/systemd/system/raspmidi.service << EOF
[Unit]
Description=RaspMIDI Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaspMIDI
Environment=PATH=/home/pi/RaspMIDI/venv/bin
ExecStart=/home/pi/RaspMIDI/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar serviço
sudo systemctl daemon-reload
sudo systemctl enable raspmidi
sudo systemctl start raspmidi
```

### Configurar Monitoramento
```bash
# Instalar htop para monitoramento
sudo apt install -y htop

# Monitorar recursos
ssh pi@192.168.4.1 "htop"
```

### Configurar Backup Automático
```bash
# Criar script de backup
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/raspmidi_$DATE.tar.gz /home/pi/RaspMIDI
echo "Backup created: $BACKUP_DIR/raspmidi_$DATE.tar.gz"
EOF

chmod +x backup.sh
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **SSH não conecta**
   ```bash
   # Verificar se SSH está habilitado
   sudo raspi-config
   # Interface Options > SSH > Enable
   ```

2. **Aplicação não inicia**
   ```bash
   # Verificar logs
   ssh pi@192.168.4.1 "tail -f /home/pi/RaspMIDI/logs/raspmidi_*.log"
   
   # Verificar dependências
   ssh pi@192.168.4.1 "cd /home/pi/RaspMIDI && source venv/bin/activate && pip list"
   ```

3. **Dispositivos MIDI não detectados**
   ```bash
   # Verificar permissões
   ssh pi@192.168.4.1 "sudo usermod -a -G audio pi"
   
   # Verificar dispositivos
   ssh pi@192.168.4.1 "aconnect -l"
   ```

4. **Porta 5000 não acessível**
   ```bash
   # Verificar firewall
   ssh pi@192.168.4.1 "sudo ufw status"
   
   # Verificar se aplicação está rodando
   ssh pi@192.168.4.1 "netstat -tlnp | grep :5000"
   ```

## 📚 Recursos Adicionais

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Python venv](https://docs.python.org/3/library/venv.html)
- [SSH Configuration](https://www.openssh.com/manual.html)
- [Systemd Services](https://systemd.io/)

---

**Dica:** Para desenvolvimento mais eficiente, use o **Método 1 (SSH Remoto no Cursor)** que permite editar código diretamente no Raspberry Pi com todas as funcionalidades do IDE! 🚀 