# =====================================================================
# Deteção e relatório (full_tdTU)
# =====================================================================
# Cada smell é uma worker   failTU `adhocTU` deteta_X
# e as workers juntam-se com seqTU (aplica as duas e concatena as listas).
# Não se usa a cadeia adhocTU(adhocTU(failTU, s1), s2): o adhocTU é uma
# escolha (o 1.º que acerta ganha) e há nós com dois smells, ex.:
# true == true (A4 e A6), que contariam como um só.

from collections import Counter
from functools import reduce

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from .analise import falha, contexto
from .catalogo import seleciona


def corrigivel(s, n, ctx) -> bool:
    if s.corrige is None:
        return False
    try:
        s.corrige(n, ctx)
        return True
    except st.StrategicError:
        return False


def worker(s, ctx):
    """failTU `adhocTU` deteta  ->  [(código, nó, corrigível)] ou []"""
    def g(n):
        if not s.deteta(n, ctx):
            falha()
        return [(s.codigo, n, corrigivel(s, n, ctx))]
    return lambda z: st.adhocTU(st.failTU, g, z)


def junta(f, g):
    """f `seqTU` g"""
    return lambda z: st.seqTU(f, g, z)


def detetar(prog, codigos=None):
    """[(código, nó, corrigível)] por ordem de travessia."""
    ctx = contexto(prog)
    passo = reduce(junta, [worker(s, ctx) for s in seleciona(codigos)], st.failTU)
    return st.full_tdTU(passo, toZipper(prog))


def relatorio(prog, codigos=None):
    """[(código, nome, ocorrências, corrigíveis, custo unitário, TD em minutos)]"""
    achados = detetar(prog, codigos)
    total = Counter(c for c, _, _ in achados)
    corr = Counter(c for c, _, ok in achados if ok)
    return [(s.codigo, s.nome, total[s.codigo], corr[s.codigo], s.custo_min,
             total[s.codigo] * s.custo_min)
            for s in seleciona(codigos)]


def divida_tecnica(prog, codigos=None) -> int:
    """TD = soma de ocorrências x custo de remediação (minutos)."""
    return sum(td for *_, td in relatorio(prog, codigos))


def imprime_relatorio(prog, codigos=None):
    linhas = relatorio(prog, codigos)
    print(f"{'':4}{'smell':<30}{'ocorr.':>7}{'corrig.':>9}{'min/oc.':>9}{'TD (min)':>10}")
    for c, nome, n, ok, custo, td in linhas:
        print(f"{c:<4}{nome:<30}{n:>7}{ok:>9}{custo:>9}{td:>10}")
    print(f"{'':4}{'total':<30}{sum(l[2] for l in linhas):>7}"
          f"{sum(l[3] for l in linhas):>9}{'':>9}{sum(l[5] for l in linhas):>10}")