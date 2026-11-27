# =====================================================================
# Catálogo: todos os smells, de todos os grupos
# =====================================================================
# Para acrescentar um grupo novo: importá-lo e somar a sua lista SMELLS.
# A deteção, o refactoring e a injeção usam esta lista e não precisam de
# ser alterados.
from . import smells_codigo
from . import smells_expressao
from . import smells_controlo
from . import smells_design


def _ordem(s):
    """A1 < A2 < ... < B9 < B10 < C1 < ...: pela letra e depois pelo número."""
    return s.codigo[0], int(s.codigo[1:])


# Ordenado pelo código: os relatórios mostram A1..A7, B1..B10, C1..C9 por
# esta ordem, seja qual for o ficheiro de onde cada smell vem.
CATALOGO = sorted(
    smells_expressao.SMELLS
    + smells_controlo.SMELLS
    + smells_design.SMELLS
    + smells_codigo.SMELLS,
    key=_ordem,
)

POR_CODIGO = {s.codigo: s for s in CATALOGO}


def seleciona(codigos=None):
    """Todos os smells, ou só os dos códigos indicados (ex.: ["A1", "A4"])."""
    return CATALOGO if codigos is None else [POR_CODIGO[c] for c in codigos]