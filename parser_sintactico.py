"""Parser descendente recursivo. Conserva el formato del AST usado por el IDE."""


class Parser:
    LIMITES = {'}', 'end', 'else', 'until'}

    def __init__(self, tokens):
        ignorados = {'ESPACIO', 'NUEVA_LINEA', 'COMENTARIO_LINEA', 'COMENTARIO_MULT'}
        self.tokens = [t for t in tokens if t['tipo'] not in ignorados]
        self.pos = 0
        self.errores = []

    def get_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek(self, tipo=None, valor=None):
        tk = self.get_token()
        if tk and (tipo is None or tk['tipo'] == tipo) and (valor is None or tk['valor'] == valor):
            return tk
        return None

    def consume(self, tipo=None, valor=None):
        tk = self.peek(tipo, valor)
        if tk:
            self.pos += 1
        return tk

    def reportar_error(self, desc):
        tk = self.get_token()
        ultimo = self.tokens[-1] if self.tokens else None
        linea = tk['linea'] if tk else (ultimo['linea'] if ultimo else 1)
        columna = tk['columna'] if tk else (ultimo['columna'] + len(ultimo['valor']) if ultimo else 1)
        self.errores.append({'linea': linea, 'columna': columna, 'fase': 'sintactico', 'desc': desc})

    def exigir(self, tipo, valor=None, desc=None):
        tk = self.consume(tipo, valor)
        if not tk:
            self.reportar_error(desc or f"Se esperaba '{valor or tipo}'")
        return tk

    def nodo(self, name, clase, token=None, children=None, **atributos):
        tk = token or self.get_token() or (self.tokens[-1] if self.tokens else None)
        return {
            'name': name, 'clase': clase,
            'linea': tk['linea'] if tk else 1, 'columna': tk['columna'] if tk else 1,
            **({'lexema': tk['valor'], 'tipo_token': tk['tipo']} if tk else {}),
            **({'children': children} if children is not None else {}), **atributos,
        }

    def bloque(self, name, limites, token=None):
        nodo = self.nodo(name, 'bloque', token, [])
        while self.get_token() and self.get_token()['valor'] not in limites | self.LIMITES:
            anterior = self.pos
            stmt = self.parse_statement()
            if stmt:
                nodo['children'].append(stmt)
            if self.pos == anterior:
                self.reportar_error('No se pudo procesar la sentencia')
                self.pos += 1
        return nodo

    def parse(self):
        raiz = self.nodo('Programa (AST)', 'programa', children=[])
        if self.peek('RESERVADA', 'main'):
            raiz['children'].append(self.parse_main())
        else:
            self.reportar_error("El programa debe iniciar con 'main'")
        while self.get_token():
            self.reportar_error(f"Elemento fuera del bloque main: '{self.get_token()['valor']}'")
            self.pos += 1
        return raiz, self.errores

    def parse_main(self):
        tk = self.consume('RESERVADA', 'main')
        apertura = self.exigir('SIMBOLO', '{', "Se esperaba '{' después de 'main'")
        cuerpo = self.bloque('Bloque', {'}'}, apertura or tk)
        self.exigir('SIMBOLO', '}', "Falta '}' al cerrar main")
        return self.nodo('Función Principal (main)', 'main', tk, [cuerpo])

    def parse_statement(self):
        tk = self.get_token()
        if not tk:
            return None
        if tk['valor'] in ('int', 'float', 'bool'):
            return self.parse_declaracion()
        if tk['valor'] == 'if':
            return self.parse_if()
        if tk['valor'] == 'while':
            return self.parse_while()
        if tk['valor'] == 'do':
            return self.parse_do()
        if tk['valor'] in ('cin', 'cout'):
            return self.parse_io()
        if tk['valor'] == '{':
            apertura = self.consume()
            bloque = self.bloque('Bloque', {'}'}, apertura)
            self.exigir('SIMBOLO', '}')
            return bloque
        if tk['tipo'] == 'ID':
            return self.parse_asignacion_o_postfix()
        self.reportar_error(f"Sentencia no válida iniciando con '{tk['valor']}'")
        self.pos += 1
        return None

    def parse_declaracion(self):
        tk = self.consume('RESERVADA')
        variables = []
        while True:
            ident = self.exigir('ID', desc='Se esperaba un identificador en la declaración')
            if not ident:
                break
            var = self.nodo('Variable', 'identificador', ident, value=ident['valor'])
            if self.consume('ASIGNACION'):
                var['children'] = [self.parse_expresion()]
            variables.append(var)
            if not self.consume('SIMBOLO', ','):
                break
        self.exigir('SIMBOLO', ';', "Falta ';' al final de la declaración")
        return self.nodo(f"Declaración ({tk['valor']})", 'declaracion', tk, variables, tipo_declarado=tk['valor'])

    def parse_asignacion_o_postfix(self):
        tk = self.consume('ID')
        var = self.nodo('Destino', 'identificador', tk, value=tk['valor'])
        op = self.consume('ASIGNACION')
        if op:
            expr = self.parse_expresion()
            self.exigir('SIMBOLO', ';', f"Falta ';' después de asignar a '{tk['valor']}'")
            return self.nodo('Asignación (=)', 'asignacion', op, [var, expr], operador='=')
        if self.peek('OPERADOR_ARIT') and self.get_token()['valor'] in ('++', '--'):
            op = self.consume()
            self.exigir('SIMBOLO', ';', "Falta ';' después del incremento/decremento")
            var['name'] = 'Variable'
            return self.nodo(f"Post-fijo ({op['valor']})", 'postfijo', op, [var], operador=op['valor'])
        self.reportar_error(f"Se esperaba asignación o incremento/decremento después de '{tk['valor']}'")
        self.consume('SIMBOLO', ';')
        return self.nodo('Error: sentencia incompleta', 'error', tk)

    def parse_io(self):
        tk = self.consume('RESERVADA')
        operador = '>>' if tk['valor'] == 'cin' else '<<'
        # Se conserva la entrada/salida antigua sin >>/<< para los archivos previos.
        if self.peek('OPERADOR_IO'):
            self.exigir('OPERADOR_IO', operador, f"{tk['valor']} requiere '{operador}'")
        if tk['valor'] == 'cin':
            ident = self.exigir('ID', desc='cin requiere una variable de destino')
            expr = self.nodo('Variable', 'identificador', ident, value=ident['valor']) if ident else self.nodo('Error', 'error')
        else:
            expr = self.parse_expresion()
        self.exigir('SIMBOLO', ';', f"Falta ';' al final de {tk['valor']}")
        return self.nodo(f"I/O ({tk['valor']})", tk['valor'], tk, [expr])

    def parse_if(self):
        tk = self.consume('RESERVADA', 'if')
        cond = self.parse_expresion()
        hijos = [cond]
        if self.peek('SIMBOLO', '{'):
            hijos.append(self.parse_statement())
            if self.consume('RESERVADA', 'else'):
                self.exigir('SIMBOLO', '{')
                hijos.append(self.bloque('Else', {'}'}, tk))
                self.exigir('SIMBOLO', '}')
        else:
            self.exigir('RESERVADA', 'then', "Falta 'then' después de la condición")
            hijos.append(self.bloque('Then', {'else', 'end'}, tk))
            if self.consume('RESERVADA', 'else'):
                hijos.append(self.bloque('Else', {'end'}, tk))
            self.exigir('RESERVADA', 'end', "Falta 'end' al cerrar if")
        self.consume('SIMBOLO', ';')
        return self.nodo('If', 'if', tk, hijos)

    def parse_while(self):
        tk = self.consume('RESERVADA', 'while')
        cond = self.parse_expresion()
        if self.peek('SIMBOLO', '{'):
            cuerpo = self.parse_statement()
        else:
            cuerpo = self.bloque('Cuerpo', {'end'}, tk)
            self.exigir('RESERVADA', 'end', "Falta 'end' al cerrar while")
        self.consume('SIMBOLO', ';')
        return self.nodo('While', 'while', tk, [cond, cuerpo])

    def parse_do(self):
        tk = self.consume('RESERVADA', 'do')
        cuerpo = self.bloque('Cuerpo', {'until'}, tk)
        self.exigir('RESERVADA', 'until', "Falta 'until' al cerrar do")
        cond = self.parse_expresion()
        self.consume('SIMBOLO', ';')
        return self.nodo('Do-Until', 'do_until', tk, [cuerpo, cond])

    def binario(self, siguiente, operadores):
        left = siguiente()
        while self.get_token() and self.get_token()['valor'] in operadores:
            op = self.consume()
            right = siguiente()
            left = self.nodo(f"Op ({op['valor']})", 'binario', op, [left, right], operador=op['valor'])
        return left

    def parse_expresion(self):
        return self.parse_or()

    def parse_or(self):
        return self.binario(self.parse_and, {'||'})

    def parse_and(self):
        return self.binario(self.parse_relacional, {'&&'})

    def parse_relacional(self):
        left = self.parse_aritmetico_1()
        if self.peek('OPERADOR_REL'):
            op = self.consume()
            right = self.parse_aritmetico_1()
            return self.nodo(f"Op ({op['valor']})", 'binario', op, [left, right], operador=op['valor'])
        return left

    def parse_aritmetico_1(self):
        return self.binario(self.parse_aritmetico_2, {'+', '-'})

    def parse_aritmetico_2(self):
        return self.binario(self.parse_unario, {'*', '/', '%'})

    def parse_unario(self):
        if self.get_token() and self.get_token()['valor'] in ('!', '+', '-'):
            op = self.consume()
            return self.nodo(f"Unario ({op['valor']})", 'unario', op, [self.parse_unario()], operador=op['valor'])
        return self.parse_potencia()

    def parse_potencia(self):
        left = self.parse_factor()
        if self.peek('OPERADOR_ARIT', '^'):
            op = self.consume()
            return self.nodo('Op (^)', 'binario', op, [left, self.parse_unario()], operador='^')
        return left

    def parse_factor(self):
        tk = self.get_token()
        if tk and tk['tipo'] in ('ID', 'NUMERO_ENTERO', 'NUMERO_REAL', 'BOOLEANO'):
            self.consume()
            clase = 'identificador' if tk['tipo'] == 'ID' else 'literal'
            return self.nodo('Valor', clase, tk, value=tk['valor'])
        if self.consume('SIMBOLO', '('):
            expr = self.parse_expresion()
            self.exigir('SIMBOLO', ')', "Se esperaba ')' al cerrar expresión")
            return expr
        self.reportar_error(f"Se esperaba un operando, se encontró '{tk['valor'] if tk else 'fin de archivo'}'")
        # Conserva los inicios de sentencia y cierres para recuperarse sin perder bloques.
        if tk and tk['tipo'] != 'RESERVADA' and tk['valor'] not in self.LIMITES | {';', ')', ',', '{'}:
            self.pos += 1
        return self.nodo('Error: expresión faltante', 'error', tk)
