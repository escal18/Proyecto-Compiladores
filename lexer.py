import re

TOKENS_RULES = [
    ('COMENTARIO_MULT', r'/\*[\s\S]*?\*/'),          # Estilo C 
    ('COMENTARIO_LINEA', r'//.*'),                   # Estilo C 
    ('NUMERO_REAL',   r'\d+\.\d+'),                  # Color 1 [cite: 11]
    ('NUMERO_ERROR',  r'\d+\.'),                     # Manejo de error léxico 
    ('NUMERO_ENTERO', r'\d+'),                       # Color 1 [cite: 11]
    # Lista exacta de 12 palabras reservadas [cite: 13]
    ('RESERVADA',     r'\b(if|else|end|do|while|switch|case|int|float|main|cin|cout)\b'), 
    ('OPERADOR_ARIT', r'\+\+|--|\+|\-|\*|/|%|\^'),   # Color 5 [cite: 14]
    ('OPERADOR_REL',  r'<=|>=|!=|==|<|>'),           # Color 6 [cite: 15]
    # Solo acepta parejas para and/or 
    ('OPERADOR_LOG',  r'&&|\|\||!'),                 # Color 6 
    ('ASIGNACION',    r'='),                         # Asignación [cite: 19]
    # Símbolos oficiales únicamente [cite: 18]
    ('SIMBOLO',       r'\(|\)|\{|\}|,|;|"|\''),      
    ('ID',            r'[a-zA-Z][a-zA-Z0-9]*'),      
    ('ESPACIO',       r'[ \t]+'),                    
    ('NUEVA_LINEA',   r'\n'),                        
]

def analizar(codigo):
    tokens_lista = []
    errores_lista = []
    linea = 1
    pos_linea_inicio = 0
    pos_actual = 0
    
    regex_master = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKENS_RULES)
    
    for match in re.finditer(regex_master, codigo):
        tipo = match.lastgroup
        valor = match.group(tipo)
        columna = match.start() - pos_linea_inicio + 1
        
        if match.start() > pos_actual:
            basura = codigo[pos_actual:match.start()].replace('\n', '').strip()
            if basura:
                errores_lista.append({
                    "linea": linea, "columna": pos_actual - pos_linea_inicio + 1,
                    "desc": f"Caracter no reconocido: '{basura}'"
                })

        if tipo == 'NUEVA_LINEA':
            linea += 1
            pos_linea_inicio = match.end()
        elif tipo == 'NUMERO_ERROR':
            errores_lista.append({
                "linea": linea, "columna": columna, "desc": f"Número real incompleto: '{valor}'"
            })
        elif tipo in ['COMENTARIO_MULT', 'COMENTARIO_LINEA', 'ESPACIO']:
            pass 
        else:
            tokens_lista.append({
                "tipo": tipo, "valor": valor, "linea": linea, "columna": columna
            })
        
        pos_actual = match.end()

    if pos_actual < len(codigo):
        final = codigo[pos_actual:].replace('\n', '').strip()
        if final:
            errores_lista.append({
                "linea": linea, "columna": pos_actual - pos_linea_inicio + 1, "desc": f"Error léxico al final: '{final}'"
            })

    return tokens_lista, errores_lista