import eel
import subprocess
import os
from tkinter import filedialog, Tk

# Inicializar Eel
eel.init('web')

# --- FUNCIONES EXPUESTAS A JS ---

@eel.expose
def finalizar_programa():
    # Cierre forzoso del proceso completo
    os._exit(0)

@eel.expose
def abrir_archivo_py():
    ruta = seleccionar_ruta("abrir")
    if ruta:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()
        return {"ruta": ruta, "contenido": contenido}
    return None

@eel.expose
def guardar_archivo_py(contenido, ruta=None):
    if not ruta:
        ruta = seleccionar_ruta("guardar")
    
    if ruta:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta
    return None

@eel.expose
def ejecutar_fase_compilador(fase, codigo):
    ruta_temp = "temp_fuente.txt"
    with open(ruta_temp, "w", encoding="utf-8") as f:
        f.write(codigo)
    
    comando = ["python", "compilador.py", fase, ruta_temp]
    proceso = subprocess.run(comando, capture_output=True, text=True)
    
    return {
        "resultado": proceso.stdout,
        "errores": proceso.stderr
    }

# --- FUNCIONES AUXILIARES ---

def seleccionar_ruta(tipo="guardar"):
    root = Tk()
    root.withdraw() 
    root.attributes("-topmost", True)
    if tipo == "abrir":
        ruta = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
    else:
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")])
    root.destroy()
    return ruta

# --- INICIO DE APLICACIÓN ---

# Usamos un solo eel.start con el close_callback para asegurar que 
# si cierran la ventana desde la "X", el proceso de Python también muera.
eel.start('index.html', size=(1200, 850), close_callback=lambda route, websockets: os._exit(0))