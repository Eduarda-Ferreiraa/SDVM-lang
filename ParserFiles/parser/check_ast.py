"""Verifica a FORMA da AST (o check_parser só verifica se o parse é aceite).

Para cada caso compara o resultado do parser com a AST esperada, e no fim
percorre todas as ASTs e verifica que cada campo tem o tipo declarado na
dataclass (ex.: Index.target tem de ser str, não Ident).

    python check_ast.py
"""
import dataclasses
import sys
import typing

from .parser import program, Program
from .expressionParser import (
    pExp, Ident, IntLit, FloatLit, BoolLit, CharLit, StringLit, Or, And, Equals,
    NotEquals, LessThan, LessEqual, GreaterThan, GreaterEqual, Add, Sub, Mul, Div,
    Mod, UnaryOp, Cast, Index, FuncCall,
)
from .declarations import VariableDeclaration, ArrayDeclaration, Parameter, FunctionDefinition
from .statements import (
    Break, Continue, Return, Print, Read, Assignment, ArrayAssignment, FunctionCallStatement,
)
from .control_flow import Block, IfStatement, WhileStatement, ForStatement

# o 1.º campo do Index chama-se target ou name, conforme a versão
IDX = dataclasses.fields(Index)[0].name


def idx(nome, i):
    return Index(**{IDX: nome, "index": i})


x, y, a = Ident("x"), Ident("y"), "a"

EXPRESSOES = [
    # literais: um tipo por literal
    ("42", IntLit(42)),
    ("2.5", FloatLit(2.5)),
    ("1.5e3", FloatLit(1500.0)),
    ("true", BoolLit(True)),
    ("false", BoolLit(False)),
    ("'a'", CharLit("'a'")),
    ('"ola"', StringLit('"ola"')),
    # o 0 e o false NÃO podem ser o mesmo literal
    ("0 == false", Equals(IntLit(0), BoolLit(False))),
    # precedência e associatividade
    ("x + y * 2", Add(x, Mul(y, IntLit(2)))),
    ("x - y - 1", Sub(Sub(x, y), IntLit(1))),
    ("(x - y) / 2 % 3", Mod(Div(Sub(x, y), IntLit(2)), IntLit(3))),
    ("x < y == true", Equals(LessThan(x, y), BoolLit(True))),
    ("x <= 1 && y >= 2 || !x", Or(And(LessEqual(x, IntLit(1)), GreaterEqual(y, IntLit(2))), UnaryOp("!", x))),
    ("x != y && x > y", And(NotEquals(x, y), GreaterThan(x, y))),
    # unários e casts
    ("-x", UnaryOp("-", x)),
    ("!!x", UnaryOp("!", UnaryOp("!", x))),
    ("-(-x)", UnaryOp("-", UnaryOp("-", x))),
    ("(double)x / 2", Div(Cast("double", x), IntLit(2))),
    ("(int)(double)x", Cast("int", Cast("double", x))),
    ("(x)", x),
    # arrays e chamadas: o nome é str
    ("a[0]", idx(a, IntLit(0))),
    ("a[x + 1]", idx(a, Add(x, IntLit(1)))),
    ("a[a[0]]", idx(a, idx(a, IntLit(0)))),
    ("f()", FuncCall("f", [])),
    ("f(x, a[1], 2.0)", FuncCall("f", [x, idx(a, IntLit(1)), FloatLit(2.0)])),
    ("-a[1] * f(x)", Mul(UnaryOp("-", idx(a, IntLit(1))), FuncCall("f", [x]))),
]

PROGRAMA = """
int g = 3;
double v[2] = {1.0, 2.5};

int f(int n, bool b) {
    int a[3];
    int i;
    a[0] = n;
    x = a[1] + 1;
    read(i);
    print("ola");
    for (i = 0; i < n; i = i + 1) { if (b) { break; } else continue; }
    for (int j = 0; ; j + 1) { }
    while (i > 0) i = i - 1;
    g(1);
    return;
}
"""

PROGRAMA_AST = Program([
    VariableDeclaration("int", "g", IntLit(3)),
    ArrayDeclaration("double", "v", 2, [FloatLit(1.0), FloatLit(2.5)]),
    FunctionDefinition("int", "f", [Parameter("int", "n"), Parameter("bool", "b")], Block([
        ArrayDeclaration("int", "a", 3, None),
        VariableDeclaration("int", "i", None),
        ArrayAssignment("a", IntLit(0), Ident("n")),
        Assignment("x", Add(idx("a", IntLit(1)), IntLit(1))),
        Read("i"),
        Print(StringLit('"ola"')),
        ForStatement(Assignment("i", IntLit(0)), LessThan(Ident("i"), Ident("n")),
                     Assignment("i", Add(Ident("i"), IntLit(1))),
                     Block([IfStatement(Ident("b"), Block([Break()]), Continue())])),
        ForStatement(VariableDeclaration("int", "j", IntLit(0)), None,
                     Add(Ident("j"), IntLit(1)), Block([])),
        WhileStatement(GreaterThan(Ident("i"), IntLit(0)),
                       Assignment("i", Sub(Ident("i"), IntLit(1)))),
        FunctionCallStatement(FuncCall("g", [IntLit(1)])),
        Return(None),
    ])),
])


# ---------------------------------------------------------------------
# verificação genérica: cada campo tem o tipo anotado na dataclass
# ---------------------------------------------------------------------
def tipos_permitidos(anotacao):
    """Converte uma anotação (Exp, str, list[Exp], Exp | None, ...) em
    (tipos aceites, tipo dos elementos se for lista)."""
    if isinstance(anotacao, typing.TypeAliasType):            # type Exp = ...
        anotacao = anotacao.__value__
    origem = typing.get_origin(anotacao)
    if origem is list:
        return (list,), typing.get_args(anotacao)[0]
    if origem in (typing.Union, getattr(__import__("types"), "UnionType")):
        tipos, elem = (), None
        for arg in typing.get_args(anotacao):
            t, e = tipos_permitidos(arg)
            tipos += t
            elem = elem or e
        return tipos, elem
    if anotacao is typing.Any or anotacao is object:
        return (object,), None
    if anotacao is type(None):
        return (type(None),), None
    return (anotacao,), None


def verifica_tipos(no, caminho="raiz"):
    erros = []
    if isinstance(no, list):
        for i, x in enumerate(no):
            erros += verifica_tipos(x, f"{caminho}[{i}]")
        return erros
    if not dataclasses.is_dataclass(no):
        return erros
    dicas = typing.get_type_hints(type(no))
    for campo in dataclasses.fields(no):
        valor = getattr(no, campo.name)
        tipos, elem = tipos_permitidos(dicas[campo.name])
        if not isinstance(valor, tipos) or (type(valor) is bool and bool not in tipos):
            erros.append(f"{caminho}.{type(no).__name__}.{campo.name}: esperado "
                         f"{dicas[campo.name]}, veio {type(valor).__name__} ({valor!r})")
        if isinstance(valor, list) and elem is not None:
            et, _ = tipos_permitidos(elem)
            for i, x in enumerate(valor):
                if not isinstance(x, et):
                    erros.append(f"{caminho}.{campo.name}[{i}]: esperado {elem}, veio {type(x).__name__}")
        erros += verifica_tipos(valor, f"{caminho}.{type(no).__name__}.{campo.name}")
    return erros


def main():
    falhas = 0
    print("== expressões")
    for src, esperado in EXPRESSOES:
        obtido = pExp.parse(src)
        ok = obtido == esperado
        falhas += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} {src}" + ("" if ok else f"\n       esperado {esperado}\n       obtido   {obtido}"))

    print("\n== programa completo")
    obtido = program.parse(PROGRAMA)
    ok = obtido == PROGRAMA_AST
    falhas += not ok
    print(f"  {'OK  ' if ok else 'FAIL'} programa de exemplo")
    if not ok:
        for e, o in zip(PROGRAMA_AST.declarations[2].body.statements,
                        obtido.declarations[2].body.statements):
            if e != o:
                print(f"       esperado {e}\n       obtido   {o}")

    print("\n== tipos dos campos")
    erros = verifica_tipos(obtido)
    for _, esperado in EXPRESSOES:
        erros += verifica_tipos(pExp.parse(_))
    for e in sorted(set(erros)):
        print("  FAIL", e)
    falhas += len(set(erros))
    if not erros:
        print("  OK   todos os campos têm o tipo declarado")

    print("\n" + ("TUDO OK" if falhas == 0 else f"{falhas} FALHA(S)"))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
