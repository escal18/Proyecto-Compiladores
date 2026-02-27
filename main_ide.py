import eel
import subprocess
import os
import json
from tkinter import filedialog, Tk

eel.init('web')

@eel.expose
def finalizar_programa():
    print("Se recibió orden de cierre desde el IDE.")
    os._exit(0)

@eel.expose
def abrir_archivo_py():
    ruta = seleccionar_ruta("abrir")
    if ruta:
        try:
            with open(ruta, "r", encoding="cp1252") as f:
                contenido = f.read()
            return {"ruta": ruta, "contenido": contenido}
        except Exception as e:
            print(f"Error al abrir archivo: {e}")
    return None

@eel.expose
def guardar_archivo_py(contenido, ruta=None):
    if not ruta:
        ruta = seleccionar_ruta("guardar")
    
    if ruta:
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            return ruta
        except Exception as e:
            print(f"Error al guardar archivo: {e}")
    return None

@eel.expose
def ejecutar_fase_compilador(fase, codigo):
    ruta_temp = "temp_fuente.txt"
    with open(ruta_temp, "w", encoding="utf-8") as f:
        f.write(codigo)
    
    comando = ["python", "compilador.py", fase, ruta_temp]
    proceso = subprocess.run(comando, capture_output=True, text=True)
    
    try:
        return json.loads(proceso.stdout)
    except:
        return {"resultado": "", "errores": [{"linea": "N/A", "desc": proceso.stderr}]}

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

if __name__ == '__main__':
    eel.start('index.html', size=(1200, 850), close_callback=lambda route, websockets: os._exit(0))