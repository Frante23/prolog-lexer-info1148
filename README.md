# Analizador léxico de Prolog INFO1148

Proyecto de la asignatura Teoría de la Computación. Implementa un analizador léxico para el subconjunto de Prolog definido en el informe, con posiciones basadas en 1, tabla de lexemas, máxima coincidencia y recuperación ante errores.

## Integrantes

- Jose Jimenez Saavedra - jose.jimenez2023@alu.uct.cl
- Franco Oyarzo Calisto - foyarzo2023@alu.uct.cl
- Demian Quezada Pasten - dquezada2023@alu.uct.cl

## Requisitos y ejecucion

Se requiere Python 3.10 o posterior. No existen dependencias externas.

```bash
python -m src.cli corpus/programa_valido.pl
python -m src.cli corpus/programa_valido.pl --json
```

El proceso devuelve código `0` cuando no hay errores y código `1` cuando se detecta al menos un error léxico. Los comentarios y espacios no se emiten como tokens, pero sí actualizan línea y columna.

## Pruebas

Desde la raiz del proyecto:

```bash
python -m unittest discover -s tests -v
```

El corpus automatizado contiene 28 pruebas válidas y 12 pruebas inválidas, de posición o de recuperación. Además, `corpus/programa_valido.pl` y `corpus/programa_con_errores.pl` permiten reproducir una ejecución completa.

## Estructura

`src/lexer.py` contiene el modelo de tokens, la tabla de lexemas y el recorrido del analizador. `src/cli.py` implementa la interfaz de línea de comandos. `tests/test_lexer.py` registra los casos automatizados. `corpus/` contiene los dos programas completos requeridos. La carpeta `informe/` reúne el documento técnico y sus fuentes en LaTeX.
