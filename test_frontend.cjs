const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const elements = new Map();
function element(id) {
    if (!elements.has(id)) elements.set(id, {value: '', innerText: '', innerHTML: '', style: {}});
    return elements.get(id);
}
let enviado;
let respuesta = {resultado: [], errores: []};
const context = vm.createContext({
    window: {},
    document: {
        getElementById: element,
        addEventListener() {},
        querySelector() { return null; },
    },
    eel: {ejecutar_fase_compilador(fase, codigo) {
        enviado = {fase, codigo};
        return async () => respuesta;
    }},
});
vm.runInContext(fs.readFileSync(`${__dirname}/web/script.js`, 'utf8'), context);
vm.runInContext('verTab = () => {}; verTabInferior = () => {};', context);

(async () => {
    const fuente = 'main {\n x +\n +; cout << x; // &lt;\n}';
    element('editor').value = fuente;
    await context.compilar('lexico');
    assert.equal(enviado.codigo, fuente);
    respuesta = {resultado: {name: 'Programa', children: []}, errores: [{desc: 'inválido'}],
        errores_lexicos: [{linea: 2, columna: 3, desc: 'Carácter no reconocido'}], errores_sintacticos: []};
    await context.compilar('sintactico');
    assert.equal(enviado.codigo, fuente);
    assert.match(element('err-lexico').innerText, /Carácter no reconocido/);
    assert.equal(element('err-sintactico').innerText, '0 errores detectados.');
    respuesta = {resultado: 'Pendiente', errores: [], implementado: false};
    await context.compilar('semantico');
    assert.match(element('err-semantico').innerText, /no está implementada/);
    const resaltado = context.resaltarCodigo('bool ok; if true then cin >> x; cout << x; end');
    assert.ok(!resaltado.includes('token-error'));
    assert.match(resaltado, /&gt;&gt;/);
    assert.match(resaltado, /&lt;&lt;/);
    const tabla = context.generarTablaTokens([{tipo: 'OPERADOR_REL', valor: '<', linea: 1, columna: 1}]);
    assert.match(tabla, /&lt;<\/td>/);
    const html = context.renderizarArbol({name: 'Op (<)', children: [{name: 'Valor', value: '<script>'}]});
    assert.ok(!html.includes('<script>'));
    console.log('OK: fuente sin alteraciones, errores separados, resaltado y HTML escapado.');
})().catch(error => {console.error(error); process.exitCode = 1;});
