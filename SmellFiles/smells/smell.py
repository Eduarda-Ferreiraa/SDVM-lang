# =====================================================================
# A "forma" de um smell. Cada smell do catálogo é um Smell(...).
# =====================================================================
# As três funções olham para UM nó (sem recursão: quem percorre a árvore
# são as estratégias em detecao.py, refactoring.py e injecao.py).
#
#   deteta(n, ctx)     -> bool   o nó tem o smell?
#   corrige(n, ctx)    -> nó     o nó corrigido; raise StrategicError se não
#                                tem o smell ou se corrigir não é seguro
#   injeta(n, z, ctx)  -> nó     o nó com o smell; raise StrategicError se
#                                não é um sítio onde se possa injetar
#                                (z é o zipper, para ver pai/antecessores)
#
# corrige e injeta podem ser None: smells "só de reporte" (ex.: Long Function).

from dataclasses import dataclass
from typing import Callable


@dataclass
class Smell:
    codigo: str
    nome: str
    deteta: Callable
    corrige: Callable | None
    injeta: Callable | None
    custo_min: int              # tempo de remediação por ocorrência (minutos)