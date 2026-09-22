"""Compila el informe y permite publicar una versión validada, sin latexmk/Perl."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


REPORT_DIR = Path(__file__).resolve().parents[1] / "informe"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        choices=("pdflatex", "xelatex", "tectonic"),
        default="pdflatex",
        help="motor de LaTeX (predeterminado: pdflatex)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="ejecuta la validación y actualiza informe/main.pdf solo tras compilar sin errores",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPORT_DIR / "build",
        help="carpeta del PDF y los auxiliares (predeterminada: informe/build)",
    )
    args = parser.parse_args()
    engine = shutil.which(args.engine)
    if engine is None:
        print(
            f"No se encontró {args.engine} en PATH. Instala MiKTeX, TeX Live o Tectonic "
            "y vuelve a abrir la terminal.",
            file=sys.stderr,
        )
        return 2

    output_dir = args.output_dir.resolve()
    if args.publish and output_dir == REPORT_DIR.resolve():
        parser.error("--publish requiere una carpeta de salida distinta de informe/")
    if args.publish:
        validation = subprocess.run(
            [sys.executable, str(REPORT_DIR.parent / "scripts" / "validate.py")],
            cwd=REPORT_DIR.parent, check=False,
        )
        if validation.returncode:
            print("No se publica el PDF: la validación falló.", file=sys.stderr)
            return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-output-directory={output_dir}",
        "main.tex",
    ]
    if args.engine == "tectonic":
        # Tectonic gestiona sus propias pasadas y descarga los paquetes necesarios.
        command = [engine, "--keep-logs", "--outdir", str(output_dir), "main.tex"]
    for pass_number in range(1, 5):
        print(f"Compilación {pass_number}: {args.engine}", flush=True)
        result = subprocess.run(
            command,
            cwd=REPORT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode:
            print(result.stdout, end="", file=sys.stderr)
            print(result.stderr, end="", file=sys.stderr)
            print(f"Revisa el registro: {output_dir / 'main.log'}", file=sys.stderr)
            return 1

        log = (output_dir / "main.log").read_text(encoding="utf-8", errors="replace")
        needs_rerun = any(
            warning in log
            for warning in (
                "Rerun to get cross-references right",
                "Label(s) may have changed",
                "Table widths have changed",
                "Rerun to get outlines right",
            )
        )
        if args.engine == "tectonic":
            if needs_rerun:
                print(f"Referencias sin converger. Revisa {output_dir / 'main.log'}", file=sys.stderr)
                return 1
            break
        if pass_number >= 2 and not needs_rerun:
            break
    else:
        print("Las referencias no convergieron tras cuatro pasadas.", file=sys.stderr)
        return 1

    if "There were undefined references" in log or "There were undefined citations" in log:
        print(f"Hay referencias sin resolver. Revisa {output_dir / 'main.log'}", file=sys.stderr)
        return 1
    pdf = output_dir / "main.pdf"
    if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
        print("El motor no produjo un PDF válido; no se publica.", file=sys.stderr)
        return 1
    print(f"PDF generado: {pdf}")
    if args.publish:
        # Sustitución solo tras validar y compilar; un fallo previo conserva la entrega.
        staging = REPORT_DIR / "main.pdf.tmp"
        shutil.copyfile(pdf, staging)
        staging.replace(REPORT_DIR / "main.pdf")
        print(f"PDF publicado: {REPORT_DIR / 'main.pdf'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
