"""C7 (variável/parâmetro/array não usado): declaração cujo nome nunca é
usado no programa. Usos: Ident, Index e os alvos de atribuições e read
(atribuir conta como usar). O esperado são os nomes.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC7
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main

CODIGO = "C7"
G = "void g(int valor) { print(valor); }"

CASOS = [
    ("variável usada -> nada", [], "void f(int total) { int soma = total; print(soma); }"),
    ("variável nunca usada -> contador", ["contador"],
     "void f(int total) { int contador = 0; print(total); }"),
    ("parâmetro nunca usado -> extra", ["extra"],
     "void f(int total, int extra) { print(total); }"),
    ("vários não usados -> contador, extra", ["contador", "extra"],
     "void f(int total, int extra) { int contador = 0; print(total); }"),
    ("só atribuída -> nada (atribuir conta como uso)", [],
     "void f(int total) { int soma = 0; soma = total; }"),
    ("só lida com read -> nada", [], "void f(int total) { int valor = 0; read(valor); print(total); }"),
    ("array usado por índice -> nada", [], "void f(int total) { int tabela[3]; print(tabela[0] + total); }"),
    ("array só atribuído -> nada", [], "void f(int total) { int tabela[3]; tabela[0] = total; }"),
    ("array nunca usado -> tabela", ["tabela"], "void f(int total) { int tabela[3]; print(total); }"),
    ("global usado numa função -> nada", [], "int LIMITE = 10; void f(int total) { print(LIMITE + total); }"),
    ("global nunca usado -> LIMITE", ["LIMITE"], "int LIMITE = 10; void f(int total) { print(total); }"),
    ("usada só no valor inicial de outra -> copia", ["copia"],
     "void f(int total) { int base = total; int copia = base; }"),
    ("contador de for usado na condição -> nada", [],
     "void f(int total) { for (int idx = 0; idx < total; idx = idx + 1) { print(total); } }"),
    ("usada numa condição -> nada", [], "void f(int total) { int lim = 5; if (total > lim) { print(total); } }"),
    ("usada num return -> nada", [], "int f(int total) { int res = total; return res; }"),
    ("usada como argumento de uma chamada -> nada", [],
     G + " void f(int total) { int arg = total; g(arg); }"),
    ("função nunca chamada não conta (só variáveis) -> nada", [],
     "void ajuda(int total) { print(total); }"),
    ("o mesmo nome usado noutra função -> nada (limitação: conta-se por nome no programa)", [],
     "void f(int total) { int aux = 0; print(total); } void h(int aux) { print(aux); }"),
]

TD = ("void f(int total, int extra) { int contador = 0; print(total); }", 6)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)
