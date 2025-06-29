// Script para executar no console do navegador
// Copie e cole este código no console (F12 → Console)

async function checkPatches() {
    console.log("🔍 Verificando patches via API...");
    
    try {
        // Verificar todos os patches
        const response = await fetch('/api/patches');
        const data = await response.json();
        
        console.log("📋 Todos os patches:", data);
        
        if (data.success && data.data) {
            console.log(`📊 Total de patches: ${data.data.length}`);
            
            // Verificar patches com input_channel
            const patchesWithChannel = data.data.filter(p => p.input_channel !== null && p.input_channel !== undefined);
            console.log(`📡 Patches com input_channel: ${patchesWithChannel.length}`);
            patchesWithChannel.forEach(p => {
                console.log(`  ID ${p.id}: "${p.name}" - Canal ${p.input_channel}`);
            });
            
            // Verificar patches com zoom_patch
            const patchesWithZoom = data.data.filter(p => p.zoom_patch !== null && p.zoom_patch !== undefined);
            console.log(`🎸 Patches com zoom_patch: ${patchesWithZoom.length}`);
            patchesWithZoom.forEach(p => {
                console.log(`  ID ${p.id}: "${p.name}" - Banco ${p.zoom_bank}, Patch ${p.zoom_patch}`);
            });
            
            // Mostrar estrutura de alguns patches
            console.log("🔍 Estrutura dos primeiros patches:");
            data.data.slice(0, 3).forEach((patch, index) => {
                console.log(`  Patch ${index + 1}:`, patch);
            });
        }
        
    } catch (error) {
        console.error("❌ Erro ao verificar patches:", error);
    }
}

// Executar verificação
checkPatches(); 