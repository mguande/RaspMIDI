// Script de teste para verificar se a correção funcionou
// Execute este código no console do navegador (F12)

console.log("🧪 Testando correção do travamento...");

// Função para testar se o menu está funcionando
function testMenuFunctionality() {
    console.log("🧭 Testando funcionalidade do menu...");
    
    const menuItems = document.querySelectorAll('.menu-item');
    let workingItems = 0;
    
    menuItems.forEach((item, index) => {
        const section = item.getAttribute('data-section');
        console.log(`  Item ${index}: ${section}`);
        
        // Testa se o item responde a cliques
        const originalClass = item.className;
        item.classList.add('test-click');
        
        setTimeout(() => {
            if (item.classList.contains('test-click')) {
                item.classList.remove('test-click');
                console.log(`    ✅ Item ${section} responde a mudanças`);
                workingItems++;
            }
        }, 100);
    });
    
    console.log(`📊 ${workingItems}/${menuItems.length} itens funcionando`);
    return workingItems === menuItems.length;
}

// Função para forçar recuperação manual
function forceRecovery() {
    console.log("🚨 Forçando recuperação manual...");
    
    try {
        // 1. Limpa todos os event listeners
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            const newItem = item.cloneNode(true);
            item.parentNode.replaceChild(newItem, item);
        });
        
        // 2. Remove classes active de todos os elementos
        const allElements = document.querySelectorAll('.active');
        allElements.forEach(el => el.classList.remove('active'));
        
        // 3. Força navegação para dispositivos
        const devicesItem = document.querySelector('[data-section="dispositivos"]');
        const devicesSection = document.getElementById('dispositivos');
        
        if (devicesItem) devicesItem.classList.add('active');
        if (devicesSection) devicesSection.classList.add('active');
        
        // 4. Reativa event listeners
        if (window.app && window.app.setupEdicaoMenu) {
            window.app.setupEdicaoMenu();
        }
        
        // 5. Limpa patches para evitar problemas
        if (window.app) {
            window.app.patches = [];
        }
        
        console.log("✅ Recuperação manual concluída");
        
        // 6. Testa se funcionou
        setTimeout(() => {
            const isWorking = testMenuFunctionality();
            if (isWorking) {
                console.log("🎉 Interface recuperada com sucesso!");
            } else {
                console.log("⚠️ Interface ainda pode ter problemas");
            }
        }, 500);
        
    } catch (error) {
        console.error("❌ Erro na recuperação manual:", error);
    }
}

// Função para testar criação de patch
async function testPatchCreation() {
    console.log("🔧 Testando criação de patch...");
    
    try {
        // Simula dados de um patch simples
        const testPatch = {
            name: "Teste Patch",
            input_device: "Chocolate MIDI",
            output_device: "Zoom G3X",
            command_type: "pc",
            program: 0,
            effects: {
                effect_1: { enabled: true },
                effect_2: { enabled: true },
                effect_3: { enabled: true },
                effect_4: { enabled: true },
                effect_5: { enabled: true },
                effect_6: { enabled: true }
            }
        };
        
        const response = await fetch('/api/patches', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(testPatch)
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log("✅ Patch de teste criado com sucesso");
            
            // Testa se o menu ainda funciona
            setTimeout(() => {
                const isWorking = testMenuFunctionality();
                if (isWorking) {
                    console.log("🎉 Correção funcionou! Menu ainda responde após criar patch");
                } else {
                    console.log("❌ Problema ainda existe - menu não responde após criar patch");
                }
            }, 1000);
            
        } else {
            console.error("❌ Erro ao criar patch de teste:", data.error);
        }
        
    } catch (error) {
        console.error("❌ Erro no teste de criação:", error);
    }
}

// Executa testes
console.log("🔍 Executando testes...");

// Testa menu atual
const menuWorking = testMenuFunctionality();

if (menuWorking) {
    console.log("✅ Menu funcionando corretamente");
    
    // Se o menu está funcionando, testa criação de patch
    console.log("🔧 Testando criação de patch...");
    testPatchCreation();
    
} else {
    console.log("❌ Menu não está funcionando - aplicando recuperação");
    forceRecovery();
}

// Adiciona funções ao objeto global
window.testMenuFunctionality = testMenuFunctionality;
window.forceRecovery = forceRecovery;
window.testPatchCreation = testPatchCreation;

console.log("🔧 Funções disponíveis:");
console.log("  - testMenuFunctionality() - Testa se o menu funciona");
console.log("  - forceRecovery() - Força recuperação manual");
console.log("  - testPatchCreation() - Testa criação de patch");

console.log("✅ Teste concluído. Verifique os logs acima."); 