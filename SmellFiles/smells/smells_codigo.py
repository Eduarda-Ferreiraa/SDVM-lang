# =====================================================================
# C2, C6, C7, C9  (só deteção: corrige=None, injeta=None)
# =====================================================================
# Cada smell é um deteta(n, ctx) -> bool sobre UM nó. Quem percorre a
# árvore é o detecao.py (full_tdTU). Por isso aqui devolve-se False nos
# nós que não interessam (e não se chama falha()).

from projeto1.SDVM_lang.ParserFiles.parser.declarations import (
    VariableDeclaration, ArrayDeclaration, Parameter, FunctionDefinition,
)
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import Block

from .smell import Smell
from .metricas import n_parametros

LIMITE_PARAMETROS = 4          # C2: 4 ou mais parâmetros
LETRAS_CICLO = {"i", "j", "k"}  # C6: isentas quando são contador de um for


def nome_declarado(n):
    """Nome de uma variável, array ou parâmetro; None nos outros nós.
    (Nomes de funções ficam de fora: decisão do grupo.)"""
    match n:
        case VariableDeclaration(_, nome, _) | ArrayDeclaration(_, nome, _, _) | Parameter(_, nome):
            return nome
        case _:
            return None


# ---------------- C2: lista de parâmetros longa -----------------------

def deteta_c2(n, ctx):
    return isinstance(n, FunctionDefinition) and n_parametros(n) >= LIMITE_PARAMETROS


# ---------------- C6: identificador curto -----------------------------
# Conta a declaração (variável, array ou parâmetro), não cada uso. Nome com
# 1 letra, exceto i/j/k que sejam contador de um for na mesma função
# (ctx.decl_for, ver declaracoes_contador em analise_c.py).

def deteta_c6(n, ctx):
    nome = nome_declarado(n)
    if nome is None or len(nome) != 1:
        return False
    return not (nome in LETRAS_CICLO and id(n) in ctx.decl_for)


# ---------------- C7: variável/parâmetro/array não usado --------------
# Fase 2: consulta o conjunto de nomes usados (ctx.usados, por nome, no
# programa todo). Só reporte.

def deteta_c7(n, ctx):
    nome = nome_declarado(n)
    return nome is not None and nome not in ctx.usados


# ---------------- C9: código duplicado --------------------------------
# Bloco com >= MIN_INSTRUCOES instruções (analise_c.py) que é uma CÓPIA A
# MAIS de outro igual (igualdade estrutural exata). O original não conta:
# duas cópias iguais -> 1 ocorrência. Um bloco dentro de um bloco duplicado
# não conta à parte. As regras completas estão em copias_duplicadas
# (analise_c.py); aqui só se consulta o resultado (ctx.c9_copias).

def deteta_c9(n, ctx):
    return isinstance(n, Block) and id(n) in ctx.c9_copias


# ---------------- catálogo deste grupo --------------------------------

SMELLS = [
    Smell("C2", "muitos parâmetros",   deteta_c2, None, None, 10),
    Smell("C6", "identificador curto", deteta_c6, None, None, 2),
    Smell("C7", "variável não usada",  deteta_c7, None, None, 3),
    Smell("C9", "código duplicado",    deteta_c9, None, None, 30),
]