"""Testa os smells sobre programas reais (por omissão: examples/ e ParserFiles/tests/valid/).

Para cada programa verifica propriedades que têm de valer sempre:
  1. pretty-printer fiel:  parse(pretty(P)) == P
  2. depois do refactoring não fica nenhum smell corrigível
  3. o refactoring é idempotente:  corrigir(corrigir(P)) == corrigir(P)
  4. com injeções aleatórias (várias seeds):
       - a deteção encontra exatamente os smells injetados (a mais do que P já tinha)
       - corrigir(injetado) == corrigir(P)   (o refactoring desfaz a injeção)
       - o programa injetado continua a ser código válido

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeProgramas
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeProgramas outra/pasta   # + outras pastas
"""
import glob
import os
import sys
from collections import Counter

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar
from projeto1.SDVM_lang.SmellFiles.smells.refactoring import corrigir
from projeto1.SDVM_lang.SmellFiles.smells.injecao import injetar_aleatorio

AQUI = os.path.dirname(os.path.abspath(__file__))                 # .../SmellFiles/tests
SDVM = os.path.normpath(os.path.join(AQUI, "..", ".."))            # .../SDVM_lang
PASTAS = [os.path.join(SDVM, "examples"), os.path.join(SDVM, "ParserFiles", "tests", "valid")]
SEEDS = range(10)


def contagem(p):
    return Counter(c for c, _, _ in detetar(p))


def testa(caminho):
    erros = []
    with open(caminho, encoding="utf-8", newline="") as f:
        p = program.parse(f.read())

    if program.parse(pretty(p)) != p:
        erros.append("pretty: parse(pretty(P)) != P")

    limpo, _ = corrigir(p)
    if any(ok for _, _, ok in detetar(limpo)):
        erros.append("refactoring: ficaram smells corrigíveis")
    if corrigir(limpo)[0] != limpo:
        erros.append("refactoring: não é idempotente")

    antes = contagem(p)
    for seed in SEEDS:
        sujo, feitos = injetar_aleatorio(p, seed=seed, limite=3)
        if program.parse(pretty(sujo)) != sujo:
            erros.append(f"seed {seed}: programa injetado não volta a ser lido")
        depois = contagem(sujo)
        for c, k in feitos.items():
            if depois[c] - antes[c] != k:
                erros.append(f"seed {seed}: injetados {k} de {c}, detetados {depois[c] - antes[c]} a mais")
        if corrigir(sujo)[0] != limpo:
            erros.append(f"seed {seed}: corrigir(injetado) != corrigir(P)")
    return erros, sum(antes.values())


def main():
    pastas = PASTAS + sys.argv[1:]
    falhas = total = 0
    for pasta in pastas:
        ficheiros = sorted(f for f in glob.glob(os.path.join(pasta, "*")) if os.path.isfile(f))
        if not ficheiros:
            print(f"FAIL sem ficheiros em {pasta}")
            falhas += 1
            continue
        print(f"\n== {pasta}")
        for f in ficheiros:
            total += 1
            try:
                erros, n_smells = testa(f)
            except Exception as e:                  # inclui erros de parse
                erros, n_smells = [f"{type(e).__name__}: {str(e)[:100]}"], 0
            falhas += bool(erros)
            print(f"  {'OK  ' if not erros else 'FAIL'} {os.path.basename(f)}  ({n_smells} smells)")
            for e in erros[:5]:
                print(f"         {e}")
    print(f"\n{total} programas, " + ("TUDO OK" if falhas == 0 else f"{falhas} FALHA(S)"))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()