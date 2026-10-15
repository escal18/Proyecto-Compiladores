# Fase 3: análisis semántico

## Funcionamiento

Al elegir **Sem** o **Compilar > Análisis Semántico**, el IDE procesa la fuente
actual mediante lexer, parser y analizador semántico. Si hay errores léxicos o
sintácticos, muestra esos errores en sus paneles y no procesa un AST incompleto.
Si no los hay, conserva el AST original y anota una copia profunda.

En **Sintáctico** se muestra el AST original; en **Semántico**, el árbol anotado
y una traza desplegable de inserciones, búsquedas, ámbitos, conversiones,
anotaciones, constantes y errores. **Hash Table** muestra la tabla realmente
utilizada por el analizador, y **Err. Semánticos** contiene línea, columna y
descripción. La fuente puede ser sintácticamente correcta y tener errores
semánticos.

## Reglas y atributos

| Construcción | Regla implementada |
| --- | --- |
| Declaración | Hereda el atributo `dtype` a cada identificador; inserta nombre y tipo en el ámbito actual. |
| Identificador | Consulta los ámbitos desde el más interno al más externo; recupera tipo, símbolo y desplazamiento. |
| Literales | Sintetizan `tipo`, `constante=true` y `valor_constante`. |
| `+ - * /` | Operandos numéricos; resultado float si algún operando es float; de lo contrario int. |
| División entera | Trunca hacia cero; por ejemplo `-7/3 = -2`. |
| `%` | Solo int; el resto conserva el signo del dividendo: `-7%3 = -1`. |
| `^` | Potencia numérica asociativa a la derecha; resultado int con operandos int y exponente conocido no negativo; float con operandos float o exponente negativo/desconocido. |
| `< <= > >=` | Operandos numéricos; resultado bool. |
| `== !=` | Dos operandos numéricos o dos bool; resultado bool. |
| `&& || !` | Operandos bool; resultado bool. |
| Unarios `+ -` y postfijos `++ --` | Operandos int o float. |
| Asignación e inicialización | Tipos iguales, o promoción int a float. |
| `if`, `while`, `until` | Condición de tipo bool. |
| `cin` | Destino declarado; no se calcula su valor durante compilación. |
| `cout` | Expresión válida de tipo int, float o bool. |

`tipo` se sintetiza desde los operandos y el contexto de cada sentencia.
`tipo_esperado` expresa que una condición debe ser bool. `valido` se propaga
hacia los nodos padres y marca construcciones que contienen errores.
`constante` y `valor_constante` indican un valor conocido en ese punto del
programa. Se propagan desde literales y variables conocidas hasta la raíz de
la expresión y la asignación; también se guardan en la tabla para las sentencias
siguientes. Las anotaciones previas conservan su valor histórico. Los nodos
Programa, main y bloque conservan tipo void: no representan una expresión.

Una entrada cin o una asignación inválida deja el destino sin valor conocido.
En if se analizan ambas ramas para detectar errores, pero solo se conserva el
estado de la rama seleccionada si la condición es conocida; de lo contrario,
se conservan únicamente valores coincidentes entre ambas rutas. Los ciclos
invalidan conservadoramente las variables que escriben antes y después de
analizar el cuerpo; no se simulan iteraciones ni se atribuye un resultado final.

## Conversiones

La única conversión implícita es int a float, en expresiones numéricas mixtas,
comparaciones numéricas y asignaciones a variables float. El nodo conserva su
tipo original, y añade `conversion={de: int, a: float}` y
`tipo_efectivo=float`. El valor conocido se convierte realmente a float y la
interfaz muestra el tipo efectivo y un decimal (por ejemplo, 2.0). La promoción
de una lectura no cambia el tipo declarado ni el valor almacenado de su variable.

Se rechazan float a int y conversiones entre bool y los tipos numéricos.
El usuario confirmó mantener estas reglas y que no se requiere switch/case.
El enunciado exige documentarlas; no proporciona una matriz completa de
conversiones ni tamaños de memoria.

## Tabla de símbolos y ámbitos

Se usa una pila de diccionarios para inserción y búsqueda. Cada bloque crea un
ámbito: main, bloques explícitos, ramas then/else y cuerpos de ciclos. Cada nombre
solo puede declararse una vez en todo el programa, según la regla de la materia.
Un registro global de nombres rechaza duplicados incluso en bloques internos,
ramas alternativas y bloques que ya terminaron. Este registro se reinicia en cada
análisis. Al salir de un bloque, sus símbolos dejan de ser visibles; su registro
se conserva para detectar duplicados, presentar la tabla y exportar evidencias.

La condición de until se analiza dentro del ámbito del cuerpo de do. Las
condiciones de if y while se analizan en el ámbito exterior a su cuerpo.
Los identificadores deben estar declarados antes de su uso.

Cada símbolo registra ID, nombre, tipo, ámbito, ubicación de declaración, líneas
de aparición, usos con línea/columna y rol, valor conocido, desplazamiento y tamaño en bytes.
La columna «Último valor conocido» muestra el valor actual si puede deducirse;
si deja de conocerse, conserva el último calculado en una operación válida del
recorrido semántico. Este historial es solo informativo: no se reutiliza para
calcular expresiones ni representa necesariamente un valor de ejecución.
Una operación errónea no reemplaza ese historial. Si nunca hubo un valor
calculable se muestra «—». Los errores se consultan en su panel; disponer de un
historial no significa por sí solo que haya ocurrido un error.
La lista de líneas conserva una entrada por aparición textual, incluyendo la
declaración y los usos: `y = y + 1;` en la línea 9 registra `9, 9`.
Un incremento `y++;` registra una aparición, con rol de lectura y escritura;
los recorridos auxiliares para analizar ciclos no añaden apariciones adicionales.
Los duplicados conservan el símbolo original y registran su aparición; el diagnóstico
indica la ubicación del duplicado y la línea de la declaración original.
Se asignan desplazamientos lógicos monotónicos, alineados al tamaño del tipo:
int 4 bytes, float 8 bytes y bool 1 byte. No se reserva memoria real.
No se reutilizan los desplazamientos de ámbitos finalizados.

## Errores y recuperación

- `NO_DECLARADO`: identificador no visible o no declarado.
- `DUPLICADO`: nombre declarado más de una vez en cualquier parte del programa.
- `CONVERSION_INVALIDA`: asignación o inicialización incompatible.
- `OPERADOR_INVALIDO`: tipos no admitidos por el operador.
- `CONDICION_NO_BOOLEANA`: condición que no es bool.
- `DIVISION_CERO`: divisor o módulo conocido e igual a cero.
- `CONSTANTE_INVALIDA`: resultado constante no real o fuera de rango.

Un error de expresión se propaga mediante el tipo `error`, evitando repetir
diagnósticos derivados del mismo problema. Se visitan los demás operandos y
sentencias para detectar otros errores. No se añaden identificadores no
declarados a la tabla como si fueran declaraciones válidas.

## Prueba principal y evidencias

Se conserva `prueba.txt`, procedente de la referencia del proyecto.
Produce seis símbolos: x, y, z, a, b y c; con desplazamientos 0, 4, 8, 16, 24 y 32.
Se detectan seis errores:

| Línea | Error |
| --- | --- |
| 4 | suma no declarada |
| 5 | asignación float a x de tipo int |
| 14 | asignación float a y de tipo int |
| 16 | asignación de a + 3 (float) a y (int) |
| 33 | mas no declarada |
| 37 | mas no declarada en cin |

Las pruebas automatizadas complementan este archivo sin reemplazarlo.
Para ejecutar todas las pruebas y exportar las evidencias:

```text
python -m unittest -v
node test_frontend.cjs
python compilador.py semantico prueba.txt --exportar evidencias_fase3
```

El último comando crea AST original y anotado, tabla de símbolos, errores y
traza en JSON, un reporte de errores en texto, la fuente analizada y el resultado
completo. También se puede utilizar **Exportar fase 3** en el IDE: recalcula la
semántica de la fuente actual y permite elegir una carpeta de destino.
Si existen errores previos, la exportación del IDE se bloquea; la de terminal
indica que la semántica no se ejecutó.

El paquete entrega_fase3 contiene datos exportados, capturas del IDE real y
el reporte técnico PDF. El archivo de integrantes requiere los nombres y
matrículas proporcionados por el equipo.

## Correcciones de la revisión del 14 de octubre de 2026

- El punto y coma ausente se ubica al final de la sentencia que lo necesita.
- La CLI entrega la fuente al parser para ubicar correctamente fin de archivo,
  incluso después de comentarios o líneas vacías.
- El editor conserva saltos de línea de texto, desactiva ajuste de línea y usa
  métricas idénticas en el textarea y su capa de resaltado. Las columnas empiezan en 1.
- Validación: unittest, pruebas JavaScript y comprobación visual del editor con
  líneas vacías, comentarios, escritura y desplazamiento vertical.
