"""C3 (aninhamento profundo): profundidade de if/while/for > MAX_PROFUNDIDADE.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC3
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main, funcao, ifs_aninhados
from projeto1.SDVM_lang.SmellFiles.smells.smells_design import MAX_PROFUNDIDADE as P

CODIGO = "C3"

CADEIA = ("if (total == 1) { print(1); } else if (total == 2) { print(2); } "
          "else if (total == 3) { print(3); } else if (total == 4) { print(4); } "
          "else if (total == 5) { print(5); } else if (total == 6) { print(6); } "
          "else { print(0); }")

CASOS = [
    (f"{P} ifs aninhados -> 0", [], funcao(ifs_aninhados(P))),
    (f"{P + 1} ifs aninhados -> f", ["f"], funcao(ifs_aninhados(P + 1))),
    ("cadeia de 6 else if -> 0 (mesmo nível)", [], funcao(CADEIA)),
    (f"else if com {P - 1} ifs dentro (total {P}) -> 0", [],
     funcao(f"if (total == 1) {{ print(1); }} else if (total == 2) {{ {ifs_aninhados(P - 1)} }}")),
    (f"else if com {P} ifs dentro (total {P + 1}) -> f", ["f"],
     funcao(f"if (total == 1) {{ print(1); }} else if (total == 2) {{ {ifs_aninhados(P)} }}")),
    ("else normal com ifs dentro soma um nível -> f", ["f"],
     funcao(f"if (total > 0) {{ print(total); }} else {{ {ifs_aninhados(P)} }}")),
    (f"while > for > {P - 2} ifs (total {P}) -> 0", [],
     funcao("while (total > 0) { for (int i = 0; i < total; i = i + 1) { "
            + ifs_aninhados(P - 2) + " } }")),
    (f"while > for > {P - 1} ifs (total {P + 1}) -> f", ["f"],
     funcao("while (total > 0) { for (int i = 0; i < total; i = i + 1) { "
            + ifs_aninhados(P - 1) + " } }")),
    ("corpos sem chavetas também contam -> f", ["f"],
     funcao("for (int i = 0; i < total; i = i + 1) "
            + " ".join(["if (total > 0)"] * P) + " print(i);")),
    ("blocos soltos { } não somam níveis -> 0", [],
     funcao(f"{{ {{ {{ {{ {ifs_aninhados(P)} }} }} }} }}")),
    ("muitos ifs em sequência (não aninhados) -> 0", [],
     funcao(" ".join(["if (total > 0) { print(total); }"] * 10))),
    ("vários ramos fundos na mesma função -> f (1 por função)", ["f"],
     funcao(ifs_aninhados(P + 1) + " " + ifs_aninhados(P + 2))),
    ("duas funções fundas -> f e g", ["f", "g"],
     funcao(ifs_aninhados(P + 1)) + " " + funcao(ifs_aninhados(P + 1), "g")),
]

TD = (funcao(ifs_aninhados(P + 1)) + " " + funcao(ifs_aninhados(P + 1), "g"), 30)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)
