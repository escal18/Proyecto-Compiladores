import eel
import subprocess
import os
from tkinter import filedialog, Tk

# Inicializar Eel
eel.init('web')

# --- FUNCIONES EXPUESTAS A JS ---
@eel.expose
def finalizar_programa():
    print("Se recibió orden de cierre desde el IDE.")
    os._exit(0) # Mata el proceso inmediatamente

@eel.expose
def abrir_archivo_py():
    ruta = seleccionar_ruta("abrir")
    if ruta:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
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
    # Comunicación mediante archivo temporal
    ruta_temp = "temp_fuente.txt"
    with open(ruta_temp, "w", encoding="utf-8") as f:
        f.write(codigo)
    
    # Llamada al sistema para ejecutar la lógica del compilador
    comando = ["python", "compilador.py", fase, ruta_temp]
    proceso = subprocess.run(comando, capture_output=True, text=True)
    
    return {
        "resultado": proceso.stdout,
        "errores": proceso.stderr
    }

# --- FUNCIONES AUXILIARES ---

def seleccionar_ruta(tipo="guardar"):
    root = Tk()
    root.withdraw() # Ocultar ventana principal de Tkinter
    root.attributes("-topmost", True) # Poner el diálogo al frente
    if tipo == "abrir":
        ruta = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
    else:
        ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")])
    root.destroy()
    return ruta

# --- INICIO DE APLICACIÓN ---

if __name__ == '__main__':
    eel.start('index.html', size=(1200, 850), close_callback=lambda route, websockets: os._exit(0))