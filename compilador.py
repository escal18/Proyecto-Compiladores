import json
import sys
import lexer
import parser_sintactico

def main():
    if len(sys.argv) < 3: return
    
    fase = sys.argv[1]
    ruta_archivo = sys.argv[2]
    
    respuesta = {"resultado": "", "errores": [], "tabla_simbolos": []}

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            codigo = f.read()
            
        if fase == "lexico":
            tokens, errores = lexer.analizar(codigo)
            respuesta["resultado"] = tokens
            respuesta["errores"] = errores
            
        elif fase == "sintactico":
            tokens, errores_lexicos = lexer.analizar(codigo)
            
            parser = parser_sintactico.Parser(tokens)
            arbol, errores_sintacticos = parser.parse()
            
            respuesta["resultado"] = arbol
            respuesta["errores"] = errores_sintacticos
            
        elif fase == "semantico":
            respuesta["resultado"] = "Validaciones Semánticas..."
        elif fase == "intermedio":
            respuesta["resultado"] = "Código de 3 Direcciones..."
        elif fase == "ejecucion":
            respuesta["resultado"] = "Salida real del programa..."
            
    except Exception as e:
        respuesta["errores"].append({"linea": "N/A", "desc": str(e)})

    print(json.dumps(respuesta))

if __name__ == "__main__":
    main()