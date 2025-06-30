// Script para adicionar logs de debug temporários
// Execute este código no console do navegador para adicionar logs temporários

// 1. Adicionar log na função handleZoomBankChange
if (window.app && window.app.handleZoomBankChange) {
    const originalHandleZoomBankChange = window.app.handleZoomBankChange;
    window.app.handleZoomBankChange = function(bankLetter) {
        console.log('🔍 [DEBUG] handleZoomBankChange chamada com:', bankLetter);
        console.log('🔍 [DEBUG] Tipo do bankLetter:', typeof bankLetter);
        return originalHandleZoomBankChange.call(this, bankLetter);
    };
    console.log('✅ Log adicionado em handleZoomBankChange');
}

// 2. Adicionar log na coleta do FormData
if (window.app && window.app.createPatch) {
    const originalCreatePatch = window.app.createPatch;
    window.app.createPatch = function() {
        console.log('🔍 [DEBUG] createPatch iniciado');
        
        const form = document.getElementById('new-patch-form');
        if (form) {
            const formData = new FormData(form);
            const zoomBank = formData.get('zoom_bank');
            console.log('🔍 [DEBUG] zoom_bank coletado do FormData:', zoomBank);
            console.log('🔍 [DEBUG] Tipo do zoomBank:', typeof zoomBank);
        }
        
        return originalCreatePatch.call(this);
    };
    console.log('✅ Log adicionado em createPatch');
}

// 3. Adicionar log na função updatePatch
if (window.app && window.app.updatePatch) {
    const originalUpdatePatch = window.app.updatePatch;
    window.app.updatePatch = function(patchId) {
        console.log('🔍 [DEBUG] updatePatch iniciado para ID:', patchId);
        
        const form = document.getElementById('new-patch-form');
        if (form) {
            const formData = new FormData(form);
            const zoomBank = formData.get('zoom_bank');
            console.log('🔍 [DEBUG] zoom_bank coletado do FormData (update):', zoomBank);
            console.log('🔍 [DEBUG] Tipo do zoomBank (update):', typeof zoomBank);
        }
        
        return originalUpdatePatch.call(this, patchId);
    };
    console.log('✅ Log adicionado em updatePatch');
}

// 4. Monitorar mudanças no select
const select = document.getElementById('patch-zoom-bank');
if (select) {
    select.addEventListener('change', function(e) {
        console.log('🔍 [DEBUG] Select zoom_bank mudou para:', e.target.value);
        console.log('🔍 [DEBUG] Tipo do valor:', typeof e.target.value);
    });
    console.log('✅ Monitoramento adicionado ao select zoom_bank');
}

// 5. Verificar se o select está sendo atualizado corretamente
if (window.app && window.app.setFormValue) {
    const originalSetFormValue = window.app.setFormValue;
    window.app.setFormValue = function(fieldId, value) {
        if (fieldId === 'zoom_bank') {
            console.log('🔍 [DEBUG] setFormValue chamado para zoom_bank com valor:', value);
            console.log('🔍 [DEBUG] Tipo do valor:', typeof value);
        }
        return originalSetFormValue.call(this, fieldId, value);
    };
    console.log('✅ Log adicionado em setFormValue para zoom_bank');
}

console.log('🎯 Logs de debug adicionados!');
console.log('📝 Agora teste:');
console.log('  1. Abra o modal de novo patch');
console.log('  2. Mude o banco de A para B');
console.log('  3. Preencha os outros campos');
console.log('  4. Clique em Salvar');
console.log('  5. Veja os logs no console'); 