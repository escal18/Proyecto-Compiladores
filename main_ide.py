import eel
import subprocess
import os
import json
import sys
import tempfile
from pathlib import Path
from archivos_fuente import leer_fuente
from tkinter import filedialog, Tk

BASE_DIR = Path(__file__).resolve().parent
eel.init(str(BASE_DIR / 'web'))

@eel.expose
def finalizar_programa():
    print("Se recibió orden de cierre desde el IDE.")
    os._exit(0)

@eel.expose
def abrir_archivo_py():
    ruta = seleccionar_ruta("abrir")
    if ruta:
        try:
            contenido = leer_fuente(ruta)
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
    try:
        with tempfile.TemporaryDirectory(prefix='compilador-') as carpeta:
            ruta_temp = Path(carpeta) / 'fuente.txt'
            ruta_temp.write_text(codigo, encoding='utf-8')
            comando = [sys.executable, str(BASE_DIR / 'compilador.py'), fase, str(ruta_temp)]
            proceso = subprocess.run(comando, capture_output=True, text=True, encoding='utf-8', timeout=30)
        if proceso.returncode:
            raise RuntimeError(proceso.stderr or 'El proceso del compilador falló')
        return json.loads(proceso.stdout)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        return {"resultado": "", "errores": [{"linea": "N/A", "columna": "N/A", "fase": "sistema", "desc": str(error)}]}

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
