"""Confirma os programas de demonstração (demo/exemplos_demo.py).

Para cada programa:
  1. o parser aceita-o e o pretty devolve a mesma árvore;
  2. as contagens de cada smell (todo o catálogo: A, B e C) antes de corrigir;
  3. o TD antes (contagens esperadas x custos do catálogo);
  4. as contagens e o TD depois de corrigir;
  5. o programa corrigido é válido e corrigir outra vez não muda nada;
  6. injetar smells A no programa corrigido e corrigir volta ao mesmo.

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeDemo
"""
import sys
from collections import Counter

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, divida_tecnica
from projeto1.SDVM_lang.SmellFiles.smells.refactoring import corrigir
from projeto1.SDVM_lang.SmellFiles.smells.injecao import injetar_aleatorio
from projeto1.SDVM_lang.SmellFiles.smells.catalogo import CATALOGO
from projeto1.SDVM_lang.SmellFiles.demo.exemplos_demo import DEMOS

CODIGOS = [s.codigo for s in CATALOGO]
CUSTO = {s.codigo: s.custo_min for s in CATALOGO}
A = [c for c in CODIGOS if c.startswith("A")]


def contagens(prog):
    achados = detetar(prog)
    total = Counter(c for c, _, _ in achados)
    corr = Counter(c for c, _, ok in achados if ok)
    return {c: ((total[c], corr[c]) if c in A else total[c]) for c in CODIGOS}


def normaliza(esperado):
    return {c: esperado.get(c, (0, 0) if c in A else 0) for c in CODIGOS}


def td_de(esperado):
    return sum((v[0] if c in A else v) * CUSTO[c] for c, v in esperado.items())


def compara(titulo, esperado, obtido):
    falhas = 0
    linhas = []
    for c in CODIGOS:
        e, o = esperado[c], obtido[c]
        if e == o and e in ((0, 0), 0):
            continue
        ok = e == o
        falhas += not ok
        fmt = (lambda v: f"{v[0]} ({v[1]} corr.)") if c in A else str
        linhas.append(f"     {c:<5}{fmt(e):>13}{fmt(o):>13}  {'OK' if ok else 'FAIL'}")
    print(f"   {titulo}: {'OK' if not falhas else f'{falhas} FALHA(S)'}")
    print(f"     {'smell':<5}{'esperado':>13}{'detetado':>13}")
    print("\n".join(linhas))
    return falhas


def verifica(descricao, ok, detalhe=""):
    print(f"   {'OK  ' if ok else 'FAIL'} {descricao}" + (f"  {detalhe}" if detalhe and not ok else ""))
    return 0 if ok else 1


def correr(nome, src, antes, depois):
    print(f"===== {nome} =====")
    try:
        p = program.parse(src)
    except Exception as e:
        print(f"   ERRO no parse: {type(e).__name__}: {e}\n")
        return 1
    falhas = verifica("pretty + parse do original dá a mesma árvore", program.parse(pretty(p)) == p)

    antes, depois = normaliza(antes), normaliza(depois)
    falhas += compara("antes de corrigir", antes, contagens(p))
    td = divida_tecnica(p)
    falhas += verifica(f"TD antes = {td_de(antes)} min", td == td_de(antes), f"(detetado {td})")

    corrigido, aplicados = corrigir(p)
    print(f"   refactorings aplicados: {dict(sorted(aplicados.items()))}")
    falhas += compara("depois de corrigir", depois, contagens(corrigido))
    td = divida_tecnica(corrigido)
    falhas += verifica(f"TD depois = {td_de(depois)} min", td == td_de(depois), f"(detetado {td})")

    try:
        ok = program.parse(pretty(corrigido)) == corrigido
    except Exception:
        ok = False
    falhas += verifica("pretty + parse do corrigido dá a mesma árvore", ok)
    falhas += verifica("corrigir outra vez não muda nada", corrigir(corrigido)[0] == corrigido)

    voltas = [corrigir(injetar_aleatorio(corrigido, seed=s, limite=2, tipos=A)[0])[0] == corrigido
              for s in range(5)]
    falhas += verifica("injetar A no corrigido e corrigir volta ao mesmo (5 seeds)", all(voltas),
                       f"(seeds que falham: {[s for s, ok in enumerate(voltas) if not ok]})")

    if falhas:
        print("\n   programa corrigido:")
        print("\n".join("     " + l for l in pretty(corrigido).splitlines()))
    print(f"--> {'TUDO OK' if falhas == 0 else f'{falhas} FALHA(S)'}\n")
    return falhas


total = sum(correr(*d) for d in DEMOS)
print("TUDO OK" if total == 0 else f"{total} FALHA(S) NO TOTAL")
sys.exit(1 if total else 0)
