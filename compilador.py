import json
import sys
import lexer
import parser_sintactico
import analizador_semantico
from pathlib import Path
from archivos_fuente import leer_fuente

def main():
    if len(sys.argv) < 3: return
    
    fase = sys.argv[1]
    ruta_archivo = sys.argv[2]
    
    respuesta = {"resultado": "", "errores": [], "tabla_simbolos": []}

    try:
        codigo = leer_fuente(ruta_archivo)
        respuesta["fuente"] = codigo
            
        if fase == "lexico":
            tokens, errores = lexer.analizar(codigo)
            respuesta["resultado"] = tokens
            respuesta["errores"] = errores
            
        elif fase in ("sintactico", "semantico"):
            tokens, errores_lexicos = lexer.analizar(codigo)
            
            parser = parser_sintactico.Parser(tokens, codigo)
            arbol, errores_sintacticos = parser.parse()
            
            respuesta["resultado"] = arbol
            respuesta["errores_lexicos"] = errores_lexicos
            respuesta["errores_sintacticos"] = errores_sintacticos
            respuesta["errores"] = errores_lexicos + errores_sintacticos
            respuesta["ast_original"] = arbol
            if fase == "semantico":
                respuesta["errores_semanticos"] = []
                respuesta["traza_semantica"] = []
                respuesta["arbol_anotado"] = None
                respuesta["semantico_ejecutado"] = not respuesta["errores"]
                respuesta["implementado"] = True
                if respuesta["semantico_ejecutado"]:
                    resultado = analizador_semantico.analizar(arbol)
                    respuesta.update(resultado)
                    respuesta["resultado"] = resultado["arbol_anotado"]
                    respuesta["errores"] = resultado["errores_semanticos"]
                    respuesta["semantico_valido"] = not respuesta["errores"]
                else:
                    respuesta["resultado"] = "Corrige los errores léxicos o sintácticos antes de analizar la semántica."
                    respuesta["semantico_valido"] = False
                if len(sys.argv) == 5 and sys.argv[3] == "--exportar":
                    exportar_evidencias(respuesta, sys.argv[4])
        elif fase == "intermedio":
            respuesta["resultado"] = "Código intermedio pendiente de implementar."
            respuesta["implementado"] = False
        elif fase == "ejecucion":
            respuesta["resultado"] = "Ejecución pendiente de implementar."
            respuesta["implementado"] = False
        else:
            respuesta["errores"].append({"linea": "N/A", "columna": "N/A", "desc": f"Fase desconocida: {fase}"})
            
    except Exception as e:
        error = {"linea": "N/A", "columna": "N/A", "fase": "sistema", "desc": str(e)}
        respuesta["errores"].append(error)
        respuesta["errores_sistema"] = [error]
        if fase == "semantico":
            respuesta["semantico_ejecutado"] = False
            respuesta["semantico_valido"] = False
            respuesta["resultado"] = "No se pudo completar el análisis semántico."

    print(json.dumps(respuesta))

def exportar_evidencias(respuesta, carpeta):
    destino = Path(carpeta)
    destino.mkdir(parents=True, exist_ok=True)
    campos = {
        'ast_original.json': 'ast_original',
        'ast_anotado.json': 'arbol_anotado',
        'tabla_simbolos.json': 'tabla_simbolos',
        'errores_semanticos.json': 'errores_semanticos',
        'traza_semantica.json': 'traza_semantica',
    }
    for archivo, campo in campos.items():
        (destino / archivo).write_text(json.dumps(respuesta[campo], ensure_ascii=False, indent=2), encoding='utf-8')
    (destino / 'fuente.txt').write_text(respuesta.get('fuente', ''), encoding='utf-8')
    (destino / 'resultado_semantico.json').write_text(json.dumps(respuesta, ensure_ascii=False, indent=2), encoding='utf-8')
    errores = respuesta['errores_semanticos']
    reporte = '\n'.join(f"Línea {e['linea']}, columna {e['columna']} [{e['codigo']}]: {e['desc']}" for e in errores)
    if not respuesta['semantico_ejecutado']:
        reporte = 'Análisis semántico no ejecutado: existen errores en fases anteriores.'
    (destino / 'errores_semanticos.txt').write_text(reporte or 'Sin errores semánticos.', encoding='utf-8')

if __name__ == "__main__":
    main()
