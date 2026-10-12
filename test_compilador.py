import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from archivos_fuente import leer_fuente
import lexer
from parser_sintactico import Parser

BASE = Path(__file__).resolve().parent


def analizar(codigo):
    tokens, lexicos = lexer.analizar(codigo)
    ast, sintacticos = Parser(tokens).parse()
    return ast, lexicos, sintacticos


def recorrer(nodo):
    yield nodo
    for hijo in nodo.get('children', []):
        yield from recorrer(hijo)


class CompiladorTests(unittest.TestCase):
    def test_archivo_de_la_imagen_y_anidacion(self):
        texto = leer_fuente(BASE / 'prueba.txt')
        self.assertNotIn('Â', texto)
        ast, lexicos, sintacticos = analizar(texto)
        self.assertEqual(lexicos + sintacticos, [])
        nodos = list(recorrer(ast))
        self.assertEqual(sum(n['clase'] == 'if' for n in nodos), 2)
        self.assertEqual(sum(n['clase'] == 'while' for n in nodos), 2)
        do = next(n for n in nodos if n['clase'] == 'do_until')
        self.assertTrue(any(n['clase'] == 'while' for n in recorrer(do['children'][0])))
        self.assertTrue(all(isinstance(n['linea'], int) and isinstance(n['columna'], int) for n in nodos))
        literal = next(n for n in nodos if n.get('value') == 'true')
        self.assertEqual(literal['tipo_token'], 'BOOLEANO')
        self.assertEqual(literal['clase'], 'literal')

    def test_lectura_utf8_bom_y_windows1252(self):
        texto = '// análisis\nmain {\n    cout\u00a0<<\u00a0x;\n}\n'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'prueba.txt'
            for encoding in ('utf-8', 'utf-8-sig', 'cp1252'):
                with self.subTest(encoding=encoding):
                    p.write_bytes(texto.replace('\n', '\r\n').encode(encoding))
                    self.assertEqual(leer_fuente(p), texto)
                    self.assertEqual(analizar(leer_fuente(p))[1:], ([], []))

    def test_comentarios_y_columnas(self):
        tokens, errores = lexer.analizar('/* uno\r\ndos */\r\n  x=1;')
        self.assertEqual(errores, [])
        self.assertEqual((tokens[0]['linea'], tokens[0]['columna']), (3, 3))
        tokens, errores = lexer.analizar('/* uno\ndos */ x;')
        self.assertEqual((tokens[0]['linea'], tokens[0]['columna']), (2, 8))

    def test_comentario_sin_cierre(self):
        _, errores = lexer.analizar('main { /* sin cierre\n')
        self.assertIn('sin cierre', errores[0]['desc'])

    def test_bool_unarios_y_potencia(self):
        ast, lexicos, sintacticos = analizar('main { bool ok; ok = !false; int x; x = -2^3^2; }')
        self.assertEqual(lexicos + sintacticos, [])
        expr = ast['children'][0]['children'][0]['children'][-1]['children'][1]
        self.assertEqual(expr['operador'], '-')
        potencia = expr['children'][0]
        self.assertEqual(potencia['operador'], '^')
        self.assertEqual(potencia['children'][1]['operador'], '^')

    def test_precedencia_aritmetica_y_logica(self):
        ast, lexicos, sintacticos = analizar('main { x=2+3*4; if x>2 && true || false then x=1; end }')
        self.assertEqual(lexicos + sintacticos, [])
        sentencias = ast['children'][0]['children'][0]['children']
        expr = sentencias[0]['children'][1]
        self.assertEqual(expr['operador'], '+')
        self.assertEqual(expr['children'][1]['operador'], '*')
        cond = sentencias[1]['children'][0]
        self.assertEqual(cond['operador'], '||')
        self.assertEqual(cond['children'][0]['operador'], '&&')

    def test_sintaxis_anterior(self):
        codigo = 'main { int x; if(x>0)then x=1; else x=2; end; do while(x>0){cin x; cout x-1;}; until(x==0); }'
        self.assertEqual(analizar(codigo)[1:], ([], []))

    def test_delimitadores_y_operandos_faltantes(self):
        casos = [
            '', 'main { int x;', 'main { x++;', 'main { x=(2+3; }',
            'main { if true x=1; end }', 'main { if true then x=1; }',
            'main { while true x=1; }', 'main { do x=1; }',
            'main { x=2+; y=3; }', 'main { if true && then x=1; end }',
            'main { cin >> 1; }', 'main { cin << x; }', 'main { cout >> x; }',
            'main {} x=1;', 'main {} main {}',
        ]
        for codigo in casos:
            with self.subTest(codigo=codigo):
                self.assertTrue(analizar(codigo)[2])

    def test_recuperacion_preserva_sentencia_siguiente(self):
        ast, _, errores = analizar('main { x=2+; y=3; }')
        self.assertTrue(errores)
        asignaciones = [n for n in recorrer(ast) if n['clase'] == 'asignacion']
        self.assertEqual([n['children'][0]['value'] for n in asignaciones], ['x', 'y'])

    def test_operadores_separados_no_se_unen(self):
        tokens, _ = lexer.analizar('x +\n +')
        self.assertEqual([t['valor'] for t in tokens], ['x', '+', '+'])

    def test_cli_conserva_errores_lexicos_y_separa_fases(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'prueba.txt'
            p.write_text('main { @ int x; }', encoding='utf-8')
            proc = subprocess.run([sys.executable, str(BASE / 'compilador.py'), 'sintactico', str(p)],
                                  capture_output=True, text=True, encoding='utf-8', check=True)
            respuesta = json.loads(proc.stdout)
            self.assertEqual(len(respuesta['errores_lexicos']), 1)
            self.assertEqual(respuesta['errores_sintacticos'], [])
            self.assertEqual(respuesta['errores'], respuesta['errores_lexicos'])

    def test_ide_abre_guarda_y_compila_desde_otro_directorio(self):
        # Sustituye únicamente el adaptador UI; se ejercitan E/S y el subprocess reales.
        import types
        fake_eel = types.SimpleNamespace(init=lambda _: None, expose=lambda f: f)
        with patch.dict(sys.modules, {'eel': fake_eel}):
            import main_ide
        texto = '// análisis\nmain { cout\u00a0<<\u00a0x; }'
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'fuente.txt'
            self.assertEqual(main_ide.guardar_archivo_py(texto, str(p)), str(p))
            with patch.object(main_ide, 'seleccionar_ruta', return_value=str(p)):
                self.assertEqual(main_ide.abrir_archivo_py()['contenido'], texto)
            import os
            anterior = os.getcwd()
            try:
                os.chdir(d)
                res = main_ide.ejecutar_fase_compilador('sintactico', texto)
            finally:
                os.chdir(anterior)
            self.assertEqual(res['errores'], [])
            self.assertFalse((Path(d) / 'temp_fuente.txt').exists())


if __name__ == '__main__':
    unittest.main()
