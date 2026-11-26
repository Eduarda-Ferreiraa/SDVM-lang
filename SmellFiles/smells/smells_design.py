# =====================================================================
# C1, C3, C4, C5, C8  (só deteção: corrige=None, injeta=None)
# =====================================================================
# Cada smell é um deteta(n, ctx) -> bool sobre UM nó; quem percorre a
# árvore é o detecao.py (full_tdTU). Aqui devolve-se False nos nós que
# não interessam.
# As contagens (instruções, profundidade, operadores lógicos) vêm do
# metricas.py, para que o smell e a métrica reportada usem a mesma conta.

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import IntLit, FloatLit
from projeto1.SDVM_lang.ParserFiles.parser.declarations import (
    VariableDeclaration, ArrayDeclaration, Parameter, FunctionDefinition,
)
from projeto1.SDVM_lang.ParserFiles.parser.statements import Assignment, ArrayAssignment, Read
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import (
    IfStatement, WhileStatement, ForStatement,
)

from .smell import Smell
from .analise import falha
from .metricas import contar_instrucoes, calcular_profundidade, contar_operadores_logicos

MAX_INSTRUCOES = 30            # C1: mais de 30 instruções
MAX_PROFUNDIDADE = 3           # C3: mais de 3 níveis (o SonarQube usa o mesmo limite)
MAX_OPERADORES_LOGICOS = 3     # C4: mais de 3 && / || (o SonarQube usa o mesmo limite)
NUMEROS_PERMITIDOS = (0, 1)    # C5: inclui 0.0 e 1.0; -1 é UnaryOp("-", IntLit(1)), logo também


# ---------------- C1: função longa -----------------------------------
# Nº de instruções do corpo (o cabeçalho do for não conta à parte).

def deteta_funcao_longa(n, ctx):
    return isinstance(n, FunctionDefinition) and contar_instrucoes(n.body) > MAX_INSTRUCOES


# ---------------- C3: aninhamento profundo ---------------------------
# Profundidade máxima de if/while/for no corpo; um else if fica ao mesmo
# nível do if (é uma cadeia, não um aninhamento).

def deteta_aninhamento_profundo(n, ctx):
    return isinstance(n, FunctionDefinition) and calcular_profundidade(n.body) > MAX_PROFUNDIDADE


# ---------------- C4: condição complexa ------------------------------
# Nº de && / || na condição de um if, while ou for. Expressões fora de
# condições (atribuições, returns) não contam: o smell é sobre condições.

def deteta_condicao_complexa(n, ctx):
    match n:
        case IfStatement(cond, _, _) | WhileStatement(cond, _) | ForStatement(_, cond, _, _):
            return cond is not None and contar_operadores_logicos(cond) > MAX_OPERADORES_LOGICOS
        case _:
            return False


# ---------------- C5: números mágicos --------------------------------
# Cada literal numérico fora de NUMEROS_PERMITIDOS, exceto os que estão no
# valor inicial de uma declaração (int dias = 7; a declaração dá-lhe nome):
# ctx.numeros_excluidos, ver analise.py.

def deteta_numero_magico(n, ctx):
    match n:
        case IntLit(v) | FloatLit(v):
            return v not in NUMEROS_PERMITIDOS and id(n) not in ctx.numeros_excluidos
        case _:
            return False


# ---------------- C8: estado global mutável --------------------------
# Uma ocorrência por FUNÇÃO que altera uma variável/array global
# (atribuição, atribuição a uma posição, ou read). Os nomes globais estão
# em ctx.globais (ver analise_c.py). Um nome declarado na função (parâmetro
# ou variável local) esconde o global, por isso não conta.
# Simplificação: conta-se por nome na função toda, não por bloco.

def _alterado(n):
    match n:
        case Assignment(nome, _) | ArrayAssignment(nome, _, _) | Read(nome):
            return [nome]
        case _:
            falha()


def _local(n):
    match n:
        case VariableDeclaration(_, nome, _) | ArrayDeclaration(_, nome, _, _) | Parameter(_, nome):
            return [nome]
        case _:
            falha()


def _recolhe(worker, no) -> set[str]:
    return set(st.full_tdTU(lambda z: st.adhocTU(st.failTU, worker, z), toZipper(no)))


def globais_alterados(f, globais) -> set[str]:
    """Nomes globais que a função f altera."""
    return (_recolhe(_alterado, f) & globais) - _recolhe(_local, f)


def deteta_estado_global_mutavel(n, ctx):
    return isinstance(n, FunctionDefinition) and bool(globais_alterados(n, ctx.globais))


SMELLS = [
    Smell("C1", "função longa",          deteta_funcao_longa,          None, None, 20),
    Smell("C3", "aninhamento profundo",  deteta_aninhamento_profundo,  None, None, 15),
    Smell("C4", "condição complexa",     deteta_condicao_complexa,     None, None, 10),
    Smell("C5", "números mágicos",       deteta_numero_magico,         None, None, 5),
    Smell("C8", "estado global mutável", deteta_estado_global_mutavel, None, None, 15),
]