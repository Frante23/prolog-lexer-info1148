"""Ejecuta las pruebas y registra resultados reales para el informe técnico."""

from __future__ import annotations

from collections import Counter
from datetime import date
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def test_ids(suite: unittest.TestSuite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id()


def main() -> int:
    sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    identifiers = list(test_ids(suite))
    groups = Counter(identifier.split(".")[-2] for identifier in identifiers)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    print(output.getvalue(), end="")
    if not result.wasSuccessful() or result.skipped or result.testsRun == 0:
        print("No se actualiza la evidencia: hay pruebas fallidas, omitidas o ausentes.")
        return 1

    corpus_results = {}
    for filename, expected_exit in (("programa_valido.pl", 0), ("programa_con_errores.pl", 1)):
        run = subprocess.run(
            [sys.executable, "-m", "src.cli", f"corpus/{filename}", "--json"],
            cwd=ROOT, capture_output=True, encoding="utf-8", check=False,
        )
        if run.returncode != expected_exit:
            print(f"Resultado inesperado para {filename}: {run.returncode}\n{run.stderr}")
            return 1
        payload = json.loads(run.stdout)
        corpus_results[filename] = {
            "tokens": len(payload["tokens"]),
            "errors": len(payload["errores"]),
            "exit_code": run.returncode,
            "diagnostics": payload["errores"],
        }

    evidence = {
        "date": date.today().isoformat(),
        "python": platform.python_version(),
        "command": "python scripts/validate.py",
        "tests": {"run": result.testsRun, "failures": 0, "errors": 0, "skipped": 0,
                  "groups": dict(sorted(groups.items())), "cases": identifiers},
        "corpus": corpus_results,
    }
    evidence_path = ROOT / "docs" / "validation.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    valid = corpus_results["programa_valido.pl"]
    invalid = corpus_results["programa_con_errores.pl"]
    macros = {
        "PruebasTotal": result.testsRun,
        "PruebasValidasBase": groups.get("LexerValidCases", 0),
        "PruebasInvalidasBase": groups.get("LexerInvalidCases", 0),
        "PruebasCLI": groups.get("CliTests", 0),
        "PruebasRegresion": result.testsRun - groups.get("LexerValidCases", 0)
        - groups.get("LexerInvalidCases", 0) - groups.get("CliTests", 0),
        "PythonValidacion": platform.python_version(),
        "FechaValidacion": date.today().isoformat(),
        "TokensValidos": valid["tokens"],
        "ErroresValidos": valid["errors"],
        "TokensInvalidos": invalid["tokens"],
        "ErroresInvalidos": invalid["errors"],
    }
    (ROOT / "informe" / "resultados.tex").write_text(
        "% Generado por python scripts/validate.py; no editar manualmente.\n"
        + "".join(f"\\newcommand{{\\{name}}}{{{value}}}\n" for name, value in macros.items()),
        encoding="utf-8",
    )
    print(f"Evidencia actualizada: {result.testsRun} pruebas OK; "
          f"corpus valido {valid['tokens']} tokens/{valid['errors']} errores; "
          f"corpus invalido {invalid['tokens']} tokens/{invalid['errors']} errores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
