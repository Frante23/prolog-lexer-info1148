# Revisión frente al enunciado INFO1148

Referencia: **Tarea INFO1148 sem2_2026.pdf**, enunciado del 7 de septiembre de 2026.
La revisión abarcó código, pruebas, corpus, generador y copias de figuras, las
nueve secciones LaTeX, PDF, instrucciones e historial Git. El alcance es léxico.

| Requisito | Implementación o evidencia |
| --- | --- |
| Categorías, patrones, ejemplos y atributos | `informe/secciones/03_especificacion.tex`; constantes y reconocedores de `src/lexer.py`. |
| AFN/AFD y estrategia integrada | Sección 04; figuras de identificadores, números y operadores; estados para citas y comentarios. |
| Determinización y minimización justificadas | Tablas del AFN, AFD determinizado, particiones, estados distinguibles y AFD mínimo en la sección 04. |
| Tipo, lexema, línea y columna | `Token`, CLI textual/JSON y prueba del ejemplo del enunciado. |
| Tabla de lexemas | `SymbolTable`, índices por tabla, pruebas de repetición y referencias en JSON. |
| Errores con ubicación y fragmento | `LexError`, pruebas de cierres, caracteres, escapes y números; corpus inválido. |
| Al menos 20 pruebas válidas y 8 inválidas | 28 válidas y 12 de errores/posición/recuperación originales; 25 regresiones adicionales. |
| Máxima coincidencia y prioridad | Operadores largos, palabras completas y comentarios antes de división, comprobados en tests. |
| Dos archivos completos | Los dos `.pl` de `corpus/`, ejecutados en pruebas CLI y validación. |
| Informe PDF e instrucciones | `informe/main.pdf`, `informe/README.md` y `scripts/build_report.py`. |
| Enlace e historial | Anexo con URL real y commits existentes; historial Git conservado. |

## Correcciones verificadas

- CR aislado no incrementaba la línea y podía hacer que un comentario `%`
  consumiera todo el archivo. LF, CRLF y CR ahora funcionan en tokens y comentarios.
- Un literal que terminaba en barra invertida generaba un segundo error; algunos
  números inválidos absorbían puntos de cláusula y texto posterior. Ahora se
  conservan los límites para continuar el análisis.
- Las comprobaciones Unicode admitían separadores fuera de las clases ASCII
  documentadas. Código e informe usan las mismas clases; Unicode sigue permitido
  dentro de las citas.
- La CLI acepta BOM UTF-8, escribe UTF-8 al redirigir y comunica fallos de lectura
  o codificación con código 2 sin trazas internas.
- La formalización precisa tipos de delimitadores, estados de citas/comentarios,
  determinización, minimalidad y relación entre AFD y recuperación.
- `fontspec` fallaba con pdfLaTeX y XeLaTeX no encontraba DejaVu. El preámbulo
  selecciona Latin Modern según el motor. El script resuelve las referencias.
- Las cifras y versión de Python se generan con una ejecución real. El anexo
  utiliza el enlace y el historial existentes del repositorio.

## Validación reproducible

```bash
python scripts/validate.py
python scripts/build_report.py
python scripts/build_report.py --engine xelatex --output-dir informe/build/xelatex
```

Resultado: 75 pruebas aprobadas; corpus válido con 94 tokens/0 errores e inválido
con 30 tokens/6 errores. Detalle: [validation.json](validation.json).

La portada conserva los integrantes originales y registra a Jose Jimenez como
jefe de grupo, según su confirmación. La copia para entrega se llama
`informe/Tarea_JefeGrupo_JoseJimenez.pdf`.
Los commits registran el autor configurado en Git; no acreditan por sí solos
tareas individuales de integrantes con otra identidad.

## Revisión de entrega

- Se agregaron seis regresiones sobre operadores adyacentes, citas vacías,
  comentarios dentro de citas, primer cierre de bloque, prefijos incompletos
  y separación entre análisis léxico y sintáctico.
- La evidencia identifica mediante SHA-256 los archivos efectivamente probados.
- El informe explica seis trazas de aceptación contrastadas con el lexer.
- La publicación ejecuta validación antes de sustituir el PDF; se comprobó que
  fallos de pruebas o compilación conservan el archivo anterior.
- El PDF se regenera desde las fuentes actuales, con enlace real al repositorio,
  cifras actualizadas y commits verificables de Pamtom21 en el anexo.
- Compartir el enlace con el profesor, subir el archivo a Educa y demostrar
  comprensión individual son acciones externas que el repositorio no acredita.
