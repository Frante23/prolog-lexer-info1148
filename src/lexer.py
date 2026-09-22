"""Analizador lexico recuperable para un subconjunto documentado de Prolog.

El signo de un numero se reconoce como operador independiente. Los comentarios y
el espacio se descartan, pero actualizan linea y columna. La politica general es
maxima coincidencia; si dos reglas empatan, se usa la prioridad de este modulo.
Los identificadores, digitos y espacios se restringen a las clases ASCII
documentadas. LF, CRLF y CR cuentan como un salto; cada tabulacion, una columna.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass(frozen=True)
class Token:
    type: str
    lexeme: str
    line: int
    column: int
    attribute: int | None = None

    def as_tuple(self) -> tuple[Any, ...]:
        base: tuple[Any, ...] = (self.type, self.lexeme, self.line, self.column)
        return base if self.attribute is None else base + (self.attribute,)


@dataclass(frozen=True)
class LexError:
    message: str
    fragment: str
    line: int
    column: int


@dataclass
class SymbolTable:
    atoms: dict[str, int] = field(default_factory=dict)
    variables: dict[str, int] = field(default_factory=dict)
    literals: dict[tuple[str, str], int] = field(default_factory=dict)

    @staticmethod
    def _intern(table: dict[Any, int], value: Any) -> int:
        if value not in table:
            table[value] = len(table)
        return table[value]

    def register(self, token_type: str, lexeme: str) -> int | None:
        if token_type in {"ATOMO", "ATOMO_CITADO"}:
            return self._intern(self.atoms, lexeme)
        if token_type == "VARIABLE":
            return self._intern(self.variables, lexeme)
        if token_type in {"ENTERO", "REAL", "CADENA"}:
            return self._intern(self.literals, (token_type, lexeme))
        return None


@dataclass(frozen=True)
class LexerResult:
    tokens: list[Token]
    errors: list[LexError]
    symbols: SymbolTable


class Lexer:
    """Recorre la fuente una sola vez y produce tokens con posicion 1-based."""

    IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*", re.ASCII)
    REAL = re.compile(
        r"(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)",
        re.ASCII,
    )
    INTEGER = re.compile(r"[0-9]+", re.ASCII)
    DIGITS = "0123456789"
    IDENTIFIER_CHARS = frozenset(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
    )
    WHITESPACE = " \t\r\n\f\v"

    WORD_OPERATORS = {
        "is": "OPERADOR_ARITMETICO",
        "mod": "OPERADOR_ARITMETICO",
    }

    # Orden descendente: hace explicita la prioridad cuando hay prefijos comunes.
    SYMBOL_OPERATORS = (
        ("\\==", "OPERADOR_COMPARACION"),
        ("=..", "OPERADOR_COMPARACION"),
        ("-->", "OPERADOR_CLAUSULA"),
        ("\\=", "OPERADOR_COMPARACION"),
        ("==", "OPERADOR_COMPARACION"),
        ("=<", "OPERADOR_COMPARACION"),
        (">=", "OPERADOR_COMPARACION"),
        ("//", "OPERADOR_ARITMETICO"),
        ("**", "OPERADOR_ARITMETICO"),
        (":-", "OPERADOR_CLAUSULA"),
        ("?-", "OPERADOR_CONSULTA"),
        ("\\+", "OPERADOR_CONTROL"),
        ("=", "OPERADOR_COMPARACION"),
        ("<", "OPERADOR_COMPARACION"),
        (">", "OPERADOR_COMPARACION"),
        ("+", "OPERADOR_ARITMETICO"),
        ("-", "OPERADOR_ARITMETICO"),
        ("*", "OPERADOR_ARITMETICO"),
        ("/", "OPERADOR_ARITMETICO"),
        ("!", "OPERADOR_CONTROL"),
        (";", "OPERADOR_CONTROL"),
    )

    DELIMITERS = {
        "(": "PARENTESIS_IZQ",
        ")": "PARENTESIS_DER",
        "[": "CORCHETE_IZQ",
        "]": "CORCHETE_DER",
        "{": "LLAVE_IZQ",
        "}": "LLAVE_DER",
        "|": "BARRA_VERTICAL",
        ",": "COMA",
        ".": "PUNTO",
    }

    VALID_ESCAPES = {"n", "t", "r", "\\", "'", '"'}

    def scan(self, source: str) -> LexerResult:
        tokens: list[Token] = []
        errors: list[LexError] = []
        symbols = SymbolTable()
        i, line, column = 0, 1, 1
        n = len(source)

        def advance(text: str) -> None:
            nonlocal line, column
            breaks = text.count("\n") + text.count("\r") - text.count("\r\n")
            if breaks:
                line += breaks
                column = len(text) - max(text.rfind("\n"), text.rfind("\r"))
            else:
                column += len(text)

        def emit(token_type: str, lexeme: str, start_line: int, start_col: int) -> None:
            attribute = symbols.register(token_type, lexeme)
            tokens.append(Token(token_type, lexeme, start_line, start_col, attribute))

        while i < n:
            ch = source[i]

            if ch in self.WHITESPACE:
                # Consumir CRLF junto evita contar el mismo salto dos veces.
                end = i + 2 if source.startswith("\r\n", i) else i + 1
                advance(source[i:end])
                i = end
                continue

            start_line, start_col = line, column

            if ch == "%":
                end = i + 1
                while end < n and source[end] not in "\r\n":
                    end += 1
                advance(source[i:end])
                i = end
                continue

            if source.startswith("/*", i):
                end = source.find("*/", i + 2)
                if end == -1:
                    fragment = source[i:]
                    errors.append(
                        LexError("Comentario de bloque sin cierre", fragment, start_line, start_col)
                    )
                    advance(fragment)
                    i = n
                else:
                    fragment = source[i : end + 2]
                    advance(fragment)
                    i = end + 2
                continue

            if ch in {"'", '"'}:
                quote = ch
                j = i + 1
                invalid_escape: str | None = None
                closed = False
                while j < n:
                    current = source[j]
                    if current in "\r\n":
                        break
                    if current == "\\":
                        if j + 1 >= n or source[j + 1] in "\r\n":
                            # La barra pertenece al literal incompleto, no a un
                            # segundo error independiente en la iteracion siguiente.
                            j += 1
                            break
                        if source[j + 1] not in self.VALID_ESCAPES and invalid_escape is None:
                            invalid_escape = source[j : j + 2]
                        j += 2
                        continue
                    if current == quote:
                        j += 1
                        closed = True
                        break
                    j += 1

                fragment = source[i:j]
                if not closed:
                    label = "Atomo citado" if quote == "'" else "Cadena"
                    errors.append(
                        LexError(f"{label} sin cierre", fragment, start_line, start_col)
                    )
                elif invalid_escape is not None:
                    errors.append(
                        LexError(
                            f"Secuencia de escape no admitida: {invalid_escape}",
                            fragment,
                            start_line,
                            start_col,
                        )
                    )
                else:
                    emit("ATOMO_CITADO" if quote == "'" else "CADENA", fragment, start_line, start_col)
                advance(fragment)
                i = j
                continue

            if ch in self.DIGITS:
                real_match = self.REAL.match(source, i)
                int_match = self.INTEGER.match(source, i)
                match = real_match or int_match
                assert match is not None
                end = match.end()

                malformed = False
                if end < n and source[end] in self.IDENTIFIER_CHARS:
                    malformed = True
                if end + 1 < n and source[end] == "." and source[end + 1] in self.DIGITS:
                    malformed = True

                if malformed:
                    while end < n:
                        current = source[end]
                        if current in self.IDENTIFIER_CHARS:
                            end += 1
                        elif current == "." and end + 1 < n and source[end + 1] in self.DIGITS:
                            # Mantener el punto de clausula como limite de recuperacion.
                            end += 1
                        elif current in "+-" and source[end - 1] in "eE":
                            # Solo un marcador de exponente admite un signo propio.
                            end += 1
                        else:
                            break
                    fragment = source[i:end]
                    errors.append(
                        LexError("Numero mal formado", fragment, start_line, start_col)
                    )
                else:
                    fragment = match.group(0)
                    emit("REAL" if real_match else "ENTERO", fragment, start_line, start_col)

                fragment = source[i:end]
                advance(fragment)
                i = end
                continue

            identifier = self.IDENTIFIER.match(source, i)
            if identifier:
                lexeme = identifier.group(0)
                if lexeme == "_":
                    emit("VARIABLE_ANONIMA", lexeme, start_line, start_col)
                elif lexeme[0].isupper() or lexeme[0] == "_":
                    emit("VARIABLE", lexeme, start_line, start_col)
                elif lexeme in self.WORD_OPERATORS:
                    emit(self.WORD_OPERATORS[lexeme], lexeme, start_line, start_col)
                else:
                    emit("ATOMO", lexeme, start_line, start_col)
                advance(lexeme)
                i = identifier.end()
                continue

            operator = next(
                ((lexeme, token_type) for lexeme, token_type in self.SYMBOL_OPERATORS if source.startswith(lexeme, i)),
                None,
            )
            if operator:
                lexeme, token_type = operator
                emit(token_type, lexeme, start_line, start_col)
                advance(lexeme)
                i += len(lexeme)
                continue

            if ch in self.DELIMITERS:
                emit(self.DELIMITERS[ch], ch, start_line, start_col)
                advance(ch)
                i += 1
                continue

            errors.append(LexError("Caracter no admitido", ch, start_line, start_col))
            advance(ch)
            i += 1

        return LexerResult(tokens, errors, symbols)
