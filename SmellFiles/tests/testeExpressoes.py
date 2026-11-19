from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, relatorio, imprime_relatorio, divida_tecnica
from projeto1.SDVM_lang.SmellFiles.smells.refactoring import corrigir
from projeto1.SDVM_lang.SmellFiles.smells.injecao import injetar, injetar_varios, injetar_aleatorio, tem_smell
from projeto1.SDVM_lang.SmellFiles.smells.analise import contexto

codigo = """
int g(int x) { return x; }

int f(int a, double d, char c, bool b) {
    int r;
    r = a + 0;                 // A1
    r = 0 + a - 0;             // A1 x2
    r = (a * 1) / 1;           // A2 x2
    r = 1 * (a + 0);           // A2 + A1
    r = a * 0;                 // A3 corrigível
    r = g(a) * 0;              // A3 NÃO corrigível (perde a chamada)
    d = d * 0;                 // A3 NÃO corrigível (NaN * 0)
    print(c + 0);              // A1 NÃO corrigível (c + 0 é int)
    if (b == true) { r = 1; }  // A4
    if (b != true) { r = 2; }  // A4 -> !b
    if (a == true) { r = 3; }  // A4 NÃO corrigível (a é int)
    if (!!b) { r = 4; }        // A5
    if (!!a) { r = 5; }        // A5 NÃO corrigível (!!5 == 1)
    r = -(-a);                 // A5
    if (a == a) { r = 6; }     // A6 -> true
    if (a < a) { r = 7; }      // A6 -> false
    if (d == d) { r = 8; }     // A6 NÃO corrigível (double)
    if (g(a) == g(a)) { r = 9; }  // A6 NÃO corrigível (impuro)
    r = (int)(int)d;           // A7 (o de fora)
    r = (int)a;                // A7
    d = (double)d;             // A7
    r = (int)d;                // não é smell
    if (true == true) { r = 10; }  // A4 e A6 no mesmo nó
    return r + 0 + 0;          // A1 x2
}
"""

prog = program.parse(codigo)

print("=== ANTES ===")
imprime_relatorio(prog)

limpo, aplicados = corrigir(prog)
print("\nrefactorings aplicados:", dict(aplicados))
print("\n=== DEPOIS ===")
imprime_relatorio(limpo)
print()
print(pretty(limpo))

# o resultado é código válido e o pretty-printer é fiel
assert program.parse(pretty(prog)) == prog
assert program.parse(pretty(limpo)) == limpo
# depois do refactoring só ficam os não corrigíveis
assert all(not ok for _, _, ok in detetar(limpo))
# idempotência
assert corrigir(limpo)[0] == limpo

# ---------------------------------------------------------------------
# Injeção num programa limpo
# ---------------------------------------------------------------------
limpo_src = """
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
"""
base = program.parse(limpo_src)
print("=== programa base ===")
imprime_relatorio(base)

for c in ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]:
    p, k = injetar(base, c, n=2, seed=7)
    contagem = {cod: n for cod, _, n, *_ in relatorio(p)}
    print(f"injetar {c} x2 -> injetados {k}, detetados {c}: {contagem[c]}")
    assert program.parse(pretty(p)) == p
    assert contagem[c] == k
    # o refactoring desfaz a injeção
    assert corrigir(p, [c])[0] == base, c

sujo, feitos = injetar_varios(base, {"A1": 3, "A4": 1, "A5": 2, "A7": 2}, seed=1)
print("\ninjetar_varios:", feitos)
print(pretty(sujo))
imprime_relatorio(sujo)
det = {c: n for c, _, n, *_ in relatorio(sujo)}
assert all(det[c] == k for c, k in feitos.items()), (det, feitos)
print("TD:", divida_tecnica(sujo), "min")
assert corrigir(sujo)[0] == base
print("\nOK - todos os testes passaram")

# ---------------------------------------------------------------------
# Injeção aleatória
# ---------------------------------------------------------------------


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


print("\n=== injeção aleatória ===")
for seed in range(3):
    p, feitos = injetar_aleatorio(base, seed=seed, limite=2)
    det = {c: n for c, _, n, *_ in relatorio(p)}
    print(f"seed {seed}: injetados {feitos}")
    assert all(1 <= k <= 2 for k in feitos.values())            # limite
    assert all(det[c] == k for c, k in feitos.items())         # tudo detetado
    assert corrigir(p)[0] == base                           # e desfeito
print()
print(pretty(p))

# nunca dois smells no mesmo sítio: nenhum nó com smell contém outro
for seed in range(200):
    p, _ = injetar_aleatorio(base, seed=seed)
    ctx = contexto(p)
    nos = [n for _, n, _ in detetar(p)]
    for n in nos:
        assert not any(tem_smell(d, ctx) for d in subnos(n)), (seed, n)
print("200 injeções aleatórias: nunca dois smells no mesmo sítio")
print("\nOK - injeção aleatória")