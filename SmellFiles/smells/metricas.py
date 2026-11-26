# =====================================================================
# Métricas
# =====================================================================
# Por função: nº de instruções, ifs, ciclos, profundidade, complexidade
# ciclomática e nº de parâmetros. Por programa: LOC.
#
# As contagens usam estratégias TU (full_tdTU), como a deteção dos smells:
# um worker reconhece o tipo de nó que interessa e a estratégia percorre a
# árvore toda. Os smells C1, C3 e C4 podem importar estas funções daqui.

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import And, Or
from projeto1.SDVM_lang.ParserFiles.parser.declarations import FunctionDefinition
from projeto1.SDVM_lang.ParserFiles.parser.statements import (
    Assignment, ArrayAssignment, Print, Read, Return, FunctionCallStatement, Break, Continue,
)
from projeto1.SDVM_lang.ParserFiles.parser.declarations import VariableDeclaration, ArrayDeclaration
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import (
    Block, IfStatement, WhileStatement, ForStatement,
)

from .analise import falha, pai
from .prettyPrinter import pretty


def contar(worker, no) -> int:
    """Nº de nós (dentro de `no`) em que o worker não falha: failTU `adhocTU` worker + full_tdTU."""
    return len(st.full_tdTU(lambda z: st.adhocTU(st.failTU, worker, z), toZipper(no)))


# ---------------------------------------------------------------------
# Ifs, ciclos e operadores lógicos
# ---------------------------------------------------------------------

def um_if(n):
    match n:
        case IfStatement():
            return [n]                 # um else if é um if: conta
        case _:
            falha()


def um_ciclo(n):
    match n:
        case WhileStatement() | ForStatement():
            return [n]
        case _:
            falha()


def um_operador_logico(n):
    match n:
        case And() | Or():
            return [n]
        case _:
            falha()


def contar_ifs(no) -> int:
    return contar(um_if, no)


def contar_ciclos(no) -> int:
    return contar(um_ciclo, no)


def contar_operadores_logicos(no) -> int:
    """&& e || em qualquer expressão de `no` (condições, atribuições, returns, ...)."""
    return contar(um_operador_logico, no)


# ---------------------------------------------------------------------
# Instruções
# Cada instrução conta 1; um bloco { } não conta (só o que tem dentro).
# As partes do cabeçalho de um for (int i = 0, i = i + 1) não contam como
# instruções à parte: o for conta 1. Para isso é preciso saber onde o nó
# está, por isso usa-se o zipper (adhocTUZ): no for, o corpo é o 4.º filho.
# ---------------------------------------------------------------------

INSTRUCOES = (
    VariableDeclaration, ArrayDeclaration, Assignment, ArrayAssignment, Print, Read,
    Return, FunctionCallStatement, Break, Continue, IfStatement, WhileStatement, ForStatement,
)


def no_cabecalho_do_for(z) -> bool:
    """O nó é o initializer, a condição ou o update de um for (não o corpo)?"""
    return isinstance(pai(z), ForStatement) and len(z.path.l) < 3


def uma_instrucao(n, z):
    if isinstance(n, INSTRUCOES) and not no_cabecalho_do_for(z):
        return [n]
    falha()


def contar_instrucoes(no) -> int:
    return len(st.full_tdTU(lambda z: st.adhocTUZ(st.failTU, uma_instrucao, z), toZipper(no)))


# ---------------------------------------------------------------------
# Profundidade de aninhamento (if / while / for)
# Recursiva porque é um máximo e não uma contagem: a profundidade de um nó
# depende da dos filhos. Um else if fica ao mesmo nível do if (visualmente
# é uma cadeia, não um aninhamento).
# ---------------------------------------------------------------------

def calcular_profundidade(no) -> int:
    match no:
        case Block(instrucoes):
            return max((calcular_profundidade(i) for i in instrucoes), default=0)
        case IfStatement(_, ramo_then, ramo_else):
            prof_then = 1 + calcular_profundidade(ramo_then)
            if isinstance(ramo_else, IfStatement):          # else if: mesmo nível
                prof_else = calcular_profundidade(ramo_else)
            elif ramo_else is not None:
                prof_else = 1 + calcular_profundidade(ramo_else)
            else:
                prof_else = 0
            return max(prof_then, prof_else)
        case WhileStatement(_, corpo) | ForStatement(_, _, _, corpo):
            return 1 + calcular_profundidade(corpo)
        case _:
            return 0


# ---------------------------------------------------------------------
# Complexidade ciclomática (McCabe): 1 + nº de pontos de decisão.
# Pontos de decisão: cada if (incluindo else if), cada ciclo, e cada && / ||
# (com avaliação em curto-circuito, cada um é um desvio no fluxo).
# ---------------------------------------------------------------------

def complexidade_ciclomatica(funcao) -> int:
    corpo = funcao.body
    return 1 + contar_ifs(corpo) + contar_ciclos(corpo) + contar_operadores_logicos(corpo)


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
# Métricas de uma função
# ---------------------------------------------------------------------

def metricas_funcao(funcao) -> dict:
    corpo = funcao.body
    return {
        "nome": funcao.name,
        "parametros": n_parametros(funcao),
        "instrucoes": contar_instrucoes(corpo),
        "ifs": contar_ifs(corpo),
        "ciclos": contar_ciclos(corpo),
        "profundidade": calcular_profundidade(corpo),
        "complexidade_ciclomatica": complexidade_ciclomatica(funcao),
    }


# ---------------------------------------------------------------------
# LOC: linhas NÃO vazias de pretty(ast).
# Conta as linhas só com chavetas. Não é o nº de instruções e não conta
# comentários (o parser descarta-os). Serve para programas originais e
# transformados, porque parte da AST e não do ficheiro.
# ---------------------------------------------------------------------

def loc(prog) -> int:
    return sum(1 for linha in pretty(prog).splitlines() if linha.strip())