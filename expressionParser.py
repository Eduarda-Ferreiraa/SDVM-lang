import re
from functools import reduce
from dataclasses import dataclass
from pprint import pprint
from parsy import *

type Exp = (Val | Ident | Or | And | Equals | NotEquals | LessThan | LessEqual |
            GreaterThan | GreaterEqual | Add | Sub | Mul | Div | Mod |
            UnaryOp | Cast | Index | FuncCall)

@dataclass
class Val: v: int | float | bool | str
@dataclass
class Ident: name: str

@dataclass
class Or: left: Exp; right: Exp
@dataclass
class And: left: Exp; right: Exp
@dataclass
class Equals: left: Exp; right: Exp
@dataclass
class NotEquals: left: Exp; right: Exp
@dataclass
class LessThan: left: Exp; right: Exp
@dataclass
class LessEqual: left: Exp; right: Exp
@dataclass
class GreaterThan: left: Exp; right: Exp
@dataclass
class GreaterEqual: left: Exp; right: Exp
@dataclass
class Add: left: Exp; right: Exp
@dataclass
class Sub: left: Exp; right: Exp
@dataclass
class Mul: left: Exp; right: Exp
@dataclass
class Div: left: Exp; right: Exp
@dataclass
class Mod: left: Exp; right: Exp

@dataclass
class UnaryOp: op: str; expr: Exp
@dataclass
class Cast: target_type: str; expr: Exp
@dataclass
class Index: target: Exp; index: Exp
@dataclass
class FuncCall: name: str; args: list[Exp]



# espaços e comentários (// e /* ... */) são ignorados
whitespace = regex(r"(?:\s|//[^\n]*|/\*.*?\*/)*", flags=re.S)
def lexeme(p):
    return p << whitespace

@generate
def pExp():
    first = yield pLogicalAnd
    rest = yield (lexeme(string('||')) >> pLogicalAnd).many()
    return reduce(lambda acc, right: Or(acc, right), rest, first)

@generate
def pLogicalAnd():
    first = yield pEquality
    rest = yield (lexeme(string('&&')) >> pEquality).many()
    return reduce(lambda acc, right: And(acc, right), rest, first)

@generate
def pEquality():
    first = yield pComparison
    op_parser = lexeme(string('==')) | lexeme(string('!='))
    rest = yield seq(op_parser, pComparison).many()

    result = first
    for op, right in rest:
        if op == '==':
            result = Equals(result, right)
        else:
            result = NotEquals(result, right)
    return result

@generate
def pComparison():
    first = yield pAdditive
    # impor ordem para que < nao roube o lugar a <=
    op_parser = lexeme(string('<=')) | lexeme(string('>=')) | lexeme(string('<')) | lexeme(string('>'))
    rest = yield seq(op_parser, pAdditive).many()

    result = first
    for op, right in rest:
        match op:
            case '<': result = LessThan(result, right)
            case '<=': result = LessEqual(result, right)
            case '>': result = GreaterThan(result, right)
            case '>=': result = GreaterEqual(result, right)
    return result


@generate
def pAdditive():
    first = yield pMultiplicative
    op_parser = lexeme(string('+')) | lexeme(string('-'))
    rest = yield seq(op_parser, pMultiplicative).many()

    result = first
    for op, right in rest:
        result = Add(result, right) if op == '+' else Sub(result, right)
    return result

@generate
def pMultiplicative():
    first = yield pUnary
    op_parser = lexeme(string('*')) | lexeme(string('/')) | lexeme(string('%'))
    rest = yield seq(op_parser, pUnary).many()

    result = first
    for op, right in rest:
        match op:
            case '*': result = Mul(result, right)
            case '/': result = Div(result, right)
            case '%': result = Mod(result, right)
    return result

type_parser = lexeme(regex(r'(int|double|char|bool)\b'))

@generate
def pUnary():
    is_cast = yield peek(lexeme(string('(')) >> type_parser >> lexeme(string(')'))).optional()
    if is_cast:
        yield lexeme(string('('))
        t = yield type_parser
        yield lexeme(string(')'))
        expr = yield pUnary
        return Cast(t, expr)

    op = yield lexeme(string('+') | string('-') | string('!')).optional()
    if op:
        expr = yield pUnary
        return UnaryOp(op, expr)

    return (yield pPostfix)

@generate
def pPostfix():
    ident = yield pIdent.optional()
    if ident is None:
        return (yield pPrimary)
    if (yield lexeme(string("[")).optional()) is not None:
        index_expr = yield pExp
        yield lexeme(string("]"))
        return Index(ident, index_expr)
    if (yield lexeme(string("(")).optional()) is not None:
        args = yield pExp.sep_by(lexeme(string(",")))
        yield lexeme(string(")"))
        return FuncCall(ident.name, args)
    return ident

# palavras reservadas: não podem ser usadas como identificadores
RESERVED_WORDS = {
    "int", "double", "char", "bool", "void",
    "if", "else", "while", "for",
    "break", "continue", "return",
    "print", "read", "true", "false",
}
identifier_pattern = (
    r"(?!(?:" + "|".join(sorted(RESERVED_WORDS)) + r")\b)[A-Za-z][A-Za-z0-9_]*"
)

pTypeBool = lexeme(regex(r'true\b').map(lambda _: True) | regex(r'false\b').map(lambda _: False))
pFloat = lexeme(regex(r'[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?')).map(float)
pInt = lexeme(regex(r'[0-9]+')).map(int)
pChar = lexeme(regex(r"'([^'\\]|\\.)'"))
pString = lexeme(regex(r'"([^"\\]|\\.)*"'))
pIdent = lexeme(regex(identifier_pattern)).map(Ident)


# valores numericos e bool sao do data type Val, mas os identificadores sao do data type Ident, para que possamos distinguir entre valores literais e variáveis.
pPrimary = (
    pTypeBool.map(Val)
    | pFloat.map(Val)
    | pInt.map(Val)
    | pChar.map(Val)
    | pString.map(Val)
    | pIdent
    | lexeme(string('(')) >> pExp << lexeme(string(')'))
)

#pprint(pExp.parse("1+2"))
#pprint(pExp.parse("divisible_by_four && (!divisible_by_hundred || divisible_by_four_hundred)"))
#pprint(pExp.parse("number % 2 == 0"))
#pprint(pExp.parse("number > 12 && total > 20"))
#pprint(pExp.parse("sum + values[i]"))
#pprint(pExp.parse("factorial(n - 1)"))
#pprint(pExp.parse("n * factorial(n - 1)"))
#pprint(pExp.parse("first % second"))


if __name__ == "__main__":
    tests = [
        # --- literais e identificadores
        "42",
        "3.14",
        "2.5e10",
        "'a'",
        '"hello"',
        "true",
        "false",
        "x",
        "true_flag",
 
        # --- precedência
        "1 + 2 * 3",
        "1 * 2 + 3",
        "1 + 2 < 3 + 4",
        "1 < 2 == 3 < 4",
        "a || b && c",
        "a && b || c",
        "a == b && c != d",
 
        # --- associatividade (esquerda)
        "1 - 2 - 3",
        "8 / 4 / 2",
        "a || b || c",
        "1 < 2 < 3",
        "a == b == c",
 
        # --- parênteses
        "(1 + 2) * 3",
        "((x))",
        "a && (b || c)",
 
        # --- unários e casts
        "-x",
        "!!x",
        "- -x",
        "-x * 2",
        "(int) x",
        "(double) a / b",
        "(char) (x + 1)",
        "(x) + 1",
 
        # --- índices e chamadas
        "v[0]",
        "v[i + 1]",
        "f()",
        "f(1)",
        "f(1, x, 2 + 3)",
        "f(g(x))",
        "f(x) + 1",
        "n * factorial(n - 1)",
        "values[f(i)]",
 
        # --- espaços
        "1+2",
        "f( 1 , 2 )",
        "v[ i ]",
        "  1   +   2  ",        # deve falhar: espaços no início
 
        # --- devem falhar com ParseError
        "i = i + 1",
        "1 +",
        "* 2",
        "1 2",
        "f(,)",
        "f(1,)",
        "v[]",
        "(1 + 2",
        "(int)",
        "a ! b",
    ]
 
    for t in tests:
        print(repr(t))
        try:
            pprint(pExp.parse(t))
        except ParseError:
            print("ParseError")
        print()