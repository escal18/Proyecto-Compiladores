let rutaActual = null;

// --- GESTIÓN DE MODAL PERSONALIZADO ---
function mostrarConfirmacion(mensaje) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-modal');
        const btnAccept = document.getElementById('modal-accept');
        const btnCancel = document.getElementById('modal-cancel');
        const msgElement = document.getElementById('modal-message');

        msgElement.innerText = mensaje;
        modal.style.display = 'flex';

        btnAccept.onclick = () => {
            modal.style.display = 'none';
            resolve(true);
        };

        btnCancel.onclick = () => {
            modal.style.display = 'none';
            resolve(false);
        };
    });
}

// --- FUNCIONES DE ARCHIVO (Req. 2.1) ---
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
        document.getElementById('tab-lexico').innerText = "Lista de tokens...";
        document.getElementById('err-lexico').innerText = "Lista de errores léxicos...";
    }
}

async function salir() {
    const confirmar = await mostrarConfirmacion("¿Está seguro de que desea salir?");
    if (confirmar) {
        eel.finalizar_programa()(); // Envía la orden a Python
        window.close();             // Cierra la ventana del navegador
    }
}

// --- LÓGICA DEL EDITOR (Req. 3.37, 3.38) ---
function actualizarEditor() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    const statusBar = document.getElementById('posicion-cursor');

    // Numeración de líneas
    const lineas = editor.value.split('\n').length;
    let numerosHtml = "";
    for (let i = 1; i <= lineas; i++) {
        numerosHtml += `<div>${i}</div>`;
    }
    lineNumbers.innerHTML = numerosHtml;

    // Posición del Cursor
    const pos = editor.selectionStart;
    const textoHastaCursor = editor.value.substring(0, pos);
    const lineasArray = textoHastaCursor.split('\n');
    const fila = lineasArray.length;
    const columna = lineasArray[lineasArray.length - 1].length;

    const nombreArchivo = rutaActual ? rutaActual.split(/[\\/]/).pop() : 'Sin título';
    statusBar.innerText = `Archivo: ${nombreArchivo} | Línea: ${fila} | Columna: ${columna}`;
    
    sincronizarScroll();
}

function sincronizarScroll() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    lineNumbers.scrollTop = editor.scrollTop;
}

// --- COMPILACIÓN (Req. 2.2) ---
async function compilar(fase) {
    const codigo = document.getElementById('editor').value;
    const tabLex = document.getElementById('tab-lexico');
    const consoleArea = document.getElementById('err-lexico');

    tabLex.innerText = "Compilando fase: " + fase + "...";
    let respuesta = await eel.ejecutar_fase_compilador(fase, codigo)();
    
    tabLex.innerText = respuesta.resultado || "Sin salida.";
    if (respuesta.errores) {
        consoleArea.innerText = respuesta.errores;
        consoleArea.style.color = "#f44336";
    } else {
        consoleArea.innerText = "Análisis finalizado sin errores.";
        consoleArea.style.color = "#4ec9b0";
    }
}

// Manejo de Pestañas
function verTab(evt, tabName) {
    let contents = document.getElementsByClassName("tab-content");
    for (let c of contents) c.classList.remove("active");
    let links = document.getElementsByClassName("tab-link");
    for (let l of links) l.classList.remove("active");
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

function verTabInferior(evt, tabName) {
    let contents = document.getElementsByClassName("tab-content-inf");
    for (let c of contents) c.classList.remove("active");
    let links = evt.currentTarget.parentElement.getElementsByClassName("tab-link");
    for (let l of links) l.classList.remove("active");
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

window.onload = () => {
    const editor = document.getElementById('editor');
    editor.addEventListener('input', actualizarEditor);
    editor.addEventListener('click', actualizarEditor);
    editor.addEventListener('keyup', actualizarEditor);
    editor.addEventListener('scroll', sincronizarScroll);
    actualizarEditor();
};