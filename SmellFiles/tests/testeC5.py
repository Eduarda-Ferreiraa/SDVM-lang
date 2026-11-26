"""C5 (números mágicos): literais numéricos diferentes de 0 e 1 fora de declarações.
O esperado são os valores dos literais assinalados.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC5
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main, funcao

CODIGO = "C5"
G = "void g(int a) { print(a); }"

CASOS = [
    ("literal numa expressão -> 7", [7], funcao("total = total * 7; print(total);")),
    ("0, 1, 0.0 e 1.0 são permitidos -> nada", [],
     "void f(int total, double d) { total = total + 1; total = 0; d = d * 1.0; d = 0.0; }"),
    ("-1 é permitido -> nada", [], funcao("total = -1;")),
    ("-5 -> 5", [5], funcao("total = -5;")),
    ("double -> 2.5", [2.5], "void f(double d) { d = d * 2.5; }"),
    ("o mesmo valor duas vezes conta duas -> 7, 7", [7, 7], funcao("total = total * 7 + 7;")),
    ("três literais numa expressão -> 3, 4, 5", [3, 4, 5], funcao("total = total * 3 + 4 - 5;")),
    ("valor inicial de uma declaração -> nada", [],
     funcao("int dias = 7; double taxa = 0.23; print(dias);")),
    ("literal numa expressão de uma declaração -> nada", [],
     funcao("int segundos = total * 60; print(segundos);")),
    ("declaração global -> nada", [], "int LIMITE = 100; " + funcao("print(LIMITE);")),
    ("valores iniciais de um array -> nada", [],
     funcao("int v[3] = {4, 5, 6}; print(v[0]);")),
    ("o tamanho de um array não é literal -> nada", [], funcao("int v[10]; print(v[0]);")),
    ("return -> 42", [42], "int f(int total) { return 42; }"),
    ("índice e valor de atribuição a array -> 2, 3", [2, 3],
     funcao("int v[5]; v[3] = 2; print(v[0]);")),
    ("índice numa leitura de array -> 4", [4], funcao("int v[5]; print(v[4]);")),
    ("condição de um if -> 100", [100], funcao("if (total > 100) { print(total); }")),
    ("limite e passo de um for (o 2 inicial é declaração) -> 10, 3", [10, 3],
     funcao("for (int i = 2; i < 10; i = i + 3) { print(i); }")),
    ("for cujo início é uma atribuição (não declaração) -> 5", [5],
     funcao("int i = 0; for (i = 5; i < total; i = i + 1) { print(i); }")),
    ("double com expoente 2.0e3 -> 2000.0", [2000.0], "void f(double d) { d = d * 2.0e3; }"),
    ("-2.5 -> 2.5", [2.5], "void f(double d) { d = -2.5; }"),
    ("argumento de print -> 7", [7], funcao("print(7);")),
    ("argumento de uma chamada -> 7", [7], G + " " + funcao("g(7);")),
    ("char, bool e string não são números -> nada", [],
     "void f(int total) { char c = 'a'; c = 'b'; bool b = true; b = false; print(\"abc 123\"); }"),
]

TD = (funcao("total = total * 3 + 4 - 5;"), 15)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)