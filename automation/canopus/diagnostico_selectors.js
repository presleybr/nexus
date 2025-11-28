// SCRIPT DE DIAGNÓSTICO - Cole no Console do Chromium (F12)
// Execute este script na página de Emissão de Cobrança

console.log('='.repeat(80));
console.log('DIAGNÓSTICO - PÁGINA DE EMISSÃO DE COBRANÇA');
console.log('='.repeat(80));

// 1. Verificar tabela de boletos
const tabela = document.querySelector('table[id*="grdBoleto_Avulso"]');
console.log('\n1. TABELA DE BOLETOS:');
if (tabela) {
    console.log('✅ Tabela encontrada!');
    console.log('   ID:', tabela.id);
    console.log('   Total de linhas:', tabela.rows.length);
} else {
    console.log('❌ Tabela não encontrada!');
    console.log('   Procurando por outras tabelas...');
    const todasTabelas = document.querySelectorAll('table');
    console.log(`   Total de tabelas na página: ${todasTabelas.length}`);
    todasTabelas.forEach((t, idx) => {
        console.log(`   Tabela ${idx + 1}: ID=${t.id || 'sem-id'}, Classes=${t.className}`);
    });
}

// 2. Verificar checkboxes
console.log('\n2. CHECKBOXES:');
const checkboxes = document.querySelectorAll('input[type="checkbox"]');
console.log(`Total de checkboxes: ${checkboxes.length}`);
checkboxes.forEach((cb, idx) => {
    console.log(`   Checkbox ${idx + 1}:`);
    console.log(`     ID: ${cb.id || 'sem-id'}`);
    console.log(`     Name: ${cb.name || 'sem-name'}`);
    console.log(`     Checked: ${cb.checked}`);
    console.log(`     Visible: ${cb.offsetParent !== null}`);
});

// 3. Verificar inputs de imagem (imgEmite_Boleto)
console.log('\n3. INPUTS DE IMAGEM (imgEmite_Boleto):');
const inputsImagem = document.querySelectorAll('input[id*="imgEmite_Boleto"]');
console.log(`Total: ${inputsImagem.length}`);
inputsImagem.forEach((img, idx) => {
    console.log(`   Input ${idx + 1}:`);
    console.log(`     ID: ${img.id}`);
    console.log(`     Type: ${img.type}`);
    console.log(`     Src: ${img.src || 'sem-src'}`);
    console.log(`     Visible: ${img.offsetParent !== null}`);
});

// 4. Verificar botões
console.log('\n4. BOTÕES:');
const botoes = document.querySelectorAll('input[type="button"], button');
console.log(`Total de botões: ${botoes.length}`);
botoes.forEach((btn, idx) => {
    const value = btn.value || btn.textContent;
    if (value && value.toLowerCase().includes('emit')) {
        console.log(`   ⭐ Botão ${idx + 1} (CONTÉM "EMIT"):`);
        console.log(`     ID: ${btn.id || 'sem-id'}`);
        console.log(`     Value/Text: ${value}`);
        console.log(`     Type: ${btn.type}`);
        console.log(`     Visible: ${btn.offsetParent !== null}`);
    }
});

// 5. Buscar botão "Emitir" especificamente
console.log('\n5. BOTÃO "EMITIR COBRANÇA":');
const botaoEmitir = document.querySelector('#ctl00_Conteudo_btnEmitir');
if (botaoEmitir) {
    console.log('✅ Botão encontrado pelo ID!');
    console.log(`   ID: ${botaoEmitir.id}`);
    console.log(`   Value: ${botaoEmitir.value}`);
    console.log(`   Visible: ${botaoEmitir.offsetParent !== null}`);
} else {
    console.log('❌ Botão não encontrado pelo ID #ctl00_Conteudo_btnEmitir');
}

// 6. SUGESTÕES DE SELETORES
console.log('\n' + '='.repeat(80));
console.log('SELETORES SUGERIDOS:');
console.log('='.repeat(80));

if (inputsImagem.length > 0) {
    console.log('\nPara CHECKBOX do boleto, use:');
    console.log(`   'input[id*="imgEmite_Boleto"]'`);
    console.log(`   ou especificamente: '#${inputsImagem[0].id}'`);
} else if (checkboxes.length > 0) {
    console.log('\nPara CHECKBOX do boleto, use:');
    console.log(`   'input[type="checkbox"]'`);
    console.log(`   ou especificamente: '#${checkboxes[0].id}'`);
}

if (botaoEmitir) {
    console.log('\nPara BOTÃO EMITIR, use:');
    console.log(`   '#${botaoEmitir.id}'`);
}

console.log('\n' + '='.repeat(80));
console.log('DIAGNÓSTICO COMPLETO!');
console.log('Copie estas informações e envie ao desenvolvedor.');
console.log('='.repeat(80));
