# =====================================================================
# Métricas
# =====================================================================
# Por função: nº de instruções, ifs, ciclos, profundidade, complexidade
# ciclomática e nº de parâmetros. Por programa: LOC.
#
# As contagens usam estratégias TU (recolhe / recolhe_z de analise_c.py,
# isto é, full_tdTU com adhocTU / adhocTUZ), como a deteção dos smells:
# um worker reconhece o tipo de nó que interessa e a estratégia percorre a
# árvore toda. Os smells C1, C3 e C4 podem importar estas funções daqui.

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import And, Or
from projeto1.SDVM_lang.ParserFiles.parser.declarations import FunctionDefinition
from projeto1.SDVM_lang.ParserFiles.parser.statements import (
    Assignment, ArrayAssignment, Print, Read, Return, FunctionCallStatement, Break, Continue,
)
from projeto1.SDVM_lang.ParserFiles.parser.declarations import VariableDeclaration, ArrayDeclaration
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import (
    IfStatement, WhileStatement, ForStatement,
)

from .analise import falha, pai
from .analise_c import recolhe, recolhe_z
from .prettyPrinter import pretty


def contar(worker, no) -> int:
    """Nº de nós (dentro de `no`) em que o worker não falha: failTU `adhocTU` worker + full_tdTU."""
    return len(recolhe(worker, no))


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
    """O nó é o initializer, a condição ou o update de um for (não o corpo)?
    z.arity(): a posição do nó entre os irmãos (1.º, 2.º, ...); o corpo é o 4.º."""
    return isinstance(pai(z), ForStatement) and z.arity() <= 3


def uma_instrucao(n, z):
    if isinstance(n, INSTRUCOES) and not no_cabecalho_do_for(z):
        return [n]
    falha()


def contar_instrucoes(no) -> int:
    return len(recolhe_z(uma_instrucao, no))


# ---------------------------------------------------------------------
# Profundidade de aninhamento (if / while / for)
# Com o zipper: o nível de um if/while/for é o nº de if/while/for no
# caminho desde a raiz até ele (os antecessores, z.path.pnodes, mais ele
# próprio). Uma TU (adhocTUZ) recolhe o nível de cada um e a profundidade
# é o máximo. Um else if fica ao mesmo nível do if (visualmente é uma
# cadeia, não um aninhamento): um if que é o else_branch de outro if não
# soma. Um else normal ({ if ... }) soma, porque o if está dentro do bloco.
# ---------------------------------------------------------------------

CONTROLO = (IfStatement, WhileStatement, ForStatement)


def _else_if(no, pai_no) -> bool:
    """no é o else de pai_no e é um if (else if)? (is: o zipper guarda os nós originais)"""
    return isinstance(no, IfStatement) and isinstance(pai_no, IfStatement) and pai_no.else_branch is no


def nivel_de_controlo(n, z):
    """worker: num if/while/for devolve [o seu nível de aninhamento]; nos outros nós falha."""
    if not isinstance(n, CONTROLO):
        falha()
    caminho = (z.path.pnodes if z.path else ()) + (n,)
    return [sum(1 for i, no in enumerate(caminho)
                if isinstance(no, CONTROLO) and not (i > 0 and _else_if(no, caminho[i - 1])))]


def calcular_profundidade(no) -> int:
    return max(recolhe_z(nivel_de_controlo, no), default=0)


# ---------------------------------------------------------------------
# Complexidade ciclomática (McCabe): 1 + nº de pontos de decisão.
# Pontos de decisão: cada if (incluindo else if), cada ciclo, e cada && / ||
# (com avaliação em curto-circuito, cada um é um desvio no fluxo).
# ---------------------------------------------------------------------

def um_ponto_de_decisao(n):
    match n:
        case IfStatement() | WhileStatement() | ForStatement() | And() | Or():
            return [n]
        case _:
            falha()


def complexidade_ciclomatica(funcao) -> int:
    """Uma só travessia (TU) que recolhe todos os pontos de decisão."""
    return 1 + contar(um_ponto_de_decisao, funcao.body)


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
    return recolhe(parametros_de, prog)


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