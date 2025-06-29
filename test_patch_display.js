// Script de teste para verificar a nova exibição de patches
console.log('🔧 Testando nova exibição de patches...');

// Função para testar a renderização de patches
function testPatchDisplay() {
    console.log('📋 Testando renderização de patches...');
    
    // Simula patches de teste
    const testPatches = [
        {
            id: 1,
            name: 'Patch Teste PC',
            command_type: 'pc',
            input_device: 'Chocolate MIDI',
            input_channel: 1,
            output_device: 'Zoom G3X',
            zoom_bank: 'A',
            zoom_patch: 0,
            effects: null
        },
        {
            id: 2,
            name: 'Patch Teste Effects',
            command_type: 'effects_config',
            input_device: 'Chocolate MIDI',
            input_channel: 2,
            output_device: 'Zoom G3X',
            zoom_bank: 'B',
            zoom_patch: 1,
            effects: {
                'FX1': { enabled: true },
                'FX2': { enabled: false },
                'FX3': { enabled: true },
                'FX4': { enabled: false },
                'FX5': { enabled: true },
                'FX6': { enabled: false }
            }
        },
        {
            id: 3,
            name: 'Patch Teste CC',
            command_type: 'cc',
            input_device: 'Chocolate MIDI',
            input_channel: 3,
            output_device: 'Zoom G3X',
            cc: 1,
            value: 127,
            effects: null
        }
    ];
    
    // Testa a função createPatchCard
    testPatches.forEach((patch, index) => {
        console.log(`\n🔍 Testando patch ${index + 1}: ${patch.name}`);
        
        try {
            const cardHtml = app.createPatchCard(patch);
            console.log('✅ Card HTML gerado com sucesso');
            
            // Verifica se contém as caixas de entrada e saída
            if (cardHtml.includes('input-box') && cardHtml.includes('output-box')) {
                console.log('✅ Caixas de entrada/saída encontradas');
            } else {
                console.log('❌ Caixas de entrada/saída não encontradas');
            }
            
            // Verifica efeitos apenas para patches de configuração
            if (patch.command_type === 'effects_config') {
                if (cardHtml.includes('patch-effects-section')) {
                    console.log('✅ Seção de efeitos encontrada');
                } else {
                    console.log('❌ Seção de efeitos não encontrada');
                }
            } else {
                if (!cardHtml.includes('patch-effects-section')) {
                    console.log('✅ Efeitos corretamente omitidos para patch PC/CC');
                } else {
                    console.log('❌ Efeitos não deveriam aparecer neste patch');
                }
            }
            
        } catch (error) {
            console.error('❌ Erro ao gerar card:', error);
        }
    });
}

// Função para testar navegação
function testNavigation() {
    console.log('\n🧭 Testando navegação...');
    
    try {
        // Testa navegação para patches
        app.navigateToSection('patches');
        console.log('✅ Navegação para patches executada');
        
        // Aguarda um pouco e testa carregamento
        setTimeout(() => {
            console.log('⏳ Aguardando carregamento de patches...');
            
            const patchesContainer = document.getElementById('patches-container');
            if (patchesContainer) {
                console.log('✅ Container de patches encontrado');
                
                if (patchesContainer.innerHTML.includes('patch-info-grid')) {
                    console.log('✅ Nova estrutura de grid encontrada');
                } else {
                    console.log('❌ Nova estrutura de grid não encontrada');
                }
            } else {
                console.log('❌ Container de patches não encontrado');
            }
        }, 2000);
        
    } catch (error) {
        console.error('❌ Erro na navegação:', error);
    }
}

// Função para verificar estilos CSS
function checkCSS() {
    console.log('\n🎨 Verificando estilos CSS...');
    
    const styleSheets = document.styleSheets;
    let foundStyles = false;
    
    for (let i = 0; i < styleSheets.length; i++) {
        try {
            const rules = styleSheets[i].cssRules || styleSheets[i].rules;
            for (let j = 0; j < rules.length; j++) {
                const rule = rules[j];
                if (rule.selectorText && rule.selectorText.includes('patch-info-box')) {
                    console.log('✅ Estilos de patch-info-box encontrados');
                    foundStyles = true;
                }
                if (rule.selectorText && rule.selectorText.includes('patch-effect-box')) {
                    console.log('✅ Estilos de patch-effect-box encontrados');
                    foundStyles = true;
                }
            }
        } catch (e) {
            // Ignora erros de CORS
        }
    }
    
    if (!foundStyles) {
        console.log('⚠️ Estilos não encontrados (pode ser problema de CORS)');
    }
}

// Executa os testes
console.log('🚀 Iniciando testes...\n');

// Aguarda um pouco para garantir que a página carregou
setTimeout(() => {
    testPatchDisplay();
    checkCSS();
    testNavigation();
    
    console.log('\n✨ Testes concluídos!');
    console.log('\n📝 Instruções:');
    console.log('1. Navegue para a seção "Patches" no menu');
    console.log('2. Verifique se os patches aparecem com as novas caixas coloridas');
    console.log('3. Verifique se os efeitos só aparecem nos patches de configuração');
    console.log('4. Teste em diferentes tamanhos de tela para responsividade');
}, 1000); 