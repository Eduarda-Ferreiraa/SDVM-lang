"""Testa as métricas novas: Halstead e metricas_por_funcao.

Os valores esperados foram contados à mão com a convenção do metricas.py
(ver o comentário do Halstead). Em cada caso estão escritos os operadores e
os operandos contados, para se poder conferir.

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeMetricas
"""
import sys

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.metricas import halstead, metricas_por_funcao

falhas = 0


def verifica(descricao, ok, detalhe=""):
    global falhas
    falhas += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {descricao}" + (f"\n       {detalhe}" if detalhe and not ok else ""))


def arredonda(h):
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in h.items()}


# (descrição, programa, n1, n2, N1, N2, volume, dificuldade, esforço)
CASOS = [
    ("atribuição e expressão",
     # operadores: = (decl.)  = + * print                -> n1 = 4, N1 = 5
     # operandos:  f a b x 0 x a b 2 x                    -> n2 = 6, N2 = 10
     "void f(int a, int b) { int x = 0; x = a + b * 2; print(x); }",
     4, 6, 5, 10, 49.829, 3.667, 182.706),

    ("if/else, return e - unário",
     # operadores: if else > return - unário return       -> n1 = 5, N1 = 6
     # operandos:  g n n 0 n n                            -> n2 = 3, N2 = 6
     "int g(int n) { if (n > 0) { return -n; } else { return n; } }",
     5, 3, 6, 6, 36.0, 4.5, 162.0),

    ("arrays, ciclos, read, break, cast e chamada",
     # operadores (22): = read [] = while > = - if == break for = < = + print [] return (double) print ()
     #   distintos (16): = read [] while > - if == break for < + print return (double) ()
     # operandos (31): v 3 1 2 3 | h k | k | v 0 k | k 0 | k k 1 | k 2 | i 0 i 3 i i 1 | v i | k | main h 1
     #   distintos (9): v 3 1 2 h k 0 i main
     """
     int v[3] = {1, 2, 3};
     double h(int k) {
         read(k);
         v[0] = k;
         while (k > 0) {
             k = k - 1;
             if (k == 2) { break; }
         }
         for (int i = 0; i < 3; i = i + 1) {
             print(v[i]);
         }
         return (double) k;
     }
     void main() { print(h(1)); }
     """,
     16, 9, 22, 31, 246.124, 11.444, 2816.757),

    ("literais de tipos diferentes são operandos diferentes",
     # operadores: = (decl.) = print print print           -> n1 = 2, N1 = 5
     # operandos:  m b c 'a' b true "ola" 1.0 1            -> n2 = 8, N2 = 9
     'void m(bool b) { char c = \'a\'; b = true; print("ola"); print(1.0); print(1); }',
     2, 8, 5, 9, 46.507, 2.125, 98.827),

    ("função vazia (V = 0, sem divisão por zero)",
     # operadores: nenhum; operandos: f                   -> n1 = 0, N1 = 0, n2 = 1, N2 = 1
     "void f() { }",
     0, 1, 0, 1, 0.0, 1.0, 0.0),

    ("negação !",
     # operadores: return !                                -> n1 = 2, N1 = 2
     # operandos:  t a a                                   -> n2 = 2, N2 = 3
     "bool t(bool a) { return !a; }",
     2, 2, 2, 3, 10.0, 2.5, 25.0),

    ("- unário e - binário são operadores diferentes",
     # operadores: return - unário -                       -> n1 = 3, N1 = 3
     # operandos:  u a a a                                 -> n2 = 2, N2 = 4
     "int u(int a) { return -a - a; }",
     3, 2, 3, 4, 16.253, 3.5, 56.887),
]


print("===== Halstead =====")
for descricao, src, n1, n2, N1, N2, V, D, E in CASOS:
    try:
        h = arredonda(halstead(program.parse(src)))
    except Exception as e:
        falhas += 1
        print(f"ERRO {descricao}\n       {type(e).__name__}: {e}")
        continue
    esperado = {"n1": n1, "n2": n2, "N1": N1, "N2": N2,
                "vocabulario": n1 + n2, "comprimento": N1 + N2,
                "volume": V, "dificuldade": D, "esforco": E}
    diferentes = {k: (esperado[k], h.get(k)) for k in esperado if esperado[k] != h.get(k)}
    verifica(descricao, not diferentes, f"(esperado, obtido): {diferentes}")

# o Halstead não depende da formatação: o pretty do programa dá o mesmo
src = CASOS[2][1]
p = program.parse(src)
verifica("o mesmo Halstead no programa original e no pretty dele",
         halstead(p) == halstead(program.parse(pretty(p))))


print("\n===== metricas_por_funcao =====")
prog = program.parse("""
int g(int n) { if (n > 0) { return -n; } else { return n; } }
void f(int a, int b) { int x = 0; x = a + b * 2; print(x); }
""")
fs = metricas_por_funcao(prog)
verifica("uma entrada por função, pela ordem do programa", [m["nome"] for m in fs] == ["g", "f"],
         str([m["nome"] for m in fs]))
if len(fs) == 2:
    g, f = fs
    # g: if + 2 returns = 3 instruções, 1 if, 0 ciclos, profundidade 1, CC = 1 + 1 if
    esperado_g = {"parametros": 1, "instrucoes": 3, "ifs": 1, "ciclos": 0,
                  "profundidade": 1, "complexidade_ciclomatica": 2}
    obtido_g = {k: g[k] for k in esperado_g}
    verifica("g: parâmetros, instruções, ifs, ciclos, profundidade, CC", obtido_g == esperado_g,
             f"esperado {esperado_g}, obtido {obtido_g}")
    # f: declaração + atribuição + print = 3 instruções, sem ifs nem ciclos, CC = 1
    esperado_f = {"parametros": 2, "instrucoes": 3, "ifs": 0, "ciclos": 0,
                  "profundidade": 0, "complexidade_ciclomatica": 1}
    obtido_f = {k: f[k] for k in esperado_f}
    verifica("f: parâmetros, instruções, ifs, ciclos, profundidade, CC", obtido_f == esperado_f,
             f"esperado {esperado_f}, obtido {obtido_f}")
    # o Halstead de cada função é o mesmo que o da função num programa sozinha
    verifica("g: Halstead igual ao da função sozinha",
             g["halstead"] == halstead(program.parse(CASOS[1][1])))
    verifica("f: Halstead igual ao da função sozinha",
             f["halstead"] == halstead(program.parse(CASOS[0][1])))

verifica("programa sem funções -> lista vazia", metricas_por_funcao(program.parse("int g = 0;")) == [])

print("\n" + ("TUDO OK" if falhas == 0 else f"{falhas} FALHA(S)"))
sys.exit(1 if falhas else 0)