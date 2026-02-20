let rutaActual = null;

// --- FUNCIONES DE ARCHIVO (Req. 2.1) ---
// Función para mostrar el modal y esperar respuesta
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

// Nueva versión de la función Nuevo
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

function cerrar() {
    if (confirm("¿Desea cerrar el archivo actual?")) {
        document.getElementById('editor').value = '';
        rutaActual = null;
        actualizarEditor();
    }
}

async function guardar() {
    const contenido = document.getElementById('editor').value;
    let resultado = await eel.guardar_archivo_py(contenido, rutaActual)();
    if (resultado) {
        rutaActual = resultado;
        console.log("Guardado en: " + rutaActual);
    }
}

async function guardarComo() {
    const contenido = document.getElementById('editor').value;
    let resultado = await eel.guardar_archivo_py(contenido, null)(); 
    if (resultado) {
        rutaActual = resultado;
    }
}

// --- LÓGICA DEL EDITOR (Req. 3.38) ---
// Función principal para sincronizar todo el editor
function actualizarEditor() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    const statusBar = document.getElementById('posicion-cursor');

    // 1. Sincronizar numeración de líneas (Req. 3.37)
    // Usamos el total de saltos de línea para generar los números
    const lineas = editor.value.split('\n').length;
    let numerosHtml = "";
    for (let i = 1; i <= lineas; i++) {
        numerosHtml += `<div>${i}</div>`;
    }
    lineNumbers.innerHTML = numerosHtml;

    // 2. Calcular Posición del Cursor (Req. 3.38)
    const posicionCursor = editor.selectionStart;
    const textoHastaCursor = editor.value.substring(0, posicionCursor);
    const lineasArray = textoHastaCursor.split('\n');
    
    const filaActual = lineasArray.length;
    const columnaActual = lineasArray[lineasArray.length - 1].length;

    statusBar.innerText = `Línea: ${filaActual} | Columna: ${columnaActual}`;
    
    // Sincronizar scroll inmediatamente
    sincronizarScroll();
}

// Sincronización de scroll mejorada
function sincronizarScroll() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    lineNumbers.scrollTop = editor.scrollTop;
}

// Configurar los eventos necesarios para que no se desfase
window.onload = () => {
    const editor = document.getElementById('editor');
    
    // Detecta escritura, borrado, pegado y movimientos de cursor
    editor.addEventListener('input', actualizarEditor);
    editor.addEventListener('click', actualizarEditor);
    editor.addEventListener('keyup', actualizarEditor);
    editor.addEventListener('scroll', sincronizarScroll);
    
    // Inicializar el estado
    actualizarEditor();
};

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
    
    // Mostrar salida en el panel correspondiente
    tabLex.innerText = respuesta.resultado || "Sin salida de tokens.";
    if (respuesta.errores) {
        consoleArea.innerText = respuesta.errores;
        consoleArea.style.color = "#f44336"; // Rojo para errores
    } else {
        consoleArea.innerText = "Análisis finalizado sin errores.";
        consoleArea.style.color = "#4ec9b0"; // Verde para éxito
    }
}

// Funciones para cambio de pestañas (Básico)
function verTab(evt, tabName) {
    let contents = document.getElementsByClassName("tab-content");
    for (let content of contents) content.classList.remove("active");
    let links = document.getElementsByClassName("tab-link");
    for (let link of links) link.classList.remove("active");
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

function verTabInferior(evt, tabName) {
    // 1. Ocultar todos los contenidos de la parte inferior
    let contents = document.getElementsByClassName("tab-content-inf");
    for (let content of contents) {
        content.classList.remove("active");
    }

    // 2. Quitar el estado activo SOLO a los botones del panel inferior
    let tabsContainer = evt.currentTarget.parentElement;
    let links = tabsContainer.getElementsByClassName("tab-link");
    for (let link of links) {
        link.classList.remove("active");
    }

    // 3. Mostrar el contenido seleccionado y activar el botón
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}