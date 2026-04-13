import re

# Definición de tokens. El orden es CRÍTICO.
TOKENS_RULES = [
    ('COMENTARIO_MULT', r'/\*[\s\S]*?\*/'),          
    ('COMENTARIO_LINEA', r'//.*'),                   
    ('NUMERO_REAL',   r'\d+\.\d+'),                  # Detecta 32.32
    ('NUMERO_ERROR',  r'\d+\.'),                     # Captura errores como '32.'
    ('NUMERO_ENTERO', r'\d+'),                       
    ('RESERVADA',     r'\b(if|else|end|do|while|switch|case|int|float|main|cin|cout)\b'), 
    ('OPERADOR_ARIT', r'\+\+|--|\+|\-|\*|/|%|\^'),   # Compuestos van PRIMERO
    ('OPERADOR_REL',  r'<=|>=|!=|==|<|>'),           # Compuestos van PRIMERO
    ('OPERADOR_LOG',  r'&&|\|\||!'),                 
    ('ASIGNACION',    r'='),
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
        
        # 1. Detectar caracteres no reconocidos antes del token actual
        if match.start() > pos_actual:
            basura = codigo[pos_actual:match.start()].replace('\n', '').strip()
            if basura:
                errores_lista.append({
                    "linea": linea, 
                    "columna": pos_actual - pos_linea_inicio + 1,
                    "desc": f"Caracter no reconocido: '{basura}'"
                })

        # 2. Procesar el token según su tipo
        if tipo == 'NUEVA_LINEA':
            linea += 1
            pos_linea_inicio = match.end()
        elif tipo == 'NUMERO_ERROR':
            errores_lista.append({
                "linea": linea, "columna": columna,
                "desc": f"Número real incompleto: '{valor}'"
            })
        elif tipo in ['COMENTARIO_MULT', 'COMENTARIO_LINEA', 'ESPACIO']:
            pass # No se agregan a la lista de tokens
        else:
            tokens_lista.append({
                "tipo": tipo, "valor": valor, "linea": linea, "columna": columna
            })
        
        pos_actual = match.end()

    # Verificar basura al final
    if pos_actual < len(codigo):
        final = codigo[pos_actual:].replace('\n', '').strip()
        if final:
            errores_lista.append({
                "linea": linea, "columna": pos_actual - pos_linea_inicio + 1,
                "desc": f"Error léxico al final: '{final}'"
            })

    return tokens_lista, errores_lista