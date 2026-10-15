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
    const multilinea = context.resaltarCodigo('main {\n\nint x;\n}\n');
    assert.equal(multilinea.split('\n').length, 5);
    assert.ok(!multilinea.includes('<br>'));
    assert.match(context.anotacionesSemanticas({tipo: 'int', tipo_efectivo: 'float',
        constante: true, valor_constante: 2}), /tipo: float.*valor: 2\.0/);
    const resaltado = context.resaltarCodigo('bool ok; if true then cin >> x; cout << x; end');
    assert.ok(!resaltado.includes('token-error'));
    assert.match(resaltado, /&gt;&gt;/);
    assert.match(resaltado, /&lt;&lt;/);
    const tabla = context.generarTablaTokens([{tipo: 'OPERADOR_REL', valor: '<', linea: 1, columna: 1}]);
    assert.match(tabla, /&lt;<\/td>/);
    const html = context.renderizarArbol({name: 'Op (<)', children: [{name: 'Valor', value: '<script>'}]});
    assert.ok(!html.includes('<script>'));
    const original = {name: 'Programa', children: [{name: 'Valor', value: 'false'}]};
    const anotado = {name: 'Programa', tipo: 'void', children: [
        {name: 'Valor', value: 'false', tipo: 'bool', constante: true, valor_constante: false,
         dtype: 'bool', direccion: 0, valido: true}
    ]};
    respuesta = {
        resultado: anotado, ast_original: original, arbol_anotado: anotado,
        errores: [], errores_lexicos: [], errores_sintacticos: [], errores_semanticos: [],
        semantico_ejecutado: true, semantico_valido: true, traza_semantica: [{accion: 'insertar'}],
        tabla_simbolos: [{id: 1, nombre: '<variable>', tipo: 'bool', ambito: 'main',
            lineas: [2, 3, 3], direccion: 0, tamano: 1}]
    };
    await context.compilar('semantico');
    assert.match(element('tab-semantico').innerHTML, /valor: false/);
    assert.match(element('tab-semantico').innerHTML, /dtype heredado: bool/);
    assert.match(element('tab-semantico').innerHTML, /Recorrido semántico/);
    assert.match(element('tab-hash').innerHTML, /&lt;variable&gt;/);
    assert.match(element('tab-hash').innerHTML, /2, 3, 3/);
    const historial = context.generarTablaSimbolos([
        {id: 1, nombre: 'x', tipo: 'int', ambito: 'main', constante: false,
         ultimo_valor_conocido: 0, lineas: [2, 3], direccion: 0, tamano: 4},
        {id: 2, nombre: 'c', tipo: 'float', ambito: 'main', constante: false,
         lineas: [2], direccion: 8, tamano: 8}
    ]);
    assert.match(historial, /Último valor conocido/);
    assert.match(historial, /<td>0<\/td>/);
    assert.match(historial, /<td>—<\/td>/);
    assert.ok(!historial.includes('no determinado'));
    assert.ok(!element('tab-sintactico').innerHTML.includes('dtype heredado'));
    respuesta.semantico_ejecutado = false;
    respuesta.semantico_valido = false;
    respuesta.resultado = 'Corrige la sintaxis';
    respuesta.tabla_simbolos = [];
    respuesta.errores_sintacticos = [{linea: 1, columna: 2, desc: 'Falta cierre'}];
    await context.compilar('semantico');
    assert.match(element('err-semantico').innerText, /no ejecutado/);
    assert.match(element('tab-hash').innerHTML, /No hay símbolos/);
    assert.equal(element('tab-semantico').innerText, 'Corrige la sintaxis');
    console.log('OK: fuente, errores por fase, AST original/anotado, constantes, tabla y bloqueo semántico.');
})().catch(error => {console.error(error); process.exitCode = 1;});
