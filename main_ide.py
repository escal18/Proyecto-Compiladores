import eel
import subprocess
import os
from tkinter import filedialog, Tk

# Inicializar Eel
eel.init('web')

# Función auxiliar para diálogos nativos de Windows/Linux
def seleccionar_ruta(tipo="guardar"):
    root = Tk()
    root.withdraw() # Ocultar ventana principal de Tkinter
    root.attributes("-topmost", True)
    if tipo == "abrir":
        ruta = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
    else:
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")])
    root.destroy()
    return ruta

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
    # Si no tiene ruta (es "Guardar como" o archivo nuevo), pedimos ruta
    if not ruta:
        ruta = seleccionar_ruta("guardar")
    
    if ruta:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta
    return None

@eel.expose
def ejecutar_fase_compilador(fase, codigo):
    # Req. 69: Comunicación mediante archivo temporal
    ruta_temp = "temp_fuente.txt"
    with open(ruta_temp, "w", encoding="utf-8") as f:
        f.write(codigo)
    
    # Req. 2.2 y 4: Llamada al sistema (System Call)
    comando = ["python", "compilador.py", fase, ruta_temp]
    proceso = subprocess.run(comando, capture_output=True, text=True)
    
    return {
        "resultado": proceso.stdout,
        "errores": proceso.stderr
    }

# Req. 73: Tamaño de ventana
eel.start('index.html', size=(1200, 850))