# =====================================================================
# Recolhas (TU) para os smells C2/C6/C7/C9
# =====================================================================
# Os workers de deteção só veem UM nó (ver smell.py). Quando um smell
# precisa de saber algo sobre o programa todo (que nomes são usados, que
# blocos se repetem, ...), isso calcula-se UMA vez aqui, com uma TU
# (full_tdTU), e fica guardado no Contexto (ver analise.py).
# É a "análise em duas fases" das fichas:
#     fase 1: recolher (aqui)      fase 2: consultar (smells_1.py)
#

from collections import Counter

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import Ident, Index
from projeto1.SDVM_lang.ParserFiles.parser.declarations import VariableDeclaration
from projeto1.SDVM_lang.ParserFiles.parser.statements import Assignment, ArrayAssignment, Read
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import Block, ForStatement

# C9: um bloco só conta para duplicação se tiver pelo menos tantas instruções
MIN_INSTRUCOES = 2


def _falha():
    """'este nó não é do tipo que esta regra trata' (não é um erro)."""
    raise st.StrategicError


def _recolhe(worker, prog):
    """failTU `adhocTU` worker, aplicada a todos os nós (full_tdTU)."""
    return st.full_tdTU(lambda z: st.adhocTU(st.failTU, worker, z), toZipper(prog))


# ---------------------------------------------------------------------
# C7, fase 1: que nomes são referenciados?
# Política do catálogo: contam Ident, Index, e os alvos de Assignment,
# ArrayAssignment e Read. (Atribuir a uma variável conta como usá-la.)
# Nota: Index/Assignment/ArrayAssignment/Read têm o nome como str.
# ---------------------------------------------------------------------

def _uso(n):
    match n:
        case Ident(nome) | Index(nome, _) | Assignment(nome, _) \
                | ArrayAssignment(nome, _, _) | Read(nome):
            return [nome]
        case _:
            _falha()


def nomes_usados(prog) -> set[str]:
    return set(_recolhe(_uso, prog))


# ---------------------------------------------------------------------
# C6: que declarações são o initializer de um for?  (guarda o id do objeto)
# O worker de deteção só vê a declaração, não o pai; por isso o ForStatement
# "marca" a sua declaração aqui. Usa-se id() porque se quer DESTA declaração,
# não de outra igual noutro sítio (int i = 0 dentro e fora de um for).
# ---------------------------------------------------------------------

def _decl_for(n):
    match n:
        case ForStatement(VariableDeclaration() as d, _, _, _):
            return [id(d)]
        case _:
            _falha()


def declaracoes_em_for(prog) -> set[int]:
    return set(_recolhe(_decl_for, prog))


# ---------------------------------------------------------------------
# C9: quantas vezes aparece cada bloco (comparação estrutural exata)?
# As dataclasses não são hashable, por isso a chave é repr(bloco): é
# determinístico e mostra todos os campos, logo blocos iguais <=> mesma chave.
# ---------------------------------------------------------------------

def _bloco(n):
    match n:
        case Block(instrucoes) if len(instrucoes) >= MIN_INSTRUCOES:
            return [repr(n)]
        case _:
            _falha()


def contagem_blocos(prog) -> Counter:
    return Counter(_recolhe(_bloco, prog))
