"""Testa os smells C1, C3, C4, C5 e C8 (smells_design.py).

Para cada caso: o smell, o nº de ocorrências esperado, o que o caso
verifica e o programa. Os casos do limite usam as constantes do ficheiro.

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeDesign
"""
import sys

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, relatorio
from projeto1.SDVM_lang.SmellFiles.smells.smells_design import (
    MAX_INSTRUCOES, MAX_PROFUNDIDADE, MAX_OPERADORES_LOGICOS,
)


def prints(n):
    return " ".join("print(total);" for _ in range(n))


def ifs_aninhados(n, dentro="print(total);"):
    """n ifs uns dentro dos outros."""
    s = dentro
    for _ in range(n):
        s = f"if (total > 0) {{ {s} }}"
    return s


def condicao(n_ops):
    """Condição com n_ops operadores && (n_ops + 1 comparações)."""
    return " && ".join(["total > 0"] * (n_ops + 1))


def funcao(corpo):
    return f"void f(int total) {{ {corpo} }}"


CASOS = [
    # ================================================================== C1
    ("C1", 0, f"{MAX_INSTRUCOES} instruções -> não é longa",
     funcao(prints(MAX_INSTRUCOES))),
    ("C1", 1, f"{MAX_INSTRUCOES + 1} instruções -> longa",
     funcao(prints(MAX_INSTRUCOES + 1))),
    ("C1", 0, "instruções dentro de if/while contam, a soma dá o limite -> 0",
     funcao(f"if (total > 0) {{ {prints(MAX_INSTRUCOES // 2 - 1)} }} "
            f"while (total > 0) {{ {prints(MAX_INSTRUCOES - MAX_INSTRUCOES // 2 - 1)} }}")),
    ("C1", 1, "instruções dentro de if/while contam, a soma passa o limite -> 1",
     funcao(f"if (total > 0) {{ {prints(MAX_INSTRUCOES // 2)} }} "
            f"while (total > 0) {{ {prints(MAX_INSTRUCOES - MAX_INSTRUCOES // 2)} }}")),
    ("C1", 0, "o cabeçalho do for não conta à parte (for = 1)",
     funcao(f"{prints(MAX_INSTRUCOES - 2)} "
            "for (int i = 0; i < total; i = i + 1) { print(i); }")),
    ("C1", 1, "duas funções, só uma longa -> 1",
     funcao(prints(MAX_INSTRUCOES + 1)) + " void g(int total) { print(total); }"),

    # ================================================================== C3
    ("C3", 0, f"{MAX_PROFUNDIDADE} ifs aninhados -> 0",
     funcao(ifs_aninhados(MAX_PROFUNDIDADE))),
    ("C3", 1, f"{MAX_PROFUNDIDADE + 1} ifs aninhados -> 1",
     funcao(ifs_aninhados(MAX_PROFUNDIDADE + 1))),
    ("C3", 0, "cadeia de 6 else if -> 0 (mesmo nível)",
     funcao("if (total == 1) { print(1); } else if (total == 2) { print(2); } "
            "else if (total == 3) { print(3); } else if (total == 4) { print(4); } "
            "else if (total == 5) { print(5); } else if (total == 6) { print(6); } "
            "else { print(0); }")),
    ("C3", 1, "aninhamento profundo dentro de um else (não else if) -> 1",
     funcao(f"if (total > 0) {{ print(total); }} else {{ {ifs_aninhados(MAX_PROFUNDIDADE)} }}")),
    ("C3", 1, "while/for/if misturados, profundidade limite + 1 -> 1",
     funcao("while (total > 0) { for (int i = 0; i < total; i = i + 1) { "
            + ifs_aninhados(MAX_PROFUNDIDADE - 1) + " } }")),
    ("C3", 1, "vários ramos fundos na mesma função -> 1 (conta por função)",
     funcao(ifs_aninhados(MAX_PROFUNDIDADE + 1) + " " + ifs_aninhados(MAX_PROFUNDIDADE + 2))),
    ("C3", 2, "duas funções fundas -> 2",
     funcao(ifs_aninhados(MAX_PROFUNDIDADE + 1))
     + f" void g(int total) {{ {ifs_aninhados(MAX_PROFUNDIDADE + 1)} }}"),

    # ================================================================== C4
    ("C4", 0, f"if com {MAX_OPERADORES_LOGICOS} operadores -> 0",
     funcao(f"if ({condicao(MAX_OPERADORES_LOGICOS)}) {{ print(total); }}")),
    ("C4", 1, f"if com {MAX_OPERADORES_LOGICOS + 1} operadores -> 1",
     funcao(f"if ({condicao(MAX_OPERADORES_LOGICOS + 1)}) {{ print(total); }}")),
    ("C4", 1, "&& e || misturados contam os dois -> 1",
     funcao("if (total > 0 && total < 9 || total == 20 && total != 5 || total == 30) "
            "{ print(total); }")),
    ("C4", 1, "while com condição complexa -> 1",
     funcao(f"while ({condicao(MAX_OPERADORES_LOGICOS + 1)}) {{ total = total - 1; }}")),
    ("C4", 1, "for com condição complexa -> 1",
     funcao(f"for (int i = 0; {condicao(MAX_OPERADORES_LOGICOS + 1)}; i = i + 1) {{ print(i); }}")),
    ("C4", 0, "expressão complexa numa atribuição (não é condição) -> 0",
     "void f(int total) { bool ok = false; "
     f"ok = {condicao(MAX_OPERADORES_LOGICOS + 2)}; print(ok); }}"),
    ("C4", 2, "if complexo com outro if complexo dentro -> 2",
     funcao(f"if ({condicao(MAX_OPERADORES_LOGICOS + 1)}) {{ "
            f"if ({condicao(MAX_OPERADORES_LOGICOS + 1)}) {{ print(total); }} }}")),

    # ================================================================== C5
    ("C5", 1, "literal numa expressão -> 1",
     funcao("total = total * 7; print(total);")),
    ("C5", 0, "0 e 1 permitidos (também 0.0 e 1.0) -> 0",
     "void f(int total, double d) { total = total + 1; total = 0; d = d * 1.0; d = 0.0; }"),
    ("C5", 0, "-1 permitido -> 0",
     funcao("total = -1;")),
    ("C5", 1, "-5 -> 1 (o 5)",
     funcao("total = -5;")),
    ("C5", 1, "double -> 1",
     "void f(double d) { d = d * 2.5; }"),
    ("C5", 0, "valor inicial de uma declaração -> 0",
     funcao("int dias = 7; double taxa = 0.23; print(dias);")),
    ("C5", 0, "literal numa expressão de uma declaração -> 0",
     funcao("int segundos = total * 60; print(segundos);")),
    ("C5", 1, "literal num return -> 1",
     "int f(int total) { return 42; }"),
    ("C5", 2, "índice e valor de atribuição a array -> 2",
     funcao("int v[5]; v[3] = 2; print(v[0]);")),
    ("C5", 1, "limite de um for -> 1",
     funcao("for (int i = 0; i < 10; i = i + 1) { print(i); }")),
    ("C5", 3, "três literais na mesma linha -> 3",
     funcao("total = total * 3 + 4 - 5;")),

    # ================================================================== C8
    ("C8", 0, "sem globais -> 0",
     funcao("total = total + 1;")),
    ("C8", 0, "global só lido -> 0",
     "int g = 0; void f(int total) { print(g + total); }"),
    ("C8", 1, "atribuição a um global -> 1",
     "int g = 0; void f(int total) { g = total; }"),
    ("C8", 1, "read para um global -> 1",
     "int g = 0; void f(int total) { read(g); }"),
    ("C8", 1, "atribuição a uma posição de um array global -> 1",
     "int v[3]; void f(int total) { v[0] = total; }"),
    ("C8", 1, "global como contador de for -> 1",
     "int g = 0; void f(int total) { for (g = 0; g < total; g = g + 1) { print(g); } }"),
    ("C8", 1, "global alterado dentro de if/while -> 1",
     "int g = 0; void f(int total) { while (total > 0) { if (total > 5) { g = total; } total = total - 1; } }"),
    ("C8", 0, "parâmetro com o nome do global esconde-o -> 0",
     "int g = 0; void f(int g) { g = 5; }"),
    ("C8", 0, "variável local com o nome do global esconde-a -> 0",
     "int g = 0; void f(int total) { int g = 1; g = total; }"),
    ("C8", 1, "a mesma função altera dois globais -> 1 (conta por função)",
     "int g = 0; int h = 0; void f(int total) { g = total; h = total; }"),
    ("C8", 2, "duas funções alteram globais -> 2",
     "int g = 0; void f(int total) { g = total; } void k(int total) { g = 0; }"),
    ("C8", 1, "local numa função não esconde o global noutra -> 1",
     "int g = 0; void f(int total) { int g = 1; g = 2; } void k(int total) { g = total; }"),
]


def main():
    print(f"MAX_INSTRUCOES={MAX_INSTRUCOES}  MAX_PROFUNDIDADE={MAX_PROFUNDIDADE}  "
          f"MAX_OPERADORES_LOGICOS={MAX_OPERADORES_LOGICOS}\n")
    falhas = 0
    atual = None
    for codigo, esperado, descricao, src in CASOS:
        if codigo != atual:
            atual = codigo
            print(f"--- {codigo} ---")
        try:
            p = program.parse(src)
            k = len(detetar(p, [codigo]))
        except Exception as e:                       # erro de parse ou na deteção
            falhas += 1
            print(f"ERRO {descricao}\n       {type(e).__name__}: {e}")
            print(f"       programa: {src}")
            continue
        ok = k == esperado
        falhas += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {descricao}")
        print(f"       esperado {esperado}, detetado {k}")
        if not ok:
            print("       programa:\n" + "\n".join("         " + l for l in pretty(p).splitlines()))

    # TD do C8: 15 min por função
    p = program.parse(next(s for c, _, d, s in CASOS if d.startswith("duas funções alteram")))
    td = next(l[5] for l in relatorio(p, ["C8"]))
    ok = td == 30
    falhas += not ok
    print(f"\n{'OK  ' if ok else 'FAIL'} TD do C8 com duas funções = 30 min (detetado {td})")

    print("\n" + ("TUDO OK" if falhas == 0 else f"{falhas} FALHA(S)"))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
