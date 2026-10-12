# Proyecto de compiladores

## Ejecutar

Requiere Python 3 y Eel (`python -m pip install -r requirements.txt`).

```text
python main_ide.py
python compilador.py lexico prueba.txt
python compilador.py sintactico prueba.txt
```

La lectura del IDE y del compilador usa UTF-8 (con o sin BOM) y acepta
Windows-1252 como alternativa para archivos antiguos. Los archivos se guardan
en UTF-8. Si un archivo ya contiene caracteres `Â` guardados como texto, debe
recuperarse del original; abrirlo correctamente no deshace esa corrupción.
`prueba.txt` contiene la fuente de la imagen de referencia, sin esos caracteres.

## Base para la fase semántica

Se reconocen `int`, `float`, `bool`, `true`, `false`, `until`, `cin >> x;`,
`cout << expresion;`, condiciones sin paréntesis y bloques `while ... end`.
Se conserva la sintaxis anterior con condiciones entre paréntesis, cuerpos de
while entre llaves, `end;`, `until(...);` y E/S sin operadores de flujo.
Las sentencias simples requieren `;`. Un programa contiene un único `main { ... }`.

La precedencia va de `||`, `&&`, comparación, suma/resta, multiplicación/división/
módulo, unarios a potencia. `^` se interpreta como potencia asociativa a la derecha;
`-2^2` representa `-(2^2)`. Esta convención debe contrastarse con la gramática
original de la asignatura. No se añadió implementación de `switch/case`.

Cada nodo conserva `name`, `value` y `children` para la visualización existente,
además de `clase`, `linea`, `columna`, `lexema` y `tipo_token`. Las declaraciones
incluyen `tipo_declarado`; los operadores incluyen `operador`. Los literales
booleanos se distinguen de los identificadores. Estos campos permiten recorrer
y copiar el AST sin depender de los textos usados para mostrarlo en el IDE.

Los errores léxicos y sintácticos se devuelven en listas separadas y también en
`errores` para compatibilidad. Los comentarios multilínea actualizan las ubicaciones.
Las fases futuras siguen pendientes y se muestran así en la interfaz.

`suma`, `mas` y las asignaciones de reales a enteros se conservan en la prueba:
no son errores sintácticos; deben evaluarse en la fase semántica.

## Validar

```text
python -m unittest -v
node test_frontend.cjs
```

Las pruebas cubren codificaciones y abrir/guardar, el subprocess real desde otra
carpeta, la muestra y sus bloques anidados, precedencia, booleanos, ubicaciones,
errores y recuperación. La prueba JS usa un DOM simulado; no sustituye una
comprobación visual del IDE abierto.
