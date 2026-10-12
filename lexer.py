import re

TOKENS_RULES = [
<<<<<<< HEAD
    ('COMENTARIO_MULT', r'/\*[\s\S]*?\*/'),
    ('COMENTARIO_SIN_CIERRE', r'/\*[\s\S]*\Z'),
    ('COMENTARIO_LINEA', r'//[^\r\n]*'),
    ('NUMERO_REAL', r'[0-9]+\.[0-9]+'),
    ('NUMERO_ERROR', r'[0-9]+\.'),
    ('NUMERO_ENTERO', r'[0-9]+'),
    ('BOOLEANO', r'\b(?:true|false)\b'),
    ('RESERVADA', r'\b(?:if|else|end|do|until|while|switch|case|int|float|bool|main|cin|cout|then)\b'),
    ('OPERADOR_IO', r'>>|<<'),
    ('OPERADOR_ARIT', r'\+\+|--|[+*/%^-]'),
    ('OPERADOR_REL', r'<=|>=|!=|==|<|>'),
    ('OPERADOR_LOG', r'&&|\|\||!'),
    ('ASIGNACION', r'='),
    ('SIMBOLO', r'''[(){};,"']'''),
    ('ID', r'[a-zA-Z][a-zA-Z0-9]*'),
    ('ESPACIO', r'[^\S\r\n]+'),
    ('NUEVA_LINEA', r'\r\n|\r|\n'),
    ('ERROR', r'[\s\S]'),
=======
    ('COMENTARIO_MULT', r'/\*[\s\S]*?\*/'),          # Estilo C 
    ('COMENTARIO_LINEA', r'//.*'),                   # Estilo C 
    ('NUMERO_REAL',   r'\d+\.\d+'),                  # Color 1 [cite: 11]
    ('NUMERO_ERROR',  r'\d+\.'),                     # Manejo de error léxico 
    ('NUMERO_ENTERO', r'\d+'),                       # Color 1 [cite: 11]
    # Lista exacta de 12 palabras reservadas [cite: 13]
    ('RESERVADA',     r'\b(if|else|end|do|while|switch|case|int|float|main|cin|cout|then)\b'), 
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
>>>>>>> aca605603ed2f2c91b9b8812b36106c963bf9e70
]
REGEX_MASTER = re.compile('|'.join(f'(?P<{nombre}>{patron})' for nombre, patron in TOKENS_RULES))


def analizar(codigo):
    tokens, errores = [], []
    linea, columna = 1, 1
    for match in REGEX_MASTER.finditer(codigo):
        tipo, valor = match.lastgroup, match.group()
        ubicacion = {"linea": linea, "columna": columna}
        if tipo in ('ERROR', 'NUMERO_ERROR', 'COMENTARIO_SIN_CIERRE'):
            descripcion = {
                'ERROR': f"Carácter no reconocido: '{valor}'",
                'NUMERO_ERROR': f"Número real incompleto: '{valor}'",
                'COMENTARIO_SIN_CIERRE': "Comentario multilínea sin cierre '*/'",
            }[tipo]
            errores.append({**ubicacion, "fase": "lexico", "desc": descripcion})
        elif tipo not in ('COMENTARIO_MULT', 'COMENTARIO_LINEA', 'ESPACIO', 'NUEVA_LINEA'):
            tokens.append({"tipo": tipo, "valor": valor, **ubicacion})
        partes = re.split(r'\r\n|\r|\n', valor)
        if len(partes) > 1:
            linea += len(partes) - 1
            columna = len(partes[-1]) + 1
        else:
            columna += len(valor)
    return tokens, errores
