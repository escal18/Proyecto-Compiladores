"""Análisis estático del AST: tipos, ámbitos y expresiones constantes."""
from copy import deepcopy
import math


NUMERICOS = {'int', 'float'}
TAMANOS = {'int': 4, 'float': 8, 'bool': 1}


class AnalizadorSemantico:
    def analizar(self, ast):
        self.errores = []
        self.ambitos = []
        self.simbolos = []
        self.traza = []
        self.desplazamiento = 0
        self.secuencia = 0
        anotado = deepcopy(ast)
        self.visitar(anotado)
        return {
            'arbol_anotado': anotado,
            'tabla_simbolos': self.simbolos,
            'errores_semanticos': self.errores,
            'traza_semantica': self.traza,
        }

    def evento(self, accion, nodo, **datos):
        self.traza.append({'accion': accion, 'linea': nodo['linea'],
                           'columna': nodo['columna'], **datos})

    def error(self, nodo, codigo, desc):
        self.errores.append({'fase': 'semantico', 'codigo': codigo,
                            'linea': nodo['linea'], 'columna': nodo['columna'], 'desc': desc})
        nodo['tipo'] = 'error'
        nodo['valido'] = False
        self.evento('error', nodo, codigo=codigo, descripcion=desc)

    def entrar(self, nombre, nodo):
        self.secuencia += 1
        padre = self.ambitos[-1]['nombre'] if self.ambitos else ''
        nombre = f"{padre}/{nombre}#{self.secuencia}" if padre else nombre
        self.ambitos.append({'nombre': nombre, 'simbolos': {}})
        nodo['ambito'] = nombre
        self.evento('entrar_ambito', nodo, ambito=nombre)

    def registrar_uso(self, simbolo, nodo, rol):
        if nodo['linea'] not in simbolo['lineas']:
            simbolo['lineas'].append(nodo['linea'])
            simbolo['lineas'].sort()
        simbolo['usos'].append({'linea': nodo['linea'], 'columna': nodo['columna'], 'rol': rol})
        nodo.update(tipo=simbolo['tipo'], simbolo_id=simbolo['id'],
                    ambito=simbolo['ambito'], direccion=simbolo['direccion'])

    def buscar(self, nodo, rol='lectura'):
        nombre = nodo['value']
        for ambito in reversed(self.ambitos):
            if nombre in ambito['simbolos']:
                simbolo = ambito['simbolos'][nombre]
                self.registrar_uso(simbolo, nodo, rol)
                self.evento('buscar', nodo, nombre=nombre, encontrado=True, simbolo_id=simbolo['id'])
                return simbolo
        self.evento('buscar', nodo, nombre=nombre, encontrado=False)
        self.error(nodo, 'NO_DECLARADO', f"Identificador '{nombre}' no declarado en este ámbito.")
        return None

    def declarar(self, nodo, tipo):
        nodo['dtype'] = tipo  # Atributo heredado desde la declaración.
        self.evento('heredar', nodo, atributo='dtype', valor=tipo)
        ambito = self.ambitos[-1]
        nombre = nodo['value']
        if nombre in ambito['simbolos']:
            self.error(nodo, 'DUPLICADO', f"Declaración duplicada de '{nombre}' en {ambito['nombre']}.")
            return None
        tamano = TAMANOS[tipo]
        self.desplazamiento = (self.desplazamiento + tamano - 1) // tamano * tamano
        simbolo = {
            'id': len(self.simbolos) + 1, 'nombre': nombre, 'tipo': tipo,
            'ambito': ambito['nombre'], 'linea_declaracion': nodo['linea'],
            'columna_declaracion': nodo['columna'], 'lineas': [], 'usos': [],
            'direccion': self.desplazamiento, 'tamano': tamano,
        }
        self.desplazamiento += tamano
        ambito['simbolos'][nombre] = simbolo
        self.simbolos.append(simbolo)
        self.registrar_uso(simbolo, nodo, 'declaracion')
        self.evento('insertar', nodo, nombre=nombre, tipo=tipo, direccion=simbolo['direccion'])
        return simbolo

    def convertir(self, nodo, destino):
        origen = nodo['tipo']
        if origen == destino:
            return True
        if origen == 'int' and destino == 'float':
            nodo['conversion'] = {'de': origen, 'a': destino}
            nodo['tipo_efectivo'] = destino
            self.evento('convertir', nodo, origen=origen, destino=destino)
            return True
        return False

    def comprobar_asignacion(self, destino, expresion, nodo):
        tipo_destino, tipo_expr = destino.get('tipo'), expresion.get('tipo')
        if 'error' in (tipo_destino, tipo_expr):
            nodo['tipo'] = 'error'
        elif not self.convertir(expresion, tipo_destino):
            self.error(nodo, 'CONVERSION_INVALIDA',
                       f"No se puede asignar {tipo_expr} a '{destino['value']}' de tipo {tipo_destino}.")
        else:
            nodo['tipo'] = tipo_destino
            self.evento('asignar', nodo, destino=destino['value'], tipo=tipo_destino)

    def condicion(self, nodo):
        self.visitar(nodo)
        nodo['tipo_esperado'] = 'bool'
        if nodo['tipo'] not in ('bool', 'error'):
            self.error(nodo, 'CONDICION_NO_BOOLEANA',
                       f"La condición requiere bool; se obtuvo {nodo['tipo']}.")

    def visitar_bloque(self, nodo, nombre=None):
        nodo['constante'] = False
        self.entrar(nombre or nodo['name'].lower(), nodo)
        for hijo in nodo.get('children', []):
            self.visitar(hijo)
        self.evento('salir_ambito', nodo, ambito=self.ambitos[-1]['nombre'])
        self.ambitos.pop()
        nodo['tipo'] = 'void'
        nodo['valido'] = all(h.get('valido', True) for h in nodo.get('children', []))

    def visitar(self, nodo):
        inicio = len(self.errores)
        nodo['constante'] = False
        nodo['valido'] = True
        clase = nodo['clase']
        hijos = nodo.get('children', [])
        if clase == 'programa':
            for hijo in hijos:
                self.visitar(hijo)
            nodo['tipo'] = 'void'
        elif clase == 'main':
            self.visitar_bloque(hijos[0], 'main')
            nodo['tipo'] = 'void'
        elif clase == 'bloque':
            self.visitar_bloque(nodo)
        elif clase == 'declaracion':
            tipo = nodo['tipo_declarado']
            nodo.update(dtype=tipo, tipo='void')
            for var in hijos:
                var.update(constante=False, valido=True)
                simbolo = self.declarar(var, tipo)
                for expr in var.get('children', []):
                    self.visitar(expr)
                    if simbolo:
                        self.comprobar_asignacion(var, expr, var)
                var['valido'] = var.get('tipo') != 'error' and all(
                    expr.get('valido', True) for expr in var.get('children', []))
        elif clase == 'identificador':
            self.buscar(nodo)
        elif clase == 'literal':
            tipo = {'NUMERO_ENTERO': 'int', 'NUMERO_REAL': 'float', 'BOOLEANO': 'bool'}[nodo['tipo_token']]
            valor = (nodo['value'] == 'true') if tipo == 'bool' else (
                int(nodo['value']) if tipo == 'int' else float(nodo['value']))
            nodo.update(tipo=tipo, constante=True, valor_constante=valor)
            if tipo == 'float' and not math.isfinite(valor):
                self.error(nodo, 'CONSTANTE_INVALIDA', 'Constante flotante fuera de rango.')
                nodo.pop('valor_constante', None)
                nodo['constante'] = False
        elif clase == 'asignacion':
            self.visitar(hijos[0])
            if hijos[0].get('simbolo_id'):
                self.simbolos[hijos[0]['simbolo_id'] - 1]['usos'][-1]['rol'] = 'escritura'
            self.visitar(hijos[1])
            self.comprobar_asignacion(hijos[0], hijos[1], nodo)
        elif clase == 'postfijo':
            self.visitar(hijos[0])
            if hijos[0].get('simbolo_id'):
                self.simbolos[hijos[0]['simbolo_id'] - 1]['usos'][-1]['rol'] = 'lectura_escritura'
            nodo['tipo'] = hijos[0]['tipo']
            if nodo['tipo'] not in NUMERICOS | {'error'}:
                self.error(nodo, 'OPERADOR_INVALIDO',
                           f"El operador {nodo['operador']} requiere int o float.")
        elif clase == 'cin':
            simbolo = self.buscar(hijos[0], 'entrada')
            hijos[0]['constante'] = False
            hijos[0]['valido'] = simbolo is not None
            nodo['tipo'] = 'void' if simbolo else 'error'
        elif clase == 'cout':
            self.visitar(hijos[0])
            nodo['tipo'] = 'void' if hijos[0]['tipo'] != 'error' else 'error'
        elif clase in ('if', 'while'):
            self.condicion(hijos[0])
            for cuerpo in hijos[1:]:
                self.visitar(cuerpo)
            nodo['tipo'] = 'void'
        elif clase == 'do_until':
            # La condición pertenece al mismo ámbito que el cuerpo del do.
            cuerpo, cond = hijos
            cuerpo.update(constante=False, tipo='void')
            self.entrar('do', cuerpo)
            for hijo in cuerpo['children']:
                self.visitar(hijo)
            self.condicion(cond)
            cuerpo['valido'] = all(h.get('valido', True) for h in cuerpo['children'])
            self.evento('salir_ambito', cuerpo, ambito=self.ambitos[-1]['nombre'])
            self.ambitos.pop()
            nodo['tipo'] = 'void'
        elif clase in ('binario', 'unario'):
            for hijo in hijos:
                self.visitar(hijo)
            self.operacion(nodo)
        else:
            self.error(nodo, 'AST_INVALIDO', f"Nodo no válido para análisis semántico: {clase}.")
        nodo['valido'] = (nodo.get('valido', True) and len(self.errores) == inicio
                          and nodo.get('tipo') != 'error'
                          and all(h.get('valido', True) for h in hijos))
        self.evento('anotar', nodo, clase=clase, tipo=nodo.get('tipo'), valido=nodo['valido'])
        return nodo.get('tipo', 'error')

    def operacion(self, nodo):
        op, hijos = nodo['operador'], nodo['children']
        tipos = [h['tipo'] for h in hijos]
        if 'error' in tipos:
            nodo['tipo'] = 'error'
            return
        numericos = all(t in NUMERICOS for t in tipos)
        if nodo['clase'] == 'unario':
            valido = tipos[0] == 'bool' if op == '!' else numericos
            resultado = 'bool' if op == '!' else tipos[0]
        elif op in ('&&', '||'):
            valido, resultado = tipos == ['bool', 'bool'], 'bool'
        elif op in ('==', '!='):
            valido, resultado = numericos or tipos == ['bool', 'bool'], 'bool'
        elif op in ('<', '<=', '>', '>='):
            valido, resultado = numericos, 'bool'
        elif op == '%':
            valido, resultado = tipos == ['int', 'int'], 'int'
        else:
            valido = numericos
            resultado = 'float' if 'float' in tipos or op == '^' else 'int'
        if not valido:
            self.error(nodo, 'OPERADOR_INVALIDO',
                       f"Operador '{op}' incompatible con los tipos {' y '.join(tipos)}.")
            return
        nodo['tipo'] = resultado
        # Comparaciones numéricas también aplican promoción aunque produzcan bool.
        if numericos and ('float' in tipos or op == '^'):
            for hijo in hijos:
                self.convertir(hijo, 'float')
        if op in ('/', '%') and hijos[1].get('constante') and hijos[1]['valor_constante'] == 0:
            self.error(nodo, 'DIVISION_CERO', 'División o módulo por cero en una expresión constante.')
            return
        if all(h.get('constante', False) for h in hijos):
            valores = [h['valor_constante'] for h in hijos]
            if numericos and ('float' in tipos or op == '^'):
                try:
                    valores = [float(v) for v in valores]
                except OverflowError:
                    self.error(nodo, 'CONSTANTE_INVALIDA', 'Conversión constante fuera de rango.')
                    return
            try:
                valor = self.evaluar(op, valores, resultado)
                if isinstance(valor, complex) or (isinstance(valor, float) and not math.isfinite(valor)):
                    raise ValueError('resultado no real o fuera de rango')
                nodo.update(constante=True, valor_constante=valor)
                self.evento('evaluar_constante', nodo, valor=valor, tipo=resultado)
            except (ArithmeticError, ValueError) as error:
                self.error(nodo, 'CONSTANTE_INVALIDA', f"Expresión constante no válida: {error}.")

    @staticmethod
    def evaluar(op, valores, tipo):
        a = valores[0]
        if len(valores) == 1:
            return not a if op == '!' else (+a if op == '+' else -a)
        b = valores[1]
        if op == '+': return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '^': return a ** b
        if op in ('/', '%'):
            if tipo == 'float': return a / b
            cociente = (abs(a) // abs(b)) * (-1 if (a < 0) != (b < 0) else 1)
            return cociente if op == '/' else a - cociente * b
        if op == '<': return a < b
        if op == '<=': return a <= b
        if op == '>': return a > b
        if op == '>=': return a >= b
        if op == '==': return a == b
        if op == '!=': return a != b
        if op == '&&': return a and b
        if op == '||': return a or b
        raise ValueError(f"Operador desconocido: {op}")


def analizar(ast):
    return AnalizadorSemantico().analizar(ast)
