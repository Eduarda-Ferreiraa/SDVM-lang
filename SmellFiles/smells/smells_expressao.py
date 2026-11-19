# =====================================================================
# Smells de expressão A1-A7
# =====================================================================
# Cada smell tem três workers sobre UM nó (ver smell.py):
#   deteta_X(n, ctx)     -> bool
#   corrige_X(n, ctx)    -> nó corrigido, ou raise StrategicError
#   injeta_X(n, z, ctx)  -> nó com o smell, ou raise StrategicError
# A regra "nunca dois smells no mesmo sítio" está em injecao.py (vale para
# todos), aqui só estão as condições próprias de cada smell.

from StrategicProg.pyztrategic import strategy as st

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import (
    IntLit, FloatLit, BoolLit, Equals, NotEquals, LessThan, LessEqual, GreaterThan,
    GreaterEqual, Add, Sub, Mul, Div, UnaryOp, Cast,
)

from .smell import Smell
from .analise import (
    LITERAIS, falha, puro, tipos_de, eh_booleana, eh_double, eh_numerica,
    promovida, pai, parametro_seguro,
)


# ---------------- A1: soma/subtração com 0 ---------------------------
# x + 0, 0 + x, x - 0  ->  x

def deteta_soma_zero(n, ctx):
    match n:
        case Add(_, IntLit(0) | FloatLit(0.0)) | Add(IntLit(0) | FloatLit(0.0), _) \
                | Sub(_, IntLit(0) | FloatLit(0.0)):
            return True
        case _:
            return False


def corrige_soma_zero(n, ctx):
    match n:
        case Add(x, IntLit(0)) | Add(IntLit(0), x) | Sub(x, IntLit(0)) if not promovida(x, ctx):
            return x
        case Add(x, FloatLit(0.0)) | Add(FloatLit(0.0), x) | Sub(x, FloatLit(0.0)) if eh_double(x, ctx):
            return x                                # x + 0.0 com x int daria double
        case _:
            falha()


def injeta_soma_zero(n, z, ctx):
    if not eh_numerica(n, ctx):
        falha()
    return ctx.rng.choice([Add(n, IntLit(0)), Add(IntLit(0), n), Sub(n, IntLit(0))])


# ---------------- A2: multiplicação/divisão por 1 --------------------
# x * 1, 1 * x, x / 1  ->  x

def deteta_mult_um(n, ctx):
    match n:
        case Mul(_, IntLit(1) | FloatLit(1.0)) | Mul(IntLit(1) | FloatLit(1.0), _) \
                | Div(_, IntLit(1) | FloatLit(1.0)):
            return True
        case _:
            return False


def corrige_mult_um(n, ctx):
    match n:
        case Mul(x, IntLit(1)) | Mul(IntLit(1), x) | Div(x, IntLit(1)) if not promovida(x, ctx):
            return x
        case Mul(x, FloatLit(1.0)) | Mul(FloatLit(1.0), x) | Div(x, FloatLit(1.0)) if eh_double(x, ctx):
            return x
        case _:
            falha()


def injeta_mult_um(n, z, ctx):
    if n in (IntLit(0), FloatLit(0.0)) or not eh_numerica(n, ctx):   # 1 * 0 seria também A3
        falha()
    return ctx.rng.choice([Mul(n, IntLit(1)), Mul(IntLit(1), n), Div(n, IntLit(1))])


# ---------------- A3: multiplicação por 0 ----------------------------
# x * 0, 0 * x  ->  0

def deteta_mult_zero(n, ctx):
    match n:
        case Mul(_, IntLit(0) | FloatLit(0.0)) | Mul(IntLit(0) | FloatLit(0.0), _):
            return True
        case _:
            return False


def pode_anular(x, ctx):
    """f() * 0 perdia a chamada; d * 0 com d double pode ser NaN."""
    t = tipos_de(x, ctx)
    return puro(x) and bool(t) and "double" not in t


def corrige_mult_zero(n, ctx):
    match n:
        case Mul(x, (IntLit(0) | FloatLit(0.0)) as zero) | Mul((IntLit(0) | FloatLit(0.0)) as zero, x) \
                if pode_anular(x, ctx):
            return zero
        case _:
            falha()


def injeta_mult_zero(n, z, ctx):
    if n != IntLit(0):                              # só onde já há um 0
        falha()
    p = parametro_seguro(z, ctx) or IntLit(ctx.rng.randint(2, 9))
    return ctx.rng.choice([Mul(p, IntLit(0)), Mul(IntLit(0), p)])


# ---------------- A4: comparação com booleano -----------------------
# x == true, x != false  ->  x        x == false, x != true  ->  !x

def deteta_comp_bool(n, ctx):
    match n:
        case Equals(_, BoolLit()) | Equals(BoolLit(), _) | NotEquals(_, BoolLit()) | NotEquals(BoolLit(), _):
            return True
        case _:
            return False


def corrige_comp_bool(n, ctx):
    # x tem de ser bool: x == true com x = 2 é falso, mas x é verdadeiro
    match n:
        case Equals(x, BoolLit(True)) | Equals(BoolLit(True), x) \
                | NotEquals(x, BoolLit(False)) | NotEquals(BoolLit(False), x) if eh_booleana(x, ctx):
            return x
        case Equals(x, BoolLit(False)) | Equals(BoolLit(False), x) \
                | NotEquals(x, BoolLit(True)) | NotEquals(BoolLit(True), x) if eh_booleana(x, ctx):
            return UnaryOp("!", x)
        case _:
            falha()


def injeta_comp_bool(n, z, ctx):
    # não em literais: false -> true == false seria ambíguo de desfazer
    if isinstance(n, LITERAIS) or not eh_booleana(n, ctx):
        falha()
    opcoes = [Equals(n, BoolLit(True)), Equals(BoolLit(True), n), NotEquals(n, BoolLit(False))]
    match n:
        case UnaryOp("!", x):                       # !x -> x == false
            opcoes.append(Equals(x, BoolLit(False)))
    return ctx.rng.choice(opcoes)


# ---------------- A5: dupla negação ---------------------------------
# !!x, -(-x)  ->  x

def deteta_dupla_neg(n, ctx):
    match n:
        case UnaryOp("!", UnaryOp("!", _)) | UnaryOp("-", UnaryOp("-", _)):
            return True
        case _:
            return False


def corrige_dupla_neg(n, ctx):
    match n:
        case UnaryOp("!", UnaryOp("!", x)) if eh_booleana(x, ctx):   # !!5 == 1, não 5
            return x
        case UnaryOp("-", UnaryOp("-", x)) if not promovida(x, ctx):
            return x
        case _:
            falha()


def injeta_dupla_neg(n, z, ctx):
    # nem em !x nem dentro de !x: !!!x contaria como duas duplas negações
    if isinstance(n, UnaryOp) or isinstance(pai(z), UnaryOp):
        falha()
    if eh_booleana(n, ctx):
        return UnaryOp("!", UnaryOp("!", n))
    if eh_numerica(n, ctx):
        return UnaryOp("-", UnaryOp("-", n))
    falha()


# ---------------- A6: auto-comparação --------------------------------
# x == x, x <= x, x >= x  ->  true        x != x, x < x, x > x  ->  false

def deteta_auto_comp(n, ctx):
    match n:
        case Equals(a, b) | NotEquals(a, b) | LessThan(a, b) | LessEqual(a, b) \
                | GreaterThan(a, b) | GreaterEqual(a, b) if a == b:
            return True
        case _:
            return False


def pode_comparar(x, ctx):
    """f() == f() pode ser falso; com double, NaN == NaN é falso."""
    t = tipos_de(x, ctx)
    return puro(x) and bool(t) and "double" not in t


def corrige_auto_comp(n, ctx):
    match n:
        case Equals(a, b) | LessEqual(a, b) | GreaterEqual(a, b) if a == b and pode_comparar(a, ctx):
            return BoolLit(True)
        case NotEquals(a, b) | LessThan(a, b) | GreaterThan(a, b) if a == b and pode_comparar(a, ctx):
            return BoolLit(False)
        case _:
            falha()


def injeta_auto_comp(n, z, ctx):
    # só onde já há um literal booleano: true -> p == p, false -> p != p
    p = parametro_seguro(z, ctx) or IntLit(ctx.rng.randint(2, 9))
    match n:
        case BoolLit(True):
            return ctx.rng.choice([Equals, LessEqual, GreaterEqual])(p, p)
        case BoolLit(False):
            return ctx.rng.choice([NotEquals, LessThan, GreaterThan])(p, p)
        case _:
            falha()


# ---------------- A7: cast redundante --------------------------------
# (t)e com e já do tipo t  ->  e        (inclui (t)(t)x)

def deteta_cast_red(n, ctx):
    match n:
        case Cast(t, e) if tipos_de(e, ctx) == {t}:
            return True
        case _:
            return False


def corrige_cast_red(n, ctx):
    match n:
        case Cast(t, e) if tipos_de(e, ctx) == {t}:
            return e
        case _:
            falha()


def injeta_cast_red(n, z, ctx):
    t = tipos_de(n, ctx)                    # vazio se n não é uma expressão
    if isinstance(n, LITERAIS) or len(t) != 1 or not t <= {"int", "double", "char", "bool"}:
        falha()
    return Cast(t.pop(), n)


# ---------------- catálogo deste grupo -------------------------------

SMELLS = [
    Smell("A1", "soma/subtração com 0",        deteta_soma_zero, corrige_soma_zero, injeta_soma_zero, 1),
    Smell("A2", "multiplicação/divisão por 1", deteta_mult_um,   corrige_mult_um,   injeta_mult_um,   1),
    Smell("A3", "multiplicação por 0",         deteta_mult_zero, corrige_mult_zero, injeta_mult_zero, 2),
    Smell("A4", "comparação com booleano",     deteta_comp_bool, corrige_comp_bool, injeta_comp_bool, 2),
    Smell("A5", "dupla negação",               deteta_dupla_neg, corrige_dupla_neg, injeta_dupla_neg, 1),
    Smell("A6", "auto-comparação",             deteta_auto_comp, corrige_auto_comp, injeta_auto_comp, 2),
    Smell("A7", "cast redundante",             deteta_cast_red,  corrige_cast_red,  injeta_cast_red,  1),
]