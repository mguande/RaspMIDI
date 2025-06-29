// Correção temporária para o problema de travamento ao carregar patches
// Adicione este código no console do navegador para testar

// Sobrescreve o método loadPatches com melhor tratamento de erro
app.loadPatches = async function() {
    try {
        console.log("🔄 Carregando patches...");
        const response = await fetch(`${this.apiBase}/patches`);
        console.log("📥 Resposta recebida, status:", response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log("📋 Dados dos patches:", data);
        
        if (data.success) {
            console.log(`✅ ${data.data.length} patches carregados`);
            
            // Valida se data.data é um array
            if (!Array.isArray(data.data)) {
                console.error("❌ Dados de patches não são um array:", data.data);
                this.patches = [];
            } else {
                this.patches = data.data;
            }
            
            console.log("🎨 Renderizando patches...");
            this.renderPatches();
            console.log("✅ Patches renderizados");
        } else {
            console.error("❌ Erro na resposta:", data.error);
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('❌ Erro ao carregar patches:', error);
        this.showNotification('Erro ao carregar patches: ' + error.message, 'error');
        // Em caso de erro, define patches como array vazio para evitar travamento
        this.patches = [];
        this.renderPatches();
    }
};

// Sobrescreve o método renderPatches com melhor tratamento de erro
app.renderPatches = function() {
    try {
        console.log("🎨 Iniciando renderização de patches...");
        const container = document.getElementById('patches-container');
        console.log("📦 Container encontrado:", !!container);
        
        if (!container) {
            console.warn("⚠️ Container de patches não encontrado");
            return;
        }
        
        console.log(`📊 Renderizando ${this.patches.length} patches`);
        
        if (!Array.isArray(this.patches) || this.patches.length === 0) {
            console.log("📭 Nenhum patch para renderizar");
            container.innerHTML = `
                <div class="card text-center">
                    <p>Nenhum patch encontrado. Crie seu primeiro patch!</p>
                    <button class="btn btn-primary" onclick="app.showNewPatchModal()">
                        Criar Patch
                    </button>
                </div>
            `;
            return;
        }
        
        console.log("🔨 Criando HTML dos patches...");
        const patchesHtml = this.patches.map(patch => {
            try {
                console.log("🔧 Criando card para patch:", patch.name || 'Sem nome');
                return this.createPatchCard(patch);
            } catch (error) {
                console.error("❌ Erro ao criar card para patch:", patch, error);
                return `<div class="patch-card error">Erro ao carregar patch: ${patch.name || 'Sem nome'}</div>`;
            }
        }).join('');
        
        console.log("📝 HTML criado, aplicando ao container...");
        container.innerHTML = `
            <div class="patches-grid">
                ${patchesHtml}
            </div>
        `;
        console.log("✅ Patches renderizados com sucesso");
    } catch (error) {
        console.error("❌ Erro ao renderizar patches:", error);
        const container = document.getElementById('patches-container');
        if (container) {
            container.innerHTML = `
                <div class="card text-center error">
                    <p>Erro ao carregar patches: ${error.message}</p>
                    <button class="btn btn-primary" onclick="app.loadPatches()">
                        Tentar Novamente
                    </button>
                </div>
            `;
        }
    }
};

// Força recarregamento dos patches
console.log("🔧 Aplicando correção de patches...");
app.loadPatches(); 