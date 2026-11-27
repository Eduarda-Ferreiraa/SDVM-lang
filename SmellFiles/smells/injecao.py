# =====================================================================
# Injeção (full_buTP + adhocTPZ)
# =====================================================================
# Para injetar n ocorrências de um smell, uma de cada vez:
#   1. contar os sítios elegíveis (TU: recolhe um 1 por sítio)
#   2. escolher um índice k ao acaso
#   3. percorrer a árvore (full_buTP) a contar e injetar no k-ésimo sítio
#   4. repetir sobre a árvore já alterada
# Em 1 só interessa quantos são, não a ordem, por isso basta uma TU.
# Em 3, bottom-up: o nó acabado de injetar não é revisitado.
#
# Um sítio é elegível se:
#   - não se sobrepõe a um smell que já existe (regra comum, aqui), e
#   - cumpre as condições do próprio smell (o seu injeta_X).

import random

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from .analise import falha, contexto
from .analise_c import recolhe, recolhe_z
from .catalogo import CATALOGO, POR_CODIGO

INJETAVEIS = [s.codigo for s in CATALOGO if s.injeta is not None]


# ---------------------------------------------------------------------
# Regra comum: nunca dois smells no mesmo sítio
# ---------------------------------------------------------------------

def tem_smell(n, ctx) -> bool:
    """Só contam os smells injetáveis: os "só de reporte" (ex.: C2 lista
    longa de parâmetros) descrevem a função inteira, não um sítio dela, e
    não devem impedir injeções lá dentro."""
    return any(s.deteta(n, ctx) for s in CATALOGO if s.injeta is not None)


def contem_smell(n, ctx) -> bool:
    """n, ou algum nó dentro de n, tem um smell?
    (full_tdTU e não once_tdTP: ver puro em analise.py)"""
    def g(m):
        return [m] if tem_smell(m, ctx) else falha()
    return recolhe(g, n) != []


def em_smell(z, ctx) -> bool:
    """O sítio sobrepõe-se a um smell: no nó, dentro dele ou num antecessor?"""
    return (contem_smell(z.node(), ctx)
            or z.ancestor(lambda u: tem_smell(u.node(), ctx)) is not None)


# ---------------------------------------------------------------------
# As duas passagens
# ---------------------------------------------------------------------

def injetado(smell, no, z, ctx):
    """O nó com o smell injetado; falha se o sítio não é elegível."""
    if em_smell(z, ctx):
        falha()
    return smell.injeta(no, z, ctx)                 # raise se não é elegível


def worker(smell, ctx, f):
    """adhocTPZ: nos sítios elegíveis aplica f ao nó com o smell injetado."""
    return lambda z: st.adhocTPZ(st.idTP, lambda no, zz: f(injetado(smell, no, zz, ctx)), z)


def contar_elegiveis(prog, codigo, ctx=None) -> int:
    """TU: um [1] por sítio elegível; o total é o tamanho da lista."""
    ctx = ctx or contexto(prog)
    smell = POR_CODIGO[codigo]
    return len(recolhe_z(lambda no, z: [1] if injetado(smell, no, z, ctx) is not None else [], prog))


def injetar_um(prog, codigo, k, ctx):
    """Injeta o smell no k-ésimo sítio elegível (a contar de 0)."""
    i = 0
    def injeta(novo):
        nonlocal i
        i += 1
        if i - 1 != k:
            falha()                                 # elegível, mas não é o escolhido
        return novo
    return st.full_buTP(worker(POR_CODIGO[codigo], ctx, injeta), toZipper(prog)).node()


# ---------------------------------------------------------------------
# Funções para usar
# ---------------------------------------------------------------------

def injetar(prog, codigo, n=1, seed=None):
    """Injeta até n ocorrências do smell em sítios diferentes (menos, se os
    sítios acabarem). Devolve (programa novo, nº injetado)."""
    ctx = contexto(prog, seed)
    feitos = 0
    for _ in range(n):
        total = contar_elegiveis(prog, codigo, ctx)
        if total == 0:
            break
        prog = injetar_um(prog, codigo, ctx.rng.randrange(total), ctx)
        feitos += 1
    return prog, feitos


def injetar_varios(prog, quantos: dict[str, int], seed=None):
    """Quantidades fixas. Ex.: injetar_varios(p, {"A1": 3, "A5": 2})"""
    rng = random.Random(seed)
    feitos = {}
    for codigo, n in quantos.items():
        prog, feitos[codigo] = injetar(prog, codigo, n, rng.randrange(1 << 30))
    return prog, feitos


def injetar_aleatorio(prog, seed=None, limite=None, tipos=None):
    """Escolhe ao acaso os tipos de smell (entre os injetáveis) e, para cada
    um, n entre 1 e o nº de sítios elegíveis (ou o limite).
    Devolve (programa novo, {código: nº injetado})."""
    rng = random.Random(seed)
    candidatos = list(tipos or INJETAVEIS)
    feitos = {}
    for codigo in rng.sample(candidatos, rng.randint(1, len(candidatos))):
        total = contar_elegiveis(prog, codigo)
        if total == 0:
            feitos[codigo] = 0
            continue
        maximo = total if limite is None else max(1, min(total, limite))
        prog, feitos[codigo] = injetar(prog, codigo, rng.randint(1, maximo), rng.randrange(1 << 30))
    return prog, feitos