// Script de correção para o problema de travamento da navegação
// Execute este código no console do navegador (F12)

console.log("🔧 Aplicando correção de navegação...");

// Função para forçar navegação para uma seção
function forceNavigateToSection(sectionName) {
    console.log(`🧭 Forçando navegação para: ${sectionName}`);
    
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
    } else {
        console.warn(`⚠️ Menu item não encontrado: ${sectionName}`);
    }
    
    // Adiciona active à seção correta
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
        console.log(`✅ Seção ativada: ${sectionName}`);
    } else {
        console.warn(`⚠️ Seção não encontrada: ${sectionName}`);
    }
    
    // Atualiza URL hash
    window.location.hash = sectionName;
}

// Função para recarregar patches com tratamento de erro
async function forceReloadPatches() {
    try {
        console.log("🔄 Forçando recarregamento de patches...");
        
        const response = await fetch('/api/patches');
        console.log("📥 Resposta recebida, status:", response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log("📋 Dados dos patches:", data);
        
        if (data.success) {
            console.log(`✅ ${data.data.length} patches carregados`);
            
            // Atualiza a variável global de patches
            if (window.app && window.app.patches) {
                window.app.patches = data.data;
                console.log("✅ Variável de patches atualizada");
                
                // Força renderização
                if (window.app.renderPatches) {
                    window.app.renderPatches();
                    console.log("✅ Patches renderizados");
                }
            } else {
                console.warn("⚠️ Objeto app não encontrado");
            }
        } else {
            console.error("❌ Erro na resposta:", data.error);
        }
        
    } catch (error) {
        console.error('❌ Erro ao recarregar patches:', error);
    }
}

// Função para limpar cache e forçar recarregamento
async function forceClearAndReload() {
    try {
        console.log("🧹 Limpando cache...");
        
        const response = await fetch('/api/cache/reload', {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.success) {
            console.log("✅ Cache limpo");
        } else {
            console.warn("⚠️ Erro ao limpar cache:", data.error);
        }
        
        // Recarrega patches
        await forceReloadPatches();
        
    } catch (error) {
        console.error('❌ Erro ao limpar cache:', error);
    }
}

// Função principal de correção
async function applyFix() {
    console.log("🚀 Iniciando correção...");
    
    // 1. Força navegação para patches
    forceNavigateToSection('patches');
    
    // 2. Aguarda um pouco
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 3. Limpa cache e recarrega patches
    await forceClearAndReload();
    
    console.log("✅ Correção aplicada!");
}

// Executa a correção
applyFix();

// Adiciona funções ao objeto global para uso manual
window.forceNavigateToSection = forceNavigateToSection;
window.forceReloadPatches = forceReloadPatches;
window.forceClearAndReload = forceClearAndReload;
window.applyFix = applyFix;

console.log("🔧 Funções disponíveis:");
console.log("  - applyFix() - Aplica correção completa");
console.log("  - forceNavigateToSection('patches') - Navega para patches");
console.log("  - forceReloadPatches() - Recarrega patches");
console.log("  - forceClearAndReload() - Limpa cache e recarrega"); 