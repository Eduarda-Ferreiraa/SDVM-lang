"""Demonstração para a apresentação (1.ª versão).

Para cada programa de exemplos_demo.py mostra:
  1. o código;
  2. os smells (relatório) e o TD;
  3. as métricas por função e o Halstead do programa;
  4. o refactoring: o que foi aplicado, o código corrigido, os smells e o TD
     depois, e as métricas antes/depois;
  5. uma injeção aleatória de smells e a correção a desfazê-la.

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.demo.demo                    # todos
    python3 -m projeto1.SDVM_lang.SmellFiles.demo.demo stock              # só um
    python3 -m projeto1.SDVM_lang.SmellFiles.demo.demo stock --seed 3     # outros sítios
    python3 -m projeto1.SDVM_lang.SmellFiles.demo.demo --aleatorio        # tipos sorteados
    python3 -m projeto1.SDVM_lang.SmellFiles.demo.demo --com-b            # injeta também B

Injeção: por omissão injeta UM smell de cada tipo (A1..A7), em sítios
escolhidos ao acaso (injetar_varios), para se verem todas as categorias.
Com --aleatorio usa o injetar_aleatorio (sorteia os tipos e quantos de cada).
A seed por omissão é diferente em cada programa; --seed N fixa-a.

Quando o relatorio.py (Membro 1) estiver pronto, a parte do TD passa a usar o
relatorio.imprime / divida.resumo_td: ver as marcas PROVISÓRIO.
"""
import sys

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, imprime_relatorio, divida_tecnica
from projeto1.SDVM_lang.SmellFiles.smells.refactoring import corrigir
from projeto1.SDVM_lang.SmellFiles.smells.injecao import injetar_aleatorio, injetar_varios
from projeto1.SDVM_lang.SmellFiles.smells.metricas import loc, halstead, metricas_por_funcao
from projeto1.SDVM_lang.SmellFiles.demo.exemplos_demo import DEMOS

A = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
B = ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]

# PROVISÓRIO: conversões do TD; vão passar a vir do divida.py (Membro 1)
EUROS_POR_MIN = 1500 / 176 / 60
MIN_POR_LOC = 28.8
GRELHA = [(0.05, "A"), (0.10, "B"), (0.20, "C"), (0.50, "D")]


def resumo_td(prog):
    td = divida_tecnica(prog)
    racio = td / (loc(prog) * MIN_POR_LOC)
    classe = next((c for limite, c in GRELHA if racio <= limite), "E")
    return {"min": td, "h": td / 60, "eur": td * EUROS_POR_MIN, "racio": racio, "classe": classe}


# ---------------------------------------------------------------------

def titulo(texto):
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def secao(texto):
    print(f"\n--- {texto} " + "-" * (73 - len(texto)))


def mostra_codigo(prog):
    for i, linha in enumerate(pretty(prog).splitlines(), 1):
        print(f"{i:3}  {linha}")


def mostra_metricas(prog):
    print(f"{'função':<16}{'par.':>5}{'instr.':>7}{'ifs':>5}{'ciclos':>7}{'prof.':>6}{'CC':>4}"
          f"{'volume':>9}{'esforço':>10}")
    for m in metricas_por_funcao(prog):
        h = m["halstead"]
        print(f"{m['nome']:<16}{m['parametros']:>5}{m['instrucoes']:>7}{m['ifs']:>5}{m['ciclos']:>7}"
              f"{m['profundidade']:>6}{m['complexidade_ciclomatica']:>4}{h['volume']:>9.1f}{h['esforco']:>10.1f}")
    h = halstead(prog)
    print(f"\nHalstead do programa: n1={h['n1']} n2={h['n2']} N1={h['N1']} N2={h['N2']}  "
          f"vocabulário={h['vocabulario']} comprimento={h['comprimento']}  "
          f"V={h['volume']:.1f} D={h['dificuldade']:.2f} E={h['esforco']:.1f}")


def mostra_comparacao(antes, depois):
    ta, td = resumo_td(antes), resumo_td(depois)
    ha, hd = halstead(antes), halstead(depois)
    linhas = [
        ("LOC", loc(antes), loc(depois), "{}"),
        ("smells", len(detetar(antes)), len(detetar(depois)), "{}"),
        ("TD (min)", ta["min"], td["min"], "{}"),
        ("TD (h)", ta["h"], td["h"], "{:.2f}"),
        ("TD (€)", ta["eur"], td["eur"], "{:.2f}"),
        ("rácio", ta["racio"] * 100, td["racio"] * 100, "{:.2f} %"),
        ("classificação", ta["classe"], td["classe"], "{}"),
        ("Halstead V", ha["volume"], hd["volume"], "{:.1f}"),
        ("Halstead E", ha["esforco"], hd["esforco"], "{:.1f}"),
    ]
    print(f"{'':<16}{'antes':>12}{'depois':>12}")
    for nome, a, d, fmt in linhas:
        print(f"{nome:<16}{fmt.format(a):>12}{fmt.format(d):>12}")


def demo(nome, src, seed, aleatorio=False, tipos=A):
    prog = program.parse(src)

    titulo(f"PROGRAMA: {nome}")
    secao("código")
    mostra_codigo(prog)

    secao("smells antes do refactoring")
    imprime_relatorio(prog, so_encontrados=True)
    t = resumo_td(prog)
    print(f"\nTD: {t['min']} min = {t['h']:.2f} h = {t['eur']:.2f} €   "
          f"rácio {t['racio'] * 100:.2f} %   classificação {t['classe']}")

    secao("métricas por função (antes)")
    mostra_metricas(prog)

    corrigido, aplicados = corrigir(prog)
    secao("refactoring")
    print("aplicados:", ", ".join(f"{c} x{n}" for c, n in sorted(aplicados.items())))
    print()
    mostra_codigo(corrigido)

    secao("smells depois do refactoring (sobram os não corrigíveis e os só de reporte)")
    imprime_relatorio(corrigido, so_encontrados=True)

    secao("antes / depois")
    mostra_comparacao(prog, corrigido)

    if aleatorio:
        secao(f"injeção aleatória no programa corrigido (seed {seed}, tipos sorteados, até 2 de cada)")
        injetado, feitos = injetar_aleatorio(corrigido, seed=seed, limite=2, tipos=tipos)
    else:
        secao(f"injeção no programa corrigido: um de cada tipo, sítios ao acaso (seed {seed})")
        injetado, feitos = injetar_varios(corrigido, {c: 1 for c in tipos}, seed=seed)
    print("injetados:", ", ".join(f"{c} x{n}" for c, n in sorted(feitos.items()) if n))
    sem_sitio = [c for c, n in sorted(feitos.items()) if n == 0]
    if sem_sitio:
        print("sem sítio onde injetar:", ", ".join(sem_sitio))
    print()
    mostra_codigo(injetado)
    print()
    imprime_relatorio(injetado, tipos, so_encontrados=True)
    volta = corrigir(injetado)[0] == corrigido
    print(f"\ncorrigir o injetado devolve o programa corrigido: {'sim' if volta else 'NÃO'}")


def main():
    args = sys.argv[1:]
    seed = None
    if "--seed" in args:
        i = args.index("--seed")
        seed = int(args[i + 1])
        del args[i:i + 2]
    aleatorio = "--aleatorio" in args
    tipos = A + B if "--com-b" in args else A
    escolhidos = [a for a in args if not a.startswith("--")]
    for k, (nome, src, *_) in enumerate(DEMOS):
        if not escolhidos or nome in escolhidos:
            demo(nome, src, seed if seed is not None else 7 + k, aleatorio, tipos)


if __name__ == "__main__":
    main()