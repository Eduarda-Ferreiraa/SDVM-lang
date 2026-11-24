from projeto1.SDVM_lang.ParserFiles.parser.declarations import FunctionDefinition

from projeto1.SDVM_lang.ParserFiles.parser.control_flow import (
    Block,
    IfStatement,
    WhileStatement,
    ForStatement,
)

from .smell import Smell

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import And, Or

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import IntLit, FloatLit
from projeto1.SDVM_lang.ParserFiles.parser.declarations import VariableDeclaration, ArrayDeclaration

from projeto1.SDVM_lang.ParserFiles.parser.parser import Program

from projeto1.SDVM_lang.ParserFiles.parser.statements import (
    Assignment,
    ArrayAssignment,
)

from dataclasses import fields, is_dataclass

MAX_INSTRUCOES = 30


def contar_instrucoes(no):
    match no:
        case Block(instrucoes):
            return sum(contar_instrucoes(i) for i in instrucoes)

        case IfStatement(_, ramo_then, ramo_else):
            total = 1 + contar_instrucoes(ramo_then)
            if ramo_else is not None:
                total += contar_instrucoes(ramo_else)
            return total

        case WhileStatement(_, corpo):
            return 1 + contar_instrucoes(corpo)

        case ForStatement(_, _, _, corpo):
            return 1 + contar_instrucoes(corpo)

        case _:
            return 1


def deteta_funcao_longa(no, ctx):
    match no:
        case FunctionDefinition(_, _, _, corpo):
            return contar_instrucoes(corpo) > MAX_INSTRUCOES

        case _:
            return False



# ---------------- C3: Aninhamento profundo ----------------

MAX_PROFUNDIDADE = 3


def calcular_profundidade(no):
    match no:
        case Block(instrucoes):
            return max(
                (calcular_profundidade(i) for i in instrucoes),
                default=0
            )

        case IfStatement(_, ramo_then, ramo_else):
            prof_then = calcular_profundidade(ramo_then)

            prof_else = (
                calcular_profundidade(ramo_else)
                if ramo_else is not None else 0
            )

            return 1 + max(prof_then, prof_else)

        case WhileStatement(_, corpo):
            return 1 + calcular_profundidade(corpo)

        case ForStatement(_, _, _, corpo):
            return 1 + calcular_profundidade(corpo)

        case _:
            return 0


def deteta_aninhamento_profundo(no, ctx):
    match no:
        case FunctionDefinition(_, _, _, corpo):
            return calcular_profundidade(corpo) > MAX_PROFUNDIDADE

        case _:
            return False



# ---------------- C4: Condição complexa ----------------

MAX_OPERADORES_LOGICOS = 3



def contar_operadores_logicos(expr):
    if expr is None:
        return 0

    if isinstance(expr, (list, tuple)):
        return sum(contar_operadores_logicos(e) for e in expr)

    total = 1 if isinstance(expr, (And, Or)) else 0

    if is_dataclass(expr):
        for campo in fields(expr):
            valor = getattr(expr, campo.name)
            total += contar_operadores_logicos(valor)

    return total



def deteta_condicao_complexa(no, ctx):
    match no:
        case IfStatement(condicao, _, _):
            return contar_operadores_logicos(condicao) > MAX_OPERADORES_LOGICOS

        case WhileStatement(condicao, _):
            return contar_operadores_logicos(condicao) > MAX_OPERADORES_LOGICOS

        case ForStatement(_, condicao, _, _):
            return (
                condicao is not None
                and contar_operadores_logicos(condicao) > MAX_OPERADORES_LOGICOS
            )

        case _:
            return False



# ---------------- C5: Números mágicos ----------------

NUMEROS_PERMITIDOS = (0, 1, -1)


def deteta_numero_magico(no, ctx):
    match no:
        case IntLit(valor) | FloatLit(valor):
            return (
                valor not in NUMEROS_PERMITIDOS
                and id(no) not in ctx.numeros_excluidos
            )

        case _:
            return False



# ---------------- C8: Estado global mutável ----------------

def recolher_globais(programa):
    globais = set()

    for declaracao in programa.declarations:
        if isinstance(declaracao, (VariableDeclaration, ArrayDeclaration)):
            globais.add(declaracao.name)

    return globais



def procurar_alteracoes_globais(no, globais, locais=None):
    if locais is None:
        locais = set()

    match no:
        case Block(instrucoes):
            nomes_locais = set(locais)

            for instrucao in instrucoes:
                if isinstance(instrucao, (VariableDeclaration, ArrayDeclaration)):
                    nomes_locais.add(instrucao.name)

                if procurar_alteracoes_globais(
                    instrucao, globais, nomes_locais
                ):
                    return True

            return False

        case Assignment(nome, _) | ArrayAssignment(nome, _, _):
            return nome in globais and nome not in locais

        case IfStatement(_, ramo_then, ramo_else):
            if procurar_alteracoes_globais(ramo_then, globais, locais.copy()):
                return True

            return (
                ramo_else is not None
                and procurar_alteracoes_globais(
                    ramo_else, globais, locais.copy()
                )
            )

        case WhileStatement(_, corpo):
            return procurar_alteracoes_globais(
                corpo, globais, locais.copy()
            )

        case ForStatement(inicio, _, atualizacao, corpo):
            nomes_for = set(locais)

            if isinstance(inicio, (VariableDeclaration, ArrayDeclaration)):
                nomes_for.add(inicio.name)

            return any(
                parte is not None
                and procurar_alteracoes_globais(
                    parte, globais, nomes_for
                )
                for parte in (inicio, atualizacao, corpo)
            )

        case _:
            return False


def deteta_estado_global_mutavel(no, ctx):
    match no:
        case Program(declaracoes):
            globais = recolher_globais(no)

            for declaracao in declaracoes:
                if isinstance(declaracao, FunctionDefinition):
                    parametros = {
                        p.name for p in declaracao.parameters
                    }

                    if procurar_alteracoes_globais(
                        declaracao.body, globais, parametros
                    ):
                        return True

            return False

        case _:
            return False


SMELLS = [
    Smell("C1", "função longa",
          deteta_funcao_longa, None, None, 20),

    Smell("C3", "aninhamento profundo",
          deteta_aninhamento_profundo, None, None, 15),

    Smell("C4", "condição complexa",
          deteta_condicao_complexa, None, None, 10),

    Smell("C5", "números mágicos",
      deteta_numero_magico, None, None, 5),

    Smell("C8", "estado global mutável",
      deteta_estado_global_mutavel, None, None, 15),
]
