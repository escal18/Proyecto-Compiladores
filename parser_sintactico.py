# parser_sintactico.py

class Parser:
    def __init__(self, tokens):
        ignorados = ['ESPACIO', 'NUEVA_LINEA', 'COMENTARIO_LINEA', 'COMENTARIO_MULT']
        self.tokens = [t for t in tokens if t['tipo'] not in ignorados]
        self.pos = 0
        self.errores = []

    def get_token(self):
        if self.pos < len(self.tokens): return self.tokens[self.pos]
        return None

    def peek(self, tipo=None, valor=None):
        tk = self.get_token()
        if tk:
            if (tipo is None or tk['tipo'] == tipo) and (valor is None or tk['valor'] == valor):
                return tk
        return None

    def consume(self, tipo=None, valor=None):
        tk = self.peek(tipo, valor)
        if tk:
            self.pos += 1
            return tk
        return None

    def reportar_error(self, desc):
        tk = self.get_token()
        linea = tk['linea'] if tk else "Fin"
        columna = tk['columna'] if tk else "Fin"
        self.errores.append({"linea": linea, "columna": columna, "desc": desc})

    def parse(self):
        # La raíz ahora especifica que es un AST
        raiz = {"name": "Programa (AST)", "children": []}
        while self.pos < len(self.tokens):
            tk = self.peek()
            
            if tk['valor'] in ['{', 'main', 'int', 'float', 'if', 'do', 'while', 'cin', 'cout'] or tk['tipo'] == 'ID':
                stmt = self.parse_statement()
                if stmt: raiz["children"].append(stmt)
            else:
                self.reportar_error(f"Elemento inesperado en el flujo principal: '{tk['valor']}'")
                self.pos += 1
                
        return raiz, self.errores

    def parse_statement(self):
        tk = self.peek()
        if not tk: return None
        
        if tk['valor'] == 'main': return self.parse_main()
        if tk['valor'] == '{': return self.parse_bloque_principal()
        if tk['valor'] in ['int', 'float']: return self.parse_declaracion()
        if tk['valor'] == 'if': return self.parse_if()
        if tk['valor'] == 'while': return self.parse_while()
        if tk['valor'] == 'do': return self.parse_do()
        if tk['valor'] in ['cin', 'cout']: return self.parse_io()
        if tk['tipo'] == 'ID': return self.parse_asignacion_o_postfix()
        
        self.reportar_error(f"Sentencia no válida iniciando con '{tk['valor']}'")
        self.pos += 1
        return None

    def parse_bloque_principal(self):
        self.consume('SIMBOLO', '{')
        nodo = {"name": "Bloque", "children": []}
        while self.pos < len(self.tokens) and not self.peek('SIMBOLO', '}'):
            stmt = self.parse_statement()
            if stmt: nodo["children"].append(stmt)
        self.consume('SIMBOLO', '}')
        return nodo

    def parse_main(self):
     
        self.consume('RESERVADA', 'main')
        
        
        if self.peek('SIMBOLO', '{'):
            bloque = self.parse_bloque_principal()
            return {"name": "Función Principal (main)", "children": [bloque]}
        else:
            self.reportar_error("Se esperaba un bloque '{' después de 'main'")
            return {"name": "Función Principal (main)", "children": [{"name": "Error: Falta bloque"}]}
    def parse_declaracion(self):
        tipo_tk = self.consume('RESERVADA')
        nodo = {"name": f"Declaración ({tipo_tk['valor']})", "children": []}
        
        while self.pos < len(self.tokens):
            id_tk = self.consume('ID')
            if not id_tk:
                self.reportar_error("Se esperaba un Identificador en la declaración")
                break
            
            nodo_var = {"name": "Variable", "value": id_tk['valor']}
            
            if self.peek('ASIGNACION'):
                self.consume('ASIGNACION')
                expr = self.parse_expresion()
                if expr: nodo_var["children"] = [expr]
                
            nodo["children"].append(nodo_var)
            
            if self.peek('SIMBOLO', ','):
                self.consume('SIMBOLO', ',')
            else:
                break
                
        if not self.consume('SIMBOLO', ';'):
            self.reportar_error("Falta ';' al final de la declaración")
        return nodo

    def parse_asignacion_o_postfix(self):
        id_tk = self.consume('ID')
        
        if self.peek('ASIGNACION'):
            self.consume('ASIGNACION')
            expr = self.parse_expresion()
            if not self.consume('SIMBOLO', ';'):
                self.reportar_error(f"Falta ';' después de asignar a '{id_tk['valor']}'")
            return {"name": "Asignación (=)", "children": [{"name": "Destino", "value": id_tk['valor']}, expr if expr else {"name": "Error: Expresión faltante"}]}
            
        elif self.peek('OPERADOR_ARIT') and self.peek('OPERADOR_ARIT')['valor'] in ['++', '--']:
            op_tk = self.consume('OPERADOR_ARIT')
            self.consume('SIMBOLO', ';')
            return {"name": f"Post-fijo ({op_tk['valor']})", "children": [{"name": "Variable", "value": id_tk['valor']}]}
            
        else:
            self.reportar_error(f"Se esperaba asignación o incremento/decremento después de '{id_tk['valor']}'")
            self.pos += 1
            return None

    def parse_io(self):
        io_tk = self.consume('RESERVADA')
        
        # En lugar de consumir un solo token, evaluamos toda la expresión matemática
        expr = self.parse_expresion() 
        
        if not self.consume('SIMBOLO', ';'):
            self.reportar_error(f"Falta ';' al final de la instrucción {io_tk['valor']}")
            
        return {
            "name": f"I/O ({io_tk['valor']})", 
            "children": [expr if expr else {"name": "Error: Expresión faltante"}]
        }

    def parse_if(self):
        self.consume('RESERVADA', 'if')
        self.consume('SIMBOLO', '(')
        cond = self.parse_expresion()
        self.consume('SIMBOLO', ')')
        
        nodo = {"name": "If", "children": [cond if cond else {"name": "Error: Condición Inválida"}]}
        
        if self.peek('RESERVADA', 'then'): self.consume('RESERVADA', 'then')
        elif self.peek('SIMBOLO', '{'): pass
        
        bloque_then = {"name": "Then", "children": []}
        while self.pos < len(self.tokens) and not (self.peek('RESERVADA', 'else') or self.peek('RESERVADA', 'end') or self.peek('SIMBOLO', '}')):
            stmt = self.parse_statement()
            if stmt: bloque_then["children"].append(stmt)
        nodo["children"].append(bloque_then)

        if self.peek('RESERVADA', 'else'):
            self.consume('RESERVADA', 'else')
            bloque_else = {"name": "Else", "children": []}
            while self.pos < len(self.tokens) and not (self.peek('RESERVADA', 'end') or self.peek('SIMBOLO', '}')):
                stmt = self.parse_statement()
                if stmt: bloque_else["children"].append(stmt)
            nodo["children"].append(bloque_else)

        if self.peek('RESERVADA', 'end'):
            self.consume('RESERVADA', 'end')
            self.consume('SIMBOLO', ';')
        elif self.peek('SIMBOLO', '}'):
            self.consume('SIMBOLO', '}')
            
        return nodo

    def parse_do(self):
        self.consume('RESERVADA', 'do')
        bloque = {"name": "Cuerpo", "children": []}
        
        while self.pos < len(self.tokens) and not self.peek('ID', 'until'):
            stmt = self.parse_statement()
            if stmt: bloque["children"].append(stmt)
            
        self.consume('ID', 'until')
        self.consume('SIMBOLO', '(')
        cond = self.parse_expresion()
        self.consume('SIMBOLO', ')')
        self.consume('SIMBOLO', ';')
        
        return {"name": "Do-Until", "children": [bloque, cond if cond else {"name": "Error: Condición Inválida"}]}

    def parse_while(self):
        self.consume('RESERVADA', 'while')
        self.consume('SIMBOLO', '(')
        cond = self.parse_expresion()
        self.consume('SIMBOLO', ')')
        
        bloque = {"name": "Cuerpo", "children": []}
        if self.peek('SIMBOLO', '{'):
            self.consume('SIMBOLO', '{')
            while self.pos < len(self.tokens) and not self.peek('SIMBOLO', '}'):
                stmt = self.parse_statement()
                if stmt: bloque["children"].append(stmt)
            self.consume('SIMBOLO', '}')
            self.consume('SIMBOLO', ';')
            
        return {"name": "While", "children": [cond if cond else {"name": "Error: Condición Inválida"}, bloque]}

    # --- GENERADOR DE AST DE EXPRESIONES MATEMÁTICAS ---
    # Evalúa precedencia de manera jerárquica
    def parse_expresion(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.pos < len(self.tokens) and self.peek('OPERADOR_LOG', '||'):
            op = self.consume()
            right = self.parse_and()
            left = {"name": f"Op ({op['valor']})", "children": [left or {"name": "Error"}, right or {"name": "Error"}]}
        return left

    def parse_and(self):
        left = self.parse_relacional()
        while self.pos < len(self.tokens) and self.peek('OPERADOR_LOG', '&&'):
            op = self.consume()
            right = self.parse_relacional()
            left = {"name": f"Op ({op['valor']})", "children": [left or {"name": "Error"}, right or {"name": "Error"}]}
        return left

    def parse_relacional(self):
        left = self.parse_aritmetico_1()
        tk = self.peek('OPERADOR_REL')
        if tk:
            op = self.consume()
            right = self.parse_aritmetico_1()
            left = {"name": f"Op ({op['valor']})", "children": [left or {"name": "Error"}, right or {"name": "Error"}]}
        return left

    def parse_aritmetico_1(self):
        left = self.parse_aritmetico_2()
        while self.pos < len(self.tokens) and self.peek('OPERADOR_ARIT') and self.peek('OPERADOR_ARIT')['valor'] in ['+', '-']:
            op = self.consume()
            right = self.parse_aritmetico_2()
            left = {"name": f"Op ({op['valor']})", "children": [left or {"name": "Error"}, right or {"name": "Error"}]}
        return left

    def parse_aritmetico_2(self):
        left = self.parse_factor()
        while self.pos < len(self.tokens) and self.peek('OPERADOR_ARIT') and self.peek('OPERADOR_ARIT')['valor'] in ['*', '/', '%']:
            op = self.consume()
            right = self.parse_factor()
            left = {"name": f"Op ({op['valor']})", "children": [left or {"name": "Error"}, right or {"name": "Error"}]}
        return left

    def parse_factor(self):
        tk = self.peek()
        if not tk: return None
        
        if tk['tipo'] in ['ID', 'NUMERO_ENTERO', 'NUMERO_REAL', 'CADENA']:
            self.consume()
            return {"name": "Valor", "value": tk['valor']}
        elif tk['valor'] == '(':
            self.consume()
            expr = self.parse_expresion()
            if not self.consume('SIMBOLO', ')'):
                self.reportar_error("Se esperaba ')' al cerrar expresión")
            return expr # Retornamos la expresión pura, ¡los paréntesis desaparecen del AST!
        elif tk['valor'] in [';', ')', '}', ']', ',']:
            # Evita loops infinitos si falta un operando (ej: '&& )')
            self.reportar_error(f"Expresión incompleta antes de '{tk['valor']}'")
            return None
        else:
            self.reportar_error(f"Se esperaba un valor o variable, se encontró '{tk['valor']}'")
            self.pos += 1
            return None