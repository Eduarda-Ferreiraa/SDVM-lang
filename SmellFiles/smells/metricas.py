
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import (
    Block,
    IfStatement,
    WhileStatement,
    ForStatement,
)

from projeto1.SDVM_lang.ParserFiles.parser.declarations import (
    FunctionDefinition,
)

from projeto1.SDVM_lang.SmellFiles.smells.smells_design import (
    contar_instrucoes,
    calcular_profundidade,
)

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import And, Or
from dataclasses import fields, is_dataclass

def contar_ifs(no):
    match no:
        case Block(instrucoes):
            return sum(contar_ifs(i) for i in instrucoes)

        case IfStatement(_, ramo_then, ramo_else):
            return (
                1
                + contar_ifs(ramo_then)
                + (contar_ifs(ramo_else) if ramo_else is not None else 0)
            )

        case WhileStatement(_, corpo):
            return contar_ifs(corpo)

        case ForStatement(_, _, _, corpo):
            return contar_ifs(corpo)

        case _:
            return 0


def contar_ciclos(no):
    match no:
        case Block(instrucoes):
            return sum(contar_ciclos(i) for i in instrucoes)

        case IfStatement(_, ramo_then, ramo_else):
            return (
                contar_ciclos(ramo_then)
                + (contar_ciclos(ramo_else) if ramo_else is not None else 0)
            )

        case WhileStatement(_, corpo):
            return 1 + contar_ciclos(corpo)

        case ForStatement(_, _, _, corpo):
            return 1 + contar_ciclos(corpo)

        case _:
            return 0



def metricas_funcao(funcao):
    corpo = funcao.body

    return {
        "nome": funcao.name,
        "instrucoes": contar_instrucoes(corpo),
        "ifs": contar_ifs(corpo),
        "ciclos": contar_ciclos(corpo),
        "profundidade": calcular_profundidade(corpo),
        "complexidade_ciclomatica": complexidade_ciclomatica(funcao),
    }


# ---------------- Complexidade ciclomática ----------------

def contar_operadores_logicos(no):
    if isinstance(no, (And, Or)):
        total = 1
    else:
        total = 0

    if isinstance(no, list):
        return sum(contar_operadores_logicos(x) for x in no)

    if is_dataclass(no):
        for campo in fields(no):
            total += contar_operadores_logicos(
                getattr(no, campo.name)
            )

    return total


def complexidade_ciclomatica(funcao):
    corpo = funcao.body

    return (
        1
        + contar_ifs(corpo)
        + contar_ciclos(corpo)
        + contar_operadores_logicos(corpo)
    )


# =====================================================================
# Métricas 1: parâmetros por função e LOC
# =====================================================================
from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from projeto1.SDVM_lang.ParserFiles.parser.declarations import FunctionDefinition

from .analise import falha
from .prettyPrinter import pretty


# ---------------------------------------------------------------------
# Parâmetros por função (TU). A mesma contagem é usada pelo smell C2.
# ---------------------------------------------------------------------

def n_parametros(f) -> int:
    return len(f.parameters)


def parametros_de(n):
    """worker: numa função devolve [(nome, nº de parâmetros)]; nos outros nós falha."""
    match n:
        case FunctionDefinition(_, nome, _, _):
            return [(nome, n_parametros(n))]
        case _:
            falha()


def parametros_por_funcao(prog) -> list[tuple[str, int]]:
    """[(nome, nº de parâmetros)], incluindo funções com 0 parâmetros."""
    return st.full_tdTU(lambda z: st.adhocTU(st.failTU, parametros_de, z), toZipper(prog))


# ---------------------------------------------------------------------
# LOC: linhas NÃO vazias de pretty(ast).
# Conta as linhas só com chavetas. Não é o nº de instruções e não conta
# comentários (o parser descarta-os). Serve para programas originais e
# transformados, porque parte da AST e não do ficheiro.
# ---------------------------------------------------------------------

def loc(prog) -> int:
    return sum(1 for linha in pretty(prog).splitlines() if linha.strip())
