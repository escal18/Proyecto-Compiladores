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

function actualizarEditor() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    const highlight = document.getElementById('line-highlight');
    const archivo = archivosAbiertos.find(a => a.id === idActivo);
    const texto = editor.value;
    const pos = editor.selectionStart;
    const lineasSub = texto.substring(0, pos).split(/\r?\n/);
    const filaActual = lineasSub.length;
    if (archivo) {
        archivo.contenido = texto;
        archivo.modificado = archivo.contenido !== archivo.original;
        actualizarPestañas();
        highlight.style.display = 'block';
        highlight.style.top = `${(filaActual - 1) * 21 + 10}px`;
    } else { highlight.style.display = 'none'; }
    const totalLineas = texto.split(/\r?\n/).length;
    let numerosHtml = "";
    for (let i = 1; i <= totalLineas; i++) {
        numerosHtml += `<div class="${i === filaActual ? 'active-line' : ''}">${i}</div>`;
    }
    lineNumbers.innerHTML = numerosHtml;
    document.getElementById('posicion-cursor').innerText = `Archivo: ${archivo ? archivo.nombre : 'Sin título'} | Línea: ${filaActual} | Columna: ${lineasSub[filaActual - 1].length}`;
    sincronizarScroll();
}

function sincronizarScroll() {
    const editor = document.getElementById('editor');
    document.getElementById('line-numbers').scrollTop = editor.scrollTop;
    document.getElementById('line-highlight').style.transform = `translateY(-${editor.scrollTop}px)`;
}

async function compilar(fase) {
    const res = await eel.ejecutar_fase_compilador(fase, document.getElementById('editor').value)();
    const tabMap = { 'lexico': 'tab-lexico', 'sintactico': 'tab-sintactico', 'semantico': 'tab-semantico', 'intermedio': 'tab-intermedio' };
    const errorTabMap = { 'lexico': 'err-lexico', 'sintactico': 'err-sintactico', 'semantico': 'err-semantico', 'intermedio': 'err-intermedio' };
    document.getElementById(tabMap[fase]).innerText = res.resultado;
    const errorArea = document.getElementById(errorTabMap[fase]);
    if (res.errores && res.errores.length > 0) {
        errorArea.innerText = res.errores.map(e => `Línea ${e.linea}: ${e.desc}`).join('\n');
        errorArea.style.color = "#f44336";
        verTabInferior(null, errorTabMap[fase]);
    } else {
        errorArea.innerText = "0 errores detectados.";
        errorArea.style.color = "#4ec9b0";
    }
    verTab(null, tabMap[fase]);
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