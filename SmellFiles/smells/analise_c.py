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
from projeto1.SDVM_lang.ParserFiles.parser.declarations import (
    VariableDeclaration, ArrayDeclaration, Parameter, FunctionDefinition,
)
from projeto1.SDVM_lang.ParserFiles.parser.statements import Assignment, ArrayAssignment, Read
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import Block, ForStatement

# C9: um bloco só conta para duplicação se tiver pelo menos tantas instruções
MIN_INSTRUCOES = 3


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
# C6: que declarações são de um contador de for?  (guarda o id do objeto)
# Um nome é contador se for declarado ou atribuído no cabeçalho de um for:
#     for (int i = 0; ...)      ou      int i; for (i = 0; ...)
# Fica isenta a declaração (variável ou parâmetro) desse nome na MESMA
# função; um "int i" noutra função, ou global, não fica isento.
# Usa-se id() porque o worker de deteção só vê a declaração; os ids só
# servem durante a deteção (o detetar recalcula o contexto).
# ---------------------------------------------------------------------

def _contadores(no) -> set[str]:
    """Nomes usados como contador de um for dentro de no."""
    def worker(n):
        match n:
            case ForStatement(VariableDeclaration(_, nome, _), _, _, _) \
                    | ForStatement(Assignment(nome, _), _, _, _):
                return [nome]
            case _:
                _falha()
    return set(_recolhe(worker, no))


def _declaracao(n):
    match n:
        case VariableDeclaration(_, nome, _) | Parameter(_, nome):
            return [(nome, id(n))]
        case _:
            _falha()


def declaracoes_contador(prog) -> set[int]:
    """ids das declarações cujo nome é contador de um for na mesma função."""
    def por_funcao(f):
        match f:
            case FunctionDefinition():
                nomes = _contadores(f)
                return [ident for nome, ident in _recolhe(_declaracao, f) if nome in nomes]
            case _:
                _falha()
    return set(_recolhe(por_funcao, prog))


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


# ---------------------------------------------------------------------
# C9: que blocos são CÓPIAS a mais (os que contam como smell)?
# Regras:
#   - em cada grupo de blocos iguais, um é o original e não conta; as outras
#     cópias contam uma ocorrência cada. Duas cópias iguais -> 1 ocorrência.
#   - um bloco que está DENTRO de um bloco duplicado não conta à parte: se
#     A e B são iguais e ambos têm lá dentro o bloco C, há uma só
#     duplicação (B), e não duas (B e a segunda cópia de C).
#   - mas uma cópia de C fora de A e de B conta: é uma duplicação a mais.
#     Nesse caso o original de C é o que está dentro de A, por isso todas as
#     cópias soltas contam, estejam antes ou depois de A no código.
#   - se nenhuma cópia está dentro de outro duplicado, o original é a
#     primeira pela ordem da travessia (a ordem do código).
# Para saber se um bloco está dentro de outro é preciso ver os antecessores,
# por isso o worker usa o zipper (adhocTUZ, path.pnodes). Guarda-se o id()
# dos blocos que contam (como no C6: interessa ESTE bloco, não outro igual).
# ---------------------------------------------------------------------

def _duplicado(n, blocos) -> bool:
    return (isinstance(n, Block) and len(n.statements) >= MIN_INSTRUCOES
            and blocos[repr(n)] >= 2)


def copias_duplicadas(prog) -> set[int]:
    blocos = contagem_blocos(prog)

    def ocorrencia(n, z):
        """[(chave, id, está dentro de um bloco duplicado?)] para cada bloco duplicado."""
        if not _duplicado(n, blocos):
            _falha()
        antecessores = z.path.pnodes if z.path else ()
        dentro = any(_duplicado(a, blocos) for a in antecessores)
        return [(repr(n), id(n), dentro)]

    ocorrencias = st.full_tdTU(lambda z: st.adhocTUZ(st.failTU, ocorrencia, z), toZipper(prog))

    grupos = {}                           # chave -> [(id, dentro), ...] pela ordem do código
    for chave, ident, dentro in ocorrencias:
        grupos.setdefault(chave, []).append((ident, dentro))

    copias = set()
    for grupo in grupos.values():
        soltas = [ident for ident, dentro in grupo if not dentro]
        if any(dentro for _, dentro in grupo):
            copias.update(soltas)         # o original está dentro de outro duplicado
        else:
            copias.update(soltas[1:])     # o primeiro é o original
    return copias


# ---------------------------------------------------------------------
# C8: que nomes são variáveis/arrays globais?
# Só interessam as declarações do nível de topo do programa, por isso basta
# olhar para prog.declarations (não é preciso percorrer a árvore).
# ---------------------------------------------------------------------

def nomes_globais(prog) -> set[str]:
    return {d.name for d in prog.declarations
            if isinstance(d, (VariableDeclaration, ArrayDeclaration))}