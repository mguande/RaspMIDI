// Script de teste para verificar a correção do combo de patches
console.log("🧪 Testando correção do combo de patches...");

// Simula a função convertFromGlobalPatchNumber
function convertFromGlobalPatchNumber(globalPatchNumber) {
    const bankNumber = Math.floor(globalPatchNumber / 10);
    const localPatchNumber = globalPatchNumber % 10;
    
    // Mapeamento de números para letras de banco (0=A, 1=B, 2=C, etc.)
    const bankMapping = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
    const bankLetter = bankMapping[bankNumber] || 'A';
    
    console.log(`🔄 Conversão reversa: Global ${globalPatchNumber} = Banco ${bankLetter} + Patch ${localPatchNumber}`);
    
    return {
        bankLetter: bankLetter,
        patch: localPatchNumber
    };
}

// Testa alguns casos
const testCases = [
    { global: 0, expected: { bank: 'A', patch: 0 } },
    { global: 5, expected: { bank: 'A', patch: 5 } },
    { global: 9, expected: { bank: 'A', patch: 9 } },
    { global: 10, expected: { bank: 'B', patch: 0 } },
    { global: 15, expected: { bank: 'B', patch: 5 } },
    { global: 19, expected: { bank: 'B', patch: 9 } },
    { global: 20, expected: { bank: 'C', patch: 0 } },
    { global: 99, expected: { bank: 'J', patch: 9 } }
];

console.log("📋 Testando conversões global → local:");
testCases.forEach(testCase => {
    const result = convertFromGlobalPatchNumber(testCase.global);
    const success = result.bankLetter === testCase.expected.bank && result.patch === testCase.expected.patch;
    
    console.log(`  Global ${testCase.global} → Banco ${result.bankLetter} + Patch ${result.patch} ${success ? '✅' : '❌'}`);
    
    if (!success) {
        console.log(`    Esperado: Banco ${testCase.expected.bank} + Patch ${testCase.expected.patch}`);
    }
});

console.log("\n🎯 Testando cenários de edição:");
const editScenarios = [
    { patch: { zoom_bank: 'A', zoom_patch: 0 }, expected: 0 },
    { patch: { zoom_bank: 'A', zoom_patch: 5 }, expected: 5 },
    { patch: { zoom_bank: 'B', zoom_patch: 10 }, expected: 0 },
    { patch: { zoom_bank: 'B', zoom_patch: 15 }, expected: 5 },
    { patch: { zoom_bank: 'C', zoom_patch: 22 }, expected: 2 },
    { patch: { zoom_bank: 'J', zoom_patch: 99 }, expected: 9 }
];

editScenarios.forEach(scenario => {
    const localPatchNumber = convertFromGlobalPatchNumber(scenario.patch.zoom_patch).patch;
    const success = localPatchNumber === scenario.expected;
    
    console.log(`  Banco ${scenario.patch.zoom_bank} + Global ${scenario.patch.zoom_patch} → Local ${localPatchNumber} ${success ? '✅' : '❌'}`);
    
    if (!success) {
        console.log(`    Esperado: Local ${scenario.expected}`);
    }
});

console.log("\n✅ Teste concluído!"); 