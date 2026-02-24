let rutaActual = null;

// --- FUNCIONES DE ARCHIVO ---
async function nuevo() {
    const confirmar = await mostrarConfirmacion("¿Crear nuevo archivo? Se perderán los cambios no guardados.");
    if (confirmar) {
        document.getElementById('editor').value = '';
        rutaActual = null;
        actualizarEditor();
    }
}

async function abrir() {
    let archivo = await eel.abrir_archivo_py()();
    if (archivo) {
        document.getElementById('editor').value = archivo.contenido;
        rutaActual = archivo.ruta;
        actualizarEditor();
    }
}

async function guardar() {
    const contenido = document.getElementById('editor').value;
    let resultado = await eel.guardar_archivo_py(contenido, rutaActual)();
    if (resultado) {
        rutaActual = resultado;
        actualizarEditor();
    }
}

async function guardarComo() {
    const contenido = document.getElementById('editor').value;
    let resultado = await eel.guardar_archivo_py(contenido, null)(); 
    if (resultado) {
        rutaActual = resultado;
        actualizarEditor();
    }
}

async function cerrar() {
    const confirmar = await mostrarConfirmacion("¿Desea cerrar el archivo actual? Se perderán los cambios no guardados.");
    if (confirmar) {
        document.getElementById('editor').value = '';
        rutaActual = null;
        actualizarEditor();
        // Limpiar paneles
        document.getElementById('tab-lexico').innerText = "Lista de tokens...";
        document.getElementById('err-lexico').innerText = "Lista de errores léxicos...";
    }
}

async function salir() {
    const confirmar = await mostrarConfirmacion("¿Está seguro de que desea salir del IDE?");
    if (confirmar) {
        eel.finalizar_programa()();
        setTimeout(() => { window.close(); }, 100);
    }
}

// --- MODAL ---
function mostrarConfirmacion(mensaje) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-modal');
        const btnAccept = document.getElementById('modal-accept');
        const btnCancel = document.getElementById('modal-cancel');
        const msgElement = document.getElementById('modal-message');

        msgElement.innerText = mensaje;
        modal.style.display = 'flex';

        btnAccept.onclick = () => { modal.style.display = 'none'; resolve(true); };
        btnCancel.onclick = () => { modal.style.display = 'none'; resolve(false); };
    });
}

// --- LÓGICA DEL EDITOR ---
function actualizarEditor() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    const statusBar = document.getElementById('posicion-cursor');
    const tabNameElement = document.getElementById('tab-name');

    const texto = editor.value;
    const totalLineas = texto.split(/\r?\n/).length;
    let numerosHtml = "";
    for (let i = 1; i <= totalLineas; i++) { numerosHtml += `<div>${i}</div>`; }
    lineNumbers.innerHTML = numerosHtml;

    const posicionCursor = editor.selectionStart;
    const textoHastaCursor = texto.substring(0, posicionCursor);
    const lineasSub = textoHastaCursor.split(/\r?\n/);
    const filaActual = lineasSub.length;
    const columnaActual = lineasSub[filaActual - 1].length;

    const nombreArchivo = rutaActual ? rutaActual.split(/[\\/]/).pop() : 'Sin título';
    statusBar.innerText = `Archivo: ${nombreArchivo} | Línea: ${filaActual} | Columna: ${columnaActual}`;
    tabNameElement.innerText = nombreArchivo;
    
    sincronizarScroll();
}

function sincronizarScroll() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    lineNumbers.scrollTop = editor.scrollTop;
}

// --- COMPILACIÓN ---
async function compilar(fase) {
    const codigo = document.getElementById('editor').value;
    const res = await eel.ejecutar_fase_compilador(fase, codigo)();

    const tabMap = { 'lexico': 'tab-lexico', 'sintactico': 'tab-sintactico', 'semantico': 'tab-semantico', 'intermedio': 'tab-intermedio' };
    const errorTabMap = { 'lexico': 'err-lexico', 'sintactico': 'err-sintactico', 'semantico': 'err-semantico', 'intermedio': 'err-intermedio' };

    document.getElementById(tabMap[fase]).innerText = res.resultado;

    const errorArea = document.getElementById(errorTabMap[fase]);
    if (res.errores && res.errores.length > 0) {
        errorArea.innerText = res.errores.map(e => `Línea ${e.linea}: ${e.desc}`).join('\n');
        errorArea.style.color = "#f44336";
    } else {
        errorArea.innerText = "0 errores detectados.";
        errorArea.style.color = "#4ec9b0";
    }

    if (res.tabla_simbolos && res.tabla_simbolos.length > 0) {
        let html = `<table style="width:100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid var(--border)"><th>ID</th><th>Tipo</th><th>Línea</th></tr>`;
        res.tabla_simbolos.forEach(s => { html += `<tr><td>${s.id}</td><td>${s.tipo}</td><td>${s.linea}</td></tr>`; });
        html += "</table>";
        document.getElementById('tab-hash').innerHTML = html;
    }

    verTab({ currentTarget: document.querySelector(`[onclick*="${fase}"]`) }, tabMap[fase]);
    if (res.errores && res.errores.length > 0) {
        verTabInferior({ currentTarget: document.querySelector(`[onclick*="${errorTabMap[fase]}"]`) }, errorTabMap[fase]);
    }
}

async function ejecutar() {
    const resPane = document.getElementById('res-ejecucion');
    resPane.innerText = "Iniciando ejecución...";
    verTabInferior(null, 'res-ejecucion');
    let respuesta = await eel.ejecutar_fase_compilador('ejecucion', document.getElementById('editor').value)();
    resPane.innerText = respuesta.resultado || respuesta.errores || "Programa finalizado.";
}

// --- GESTIÓN DE PESTAÑAS UI ---
function verTab(evt, tabName) {
    let contents = document.getElementsByClassName("tab-content");
    for (let c of contents) c.classList.remove("active");
    let links = document.getElementsByClassName("tab-link");
    for (let l of links) l.classList.remove("active");
    document.getElementById(tabName).classList.add("active");
    if(evt) evt.currentTarget.classList.add("active");
}

function verTabInferior(evt, tabName) {
    let contents = document.getElementsByClassName("tab-content-inf");
    for (let c of contents) c.classList.remove("active");
    let parent = evt ? evt.currentTarget.parentElement : document.querySelector('.bottom-pane .tabs');
    let links = parent.getElementsByClassName("tab-link");
    for (let l of links) l.classList.remove("active");
    document.getElementById(tabName).classList.add("active");
    if(evt) evt.currentTarget.classList.add("active");
}

// --- EVENTOS ---
window.onload = () => {
    const editor = document.getElementById('editor');
    editor.addEventListener('input', actualizarEditor);
    editor.addEventListener('click', actualizarEditor);
    editor.addEventListener('keyup', actualizarEditor);
    editor.addEventListener('scroll', sincronizarScroll);
    actualizarEditor();
};

document.addEventListener('DOMContentLoaded', function () {
    const resizer = document.getElementById('dragMe');
    const leftSide = document.getElementById('left-panel');
    let x = 0; let leftWidth = 0;

    const mouseDownHandler = function (e) {
        x = e.clientX;
        leftWidth = leftSide.getBoundingClientRect().width;
        document.addEventListener('mousemove', mouseMoveHandler);
        document.addEventListener('mouseup', mouseUpHandler);
    };

    const mouseMoveHandler = function (e) {
        const dx = e.clientX - x;
        const containerWidth = resizer.parentNode.getBoundingClientRect().width;
        const newLeftWidth = ((leftWidth + dx) * 100) / containerWidth;
        leftSide.style.flex = `0 0 ${newLeftWidth}%`;
        actualizarEditor();
    };

    const mouseUpHandler = function () {
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
    };
    resizer.addEventListener('mousedown', mouseDownHandler);
});