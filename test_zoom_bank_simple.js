// Script simples para testar zoom_bank
// Cole no console do navegador

console.log('🧪 Teste simples do zoom_bank');

// 1. Verificar se o select existe
const select = document.getElementById('patch-zoom-bank');
if (select) {
    console.log('✅ Select encontrado');
    console.log('Valor atual:', select.value);
    console.log('Opções disponíveis:');
    for (let i = 0; i < select.options.length; i++) {
        console.log(`  ${i}: ${select.options[i].value} - ${select.options[i].text}`);
    }
} else {
    console.log('❌ Select não encontrado');
}

// 2. Testar mudança manual
if (select) {
    console.log('\n🧪 Testando mudança para banco B...');
    select.value = 'B';
    console.log('Valor após mudança:', select.value);
    
    // Disparar evento
    select.dispatchEvent(new Event('change'));
    console.log('Evento change disparado');
}

// 3. Verificar FormData
const form = document.querySelector('#new-patch-form');
if (form) {
    const formData = new FormData(form);
    const zoomBank = formData.get('zoom_bank');
    console.log('\n📋 FormData zoom_bank:', zoomBank);
} else {
    console.log('\n❌ Formulário não encontrado');
} 