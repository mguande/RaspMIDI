// Correção para o carregamento infinito de patches
// Execute este código no console do navegador

console.log("🔄 Corrigindo carregamento infinito de patches...");

// Para qualquer carregamento em andamento
if (window.app && window.app.patches) {
    console.log("🛑 Parando carregamento de patches...");
    window.app.patches = [];
}

// Função para forçar parada do carregamento
function stopInfiniteLoading() {
    console.log("🛑 Parando carregamento infinito...");
    
    try {
        // 1. Limpa patches para parar loops
        if (window.app) {
            window.app.patches = [];
        }
        
        // 2. Força navegação para dispositivos (que não carrega patches)
        const menuItems = document.querySelectorAll('.menu-item');
        const contentSections = document.querySelectorAll('.content-section');
        
        menuItems.forEach(menuItem => menuItem.classList.remove('active'));
        contentSections.forEach(section => section.classList.remove('active'));
        
        const devicesItem = document.querySelector('[data-section="dispositivos"]');
        const devicesSection = document.getElementById('dispositivos');
        
        if (devicesItem) devicesItem.classList.add('active');
        if (devicesSection) devicesSection.classList.add('active');
        
        window.location.hash = 'dispositivos';
        
        // 3. Limpa o container de patches
        const patchesContainer = document.getElementById('patches-container');
        if (patchesContainer) {
            patchesContainer.innerHTML = `
                <div class="card text-center">
                    <p>Carregamento interrompido. Clique em "Patches" para tentar novamente.</p>
                    <button class="btn btn-primary" onclick="window.app.loadPatches()">
                        Carregar Patches
                    </button>
                </div>
            `;
        }
        
        console.log("✅ Carregamento infinito parado");
        
    } catch (error) {
        console.error("❌ Erro ao parar carregamento:", error);
    }
}

// Função para testar carregamento de patches de forma segura
async function safeLoadPatches() {
    console.log("🔄 Testando carregamento seguro de patches...");
    
    try {
        // Define um timeout para evitar carregamento infinito
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Timeout - carregamento demorou muito')), 5000);
        });
        
        const fetchPromise = fetch('/api/patches');
        
        const response = await Promise.race([fetchPromise, timeoutPromise]);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ ${data.data.length} patches carregados com sucesso`);
            
            // Atualiza patches de forma segura
            if (window.app) {
                window.app.patches = data.data || [];
                
                // Renderiza apenas se estiver na seção de patches
                const patchesSection = document.getElementById('patches');
                if (patchesSection && patchesSection.classList.contains('active')) {
                    window.app.renderPatches();
                }
            }
            
            return true;
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error("❌ Erro no carregamento seguro:", error);
        return false;
    }
}

// Função para navegar para patches de forma segura
function safeNavigateToPatches() {
    console.log("🧭 Navegando para patches de forma segura...");
    
    try {
        // Remove active de todos
        const menuItems = document.querySelectorAll('.menu-item');
        const contentSections = document.querySelectorAll('.content-section');
        
        menuItems.forEach(menuItem => menuItem.classList.remove('active'));
        contentSections.forEach(section => section.classList.remove('active'));
        
        // Ativa patches
        const patchesItem = document.querySelector('[data-section="patches"]');
        const patchesSection = document.getElementById('patches');
        
        if (patchesItem) patchesItem.classList.add('active');
        if (patchesSection) patchesSection.classList.add('active');
        
        window.location.hash = 'patches';
        
        // Carrega patches de forma segura
        setTimeout(() => {
            safeLoadPatches();
        }, 100);
        
        console.log("✅ Navegação para patches concluída");
        
    } catch (error) {
        console.error("❌ Erro na navegação para patches:", error);
    }
}

// Executa correção imediata
stopInfiniteLoading();

// Adiciona funções ao objeto global
window.stopInfiniteLoading = stopInfiniteLoading;
window.safeLoadPatches = safeLoadPatches;
window.safeNavigateToPatches = safeNavigateToPatches;

console.log("🔧 Funções disponíveis:");
console.log("  - stopInfiniteLoading() - Para carregamento infinito");
console.log("  - safeLoadPatches() - Carrega patches de forma segura");
console.log("  - safeNavigateToPatches() - Navega para patches de forma segura");

console.log("✅ Correção aplicada. Agora você pode:");
console.log("  1. Clicar nos itens do menu normalmente");
console.log("  2. Usar safeNavigateToPatches() para ir para patches");
console.log("  3. Usar safeLoadPatches() para carregar patches sem travamento"); 