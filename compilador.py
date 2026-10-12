import json
import sys
import lexer
import parser_sintactico
from archivos_fuente import leer_fuente

def main():
    if len(sys.argv) < 3: return
    
    fase = sys.argv[1]
    ruta_archivo = sys.argv[2]
    
    respuesta = {"resultado": "", "errores": [], "tabla_simbolos": []}

    try:
        codigo = leer_fuente(ruta_archivo)
            
        if fase == "lexico":
            tokens, errores = lexer.analizar(codigo)
            respuesta["resultado"] = tokens
            respuesta["errores"] = errores
            
        elif fase == "sintactico":
            tokens, errores_lexicos = lexer.analizar(codigo)
            
            parser = parser_sintactico.Parser(tokens)
            arbol, errores_sintacticos = parser.parse()
            
            respuesta["resultado"] = arbol
            respuesta["errores_lexicos"] = errores_lexicos
            respuesta["errores_sintacticos"] = errores_sintacticos
            respuesta["errores"] = errores_lexicos + errores_sintacticos
            
        elif fase == "semantico":
            respuesta["resultado"] = "Análisis semántico pendiente de implementar."
            respuesta["implementado"] = False
        elif fase == "intermedio":
            respuesta["resultado"] = "Código intermedio pendiente de implementar."
            respuesta["implementado"] = False
        elif fase == "ejecucion":
            respuesta["resultado"] = "Ejecución pendiente de implementar."
            respuesta["implementado"] = False
        else:
            respuesta["errores"].append({"linea": "N/A", "columna": "N/A", "desc": f"Fase desconocida: {fase}"})
            
    except Exception as e:
        respuesta["errores"].append({"linea": "N/A", "desc": str(e)})

    print(json.dumps(respuesta))

if __name__ == "__main__":
    main()
