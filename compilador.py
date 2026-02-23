import json
import sys

def main():
    fase = sys.argv[1]
    archivo = sys.argv[2]
    
    respuesta = {"resultado": "", "errores": [], "tabla_simbolos": []}

    try:
        if fase == "lexico":
            respuesta["resultado"] = "Lista de Tokens..." 
        elif fase == "sintactico":
            respuesta["resultado"] = "Árbol Sintáctico Estructurado..."
        elif fase == "semantico":
            respuesta["resultado"] = "Validaciones Semánticas..."
        elif fase == "intermedio":
            respuesta["resultado"] = "Código de 3 Direcciones..."
        elif fase == "ejecucion":
            respuesta["resultado"] = "Salida real del programa..."
            
    except Exception as e:
        respuesta["errores"].append({"linea": 1, "desc": str(e)})

    print(json.dumps(respuesta))