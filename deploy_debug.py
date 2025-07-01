import os
import subprocess

RASPBERRY_USER = 'matheus'
RASPBERRY_IP = '192.168.15.8'
RASPBERRY_PATH = '/home/matheus/RaspMIDI'
SSH_KEY_PATH = os.path.expanduser('~/.ssh/id_rsa')  # Ajuste se sua chave for diferente

# Lista de arquivos e pastas a serem enviados (ajuste conforme necessário)
FILES_TO_DEPLOY = [
    'app/',
    'run.py',
    'requirements.txt',
    'app/web/static/js/app.js',
    'app/web/static/css/style.css',
    'app/web/templates/',
]

print('🚀 [DEBUG] Deploy em modo debug para Raspberry Pi')

# Envia arquivos para o Raspberry Pi
for item in FILES_TO_DEPLOY:
    print(f'📁 Enviando {item}...')
    subprocess.run([
        'scp',
        '-i', SSH_KEY_PATH,
        '-r',
        item,
        f'{RASPBERRY_USER}@{RASPBERRY_IP}:{RASPBERRY_PATH}/'
    ])
    print(f'✅ {item} enviado com sucesso')

# Comando para iniciar o app em modo debug
start_cmd = (
    f'cd {RASPBERRY_PATH} && '
    'export FLASK_ENV=development && '
    'export FLASK_DEBUG=1 && '
    'source venv/bin/activate && '
    'nohup python run.py > logs/app_debug.log 2>&1 &'
)

print('🔄 Reiniciando aplicação em modo debug...')
subprocess.run([
    'ssh', '-i', SSH_KEY_PATH, f'{RASPBERRY_USER}@{RASPBERRY_IP}',
    f'pkill -f run.py || true && {start_cmd}'
])
print('✅ Aplicação reiniciada em modo debug!')
print('📋 Logs em: logs/app_debug.log no Raspberry Pi') 