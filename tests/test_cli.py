"""Pruebas del comando real, sus salidas y los dos archivos de entrega."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "src.cli", *args],
            cwd=ROOT, capture_output=True, encoding="utf-8",
            env={**os.environ, **env}, check=False,
        )

    def run_source(self, source: bytes, *args: str, **env: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "entrada.pl"
            path.write_bytes(source)
            return self.run_cli(str(path), *args, **env)

    def test_valid_corpus_json_and_symbol_references(self):
        run = self.run_cli("corpus/programa_valido.pl", "--json")
        self.assertEqual(run.returncode, 0, run.stderr)
        payload = json.loads(run.stdout)
        self.assertEqual(payload["errores"], [])
        self.assertEqual(len(payload["tokens"]), 94)
        tables = payload["tabla_lexemas"]
        literals = {row["indice"]: (row["tipo"], row["lexema"]) for row in tables["literales"]}
        for token in payload["tokens"]:
            kind, lexeme, index = token["tipo"], token["lexema"], token["atributo"]
            if kind in {"ATOMO", "ATOMO_CITADO"}:
                self.assertEqual(tables["atomos"][lexeme], index)
            elif kind == "VARIABLE":
                self.assertEqual(tables["variables"][lexeme], index)
            elif kind in {"ENTERO", "REAL", "CADENA"}:
                self.assertEqual(literals[index], (kind, lexeme))
            else:
                self.assertIsNone(index)

    def test_invalid_corpus_recovers_and_reports_positions(self):
        run = self.run_cli("corpus/programa_con_errores.pl", "--json")
        self.assertEqual(run.returncode, 1, run.stderr)
        payload = json.loads(run.stdout)
        self.assertEqual(len(payload["tokens"]), 30)
        self.assertEqual(
            [(error["linea"], error["columna"]) for error in payload["errores"]],
            [(3, 6), (4, 9), (5, 7), (7, 9), (8, 8), (9, 1)],
        )
        self.assertIn("recuperado", [token["lexema"] for token in payload["tokens"]])

    def test_text_output_matches_assignment_example(self):
        run = self.run_source(b"% Hechos\npadre(juan, ana).\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.splitlines(), [
            "<ATOMO, 'padre', 2, 1, 0>",
            "<PARENTESIS_IZQ, '(', 2, 6>",
            "<ATOMO, 'juan', 2, 7, 1>",
            "<COMA, ',', 2, 11>",
            "<ATOMO, 'ana', 2, 13, 2>",
            "<PARENTESIS_DER, ')', 2, 16>",
            "<PUNTO, '.', 2, 17>",
        ])

    def test_text_errors_include_location_and_fragment(self):
        run = self.run_source(b"a.\n  @ b.")
        self.assertEqual(run.returncode, 1)
        self.assertIn("2:3: Caracter no admitido: '@'", run.stdout)
        self.assertIn("<ATOMO, 'b', 2, 5, 1>", run.stdout)

    def test_utf8_bom_is_not_a_lexical_error(self):
        run = self.run_source(b"\xef\xbb\xbfpadre.", "--json")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["tokens"][0]["columna"], 1)

    def test_unicode_output_is_utf8_even_with_legacy_pipe_encoding(self):
        source = "'Juan Pérez 😀'.".encode("utf-8")
        for args in ((), ("--json",)):
            with self.subTest(args=args):
                run = self.run_source(source, *args, PYTHONIOENCODING="ascii")
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertIn("Juan Pérez 😀", run.stdout)

    def test_invalid_utf8_has_actionable_error_without_traceback(self):
        run = self.run_source(b"'\xff'.", "--json")
        self.assertEqual(run.returncode, 2)
        self.assertEqual(run.stdout, "")
        self.assertIn("UTF-8", run.stderr)
        self.assertNotIn("Traceback", run.stderr)

    def test_missing_file_returns_usage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self.run_cli(str(Path(directory) / "no_existe.pl"))
        self.assertEqual(run.returncode, 2)
        self.assertIn("No se pudo leer", run.stderr)
        self.assertNotIn("Traceback", run.stderr)

    def test_empty_file_has_empty_result(self):
        run = self.run_source(b"", "--json")
        self.assertEqual(run.returncode, 0, run.stderr)
        payload = json.loads(run.stdout)
        self.assertEqual(payload["tokens"], [])
        self.assertEqual(payload["errores"], [])
        self.assertEqual(payload["tabla_lexemas"], {"atomos": {}, "variables": {}, "literales": []})

    def test_help_returns_success(self):
        run = self.run_cli("--help")
        self.assertEqual(run.returncode, 0)
        self.assertIn("--json", run.stdout)


if __name__ == "__main__":
    unittest.main()
