from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import analizador_semantico
from archivos_fuente import leer_fuente
from test_compilador import analizar, recorrer

BASE = Path(__file__).resolve().parent


def semantica(codigo):
    ast, lexicos, sintacticos = analizar(codigo)
    if lexicos or sintacticos:
        raise AssertionError(lexicos + sintacticos)
    return analizador_semantico.analizar(ast)


class SemanticoTests(unittest.TestCase):
    def test_muestra_six_errores_y_tabla_real(self):
        res = semantica(leer_fuente(BASE / 'prueba.txt'))
        self.assertEqual([s['nombre'] for s in res['tabla_simbolos']], list('xyzabc'))
        self.assertEqual([s['direccion'] for s in res['tabla_simbolos']], [0, 4, 8, 16, 24, 32])
        errores = res['errores_semanticos']
        self.assertEqual([(e['codigo'], e['linea']) for e in errores], [
            ('NO_DECLARADO', 4), ('CONVERSION_INVALIDA', 5), ('CONVERSION_INVALIDA', 14),
            ('CONVERSION_INVALIDA', 16), ('NO_DECLARADO', 33), ('NO_DECLARADO', 37)])
        self.assertFalse(res['arbol_anotado']['valido'])
        self.assertIn(32, res['tabla_simbolos'][0]['lineas'])

    def test_original_inmutable_y_analizador_reutilizable(self):
        ast, _, _ = analizar('main { int x; x=2+3; }')
        antes = deepcopy(ast)
        analizador = analizador_semantico.AnalizadorSemantico()
        res = analizador.analizar(ast)
        self.assertEqual(ast, antes)
        self.assertNotIn('tipo', ast)
        self.assertIsNot(res['arbol_anotado'], ast)
        self.assertEqual(analizador.analizar(ast), res)
        self.assertTrue(res['arbol_anotado']['valido'])

    def test_atributos_heredados_y_sintetizados(self):
        res = semantica('main { float a,b; a=2+3.5; }')
        nodos = list(recorrer(res['arbol_anotado']))
        variables = [n for n in nodos if n['name'] == 'Variable']
        self.assertEqual([n['dtype'] for n in variables], ['float', 'float'])
        op = next(n for n in nodos if n.get('operador') == '+')
        self.assertEqual(op['tipo'], 'float')
        self.assertEqual(op['valor_constante'], 5.5)
        self.assertEqual(op['children'][0]['conversion'], {'de': 'int', 'a': 'float'})
        self.assertTrue(any(t['accion'] == 'convertir' for t in res['traza_semantica']))

    def test_asignacion_int_float_promueve_sin_cambiar_tipo_original(self):
        res = semantica('main { float a; a=2; }')
        self.assertEqual(res['errores_semanticos'], [])
        literal = next(n for n in recorrer(res['arbol_anotado']) if n['clase'] == 'literal')
        self.assertEqual(literal['tipo'], 'int')
        self.assertEqual(literal['tipo_efectivo'], 'float')

    def test_variables_y_entrada_no_reciben_valor_inventado(self):
        res = semantica('main { int x,y; x=2; cin >> x; y=x+1; }')
        self.assertEqual(res['errores_semanticos'], [])
        nodos = list(recorrer(res['arbol_anotado']))
        for n in nodos:
            if n['clase'] == 'identificador' and n['name'] != 'Destino':
                self.assertFalse(n['constante'])
                self.assertNotIn('valor_constante', n)
        expr = next(n for n in nodos if n.get('operador') == '+')
        self.assertFalse(expr['constante'])
        self.assertEqual([u['rol'] for u in res['tabla_simbolos'][0]['usos']],
                         ['declaracion', 'escritura', 'entrada', 'lectura'])

    def test_duplicados_no_reemplazan_simbolo_y_continua(self):
        res = semantica('main { int x; float x; x=1; y=2; z=3; }')
        self.assertEqual([e['codigo'] for e in res['errores_semanticos']],
                         ['DUPLICADO', 'NO_DECLARADO', 'NO_DECLARADO'])
        self.assertEqual(len(res['tabla_simbolos']), 1)
        self.assertEqual(res['tabla_simbolos'][0]['tipo'], 'int')

    def test_duplicados_globales_y_salida_de_bloque(self):
        res = semantica('main { int x; if true then float x; x=1.5; int local; end x=1; local=2; }')
        self.assertEqual([e['codigo'] for e in res['errores_semanticos']],
                         ['DUPLICADO', 'CONVERSION_INVALIDA', 'NO_DECLARADO'])
        x = [s for s in res['tabla_simbolos'] if s['nombre'] == 'x']
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]['tipo'], 'int')
        self.assertEqual(x[0]['valor_constante'], 1)

    def test_nombre_unico_incluso_en_bloques_separados(self):
        casos = [
            'int x; { float x; }',
            '{ int x; } { float x; }',
            '{ int x; } float x;',
            'if true then int x; else float x; end',
            'while false int x; end do float x; until true',
        ]
        for codigo in casos:
            with self.subTest(codigo=codigo):
                res = semantica('main {\n' + codigo.replace('float', '\nfloat') + '\n}')
                self.assertEqual([e['codigo'] for e in res['errores_semanticos']], ['DUPLICADO'])
                self.assertEqual(res['errores_semanticos'][0]['linea'], 3)
                self.assertIn('línea 2', res['errores_semanticos'][0]['desc'])
                self.assertEqual(len(res['tabla_simbolos']), 1)
                self.assertEqual(res['tabla_simbolos'][0]['tipo'], 'int')

    def test_inicializador_duplicado_no_modifica_original(self):
        res = semantica('main { int x=2; { float x=9.5; } int y=x; }')
        self.assertEqual([e['codigo'] for e in res['errores_semanticos']], ['DUPLICADO'])
        self.assertEqual([s['valor_constante'] for s in res['tabla_simbolos']], [2, 2])

    def test_valores_suben_a_asignacion_y_se_reutilizan(self):
        res = semantica('main { int x=2,y; x=x+3; y=x*2; y++; float z; z=y; }')
        self.assertEqual(res['errores_semanticos'], [])
        self.assertEqual([s['valor_constante'] for s in res['tabla_simbolos']], [5, 11, 11.0])
        asignaciones = [n for n in recorrer(res['arbol_anotado']) if n['clase'] == 'asignacion']
        self.assertEqual([n['valor_constante'] for n in asignaciones], [5, 10, 11.0])
        self.assertIsInstance(asignaciones[-1]['valor_constante'], float)
        self.assertEqual(asignaciones[0]['children'][1]['children'][0]['valor_constante'], 2)

    def test_potencia_entera_y_promocion_local(self):
        res = semantica('main { int x; x=2^3; float y; y=x+0.5; }')
        self.assertEqual(res['errores_semanticos'], [])
        self.assertEqual(res['tabla_simbolos'][0]['valor_constante'], 8)
        potencia = next(n for n in recorrer(res['arbol_anotado']) if n.get('operador') == '^')
        self.assertEqual(potencia['tipo'], 'int')
        self.assertTrue(all('conversion' not in h for h in potencia['children']))
        self.assertEqual(res['tabla_simbolos'][0]['tipo'], 'int')

    def test_flujo_no_inventa_valores_entre_ramas_y_ciclos(self):
        casos = [
            ('bool b; cin >> b; int x=1; if b then x=2; else x=3; end', None),
            ('bool b; cin >> b; int x=1; if b then x=2; else x=2; end', 2),
            ('int x=1; if false then x=9; end', 1),
            ('int x=1; if true then x=9; else x=3; end', 9),
            ('int x=1; while x<3 x=x+1; end', None),
            ('int x=1; do x=x+1; until x>3', None),
            ('int x=1; x=true;', None),
        ]
        for fuente, esperado in casos:
            with self.subTest(fuente=fuente):
                res = semantica('main { ' + fuente + ' }')
                x = next(s for s in res['tabla_simbolos'] if s['nombre'] == 'x')
                self.assertEqual(x.get('valor_constante'), esperado)

    def test_duplicado_en_lista_conserva_linea_y_simbolo(self):
        res = semantica('main {\n int x,\n x;\n x=4;\n}')
        self.assertEqual([(e['codigo'], e['linea']) for e in res['errores_semanticos']], [('DUPLICADO', 3)])
        self.assertEqual(len(res['tabla_simbolos']), 1)
        self.assertEqual(res['tabla_simbolos'][0]['valor_constante'], 4)

    def test_punto_y_coma_faltante_se_ubica_en_sentencia_anterior(self):
        for salto in ('\n', '\r\n', '\r'):
            _, lexicos, errores = analizar(salto.join(['main {', 'int x', 'x=2', 'cout << x;', '}']))
            self.assertEqual(lexicos, [])
            self.assertEqual([e['linea'] for e in errores], [2, 3])
            self.assertEqual([e['columna'] for e in errores], [6, 4])

    def test_error_fin_archivo_incluye_comentarios_y_lineas_vacias(self):
        import lexer
        from parser_sintactico import Parser
        fuente = 'main {\n int x;\n // falta cierre\n\n'
        tokens, _ = lexer.analizar(fuente)
        _, errores = Parser(tokens, fuente).parse()
        self.assertEqual([(e['linea'], e['columna']) for e in errores], [(5, 1)])

    def test_do_condicion_comparte_ambito(self):
        res = semantica('main { do int x; x=1; until x==1 x=2; }')
        self.assertEqual(len(res['errores_semanticos']), 1)
        self.assertEqual(res['errores_semanticos'][0]['codigo'], 'NO_DECLARADO')
        self.assertEqual(res['tabla_simbolos'][0]['usos'][-1]['rol'], 'lectura')

    def test_errores_tipos_operadores_condiciones(self):
        casos = {
            'bool b; b=1;': 'CONVERSION_INVALIDA',
            'int x; x=true;': 'CONVERSION_INVALIDA',
            'float a; a=true+1;': 'OPERADOR_INVALIDO',
            'bool b; b=1 && true;': 'OPERADOR_INVALIDO',
            'bool b; b=true<false;': 'OPERADOR_INVALIDO',
            'bool b; b=true==1;': 'OPERADOR_INVALIDO',
            'float a; a=1.5%2;': 'OPERADOR_INVALIDO',
            'bool b; b++;': 'OPERADOR_INVALIDO',
            'bool b; b=-true;': 'OPERADOR_INVALIDO',
            'if 1 then end': 'CONDICION_NO_BOOLEANA',
            'while 1 end': 'CONDICION_NO_BOOLEANA',
            'do until 1': 'CONDICION_NO_BOOLEANA',
        }
        for codigo, error in casos.items():
            with self.subTest(codigo=codigo):
                res = semantica('main { ' + codigo + ' }')
                self.assertEqual([e['codigo'] for e in res['errores_semanticos']], [error])

    def test_no_cascadas_por_identificadores_desconocidos(self):
        res = semantica('main { int x; x=noExiste+otro; if tercero then x=2; end }')
        self.assertEqual([e['codigo'] for e in res['errores_semanticos']], ['NO_DECLARADO'] * 3)

    def test_constantes_booleanas_division_modulo_y_potencia(self):
        res = semantica('main { bool b; b=!false && (2<3); int x; x=-7/3; x=-7%3; float a; a=2^-1; }')
        self.assertEqual(res['errores_semanticos'], [])
        ops = [n for n in recorrer(res['arbol_anotado']) if n['clase'] == 'binario']
        self.assertEqual(next(n for n in ops if n['operador'] == '&&')['valor_constante'], True)
        self.assertEqual(next(n for n in ops if n['operador'] == '/')['valor_constante'], -2)
        self.assertEqual(next(n for n in ops if n['operador'] == '%')['valor_constante'], -1)
        self.assertEqual(next(n for n in ops if n['operador'] == '^')['valor_constante'], 0.5)

    def test_cero_y_resultados_fuera_de_rango(self):
        for expr, codigo in [('1/0', 'DIVISION_CERO'), ('2%(3-3)', 'DIVISION_CERO'),
                             ('(-1)^0.5', 'CONSTANTE_INVALIDA'), ('10^1000', 'CONSTANTE_INVALIDA')]:
            with self.subTest(expr=expr):
                res = semantica('main { float a; a=' + expr + '; }')
                self.assertEqual([e['codigo'] for e in res['errores_semanticos']], [codigo])
                self.assertNotIn('NaN', json.dumps(res, allow_nan=False))

    def test_cli_exporta_y_bloquea_ast_con_errores_previos(self):
        with tempfile.TemporaryDirectory() as d:
            fuente = Path(d) / 'fuente.txt'
            destino = Path(d) / 'evidencias'
            for texto, ejecutado in [('main { int x; x=2; }', True),
                                     ('main { @ int x; }', False),
                                     ('main { int x;', False)]:
                fuente.write_text(texto, encoding='utf-8')
                proc = subprocess.run([sys.executable, str(BASE / 'compilador.py'), 'semantico',
                                       str(fuente), '--exportar', str(destino)], capture_output=True,
                                      text=True, encoding='utf-8', check=True)
                res = json.loads(proc.stdout)
                self.assertEqual(res['semantico_ejecutado'], ejecutado)
                self.assertEqual(res['errores_semanticos'], [])
                self.assertEqual(len(list(destino.iterdir())), 8)
                self.assertEqual((destino / 'fuente.txt').read_text(encoding='utf-8'), texto)
                self.assertEqual(json.loads((destino / 'ast_anotado.json').read_text(encoding='utf-8')),
                                 res['arbol_anotado'])
                if not ejecutado:
                    self.assertTrue(res['errores'])
                    self.assertIn('no ejecutado', (destino / 'errores_semanticos.txt').read_text(encoding='utf-8'))

    def test_exportacion_desde_ide_recalcula_y_registra_fuente(self):
        import main_ide
        codigo = 'main { int x; x=1; desconocida=2; }'
        with tempfile.TemporaryDirectory() as d:
            with patch.object(main_ide, 'Tk'), patch.object(main_ide.filedialog, 'askdirectory', return_value=d):
                resultado = main_ide.exportar_semantico_py(codigo)
            self.assertEqual(resultado['ruta'], d)
            self.assertEqual(resultado['errores_semanticos'], 1)
            self.assertEqual((Path(d) / 'fuente.txt').read_text(encoding='utf-8'), codigo)
            reporte = json.loads((Path(d) / 'resultado_semantico.json').read_text(encoding='utf-8'))
            self.assertEqual(reporte['errores_semanticos'][0]['codigo'], 'NO_DECLARADO')
        with patch.object(main_ide, 'Tk') as ventana:
            self.assertIn('error', main_ide.exportar_semantico_py('main { @ }'))
            ventana.assert_not_called()
        with patch.object(main_ide, 'Tk'), patch.object(main_ide.filedialog, 'askdirectory', return_value=''):
            self.assertIsNone(main_ide.exportar_semantico_py('main {}'))


if __name__ == '__main__':
    unittest.main()
