// RaspMIDI - Interface Web JavaScript

class RaspMIDI {
    constructor() {
        this.apiBase = '/api';
        this.patches = [];
        this.effects = {};
        this.devices = { inputs: [], outputs: [] };
        this.midiConfig = {};
        this.status = {};
        this._renderingPatches = false;
        this._creatingPatch = false;
        this._updatingPatch = false;
        this._editingPatchId = null; // Controle para modo de edição
        this._patchViewMode = 'cards'; // Adiciona este atributo
        
        // Monitor MIDI
        this.midiMonitor = {
            active: false,
            currentDevice: null,
            commands: [],
            commandCount: 0,
            lastCommand: null,
            maxLines: 100,
            polling: false
        };
        
        // Log de comandos
        this.commandLog = [];
        this.MAX_LOG_ENTRIES = 50;
        
        // Polling MIDI
        this.midiPolling = {
            active: false,
            interval: null,
            lastCheck: null
        };
        
        // Inicializar quando o DOM estiver pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    async init() {
        try {
            console.log("🚀 Iniciando aplicação...");
            await this.loadInitialData();
            this.setupEventListeners();
            this.setupModalListeners();
            this.setupEdicaoMenu(); // Chamado apenas uma vez
            this.startStatusUpdates();
            this.setupPatchListControls(); // Adiciona listeners para ordenação e visualização
            this.setupSysExSection();
            
            console.log("✅ Aplicação inicializada com sucesso");
            
        } catch (error) {
            console.error('❌ Erro ao inicializar aplicação:', error);
        }
    }
    
    async loadInitialData() {
        try {
            // Carrega dados em paralelo
            await Promise.all([
                this.loadPatches(),
                this.loadEffects(),
                this.loadDevices(),
                this.loadMidiConfig(),
                this.loadStatus(),
                this.loadDeviceStatus() // Nova função
            ]);
            
            // Inicia atualizações automáticas
            this.startStatusUpdates();
            this.startMidiPolling();
            
        } catch (error) {
            console.error('Erro ao carregar dados iniciais:', error);
            this.showNotification('Erro ao carregar dados iniciais', 'error');
        }
    }
    
    setupEventListeners() {
        // Botão de recarregar cache
        const reloadBtn = document.getElementById('reload-cache');
        if (reloadBtn) {
            reloadBtn.addEventListener('click', () => this.reloadCache());
        }
        
        // Botão de novo patch
        const newPatchBtn = document.getElementById('new-patch');
        if (newPatchBtn) {
            newPatchBtn.addEventListener('click', () => this.showNewPatchModal());
        }
        
        // Botão de escanear dispositivos
        const scanBtn = document.getElementById('scan-devices');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => this.scanDevices());
        }
        
        // Botão de atualizar dispositivos
        const refreshBtn = document.getElementById('refresh-devices');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDevices());
        }
        
        // Botão de salvar configuração
        const saveConfigBtn = document.getElementById('save-config');
        if (saveConfigBtn) {
            saveConfigBtn.addEventListener('click', () => this.saveMidiConfig());
        }
        
        // Event listeners para modais
        this.setupModalListeners();
        
        // Event listeners para monitoramento MIDI
        document.getElementById('toggle-monitor')?.addEventListener('click', () => {
            this.toggleMidiMonitor();
        });
        
        document.getElementById('clear-monitor')?.addEventListener('click', () => {
            this.clearMidiMonitor();
        });
        
        document.getElementById('clear-midi-monitor')?.addEventListener('click', () => {
            this.clearMidiMonitor();
        });
        
        document.getElementById('simulate-command')?.addEventListener('click', () => {
            this.simulateMidiCommand();
        });
        
        // Inicia polling para comandos MIDI se monitor estiver ativo
        this.startMidiPolling();
        
        // Configura comandos MIDI
        this.setupMidiCommands();
        
        // Event listener para limpar log de comandos
        document.getElementById('clear-command-log')?.addEventListener('click', () => {
            this.clearCommandLog();
        });
        
        // Event listeners para controle de linhas dos logs
        document.getElementById('command-log-lines')?.addEventListener('change', (e) => {
            this.MAX_LOG_ENTRIES = parseInt(e.target.value);
            this.updateCommandLogDisplay();
        });
        
        document.getElementById('midi-monitor-lines')?.addEventListener('change', (e) => {
            this.midiMonitor.maxLines = parseInt(e.target.value);
            this.updateMidiMonitorDisplay();
        });

        // Event listeners para alertas de alimentação
        document.getElementById('test-power-status')?.addEventListener('click', () => {
            this.testPowerStatus();
        });
        
        document.getElementById('dismiss-power-alert')?.addEventListener('click', () => {
            this.dismissPowerAlert();
        });
        
        // Botão para reativar alertas
        document.getElementById('reactivate-alerts')?.addEventListener('click', () => {
            this.reactivateAlerts();
        });
        
        // Botão para reconectar Chocolate
        document.getElementById('reconnect-chocolate')?.addEventListener('click', () => {
            this.reconnectChocolate();
        });

        // Botão para atualizar status dos dispositivos
        document.getElementById('refresh-device-status')?.addEventListener('click', () => {
            this.loadDeviceStatus();
        });

        // Event listeners para combos de dispositivos
        document.getElementById('input-device')?.addEventListener('change', async (e) => {
            console.log('🎹 Combo input-device mudou para:', e.target.value);
            this.midiConfig.input_device = e.target.value;
            await this.saveMidiConfig();
            this.renderDevices();
        });
        
        document.getElementById('output-device')?.addEventListener('change', async (e) => {
            console.log('🎹 Combo output-device mudou para:', e.target.value);
            this.midiConfig.output_device = e.target.value;
            await this.saveMidiConfig();
            this.renderDevices();
        });

        // Menu de navegação do modo edição
        this.setupEdicaoMenu();

        // === Comandos SysEx Zoom ===
        function getSelectedOutputDeviceName() {
            const select = document.getElementById('output-device-select');
            return select ? select.value : null;
        }

        document.getElementById('btn-zoom-tuner-on')?.addEventListener('click', async () => {
            const device = getSelectedOutputDeviceName();
            if (!device) return showNotification('Selecione um dispositivo de saída!', 'warning');
            await sendZoomTuner(device, true);
        });
        document.getElementById('btn-zoom-tuner-off')?.addEventListener('click', async () => {
            const device = getSelectedOutputDeviceName();
            if (!device) return showNotification('Selecione um dispositivo de saída!', 'warning');
            await sendZoomTuner(device, false);
        });
        async function sendZoomTuner(device, enabled = true) {
            try {
                const resp = await fetch('/api/midi/sysex/tuner', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        device: device,
                        enabled: enabled 
                    })
                });
                const data = await resp.json();
                if (data.success) {
                    showNotification(data.message || `Afinador ${enabled ? 'ligado' : 'desligado'}!`, 'success');
                } else {
                    showNotification('Erro ao controlar afinador: ' + data.error, 'error');
                }
            } catch (e) {
                showNotification('Erro ao controlar afinador: ' + e.message, 'error');
            }
        }

        document.getElementById('btn-zoom-select-patch')?.addEventListener('click', async () => {
            const device = getSelectedOutputDeviceName();
            const patch = parseInt(document.getElementById('zoom-patch-number').value);
            if (!device) return showNotification('Selecione um dispositivo de saída!', 'warning');
            if (isNaN(patch) || patch < 10 || patch > 59) return showNotification('Patch inválido (10-59)', 'warning');
            try {
                const resp = await fetch('/api/midi/sysex/patch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device, patch })
                });
                const data = await resp.json();
                if (data.success) showNotification('Patch selecionado!', 'success');
                else showNotification('Erro ao selecionar patch: ' + data.error, 'error');
            } catch (e) {
                showNotification('Erro ao selecionar patch', 'error');
            }
        });

        document.getElementById('btn-zoom-effect-on')?.addEventListener('click', async () => {
            const device = getSelectedOutputDeviceName();
            const block = parseInt(document.getElementById('zoom-effect-block').value);
            if (!device) return showNotification('Selecione um dispositivo de saída!', 'warning');
            await sendZoomEffect(device, block, 1);
        });
        document.getElementById('btn-zoom-effect-off')?.addEventListener('click', async () => {
            const device = getSelectedOutputDeviceName();
            const block = parseInt(document.getElementById('zoom-effect-block').value);
            if (!device) return showNotification('Selecione um dispositivo de saída!', 'warning');
            await sendZoomEffect(device, block, 0);
        });
        async function sendZoomEffect(device, block, state) {
            try {
                const resp = await fetch('/api/midi/sysex/effect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device, block, state })
                });
                const data = await resp.json();
                if (data.success) {
                    showNotification(data.message || `Bloco de efeito ${block} ${state ? 'ligado' : 'desligado'}!`, 'success');
                } else {
                    showNotification('Erro ao controlar bloco de efeito: ' + data.error, 'error');
                }
            } catch (e) {
                showNotification('Erro ao controlar bloco de efeito: ' + e.message, 'error');
            }
        }
    }
    
    setupModalListeners() {
        // Fechar modais
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal') || e.target.classList.contains('modal-close')) {
                this.closeModal(e.target.closest('.modal'));
            }
        });
        
        // Form de novo patch
        const newPatchForm = document.getElementById('new-patch-form');
        if (newPatchForm) {
            newPatchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                
                // Verifica se estamos em modo de edição
                if (this._editingPatchId) {
                    console.log(`🔧 Submit do formulário em modo de edição, chamando updatePatch(${this._editingPatchId})`);
                    this.updatePatch(this._editingPatchId);
                } else {
                    console.log('🔧 Submit do formulário em modo de criação, chamando createPatch()');
                    this.createPatch();
                }
            });
        }
    }
    
    async loadPatches() {
        // Evita carregamentos simultâneos
        if (this._loadingPatches) {
            console.log("⚠️ Patches já estão sendo carregados, ignorando chamada dupla");
            return;
        }
        
        this._loadingPatches = true;
        
        try {
            console.log("🔄 Carregando patches...");
            
            const response = await fetch(`${this.apiBase}/patches`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Valida se data.data é um array
                if (!Array.isArray(data.data)) {
                    console.error("❌ Dados de patches não são um array:", data.data);
                    this.patches = [];
                } else {
                    this.patches = data.data;
                    console.log(`✅ ${this.patches.length} patches carregados`);
                }
                
                // Renderiza patches com timeout de segurança
                try {
                    await Promise.race([
                        this.renderPatches(),
                        new Promise((_, reject) => 
                            setTimeout(() => reject(new Error('Render timeout')), 3000)
                        )
                    ]);
                } catch (error) {
                    console.error("❌ Erro ao renderizar patches:", error);
                    // Continua mesmo com erro de renderização
                }
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('❌ Erro ao carregar patches:', error);
            this.showNotification('Erro ao carregar patches: ' + error.message, 'error');
            // Em caso de erro, define patches como array vazio para evitar travamento
            this.patches = [];
        } finally {
            this._loadingPatches = false;
        }
    }
    
    async loadEffects() {
        try {
            const response = await fetch(`${this.apiBase}/effects`);
            const data = await response.json();
            
            if (data.success) {
                this.effects = data.data;
                this.renderEffects();
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao carregar efeitos:', error);
            this.showNotification('Erro ao carregar efeitos', 'error');
        }
    }
    
    async loadDevices() {
        try {
            const response = await fetch(`${this.apiBase}/midi/devices/list`);
            const data = await response.json();
            
            if (data.success) {
                this.devices = data.data;
                this.renderDevices();
                this.populateAllDeviceSelects(); // Centraliza a população dos selects
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao carregar dispositivos:', error);
            this.showNotification('Erro ao carregar dispositivos', 'error');
        }
    }
    
    async loadMidiConfig() {
        try {
            const response = await fetch(`${this.apiBase}/midi/config`);
            const data = await response.json();
            
            if (data.success) {
                this.midiConfig = data.data;
                this.renderMidiConfig();
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao carregar configuração MIDI:', error);
            this.showNotification('Erro ao carregar configuração MIDI', 'error');
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            const data = await response.json();
            
            if (data.success) {
                this.status = data.data;
                this.updateStatusDisplay();
                
                // Verifica se há alertas de alimentação
                this.checkPowerAlerts();
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao carregar status:', error);
        }
    }
    
    async loadDeviceStatus() {
        try {
            const response = await fetch(`${this.apiBase}/midi/devices/status_detailed`);
            const data = await response.json();
            
            if (data.success) {
                this.renderDeviceStatus(data.data);
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao carregar status dos dispositivos:', error);
            this.showNotification('Erro ao carregar status dos dispositivos', 'error');
        }
    }
    
    renderDeviceStatus(devices) {
        const container = document.getElementById('device-status-container');
        if (!container) return;
        
        if (!Array.isArray(devices) || devices.length === 0) {
            container.innerHTML = `
                <div class="text-center">
                    <p>Nenhum dispositivo encontrado</p>
                </div>
            `;
            return;
        }
        
        const devicesHtml = devices.map(device => {
            const statusClass = device.connected ? 'connected' : 'disconnected';
            const statusText = device.connected ? 'Conectado' : 'Desconectado';
            const lastPc = device.last_pc !== null && device.last_pc !== undefined ? device.last_pc : '-';
            const statusDetails = device.status_details || 'Status desconhecido';
            
            // Botão de reconexão apenas se desconectado
            let reconnectBtn = '';
            if (!device.connected) {
                if (device.type === 'zoom_g3x') {
                    reconnectBtn = `
                        <button class="reconnect-device-btn" onclick="window.app.reconnectZoomG3X()">
                            Reconectar Zoom G3X
                        </button>
                    `;
                } else if (device.type === 'chocolate') {
                    reconnectBtn = `
                        <button class="reconnect-device-btn" onclick="window.app.reconnectChocolate()">
                            Reconectar Chocolate
                        </button>
                    `;
                }
            }
            
            return `
                <div class="device-status-card ${statusClass}">
                    <div class="device-status-header">
                        <div class="device-status-name">${device.name}</div>
                        <div class="device-status-indicator ${statusClass}"></div>
                    </div>
                    <div class="device-status-details">
                        <div class="device-status-item">
                            <div class="device-status-label">Status</div>
                            <div class="device-status-value">${statusText}</div>
                        </div>
                        <div class="device-status-item">
                            <div class="device-status-label">Porta</div>
                            <div class="device-status-value port">${device.port || '-'}</div>
                        </div>
                        <div class="device-status-item">
                            <div class="device-status-label">Último PC</div>
                            <div class="device-status-value last-pc">${lastPc}</div>
                        </div>
                        <div class="device-status-item">
                            <div class="device-status-label">Tipo</div>
                            <div class="device-status-value">${device.type || '-'}</div>
                        </div>
                    </div>
                    <div class="device-status-info">
                        <div class="device-status-label">Detalhes</div>
                        <div class="device-status-value details">${statusDetails}</div>
                    </div>
                    ${reconnectBtn ? `<div class="device-status-actions">${reconnectBtn}</div>` : ''}
                </div>
            `;
        }).join('');
        
        container.innerHTML = `
            <div class="device-status-grid">
                ${devicesHtml}
            </div>
        `;
    }
    
    async checkPowerAlerts() {
        try {
            // Verifica se o usuário descartou o alerta nesta sessão
            const alertDismissed = localStorage.getItem('powerAlertDismissed');
            if (alertDismissed === 'true') {
                return; // Não mostra o alerta se foi descartado
            }
            
            const response = await fetch(`${this.apiBase}/midi/devices/power_status`);
            const data = await response.json();
            
            if (data.success) {
                const status = data.data;
                
                // Verifica se há dispositivos que precisam de alimentação externa
                const needsExternalPower = this.checkDevicesPowerStatus(status);
                
                if (needsExternalPower) {
                    this.showPowerAlert(needsExternalPower);
                } else {
                    this.hidePowerAlert();
                }
            }
        } catch (error) {
            console.error('Erro ao verificar alertas de alimentação:', error);
        }
    }
    
    checkDevicesPowerStatus(status) {
        const devices = [];
        
        // Verifica Zoom G3X
        if (status.zoom_g3x && !status.zoom_g3x.connected) {
            devices.push('Zoom G3X');
        }
        
        // Verifica Chocolate
        if (status.chocolate && !status.chocolate.connected) {
            devices.push('Chocolate');
        }
        
        return devices.length > 0 ? devices : null;
    }
    
    showPowerAlert(devices) {
        const alertContainer = document.getElementById('power-alerts');
        const alertMessage = document.getElementById('power-alert-message');
        
        if (alertContainer && alertMessage) {
            const deviceList = devices.join(', ');
            alertMessage.textContent = `Os seguintes dispositivos podem precisar de alimentação externa: ${deviceList}. Conecte a alimentação externa e tente novamente.`;
            alertContainer.style.display = 'block';
        }
    }
    
    hidePowerAlert() {
        const alertContainer = document.getElementById('power-alerts');
        if (alertContainer) {
            alertContainer.style.display = 'none';
        }
    }
    
    renderPatches() {
        try {
            if (this._renderingPatches) return;
            this._renderingPatches = true;
            const container = document.getElementById('patches-container');
            if (!container) { this._renderingPatches = false; return; }
            if (!Array.isArray(this.patches)) this.patches = [];
            if (this.patches.length === 0) {
                container.innerHTML = `<div class="card text-center"><p>Nenhum patch encontrado. Crie seu primeiro patch!</p><button class="btn btn-primary" onclick="app.showNewPatchModal()">Criar Patch</button></div>`;
                this._renderingPatches = false; return;
            }
            // Ordenação
            const sortCombo = document.getElementById('patch-sort-mode');
            let patches = [...this.patches];
            let sortMode = sortCombo ? sortCombo.value : 'input';
            if (sortMode === 'input') {
                patches.sort((a, b) => (a.input_channel ?? 999) - (b.input_channel ?? 999));
            } else if (sortMode === 'output') {
                patches.sort((a, b) => {
                    if ((a.zoom_bank || '') < (b.zoom_bank || '')) return -1;
                    if ((a.zoom_bank || '') > (b.zoom_bank || '')) return 1;
                    return (a.zoom_patch ?? 999) - (b.zoom_patch ?? 999);
                });
            } else if (sortMode === 'created') {
                patches.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
            }
            // Visualização
            const viewMode = this._patchViewMode || 'cards';
            if (viewMode === 'list') {
                container.innerHTML = `<table class="patch-list-table" style="width:100%;background:#1a1e2a;color:#fff;border-radius:8px;overflow:hidden;"><thead><tr><th>Nome</th><th>Canal Entrada</th><th>Dispositivo Entrada</th><th>Banco/Patch Saída</th><th>Dispositivo Saída</th><th>Ações</th></tr></thead><tbody>${patches.map(patch => this.createPatchListRow(patch)).join('')}</tbody></table>`;
            } else {
                const patchesHtml = patches.map(patch => this.createPatchCard(patch)).join('');
                container.innerHTML = `<div class="patches-grid">${patchesHtml}</div>`;
            }
            this._renderingPatches = false;
        } catch (error) {
            this._renderingPatches = false;
            const container = document.getElementById('patches-container');
            if (container) {
                container.innerHTML = `<div class="card text-center error"><p>Erro ao carregar patches: ${error.message}</p><button class="btn btn-primary" onclick="app.loadPatches()">Tentar Novamente</button></div>`;
            }
        }
    }
    
    createPatchCard(patch) {
        // Determina o tipo de comando para exibição
        let commandTypeText = 'Desconhecido';
        let commandDetails = '';
        let commandIcon = '❓';
        
        if (patch.command_type === 'pc') {
            commandTypeText = 'Program Change';
            commandIcon = '🎸';
            if (patch.zoom_bank && patch.program !== undefined) {
                commandDetails = `<i class="fas fa-layer-group"></i> ${patch.zoom_bank} <i class="fas fa-music"></i> ${patch.program}`;
            } else if (patch.program !== undefined) {
                commandDetails = `<i class="fas fa-music"></i> Programa ${patch.program}`;
            }
        } else if (patch.command_type === 'cc') {
            commandTypeText = 'Control Change';
            commandIcon = '🎛️';
            if (patch.cc !== undefined && patch.value !== undefined) {
                commandDetails = `<i class="fas fa-sliders-h"></i> CC${patch.cc} = ${patch.value}`;
            }
        } else if (patch.command_type === 'note_on') {
            commandTypeText = 'Note On';
            commandIcon = '🎵';
            if (patch.note !== undefined && patch.velocity !== undefined) {
                commandDetails = `<i class="fas fa-music"></i> Nota ${patch.note} <i class="fas fa-tachometer-alt"></i> Velocidade ${patch.velocity}`;
            }
        } else if (patch.command_type === 'note_off') {
            commandTypeText = 'Note Off';
            commandIcon = '🔇';
            if (patch.note !== undefined) {
                commandDetails = `<i class="fas fa-music"></i> Nota ${patch.note}`;
            }
        } else if (patch.command_type === 'effects_config') {
            commandTypeText = 'Configuração de Efeitos';
            commandIcon = '🎚️';
            if (patch.zoom_bank && patch.program !== undefined) {
                commandDetails = `<i class="fas fa-layer-group"></i> ${patch.zoom_bank} <i class="fas fa-music"></i> ${patch.program}`;
            }
        }
        
        // Cria as caixas de entrada e saída
        const inputBox = `
            <div class="patch-info-box input-box">
                <div class="box-header">
                    <i class="fas fa-sign-in-alt"></i>
                    Entrada
                </div>
                <div class="box-content">
                    <div class="device-info">
                        ${patch.input_device || 'N/A'}
                    </div>
                    ${patch.input_channel !== undefined ? `<div class="channel-info"><i class="fas fa-hashtag"></i> ${patch.input_channel}</div>` : ''}
                </div>
            </div>
        `;
        
        const outputBox = `
            <div class="patch-info-box output-box">
                <div class="box-header">
                    <i class="fas fa-sign-out-alt"></i>
                    Saída
                </div>
                <div class="box-content">
                    <div class="device-info">
                        ${patch.output_device || 'N/A'}
                    </div>
                    ${commandDetails ? `<div class="command-info">${commandDetails}</div>` : ''}
                </div>
            </div>
        `;
        
        // Cria os efeitos apenas para patches de configuração de efeitos
        let effectsHtml = '';
        if (patch.command_type === 'effects_config' && patch.effects) {
            const effects = Object.keys(patch.effects).map(effect => {
                const enabled = patch.effects[effect].enabled;
                // Extrai o número do efeito (effect_1 -> 1, effect_2 -> 2, etc.)
                const effectNumber = effect.replace('effect_', '');
                return `
                    <div class="patch-effect-box ${enabled ? 'enabled' : 'disabled'}">
                        <div class="patch-effect-label">FX ${effectNumber}</div>
                    </div>
                `;
            }).join('');
            
            if (effects) {
                effectsHtml = `
                    <div class="patch-effects-section">
                        <div class="effects-section-title">Efeitos</div>
                        <div class="patch-effects-grid">
                            ${effects}
                        </div>
                    </div>
                `;
            }
        }
        
        return `
            <div class="patch-card ${patch.command_type}">
                <div class="patch-header">
                    <div class="patch-name">${patch.name}</div>
                    <div class="patch-command-type">
                        <i>${commandIcon}</i>
                        ${commandTypeText}
                    </div>
                </div>
                <div class="patch-info-grid">
                    ${inputBox}
                    ${outputBox}
                </div>
                ${effectsHtml}
                <div class="patch-actions">
                    <button class="btn btn-success btn-small" onclick="app.loadPatch(${patch.id})">
                        <i class="fas fa-play"></i>
                        Carregar
                    </button>
                    <button class="btn btn-primary btn-small" onclick="app.editPatch(${patch.id})">
                        <i class="fas fa-edit"></i>
                        Editar
                    </button>
                    <button class="btn btn-danger btn-small" onclick="app.deletePatch(${patch.id})">
                        <i class="fas fa-trash"></i>
                        Deletar
                    </button>
                    <button class="btn btn-info btn-small" title="Carregar Patch" onclick="app.activatePatch(${patch.id})"><i class="fas fa-play"></i></button>
                </div>
            </div>
        `;
    }
    
    renderEffects() {
        const container = document.getElementById('effects-container');
        if (!container) return;
        
        const effectsHtml = Object.entries(this.effects).map(([key, effect]) => `
            <div class="effect-item" data-effect="${key}">
                <div class="effect-name">${effect.name}</div>
                <div class="effect-toggle">
                    <div class="toggle-switch" onclick="app.toggleEffect('${key}')"></div>
                    <span>Ligado/Desligado</span>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = `
            <div class="effects-panel">
                ${effectsHtml}
            </div>
        `;
    }
    
    renderDevices() {
        // Carrega a configuração MIDI antes de renderizar para ter os valores selecionados
        this.loadMidiConfig().then(() => {
            // Categoriza dispositivos por tipo (USB/Bluetooth) baseado no nome
            const usbDevices = [];
            const bluetoothDevices = [];
            
            // Processa dispositivos de entrada
            const inputDevices = this.devices.inputs || [];
            inputDevices.forEach(device => {
                const deviceInfo = {
                    ...device,
                    type: 'input',
                    connected: false // Será determinado pelo status real
                };
                
                if (device.real_name.toLowerCase().includes('bt') || device.real_name.toLowerCase().includes('bluetooth')) {
                    bluetoothDevices.push(deviceInfo);
                } else {
                    usbDevices.push(deviceInfo);
                }
            });
            
            // Processa dispositivos de saída
            const outputDevices = this.devices.outputs || [];
            outputDevices.forEach(device => {
                const deviceInfo = {
                    ...device,
                    type: 'output',
                    connected: false // Será determinado pelo status real
                };
                
                if (device.real_name.toLowerCase().includes('bt') || device.real_name.toLowerCase().includes('bluetooth')) {
                    bluetoothDevices.push(deviceInfo);
                } else {
                    usbDevices.push(deviceInfo);
                }
            });
            
            // Renderiza dispositivos USB
            const usbContainer = document.getElementById('usb-devices');
            if (usbContainer) {
                if (usbDevices.length === 0) {
                    usbContainer.innerHTML = '<p class="text-center">Nenhum dispositivo USB encontrado</p>';
                } else {
                    const usbHtml = usbDevices.map(device => this.createDeviceCard(device)).join('');
                    usbContainer.innerHTML = usbHtml;
                }
            }
            
            // Renderiza dispositivos Bluetooth
            const btContainer = document.getElementById('bluetooth-devices');
            if (btContainer) {
                if (bluetoothDevices.length === 0) {
                    btContainer.innerHTML = '<p class="text-center">Nenhum dispositivo Bluetooth encontrado</p>';
                } else {
                    const btHtml = bluetoothDevices.map(device => this.createDeviceCard(device)).join('');
                    btContainer.innerHTML = btHtml;
                }
            }
        });
    }
    
    createDeviceCard(device) {
        const isConnected = device.connected;
        const statusClass = isConnected ? 'connected' : 'disconnected';
        const statusText = isConnected ? 'Conectado' : 'Desconectado';
        
        // Verifica se o dispositivo está selecionado na configuração MIDI
        const isSelectedAsInput = this.midiConfig.input_device === device.name;
        const isSelectedAsOutput = this.midiConfig.output_device === device.name;
        const isSelected = isSelectedAsInput || isSelectedAsOutput;
        
        // Define cor de fundo e ícone baseado no tipo de dispositivo
        let deviceClass = '';
        let deviceIcon = '';
        
        if (device.type === 'input') {
            deviceClass = 'device-input';
            deviceIcon = '📥'; // Ícone de entrada
        } else if (device.type === 'output') {
            deviceClass = 'device-output';
            deviceIcon = '📤'; // Ícone de saída
        }
        
        // Ícones FontAwesome para entrada/saída
        const iconIn = '<i class="fa fa-sign-in-alt"></i>';
        const iconOut = '<i class="fa fa-sign-out-alt"></i>';
        const badgeType = device.type === 'input'
            ? `<span class="badge input">${iconIn} <span style=\"font-size:0.8em;\">IN</span></span>`
            : `<span class="badge output">${iconOut} <span style=\"font-size:0.8em;\">OUT</span></span>`;
        const statusDot = `<span class="status-dot ${statusClass}"></span>`;
        // Botão de seleção padrão
        let buttonHtml = '';
        if (isSelected) {
            buttonHtml = `<button class='select-btn selected' disabled><i class='fa fa-check'></i> Selecionado</button>`;
        } else {
            buttonHtml = `<button class='select-btn' onclick=\"app.selectDevice('${device.name}', '${device.type}')\"><i class='fa fa-mouse-pointer'></i> Selecionar</button>`;
        }
        return `
            <div class="device-card ${statusClass} ${isSelected ? 'selected' : ''}">
                <div class="device-header">
                    <span class="device-name" style="white-space:normal;">${device.real_name || device.name}</span>
                    ${statusDot}
                    ${badgeType}
                </div>
                <div class="device-details">${device.port || ''}</div>
                ${buttonHtml}
            </div>
        `;
    }
    
    renderMidiConfig() {
        // Preenche selects de entrada e saída
        const inputSelect = document.getElementById('input-device');
        const outputSelect = document.getElementById('output-device');
        
        if (inputSelect) {
            inputSelect.innerHTML = '<option value="">Selecione...</option>';
            // Usa a estrutura correta: inputs e outputs
            const inputDevices = this.devices.inputs || [];
            inputDevices.forEach(device => {
                const selected = device.name === this.midiConfig.input_device ? 'selected' : '';
                inputSelect.innerHTML += `<option value="${device.name}" ${selected}>${device.name}</option>`;
            });
        }
        
        if (outputSelect) {
            outputSelect.innerHTML = '<option value="">Selecione...</option>';
            // Usa a estrutura correta: inputs e outputs
            const outputDevices = this.devices.outputs || [];
            outputDevices.forEach(device => {
                const selected = device.name === this.midiConfig.output_device ? 'selected' : '';
                outputSelect.innerHTML += `<option value="${device.name}" ${selected}>${device.name}</option>`;
            });
        }
        
        // Não chama renderDevices() aqui para evitar duplicação
        // renderDevices() já é chamada em loadDevices()
    }
    
    updateStatusDisplay() {
        // Atualiza indicadores de status
        const midiStatus = document.getElementById('midi-status');
        const cacheStatus = document.getElementById('cache-status');
        
        if (midiStatus) {
            const connected = this.status.midi?.connected || false;
            midiStatus.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
            midiStatus.nextElementSibling.textContent = connected ? 'MIDI Conectado' : 'MIDI Desconectado';
        }
        
        if (cacheStatus) {
            const loaded = this.status.cache?.loaded || false;
            cacheStatus.className = `status-indicator ${loaded ? 'connected' : 'disconnected'}`;
            cacheStatus.nextElementSibling.textContent = loaded ? 'Cache Carregado' : 'Cache Vazio';
        }
    }
    
    async reloadCache() {
        try {
            const button = document.getElementById('reload-cache');
            const originalText = button.textContent;
            
            button.innerHTML = '<span class="loading"></span> Recarregando...';
            button.disabled = true;
            
            const response = await fetch(`${this.apiBase}/cache/reload`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Cache recarregado com sucesso', 'success');
                await this.loadInitialData();
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao recarregar cache:', error);
            this.showNotification('Erro ao recarregar cache', 'error');
        } finally {
            const button = document.getElementById('reload-cache');
            button.textContent = 'Recarregar Cache';
            button.disabled = false;
        }
    }
    
    async loadPatch(patchId) {
        try {
            const response = await fetch(`${this.apiBase}/midi/patch/load`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ patch_id: patchId })
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Patch ${data.data.name} carregado!`, 'success');
                this.currentPatch = data.data;
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao carregar patch:', error);
            this.showNotification('Erro ao carregar patch', 'error');
        }
    }
    
    async toggleEffect(effectName) {
        try {
            const effectItem = document.querySelector(`[data-effect="${effectName}"]`);
            const toggle = effectItem.querySelector('.toggle-switch');
            const isActive = toggle.classList.contains('active');
            
            const response = await fetch(`${this.apiBase}/midi/effect/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    effect_name: effectName,
                    enabled: !isActive
                })
            });
            const data = await response.json();
            
            if (data.success) {
                toggle.classList.toggle('active');
                effectItem.classList.toggle('active');
                this.showNotification(data.message, 'success');
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao alternar efeito:', error);
            this.showNotification('Erro ao alternar efeito', 'error');
        }
    }
    
    async scanDevices() {
        try {
            const button = document.getElementById('scan-devices');
            const originalText = button.textContent;
            
            button.innerHTML = '<span class="loading"></span> Escaneando...';
            button.disabled = true;
            
            const response = await fetch(`${this.apiBase}/midi/devices/scan`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Dispositivos escaneados', 'success');
                await this.loadDevices();
                await this.loadMidiConfig();
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao escanear dispositivos:', error);
            this.showNotification('Erro ao escanear dispositivos', 'error');
        } finally {
            const button = document.getElementById('scan-devices');
            button.textContent = 'Escanear Dispositivos';
            button.disabled = false;
        }
    }
    
    async saveMidiConfig() {
        try {
            const inputDevice = document.getElementById('input-device').value;
            const outputDevice = document.getElementById('output-device').value;
            
            const config = {
                input_device: inputDevice || null,
                output_device: outputDevice || null
            };
            
            const response = await fetch(`${this.apiBase}/midi/config`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Configuração MIDI salva com sucesso', 'success');
                this.midiConfig = data.data;
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao salvar configuração MIDI:', error);
            this.showNotification('Erro ao salvar configuração MIDI', 'error');
        }
    }
    
    async selectDevice(deviceName, deviceType) {
        try {
            console.log(`🎹 Selecionando dispositivo: ${deviceName} (${deviceType})`);
            
            if (deviceType === 'input') {
                const inputSelect = document.getElementById('input-device');
                if (inputSelect) {
                    inputSelect.value = deviceName;
                }
                // Atualiza a configuração MIDI
                this.midiConfig.input_device = deviceName;
            } else if (deviceType === 'output') {
                const outputSelect = document.getElementById('output-device');
                if (outputSelect) {
                    outputSelect.value = deviceName;
                }
                // Atualiza a configuração MIDI
                this.midiConfig.output_device = deviceName;
            }
            
            // Salva a configuração no backend
            console.log('🎹 Salvando configuração MIDI...');
            await this.saveMidiConfig();
            
            // Recarrega os dispositivos para atualizar o estado dos botões
            this.renderDevices();
            
            this.showNotification(`Dispositivo ${deviceName} selecionado e salvo`, 'success');
            
        } catch (error) {
            console.error('❌ Erro ao selecionar dispositivo:', error);
            this.showNotification('Erro ao selecionar dispositivo', 'error');
        }
    }
    
    showNewPatchModal() {
        const modal = document.getElementById('new-patch-modal');
        if (!modal) {
            console.warn('Modal new-patch-modal não encontrado');
            return;
        }
        
        // Sempre restaura o botão para modo de criação
        const submitButton = document.querySelector('#new-patch-modal .btn-success');
        if (submitButton) {
            submitButton.textContent = 'Criar Patch';
            // Remove onclick manual, deixa o submit do formulário cuidar disso
            submitButton.onclick = null;
        }
        
        // Restaura o título do modal
        const modalTitle = document.querySelector('#new-patch-modal .modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Novo Patch';
        }
        
        // Preencher selects de dispositivos
        const inputSelect = document.getElementById('patch-input-device');
        const outputSelect = document.getElementById('patch-output-device');
        
        if (inputSelect) {
            inputSelect.innerHTML = '<option value="">Selecione...</option>';
            (this.devices.inputs || []).forEach(device => {
                const selected = device.name === this.midiConfig.input_device ? 'selected' : '';
                inputSelect.innerHTML += `<option value="${device.name}" ${selected}>${device.name}</option>`;
            });
        }
        
        if (outputSelect) {
            outputSelect.innerHTML = '<option value="">Selecione...</option>';
            (this.devices.outputs || []).forEach(device => {
                const selected = device.name === this.midiConfig.output_device ? 'selected' : '';
                outputSelect.innerHTML += `<option value="${device.name}" ${selected}>${device.name}</option>`;
            });
        }
        
        // Limpar campos
        const nameField = document.getElementById('patch-name');
        const commandTypeField = document.getElementById('patch-command-type');
        const paramsField = document.getElementById('patch-command-params');
        
        if (nameField) nameField.value = '';
        if (commandTypeField) commandTypeField.value = '';
        if (paramsField) paramsField.innerHTML = '';
        
        // Resetar configuração de efeitos
        const effectsConfig = document.getElementById('zoom-effects-config');
        const effectsGrid = document.getElementById('effects-grid');
        const enableEffectsCheckbox = document.getElementById('enable-effects-config');
        
        if (effectsConfig) effectsConfig.style.display = 'none';
        if (effectsGrid) effectsGrid.style.display = 'none';
        if (enableEffectsCheckbox) enableEffectsCheckbox.checked = false;
        
        // Resetar efeitos para padrão
        this.resetEffectsToDefault();
        
        // Esconder seções específicas
        this.hideAllPatchSections();
        
        // Se há dispositivos pré-selecionados, mostrar seções correspondentes
        if (this.midiConfig.input_device) {
            this.handleInputDeviceChange(this.midiConfig.input_device);
        }
        if (this.midiConfig.output_device) {
            this.handleOutputDeviceChange(this.midiConfig.output_device);
        }
        
        // Configurar listener do tipo de comando
        this.setupPatchCommandTypeListener();
        
        modal.classList.add('show');
        
        // Adiciona logs para depuração
        console.log('[Novo Patch] Abrindo modal de novo patch');
        // Carrega canais disponíveis para Chocolate
        this.loadAvailableChannels();
        // Carrega patches disponíveis para Zoom (banco A por padrão)
        this.loadZoomPatchesForBank('A');
    }

    // Esconder todas as seções específicas
    hideAllPatchSections() {
        const sections = [
            'input-channel-section',
            'output-zoom-section',
            'output-command-section'
        ];
        sections.forEach(id => {
            const section = document.getElementById(id);
            if (section) section.style.display = 'none';
        });
    }

    // Handler para mudança de dispositivo de entrada
    handleInputDeviceChange(deviceName) {
        const channelSection = document.getElementById('input-channel-section');
        if (!channelSection) return;
        
        if (deviceName.toLowerCase().includes('chocolate')) {
            this.loadAvailableChannels();
            channelSection.style.display = 'block';
        } else {
            channelSection.style.display = 'none';
        }
    }

    // Handler para mudança de dispositivo de saída
    handleOutputDeviceChange(deviceName) {
        const zoomSection = document.getElementById('output-zoom-section');
        const commandSection = document.getElementById('output-command-section');
        
        if (!zoomSection || !commandSection) return;
        
        if (deviceName.toLowerCase().includes('zoom')) {
            zoomSection.style.display = 'block';
            commandSection.style.display = 'none';
        } else {
            zoomSection.style.display = 'none';
            commandSection.style.display = 'block';
        }
    }

    // Handler para mudança de banco da Zoom
    handleZoomBankChange(bankLetter) {
        if (!bankLetter) return;
        // Define automaticamente a letra do banco
        const bankLetterField = document.getElementById('patch-zoom-bank-letter');
        if (bankLetterField) {
            bankLetterField.value = bankLetter;
        }
        // Limpa o combo de patch
        const patchSelect = document.getElementById('patch-zoom-patch');
        if (patchSelect) {
            patchSelect.innerHTML = '<option value="">Selecione um patch...</option>';
            patchSelect.disabled = false;
        }
        // Não carrega nomes automaticamente!
    }

    // Carregar canais disponíveis para Chocolate (excluindo já usados)
    async loadAvailableChannels(excludePatchId = null) {
        try {
            const response = await fetch(`${this.apiBase}/patches/used_channels`);
            const data = await response.json();
            let usedChannels = data.success ? data.data : [];
            
            // Se estamos editando um patch, remove o canal do próprio patch da lista de usados
            if (excludePatchId) {
                const currentPatch = this.patches.find(p => p.id === excludePatchId);
                if (currentPatch && currentPatch.input_channel !== undefined) {
                    usedChannels = usedChannels.filter(channel => channel !== currentPatch.input_channel);
                    console.log(`[Edição] Canal ${currentPatch.input_channel} do patch atual será incluído na lista`);
                }
            }
            
            console.log('[Novo Patch] Canais já utilizados:', usedChannels);
            const channelSelect = document.getElementById('patch-input-channel');
            if (!channelSelect) return;
            channelSelect.innerHTML = '<option value="">Selecione um canal...</option>';
            for (let i = 0; i <= 127; i++) {
                if (!usedChannels.includes(i)) {
                    channelSelect.innerHTML += `<option value="${i}">Canal ${i}</option>`;
                } else {
                    console.log(`[Novo Patch] Canal ${i} já está em uso`);
                }
            }
        } catch (error) {
            console.error('Erro ao carregar canais disponíveis:', error);
        }
    }

    // Carregar patches da Zoom para um banco específico
    async loadZoomPatchesForBank(bankLetter, excludePatchId = null) {
        try {
            console.log('[DEBUG] Chamou loadZoomPatchesForBank para banco:', bankLetter);
            const patchSelect = document.getElementById('patch-zoom-patch');
            if (!patchSelect) return;
            patchSelect.innerHTML = '<option value="">Carregando patches...</option>';
            patchSelect.disabled = true;
            // Primeiro, obtém os patches usados
            const usedPatchesResponse = await fetch(`${this.apiBase}/patches/used_zoom_patches`);
            const usedPatchesData = await usedPatchesResponse.json();
            console.log('[DEBUG] used_zoom_patches response:', usedPatchesData);
            let usedPatches = usedPatchesData.success ? usedPatchesData.data : [];
            // Filtra apenas os usados para o banco atual
            const usedPatchesInBank = usedPatches.filter(p => p.bank === bankLetter).map(p => {
                if (p.patch !== undefined) return p.patch;
                if (p.zoom_patch !== undefined) return this.convertFromGlobalPatchNumber(p.zoom_patch).patch;
                return undefined;
            }).filter(x => x !== undefined);
            console.log('[DEBUG] Patches usados neste banco:', usedPatchesInBank);
            if (excludePatchId) {
                const currentPatch = this.patches.find(p => p.id === excludePatchId);
                if (currentPatch && currentPatch.zoom_patch !== undefined && currentPatch.zoom_bank === bankLetter) {
                    const localPatchNumber = this.convertFromGlobalPatchNumber(currentPatch.zoom_patch).patch;
                    const idx = usedPatchesInBank.indexOf(localPatchNumber);
                    if (idx !== -1) usedPatchesInBank.splice(idx, 1);
                }
            }
            // Busca patches do banco de dados
            const response = await fetch(`${this.apiBase}/midi/zoom/patches_db/${bankLetter}`);
            const data = await response.json();
            console.log('[DEBUG] /midi/zoom/patches_db response:', data);
            patchSelect.disabled = false;
            patchSelect.innerHTML = '<option value="">Selecione um patch...</option>';
            let patchesAdicionados = [];
            if (data.success && data.data) {
                data.data.forEach((patch, index) => {
                    const patchNumber = parseInt(patch.number) || 0;
                    const patchName = patch.name || `Patch ${patchNumber}`;
                    if (!usedPatchesInBank.includes(patchNumber)) {
                        patchSelect.innerHTML += `<option value="${patchNumber}">${patchName}</option>`;
                        patchesAdicionados.push(patchNumber);
                    }
                });
            } else {
                for (let i = 0; i < 10; i++) {
                    if (!usedPatchesInBank.includes(i)) {
                        patchSelect.innerHTML += `<option value="${i}">Patch ${i}</option>`;
                        patchesAdicionados.push(i);
                    }
                }
            }
            console.log('[DEBUG] Patches adicionados ao combo:', patchesAdicionados);
        } catch (e) {
            console.error('Erro ao carregar patches da Zoom:', e);
            const patchSelect = document.getElementById('patch-zoom-patch');
            if (patchSelect) {
                patchSelect.disabled = false;
                patchSelect.innerHTML = '<option value="">Erro ao carregar patches...</option>';
            }
        }
    }
    
    closeModal(modal) {
        if (modal) {
            modal.classList.remove('show');
            // Limpa o modo de edição
            this._editingPatchId = null;
            // Sempre restaura o botão para modo de criação ao fechar
            const submitButton = document.querySelector('#new-patch-modal .btn-success');
            if (submitButton) {
                submitButton.textContent = 'Criar Patch';
                // Remove onclick manual, deixa o submit do formulário cuidar disso
                submitButton.onclick = null;
            }
        }
    }
    
    async createPatch() {
        // Evita chamadas duplas
        if (this._creatingPatch) {
            console.log("⚠️ Patch já está sendo criado, ignorando chamada dupla");
            return;
        }
        
        this._creatingPatch = true;
        
        try {
            console.log("🔧 Iniciando criação de patch...");
            
            const form = document.getElementById('new-patch-form');
            const formData = new FormData(form);
            
            console.log("📋 Dados do formulário:");
            for (let [key, value] of formData.entries()) {
                console.log(`  ${key}: ${value}`);
            }
            // Log específico para zoom_bank_letter
            const zoomBankLetter = formData.get('zoom_bank_letter');
            console.log(`🔍 [DEBUG] zoom_bank_letter no FormData: "${zoomBankLetter}" (tipo: ${typeof zoomBankLetter})`);
            
            const patchData = {
                name: formData.get('name'),
                input_device: formData.get('input_device'),
                output_device: formData.get('output_device'),
            };
            
            console.log("📝 Dados básicos do patch:", patchData);
            
            // Adiciona canal de entrada se for Chocolate
            const inputChannel = formData.get('input_channel');
            if (inputChannel) {
                patchData.input_channel = parseInt(inputChannel);
                console.log("🎛️ Canal de entrada adicionado:", patchData.input_channel);
            }
            
            // Verifica se é Zoom G3X
            if (patchData.output_device.toLowerCase().includes('zoom')) {
                console.log("🎸 Detectado dispositivo Zoom G3X");
                const zoomBank = formData.get('zoom_bank');
                const localPatchNumber = formData.get('zoom_patch');
                const enableEffectsConfig = formData.get('enable_effects_config');
                console.log("🏦 Banco Zoom:", zoomBank, "Patch Local:", localPatchNumber, "Config Efeitos:", enableEffectsConfig);
                
                if (zoomBank && localPatchNumber) {
                    // Garante que ambos os campos tenham o mesmo valor
                    patchData.zoom_bank = zoomBank;
                    patchData.zoom_bank_letter = zoomBank;
                    patchData.program = parseInt(localPatchNumber); // Salva o número local (0-9)
                    console.log(`[Criação] Banco definido: zoom_bank=${zoomBank}, zoom_bank_letter=${zoomBank}`);

                    // Calcula e salva o número global do patch
                    patchData.zoom_patch = this.convertToGlobalPatchNumber(zoomBank, localPatchNumber);
                    
                    // Define o tipo de comando baseado na configuração de efeitos
                    if (enableEffectsConfig) {
                        // Se configuração de efeitos está habilitada, é um comando de efeitos
                        patchData.command_type = 'effects_config';
                        console.log("🎛️ Tipo de comando: Configuração de Efeitos");
                        
                        // Adiciona configuração de efeitos
                        patchData.effects = this.getEffectsConfig();
                        console.log("🎛️ Efeitos configurados:", patchData.effects);
                    } else {
                        // Se não habilitada, é um comando de mudança de patch
                        patchData.command_type = 'pc';
                        console.log("🎛️ Tipo de comando: Program Change (PC)");
                        
                        // Efeitos padrão (todos ligados) para mudança de patch
                        patchData.effects = {
                            effect_1: { enabled: true },
                            effect_2: { enabled: true },
                            effect_3: { enabled: true },
                            effect_4: { enabled: true },
                            effect_5: { enabled: true },
                            effect_6: { enabled: true }
                        };
                        console.log("🎛️ Efeitos padrão (todos ligados):", patchData.effects);
                    }
                    
                    console.log("✅ Dados Zoom configurados:", {
                        zoom_bank: patchData.zoom_bank,
                        zoom_patch: patchData.zoom_patch,
                        program: patchData.program,
                        command_type: patchData.command_type
                    });
                } else {
                    console.warn("⚠️ Dados Zoom incompletos - banco:", zoomBank, "patch:", localPatchNumber);
                }
            } else {
                console.log("🎛️ Dispositivo não-Zoom detectado");
                // Para outros dispositivos, usa comandos MIDI
                patchData.command_type = formData.get('command_type');
                
                // Adiciona parâmetros do comando
                if (patchData.command_type === 'pc') {
                    patchData.program = parseInt(formData.get('program'));
                } else if (patchData.command_type === 'cc') {
                    const ccValue = formData.get('cc');
                    if (ccValue === 'custom') {
                        patchData.cc = parseInt(formData.get('cc_custom'));
                    } else {
                        patchData.cc = parseInt(ccValue);
                    }
                    patchData.value = parseInt(formData.get('value'));
                } else if (patchData.command_type === 'note_on') {
                    patchData.note = parseInt(formData.get('note'));
                    patchData.velocity = parseInt(formData.get('velocity'));
                } else if (patchData.command_type === 'note_off') {
                    patchData.note = parseInt(formData.get('note'));
                }
                
                console.log("🎛️ Comando MIDI configurado:", patchData.command_type);
            }
            
            console.log("📤 Enviando dados para API:", patchData);
            
            // Log detalhado dos campos zoom
            console.log(`🔍 [DEBUG] Dados Zoom finais:`);
            console.log(`   zoom_bank: "${patchData.zoom_bank}" (tipo: ${typeof patchData.zoom_bank})`);
            console.log(`   zoom_bank_letter: "${patchData.zoom_bank_letter}" (tipo: ${typeof patchData.zoom_bank_letter})`);
            console.log(`   zoom_patch: ${patchData.zoom_patch} (tipo: ${typeof patchData.zoom_patch})`);
            console.log(`   program: ${patchData.program} (tipo: ${typeof patchData.program})`);
            
            // Criar AbortController para timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 segundos
            
            const response = await fetch(`${this.apiBase}/patches`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(patchData),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            console.log("📥 Resposta recebida, status:", response.status);
            
            const data = await response.json();
            console.log("📋 Dados da resposta:", data);
            
            if (data.success) {
                console.log("✅ Patch criado com sucesso, ID:", data.data?.id);
                this.showNotification('Patch criado com sucesso', 'success');
                this.closeModal(document.getElementById('new-patch-modal'));
                
                // Recarrega patches com timeout de segurança
                try {
                    console.log("🔄 Recarregando patches...");
                    await Promise.race([
                        this.loadPatches(),
                        new Promise((_, reject) => 
                            setTimeout(() => reject(new Error('Timeout')), 5000)
                        )
                    ]);
                    console.log("✅ Patches recarregados com sucesso");
                } catch (error) {
                    console.error("❌ Erro ao recarregar patches:", error);
                    this.showNotification('Patch salvo, mas erro ao atualizar lista', 'warning');
                }
                
            } else {
                console.error("❌ Erro na resposta da API:", data.error);
                throw new Error(data.error);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error('❌ Timeout na requisição - API não respondeu em 10 segundos');
                this.showNotification('Erro: API não respondeu. Tente novamente.', 'error');
            } else {
                console.error('❌ Erro ao criar patch:', error);
                this.showNotification('Erro ao criar patch: ' + error.message, 'error');
            }
        } finally {
            // Sempre libera a flag
            this._creatingPatch = false;
        }
    }
    
    // Método para reativar event listeners do menu
    reinitializeMenuListeners() {
        try {
            console.log("🔄 Reativando event listeners do menu...");
            
            // Remove event listeners antigos
            const menuItems = document.querySelectorAll('.menu-item');
            menuItems.forEach(item => {
                const newItem = item.cloneNode(true);
                item.parentNode.replaceChild(newItem, item);
            });
            
            // Reativa o menu de edição
            this.setupEdicaoMenu();
            
            console.log("✅ Event listeners do menu reativados");
            
        } catch (error) {
            console.error("❌ Erro ao reativar event listeners:", error);
        }
    }
    
    // Método auxiliar para navegar para uma seção específica
    navigateToSection(sectionName) {
        try {
            console.log(`🧭 Navegando para seção: ${sectionName}`);
            
            // Remove active de todos os itens do menu
            const menuItems = document.querySelectorAll('.menu-item');
            menuItems.forEach(menuItem => menuItem.classList.remove('active'));
            
            // Remove active de todas as seções
            const contentSections = document.querySelectorAll('.content-section');
            contentSections.forEach(section => section.classList.remove('active'));
            
            // Adiciona active ao item correto
            const targetItem = document.querySelector(`[data-section="${sectionName}"]`);
            if (targetItem) {
                targetItem.classList.add('active');
                console.log(`✅ Menu item ativado: ${sectionName}`);
            }
            
            // Adiciona active à seção correta
            const targetSection = document.getElementById(sectionName);
            if (targetSection) {
                targetSection.classList.add('active');
                console.log(`✅ Seção ativada: ${sectionName}`);
            }
            
            // Atualiza URL hash
            window.location.hash = sectionName;
            
        } catch (error) {
            console.error(`❌ Erro ao navegar para seção ${sectionName}:`, error);
        }
    }
    
    async editPatch(patchId) {
        try {
            console.log(`🔧 Iniciando edição do patch ${patchId}...`);
            
            // Define o modo de edição
            this._editingPatchId = patchId;
            
            // Busca os dados do patch
            const response = await fetch(`${this.apiBase}/patches/${patchId}`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Erro ao carregar patch');
            }
            
            const patch = data.data;
            console.log('📋 Dados do patch carregados:', patch);
            
            // Abre o modal de novo patch
            this.showNewPatchModal();
            
            // Preenche o formulário com os dados do patch
            this.fillPatchForm(patch);
            
            // Muda o título do modal para "Editar Patch"
            const modalTitle = document.querySelector('#new-patch-modal .modal-title');
            if (modalTitle) {
                modalTitle.textContent = 'Editar Patch';
            }
            
            // Muda o texto do botão para "Atualizar"
            const submitButton = document.querySelector('#new-patch-modal .btn-success');
            if (submitButton) {
                submitButton.textContent = 'Atualizar Patch';
                // Remove onclick manual, deixa o submit do formulário cuidar disso
                submitButton.onclick = null;
            }
            
            this.showNotification('Patch carregado para edição', 'info');
            
        } catch (error) {
            console.error('❌ Erro ao carregar patch para edição:', error);
            this.showNotification('Erro ao carregar patch: ' + error.message, 'error');
            // Limpa o modo de edição em caso de erro
            this._editingPatchId = null;
        }
    }
    
    fillPatchForm(patch) {
        try {
            console.log('📝 Preenchendo formulário com dados do patch:', patch);
            
            const form = document.getElementById('new-patch-form');
            if (!form) {
                throw new Error('Formulário não encontrado');
            }
            
            // Dados básicos
            this.setFormValue('name', patch.name);
            this.setFormValue('input_device', patch.input_device);
            this.setFormValue('output_device', patch.output_device);
            
            // Canal de entrada
            if (patch.input_channel !== undefined) {
                // Carrega canais disponíveis incluindo o do patch atual
                this.loadAvailableChannels(patch.id).then(() => {
                    this.setFormValue('input_channel', patch.input_channel.toString());
                });
            }
            
            // Verifica se é dispositivo Zoom
            if (patch.output_device && patch.output_device.toLowerCase().includes('zoom')) {
                console.log('🎸 Patch Zoom detectado');
                
                // Banco e patch Zoom
                if (patch.zoom_bank) {
                    this.setFormValue('zoom_bank', patch.zoom_bank);
                    
                    // Garante que ambos os campos tenham o mesmo valor
                    const bankValue = patch.zoom_bank_letter || patch.zoom_bank;
                    this.setFormValue('zoom_bank_letter', bankValue);
                    console.log(`[Edição] Banco definido: zoom_bank=${patch.zoom_bank}, zoom_bank_letter=${bankValue}`);
                    
                    this.handleZoomBankChange(patch.zoom_bank);
                    
                    // Carrega patches disponíveis incluindo o do patch atual
                    setTimeout(() => {
                        this.loadZoomPatchesForBank(patch.zoom_bank, patch.id).then(() => {
                            if (patch.zoom_patch !== undefined) {
                                // Converte número global para local para exibição no combo
                                const localPatchNumber = this.convertFromGlobalPatchNumber(patch.zoom_patch).patch;
                                this.setFormValue('zoom_patch', localPatchNumber.toString());
                                console.log(`[Edição] Patch global ${patch.zoom_patch} convertido para local ${localPatchNumber}`);
                            }
                        });
                    }, 500);
                } else if (patch.zoom_patch !== undefined) {
                    // fallback para garantir seleção
                    setTimeout(() => {
                        // Converte número global para local para exibição no combo
                        const localPatchNumber = this.convertFromGlobalPatchNumber(patch.zoom_patch).patch;
                        this.setFormValue('zoom_patch', localPatchNumber.toString());
                        console.log(`[Edição] Patch global ${patch.zoom_patch} convertido para local ${localPatchNumber} (fallback)`);
                    }, 1000);
                }
                
                // Configuração de efeitos
                if (patch.command_type === 'effects_config') {
                    this.setFormValue('enable_effects_config', 'on');
                    this.toggleEffectsConfig(true);
                    
                    // Configura os efeitos
                    if (patch.effects) {
                        setTimeout(() => {
                            this.loadEffectsConfig(patch.effects);
                        }, 1000);
                    }
                } else {
                    this.setFormValue('enable_effects_config', '');
                    this.toggleEffectsConfig(false);
                }
                
            } else {
                console.log('🎛️ Patch não-Zoom detectado');
                
                // Tipo de comando
                this.setFormValue('command_type', patch.command_type);
                this.showCommandParams(patch.command_type);
                
                // Parâmetros específicos do comando
                if (patch.command_type === 'pc') {
                    this.setFormValue('program', patch.program ? patch.program.toString() : '');
                } else if (patch.command_type === 'cc') {
                    if (patch.cc !== undefined) {
                        // Verifica se é um CC customizado
                        const ccOptions = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16'];
                        if (ccOptions.includes(patch.cc.toString())) {
                            this.setFormValue('cc', patch.cc.toString());
                        } else {
                            this.setFormValue('cc', 'custom');
                            this.setFormValue('cc_custom', patch.cc.toString());
                        }
                    }
                    this.setFormValue('value', patch.value ? patch.value.toString() : '');
                } else if (patch.command_type === 'note_on' || patch.command_type === 'note_off') {
                    this.setFormValue('note', patch.note ? patch.note.toString() : '');
                    if (patch.command_type === 'note_on') {
                        this.setFormValue('velocity', patch.velocity ? patch.velocity.toString() : '');
                    }
                }
            }
            
            console.log('✅ Formulário preenchido com sucesso');
            
        } catch (error) {
            console.error('❌ Erro ao preencher formulário:', error);
            throw error;
        }
    }
    
    setFormValue(fieldName, value) {
        const field = document.querySelector(`[name="${fieldName}"]`);
        if (field) {
            if (field.type === 'checkbox') {
                field.checked = value === 'on' || value === true;
            } else {
                field.value = value;
            }
            
            // Dispara evento change para ativar listeners
            field.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            console.warn(`⚠️ Campo ${fieldName} não encontrado`);
        }
    }
    
    loadEffectsConfig(effects) {
        try {
            console.log('🎛️ Carregando configuração de efeitos:', effects);
            
            // Itera pelos efeitos e configura cada um
            Object.keys(effects).forEach(effectKey => {
                const effect = effects[effectKey];
                const effectNumber = effectKey.replace('effect_', '');
                
                if (effect.enabled !== undefined) {
                    this.setEffectState(effectNumber, effect.enabled);
                }
            });
            
            console.log('✅ Configuração de efeitos carregada');
            
        } catch (error) {
            console.error('❌ Erro ao carregar configuração de efeitos:', error);
        }
    }
    
    setEffectState(effectNumber, enabled) {
        const effectElement = document.querySelector(`[data-effect="${effectNumber}"]`);
        if (effectElement) {
            if (enabled) {
                effectElement.classList.add('enabled');
                effectElement.classList.remove('disabled');
            } else {
                effectElement.classList.add('disabled');
                effectElement.classList.remove('enabled');
            }
        }
    }
    
    async updatePatch(patchId) {
        // Evita chamadas duplas
        if (this._updatingPatch) {
            console.log("⚠️ Patch já está sendo atualizado, ignorando chamada dupla");
            return;
        }
        
        this._updatingPatch = true;
        
        try {
            console.log(`🔧 Iniciando atualização do patch ${patchId}...`);
            
            const form = document.getElementById('new-patch-form');
            const formData = new FormData(form);
            
            console.log("📋 Dados do formulário:");
            for (let [key, value] of formData.entries()) {
                console.log(`  ${key}: ${value}`);
            }
            
            const patchData = {
                name: formData.get('name'),
                input_device: formData.get('input_device'),
                output_device: formData.get('output_device'),
            };
            
            console.log("📝 Dados básicos do patch:", patchData);
            
            // Adiciona canal de entrada se for Chocolate
            const inputChannel = formData.get('input_channel');
            if (inputChannel) {
                patchData.input_channel = parseInt(inputChannel);
                console.log("🎛️ Canal de entrada adicionado:", patchData.input_channel);
            }
            
            // Verifica se é Zoom G3X
            if (patchData.output_device.toLowerCase().includes('zoom')) {
                console.log("🎸 Detectado dispositivo Zoom G3X");
                const zoomBank = formData.get('zoom_bank');
                const localPatchNumber = formData.get('zoom_patch');
                const enableEffectsConfig = formData.get('enable_effects_config');
                console.log("🏦 Banco Zoom:", zoomBank, "Patch Local:", localPatchNumber, "Config Efeitos:", enableEffectsConfig);
                
                if (zoomBank && localPatchNumber) {
                    // Garante que ambos os campos tenham o mesmo valor
                    patchData.zoom_bank = zoomBank;
                    patchData.zoom_bank_letter = zoomBank;
                    console.log(`[Atualização] Banco definido: zoom_bank=${zoomBank}, zoom_bank_letter=${zoomBank}`);

                    // Calcula e salva o número global do patch
                    patchData.zoom_patch = this.convertToGlobalPatchNumber(zoomBank, localPatchNumber);
                    
                    // Para patches Zoom, o program é o número local (0-9) que será enviado para a Zoom
                    patchData.program = parseInt(localPatchNumber);
                    
                    // Define o tipo de comando baseado na configuração de efeitos
                    if (enableEffectsConfig) {
                        // Se configuração de efeitos está habilitada, é um comando de efeitos
                        patchData.command_type = 'effects_config';
                        console.log("🎛️ Tipo de comando: Configuração de Efeitos");
                        
                        // Adiciona configuração de efeitos
                        patchData.effects = this.getEffectsConfig();
                        console.log("🎛️ Efeitos configurados:", patchData.effects);
                    } else {
                        // Se não habilitada, é um comando de mudança de patch
                        patchData.command_type = 'pc';
                        console.log("🎛️ Tipo de comando: Program Change (PC)");
                        
                        // Efeitos padrão (todos ligados) para mudança de patch
                        patchData.effects = {
                            effect_1: { enabled: true },
                            effect_2: { enabled: true },
                            effect_3: { enabled: true },
                            effect_4: { enabled: true },
                            effect_5: { enabled: true },
                            effect_6: { enabled: true }
                        };
                        console.log("🎛️ Efeitos padrão (todos ligados):", patchData.effects);
                    }
                    
                    console.log("✅ Dados Zoom configurados:", {
                        zoom_bank: patchData.zoom_bank,
                        zoom_patch: patchData.zoom_patch,
                        program: patchData.program,
                        command_type: patchData.command_type
                    });
                } else {
                    console.warn("⚠️ Dados Zoom incompletos - banco:", zoomBank, "patch:", localPatchNumber);
                }
            } else {
                console.log("🎛️ Dispositivo não-Zoom detectado");
                // Para outros dispositivos, usa comandos MIDI
                patchData.command_type = formData.get('command_type');
                
                // Adiciona parâmetros do comando
                if (patchData.command_type === 'pc') {
                    patchData.program = parseInt(formData.get('program'));
                } else if (patchData.command_type === 'cc') {
                    const ccValue = formData.get('cc');
                    if (ccValue === 'custom') {
                        patchData.cc = parseInt(formData.get('cc_custom'));
                    } else {
                        patchData.cc = parseInt(ccValue);
                    }
                    patchData.value = parseInt(formData.get('value'));
                } else if (patchData.command_type === 'note_on') {
                    patchData.note = parseInt(formData.get('note'));
                    patchData.velocity = parseInt(formData.get('velocity'));
                } else if (patchData.command_type === 'note_off') {
                    patchData.note = parseInt(formData.get('note'));
                }
                
                console.log("🎛️ Comando MIDI configurado:", patchData.command_type);
            }
            
            console.log("📤 Enviando dados para API:", patchData);
            
            // Log detalhado dos campos zoom
            console.log(`🔍 [DEBUG] Dados Zoom finais:`);
            console.log(`   zoom_bank: "${patchData.zoom_bank}" (tipo: ${typeof patchData.zoom_bank})`);
            console.log(`   zoom_bank_letter: "${patchData.zoom_bank_letter}" (tipo: ${typeof patchData.zoom_bank_letter})`);
            console.log(`   zoom_patch: ${patchData.zoom_patch} (tipo: ${typeof patchData.zoom_patch})`);
            console.log(`   program: ${patchData.program} (tipo: ${typeof patchData.program})`);
            
            // Criar AbortController para timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 segundos
            
            const response = await fetch(`${this.apiBase}/patches/${patchId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(patchData),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            console.log("📥 Resposta recebida, status:", response.status);
            
            const data = await response.json();
            console.log("📋 Dados da resposta:", data);
            
            if (data.success) {
                console.log("✅ Patch atualizado com sucesso");
                this.showNotification('Patch atualizado com sucesso', 'success');
                
                // Limpa o modo de edição
                this._editingPatchId = null;
                
                this.closeModal(document.getElementById('new-patch-modal'));
                
                // Recarrega patches com timeout de segurança
                try {
                    console.log("🔄 Recarregando patches...");
                    await Promise.race([
                        this.loadPatches(),
                        new Promise((_, reject) => 
                            setTimeout(() => reject(new Error('Timeout')), 5000)
                        )
                    ]);
                    console.log("✅ Patches recarregados com sucesso");
                } catch (error) {
                    console.error("❌ Erro ao recarregar patches:", error);
                    this.showNotification('Patch salvo, mas erro ao atualizar lista', 'warning');
                }
                
            } else {
                console.error("❌ Erro na resposta da API:", data.error);
                throw new Error(data.error);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error('❌ Timeout na requisição - API não respondeu em 10 segundos');
                this.showNotification('Erro: API não respondeu. Tente novamente.', 'error');
            } else {
                console.error('❌ Erro ao atualizar patch:', error);
                this.showNotification('Erro ao atualizar patch: ' + error.message, 'error');
            }
        } finally {
            // Sempre libera a flag
            this._updatingPatch = false;
        }
    }
    
    async deletePatch(patchId) {
        if (!confirm('Tem certeza que deseja deletar este patch?')) {
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/patches/${patchId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Patch deletado com sucesso', 'success');
                await this.loadPatches();
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            console.error('Erro ao deletar patch:', error);
            this.showNotification('Erro ao deletar patch', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        // Cria notificação
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Adiciona ao DOM
        document.body.appendChild(notification);
        
        // Remove após 3 segundos
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    startStatusUpdates() {
        // Atualiza status a cada 5 segundos
        setInterval(async () => {
            await this.loadStatus();
            await this.loadDeviceStatus(); // Adiciona atualização do status dos dispositivos
        }, 5000);
    }
    
    // Métodos de Monitoramento MIDI
    async toggleMidiMonitor() {
        try {
            if (!this.midiMonitor.active) {
                // Verifica se um dispositivo foi selecionado
                const deviceSelect = document.getElementById('monitor-input-device');
                const selectedDevice = deviceSelect ? deviceSelect.value : '';
                
                if (!selectedDevice) {
                    this.showNotification('Selecione um dispositivo de entrada primeiro', 'warning');
                    return;
                }
                
                // Inicia monitoramento com o dispositivo selecionado
                const response = await fetch('/api/midi/monitor/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        device: selectedDevice
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.midiMonitor.active = true;
                    this.midiMonitor.currentDevice = selectedDevice;
                    const button = document.getElementById('toggle-monitor');
                    const status = document.getElementById('monitor-status');
                    
                    if (button) {
                        button.textContent = 'Parar Monitor';
                        button.className = 'btn btn-accent btn-small';
                    }
                    
                    if (status) {
                        status.textContent = 'Conectado';
                        status.className = 'stat-value connected';
                    }
                    
                    // Limpa comandos antigos ao iniciar
                    this.midiMonitor.commands = [];
                    this.midiMonitor.commandCount = 0;
                    this.midiMonitor.lastCommand = null;
                    this.updateMidiMonitorDisplay();
                    
                    // Atualiza informações do dispositivo imediatamente
                    await this.updateMonitoringStatus();
                    
                    this.showNotification(`Monitor MIDI iniciado no dispositivo: ${selectedDevice}`, 'success');
                } else {
                    throw new Error(data.error);
                }
            } else {
                // Para monitoramento
                const response = await fetch('/api/midi/monitor/stop', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.midiMonitor.active = false;
                    this.midiMonitor.currentDevice = null;
                    const button = document.getElementById('toggle-monitor');
                    const status = document.getElementById('monitor-status');
                    
                    if (button) {
                        button.textContent = 'Iniciar Monitor';
                        button.className = 'btn btn-success btn-small';
                    }
                    
                    if (status) {
                        status.textContent = 'Desconectado';
                        status.className = 'stat-value disconnected';
                    }
                    
                    // Para o polling
                    this.midiMonitor.polling = false;
                    
                    // Atualiza informações do dispositivo
                    await this.updateMonitoringStatus();
                    
                    this.showNotification('Monitor MIDI parado', 'warning');
                } else {
                    throw new Error(data.error);
                }
            }
        } catch (error) {
            this.showNotification(`Erro: ${error.message}`, 'error');
        }
    }
    
    clearMidiMonitor() {
        this.midiMonitor.commands = [];
        this.midiMonitor.lastCommand = null;
        this.midiMonitor.commandCount = 0;
        this.updateMidiMonitorDisplay();
        this.showNotification('Monitor MIDI limpo', 'info');
    }
    
    addMidiCommand(command) {
        if (!this.midiMonitor.active) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const commandData = {
            ...command,
            timestamp,
            id: Date.now()
        };
        
        this.midiMonitor.commands.unshift(commandData);
        this.midiMonitor.commandCount++;
        this.midiMonitor.lastCommand = commandData;
        
        // Limita o número de comandos no log
        if (this.midiMonitor.commands.length > this.midiMonitor.maxLines) {
            this.midiMonitor.commands = this.midiMonitor.commands.slice(0, this.midiMonitor.maxLines);
        }
        
        this.updateMidiMonitorDisplay();
    }
    
    async updateMidiMonitorDisplay() {
        const logContent = document.getElementById('midi-monitor-content');
        
        // Verifica se o elemento existe antes de tentar acessá-lo
        if (!logContent) {
            console.warn('Elemento midi-monitor-content não encontrado');
            return;
        }
        
        if (this.midiMonitor.commands.length === 0) {
            logContent.innerHTML = `
                <div class="log-entry">
                    <span class="log-time">--:--:--</span>
                    <span class="log-prompt">></span>
                    <span class="log-text">Monitor desativado. Clique em "Iniciar Monitor" para começar.</span>
                </div>
            `;
            return;
        }
        
        // Limita o número de comandos exibidos
        const maxCommands = this.midiMonitor.maxLines || 5;
        const recentCommands = this.midiMonitor.commands.slice(-maxCommands);
        
        logContent.innerHTML = recentCommands.map(cmd => {
            const time = new Date(cmd.timestamp * 1000).toLocaleTimeString();
            let commandText = '';
            
            switch (cmd.type) {
                case 'control_change':
                    commandText = `CC ${cmd.cc} = ${cmd.value} (ch: ${cmd.channel})`;
                    break;
                case 'program_change':
                    commandText = `PC ${cmd.program} (ch: ${cmd.channel})`;
                    break;
                case 'note_on':
                    commandText = `Note On: ${cmd.note} vel: ${cmd.velocity} (ch: ${cmd.channel})`;
                    break;
                case 'note_off':
                    commandText = `Note Off: ${cmd.note} (ch: ${cmd.channel})`;
                    break;
                default:
                    commandText = `${cmd.type}: ${JSON.stringify(cmd)}`;
            }
            
            return `
                <div class="log-entry">
                    <span class="log-time">${time}</span>
                    <span class="log-prompt">></span>
                    <span class="log-text">${commandText}</span>
                </div>
            `;
        }).join('');
        
        // Scroll para o topo
        logContent.scrollTop = 0;
    }
    
    async updateMonitoringStatus() {
        const statusElement = document.getElementById('monitor-status');
        const deviceElement = document.getElementById('monitor-device');
        const modeElement = document.getElementById('monitor-mode');
        
        if (statusElement) {
            statusElement.textContent = this.midiMonitor.active ? 'Monitorando' : 'Desconectado';
            statusElement.className = `stat-value ${this.midiMonitor.active ? 'connected' : 'disconnected'}`;
        }
        
        if (deviceElement) {
            deviceElement.textContent = this.midiMonitor.currentDevice || 'Nenhum';
        }
        
        if (modeElement) {
            modeElement.textContent = this.midiMonitor.active ? 'Ativo' : '-';
        }
    }
    
    updateMonitorDeviceSelector() {
        const select = document.getElementById('monitor-input-device');
        if (!select) return;
        
        // Limpa opções existentes
        select.innerHTML = '<option value="">Selecione um dispositivo...</option>';
        
        // Adiciona dispositivos de entrada disponíveis
        const inputDevices = this.devices.inputs || [];
        
        inputDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.name;
            option.textContent = `${device.name} (${device.real_name})`;
            select.appendChild(option);
        });
        
        // Seleciona o dispositivo atual se estiver monitorando
        if (this.midiMonitor.active && this.midiMonitor.currentDevice) {
            select.value = this.midiMonitor.currentDevice;
        }
    }
    
    updateOutputDeviceSelector() {
        const select = document.getElementById('output-device-select');
        if (!select) return;
        
        // Limpa opções existentes
        select.innerHTML = '<option value="">Selecione um dispositivo...</option>';
        
        // Adiciona dispositivos de saída disponíveis
        const outputDevices = this.devices.outputs || [];
        outputDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.name;
            option.textContent = `${device.name} (${device.real_name})`;
            select.appendChild(option);
        });
        
        // Seleciona o dispositivo correto baseado na configuração
        if (this.midiConfig.output_device) {
            select.value = this.midiConfig.output_device;
        }
    }
    
    setupMidiCommands() {
        // Configura seletor de tipo de comando
        const commandTypeSelect = document.getElementById('command-type');
        if (commandTypeSelect) {
            commandTypeSelect.addEventListener('change', () => {
                this.showCommandParams(commandTypeSelect.value);
            });
        }
        
        // Configura botões pré-configurados
        const presetButtons = document.querySelectorAll('.preset-btn');
        presetButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.sendPresetCommand(e.target);
            });
        });
        
        // Configura botão de envio de comando personalizado
        const sendButton = document.getElementById('send-custom-command');
        if (sendButton) {
            sendButton.addEventListener('click', () => {
                this.sendCustomCommand();
            });
        }
        
        // Configura botão de salvar template
        const saveTemplateButton = document.getElementById('save-command-template');
        if (saveTemplateButton) {
            saveTemplateButton.addEventListener('click', () => {
                this.saveCommandTemplate();
            });
        }
    }
    
    showCommandParams(commandType) {
        // Esconde todos os grupos de parâmetros
        const paramGroups = document.querySelectorAll('.param-group');
        paramGroups.forEach(group => {
            group.style.display = 'none';
        });
        
        // Mostra o grupo apropriado
        const targetGroup = document.getElementById(`${commandType}-params`);
        if (targetGroup) {
            targetGroup.style.display = 'grid';
        }
    }
    
    async sendPresetCommand(button) {
        const device = this.getSelectedOutputDevice();
        if (!device) {
            this.showNotification('Selecione um dispositivo de saída primeiro', 'warning');
            return;
        }
        
        const type = button.dataset.type;
        const label = button.dataset.label;
        
        try {
            if (type === 'pc') {
                const program = parseInt(button.dataset.program);
                await this.sendPC(program, device);
            } else if (type === 'cc') {
                const cc = parseInt(button.dataset.cc);
                const value = parseInt(button.dataset.value);
                await this.sendCC(cc, value, device);
            } else if (type === 'multi') {
                const commands = JSON.parse(button.dataset.commands);
                await this.sendMultipleCommands(commands, device);
                this.addCommandToLog(`Múltiplos comandos (${commands.length})`, device, true);
                this.showNotification(`Comandos múltiplos enviados para ${device}`, 'success');
            }
        } catch (error) {
            this.showNotification(`Erro ao enviar comando: ${error.message}`, 'error');
        }
    }
    
    async sendCustomCommand() {
        const device = this.getSelectedOutputDevice();
        if (!device) {
            this.showNotification('Selecione um dispositivo de saída primeiro', 'warning');
            return;
        }
        
        const commandType = document.getElementById('command-type').value;
        
        try {
            switch (commandType) {
                case 'cc':
                    const cc = parseInt(document.getElementById('cc-number').value);
                    const value = parseInt(document.getElementById('cc-value').value);
                    if (isNaN(cc) || isNaN(value)) {
                        throw new Error('Valores CC inválidos');
                    }
                    await this.sendCC(cc, value, device);
                    break;
                case 'pc':
                    const program = parseInt(document.getElementById('pc-program').value);
                    if (isNaN(program)) {
                        throw new Error('Programa inválido');
                    }
                    await this.sendPC(program, device);
                    break;
                case 'note':
                    const note = parseInt(document.getElementById('note-number').value);
                    const velocity = parseInt(document.getElementById('note-velocity').value);
                    const type = document.getElementById('note-type').value;
                    if (isNaN(note) || isNaN(velocity)) {
                        throw new Error('Valores de nota inválidos');
                    }
                    await this.sendNote(note, velocity, type, device);
                    break;
                default:
                    throw new Error('Tipo de comando não suportado');
            }
        } catch (error) {
            this.showNotification(`Erro ao enviar comando: ${error.message}`, 'error');
        }
    }
    
    async sendMultipleCommands(commands, device) {
        for (const command of commands) {
            try {
                if (command.type === 'pc') {
                    await this.sendPC(command.program, device);
                } else if (command.type === 'cc') {
                    await this.sendCC(command.cc, command.value, device);
                } else if (command.type === 'delay') {
                    // Aguarda o tempo especificado
                    await new Promise(resolve => setTimeout(resolve, command.ms));
                    continue; // Pula para o próximo comando
                }
                
                // Pequeno delay entre comandos (exceto delays explícitos)
                if (command.type !== 'delay') {
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                
            } catch (error) {
                console.error(`Erro ao executar comando ${command.type}:`, error);
                this.addCommandToLog(`Erro: ${command.type}`, device, false);
                throw error;
            }
        }
    }
    
    getSelectedOutputDevice() {
        const select = document.getElementById('output-device-select');
        return select ? select.value : null;
    }
    
    saveCommandTemplate() {
        const commandType = document.getElementById('command-type').value;
        let template = {};
        
        switch (commandType) {
            case 'cc':
                template = {
                    type: 'cc',
                    cc: parseInt(document.getElementById('cc-number').value) || 0,
                    value: parseInt(document.getElementById('cc-value').value) || 0
                };
                break;
            case 'pc':
                template = {
                    type: 'pc',
                    program: parseInt(document.getElementById('pc-program').value) || 0
                };
                break;
            case 'note':
                template = {
                    type: 'note',
                    note: parseInt(document.getElementById('note-number').value) || 60,
                    velocity: parseInt(document.getElementById('note-velocity').value) || 64,
                    noteType: document.getElementById('note-type').value
                };
                break;
        }
        
        // Copia para clipboard
        navigator.clipboard.writeText(JSON.stringify(template, null, 2)).then(() => {
            this.showNotification('Template copiado para clipboard!', 'success');
        }).catch(() => {
            this.showNotification('Erro ao copiar template', 'error');
        });
    }
    
    startMidiPolling() {
        // Polling para verificar novos comandos MIDI
        setInterval(() => {
            if (this.midiMonitor.active && !this.midiMonitor.polling) {
                this.checkMidiCommands();
            }
        }, 1000); // Verifica a cada 1 segundo em vez de 100ms
    }
    
    async checkMidiCommands() {
        if (this.midiMonitor.polling) return; // Evita chamadas simultâneas
        
        try {
            this.midiMonitor.polling = true;
            const response = await fetch('/api/midi/commands/received');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.commands && data.commands.length > 0) {
                    data.commands.forEach(cmd => {
                        this.addMidiCommand(cmd);
                    });
                }
            }
        } catch (error) {
            // Silencioso - não mostra erro se não conseguir conectar
        } finally {
            this.midiMonitor.polling = false;
        }
    }
    
    async simulateMidiCommand() {
        try {
            const response = await fetch('/api/midi/commands/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                // Adiciona o comando simulado ao monitor se estiver ativo
                if (this.midiMonitor.active && data.command) {
                    this.addMidiCommand(data.command);
                }
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.showNotification('Erro ao simular comando MIDI', 'error');
        }
    }
    
    async pollMidiCommands() {
        if (!this.midiMonitor.active || this.midiMonitor.polling) {
            return;
        }
        
        this.midiMonitor.polling = true;
        
        try {
            const response = await fetch('/api/midi/commands/received');
            const data = await response.json();
            
            if (data.success && data.commands) {
                if (data.commands.length > 0) {
                    this.midiMonitor.commands = [...this.midiMonitor.commands, ...data.commands];
                    this.midiMonitor.lastCommand = data.commands[data.commands.length - 1];
                    this.midiMonitor.commandCount = this.midiMonitor.commands.length;
                    this.updateMidiMonitorDisplay();
                }
            }
            
            // Atualiza status do monitoramento
            await this.updateMonitoringStatus();
            
        } catch (error) {
            console.error('Erro ao buscar comandos MIDI:', error);
        } finally {
            this.midiMonitor.polling = false;
            
            // Agenda próxima verificação
            if (this.midiMonitor.active) {
                setTimeout(() => this.pollMidiCommands(), 1000);
            }
        }
    }

    // Log de comandos enviados
    addCommandToLog(command, device, success = true) {
        const now = new Date();
        const time = now.toLocaleTimeString();
        
        const logEntry = {
            time: time,
            command: command,
            device: device,
            success: success
        };
        
        this.commandLog.unshift(logEntry);
        
        // Manter apenas os últimos 3 comandos
        if (this.commandLog.length > this.MAX_LOG_ENTRIES) {
            this.commandLog = this.commandLog.slice(0, this.MAX_LOG_ENTRIES);
        }
        
        this.updateCommandLogDisplay();
    }

    updateCommandLogDisplay() {
        const logContent = document.getElementById('command-log-content');
        
        // Verifica se o elemento existe antes de tentar acessá-lo
        if (!logContent) {
            console.warn('Elemento command-log-content não encontrado');
            return;
        }
        
        if (this.commandLog.length === 0) {
            logContent.innerHTML = `
                <div class="log-entry">
                    <span class="log-time">--:--:--</span>
                    <span class="log-prompt">$</span>
                    <span class="log-text">Sistema pronto. Aguardando comandos...</span>
                </div>
            `;
            return;
        }
        
        logContent.innerHTML = this.commandLog.map(entry => {
            const statusClass = entry.success ? 'success' : 'error';
            const statusIcon = entry.success ? '✓' : '✗';
            return `
                <div class="log-entry ${statusClass}">
                    <span class="log-time">${entry.time}</span>
                    <span class="log-prompt">$</span>
                    <span class="log-text">${statusIcon} ${entry.command} → ${entry.device}</span>
                </div>
            `;
        }).join('');
        
        // Scroll para o topo
        logContent.scrollTop = 0;
    }

    clearCommandLog() {
        this.commandLog = [];
        this.updateCommandLogDisplay();
    }

    // Função para enviar comando CC
    async sendCC(cc, value, device) {
        try {
            const response = await fetch('/api/midi/cc', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    cc: cc,
                    value: value,
                    device: device
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.addCommandToLog(`CC ${cc} = ${value}`, device, true);
                this.showNotification('Comando CC enviado com sucesso!', 'success');
            } else {
                this.addCommandToLog(`CC ${cc} = ${value}`, device, false);
                this.showNotification('Erro ao enviar comando CC: ' + result.error, 'error');
            }
        } catch (error) {
            this.addCommandToLog(`CC ${cc} = ${value}`, device, false);
            this.showNotification('Erro ao enviar comando CC: ' + error.message, 'error');
        }
    }

    // Função para enviar comando PC
    async sendPC(program, device) {
        try {
            const response = await fetch('/api/midi/pc', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    program: program,
                    device: device
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.addCommandToLog(`PC ${program}`, device, true);
                this.showNotification('Comando PC enviado com sucesso!', 'success');
            } else {
                this.addCommandToLog(`PC ${program}`, device, false);
                this.showNotification('Erro ao enviar comando PC: ' + result.error, 'error');
            }
        } catch (error) {
            this.addCommandToLog(`PC ${program}`, device, false);
            this.showNotification('Erro ao enviar comando PC: ' + error.message, 'error');
        }
    }

    // Função para enviar comando Note
    async sendNote(note, velocity, noteType, device) {
        try {
            const response = await fetch('/api/midi/note', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    note: note,
                    velocity: velocity,
                    type: noteType,
                    device: device
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.addCommandToLog(`Note ${note} ${noteType} (vel: ${velocity})`, device, true);
                this.showNotification('Comando Note enviado com sucesso!', 'success');
            } else {
                this.addCommandToLog(`Note ${note} ${noteType} (vel: ${velocity})`, device, false);
                this.showNotification('Erro ao enviar comando Note: ' + result.error, 'error');
            }
        } catch (error) {
            this.addCommandToLog(`Note ${note} ${noteType} (vel: ${velocity})`, device, false);
            this.showNotification('Erro ao enviar comando Note: ' + error.message, 'error');
        }
    }

    // Event listeners para alertas de alimentação
    async testPowerStatus() {
        try {
            const response = await fetch(`${this.apiBase}/midi/devices/power_status`);
            const data = await response.json();
            
            if (data.success) {
                const status = data.data;
                
                // Força verificação de alertas de alimentação
                this.resetPowerAlerts();
                await this.checkPowerAlerts();
                
                this.showNotification('Status de alimentação verificado', 'success');
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Erro ao verificar status de alimentação:', error);
            this.showNotification('Erro ao verificar status de alimentação', 'error');
        }
    }
    
    async dismissPowerAlert() {
        try {
            // Esconde o alerta localmente
            this.hidePowerAlert();
            
            // Salva no localStorage para não mostrar novamente nesta sessão
            localStorage.setItem('powerAlertDismissed', 'true');
            
            this.showNotification('Alerta de alimentação descartado', 'success');
        } catch (error) {
            console.error('Erro ao descartar alerta de alimentação:', error);
            this.showNotification('Erro ao descartar alerta de alimentação', 'error');
        }
    }

    resetPowerAlerts() {
        // Remove o flag de alerta descartado para permitir nova verificação
        localStorage.removeItem('powerAlertDismissed');
    }

    // Botão para reativar alertas
    async reactivateAlerts() {
        try {
            // Remove o flag de alerta descartado para permitir nova verificação
            localStorage.removeItem('powerAlertDismissed');
            
            this.showNotification('Alerta de alimentação reativado', 'success');
        } catch (error) {
            console.error('Erro ao reativar alerta de alimentação:', error);
            this.showNotification('Erro ao reativar alerta de alimentação', 'error');
        }
    }

    // Botão para reconectar Chocolate
    async reconnectChocolate() {
        try {
            this.showNotification('Reconectando Chocolate...', 'info');
            
            const response = await fetch(`${this.apiBase}/midi/devices/chocolate/reconnect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Chocolate reconectado com sucesso!', 'success');
                
                // Atualiza o status dos dispositivos
                await this.loadStatus();
                await this.loadDevices();
                
                // Verifica alertas de alimentação
                await this.checkPowerAlerts();
            } else {
                throw new Error(data.error || 'Erro desconhecido');
            }
        } catch (error) {
            console.error('Erro ao reconectar Chocolate:', error);
            this.showNotification(`Erro ao reconectar Chocolate: ${error.message}`, 'error');
        }
    }

    // Botão para reconectar Zoom G3X
    async reconnectZoomG3X() {
        try {
            this.showNotification('Reconectando Zoom G3X...', 'info');
            
            const response = await fetch(`${this.apiBase}/midi/devices/zoom_g3x/reconnect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Zoom G3X reconectado com sucesso!', 'success');
                
                // Atualiza o status dos dispositivos
                await this.loadStatus();
                await this.loadDevices();
                
                // Verifica alertas de alimentação
                await this.checkPowerAlerts();
            } else {
                throw new Error(data.error || 'Erro desconhecido');
            }
        } catch (error) {
            console.error('Erro ao reconectar Zoom G3X:', error);
            this.showNotification(`Erro ao reconectar Zoom G3X: ${error.message}`, 'error');
        }
    }

    // Menu de navegação do modo edição
    setupEdicaoMenu() {
        console.log("🔧 Configurando menu de edição...");
        
        // Event listeners para o menu de navegação
        const menuItems = document.querySelectorAll('.menu-item');
        const contentSections = document.querySelectorAll('.content-section');
        
        console.log(`📋 Encontrados ${menuItems.length} itens de menu e ${contentSections.length} seções`);
        
        menuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                console.log(`🖱️ Menu item clicado: ${item.getAttribute('data-section')}`);
                
                // Remove active de todos os itens do menu
                menuItems.forEach(menuItem => menuItem.classList.remove('active'));
                
                // Remove active de todas as seções
                contentSections.forEach(section => section.classList.remove('active'));
                
                // Adiciona active ao item clicado
                item.classList.add('active');
                
                // Mostra a seção correspondente
                const targetSection = item.getAttribute('data-section');
                const section = document.getElementById(targetSection);
                if (section) {
                    section.classList.add('active');
                    console.log(`✅ Seção ${targetSection} ativada`);
                } else {
                    console.warn(`⚠️ Seção ${targetSection} não encontrada`);
                }
            });
        });
        
        // Navegação por URL hash
        const handleHashChange = () => {
            const hash = window.location.hash.substring(1) || 'dispositivos';
            console.log(`🔗 Hash da URL: ${hash}`);
            
            const targetItem = document.querySelector(`[data-section="${hash}"]`);
            const targetSection = document.getElementById(hash);
            
            console.log(`🎯 Item de menu encontrado: ${!!targetItem}, Seção encontrada: ${!!targetSection}`);
            
            if (targetItem && targetSection) {
                // Remove active de todos
                menuItems.forEach(menuItem => menuItem.classList.remove('active'));
                contentSections.forEach(section => section.classList.remove('active'));
                
                // Adiciona active aos elementos corretos
                targetItem.classList.add('active');
                targetSection.classList.add('active');
                console.log(`✅ Navegação para ${hash} concluída`);
            } else {
                console.warn(`⚠️ Elementos para hash ${hash} não encontrados`);
            }
        };
        
        // Listener para mudanças no hash
        window.addEventListener('hashchange', handleHashChange);
        
        // Executa na inicialização
        handleHashChange();
        
        console.log("✅ Menu de edição configurado");
    }

    // Campos dinâmicos para tipo de comando
    setupPatchCommandTypeListener() {
        const commandTypeSelect = document.getElementById('patch-command-type');
        if (!commandTypeSelect) {
            console.warn('Elemento patch-command-type não encontrado');
            return;
        }
        
        commandTypeSelect.addEventListener('change', (e) => {
            const type = e.target.value;
            const paramsDiv = document.getElementById('patch-command-params');
            if (!paramsDiv) {
                console.warn('Elemento patch-command-params não encontrado');
                return;
            }
            
            let html = '';
            
            if (type === 'pc') {
                // Program Change - Patches do Zoom G3X
                html = `
                    <div class="form-group">
                        <label>Programa (Patch)</label>
                        <select name="program" class="form-input" required>
                            <option value="">Selecione um patch...</option>
                            <optgroup label="Patches Clean (0-9)">
                                <option value="0">0 - Clean</option>
                                <option value="1">1 - Clean Bright</option>
                                <option value="2">2 - Clean Warm</option>
                                <option value="3">3 - Clean Crunch</option>
                            </optgroup>
                            <optgroup label="Patches Overdrive (10-19)">
                                <option value="10">10 - Overdrive</option>
                                <option value="11">11 - Overdrive Crunch</option>
                                <option value="12">12 - Overdrive Lead</option>
                                <option value="13">13 - Overdrive Blues</option>
                            </optgroup>
                            <optgroup label="Patches Distortion (20-29)">
                                <option value="20">20 - Distortion</option>
                                <option value="21">21 - Distortion Heavy</option>
                                <option value="22">22 - Distortion Metal</option>
                                <option value="23">23 - Distortion Lead</option>
                            </optgroup>
                            <optgroup label="Patches Lead (30-39)">
                                <option value="30">30 - Lead</option>
                                <option value="31">31 - Lead Solo</option>
                                <option value="32">32 - Lead High Gain</option>
                                <option value="33">33 - Lead Saturated</option>
                            </optgroup>
                            <optgroup label="Patches Bass (40-49)">
                                <option value="40">40 - Bass Clean</option>
                                <option value="41">41 - Bass Overdrive</option>
                                <option value="42">42 - Bass Distortion</option>
                                <option value="43">43 - Bass Lead</option>
                            </optgroup>
                            <optgroup label="Patches Acoustic (50-59)">
                                <option value="50">50 - Acoustic</option>
                                <option value="51">51 - Acoustic Bright</option>
                                <option value="52">52 - Acoustic Warm</option>
                                <option value="53">53 - Acoustic Piezo</option>
                            </optgroup>
                            <optgroup label="Custom (60-127)">
                                <option value="60">60 - Custom 1</option>
                                <option value="61">61 - Custom 2</option>
                                <option value="62">62 - Custom 3</option>
                                <option value="63">63 - Custom 4</option>
                            </optgroup>
                        </select>
                    </div>
                `;
            } else if (type === 'cc') {
                // Control Change - Controles comuns
                html = `
                    <div class="form-group">
                        <label>CC Number (Controle)</label>
                        <select name="cc" class="form-input" required onchange="app.handleCCSelection(this.value)">
                            <option value="">Selecione um controle...</option>
                            <optgroup label="Controles de Volume e Expressão">
                                <option value="7">7 - Volume</option>
                                <option value="11">11 - Expression</option>
                                <option value="1">1 - Modulation</option>
                                <option value="2">2 - Breath Controller</option>
                            </optgroup>
                            <optgroup label="Controles de Efeitos">
                                <option value="91">91 - Reverb</option>
                                <option value="93">93 - Chorus</option>
                                <option value="94">94 - Detune</option>
                                <option value="95">95 - Phaser</option>
                                <option value="96">96 - Data Increment</option>
                                <option value="97">97 - Data Decrement</option>
                            </optgroup>
                            <optgroup label="Controles de Pedal">
                                <option value="4">4 - Foot Controller</option>
                                <option value="64">64 - Sustain Pedal</option>
                                <option value="65">65 - Portamento</option>
                                <option value="66">66 - Sostenuto</option>
                                <option value="67">67 - Soft Pedal</option>
                            </optgroup>
                            <optgroup label="Controles de Pitch">
                                <option value="0">0 - Bank Select</option>
                                <option value="32">32 - Bank Select LSB</option>
                                <option value="5">5 - Portamento Time</option>
                                <option value="84">84 - Portamento Control</option>
                            </optgroup>
                            <optgroup label="Controles Específicos Zoom G3X">
                                <option value="20">20 - Effect Block 1</option>
                                <option value="21">21 - Effect Block 2</option>
                                <option value="22">22 - Effect Block 3</option>
                                <option value="23">23 - Effect Block 4</option>
                                <option value="24">24 - Effect Block 5</option>
                                <option value="25">25 - Effect Block 6</option>
                                <option value="26">26 - Tuner</option>
                                <option value="27">27 - Tap Tempo</option>
                            </optgroup>
                            <optgroup label="Custom">
                                <option value="custom">Custom (0-127)</option>
                            </optgroup>
                        </select>
                    </div>
                    <div id="cc-custom-field" style="display: none;">
                        <div class="form-group">
                            <label>CC Number Custom (0-127)</label>
                            <input type="number" name="cc_custom" min="0" max="127" class="form-input" placeholder="Digite o número do CC">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Valor (0-127)</label>
                        <input type="range" name="value" min="0" max="127" value="64" class="form-input" oninput="this.nextElementSibling.value = this.value">
                        <output>64</output>
                    </div>
                `;
            } else if (type === 'note_on') {
                // Note On - Notas musicais
                html = `
                    <div class="form-group">
                        <label>Nota</label>
                        <select name="note" class="form-input" required>
                            <option value="">Selecione uma nota...</option>
                            <optgroup label="Notas Baixas (E2-G3)">
                                <option value="40">40 - E2</option>
                                <option value="41">41 - F2</option>
                                <option value="42">42 - F#2</option>
                                <option value="43">43 - G2</option>
                                <option value="44">44 - G#2</option>
                                <option value="45">45 - A2</option>
                                <option value="46">46 - A#2</option>
                                <option value="47">47 - B2</option>
                                <option value="48">48 - C3</option>
                                <option value="49">49 - C#3</option>
                                <option value="50">50 - D3</option>
                                <option value="51">51 - D#3</option>
                                <option value="52">52 - E3</option>
                                <option value="53">53 - F3</option>
                                <option value="54">54 - F#3</option>
                                <option value="55">55 - G3</option>
                            </optgroup>
                            <optgroup label="Notas Médias (G#3-B4)">
                                <option value="56">56 - G#3</option>
                                <option value="57">57 - A3</option>
                                <option value="58">58 - A#3</option>
                                <option value="59">59 - B3</option>
                                <option value="60">60 - C4 (Middle C)</option>
                                <option value="61">61 - C#4</option>
                                <option value="62">62 - D4</option>
                                <option value="63">63 - D#4</option>
                                <option value="64">64 - E4</option>
                                <option value="65">65 - F4</option>
                                <option value="66">66 - F#4</option>
                                <option value="67">67 - G4</option>
                                <option value="68">68 - G#4</option>
                                <option value="69">69 - A4</option>
                                <option value="70">70 - A#4</option>
                                <option value="71">71 - B4</option>
                            </optgroup>
                            <optgroup label="Notas Altas (C5-E6)">
                                <option value="72">72 - C5</option>
                                <option value="73">73 - C#5</option>
                                <option value="74">74 - D5</option>
                                <option value="75">75 - D#5</option>
                                <option value="76">76 - E5</option>
                                <option value="77">77 - F5</option>
                                <option value="78">78 - F#5</option>
                                <option value="79">79 - G5</option>
                                <option value="80">80 - G#5</option>
                                <option value="81">81 - A5</option>
                                <option value="82">82 - A#5</option>
                                <option value="83">83 - B5</option>
                                <option value="84">84 - C6</option>
                                <option value="85">85 - C#6</option>
                                <option value="86">86 - D6</option>
                                <option value="87">87 - D#6</option>
                                <option value="88">88 - E6</option>
                            </optgroup>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Velocidade (0-127)</label>
                        <input type="range" name="velocity" min="0" max="127" value="100" class="form-input" oninput="this.nextElementSibling.value = this.value">
                        <output>100</output>
                    </div>
                `;
            } else if (type === 'note_off') {
                // Note Off - Mesmas notas, sem velocidade
                html = `
                    <div class="form-group">
                        <label>Nota</label>
                        <select name="note" class="form-input" required>
                            <option value="">Selecione uma nota...</option>
                            <optgroup label="Notas Baixas (E2-G3)">
                                <option value="40">40 - E2</option>
                                <option value="41">41 - F2</option>
                                <option value="42">42 - F#2</option>
                                <option value="43">43 - G2</option>
                                <option value="44">44 - G#2</option>
                                <option value="45">45 - A2</option>
                                <option value="46">46 - A#2</option>
                                <option value="47">47 - B2</option>
                                <option value="48">48 - C3</option>
                                <option value="49">49 - C#3</option>
                                <option value="50">50 - D3</option>
                                <option value="51">51 - D#3</option>
                                <option value="52">52 - E3</option>
                                <option value="53">53 - F3</option>
                                <option value="54">54 - F#3</option>
                                <option value="55">55 - G3</option>
                            </optgroup>
                            <optgroup label="Notas Médias (G#3-B4)">
                                <option value="56">56 - G#3</option>
                                <option value="57">57 - A3</option>
                                <option value="58">58 - A#3</option>
                                <option value="59">59 - B3</option>
                                <option value="60">60 - C4 (Middle C)</option>
                                <option value="61">61 - C#4</option>
                                <option value="62">62 - D4</option>
                                <option value="63">63 - D#4</option>
                                <option value="64">64 - E4</option>
                                <option value="65">65 - F4</option>
                                <option value="66">66 - F#4</option>
                                <option value="67">67 - G4</option>
                                <option value="68">68 - G#4</option>
                                <option value="69">69 - A4</option>
                                <option value="70">70 - A#4</option>
                                <option value="71">71 - B4</option>
                            </optgroup>
                            <optgroup label="Notas Altas (C5-E6)">
                                <option value="72">72 - C5</option>
                                <option value="73">73 - C#5</option>
                                <option value="74">74 - D5</option>
                                <option value="75">75 - D#5</option>
                                <option value="76">76 - E5</option>
                                <option value="77">77 - F5</option>
                                <option value="78">78 - F#5</option>
                                <option value="79">79 - G5</option>
                                <option value="80">80 - G#5</option>
                                <option value="81">81 - A5</option>
                                <option value="82">82 - A#5</option>
                                <option value="83">83 - B5</option>
                                <option value="84">84 - C6</option>
                                <option value="85">85 - C#6</option>
                                <option value="86">86 - D6</option>
                                <option value="87">87 - D#6</option>
                                <option value="88">88 - E6</option>
                            </optgroup>
                        </select>
                    </div>
                `;
            }
            paramsDiv.innerHTML = html;
        });
    }

    // Handler para seleção de CC custom
    handleCCSelection(value) {
        const customField = document.getElementById('cc-custom-field');
        if (value === 'custom') {
            customField.style.display = 'block';
        } else {
            customField.style.display = 'none';
        }
    }

    // Atualizar patches da Zoom G3X
    async refreshZoomPatches() {
        try {
            this.showNotification('Atualizando patches da Zoom G3X...', 'info');
            
            // Tenta reconectar com a Zoom G3X primeiro
            const reconnectResponse = await fetch(`${this.apiBase}/midi/devices/zoom_g3x/reconnect`, {
                method: 'POST'
            });
            
            if (reconnectResponse.ok) {
                const reconnectData = await reconnectResponse.json();
                if (reconnectData.success) {
                    this.showNotification('Zoom G3X reconectada com sucesso!', 'success');
                } else {
                    this.showNotification('Erro ao reconectar Zoom G3X: ' + reconnectData.error, 'error');
                }
            }
            
            // Atualiza o status dos dispositivos
            await this.loadDeviceStatus();
            
            // Recarrega a lista de patches se estiver no modal
            const zoomBankSelect = document.getElementById('patch-zoom-bank');
            if (zoomBankSelect && zoomBankSelect.value) {
                await this.loadZoomPatchesForBank(zoomBankSelect.value);
                this.showNotification('Lista de patches atualizada!', 'success');
            }
            
        } catch (error) {
            console.error('Erro ao atualizar patches da Zoom:', error);
            this.showNotification('Erro ao atualizar patches da Zoom G3X', 'error');
        }
    }

    // Handler para mudança de patch da Zoom
    handleZoomPatchChange(patchNumber) {
        if (!patchNumber) {
            document.getElementById('zoom-effects-config').style.display = 'none';
            return;
        }
        
        // Mostra a seção de configuração de efeitos
        document.getElementById('zoom-effects-config').style.display = 'block';
        
        // Reseta os efeitos para o estado padrão (todos ligados)
        this.resetEffectsToDefault();
    }

    // Alternar configuração de efeitos
    toggleEffectsConfig(enabled) {
        const effectsGrid = document.getElementById('effects-grid');
        if (enabled) {
            effectsGrid.style.display = 'block';
        } else {
            effectsGrid.style.display = 'none';
        }
    }

    // Alternar estado de um efeito
    toggleEffect(effectNumber) {
        const effectBox = document.querySelector(`[data-effect="${effectNumber}"]`);
        const effectStatus = effectBox.querySelector('.effect-status');
        
        if (effectStatus.classList.contains('enabled')) {
            // Desliga o efeito
            effectStatus.classList.remove('enabled');
            effectStatus.classList.add('disabled');
            effectBox.classList.remove('enabled');
            effectBox.classList.add('disabled');
        } else {
            // Liga o efeito
            effectStatus.classList.remove('disabled');
            effectStatus.classList.add('enabled');
            effectBox.classList.remove('disabled');
            effectBox.classList.add('enabled');
        }
    }

    // Resetar efeitos para o estado padrão (todos ligados)
    resetEffectsToDefault() {
        const effectBoxes = document.querySelectorAll('.effect-box');
        effectBoxes.forEach(box => {
            const effectStatus = box.querySelector('.effect-status');
            effectStatus.classList.remove('disabled');
            effectStatus.classList.add('enabled');
            box.classList.remove('disabled');
            box.classList.add('enabled');
        });
    }

    // Obter configuração atual dos efeitos
    getEffectsConfig() {
        const effects = {};
        const effectBoxes = document.querySelectorAll('.effect-box');
        
        effectBoxes.forEach(box => {
            const effectNumber = box.getAttribute('data-effect');
            const isEnabled = box.querySelector('.effect-status').classList.contains('enabled');
            effects[`effect_${effectNumber}`] = {
                enabled: isEnabled
            };
        });
        
        return effects;
    }

    populateAllDeviceSelects() {
        // Popula todos os selects de dispositivos na página
        const deviceSelects = [
            'input-device',
            'output-device', 
            'output-device-select',
            'monitor-input-device',
            'patch-input-device',
            'patch-output-device'
        ];
        
        deviceSelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (!select) return;
            
            // Limpa opções existentes
            select.innerHTML = '<option value="">Selecione...</option>';
            
            if (selectId.includes('input') || selectId.includes('monitor')) {
                // Popula com dispositivos de entrada
                const inputDevices = this.devices.inputs || [];
                inputDevices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.name;
                    option.textContent = `${device.name} (${device.real_name})`;
                    select.appendChild(option);
                });
                
                // Seleciona o dispositivo correto baseado na configuração
                if (selectId === 'input-device' && this.midiConfig.input_device) {
                    select.value = this.midiConfig.input_device;
                } else if (selectId === 'monitor-input-device' && this.midiConfig.input_device) {
                    select.value = this.midiConfig.input_device;
                } else if (selectId === 'patch-input-device' && this.midiConfig.input_device) {
                    select.value = this.midiConfig.input_device;
                }
            } else {
                // Popula com dispositivos de saída
                const outputDevices = this.devices.outputs || [];
                outputDevices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.name;
                    option.textContent = `${device.name} (${device.real_name})`;
                    select.appendChild(option);
                });
                
                // Seleciona o dispositivo correto baseado na configuração
                if (selectId === 'output-device' && this.midiConfig.output_device) {
                    select.value = this.midiConfig.output_device;
                } else if (selectId === 'output-device-select' && this.midiConfig.output_device) {
                    select.value = this.midiConfig.output_device;
                } else if (selectId === 'patch-output-device' && this.midiConfig.output_device) {
                    select.value = this.midiConfig.output_device;
                }
            }
        });
        
        console.log('✅ Todos os selects de dispositivos foram populados sem duplicações');
    }

    renderChocolatePedal(bankNumber, connected) {
        // Calcula página de 4 bancos
        let page = Math.floor(bankNumber / 4);
        let ledIndex = bankNumber % 4;
        // Atualiza LEDs
        for (let i = 0; i < 4; i++) {
            const led = document.getElementById('led-' + i);
            if (!led) continue;
            if (connected && i === ledIndex) {
                led.classList.add('on');
                led.classList.remove('off');
            } else {
                led.classList.remove('on');
                led.classList.add('off');
            }
        }
        // Atualiza display
        const display = document.getElementById('chocolate-display');
        if (display) {
            if (connected) {
                display.textContent = ('' + (bankNumber + 1)).padStart(3, '0');
                display.classList.remove('off');
            } else {
                display.textContent = 'OFF';
                display.classList.add('off');
            }
        }
        // Atualiza ícone de conexão
        const icon = document.getElementById('chocolate-connection-icon');
        if (icon) {
            icon.classList.toggle('connected', connected);
            icon.classList.toggle('disconnected', !connected);
        }
    }

    // Função para converter banco e patch local para número sequencial global da Zoom G3X
    convertToGlobalPatchNumber(bankLetter, localPatchNumber) {
        // Mapeamento de letras para números de banco (A=0, B=1, C=2, etc.)
        const bankMapping = {
            'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4,
            'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9
        };
        
        const bankNumber = bankMapping[bankLetter.toUpperCase()] || 0;
        const globalPatchNumber = (bankNumber * 10) + parseInt(localPatchNumber);
        
        console.log(`🔄 Conversão: Banco ${bankLetter} (${bankNumber}) + Patch ${localPatchNumber} = Global ${globalPatchNumber}`);
        
        return globalPatchNumber;
    }
    
    // Função para converter número sequencial global para banco e patch local
    convertFromGlobalPatchNumber(globalPatchNumber) {
        const bankNumber = Math.floor(globalPatchNumber / 10);
        const localPatchNumber = globalPatchNumber % 10;
        
        // Mapeamento de números para letras de banco (0=A, 1=B, 2=C, etc.)
        const bankMapping = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
        const bankLetter = bankMapping[bankNumber] || 'A';
        
        console.log(`🔄 Conversão reversa: Global ${globalPatchNumber} = Banco ${bankLetter} + Patch ${localPatchNumber}`);
        
        return {
            bankLetter: bankLetter,
            patch: localPatchNumber  // Mudança aqui: patch em vez de localPatchNumber
        };
    }

    // Adiciona listeners para ordenação e visualização
    setupPatchListControls() {
        const sortCombo = document.getElementById('patch-sort-mode');
        const btnCards = document.getElementById('view-cards');
        const btnList = document.getElementById('view-list');
        if (sortCombo) {
            sortCombo.addEventListener('change', () => this.renderPatches());
        }
        if (btnCards) {
            btnCards.addEventListener('click', () => {
                this._patchViewMode = 'cards';
                this.renderPatches();
            });
        }
        if (btnList) {
            btnList.addEventListener('click', () => {
                this._patchViewMode = 'list';
                this.renderPatches();
            });
        }
    }

    // Cria uma linha para visualização em lista
    createPatchListRow(patch) {
        const inputChannel = patch.input_channel !== undefined ? patch.input_channel : '-';
        let outputDetails = '';
        // Se for patch da Zoom, sempre tenta mostrar banco/letra + número local
        if ((patch.command_type === 'pc' || patch.command_type === 'effects_config') && patch.zoom_bank) {
            let localPatch = (patch.program !== undefined && patch.program !== null) ? patch.program : undefined;
            if ((localPatch === undefined || localPatch === null) && patch.zoom_patch !== undefined && patch.zoom_patch !== null) {
                // Converte global para local
                localPatch = this.convertFromGlobalPatchNumber(patch.zoom_patch).patch;
            }
            outputDetails = `${patch.zoom_bank} / ${localPatch !== undefined && localPatch !== null ? localPatch : '-'}`;
        } else if (patch.command_type === 'pc' && patch.program !== undefined) {
            outputDetails = `PC: ${patch.program}`;
        } else if (patch.command_type === 'cc') {
            outputDetails = `CC: ${patch.cc}=${patch.value}`;
        }
        return `
            <tr>
                <td>${patch.name}</td>
                <td>${inputChannel}</td>
                <td>${patch.input_device || '-'}</td>
                <td>${outputDetails}</td>
                <td>${patch.output_device || '-'}</td>
                <td class="patch-actions">
                    <button class="btn btn-success btn-small" onclick="app.loadPatch(${patch.id})">Carregar</button>
                    <button class="btn btn-primary btn-small" onclick="app.editPatch(${patch.id})">Editar</button>
                    <button class="btn btn-danger btn-small" onclick="app.deletePatch(${patch.id})">Deletar</button>
                </td>
            </tr>
        `;
    }

    // Ativar patch na Zoom G3X ao clicar no botão
    async activatePatch(patchId) {
        try {
            const patch = this.patches.find(p => p.id === patchId);
            if (!patch) {
                this.showNotification('Patch não encontrado.', 'error');
                return;
            }
            // Chama API para ativar patch
            const response = await fetch(`${this.apiBase}/patches/${patchId}/activate`, { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.showNotification('Patch ativado na Zoom G3X!', 'success');
            } else {
                this.showNotification('Erro ao ativar patch: ' + (data.error || 'Erro desconhecido'), 'error');
            }
        } catch (e) {
            this.showNotification('Erro ao ativar patch: ' + e.message, 'error');
        }
    }

    // --- SysEx Section ---
    setupSysExSection() {
        const btnSend = document.getElementById('btn-send-sysex');
        const btnExample = document.getElementById('btn-sysex-example');
        const btnAutomate = document.getElementById('btn-sysex-automate');
        const log = document.getElementById('sysex-log');
        // Novos selects
        const inputDeviceSelect = document.getElementById('sysex-input-device');
        const outputDeviceSelect = document.getElementById('sysex-output-device');
        // Popular combos de dispositivos
        this.populateSysExDeviceSelects();
        if (!btnSend || !btnExample || !btnAutomate || !log) return;

        btnSend.onclick = async () => {
            const inputCh = parseInt(document.getElementById('sysex-input-channel').value);
            const outputCh = parseInt(document.getElementById('sysex-output-channel').value);
            const inputDevice = inputDeviceSelect.value;
            const outputDevice = outputDeviceSelect.value;
            const hex = document.getElementById('sysex-command').value.trim();
            this.logSysEx(`$ Enviando SysEx: ${hex}`);
            // Enviar para backend
            try {
                const response = await fetch(`${this.apiBase}/midi/sysex`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        command: hex,
                        input_channel: inputCh,
                        output_channel: outputCh,
                        input_device: inputDevice,
                        output_device: outputDevice
                    })
                });
                const data = await response.json();
                if (data.success) {
                    this.logSysEx('> ' + (data.result || 'Comando enviado com sucesso.'));
                } else {
                    this.logSysEx('! Erro: ' + (data.error || 'Erro desconhecido.'));
                }
            } catch (e) {
                this.logSysEx('! Erro ao enviar SysEx: ' + e.message);
            }
        };
        btnExample.onclick = () => {
            document.getElementById('sysex-command').value = 'F0 52 00 5A 09 00 00 22 F7';
            this.logSysEx('# Exemplo carregado: Carregar patch C2 (SysEx correto para Zoom G3X)');
        };
        btnAutomate.onclick = async () => {
            this.logSysEx('# Automatizando: Enviando patches C0 a C9');
            for (let i = 0; i < 10; i++) {
                const hex = `F0 52 00 5A 09 00 00 ${((2*10)+i).toString(16).padStart(2,'0').toUpperCase()} F7`;
                document.getElementById('sysex-command').value = hex;
                await new Promise(r => setTimeout(r, 400));
                btnSend.click();
            }
        };
    }

    populateSysExDeviceSelects() {
        // Preenche os selects de dispositivos de entrada e saída na seção SysEx
        const inputDeviceSelect = document.getElementById('sysex-input-device');
        const outputDeviceSelect = document.getElementById('sysex-output-device');
        if (!inputDeviceSelect || !outputDeviceSelect) return;
        // Limpa
        inputDeviceSelect.innerHTML = '<option value="">Selecione...</option>';
        outputDeviceSelect.innerHTML = '<option value="">Selecione...</option>';
        // Popula entrada
        (this.devices?.inputs || []).forEach(device => {
            const option = document.createElement('option');
            option.value = device.name;
            option.textContent = `${device.name} (${device.real_name})`;
            inputDeviceSelect.appendChild(option);
        });
        // Popula saída
        (this.devices?.outputs || []).forEach(device => {
            const option = document.createElement('option');
            option.value = device.name;
            option.textContent = `${device.name} (${device.real_name})`;
            outputDeviceSelect.appendChild(option);
        });
    }

    logSysEx(msg) {
        const log = document.getElementById('sysex-log');
        if (!log) return;
        log.textContent += (log.textContent ? '\n' : '') + msg;
        log.scrollTop = log.scrollHeight;
    }

    // ========================================
    // FUNCIONALIDADES DA TELA DE CHECKUP
    // ========================================
    
    setupCheckupEventListeners() {
        // Botão para ler log do sistema
        const readLogBtn = document.getElementById('read-system-log');
        if (readLogBtn) {
            readLogBtn.addEventListener('click', () => this.readSystemLog());
        }
        
        // Botão para testar conectividade
        const testConnectivityBtn = document.getElementById('test-connectivity');
        if (testConnectivityBtn) {
            testConnectivityBtn.addEventListener('click', () => this.testConnectivity());
        }
        
        // Botão para listar dispositivos
        const listDevicesBtn = document.getElementById('list-devices');
        if (listDevicesBtn) {
            listDevicesBtn.addEventListener('click', () => this.listDevices());
        }
        
        // Botão para reconectar entrada MIDI
        const reconnectInputBtn = document.getElementById('reconnect-midi-input');
        if (reconnectInputBtn) {
            reconnectInputBtn.addEventListener('click', () => this.reconnectMidiInput());
        }
        
        // Botão para reconectar saída MIDI
        const reconnectOutputBtn = document.getElementById('reconnect-midi-output');
        if (reconnectOutputBtn) {
            reconnectOutputBtn.addEventListener('click', () => this.reconnectMidiOutput());
        }
        
        // Select para quantidade de linhas do log
        const logLinesSelect = document.getElementById('log-lines');
        if (logLinesSelect) {
            logLinesSelect.addEventListener('change', (e) => {
                this.logLines = parseInt(e.target.value);
            });
        }
    }
    
    async readSystemLog() {
        try {
            const logLines = document.getElementById('log-lines')?.value || 50;
            const logOutput = document.getElementById('system-log-output');
            
            if (!logOutput) {
                console.error('Elemento system-log-output não encontrado');
                return;
            }
            
            // Mostrar loading
            logOutput.innerHTML = '<div class="loading">📋 Carregando log do sistema...</div>';
            
            const response = await fetch(`/api/checkup/system-log?lines=${logLines}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Formatar o log para exibição
                const formattedLog = this.formatSystemLog(data.log);
                logOutput.innerHTML = `<pre class="log-content">${formattedLog}</pre>`;
                this.showNotification('Log do sistema carregado com sucesso', 'success');
            } else {
                logOutput.innerHTML = `<div class="error">❌ Erro: ${data.error || 'Erro desconhecido'}</div>`;
                this.showNotification('Erro ao carregar log do sistema', 'error');
            }
            
        } catch (error) {
            console.error('Erro ao ler log do sistema:', error);
            const logOutput = document.getElementById('system-log-output');
            if (logOutput) {
                logOutput.innerHTML = `<div class="error">❌ Erro de conexão: ${error.message}</div>`;
            }
            this.showNotification('Erro de conexão ao carregar log', 'error');
        }
    }
    
    formatSystemLog(logText) {
        if (!logText) return 'Log vazio';
        
        // Quebrar em linhas e adicionar numeração
        const lines = logText.split('\n');
        const formattedLines = lines.map((line, index) => {
            const lineNumber = (index + 1).toString().padStart(4, ' ');
            return `${lineNumber}: ${line}`;
        });
        
        return formattedLines.join('\n');
    }
    
    async testConnectivity() {
        try {
            const connectivityOutput = document.getElementById('connectivity-output');
            
            if (!connectivityOutput) {
                console.error('Elemento connectivity-output não encontrado');
                return;
            }
            
            // Mostrar loading
            connectivityOutput.innerHTML = '<div class="loading">🔍 Testando conectividade...</div>';
            
            const response = await fetch('/api/checkup/test-connectivity');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                const results = data.results;
                let html = '<div class="connectivity-results">';
                
                // Teste de rede
                html += `<div class="test-result ${results.network ? 'success' : 'error'}">`;
                html += `<span class="test-icon">${results.network ? '✅' : '❌'}</span>`;
                html += `<span class="test-name">Rede</span>`;
                html += `<span class="test-details">${results.network ? 'Conectado' : 'Sem conexão'}</span>`;
                html += '</div>';
                
                // Teste de MIDI
                html += `<div class="test-result ${results.midi ? 'success' : 'error'}">`;
                html += `<span class="test-icon">${results.midi ? '✅' : '❌'}</span>`;
                html += `<span class="test-name">MIDI</span>`;
                html += `<span class="test-details">${results.midi ? 'Dispositivos disponíveis' : 'Nenhum dispositivo'}</span>`;
                html += '</div>';
                
                // Teste de banco de dados
                html += `<div class="test-result ${results.database ? 'success' : 'error'}">`;
                html += `<span class="test-icon">${results.database ? '✅' : '❌'}</span>`;
                html += `<span class="test-name">Banco de Dados</span>`;
                html += `<span class="test-details">${results.database ? 'Conectado' : 'Erro de conexão'}</span>`;
                html += '</div>';
                
                // Teste de cache
                html += `<div class="test-result ${results.cache ? 'success' : 'error'}">`;
                html += `<span class="test-icon">${results.cache ? '✅' : '❌'}</span>`;
                html += `<span class="test-name">Cache</span>`;
                html += `<span class="test-details">${results.cache ? 'Funcionando' : 'Erro no cache'}</span>`;
                html += '</div>';
                
                html += '</div>';
                connectivityOutput.innerHTML = html;
                
                this.showNotification('Teste de conectividade concluído', 'success');
            } else {
                connectivityOutput.innerHTML = `<div class="error">❌ Erro: ${data.error || 'Erro desconhecido'}</div>`;
                this.showNotification('Erro no teste de conectividade', 'error');
            }
            
        } catch (error) {
            console.error('Erro ao testar conectividade:', error);
            const connectivityOutput = document.getElementById('connectivity-output');
            if (connectivityOutput) {
                connectivityOutput.innerHTML = `<div class="error">❌ Erro de conexão: ${error.message}</div>`;
            }
            this.showNotification('Erro de conexão no teste', 'error');
        }
    }
    
    async listDevices() {
        try {
            const devicesOutput = document.getElementById('devices-output');
            
            if (!devicesOutput) {
                console.error('Elemento devices-output não encontrado');
                return;
            }
            
            // Mostrar loading
            devicesOutput.innerHTML = '<div class="loading">🔍 Listando dispositivos...</div>';
            
            const response = await fetch('/api/checkup/list-devices');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                const devices = data.devices;
                let html = '<div class="devices-list">';
                
                if (devices.inputs && devices.inputs.length > 0) {
                    html += '<div class="device-category">';
                    html += '<h4>🎹 Entradas MIDI</h4>';
                    devices.inputs.forEach(device => {
                        html += `<div class="device-item">`;
                        html += `<span class="device-name">${device.name}</span>`;
                        html += `<span class="device-type">${device.type}</span>`;
                        html += '</div>';
                    });
                    html += '</div>';
                } else {
                    html += '<div class="device-category">';
                    html += '<h4>🎹 Entradas MIDI</h4>';
                    html += '<div class="no-devices">Nenhuma entrada MIDI encontrada</div>';
                    html += '</div>';
                }
                
                if (devices.outputs && devices.outputs.length > 0) {
                    html += '<div class="device-category">';
                    html += '<h4>🔊 Saídas MIDI</h4>';
                    devices.outputs.forEach(device => {
                        html += `<div class="device-item">`;
                        html += `<span class="device-name">${device.name}</span>`;
                        html += `<span class="device-type">${device.type}</span>`;
                        html += '</div>';
                    });
                    html += '</div>';
                } else {
                    html += '<div class="device-category">';
                    html += '<h4>🔊 Saídas MIDI</h4>';
                    html += '<div class="no-devices">Nenhuma saída MIDI encontrada</div>';
                    html += '</div>';
                }
                
                html += '</div>';
                devicesOutput.innerHTML = html;
                
                this.showNotification('Dispositivos listados com sucesso', 'success');
            } else {
                devicesOutput.innerHTML = `<div class="error">❌ Erro: ${data.error || 'Erro desconhecido'}</div>`;
                this.showNotification('Erro ao listar dispositivos', 'error');
            }
            
        } catch (error) {
            console.error('Erro ao listar dispositivos:', error);
            const devicesOutput = document.getElementById('devices-output');
            if (devicesOutput) {
                devicesOutput.innerHTML = `<div class="error">❌ Erro de conexão: ${error.message}</div>`;
            }
            this.showNotification('Erro de conexão ao listar dispositivos', 'error');
        }
    }
    
    async reconnectMidiInput() {
        try {
            const reconnectOutput = document.getElementById('reconnect-output');
            
            if (!reconnectOutput) {
                console.error('Elemento reconnect-output não encontrado');
                return;
            }
            
            // Mostrar loading
            reconnectOutput.innerHTML = '<div class="loading">🔄 Reconectando entrada MIDI...</div>';
            
            const response = await fetch('/api/checkup/reconnect-midi-input', { method: 'POST' });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                reconnectOutput.innerHTML = `<div class="success">✅ Entrada MIDI reconectada com sucesso</div>`;
                this.showNotification('Entrada MIDI reconectada', 'success');
                
                // Recarregar dispositivos após reconexão
                setTimeout(() => {
                    this.loadDevices();
                }, 1000);
            } else {
                reconnectOutput.innerHTML = `<div class="error">❌ Erro: ${data.error || 'Erro desconhecido'}</div>`;
                this.showNotification('Erro ao reconectar entrada MIDI', 'error');
            }
            
        } catch (error) {
            console.error('Erro ao reconectar entrada MIDI:', error);
            const reconnectOutput = document.getElementById('reconnect-output');
            if (reconnectOutput) {
                reconnectOutput.innerHTML = `<div class="error">❌ Erro de conexão: ${error.message}</div>`;
            }
            this.showNotification('Erro de conexão na reconexão', 'error');
        }
    }
    
    async reconnectMidiOutput() {
        try {
            const reconnectOutput = document.getElementById('reconnect-output');
            
            if (!reconnectOutput) {
                console.error('Elemento reconnect-output não encontrado');
                return;
            }
            
            // Mostrar loading
            reconnectOutput.innerHTML = '<div class="loading">🔄 Reconectando saída MIDI...</div>';
            
            const response = await fetch('/api/checkup/reconnect-midi-output', { method: 'POST' });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                reconnectOutput.innerHTML = `<div class="success">✅ Saída MIDI reconectada com sucesso</div>`;
                this.showNotification('Saída MIDI reconectada', 'success');
                
                // Recarregar dispositivos após reconexão
                setTimeout(() => {
                    this.loadDevices();
                }, 1000);
            } else {
                reconnectOutput.innerHTML = `<div class="error">❌ Erro: ${data.error || 'Erro desconhecido'}</div>`;
                this.showNotification('Erro ao reconectar saída MIDI', 'error');
            }
            
        } catch (error) {
            console.error('Erro ao reconectar saída MIDI:', error);
            const reconnectOutput = document.getElementById('reconnect-output');
            if (reconnectOutput) {
                reconnectOutput.innerHTML = `<div class="error">❌ Erro de conexão: ${error.message}</div>`;
            }
            this.showNotification('Erro de conexão na reconexão', 'error');
        }
    }
    
    // Inicializar funcionalidades de checkup se estivermos na página de checkup
    initCheckupPage() {
        if (window.location.pathname === '/checkup') {
            this.setupCheckupEventListeners();
            console.log('✅ Funcionalidades de checkup inicializadas');
        }
    }

    selectDeviceOption(name, value) {
        if (value === 'input') {
            this.selectDevice(name, 'input');
        } else if (value === 'output') {
            this.selectDevice(name, 'output');
        } else {
            // Desmarcar: remove seleção se for o dispositivo atual
            if (this.midiConfig.input_device === name) {
                this.midiConfig.input_device = '';
            }
            if (this.midiConfig.output_device === name) {
                this.midiConfig.output_device = '';
            }
            this.renderDevices();
            this.saveMidiConfig();
        }
    }
}

// Inicializar aplicação
const app = new RaspMIDI();

// Inicializar checkup se necessário
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/checkup') {
        app.initCheckupPage();
    }
}); 