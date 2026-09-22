# Compilación del informe

El archivo principal es `main.tex`. Se puede compilar con **pdfLaTeX**
(predeterminado) o **XeLaTeX**. Ambos usan Latin Modern, incluida en las
distribuciones de TeX, sin depender de fuentes instaladas en Windows.

## Compilación local

Instala MiKTeX o TeX Live con los paquetes usados en `main.tex`. Desde la raíz
del repositorio ejecuta:

```bash
python scripts/validate.py
python scripts/build_report.py
```

El primer comando verifica las pruebas y el corpus y actualiza los resultados
incluidos en el informe. El segundo genera **`informe/build/main.pdf`**, con un
mínimo de dos pasadas para resolver las referencias. También puede ejecutarse
desde otra carpeta usando la ruta completa del script. No requiere `latexmk`
ni Perl; necesita Python 3.10 o posterior y el motor elegido disponible en `PATH`.

Para usar XeLaTeX o una carpeta de salida diferente:

```bash
python scripts/build_report.py --engine xelatex --output-dir informe/build/xelatex
```

Si la compilación falla, el script devuelve un código distinto de cero y muestra
el diagnóstico. El registro completo está en `main.log`, dentro de la carpeta
de salida. Los auxiliares de LaTeX y `informe/build/` se excluyen de Git.

También puedes compilar manualmente desde **esta carpeta**, dos veces:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

En ese caso el resultado reemplaza directamente `informe/main.pdf`, que se
conserva en el repositorio como versión de entrega. Al usar el script, copia el
PDF validado de `build/main.pdf` a `main.pdf` cuando actualices esa entrega.

## Actualizar el PDF incluido en Git

Para evitar que las fuentes y el PDF publicado diverjan, usa:

```bash
python scripts/build_report.py --publish
```

Este comando ejecuta las pruebas y ambos archivos del corpus, actualiza las
cifras, compila y reemplaza `informe/main.pdf` únicamente si todo termina bien.
Con `--publish`, la carpeta de salida no puede ser `informe/`: así un fallo de
compilación conserva el PDF publicado anteriormente. Revisa visualmente el PDF
generado antes de incorporarlo al commit; la compilación no detecta todos los
problemas de presentación.

Como alternativa portable se admite [Tectonic](https://tectonic-typesetting.github.io/),
con su ejecutable disponible en `PATH`:

```bash
python scripts/build_report.py --engine tectonic --publish
```

Tectonic gestiona las pasadas y descarga los paquetes necesarios en su caché;
la primera compilación requiere conexión a Internet. No agrega dependencias al
lexer ni a sus pruebas. El PDF de plataforma debe copiarse con el nombre
`Tarea_JefeGrupo_nombreApellido.pdf`, sustituyendo los datos del jefe real.

## Overleaf

1. Sube el **contenido** de `informe/`, incluyendo `secciones/`, `figuras/` y
   `resultados.tex`, de modo que `main.tex` quede en la raíz del proyecto.
   Es la estructura [recomendada por Overleaf](https://docs.overleaf.com/getting-started/recompiling-your-project/the-main-document).
2. En la configuración del proyecto selecciona `main.tex` como documento
   principal, o `informe/main.tex` si subiste el repositorio completo.
3. Selecciona **pdfLaTeX** o **XeLaTeX** como compilador y recompila.

El archivo principal también busca las secciones y figuras dentro de `informe/`,
por lo que admite compilar desde la raíz del repositorio completo.

La versión anterior cargaba `fontspec` sin comprobar el motor; eso produce un
error fatal con pdfLaTeX. Ahora la configuración tipográfica se adapta al motor.
Si conservas archivos auxiliares de una compilación anterior con otro motor,
usa la opción de recompilar desde cero.

## Estructura

- `main.tex`: formato, tipografía e inclusión de las secciones.
- `secciones/`: contenido del informe.
- `figuras/`: autómatas utilizados en el documento.
- `resultados.tex`: resultados generados por `scripts/validate.py`.
- `main.pdf`: PDF de entrega incluido en Git.
- `build/`: resultados locales de compilación, sin seguimiento en Git.
