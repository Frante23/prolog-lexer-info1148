# Analizador léxico de Prolog · INFO1148

Proyecto de Teoría de la Computación para el subconjunto definido en la tarea del
segundo semestre de 2026. Produce tokens con tipo, lexema, línea y columna,
registra lexemas sin repeticiones y detecta errores procurando continuar el análisis.

Repositorio: <https://github.com/Frante23/prolog-lexer-info1148>.
Informe técnico: [informe/main.pdf](informe/main.pdf).

## Integrantes

- Jose Jimenez Saavedra — jose.jimenez2023@alu.uct.cl
- Franco Oyarzo Calisto — foyarzo2023@alu.uct.cl
- Demian Quezada Pasten — dquezada2023@alu.uct.cl

## Ejecución

El lexer y las pruebas requieren **Python 3.10 o posterior**, sin dependencias
externas. Ejecuta estos comandos desde la raíz del repositorio:

```bash
python -m src.cli corpus/programa_valido.pl
python -m src.cli corpus/programa_valido.pl --json
python -m src.cli corpus/programa_con_errores.pl --json
```

El tercer comando termina con código `1`: contiene errores intencionales.

| Código de salida | Significado |
| --- | --- |
| `0` | Análisis terminado sin errores léxicos. |
| `1` | Análisis terminado con uno o más errores léxicos. |
| `2` | Argumentos incorrectos, archivo ilegible o codificación UTF-8 inválida. |

Los archivos se leen en UTF-8, con BOM inicial opcional. Las salidas de texto y
JSON también usan UTF-8, incluso al redirigirlas. Ejemplo de token:

```text
<ATOMO, 'padre', 2, 1, 0>
```

El quinto campo es el índice de la tabla de lexemas; aparece cuando corresponde.
El modo `--json` incluye `tokens`, `errores` y `tabla_lexemas`, con tablas separadas
de átomos, variables y literales. Los índices comienzan en cero dentro de cada
tabla y se reutilizan para la misma escritura y categoría.

## Subconjunto y decisiones léxicas

- Identificadores ASCII: átomos `[a-z][A-Za-z0-9_]*`, variables
  `[A-Z_][A-Za-z0-9_]*` y `_` como anónima sin índice.
- Átomos con comillas simples y cadenas con comillas dobles, con Unicode dentro
  de las comillas. Escapes: `\n`, `\t`, `\r`, `\\`, `\'` y `\"`.
  No se permiten CR o LF dentro de un literal.
- Enteros y reales decimales, incluidos `3.14`, `2e-3` y `1.5E+2`. Los signos
  iniciales se emiten como operadores: `-25` genera `-` y `25`.
- Operadores de cláusula `:-` y `-->`, consulta `?-`, comparación
  `= \= == \== =.. < =< > >=`, aritmética `+ - * / // ** is mod` y control `\+ ! ;`.
- Delimitadores `( ) [ ] { } | , .`; comentarios `%` hasta fin de línea y
  `/* ... */` hasta el primer cierre, sin anidamiento.
- Espacios ASCII ` `, `\t`, `\r`, `\n`, `\f` y `\v`. LF, CRLF y CR cuentan
  como un salto. Las posiciones parten de uno; una tabulación ocupa una columna lógica.

Se aplica máxima coincidencia: `\==` se reconoce completo e `island` es un átomo.
Las escrituras originales se conservan sin interpretar sus valores. Ante un número
mal formado, el punto que no precede a un dígito queda como delimitador:
`12abc.ok.` produce un error por `12abc` y permite reconocer `.`, `ok`, `.`.
Un literal abierto se recupera en la línea siguiente; un comentario de bloque sin
cierre consume hasta EOF. No se comprueba sintaxis, precedencia, ámbitos ni unificación.

## Pruebas y evidencia

```bash
python -m unittest discover -s tests -v
python scripts/validate.py
```

Última validación: **75 pruebas aprobadas**. Se conservan 28 válidas y 12 de errores,
posición o recuperación del corpus original, y se añaden 25 regresiones y 10 de
la CLI. Los casos parametrizados se ejecutan como subpruebas dentro de esos métodos.

| Archivo completo | Tokens | Errores | Salida |
| --- | ---: | ---: | ---: |
| `corpus/programa_valido.pl` | 94 | 0 | 0 |
| `corpus/programa_con_errores.pl` | 30 | 6 | 1 |

`scripts/validate.py` ejecuta las pruebas y ambos archivos; solo si la validación
termina correctamente actualiza [docs/validation.json](docs/validation.json) y las
cifras del informe mediante `informe/resultados.tex`.

La evidencia incluye las huellas SHA-256 del código, las pruebas, el corpus y el
validador ejecutados. Se normaliza CRLF a LF antes de calcularlas para comparar
checkouts de Windows y Linux. Si esos archivos cambian durante la ejecución, no
se publica evidencia. Las huellas identifican el contenido probado; no certifican
la autoría ni reemplazan el historial Git.

## Informe y autómatas

La compilación requiere una distribución LaTeX con **pdfLaTeX o XeLaTeX**:

```bash
python scripts/validate.py
python scripts/build_report.py
```

El PDF nuevo se genera en `informe/build/main.pdf`. La versión revisada incluida
en Git es `informe/main.pdf`. Consulta la [guía local y Overleaf](informe/README.md).

Para regenerar las figuras se necesita adicionalmente Matplotlib:

```bash
python -m pip install matplotlib
python docs/generate_diagrams.py
```

El generador actualiza `docs/figures/` y las copias de `informe/figuras/`.
Matplotlib es una dependencia exclusiva de las ilustraciones.

Para entregar en la plataforma usa el nombre solicitado por el enunciado:
`Tarea_JefeGrupo_nombreApellido.pdf`, reemplazando nombre y apellido por los del
jefe de grupo. El historial se consulta con `git log --format="%h | %an | %s"`;
la autoría individual se documenta según los commits existentes.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `src/lexer.py` | Tokens, errores, tabla de lexemas y recorrido. |
| `src/cli.py` | Lectura de archivos y salidas textual/JSON. |
| `tests/` | Pruebas del lexer, regresiones, CLI y corpus. |
| `corpus/` | Archivos completos válido e inválido. |
| `docs/` | Generador, figuras, evidencia y [revisión de requisitos](docs/REVISION.md). |
| `scripts/` | Validación y compilación reproducibles. |
| `informe/` | Fuentes LaTeX, figuras y PDF técnico. |
