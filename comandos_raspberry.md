# Comandos para Raspberry Pi - RaspMIDI

## 🛑 1. Parar Serviços

```bash
# Parar aplicação Flask
pkill -f "python run.py"

# Parar serviço systemd (se existir)
sudo systemctl stop raspmidi

# Verificar se parou
ps aux | grep python
```

## 📁 2. Navegar para o Diretório

```bash
cd /home/matheus/RaspMIDI
pwd
```

## 💾 3. Backup (Opcional)

```bash
# Criar backup com timestamp
mkdir -p backup/$(date +%Y%m%d_%H%M%S)
cp -r app/web/static backup/$(date +%Y%m%d_%H%M%S)/
cp -r logs backup/$(date +%Y%m%d_%H%M%S)/
cp *.json backup/$(date +%Y%m%d_%H%M%S)/
```

## 📥 4. Atualizar do Git

```bash
# Se já tem repositório Git
git stash
git pull origin main

# OU se não tem repositório Git
cd ..
rm -rf RaspMIDI
git clone https://github.com/seu-usuario/RaspMIDI.git
cd RaspMIDI
```

## 🐍 5. Atualizar Dependências Python

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
```

## 🔧 6. Configurar Permissões

```bash
# Adicionar usuário ao grupo audio
sudo usermod -a -G audio matheus

# Configurar permissões de áudio
sudo chmod 666 /dev/snd/*
```

## 📁 7. Criar Diretórios

```bash
mkdir -p logs
mkdir -p app/web/static/css
mkdir -p app/web/static/js
```

## 🚀 8. Iniciar Aplicação

```bash
# Iniciar Flask app
nohup python run.py > logs/app.log 2>&1 &

# Aguardar um pouco
sleep 3
```

## 🔍 9. Verificar Status

```bash
# Verificar se está rodando
ps aux | grep "python run.py"

# Verificar porta
netstat -tlnp | grep 5000

# Ver logs
tail -f logs/app.log
```

## 🌐 10. Testar Acesso

```bash
# Ver IP do Raspberry Pi
hostname -I

# Testar localmente
curl http://localhost:5000
```

## ⚙️ 11. Configurar Serviço Systemd (Opcional)

```bash
# Copiar arquivo de serviço
sudo cp raspmidi.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço
sudo systemctl enable raspmidi

# Iniciar serviço
sudo systemctl start raspmidi
```

## 🔄 Comandos Rápidos

```bash
# Parar e reiniciar rapidamente
pkill -f "python run.py" && nohup python run.py > logs/app.log 2>&1 &

# Ver logs em tempo real
tail -f logs/app.log

# Ver status completo
ps aux | grep python && netstat -tlnp | grep 5000

# Limpar logs antigos
find logs/ -name "*.log" -mtime +7 -delete
```

## 📋 Script Completo

Para executar tudo de uma vez, use o script:

```bash
chmod +x deploy_raspberry_commands.sh
./deploy_raspberry_commands.sh
```

## 🆘 Troubleshooting

```bash
# Se a aplicação não iniciar
tail -20 logs/app.log

# Se a porta estiver ocupada
sudo lsof -i :5000
sudo kill -9 [PID]

# Se houver problema de permissão
sudo chown -R matheus:matheus /home/matheus/RaspMIDI
chmod +x run.py
``` 