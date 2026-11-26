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
    LITERAIS, falha, se_aplica, puro, tipos_de, eh_booleana, eh_numerica,
    pai, parametro_seguro,
)


# ---------------- A1: soma/subtração com 0 ---------------------------
# x + 0, 0 + x, x - 0, x + 0.0, 0.0 + x, x - 0.0  ->  x      (x int ou double)
# Só para números: c + 0 (char) e b + 0 (bool) não são smell.
# Opção do grupo: a + 0.0 com a int também é smell e fica a; a conversão
# para double que o + 0.0 fazia é ignorada.

def corrige_soma_zero(n, ctx):
    match n:
        case Add(x, IntLit(0) | FloatLit(0.0)) | Add(IntLit(0) | FloatLit(0.0), x) \
                | Sub(x, IntLit(0) | FloatLit(0.0)) if eh_numerica(x, ctx):
            return x
        case _:
            falha()


def deteta_soma_zero(n, ctx):
    return se_aplica(corrige_soma_zero, n, ctx)     # smell = a correção aplica-se


NEUTROS_SOMA = (IntLit(0), FloatLit(0.0))
NEUTROS_MULT = (IntLit(1), FloatLit(1.0))


def injeta_soma_zero(n, z, ctx):
    # não num 0 / 0.0: 0 + 0.0 desfazia-se em 0 (a regra x + 0 apanha o lado errado)
    if n in NEUTROS_SOMA or not eh_numerica(n, ctx):
        falha()
    return ctx.rng.choice([Add(n, IntLit(0)), Add(IntLit(0), n), Sub(n, IntLit(0))])


# ---------------- A2: multiplicação/divisão por 1 --------------------
# x * 1, 1 * x, x / 1, x * 1.0, 1.0 * x, x / 1.0  ->  x      (x int ou double)
# Só para números: c * 1 (char), b * 1 (bool) e tipos desconhecidos não são smell.
# Opção do grupo: a * 1.0 com a int também é smell e fica a; a conversão
# para double que o 1.0 fazia é ignorada.

def corrige_mult_um(n, ctx):
    match n:
        case Mul(x, IntLit(1) | FloatLit(1.0)) | Mul(IntLit(1) | FloatLit(1.0), x) \
                | Div(x, IntLit(1) | FloatLit(1.0)) if eh_numerica(x, ctx):
            return x
        case _:
            falha()


def deteta_mult_um(n, ctx):
    return se_aplica(corrige_mult_um, n, ctx)       # smell = a correção aplica-se


def injeta_mult_um(n, z, ctx):
    # não num 0 (1 * 0 seria também A3) nem num 1 / 1.0 (1 * 1.0 desfazia-se em 1)
    if n in NEUTROS_SOMA + NEUTROS_MULT or not eh_numerica(n, ctx):
        falha()
    return ctx.rng.choice([Mul(n, IntLit(1)), Mul(IntLit(1), n), Div(n, IntLit(1))])


# ---------------- A3: multiplicação por 0 ----------------------------
# x * 0, 0 * x, x * 0.0, 0.0 * x  ->  0 (o zero como estava escrito)
# Só para números (int ou double): c * 0, b * 0 e tipos desconhecidos não
# são smell. Opção do grupo: um double é tratado como número normal
# (ignora-se o caso NaN/infinito * 0).
# Só se corrige se x for puro: f(a) * 0 perdia a chamada e (a / b) * 0
# escondia uma possível divisão por zero. Esses são smell não corrigível.

def deteta_mult_zero(n, ctx):
    match n:
        case Mul(x, IntLit(0) | FloatLit(0.0)) | Mul(IntLit(0) | FloatLit(0.0), x) if eh_numerica(x, ctx):
            return True
        case _:
            return False


def corrige_mult_zero(n, ctx):
    match n:
        case Mul(x, (IntLit(0) | FloatLit(0.0)) as zero) | Mul((IntLit(0) | FloatLit(0.0)) as zero, x) \
                if eh_numerica(x, ctx) and puro(x):
            return zero
        case _:
            falha()


def injeta_mult_zero(n, z, ctx):
    if n != IntLit(0):                              # só onde já há um 0
        falha()
    p = parametro_seguro(z, ctx, {"int", "double"}) or IntLit(ctx.rng.randint(2, 9))
    return ctx.rng.choice([Mul(p, IntLit(0)), Mul(IntLit(0), p)])


# ---------------- A4: comparação com booleano -----------------------
# x == true, x != false  ->  x        x == false, x != true  ->  !x
# Só quando x é bool (variável, comparação, && / ||, função que devolve bool).
# Comparar um número com true/false (a == true com a int) não é smell, é um
# erro: não é detetado nem corrigido.

def corrige_comp_bool(n, ctx):
    match n:
        case Equals(x, BoolLit(True)) | Equals(BoolLit(True), x) \
                | NotEquals(x, BoolLit(False)) | NotEquals(BoolLit(False), x) if eh_booleana(x, ctx):
            return x
        case Equals(x, BoolLit(False)) | Equals(BoolLit(False), x) \
                | NotEquals(x, BoolLit(True)) | NotEquals(BoolLit(True), x) if eh_booleana(x, ctx):
            return UnaryOp("!", x)
        case _:
            falha()


def deteta_comp_bool(n, ctx):
    return se_aplica(corrige_comp_bool, n, ctx)     # smell = a correção aplica-se


def injeta_comp_bool(n, z, ctx):
    # não em literais: false -> true == false seria ambíguo de desfazer
    if isinstance(n, LITERAIS) or not eh_booleana(n, ctx):
        falha()
    opcoes = [Equals(n, BoolLit(True)), Equals(BoolLit(True), n), NotEquals(n, BoolLit(False))]
    match n:
        case UnaryOp("!", x) if eh_booleana(x, ctx):   # !x -> x == false (só se x for bool)
            opcoes.append(Equals(x, BoolLit(False)))
    return ctx.rng.choice(opcoes)


# ---------------- A5: dupla negação ---------------------------------
# !!x  ->  x   (x bool)          -(-x)  ->  x   (x int ou double)
# Só quando o tipo condiz com o operador. Fora disso não é smell:
#   !!a com a int é uma normalização para 0/1 (!!5 == 1)
#   -(-c), -(-b) (char, bool) e tipos desconhecidos

def corrige_dupla_neg(n, ctx):
    match n:
        case UnaryOp("!", UnaryOp("!", x)) if eh_booleana(x, ctx):
            return x
        case UnaryOp("-", UnaryOp("-", x)) if eh_numerica(x, ctx):
            return x
        case _:
            falha()


def deteta_dupla_neg(n, ctx):
    return se_aplica(corrige_dupla_neg, n, ctx)     # smell = a correção aplica-se


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
# Só para tipos comparáveis (int, double, char, bool). Strings ("a" == "a"
# compara endereços em C: é um erro) e tipos desconhecidos não são smell.
# Opção do grupo: um double é tratado como número normal (ignora-se o caso
# NaN, em que d != d seria verdadeiro).
# Só se corrige se x for puro: f(a) == f(a) chama f duas vezes (e pode dar
# valores diferentes) e (a / k) == (a / k) esconderia uma divisão por zero.
# Esses são smell não corrigível.

def comparavel(x, ctx):
    t = tipos_de(x, ctx)
    return bool(t) and t <= {"int", "double", "char", "bool"}


def deteta_auto_comp(n, ctx):
    match n:
        case Equals(a, b) | NotEquals(a, b) | LessThan(a, b) | LessEqual(a, b) \
                | GreaterThan(a, b) | GreaterEqual(a, b) if a == b and comparavel(a, ctx):
            return True
        case _:
            return False


def corrige_auto_comp(n, ctx):
    match n:
        case Equals(a, b) | LessEqual(a, b) | GreaterEqual(a, b) if a == b and comparavel(a, ctx) and puro(a):
            return BoolLit(True)
        case NotEquals(a, b) | LessThan(a, b) | GreaterThan(a, b) if a == b and comparavel(a, ctx) and puro(a):
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