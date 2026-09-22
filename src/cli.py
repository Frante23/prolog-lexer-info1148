"""Interfaz de linea de comandos del analizador."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lexer import Lexer


def format_token(token) -> str:
    """Representa un token con el formato solicitado en el enunciado."""
    fields = [token.type, repr(token.lexeme), str(token.line), str(token.column)]
    if token.attribute is not None:
        fields.append(str(token.attribute))
    return f"<{', '.join(fields)}>"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analizador lexico del subconjunto Prolog INFO1148")
    parser.add_argument("source", type=Path, help="Archivo fuente .pl")
    parser.add_argument("--json", action="store_true", help="Emite un objeto JSON reproducible")
    args = parser.parse_args()

    try:
        source = args.source.read_text(encoding="utf-8")
    except OSError as exc:
        parser.error(str(exc))

    result = Lexer().scan(source)
    if args.json:
        payload = {
            "tokens": [
                {
                    "tipo": token.type,
                    "lexema": token.lexeme,
                    "linea": token.line,
                    "columna": token.column,
                    "atributo": token.attribute,
                }
                for token in result.tokens
            ],
            "errores": [
                {
                    "mensaje": error.message,
                    "fragmento": error.fragment,
                    "linea": error.line,
                    "columna": error.column,
                }
                for error in result.errors
            ],
            "tabla_lexemas": {
                "atomos": result.symbols.atoms,
                "variables": result.symbols.variables,
                "literales": [
                    {"tipo": kind, "lexema": value, "indice": index}
                    for (kind, value), index in result.symbols.literals.items()
                ],
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for token in result.tokens:
            print(format_token(token))
        if result.errors:
            print("\nERRORES")
            for error in result.errors:
                print(f"{error.line}:{error.column}: {error.message}: {error.fragment!r}")

    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
