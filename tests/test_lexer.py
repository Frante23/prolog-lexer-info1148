from __future__ import annotations

import unittest

from src.lexer import Lexer


class LexerValidCases(unittest.TestCase):
    def setUp(self) -> None:
        self.lexer = Lexer()

    def assert_types(self, source: str, expected: list[str]) -> None:
        result = self.lexer.scan(source)
        self.assertEqual(result.errors, [], result.errors)
        self.assertEqual([token.type for token in result.tokens], expected)

    def test_01_unquoted_atom(self):
        self.assert_types("padre", ["ATOMO"])

    def test_02_atom_with_suffix(self):
        self.assert_types("persona_1", ["ATOMO"])

    def test_03_quoted_atom(self):
        self.assert_types("'Juan Perez'", ["ATOMO_CITADO"])

    def test_04_quoted_operator_is_atom(self):
        self.assert_types("':-'", ["ATOMO_CITADO"])

    def test_05_uppercase_variable(self):
        self.assert_types("Persona", ["VARIABLE"])

    def test_06_underscore_variable(self):
        self.assert_types("_Temporal", ["VARIABLE"])

    def test_07_anonymous_variable(self):
        result = self.lexer.scan("_")
        self.assertEqual(result.tokens[0].type, "VARIABLE_ANONIMA")
        self.assertEqual(result.symbols.variables, {})

    def test_08_integer(self):
        self.assert_types("25", ["ENTERO"])

    def test_09_decimal(self):
        self.assert_types("3.14", ["REAL"])

    def test_10_exponent(self):
        self.assert_types("2e-3", ["REAL"])

    def test_11_string(self):
        self.assert_types('"hola mundo"', ["CADENA"])

    def test_12_escaped_string(self):
        self.assert_types(r'"linea\nsegunda"', ["CADENA"])

    def test_13_clause_operator(self):
        self.assert_types(":-", ["OPERADOR_CLAUSULA"])

    def test_14_query_operator(self):
        self.assert_types("?-", ["OPERADOR_CONSULTA"])

    def test_15_dcg_operator(self):
        self.assert_types("-->", ["OPERADOR_CLAUSULA"])

    def test_16_comparison_operators(self):
        source = r"= \= == \== =.. < =< > >="
        self.assert_types(source, ["OPERADOR_COMPARACION"] * 9)

    def test_17_arithmetic_operators(self):
        self.assert_types("+ - * / // ** is mod", ["OPERADOR_ARITMETICO"] * 8)

    def test_18_control_operators(self):
        self.assert_types(r"\+ ! ; ,", ["OPERADOR_CONTROL"] * 3 + ["COMA"])

    def test_19_delimiters(self):
        self.assert_types("()[]{}|.", [
            "PARENTESIS_IZQ", "PARENTESIS_DER", "CORCHETE_IZQ", "CORCHETE_DER",
            "LLAVE_IZQ", "LLAVE_DER", "BARRA_VERTICAL", "PUNTO",
        ])

    def test_20_line_comment_is_ignored(self):
        result = self.lexer.scan("% comentario\npadre")
        self.assertEqual([(t.lexeme, t.line, t.column) for t in result.tokens], [("padre", 2, 1)])

    def test_21_block_comment_is_ignored(self):
        result = self.lexer.scan("/* uno\ndos */X")
        self.assertEqual((result.tokens[0].line, result.tokens[0].column), (2, 7))

    def test_22_longest_comparison(self):
        result = self.lexer.scan(r"\== \=")
        self.assertEqual([t.lexeme for t in result.tokens], [r"\==", r"\="])

    def test_23_longest_univ(self):
        result = self.lexer.scan("=.. =")
        self.assertEqual([t.lexeme for t in result.tokens], ["=..", "="])

    def test_24_keyword_boundary(self):
        result = self.lexer.scan("is island mod modulo")
        self.assertEqual([t.type for t in result.tokens], [
            "OPERADOR_ARITMETICO", "ATOMO", "OPERADOR_ARITMETICO", "ATOMO"
        ])

    def test_25_sign_is_operator(self):
        self.assert_types("-25 +3.0", ["OPERADOR_ARITMETICO", "ENTERO", "OPERADOR_ARITMETICO", "REAL"])

    def test_26_clause_dot_after_integer(self):
        self.assert_types("edad(ana,12).", ["ATOMO", "PARENTESIS_IZQ", "ATOMO", "COMA", "ENTERO", "PARENTESIS_DER", "PUNTO"])

    def test_27_symbol_deduplication(self):
        result = self.lexer.scan("padre(X). padre(X).")
        self.assertEqual(result.symbols.atoms, {"padre": 0})
        self.assertEqual(result.symbols.variables, {"X": 0})

    def test_28_complete_program(self):
        source = "padre(juan, ana).\nabuelo(X,Z) :- padre(X,Y), padre(Y,Z)."
        result = self.lexer.scan(source)
        self.assertFalse(result.errors)
        self.assertEqual(result.tokens[-1].type, "PUNTO")


class LexerInvalidCases(unittest.TestCase):
    def setUp(self) -> None:
        self.lexer = Lexer()

    def assert_error(self, source: str, message: str) -> None:
        result = self.lexer.scan(source)
        self.assertTrue(any(message in error.message for error in result.errors), result.errors)

    def test_29_unclosed_quoted_atom(self):
        self.assert_error("'juan", "sin cierre")

    def test_30_unclosed_string(self):
        self.assert_error('"hola', "sin cierre")

    def test_31_unclosed_block_comment(self):
        self.assert_error("/* comentario", "Comentario de bloque sin cierre")

    def test_32_invalid_character(self):
        self.assert_error("padre@ana", "Caracter no admitido")

    def test_33_number_letter_suffix(self):
        self.assert_error("12abc", "Numero mal formado")

    def test_34_incomplete_exponent(self):
        self.assert_error("2e", "Numero mal formado")

    def test_35_multiple_decimal_points(self):
        self.assert_error("3.14.15", "Numero mal formado")

    def test_36_invalid_escape(self):
        self.assert_error(r'"hola\q"', "escape no admitida")

    def test_37_recovery_after_invalid_character(self):
        result = self.lexer.scan("a @ b.")
        self.assertEqual([t.lexeme for t in result.tokens], ["a", "b", "."])
        self.assertEqual(len(result.errors), 1)

    def test_38_error_position(self):
        result = self.lexer.scan("a.\n  @")
        self.assertEqual((result.errors[0].line, result.errors[0].column), (2, 3))

    def test_39_incomplete_signed_exponent_fragment(self):
        result = self.lexer.scan("1e+")
        self.assertEqual(result.errors[0].fragment, "1e+")
        self.assertEqual(result.tokens, [])

    def test_40_recovery_after_malformed_number(self):
        result = self.lexer.scan("12abc, ok.")
        self.assertEqual([token.lexeme for token in result.tokens], [",", "ok", "."])
        self.assertEqual(len(result.errors), 1)


if __name__ == "__main__":
    unittest.main()
