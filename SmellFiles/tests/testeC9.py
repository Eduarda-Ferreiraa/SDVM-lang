"""C9 (código duplicado): bloco com >= MIN_INSTRUCOES instruções que é uma
cópia a mais de outro igual (o original não conta; um bloco dentro de um
bloco duplicado não conta à parte). O esperado é o nº de ocorrências.
Os blocos dos casos têm 4 instruções (servem para MIN_INSTRUCOES <= 4).

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC9
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main
from projeto1.SDVM_lang.SmellFiles.smells.analise_c import MIN_INSTRUCOES as MIN

CODIGO = "C9"

X = "a = a + 1; print(a); a = a * 2; print(a);"
Y = "a = a - 3; print(0); a = a / 2; print(1);"
C = "s = s * 2; print(s); s = s + 3; print(0);"
A = f"s = s + 1; print(s); s = s - 1; while (s < 10) {{ {C} }}"     # 4 instruções, com C dentro
D = "print(s); s = s + 2; print(1); s = s - 1;"
C3 = f"s = s + 1; print(s); s = s - 1; if (s > 4) {{ {D} }}"
A3 = f"s = 1; print(s); s = 2; while (s < 9) {{ {C3} }}"


def bloco_com(n):
    return " ".join(f"print({k});" for k in range(1, n + 1))


def f(corpo, params="int a"):
    return f"void f({params}) {{ {corpo} }}"


CASOS = [
    # básicos
    ("sem duplicados -> 0", 0, f(f"if (a > 0) {{ {X} }} if (a < 0) {{ {Y} }}")),
    ("duas cópias iguais -> 1 (o original não conta)", 1,
     f(f"if (a > 0) {{ {X} }} if (a < 0) {{ {X} }}")),
    ("três cópias iguais -> 2", 2,
     f(f"if (a > 0) {{ {X} }} if (a < 0) {{ {X} }} if (a == 0) {{ {X} }}")),
    ("dois pares diferentes -> 2", 2,
     f(f"if (a > 0) {{ {X} }} if (a < 0) {{ {X} }} while (a > 9) {{ {Y} }} while (a > 5) {{ {Y} }}")),
    ("o mesmo bloco em if e em while -> 1 (só o bloco interessa)", 1,
     f(f"if (a > 0) {{ {X} }} while (a > 9) {{ {X} }}")),
    # aninhados
    ("A e B iguais, ambos com C dentro -> 1", 1,
     f(f"if (a > 0) {{ {A} }} if (a < 0) {{ {A} }}", "int a, int s")),
    ("A, B e uma cópia solta de C DEPOIS -> 2", 2,
     f(f"if (a > 0) {{ {A} }} if (a < 0) {{ {A} }} while (a > 5) {{ {C} }}", "int a, int s")),
    ("cópia solta de C ANTES de A e B -> 2 (a ordem não importa)", 2,
     f(f"while (a > 5) {{ {C} }} if (a > 0) {{ {A} }} if (a < 0) {{ {A} }}", "int a, int s")),
    ("bloco igual dentro de pais diferentes -> 1", 1,
     f(f"if (a > 0) {{ print(1); print(9); print(8); while (s < 10) {{ {C} }} }} "
       f"if (a < 0) {{ print(2); print(9); print(8); while (s < 10) {{ {C} }} }}", "int a, int s")),
    ("três níveis: A=B, C dentro, D dentro de C -> 1", 1,
     f(f"if (a > 0) {{ {A3} }} if (a < 0) {{ {A3} }}", "int a, int s")),
    # o que não é igual
    ("nomes de variáveis diferentes -> 0", 0,
     f(f"if (a > 0) {{ {X} }} if (a < 0) {{ {X.replace('a', 's')} }}", "int a, int s")),
    ("mesmas instruções por outra ordem -> 0", 0,
     f("if (a > 0) { a = a + 1; print(a); a = a * 2; print(0); } "
       "if (a < 0) { print(0); a = a * 2; print(a); a = a + 1; }")),
    ("um literal diferente -> 0", 0,
     f(f"if (a > 0) {{ {X} }} if (a < 0) {{ {X.replace('2', '3')} }}")),
    ("literal de tipo diferente (1 vs true) -> 0", 0,
     "void f(bool b) { if (b) { b = 1; print(b); b = false; print(0); } "
     "if (!b) { b = true; print(b); b = false; print(0); } }"),
    # tamanho mínimo
    ("blocos vazios -> 0", 0, f("if (a > 0) { } if (a < 0) { }")),
    (f"blocos com MIN_INSTRUCOES - 1 = {MIN - 1} instruções -> 0", 0,
     f(f"if (a > 0) {{ {bloco_com(MIN - 1)} }} if (a < 0) {{ {bloco_com(MIN - 1)} }}")),
    (f"blocos com MIN_INSTRUCOES = {MIN} instruções -> 1", 1,
     f(f"if (a > 0) {{ {bloco_com(MIN)} }} if (a < 0) {{ {bloco_com(MIN)} }}")),
    # entre funções
    ("corpos de duas funções iguais -> 1", 1, f"void f(int a) {{ {X} }} void g(int a) {{ {X} }}"),
    ("duas funções iguais exceto no nome (corpo com 4 instruções) -> 1", 1,
     f"int f(int a) {{ a = a + 1; print(a); if (a > 2) {{ {X} }} return a; }} "
     f"int g(int a) {{ a = a + 1; print(a); if (a > 2) {{ {X} }} return a; }}"),
    ("duas funções iguais exceto no nome (corpo com 1 instrução, abaixo do mínimo) -> 1 (o bloco de dentro)", 1,
     f"void f(int a) {{ if (a > 0) {{ {X} }} }} void g(int a) {{ if (a > 0) {{ {X} }} }}"),
    ("bloco igual em duas funções -> 1", 1,
     f"void f(int a) {{ if (a > 0) {{ {X} }} }} void g(int a) {{ if (a < 5) {{ {X} }} }}"),
    ("then e else iguais -> 1 (o B2 também o deteta)", 1,
     f(f"if (a > 0) {{ {X} }} else {{ {X} }}")),
]

TD = (f(f"if (a > 0) {{ {X} }} if (a < 0) {{ {X} }}"), 30)

if __name__ == "__main__":
    if MIN > 4:
        print("Aviso: os casos usam blocos de 4 instruções; com MIN_INSTRUCOES > 4 vão falhar.\n")
    main(CODIGO, CASOS, TD)