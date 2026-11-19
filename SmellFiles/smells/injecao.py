# =====================================================================
# Injeção (full_buTP + adhocTPZ)
# =====================================================================
# Para injetar n ocorrências de um smell, uma de cada vez:
#   1. contar os sítios elegíveis
#   2. escolher um índice k ao acaso
#   3. percorrer a árvore a contar e injetar no k-ésimo sítio
#   4. repetir sobre a árvore já alterada
# 1 e 3 usam a mesma estratégia, para o k-ésimo sítio ser o mesmo.
# Bottom-up: o nó acabado de injetar não é revisitado.
#
# Um sítio é elegível se:
#   - não se sobrepõe a um smell que já existe (regra comum, aqui), e
#   - cumpre as condições do próprio smell (o seu injeta_X).

import random

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from .analise import falha, contexto
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
    """n, ou algum nó dentro de n, tem um smell?"""
    def g(m):
        return [m] if tem_smell(m, ctx) else falha()
    return st.full_tdTU(lambda z: st.adhocTU(st.failTU, g, z), toZipper(n)) != []


def em_smell(z, ctx) -> bool:
    """O sítio sobrepõe-se a um smell: no nó, dentro dele ou num antecessor?"""
    antecessores = z.path.pnodes if z.path else ()
    return contem_smell(z.node(), ctx) or any(tem_smell(a, ctx) for a in antecessores)


# ---------------------------------------------------------------------
# As duas passagens
# ---------------------------------------------------------------------

def worker(smell, ctx, f):
    """adhocTPZ: nos sítios elegíveis aplica f ao nó com o smell injetado."""
    def g(no, z):
        if em_smell(z, ctx):
            falha()
        return f(smell.injeta(no, z, ctx))          # raise se não é elegível
    return lambda z: st.adhocTPZ(st.idTP, g, z)


def contar_elegiveis(prog, codigo, ctx=None) -> int:
    ctx = ctx or contexto(prog)
    total = 0
    def conta(_):
        nonlocal total
        total += 1
        falha()                                     # não altera a árvore
    st.full_buTP(worker(POR_CODIGO[codigo], ctx, conta), toZipper(prog))
    return total


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