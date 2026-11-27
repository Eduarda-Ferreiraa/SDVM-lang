from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import (
    detetar, relatorio, imprime_relatorio, divida_tecnica,
)
from projeto1.SDVM_lang.SmellFiles.smells.refactoring import corrigir
from projeto1.SDVM_lang.SmellFiles.smells.injecao import injetar, injetar_varios

TODOS_B = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]

codigo = """
bool efeito(int x) {
    print(x);
    return x > 0;
}

int f(int a, bool flag) {
    int r = 0;

    // B1: condição constante
    if (true) { r = 1; }
    if (false) { r = 2; } else { r = 3; }
    while (false) { r = 4; }

    // B2: ramos iguais (puro vs. impuro)
    if (a > 0) { r = 5; } else { r = 5; }
    if (efeito(a)) { r = 6; } else { r = 6; }

    // B3: then vazio (sem else puro, sem else impuro, e com else)
    if (a > 1) { }
    if (efeito(a)) { }
    if (flag) { } else { r = 7; }

    // B4: else vazio
    if (a > 2) { r = 8; } else { }

    // B5: ramos booleanos
    if (a > 3) { flag = true; } else { flag = false; }

    // B6: if redundante
    if (a > 0) {
        if (flag) {
            r = 9;
        }
    }

    // B7: bloco redundante (sem declarações) vs. bloco com declaração (mantém-se)
    {
        r = 10;
    }
    {
        int local = 20;
        r = local;
    }

    // B8: código inalcançável após return
    return r;
    r = 999;
}
"""

prog = program.parse(codigo)

print("=== ANTES (GRUPO B) ===")
imprime_relatorio(prog, TODOS_B)

limpo, aplicados = corrigir(prog, TODOS_B)
print("\nrefactorings aplicados:", dict(aplicados))
print("\n=== DEPOIS (GRUPO B) ===")
imprime_relatorio(limpo, TODOS_B)
print()
print(pretty(limpo))

# 1. Pretty-printer fiel e AST válida
assert program.parse(pretty(prog)) == prog
assert program.parse(pretty(limpo)) == limpo

# 2. Depois do refactoring só sobram os 2 casos não corrigíveis (B2 e B3 com efeito(a))
nao_corrigiveis = [(c, ok) for c, _, ok in detetar(limpo, TODOS_B)]
assert nao_corrigiveis == [("B2", False), ("B3", False)], nao_corrigiveis

# 3. Idempotência
assert corrigir(limpo, TODOS_B)[0] == limpo

# ---------------------------------------------------------------------
# Injeção num programa limpo (B1 a B8)
# ---------------------------------------------------------------------
limpo_src = """
int calcula(int n, bool ativo) {
    int total = 0;
    if (ativo && n > 0) {
        total = n + 1;
    }
    if (n > 10) {
        total = total + 5;
    }
    return total == 6;
}
"""
base = program.parse(limpo_src)

for c in TODOS_B:
    p, k = injetar(base, c, n=1, seed=7)
    contagem = {cod: n for cod, _, n, *_ in relatorio(p)}
    print(f"injetar {c} -> injetados {k}, detetados {c}: {contagem[c]}")
    assert program.parse(pretty(p)) == p
    assert contagem[c] == k
    # A refatoração completa desfaz a injeção (incluindo B3 + A5)
    assert corrigir(p)[0] == base, c

sujo, feitos = injetar_varios(base, {"B1": 1, "B4": 1, "B5": 1, "B7": 1, "B8": 1}, seed=3)
det = {c: n for c, _, n, *_ in relatorio(sujo)}
assert all(det[c] == k for c, k in feitos.items()), (det, feitos)
assert corrigir(sujo)[0] == base
print("TD injetado:", divida_tecnica(sujo), "min")
print("\nOK - todos os testes do Grupo B passaram")
