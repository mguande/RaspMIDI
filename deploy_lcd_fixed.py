#!/usr/bin/env python3
"""
Deploy da versão corrigida do serviço LCD (sem paramiko, só subprocess)
"""

import subprocess
import sys

PI_HOST = '192.168.15.8'
PI_USER = 'matheus'
REMOTE_APP_PATH = '/home/matheus/RaspMIDI/app/'
LOCAL_FILE = 'app/lcd_service_simple_fixed.py'
REMOTE_FILE = REMOTE_APP_PATH + 'lcd_service_improved.py'
SERVICE_NAME = 'raspmidi-lcd-improved.service'


def run_cmd(cmd, desc):
    print(f'\n=== {desc} ===')
    print(f'Comando: {cmd}')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


def main():
    print('=== DEPLOY LCD FIXED (subprocess) ===')
    # 1. Parar serviço
    run_cmd(f"ssh {PI_USER}@{PI_HOST} 'sudo systemctl stop {SERVICE_NAME}'", 'Parando serviço')
    # 2. Copiar arquivo
    run_cmd(f"scp {LOCAL_FILE} {PI_USER}@{PI_HOST}:{REMOTE_FILE}", 'Copiando arquivo')
    # 3. Backup do arquivo anterior (opcional)
    run_cmd(f"ssh {PI_USER}@{PI_HOST} 'cp {REMOTE_FILE} {REMOTE_FILE}.backup'", 'Backup do arquivo anterior')
    # 4. Dar permissão de execução
    run_cmd(f"ssh {PI_USER}@{PI_HOST} 'chmod +x {REMOTE_FILE}'", 'Definindo permissões')
    # 5. Reiniciar serviço
    run_cmd(f"ssh {PI_USER}@{PI_HOST} 'sudo systemctl restart {SERVICE_NAME}'", 'Reiniciando serviço')
    # 6. Verificar status
    run_cmd(f"ssh {PI_USER}@{PI_HOST} 'systemctl status {SERVICE_NAME} --no-pager'", 'Status do serviço')
    print('\n=== DEPLOY CONCLUÍDO ===')
    print(f'Para ver os logs em tempo real: ssh {PI_USER}@{PI_HOST} "sudo journalctl -u {SERVICE_NAME} -f"')

if __name__ == '__main__':
    main() 