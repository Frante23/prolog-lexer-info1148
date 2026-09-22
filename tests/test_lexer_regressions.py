from __future__ import annotations

import unittest

from src.lexer import Lexer


class LexerRegressionCases(unittest.TestCase):
    def setUp(self) -> None:
        self.lexer = Lexer()

    def test_adjacent_operators_keep_longest_match_and_positions(self):
        result = self.lexer.scan(r"X\==Y=..Z//2**3-->a.")
        self.assertEqual(result.errors, [])
        self.assertEqual(
            [(token.lexeme, token.column) for token in result.tokens],
            [("X", 1), (r"\==", 2), ("Y", 5), ("=..", 6), ("Z", 9),
             ("//", 10), ("2", 12), ("**", 13), ("3", 15),
             ("-->", 16), ("a", 19), (".", 20)],
        )

    def test_comment_markers_inside_quotes_remain_literal_content(self):
        result = self.lexer.scan("'% /* */' \"% /* */\" ok")
        self.assertEqual(result.errors, [])
        self.assertEqual(
            [(token.type, token.lexeme) for token in result.tokens],
            [("ATOMO_CITADO", "'% /* */'"), ("CADENA", '"% /* */"'),
             ("ATOMO", "ok")],
        )

    def test_block_comment_stops_at_first_closing_marker(self):
        result = self.lexer.scan("/* outer /* inner */ok*/fin")
        self.assertEqual(result.errors, [])
        self.assertEqual([token.lexeme for token in result.tokens],
                         ["ok", "*", "/", "fin"])

    def test_empty_quoted_literals_are_valid_and_interned(self):
        result = self.lexer.scan("'' \"\" '' \"\"")
        self.assertEqual(result.errors, [])
        self.assertEqual([token.type for token in result.tokens],
                         ["ATOMO_CITADO", "CADENA", "ATOMO_CITADO", "CADENA"])
        self.assertEqual(result.symbols.atoms, {"''": 0})
        self.assertEqual(result.symbols.literals, {("CADENA", '\"\"'): 0})
        self.assertEqual([token.attribute for token in result.tokens], [0, 0, 0, 0])

    def test_incomplete_operator_prefixes_report_exact_locations(self):
        result = self.lexer.scan(": ? \\ ok.")
        self.assertEqual(
            [(error.fragment, error.line, error.column) for error in result.errors],
            [(":", 1, 1), ("?", 1, 3), ("\\", 1, 5)],
        )
        self.assertEqual([token.lexeme for token in result.tokens], ["ok", "."])

    def test_lexically_valid_input_does_not_require_valid_syntax(self):
        result = self.lexer.scan(")][(,;.")
        self.assertEqual(result.errors, [])
        self.assertEqual([token.type for token in result.tokens],
                         ["PARENTESIS_DER", "CORCHETE_DER", "CORCHETE_IZQ",
                          "PARENTESIS_IZQ", "COMA", "OPERADOR_CONTROL", "PUNTO"])

    def test_line_endings_preserve_token_positions(self):
        for newline in ("\n", "\r\n", "\r"):
            with self.subTest(newline=repr(newline)):
                result = self.lexer.scan(f"a.{newline}  X")
                self.assertEqual(result.errors, [])
                self.assertEqual(
                    [(token.lexeme, token.line, token.column) for token in result.tokens],
                    [("a", 1, 1), (".", 1, 2), ("X", 2, 3)],
                )

    def test_line_comments_end_at_every_supported_newline(self):
        for newline in ("\n", "\r\n", "\r"):
            with self.subTest(newline=repr(newline)):
                result = self.lexer.scan(f"% descartado{newline}ok.")
                self.assertEqual(result.errors, [])
                self.assertEqual(
                    [(token.lexeme, token.line, token.column) for token in result.tokens],
                    [("ok", 2, 1), (".", 2, 3)],
                )

    def test_block_comment_with_mixed_newlines(self):
        result = self.lexer.scan("/* a\r\nb\rc\n*/  X")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.tokens[0].as_tuple(), ("VARIABLE", "X", 4, 5, 0))

    def test_tabs_and_other_ascii_separators_count_one_column(self):
        result = self.lexer.scan("\t  a.\f\vX")
        self.assertEqual(result.errors, [])
        self.assertEqual([token.column for token in result.tokens], [4, 5, 8])

    def test_non_ascii_whitespace_is_reported(self):
        result = self.lexer.scan("a\u00a0b\u2003c")
        self.assertEqual([token.lexeme for token in result.tokens], ["a", "b", "c"])
        self.assertEqual(
            [(error.message, error.fragment, error.line, error.column) for error in result.errors],
            [("Caracter no admitido", "\u00a0", 1, 2), ("Caracter no admitido", "\u2003", 1, 4)],
        )

    def test_number_boundaries_use_ascii_classes(self):
        result = self.lexer.scan("12é ３ 7٢")
        self.assertEqual([(token.type, token.lexeme) for token in result.tokens],
                         [("ENTERO", "12"), ("ENTERO", "7")])
        self.assertEqual(
            [(error.message, error.fragment) for error in result.errors],
            [("Caracter no admitido", "é"), ("Caracter no admitido", "３"),
             ("Caracter no admitido", "٢")],
        )

    def test_unicode_is_allowed_in_quoted_literals(self):
        result = self.lexer.scan("'Juan Pérez' \"información\"")
        self.assertEqual(result.errors, [])
        self.assertEqual([token.type for token in result.tokens], ["ATOMO_CITADO", "CADENA"])

    def test_all_documented_escapes_in_both_literal_types(self):
        content = r"a\n\t\r\\\'\"z"
        for quote, token_type in (("'", "ATOMO_CITADO"), ('"', "CADENA")):
            with self.subTest(quote=quote):
                source = quote + content + quote
                result = self.lexer.scan(source)
                self.assertEqual(result.errors, [])
                self.assertEqual([(token.type, token.lexeme) for token in result.tokens],
                                 [(token_type, source)])

    def test_unclosed_literals_preserve_fragment_and_resume_on_next_line(self):
        for quote in ("'", '"'):
            for suffix in ("", "\\"):
                for newline in ("\n", "\r\n", "\r"):
                    with self.subTest(quote=quote, suffix=suffix, newline=repr(newline)):
                        fragment = quote + "abierto" + suffix
                        result = self.lexer.scan(fragment + newline + "ok.")
                        self.assertEqual(len(result.errors), 1)
                        self.assertEqual(result.errors[0].fragment, fragment)
                        self.assertIn("sin cierre", result.errors[0].message)
                        self.assertEqual(
                            [(token.lexeme, token.line, token.column) for token in result.tokens],
                            [("ok", 2, 1), (".", 2, 3)],
                        )

    def test_unclosed_literal_at_eof_includes_trailing_backslash(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                fragment = quote + "abierto\\"
                result = self.lexer.scan(fragment)
                self.assertEqual(result.tokens, [])
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(result.errors[0].fragment, fragment)
                self.assertEqual((result.errors[0].line, result.errors[0].column), (1, 1))

    def test_invalid_escape_discards_literal_and_resumes_at_delimiter(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                fragment = quote + r"a\q" + quote
                result = self.lexer.scan(fragment + ",ok.")
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(result.errors[0].fragment, fragment)
                self.assertIn("escape no admitida", result.errors[0].message)
                self.assertEqual([token.lexeme for token in result.tokens], [",", "ok", "."])
                self.assertEqual(result.tokens[0].column, len(fragment) + 1)
                self.assertEqual(result.symbols.literals, {})

    def test_malformed_number_preserves_clause_dot_and_following_atom(self):
        for fragment in ("12abc", "3.14.15", "1e+", "1.2e-", "2e3e+"):
            with self.subTest(fragment=fragment):
                result = self.lexer.scan(fragment + ".ok.")
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(result.errors[0].fragment, fragment)
                self.assertEqual(result.errors[0].message, "Numero mal formado")
                self.assertEqual([token.lexeme for token in result.tokens], [".", "ok", "."])
                self.assertEqual(result.tokens[0].column, len(fragment) + 1)
                self.assertEqual(result.symbols.literals, {})

    def test_malformed_number_preserves_arithmetic_operator(self):
        for fragment in ("12abc", "3.14.15", "1e+abc"):
            for operator in ("+", "-", "*", "/"):
                with self.subTest(fragment=fragment, operator=operator):
                    result = self.lexer.scan(fragment + operator + "3")
                    self.assertEqual(len(result.errors), 1)
                    self.assertEqual(result.errors[0].fragment, fragment)
                    self.assertEqual([token.lexeme for token in result.tokens], [operator, "3"])

    def test_numeric_dot_is_distinct_from_clause_dot(self):
        result = self.lexer.scan("1.foo(2). 3.14. 2e3.")
        self.assertEqual(result.errors, [])
        self.assertEqual(
            [(token.type, token.lexeme) for token in result.tokens],
            [("ENTERO", "1"), ("PUNTO", "."), ("ATOMO", "foo"),
             ("PARENTESIS_IZQ", "("), ("ENTERO", "2"), ("PARENTESIS_DER", ")"),
             ("PUNTO", "."), ("REAL", "3.14"), ("PUNTO", "."),
             ("REAL", "2e3"), ("PUNTO", ".")],
        )

    def test_comment_priority_over_division_operator(self):
        result = self.lexer.scan("8/* descartar */ /2//1.")
        self.assertEqual(result.errors, [])
        self.assertEqual([token.lexeme for token in result.tokens], ["8", "/", "2", "//", "1", "."])

    def test_unclosed_block_comment_consumes_remainder_with_exact_location(self):
        fragment = "/* comentario\r\ncon tokens aparentes(X)."
        result = self.lexer.scan("a.\r  " + fragment)
        self.assertEqual([token.lexeme for token in result.tokens], ["a", "."])
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].fragment, fragment)
        self.assertEqual((result.errors[0].line, result.errors[0].column), (2, 3))

    def test_anonymous_occurrences_do_not_share_an_interned_variable(self):
        result = self.lexer.scan("_ _ _X __ _X")
        self.assertEqual(result.errors, [])
        self.assertEqual([token.attribute for token in result.tokens], [None, None, 0, 1, 0])
        self.assertEqual(result.symbols.variables, {"_X": 0, "__": 1})

    def test_literal_interning_preserves_type_and_spelling(self):
        result = self.lexer.scan('1 1 01 1.0 1.0 "1" "1"')
        self.assertEqual(result.errors, [])
        self.assertEqual([token.attribute for token in result.tokens], [0, 0, 1, 2, 2, 3, 3])
        self.assertEqual(result.symbols.literals,
                         {("ENTERO", "1"): 0, ("ENTERO", "01"): 1,
                          ("REAL", "1.0"): 2, ("CADENA", '"1"'): 3})

    def test_reusing_lexer_does_not_leak_previous_symbols_or_errors(self):
        previous = self.lexer.scan("a(X,1). @")
        current = self.lexer.scan("b(Y,2).")
        self.assertEqual(current.errors, [])
        self.assertEqual(current.symbols.atoms, {"b": 0})
        self.assertEqual(current.symbols.variables, {"Y": 0})
        self.assertEqual(current.symbols.literals, {("ENTERO", "2"): 0})
        self.assertEqual(previous.symbols.atoms, {"a": 0})
        self.assertEqual(len(previous.errors), 1)


if __name__ == "__main__":
    unittest.main()
