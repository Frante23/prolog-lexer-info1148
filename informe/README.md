# Compilación del informe

El documento usa XeLaTeX y una estructura modular. Desde esta carpeta se compila con:

```bash
latexmk -xelatex main.tex
```

`main.tex` define el formato general. El contenido se encuentra en `secciones/` y las tres figuras de autómatas están en `figuras/`. El archivo `main.pdf` corresponde a la versión compilada del informe técnico.
