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
        document.getElementById('tab-lexico').innerText = "Lista de tokens...";
        document.getElementById('err-lexico').innerText = "Lista de errores léxicos...";
    }
}

// --- FUNCIÓN SALIR CORREGIDA ---
async function salir() {
    const confirmar = await mostrarConfirmacion("¿Está seguro de que desea salir del IDE?");
    
    if (confirmar) {
        console.log("Cerrando sistema...");
        // 1. Llamamos a la función de Python (sin await para que no espere respuesta)
        eel.finalizar_programa()();
        
        // 2. Cerramos la ventana visualmente después de un milisegundo
        // Esto ayuda si el navegador está bloqueando el cierre del proceso
        setTimeout(() => {
            window.close();
        }, 100);
    }
}

function mostrarConfirmacion(mensaje) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-modal');
        const btnAccept = document.getElementById('modal-accept');
        const btnCancel = document.getElementById('modal-cancel');
        const msgElement = document.getElementById('modal-message');

        msgElement.innerText = mensaje;
        modal.style.display = 'flex';

        // Limpiamos eventos previos para que no se acumulen
        btnAccept.onclick = null;
        btnCancel.onclick = null;

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

// --- LÓGICA DEL EDITOR ---
function actualizarEditor() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.getElementById('line-numbers');
    const statusBar = document.getElementById('posicion-cursor');

    // 1. Obtener el texto actual
    const texto = editor.value;

    // 2. Sincronizar numeración de líneas
    // Usamos una expresión regular para contar todas las líneas, incluso si están vacías
    const totalLineas = texto.split(/\r?\n/).length;
    let numerosHtml = "";
    for (let i = 1; i <= totalLineas; i++) {
        numerosHtml += `<div>${i}</div>`;
    }
    lineNumbers.innerHTML = numerosHtml;

    // 3. Calcular Fila y Columna exactas
    const posicionCursor = editor.selectionStart;
    
    // Cortamos el texto hasta donde está el cursor
    const textoHastaCursor = texto.substring(0, posicionCursor);
    
    // Las líneas son el número de saltos de línea encontrados + 1
    const lineasSub = textoHastaCursor.split(/\r?\n/);
    const filaActual = lineasSub.length;
    
    // La columna es el largo de la última línea en el array (donde está el cursor)
    const columnaActual = lineasSub[filaActual - 1].length;

    // 4. Actualizar Barra de Estado
    const nombreArchivo = rutaActual ? rutaActual.split(/[\\/]/).pop() : 'Sin título';
    statusBar.innerText = `Archivo: ${nombreArchivo} | Línea: ${filaActual} | Columna: ${columnaActual}`;
    
    // 5. Sincronizar el scroll de los números
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

document.addEventListener('DOMContentLoaded', function () {
    const resizer = document.getElementById('dragMe');
    const leftSide = document.getElementById('left-panel'); // Asegúrate de que coincida con el ID del HTML

    let x = 0;
    let leftWidth = 0;

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
        
        // Aplicamos el nuevo ancho en porcentaje
        leftSide.style.flex = `0 0 ${newLeftWidth}%`;
        actualizarEditor();
    };

    const mouseUpHandler = function () {
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
    };

    resizer.addEventListener('mousedown', mouseDownHandler);
});