// Script para executar no console do navegador
// Copie e cole este código no console (F12 → Console)

async function clearAllPatches() {
    console.log("🗑️ Limpando todos os patches...");
    
    try {
        // Deletar todos os patches via API
        const response = await fetch('/api/patches', {
            method: 'GET'
        });
        const data = await response.json();
        
        if (data.success && data.data) {
            console.log(`📊 Patches encontrados: ${data.data.length}`);
            
            // Deletar cada patch
            for (const patch of data.data) {
                console.log(`🗑️ Deletando patch ${patch.id}: ${patch.name}`);
                
                const deleteResponse = await fetch(`/api/patches/${patch.id}`, {
                    method: 'DELETE'
                });
                
                if (deleteResponse.ok) {
                    console.log(`✅ Patch ${patch.id} deletado`);
                } else {
                    console.log(`❌ Erro ao deletar patch ${patch.id}`);
                }
            }
            
            // Verificar se foram deletados
            const checkResponse = await fetch('/api/patches');
            const checkData = await checkResponse.json();
            
            console.log(`📊 Patches restantes: ${checkData.data?.length || 0}`);
            
            if (checkData.data?.length === 0) {
                console.log("✅ Todos os patches foram removidos!");
            } else {
                console.log("⚠️ Ainda há patches no banco");
            }
        } else {
            console.log("ℹ️ Nenhum patch encontrado");
        }
        
    } catch (error) {
        console.error("❌ Erro:", error);
    }
}

// Executar limpeza
clearAllPatches(); 