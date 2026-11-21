# =====================================================================
# Catálogo: todos os smells, de todos os grupos
# =====================================================================
# Para acrescentar um grupo novo: importá-lo e somar a sua lista SMELLS.
# A deteção, o refactoring e a injeção usam esta lista e não precisam de
# ser alterados.

from . import smells_expressao
from . import smells_controlo
# from . import smells_design

CATALOGO = (
    smells_expressao.SMELLS
    + smells_controlo.SMELLS
    # + smells_design.SMELLS
)

POR_CODIGO = {s.codigo: s for s in CATALOGO}


def seleciona(codigos=None):
    """Todos os smells, ou só os dos códigos indicados (ex.: ["A1", "A4"])."""
    return CATALOGO if codigos is None else [POR_CODIGO[c] for c in codigos]
