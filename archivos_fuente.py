"""Lectura común para el IDE y la línea de comandos."""
from pathlib import Path


def leer_fuente(ruta):
    datos = Path(ruta).read_bytes()
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Compatibilidad con archivos antiguos guardados por Windows.
        texto = datos.decode("cp1252")
    return texto.replace("\r\n", "\n").replace("\r", "\n")
