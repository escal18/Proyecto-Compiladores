import re

# Definición de tokens y sus expresiones regulares según el PDF [cite: 11-19]
TOKENS_RULES = [
    ('COMENTARIO_MULT', r'/\*[\s\S]*?\*/'),          # Color 3
    ('COMENTARIO_LINEA', r'//.*'),                   # Color 3
    ('NUMERO_REAL',   r'\d+\.\d+'),                  # Color 1
    ('NUMERO_ENTERO', r'\d+'),                       # Color 1
    ('RESERVADA',     r'\b(if|else|end|do|while|switch|case|int|float|main|cin|cout)\b'), # Color 4
    ('OPERADOR_ARIT', r'\+\+|--|\+|\-|\*|/|%|\^'),   # Color 5
    ('OPERADOR_REL',  r'<=|>=|!=|==|<|>'),           # Color 6
    ('OPERADOR_LOG',  r'&&|\|\||!'),                 # Color 6
    ('ASIGNACION',    r'='),
    ('SIMBOLO',       r'\(|\)|\{|\}|,|;|"|\''),      # Símbolos [cite: 18]
    ('ID',            r'[a-zA-Z][a-zA-Z0-9]*'),      # Color 2 (no empieza con dígito)
    ('ESPACIO',       r'[ \t]+'),                    # Ignorar
    ('NUEVA_LINEA',   r'\n'),                        # Para contar líneas
]

def analizar(codigo):
    tokens_lista = []
    errores_lista = []
    
    linea = 1
    pos_linea_inicio = 0
    pos_actual = 0
    
    # Unir todas las reglas en una sola regex master
    regex_master = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKENS_RULES)
    
    for match in re.finditer(regex_master, codigo):
        tipo = match.lastgroup
        valor = match.group(tipo)
        columna = match.start() - pos_linea_inicio + 1
        
        # Manejar caracteres no reconocidos antes del match actual
        if match.start() > pos_actual:
            error_txt = codigo[pos_actual:match.start()].strip()
            if error_txt:
                errores_lista.append({
                    "linea": linea, 
                    "columna": pos_actual - pos_linea_inicio + 1,
                    "desc": f"Caracter no reconocido: '{error_txt}'"
                })

        if tipo == 'NUEVA_LINEA':
            linea += 1
            pos_linea_inicio = match.end()
        elif tipo == 'ESPACIO':
            pass
        else:
            tokens_lista.append(f"<{tipo}, {valor}, Lin: {linea}, Col: {columna}>")
        
        pos_actual = match.end()

    # Verificar si quedó basura al final del archivo 
    if pos_actual < len(codigo):
        error_txt = codigo[pos_actual:].strip()
        if error_txt:
            errores_lista.append({
                "linea": linea, 
                "columna": pos_actual - pos_linea_inicio + 1,
                "desc": f"Error léxico al final: '{error_txt}'"
            })

    return "\n".join(tokens_lista), errores_lista