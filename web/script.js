let archivosAbiertos = [];
let idActivo = null;

async function nuevo() {
    const id = Date.now();
    const nuevoArchivo = { id, ruta: null, nombre: "Sin título", contenido: "", original: "", modificado: false };
    archivosAbiertos.push(nuevoArchivo);
    seleccionarArchivo(id);
    actualizarPestañas();
}

async function abrir() {
    let datos = await eel.abrir_archivo_py()();
    if (datos) {
        const yaAbierto = archivosAbiertos.find(a => a.ruta === datos.ruta);
        if (yaAbierto) { seleccionarArchivo(yaAbierto.id); return; }
        const id = Date.now();
        archivosAbiertos.push({ id, ruta: datos.ruta, nombre: datos.ruta.split(/[\\/]/).pop(), contenido: datos.contenido, original: datos.contenido, modificado: false });
        seleccionarArchivo(id);
        actualizarPestañas();
    }
}

function seleccionarArchivo(id) {
    idActivo = id;
    const archivo = archivosAbiertos.find(a => a.id === id);
    if (archivo) {
        document.getElementById('editor').value = archivo.contenido;
        actualizarEditor();
        actualizarPestañas();
    }
}

async function guardar() {
    const archivo = archivosAbiertos.find(a => a.id === idActivo);
    if (!archivo) return;
    const contenidoActual = document.getElementById('editor').value;
    let resultado = await eel.guardar_archivo_py(contenidoActual, archivo.ruta)();
    if (resultado) {
        archivo.ruta = resultado;
        archivo.nombre = resultado.split(/[\\/]/).pop();
        archivo.contenido = contenidoActual;
        archivo.original = contenidoActual;
        archivo.modificado = false;
        actualizarPestañas();
        actualizarEditor();
    }
}

async function guardarComo() {
    const archivo = archivosAbiertos.find(a => a.id === idActivo);
    if (!archivo) return;
    const contenidoActual = document.getElementById('editor').value;
    let resultado = await eel.guardar_archivo_py(contenidoActual, null)();
    if (resultado) {
        archivo.ruta = resultado;
        archivo.nombre = resultado.split(/[\\/]/).pop();
        archivo.contenido = contenidoActual;
        archivo.original = contenidoActual;
        archivo.modificado = false;
        actualizarPestañas();
        actualizarEditor();
    }
}

function cerrarActual() { if (idActivo) cerrarArchivo(idActivo); }

async function cerrarArchivo(id, event) {
    if (event) event.stopPropagation();
    const archivo = archivosAbiertos.find(a => a.id === id);
    if (archivo && archivo.modificado) {
        const confirmar = await mostrarConfirmacion(`¿Cerrar ${archivo.nombre}? Tienes cambios sin guardar.`);
        if (!confirmar) return;
    }
    archivosAbiertos = archivosAbiertos.filter(a => a.id !== id);
    if (archivosAbiertos.length > 0) {
        if (idActivo === id) seleccionarArchivo(archivosAbiertos[0].id);
    } else {
        idActivo = null;
        document.getElementById('editor').value = '';
        actualizarEditor();
    }
    actualizarPestañas();
}

async function salir() {
    const confirmar = await mostrarConfirmacion("¿Está seguro de que desea salir del IDE?");
    if (confirmar) { eel.finalizar_programa()(); setTimeout(() => { window.close(); }, 100); }
}

function mostrarConfirmacion(mensaje) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-modal');
        document.getElementById('modal-message').innerText = mensaje;
        modal.style.display = 'flex';
        document.getElementById('modal-accept').onclick = () => { modal.style.display = 'none'; resolve(true); };
        document.getElementById('modal-cancel').onclick = () => { modal.style.display = 'none'; resolve(false); };
    });
}

function actualizarPestañas() {
    const contenedor = document.getElementById('file-tabs-container');
    contenedor.innerHTML = '';
    archivosAbiertos.forEach(archivo => {
        const tab = document.createElement('div');
        tab.className = `file-tab ${archivo.id === idActivo ? 'active' : ''}`;
        tab.onclick = () => seleccionarArchivo(archivo.id);
        const mod = archivo.modificado ? ' ●' : '';
        tab.innerHTML = `<span class="file-icon"><svg viewBox="0 0 24 24"><path d="M19 9V17.8C19 18.9201 19 19.4802 18.782 19.908C18.5903 20.2843 18.2843 20.5903 17.908 20.782C17.4802 21 16.9201 21 15.8 21H8.2C7.07989 21 6.51984 21 6.09202 20.782C5.71569 20.5903 5.40973 20.2843 5.21799 19.908C5 19.4802 5 18.9201 5 17.8V6.2C5 5.07989 5 4.51984 5.21799 4.09202C5.40973 3.71569 5.71569 3.40973 6.09202 3.21799C6.51984 3 7.0799 3 8.2 3H13M19 9L13 3M19 9H14C13.4477 9 13 8.55228 13 8V3"></path></svg></span><span>${archivo.nombre}${mod}</span><button class="close-tab-btn" onclick="cerrarArchivo(${archivo.id}, event)">×</button>`;
        contenedor.appendChild(tab);
    });
}

// En script.js
function actualizarEditor() {
    const editor = document.getElementById('editor');
    const highlightingContent = document.getElementById('highlighting-content');
    const lineNumbers = document.getElementById('line-numbers');
    const highlight = document.getElementById('line-highlight');
    const archivo = archivosAbiertos.find(a => a.id === idActivo);
    
    // Obtener el texto PURO del textarea
    const texto = editor.value; 
    
    // 1. Aplicar Resaltado de Sintaxis SOLO a la capa visual
    // Pasamos el texto puro, la función se encarga de los colores
    highlightingContent.innerHTML = resaltarCodigo(texto); 

    // 2. Lógica de cursor y líneas
    const pos = editor.selectionStart;
    const lineasSub = texto.substring(0, pos).split(/\r?\n/);
    const filaActual = lineasSub.length;

    if (archivo) {
        archivo.contenido = texto; // Guardar el texto puro, sin "&gt;"
        archivo.modificado = archivo.contenido !== archivo.original;
        actualizarPestañas();
        highlight.style.display = 'block';
        highlight.style.top = `${(filaActual - 1) * 24 + 10}px`;
    }

    // Actualizar números de línea
    const totalLineas = texto.split(/\r?\n/).length;
    let numerosHtml = "";
    for (let i = 1; i <= totalLineas; i++) {
        numerosHtml += `<div class="${i === filaActual ? 'active-line' : ''}">${i}</div>`;
    }
    lineNumbers.innerHTML = numerosHtml;
    
    // Actualizar barra de estado
    const columnaActual = lineasSub[filaActual - 1].length;
    document.getElementById('posicion-cursor').innerText = 
        `Archivo: ${archivo ? archivo.nombre : 'Sin título'} | Línea: ${filaActual} | Columna: ${columnaActual}`;
    
    sincronizarScroll();
}

function resaltarCodigo(codigo) {
    // 1. Limpieza de entidades para que el análisis sea real
    let codigoLimpio = codigo.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');

    // 2. Regex Maestra actualizada (sin & o | individuales)
    const regexMaster = /(?<c3>\/\*[\s\S]*?\*\/|\/\/.*)|(?<c4>\b(if|else|end|do|while|switch|case|int|float|main|cin|cout)\b)|(?<c1>\d+\.\d+|\d+)|(?<c5>\+\+|--|\+|\-|\*|\/|%|\^)|(?<c6><=|>=|!=|==|<|>|&&|\|\||!)|(?<c2>[a-zA-Z][a-zA-Z0-9]*)|(?<error>[&|]+|[^ \t\n\w])/g;

    return codigoLimpio.replace(regexMaster, (match, ...args) => {
        const groups = args[args.length - 1];
        
        // Escapamos para el HTML final
        let safe = match.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

        if (groups.c3) return `<span class="token-c3">${safe}</span>`;
        if (groups.c4) return `<span class="token-c4">${safe}</span>`;
        if (groups.c1) return `<span class="token-c1">${safe}</span>`;
        if (groups.c5) return `<span class="token-c5">${safe}</span>`;
        if (groups.c6) return `<span class="token-c6">${safe}</span>`;
        if (groups.c2) return `<span class="token-c2">${safe}</span>`;
        
        // Si cae aquí, es un error (como un & solo)
        return `<span class="token-error">${safe}</span>`; 
    }).replace(/\n/g, "<br>");
}

function sincronizarScroll() {
    const editor = document.getElementById('editor');
    const highlighting = document.getElementById('highlighting-content');
    const lineNumbers = document.getElementById('line-numbers');
    
    highlighting.scrollTop = editor.scrollTop;
    highlighting.scrollLeft = editor.scrollLeft;
    lineNumbers.scrollTop = editor.scrollTop;
    
    document.getElementById('line-highlight').style.transform = `translateY(-${editor.scrollTop}px)`;
}

// En script.js
async function compilar(fase) {
    let codigoPuro = document.getElementById('editor').value;
    
    // LIMPIEZA CRÍTICA: Quitamos entidades HTML que se hayan colado
    codigoPuro = codigoPuro.replace(/&amp;/g, '&')
                           .replace(/&lt;/g, '<')
                           .replace(/&gt;/g, '>');

    const res = await eel.ejecutar_fase_compilador(fase, codigoPuro)();
    
    // Mapeo de IDs según index.html
    const tabMap = { 'lexico': 'tab-lexico', 'sintactico': 'tab-sintactico', 'semantico': 'tab-semantico', 'intermedio': 'tab-intermedio' };
    const errorTabMap = { 'lexico': 'err-lexico', 'sintactico': 'err-sintactico', 'semantico': 'err-semantico', 'intermedio': 'err-intermedio' };
    
    // 1. Mostrar Resultado (Tabla o Texto)
    const displayArea = document.getElementById(tabMap[fase]);
    if (fase === 'lexico' && Array.isArray(res.resultado)) {
        displayArea.innerHTML = generarTablaTokens(res.resultado); // Función auxiliar para la tabla
    } else {
        displayArea.innerText = res.resultado || "";
    }

    // 2. Manejo de Errores
    const errorArea = document.getElementById(errorTabMap[fase]);
    errorArea.innerText = ""; // Limpiar errores previos

    if (res.errores && res.errores.length > 0) {
        // Formatear y mostrar errores
        errorArea.innerText = res.errores.map(e => `Línea ${e.linea}, Col ${e.columna}: ${e.desc}`).join('\n');
        errorArea.style.color = "#f44336"; // Rojo para errores
        
        // Cambiar automáticamente a la pestaña de errores correspondiente
        verTabInferior(null, errorTabMap[fase]); 
    } else {
        errorArea.innerText = "0 errores detectados.";
        errorArea.style.color = "#4ec9b0"; // Verde para éxito
    }
    
    verTab(null, tabMap[fase]); // Mostrar pestaña de resultados
}

// Función auxiliar para mantener limpio el código
function generarTablaTokens(tokens) {
    return `
        <table class="tabla-tokens">
            <thead>
                <tr><th>Token</th><th>Lexema</th><th>Línea</th><th>Col</th></tr>
            </thead>
            <tbody>
                ${tokens.map(t => `
                    <tr>
                        <td><span class="badge-${t.tipo}">${t.tipo}</span></td>
                        <td>${t.valor}</td>
                        <td>${t.linea}</td>
                        <td>${t.columna}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>`;
}

async function ejecutar() {
    const resPane = document.getElementById('res-ejecucion');
    resPane.innerText = "Iniciando ejecución...";
    verTabInferior(null, 'res-ejecucion');
    let respuesta = await eel.ejecutar_fase_compilador('ejecucion', document.getElementById('editor').value)();
    resPane.innerText = respuesta.resultado || respuesta.errores || "Programa finalizado.";
}

function verTab(evt, name) {
    const panel = document.getElementById("right-panel"); // results-pane (arriba derecha)
    if (!panel) return;

    // 1) contenido
    panel.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    const content = panel.querySelector("#" + name);
    if (content) content.classList.add("active");

    // 2) botones (pestañas)
    panel.querySelectorAll(".tabs .tab-link").forEach(b => b.classList.remove("active"));

    // si viene event, activamos el botón clickeado
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add("active");
        return;
    }

    // si NO viene event (ej: compilar()), buscamos el botón que abre ese tab
    const btn = Array.from(panel.querySelectorAll(".tabs .tab-link"))
        .find(b => (b.getAttribute("onclick") || "").includes(`'${name}'`));
    if (btn) btn.classList.add("active");
}

function verTabInferior(evt, name) {
    const panel = document.querySelector(".bottom-pane"); // panel inferior
    if (!panel) return;

    // 1) contenido
    panel.querySelectorAll(".tab-content-inf").forEach(c => c.classList.remove("active"));
    const content = panel.querySelector("#" + name);
    if (content) content.classList.add("active");

    // 2) botones
    panel.querySelectorAll(".tabs .tab-link").forEach(b => b.classList.remove("active"));

    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add("active");
        return;
    }

    const btn = Array.from(panel.querySelectorAll(".tabs .tab-link"))
        .find(b => (b.getAttribute("onclick") || "").includes(`'${name}'`));
    if (btn) btn.classList.add("active");
}

window.onkeydown = (e) => {
    if (e.ctrlKey) {
        if (e.key === 's') { e.preventDefault(); guardar(); }
        if (e.key === 'o') { e.preventDefault(); abrir(); }
        if (e.key === 'n') { e.preventDefault(); nuevo(); }
    }
};

window.onload = () => {
    nuevo();
    const ed = document.getElementById('editor');
    ed.addEventListener('input', actualizarEditor);
    ed.addEventListener('click', actualizarEditor);
    ed.addEventListener('keyup', actualizarEditor);
    ed.addEventListener('scroll', sincronizarScroll);
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