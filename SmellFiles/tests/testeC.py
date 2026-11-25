"""Testes dirigidos de C2, C6, C7, C9, das métricas e do TD.

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC

Cada teste devolve a lista de erros; no fim imprime OK/FAIL por teste.
"""
import sys

from projeto1.SDVM_lang.ParserFiles.parser.parser import program, Program
from projeto1.SDVM_lang.ParserFiles.parser.declarations import FunctionDefinition, Parameter
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import Block
from projeto1.SDVM_lang.SmellFiles.smells.metricas import parametros_por_funcao, loc
from projeto1.SDVM_lang.SmellFiles.smells.smells_1 import deteta_c2
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, relatorio, divida_tecnica

TODOS_C = ["C2", "C6", "C7", "C9"]


def verifica(descricao, obtido, esperado, erros):
    if obtido != esperado:
        erros.append(f"{descricao}: esperado {esperado}, obtido {obtido}")


def nomes(src, codigo):
    """nomes das declarações apanhadas pelo smell (ordenados)."""
    return sorted(n.name for _, n, _ in detetar(program.parse(src), [codigo]))


def conta(src, codigo):
    return len(detetar(program.parse(src), [codigo]))


# ---------------------------------------------------------------- C2 + métrica

def fn(nome, k):
    return FunctionDefinition("void", nome, [Parameter("int", f"p{i}") for i in range(k)], Block([]))


def t_c2():
    erros = []
    prog = Program([fn("a", 0), fn("b", 3), fn("c", 4)])
    verifica("parametros_por_funcao", sorted(parametros_por_funcao(prog)),
             [("a", 0), ("b", 3), ("c", 4)], erros)
    verifica("deteta_c2 (0, 3, 4 parâmetros)", [deteta_c2(f, None) for f in prog.declarations],
             [False, False, True], erros)
    verifica("relatorio C2", relatorio(prog, ["C2"]),
             [("C2", "muitos parâmetros", 1, 0, 10, 10)], erros)
    return erros


# ---------------------------------------------------------------- C6

def t_c6():
    erros = []
    casos = [
        ("nome curto",              "void f() { int x; }", ["x"]),
        ("nome longo",              "void f() { int total; }", []),
        ("i em for (declarado)",    "void f() { for (int i = 0; i < 3; i = i + 1) { } }", []),
        ("i declarado fora do for", "void f() { int i; for (i = 0; i < 3; i = i + 1) { } }", ["i"]),
        ("x em for não é isento",   "void f() { for (int x = 0; x < 3; x = x + 1) { } }", ["x"]),
        ("parâmetro curto",         "void f(int a, int total) { }", ["a"]),
        ("array curto",             "void f() { int v[2]; }", ["v"]),
        ("nome de função não conta", "void f() { }", []),
        ("i no for numa função, i fora do for noutra (só a 2.ª conta)",
         "void f() { for (int i = 0; i < 3; i = i + 1) { } } void g() { int i; }", ["i"]),
    ]
    for descricao, src, esperado in casos:
        verifica("C6 " + descricao, nomes(src, "C6"), esperado, erros)
    return erros


# ---------------------------------------------------------------- C7

def t_c7():
    erros = []
    casos = [
        ("variável não usada",        "void f() { int x; }", ["x"]),
        ("variável usada",            "void f() { int x; print(x); }", []),
        ("parâmetro não usado",       "void f(int p) { }", ["p"]),
        ("parâmetro usado",           "int f(int p) { return p; }", []),
        ("array não usado",           "void f() { int v[2]; }", ["v"]),
        ("array atribuído (conta)",   "void f() { int v[2]; v[0] = 1; }", []),
        ("array lido por índice",     "void f() { int v[2]; print(v[0]); }", []),
        ("atribuição conta como uso", "void f() { int x; x = 1; }", []),
        ("read conta como uso",       "void f() { int x; read(x); }", []),
        ("uso no inicializador",      "void f() { int a = 1; int b = a; print(b); }", []),
        ("uso no for",                "void f() { for (int j = 0; j < 2; j = j + 1) { } }", []),
        ("inicializador com chamada (só reporte)",
         "int h() { return 1; } void f() { int x = h(); }", ["x"]),
        ("LIMITAÇÃO: mesmo nome noutra função esconde (falso negativo)",
         "void f() { int x; } void g() { int x; print(x); }", []),
        ("LIMITAÇÃO: shadowing não distinguido (falso negativo)",
         "void f() { int x; { int x; print(x); } }", []),
    ]
    for descricao, src, esperado in casos:
        verifica("C7 " + descricao, nomes(src, "C7"), esperado, erros)
    return erros


# ---------------------------------------------------------------- C9

def t_c9():
    erros = []
    casos = [
        ("blocos diferentes",
         "void f() { print(1); print(2); } void g() { print(1); print(3); }", 0),
        ("dois blocos iguais (nomes de função diferentes)",
         "void f() { print(1); print(2); } void g() { print(1); print(2); }", 2),
        ("três cópias (participantes)",
         "void f() { print(1); print(2); } void g() { print(1); print(2); } "
         "void h() { print(1); print(2); }", 3),
        ("blocos vazios", "void f() { } void g() { }", 0),
        ("blocos de 1 instrução", "void f() { print(1); } void g() { print(1); }", 0),
        ("then e else iguais",
         "void f(int x) { if (x > 0) { print(1); print(2); } else { print(1); print(2); } }", 2),
        ("LIMITAÇÃO: aninhamento conta tudo (2 corpos + 2 blocos internos)",
         "void f(int x) { if (x > 0) { print(1); print(2); } print(3); } "
         "void g(int x) { if (x > 0) { print(1); print(2); } print(3); }", 4),
    ]
    for descricao, src, esperado in casos:
        verifica("C9 " + descricao, conta(src, "C9"), esperado, erros)
    return erros


# ---------------------------------------------------------------- LOC e params (parsed)

def t_metricas():
    erros = []
    p = program.parse("void a() { } int b(int x, int y) { return x; }")
    verifica("parametros_por_funcao", sorted(parametros_por_funcao(p)), [("a", 0), ("b", 2)], erros)
    verifica("LOC global + main",
             loc(program.parse("int g = 1; void main() { print(g); }")), 4, erros)
    verifica("LOC if/else",
             loc(program.parse("void f(int x) { if (x > 0) { print(1); } else { print(2); } }")), 7, erros)
    verifica("LOC bloco vazio", loc(program.parse("void f() { }")), 1, erros)
    return erros


# ---------------------------------------------------------------- TD

PROGRAMA_TD = """
int soma(int a, int b, int c, int d) {
    return a + b + c + d;
}
void main() {
    int total = soma(1, 2, 3, 4);
    int resto;
    print(total);
}
void um()   { print(1); print(2); }
void dois() { print(1); print(2); }
"""


def t_td():
    """C2: 1 x 10 = 10 | C6: a,b,c,d = 4 x 2 = 8 | C7: resto = 1 x 3 = 3 | C9: 2 x 30 = 60."""
    erros = []
    prog = program.parse(PROGRAMA_TD)
    rel = {linha[0]: linha for linha in relatorio(prog, TODOS_C)}
    for codigo, ocorr, td in [("C2", 1, 10), ("C6", 4, 8), ("C7", 1, 3), ("C9", 2, 60)]:
        verifica(f"{codigo} ocorrências", rel[codigo][2], ocorr, erros)
        verifica(f"{codigo} TD", rel[codigo][5], td, erros)
    verifica("TD total", divida_tecnica(prog, TODOS_C), 81, erros)
    return erros


TESTES = [t_c2, t_c6, t_c7, t_c9, t_metricas, t_td]


def main():
    falhas = 0
    for t in TESTES:
        try:
            erros = t()
        except Exception as e:                      # inclui erros de parse
            erros = [f"{type(e).__name__}: {str(e)[:200]}"]
        falhas += bool(erros)
        print(f"{'OK  ' if not erros else 'FAIL'} {t.__name__}")
        for e in erros:
            print(f"       {e}")
    print("\n" + ("TUDO OK" if falhas == 0 else f"{falhas} TESTE(S) COM FALHAS"))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
