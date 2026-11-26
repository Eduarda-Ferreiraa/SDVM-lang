"""C8 (estado global mutável): função que altera uma variável/array global
(atribuição, atribuição a posição, read). O esperado são os nomes das funções.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC8
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main

CODIGO = "C8"

CASOS = [
    ("sem globais -> nada", [], "void f(int total) { total = total + 1; }"),
    ("global só lido -> nada", [], "int g = 0; void f(int total) { print(g + total); }"),
    ("global só numa condição -> nada", [], "int g = 0; void f(int total) { if (g > total) { print(total); } }"),
    ("atribuição a um global -> f", ["f"], "int g = 0; void f(int total) { g = total; }"),
    ("read para um global -> f", ["f"], "int g = 0; void f(int total) { read(g); }"),
    ("atribuição a uma posição de um array global -> f", ["f"],
     "int v[3]; void f(int total) { v[0] = total; }"),
    ("global como contador de for -> f", ["f"],
     "int g = 0; void f(int total) { for (g = 0; g < total; g = g + 1) { print(g); } }"),
    ("global alterado só no update do for -> f", ["f"],
     "int g = 0; void f(int total) { for (int i = 0; i < total; g = g + 1) { print(i); } }"),
    ("global alterado dentro de if/while -> f", ["f"],
     "int g = 0; void f(int total) { while (total > 0) { if (total > 5) { g = total; } total = total - 1; } }"),
    ("parâmetro com o nome do global esconde-o -> nada", [],
     "int g = 0; void f(int g) { g = 5; }"),
    ("variável local com o nome do global esconde-a -> nada", [],
     "int g = 0; void f(int total) { int g = 1; g = total; }"),
    ("array local com o nome do array global esconde-o -> nada", [],
     "int v[3]; void f(int total) { int v[2]; v[0] = total; }"),
    ("a mesma função altera dois globais -> f (1 por função)", ["f"],
     "int g = 0; int h = 0; void f(int total) { g = total; h = total; }"),
    ("duas funções alteram globais -> f e k", ["f", "k"],
     "int g = 0; void f(int total) { g = total; } void k(int total) { g = 0; }"),
    ("local numa função não esconde o global noutra -> k", ["k"],
     "int g = 0; void f(int total) { int g = 1; g = 2; } void k(int total) { g = total; }"),
    ("LIMITAÇÃO ACEITE: local só dentro de um if esconde o global na função toda -> nada", [],
     "int g = 0; void f(int total) { if (total > 0) { int g = 1; g = 2; } g = total; }"),
]

TD = ("int g = 0; void f(int total) { g = total; } void k(int total) { g = 0; }", 30)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)
