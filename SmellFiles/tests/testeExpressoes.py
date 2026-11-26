"""Testa os smells de expressão A1-A7: deteção, refactoring e injeção.

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeExpressoes

Partes:
  1. deteção e refactoring num programa com todos os casos (contagens esperadas);
  2. injeção de cada A, em dois programas base limpos;
  3. injetar_varios;
  4. injeção aleatória (limite, deteção, refactoring, mesma seed, nunca dois
     smells no mesmo sítio, injetar num programa que já tem smells);
  5. os C que a injeção cria (só informação, não é erro).
"""
import sys
from collections import Counter

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, relatorio, imprime_relatorio, divida_tecnica
from projeto1.SDVM_lang.SmellFiles.smells.refactoring import corrigir
from projeto1.SDVM_lang.SmellFiles.smells.injecao import (
    injetar, injetar_varios, injetar_aleatorio, tem_smell, INJETAVEIS,
)
from projeto1.SDVM_lang.SmellFiles.smells.analise import contexto

A = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
falhas = 0


def verifica(descricao, ok, detalhe=""):
    global falhas
    falhas += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {descricao}" + (f"\n       {detalhe}" if detalhe and not ok else ""))


def contagens(prog, codigos=A):
    """{código: (ocorrências, corrigíveis)}"""
    achados = detetar(prog, codigos)
    total = Counter(c for c, _, _ in achados)
    corr = Counter(c for c, _, ok in achados if ok)
    return {c: (total[c], corr[c]) for c in codigos}


def detetados(prog, codigos):
    return {c: n for c, n in Counter(c for c, _, _ in detetar(prog, codigos)).items()}


# =====================================================================
# 1. Deteção e refactoring
# Tipos: a int, d double, c char, b bool, r int, g devolve int.
# =====================================================================
print("===== 1. deteção e refactoring =====")
codigo = """
int g(int x) { return x; }

int f(int a, double d, char c, bool b) {
    int r;
    r = a + 0;                 // A1
    r = 0 + a - 0;             // A1 x2
    r = (a * 1) / 1;           // A2 x2
    r = 1 * (a + 0);           // A2 + A1
    r = a * 0;                 // A3
    r = g(a) * 0;              // A3 NÃO corrigível (perdia a chamada)
    d = d * 0;                 // A3 (double tratado como número normal)
    print(c + 0);              // não é smell (char: c + 0 é int)
    if (b == true) { r = 1; }  // A4
    if (b != true) { r = 2; }  // A4 -> !b
    if (a == true) { r = 3; }  // não é smell, é um erro (a é int)
    if (!!b) { r = 4; }        // A5
    if (!!a) { r = 5; }        // não é smell (!!5 == 1: normaliza para 0/1)
    r = -(-a);                 // A5
    if (a == a) { r = 6; }     // A6 -> true
    if (a < a) { r = 7; }      // A6 -> false
    if (d == d) { r = 8; }     // A6 (double tratado como número normal)
    if (g(a) == g(a)) { r = 9; }  // A6 NÃO corrigível (impuro)
    r = (int)(int)d;           // A7 (só o de fora)
    r = (int)a;                // A7
    d = (double)d;             // A7
    r = (int)d;                // não é smell (conversão a sério)
    if (true == true) { r = 10; }  // A4 e A6 no mesmo nó
    return r + 0 + 0;          // A1 x2
}
"""
ESPERADO_ANTES = {"A1": (6, 6), "A2": (3, 3), "A3": (3, 2), "A4": (3, 3),
                  "A5": (2, 2), "A6": (5, 4), "A7": (3, 3)}
ESPERADO_DEPOIS = {"A1": (0, 0), "A2": (0, 0), "A3": (1, 0), "A4": (0, 0),
                   "A5": (0, 0), "A6": (1, 0), "A7": (0, 0)}

prog = program.parse(codigo)
imprime_relatorio(prog, A)
obtido = contagens(prog)
for c in A:
    verifica(f"antes: {c} = {ESPERADO_ANTES[c][0]} ({ESPERADO_ANTES[c][1]} corrigíveis)",
             obtido[c] == ESPERADO_ANTES[c], f"detetado {obtido[c][0]} ({obtido[c][1]} corrigíveis)")

limpo, aplicados = corrigir(prog, A)
print("refactorings aplicados:", dict(sorted(aplicados.items())))
obtido = contagens(limpo)
for c in A:
    verifica(f"depois: {c} = {ESPERADO_DEPOIS[c][0]}",
             obtido[c] == ESPERADO_DEPOIS[c], f"detetado {obtido[c][0]} ({obtido[c][1]} corrigíveis)")
verifica("pretty + parse do original dá a mesma árvore", program.parse(pretty(prog)) == prog)
verifica("pretty + parse do corrigido dá a mesma árvore", program.parse(pretty(limpo)) == limpo)
verifica("depois de corrigir só ficam não corrigíveis", all(not ok for _, _, ok in detetar(limpo, A)))
verifica("corrigir outra vez não muda nada", corrigir(limpo, A)[0] == limpo)


# =====================================================================
# 2. Injeção de cada A em dois programas limpos
# =====================================================================
BASE1 = program.parse("""
int v[10];

int soma(int n) {
    int s = 0;
    int i;
    bool fim = false;
    for (i = 0; i < n && !fim; i = i + 1) {
        s = s + v[i];
        if (s > 100) { fim = true; }
    }
    return (int)(s / 2.0);
}
""")

# com double, char, chamadas e parâmetros de vários tipos
BASE2 = program.parse("""
double media(double soma, int n) {
    double r = 0.0;
    if (n > 0) { r = soma / n; }
    return r;
}

int conta(char letra, bool maiusculas, int limite) {
    int total = 0;
    int pos = 0;
    bool fim = false;
    while (pos < limite && !maiusculas && !fim) {
        if (letra == 'a') { total = total + 1; }
        if (total > limite) { fim = true; }
        pos = pos + 1;
    }
    print(media(1.5, total));
    return total;
}
""")
BASES = [("base 1", BASE1), ("base 2", BASE2)]

print("\n===== 2. injeção de cada A =====")
for nome, base in BASES:
    verifica(f"{nome}: não tem smells A", sum(n for n, _ in contagens(base).values()) == 0,
             str(contagens(base)))
    for c in A:
        p, k = injetar(base, c, n=2, seed=7)
        det = detetados(p, [c]).get(c, 0)
        verifica(f"{nome}: injetar {c} x2 -> injetou {k}, detetou {det}, a correção desfaz",
                 k == 2 and det == k and program.parse(pretty(p)) == p and corrigir(p, [c])[0] == base,
                 f"injetou {k}, detetou {det}\n{pretty(p)}")

# literais neutros (0, 0.0, 1, 1.0): a injeção não os usa, porque 0 + 0.0
# desfazia-se em 0 e 1 * 1.0 em 1 (mudava o tipo)
NEUTROS = program.parse("""
double f(double d, int k) {
    d = 0.0;
    d = 1.0;
    k = 0;
    k = 1;
    return d + 0.5;
}
""")
for c in ["A1", "A2"]:
    maus = [seed for seed in range(30)
            if corrigir(injetar(NEUTROS, c, n=3, seed=seed)[0], [c])[0] != NEUTROS]
    verifica(f"literais neutros: injetar {c} x3 e corrigir volta ao original (30 seeds)", not maus,
             f"seeds que falham: {maus}")

# pedir mais do que os sítios que existem: injeta o que dá, sem erro
for c in ["A3", "A6"]:
    p, k = injetar(BASE1, c, n=50, seed=3)
    det = detetados(p, [c]).get(c, 0)
    verifica(f"base 1: injetar {c} x50 -> só há sítio para {k} (1 <= k < 50), todos detetados",
             1 <= k < 50 and det == k and corrigir(p, [c])[0] == BASE1, f"injetou {k}, detetou {det}")


# =====================================================================
# 3. injetar_varios
# =====================================================================
print("\n===== 3. injetar_varios =====")
for nome, base in BASES:
    pedido = {"A1": 3, "A4": 1, "A5": 2, "A7": 2}
    sujo, feitos = injetar_varios(base, pedido, seed=1)
    det = detetados(sujo, A)
    verifica(f"{nome}: injetados {feitos}, todos detetados",
             feitos == pedido and all(det.get(c, 0) == k for c, k in feitos.items()), f"detetados {det}")
    print(f"       TD: {divida_tecnica(sujo, A)} min")
    verifica(f"{nome}: a correção devolve o programa base", corrigir(sujo)[0] == base)


# =====================================================================
# 4. Injeção aleatória
# =====================================================================
def subnos(n):
    """Todos os nós dentro de n (sem o próprio)."""
    if isinstance(n, list):
        for x in n:
            yield x
            yield from subnos(x)
    elif hasattr(n, "__dataclass_fields__"):
        for v in vars(n).values():
            if hasattr(v, "__dataclass_fields__") or isinstance(v, list):
                yield v
                yield from subnos(v)


def sem_sobreposicao(p):
    ctx = contexto(p)
    nos = [n for c, n, _ in detetar(p) if c in INJETAVEIS]     # os só de reporte não contam
    return all(not any(tem_smell(d, ctx) for d in subnos(n)) for n in nos)


print("\n===== 4. injeção aleatória =====")
for nome, base in BASES:
    ok = True
    for seed in range(5):
        p, feitos = injetar_aleatorio(base, seed=seed, limite=2)
        det = detetados(p, INJETAVEIS)
        ok_seed = (all(0 <= k <= 2 for k in feitos.values())
                   and all(det.get(c, 0) == k for c, k in feitos.items())
                   and corrigir(p)[0] == base)
        if not ok_seed:
            print(f"       seed {seed}: injetados {feitos}, detetados {det}")
        ok = ok and ok_seed
    verifica(f"{nome}: 5 seeds com limite 2 -> limite respeitado, tudo detetado e desfeito", ok)

    a1, f1 = injetar_aleatorio(base, seed=42)
    a2, f2 = injetar_aleatorio(base, seed=42)
    verifica(f"{nome}: a mesma seed dá o mesmo programa", a1 == a2 and f1 == f2)

    maus = [s for s in range(200) if not sem_sobreposicao(injetar_aleatorio(base, seed=s)[0])]
    verifica(f"{nome}: 200 injeções aleatórias, nunca dois smells no mesmo sítio", not maus,
             f"seeds com sobreposição: {maus[:10]}")

# injetar por cima de um programa que já tem smells
sujo, _ = injetar_varios(BASE2, {"A1": 2, "A5": 1, "A6": 1}, seed=9)
antes = detetados(sujo, INJETAVEIS)
ok_contas, ok_sobrep, ok_corr = True, True, True
for seed in range(20):
    p, feitos = injetar_aleatorio(sujo, seed=seed, limite=2)
    det = detetados(p, INJETAVEIS)
    ok_contas &= all(det.get(c, 0) == antes.get(c, 0) + k for c, k in feitos.items())
    ok_sobrep &= sem_sobreposicao(p)
    ok_corr &= corrigir(p)[0] == BASE2
verifica("num programa já com smells: detetados = os que havia + os injetados (20 seeds)", ok_contas)
verifica("num programa já com smells: nunca dois smells no mesmo sítio (20 seeds)", ok_sobrep)
verifica("num programa já com smells: a correção devolve o programa base (20 seeds)", ok_corr)


# =====================================================================
# 5. C criados pela injeção (informação: os A3/A6 injetados podem trazer um
# literal 2..9, que é um C5; os C só são reportados, por isso não é erro)
# =====================================================================
print("\n===== 5. C criados pela injeção (informação) =====")
for nome, base in BASES:
    for c in ["A3", "A6"]:
        p, k = injetar(base, c, n=2, seed=7)
        c5_antes = detetados(base, ["C5"]).get("C5", 0)
        c5_depois = detetados(p, ["C5"]).get("C5", 0)
        td_a = sum(l[5] for l in relatorio(p, [c]))
        td_total = divida_tecnica(p) - divida_tecnica(base)
        print(f"     {nome}: {k} x {c} -> C5 {c5_antes} -> {c5_depois}; "
              f"TD dos {c} = {td_a} min, TD total subiu {td_total} min")

print("\n" + ("TUDO OK" if falhas == 0 else f"{falhas} FALHA(S)"))
sys.exit(1 if falhas else 0)