# =====================================================================
# Análise do programa: perguntas que os smells fazem sobre uma expressão
# =====================================================================
#   puro(e)            e não tem chamadas de função nem divisões que possam falhar?
#   tipos_de(e, ctx)   que tipo(s) pode ter e?  {"int"}, {"bool"}, ...
#   eh_booleana / eh_numerica / eh_double / promovida
#
# Os smells usam-nas nas condições: x * 0 -> 0 só se x for puro;
# x == true -> x só se x for bool; c + 0 -> c não se c for char; ...
# Ficam aqui (e não em cada ficheiro de smells) porque os outros grupos
# também precisam delas: B2 "ramos iguais" precisa de puro, C7 "variável
# não usada" precisa das declarações.

import random
from dataclasses import dataclass, field, fields, is_dataclass

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import (
    IntLit, FloatLit, BoolLit, CharLit, StringLit, Ident, Or, And, Equals, NotEquals,
    LessThan, LessEqual, GreaterThan, GreaterEqual, Add, Sub, Mul, Div, Mod, UnaryOp,
    Cast, Index, FuncCall,
)
from projeto1.SDVM_lang.ParserFiles.parser.declarations import (
    VariableDeclaration, ArrayDeclaration, Parameter, FunctionDefinition,
)

LITERAIS = (IntLit, FloatLit, BoolLit, CharLit, StringLit)
RELACIONAIS = (Equals, NotEquals, LessThan, LessEqual, GreaterThan, GreaterEqual)
ARITMETICOS = (Add, Sub, Mul, Div, Mod)


def falha():
    raise st.StrategicError


# ---------------------------------------------------------------------
# Pureza: avaliar e não tem efeitos nem pode falhar.
# Na SDVM-lang o único efeito lateral numa expressão é uma FuncCall; o que
# pode falhar é dividir por zero. Uma divisão só é segura se o divisor for
# um literal diferente de 0 (senão (1 / 0) * 0 -> 0 escondia o erro).
# ---------------------------------------------------------------------

def impuro(n):
    match n:
        case FuncCall():
            return [n]
        case Div(_, d) | Mod(_, d) if not (isinstance(d, (IntLit, FloatLit)) and d.v != 0):
            return [n]
        case _:
            falha()


def puro(e) -> bool:
    return st.full_tdTU(lambda z: st.adhocTU(st.failTU, impuro, z), toZipper(e)) == []


# ---------------------------------------------------------------------
# Tipos: tipo declarado de cada nome (variáveis, arrays, parâmetros, funções)
# Ignora o âmbito: um nome declarado com tipos diferentes fica com vários,
# e os refactorings que dependem dele não se aplicam (conservador).
# ---------------------------------------------------------------------

def declaracao(n):
    match n:
        case VariableDeclaration(t, nome, _) | Parameter(t, nome) | FunctionDefinition(t, nome, _, _):
            return [(nome, t)]
        case ArrayDeclaration(t, nome, _, _):
            return [(nome, t + "[]")]               # int a[3] -> "int[]"
        case _:
            falha()


def tipos_declarados(prog) -> dict[str, set[str]]:
    tipos = {}
    for nome, t in st.full_tdTU(lambda z: st.adhocTU(st.failTU, declaracao, z), toZipper(prog)):
        tipos.setdefault(nome, set()).add(t)
    return tipos


def tipos_de(e, ctx) -> set[str]:
    """Tipos possíveis de e. Conjunto vazio = desconhecido (ou não é expressão)."""
    match e:
        case IntLit():    return {"int"}
        case FloatLit():  return {"double"}
        case BoolLit():   return {"bool"}
        case CharLit():   return {"char"}
        case StringLit(): return {"string"}
        case Index(nome, _):                        # a[i]: tipo do elemento
            return {t.removesuffix("[]") for t in ctx.tipos.get(nome, set())}
        case Ident(nome) | FuncCall(nome, _):
            return set(ctx.tipos.get(nome, set()))
        case Cast(t, _):
            return {t}
        case Or() | And() | UnaryOp("!", _) | Equals() | NotEquals() | LessThan() \
                | LessEqual() | GreaterThan() | GreaterEqual():
            return {"bool"}
        case UnaryOp(_, x):                         # + e - : char/bool -> int
            return {"double" if t == "double" else "int" for t in tipos_de(x, ctx)}
        case Add(l, r) | Sub(l, r) | Mul(l, r) | Div(l, r) | Mod(l, r):
            tl, tr = tipos_de(l, ctx), tipos_de(r, ctx)
            if not tl or not tr:
                return set()
            if tl == {"double"} or tr == {"double"}:
                return {"double"}
            return {"int", "double"} if "double" in tl | tr else {"int"}
        case _:
            return set()


def eh_booleana(e, ctx) -> bool:
    return tipos_de(e, ctx) == {"bool"}


def eh_double(e, ctx) -> bool:
    return tipos_de(e, ctx) == {"double"}


def eh_numerica(e, ctx) -> bool:
    t = tipos_de(e, ctx)
    return bool(t) and t <= {"int", "double"}


def promovida(e, ctx) -> bool:
    """Uma conta sobre e muda-lhe o tipo? (char/bool -> int)
    print(c + 0) imprime 97, print(c) imprime 'a'."""
    return bool(tipos_de(e, ctx) & {"char", "bool", "string"})


def numeros_em_declaracoes(prog):
    excluidos = set()

    def visitar(no):
        if isinstance(no, (IntLit, FloatLit)):
            excluidos.add(id(no))

        elif isinstance(no, (list, tuple)):
            for elemento in no:
                visitar(elemento)

        elif is_dataclass(no):
            for campo in fields(no):
                visitar(getattr(no, campo.name))

    def procurar(no):
        if isinstance(no, (VariableDeclaration, ArrayDeclaration)):
            visitar(no.initializer)

        elif isinstance(no, (list, tuple)):
            for elemento in no:
                procurar(elemento)

        elif is_dataclass(no):
            for campo in fields(no):
                procurar(getattr(no, campo.name))

    procurar(prog)
    return excluidos

# ---------------------------------------------------------------------
# Contexto: o que se calcula uma vez por programa
# ---------------------------------------------------------------------

@dataclass
class Contexto:
    tipos: dict[str, set[str]]
    rng: random.Random = field(default_factory=random.Random)
    numeros_excluidos: set[int] = field(default_factory=set)


def contexto(prog, seed=None) -> Contexto:
    return Contexto(
        tipos_declarados(prog),
        random.Random(seed),
        numeros_em_declaracoes(prog)
    )


# ---------------------------------------------------------------------
# Zipper: onde está o nó (usado pelas injeções)
# ---------------------------------------------------------------------

def pai(z):
    return z.path.pnodes[-1] if z.path and z.path.pnodes else None


def parametro_seguro(z, ctx):
    """Um parâmetro int/char/bool da função onde o nó está (está sempre no
    âmbito), ou None."""
    f = z.ancestor(lambda u: isinstance(u.node(), FunctionDefinition))
    if f is None:
        return None
    nomes = [p.name for p in f.node().parameters
             if ctx.tipos.get(p.name) and ctx.tipos[p.name] <= {"int", "char", "bool"}]
    return Ident(ctx.rng.choice(nomes)) if nomes else None