"""C6 (identificador curto): declarações com nome de 1 letra, exceto i/j/k
que sejam contador de um for na mesma função. O esperado são os nomes.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC6
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main

CODIGO = "C6"

CASOS = [
    # contadores de for (isentos)
    ("for (int i = 0; ...) -> nada", [],
     "void f(int total) { for (int i = 0; i < total; i = i + 1) { print(i); } }"),
    ("int i fora e for (i = 0; ...) na mesma função -> nada", [],
     "void f(int total) { int i = 0; for (i = 0; i < total; i = i + 1) { print(i); } }"),
    ("for aninhados com i e j -> nada", [],
     "void f(int total) { for (int i = 0; i < total; i = i + 1) "
     "{ for (int j = 0; j < i; j = j + 1) { print(j); } } }"),
    ("dois for seguidos, cada um com int i -> nada", [],
     "void f(int total) { for (int i = 0; i < total; i = i + 1) { print(i); } "
     "for (int i = 0; i < total; i = i + 1) { print(i); } }"),
    ("k contador de um for dentro de um if -> nada", [],
     "void f(int total) { int k = 0; if (total > 0) { for (k = 0; k < total; k = k + 1) { print(k); } } }"),
    ("parâmetro i usado como contador -> nada", [],
     "void f(int i) { for (i = 0; i < 10; i = i + 1) { print(i); } }"),
    # i/j/k que não são contador
    ("int i usado só num while -> i", ["i"],
     "void f(int total) { int i = 0; while (i < total) { print(i); i = i + 1; } }"),
    ("int i numa função, o for noutra -> só o i da 1ª", ["i"],
     "void f(int total) { int i = 0; print(i); } "
     "void g(int total) { for (int i = 0; i < total; i = i + 1) { print(i); } }"),
    ("i global usado no for de uma função -> o global", ["i"],
     "int i = 0; void f(int total) { for (i = 0; i < total; i = i + 1) { print(i); } }"),
    ("j fora (num while) e k no for -> j", ["j"],
     "void f(int total) { int j = 0; while (j < total) { j = j + 1; } "
     "for (int k = 0; k < total; k = k + 1) { print(k); } }"),
    # outras letras
    ("for (int x = 0; ...) -> x (não é i/j/k)", ["x"],
     "void f(int total) { for (int x = 0; x < total; x = x + 1) { print(x); } }"),
    ("int n; for (n = 0; ...) -> n", ["n"],
     "void f(int total) { int n = 0; for (n = 0; n < total; n = n + 1) { print(n); } }"),
    ("variável local -> x", ["x"], "void f(int total) { int x = total * 2; print(x); }"),
    ("array -> v", ["v"], "void f(int total) { int v[3]; v[0] = total; print(v[0]); }"),
    ("global -> g", ["g"], "int g = 0; void f(int total) { print(g); }"),
    ("char e bool -> c, b", ["c", "b"],
     "void f(int total) { char c = 'a'; bool b = true; print(c); print(b); }"),
    # parâmetros
    ("dois parâmetros -> a, b", ["a", "b"],
     "int maior(int a, int b) { if (a > b) { return a; } return b; }"),
    ("parâmetro double -> x", ["x"], "double dobro(double x) { return x * 2.0; }"),
    # o que não conta
    ("nomes com 2 ou mais letras -> nada", [],
     "void f(int total) { int xy = total; int contador = xy + 1; print(contador); }"),
    ("nome de função com 1 letra -> nada (funções ficam de fora)", [],
     "void f(int total) { print(total); }"),
]

TD = ("int maior(int a, int b) { if (a > b) { return a; } return b; }", 4)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)
