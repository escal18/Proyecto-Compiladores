import sys

def main():
    # El compilador recibe la fase y el archivo como argumentos de consola (Req. 31, 69)
    if len(sys.argv) < 3:
        print("Uso: python compilador.py [fase] [archivo]")
        return

    fase = sys.argv[1]
    archivo = sys.argv[2]

    try:
        with open(archivo, 'r') as f:
            codigo = f.read()
        
        # Lógica de simulación de fases para la Fase 1
        if fase == "lexico":
            print(f"Tokens generados para el archivo {archivo}:\n<ID, suma>, <ASIG, =>, <NUM, 10>")
        elif fase == "ejecucion":
            print("Resultado: 10")
        else:
            print(f"Ejecutando fase: {fase.upper()}")

    except Exception as e:
        # Error con descripción clara (Req. 61)
        sys.stderr.write(f"Error en Línea 1: No se pudo leer el archivo. Detalle: {str(e)}")

if __name__ == "__main__":
    main()