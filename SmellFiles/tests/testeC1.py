"""C1 (função longa): função com mais de MAX_INSTRUCOES instruções.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC1
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main, prints, funcao
from projeto1.SDVM_lang.SmellFiles.smells.smells_design import MAX_INSTRUCOES as M

CODIGO = "C1"

# 14 instruções, uma de cada tipo (os ciclos e o if contam também o que têm dentro)
TIPOS = ("int x = 0; int v[2]; x = 1; v[0] = 1; read(x); g(x); "
         "while (x > 0) { break; } while (x > 0) { continue; } "
         "if (x > 0) { print(x); } else { print(0); }")
N_TIPOS = 13                                   # + o return no fim = 14
G = "void g(int a) { print(a); }"


def com_tipos(n_prints):
    return G + f" void f(int total) {{ {TIPOS} {prints(n_prints)} return; }}"


CASOS = [
    (f"{M} instruções -> 0", [], funcao(prints(M))),
    (f"{M + 1} instruções -> f", ["f"], funcao(prints(M + 1))),
    (f"todos os tipos de instrução contam: {M} no total -> 0", [], com_tipos(M - N_TIPOS - 1)),
    (f"todos os tipos de instrução contam: {M + 1} no total -> f", ["f"], com_tipos(M - N_TIPOS)),
    ("instruções no then e no else contam (soma = limite) -> 0", [],
     funcao(f"if (total > 0) {{ {prints(M // 2 - 1)} }} else {{ {prints(M - M // 2)} }}")),
    ("instruções no then e no else contam (soma = limite + 1) -> f", ["f"],
     funcao(f"if (total > 0) {{ {prints(M // 2)} }} else {{ {prints(M - M // 2)} }}")),
    ("o cabeçalho do for não conta à parte (total = limite) -> 0", [],
     funcao(f"{prints(M - 2)} for (int i = 0; i < total; i = i + 1) {{ print(i); }}")),
    ("o corpo do for conta (total = limite + 1) -> f", ["f"],
     funcao(f"{prints(M - 1)} for (int i = 0; i < total; i = i + 1) {{ print(i); }}")),
    ("blocos soltos { } não contam -> 0", [], funcao(f"{{ {{ {prints(M)} }} }}")),
    ("declarações globais não contam para nenhuma função -> 0", [],
     " ".join(f"int g{k} = 0;" for k in range(M)) + " " + funcao(prints(M))),
    ("função vazia -> 0", [], "void f(int total) { }"),
    ("duas funções, só uma longa -> f", ["f"],
     funcao(prints(M + 1)) + " " + funcao(prints(3), "g")),
    ("duas funções longas -> f e g", ["f", "g"],
     funcao(prints(M + 1)) + " " + funcao(prints(M + 5), "g")),
]

TD = (funcao(prints(M + 1)) + " " + funcao(prints(M + 1), "g"), 40)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)
