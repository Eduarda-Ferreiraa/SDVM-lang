"""C2 (lista de parâmetros longa): função com LIMITE_PARAMETROS ou mais parâmetros.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC2
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main
from projeto1.SDVM_lang.SmellFiles.smells.smells_codigo import LIMITE_PARAMETROS as L

CODIGO = "C2"


def com_params(n, nome="f"):
    params = ", ".join(f"int p{k}" for k in range(n))
    return f"void {nome}({params}) {{ print(0); }}"


CASOS = [
    ("sem parâmetros -> 0", [], com_params(0)),
    (f"{L - 1} parâmetros -> 0", [], com_params(L - 1)),
    (f"{L} parâmetros -> f", ["f"], com_params(L)),
    (f"{L + 3} parâmetros -> f (1 ocorrência, não uma por parâmetro)", ["f"], com_params(L + 3)),
    ("tipos diferentes contam todos -> f", ["f"],
     "void f(int a1, double a2, char a3, bool a4) { print(0); }"),
    ("função com retorno int -> f", ["f"],
     "int f(int a1, int a2, int a3, int a4) { return a1; }"),
    ("duas funções, só uma com muitos -> g", ["g"], com_params(2) + " " + com_params(L, "g")),
    ("duas funções com muitos -> f e g", ["f", "g"], com_params(L) + " " + com_params(L + 1, "g")),
]

TD = (com_params(L) + " " + com_params(L, "g"), 20)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)
