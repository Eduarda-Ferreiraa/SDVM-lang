from projeto1.SDVM_lang.ParserFiles.parser.control_flow import (
    Block, IfStatement, WhileStatement,
)

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import (
    BoolLit, IntLit, LessThan, UnaryOp, Equals, NotEquals, LessEqual, GreaterThan, GreaterEqual, And, Or,
)

from projeto1.SDVM_lang.ParserFiles.parser.declarations import (
    FunctionDefinition, VariableDeclaration, ArrayDeclaration,
)

from projeto1.SDVM_lang.ParserFiles.parser.statements import (
    Assignment, Print, Return, Break, Continue,
)
from .smell import Smell
from .analise import (
    falha, puro, eh_booleana, pai,
)

# ----------------B1: condição constante ---------------------------

def deteta_cond_const(n, ctx):
    match n:
        case IfStatement(BoolLit(True), then_branch, else_branch):
            return True
        case IfStatement(BoolLit(False), then_branch, else_branch):
            return True
        case WhileStatement(BoolLit(False), body):
            return True
        case _:
            return False

def corrige_cond_const(n, ctx):
    match n:
        case IfStatement(BoolLit(True), then_branch, else_branch):
            return then_branch
        case IfStatement(BoolLit(False), then_branch, else_branch):
            return else_branch if else_branch is not None else Block([])                       
        case WhileStatement(BoolLit(False), body):
            return Block([])
        case _:
            falha()


def injeta_cond_const(n, z, ctx):
    p = pai(z)

    # não podemos substituir o corpo principal de uma função nem injetar em blocos vazios
    if not isinstance(n, Block) or not n.statements or isinstance(p, FunctionDefinition):
        falha()

    # evita dangling else: não mete um if dentro do ramo de outro if que já tenha else
    if isinstance(p, IfStatement) and p.else_branch is not None:
        falha()

    return ctx.rng.choice([
        IfStatement(BoolLit(True), n, None),
        IfStatement(BoolLit(False), Block([]), n),
    ])

# ---------------- B2: ramos iguais ---------------------------

def deteta_ramos_iguais(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, else_branch) if else_branch is not None and then_branch == else_branch:
            return True
        case _:
            return False

def corrige_ramos_iguais(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, else_branch) if else_branch is not None and then_branch == else_branch and puro(condicao):
            return then_branch
        case _:
            falha()

def injeta_ramos_iguais(n, z, ctx):
    p = pai(z)

    # não podemos substituir o corpo principal de uma função por um IfStatement
    if not isinstance(n, Block) or not n.statements or isinstance(p, FunctionDefinition):
        falha()

    # evita dangling else: não mete um if dentro do ramo de outro if que já tenha else
    if isinstance(p, IfStatement) and p.else_branch is not None:
        falha()

    cond = LessThan(IntLit(0), IntLit(1)) # expressão que é sempre verdade (0<1) - não ativa o A6 nem o B1
    return IfStatement(cond, n, n)

# ---------------- B3: ramos then vazio ---------------------------

def deteta_empy_then(n, ctx):
    match n:
        case IfStatement(condicao, Block([]), else_branch) if not isinstance(condicao, BoolLit): # ignora o caso de serem condições constantes (B1)
            return True
        case _:
            return False

def corrige_empty_then(n, ctx):
    match n:
        # vamos ter de verificar se não são condições constantes para não entrar no B1
        
        # 1º caso: temos de ver se a condição não é do tipo f(x) e muda variáveis
        case IfStatement(condicao, Block([]), None) if not isinstance(condicao, BoolLit) and puro(condicao):
            return Block([])
            
        # 2º caso: 
        case IfStatement(condicao, Block([]), else_branch) if not isinstance(condicao, BoolLit) and else_branch is not None and else_branch != Block([]):
            novo_then = else_branch if isinstance(else_branch, Block) else Block([else_branch])
            # se o then já vier com {} fica igual, senao temos de o meter dentro de chavetas
            return IfStatement(UnaryOp("!", condicao), novo_then, None)
            
        case _:
            falha()
            
def injeta_empy_then(n, z, ctx):
    match n:
        case IfStatement(condicao, Block() as then_branch, None) if then_branch != Block([]) and eh_booleana(condicao, ctx) and not isinstance(condicao, UnaryOp):
            return IfStatement(UnaryOp("!", condicao), Block([]), then_branch)
        case _:
            falha()

# ---------------- B4: ramos else vazio ---------------------------

def deteta_empy_else(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, Block([])) if not isinstance(condicao, BoolLit) and then_branch != Block([]): # ignora o caso de serem condições constantes (B1) ou ambos vazios (B3)
            return True
        case _:
            return False

def corrige_empty_else(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, Block([])) if not isinstance(condicao, BoolLit) and then_branch != Block([]):
            return IfStatement(condicao, then_branch, None)
        case _:
            falha()

def injeta_empy_else(n, z, ctx):
    match n:
        case IfStatement(condicao, then_branch, None) if not isinstance(condicao, BoolLit) and isinstance(then_branch, Block) and then_branch != Block([]):
            return IfStatement(condicao,then_branch, Block([]))
        case _:
            falha()

# ---------------- B5: ramos booleanos ---------------------------

# para os casos em que temos {return x;} dentro de chavetas
def unica_instr(ramo):
    match ramo:
        case Block([stmt]):
            return stmt
        case _:
            return ramo

def deteta_ramos_bool(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, else_branch) if not isinstance(condicao, BoolLit) and else_branch is not None:
            match (unica_instr(then_branch), unica_instr(else_branch)):
                case (Return(BoolLit(b1)), Return(BoolLit(b2))) if b1 != b2:
                    return True
                case (Assignment(v1, BoolLit(b1)), Assignment(v2, BoolLit(b2))) if b1 != b2 and v1 == v2:
                    return True
                case _:
                    return False
        case _:
            return False

def corrige_ramos_bool(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, else_branch) if not isinstance(condicao, BoolLit) and else_branch is not None:
            match (unica_instr(then_branch), unica_instr(else_branch)):
                case (Return(BoolLit(b1)), Return(BoolLit(b2))) if b1 != b2:
                    if b1 == True:
                        return Return(condicao)
                    else:
                        return Return(UnaryOp("!", condicao))
                case (Assignment(v1, BoolLit(b1)), Assignment(v2, BoolLit(b2))) if b1 != b2 and v1 == v2:
                    if b1 == True:
                        return Assignment(v1, condicao)
                    else:
                        return Assignment(v1, UnaryOp("!", condicao))
                case _:
                    falha()
        case _:
            falha()

BOOL_EXPR = (Equals, NotEquals, LessThan, LessEqual, GreaterThan, GreaterEqual, And, Or)

def injeta_ramos_bool(n, z, ctx):
    match n:
        case Return(exp) if isinstance(exp, BOOL_EXPR):
            return IfStatement(exp, Block([Return(BoolLit(True))]), Block([Return(BoolLit(False))]))
        case Assignment(v, exp) if isinstance(exp, BOOL_EXPR):
            return IfStatement(exp, Block([Assignment(v, BoolLit(True))]), Block([Assignment(v, BoolLit(False))]))
        case _:
            falha()

# ---------------- B6: if redundante ---------------------------

def deteta_if_redundante(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, None) if not isinstance(condicao, BoolLit):
            match unica_instr(then_branch):
                case IfStatement(condicao2, then2, None) if not isinstance(condicao2, BoolLit):
                    return True
                case _:
                    return False
        case _:
            return False

def corrige_if_redundante(n, ctx):
    match n:
        case IfStatement(condicao, then_branch, None) if not isinstance(condicao, BoolLit):
            match unica_instr(then_branch):
                case IfStatement(condicao2, then2, None) if not isinstance(condicao2, BoolLit):
                    novo_then = then2 if isinstance(then2, Block) else Block([then2])
                    return IfStatement(And(condicao,condicao2), novo_then, None)
                case _:
                    falha()
        case _:
            falha()

def injeta_if_redundante(n, z, ctx):
    p = pai(z)
    if isinstance(p, IfStatement) and p.else_branch is not None:
        falha()
    match n:
        case IfStatement(And(c1, c2), then, None):
            return IfStatement(c1, Block([IfStatement(c2, then, None)]), None)
        case _:
            falha()

# ---------------- B7: bloco redundante ---------------------------

DECLS = (VariableDeclaration, ArrayDeclaration)

def sem_declaracoes(bloco):
    match bloco:
        case Block(stmts):
            return not any(isinstance(s, DECLS) for s in stmts) # true se nenhuma for declaração de variável ou array -> podemos tirar chavetas
        case _:
            return False

def deteta_bloco_redundante(n, ctx):
    match n:
        case Block(stmts): # ve se para cada bloco exterior alguma das instrucoes de dentro é um bloco (nao associado a if/while/etc)
            return any(isinstance(s, Block) and sem_declaracoes(s) for s in stmts)
        case _:
            return False

def corrige_bloco_redundante(n, ctx):
    match n:
        case Block(stmts):
            novos = []
            mudou = False
            for s in stmts:
                if isinstance(s, Block) and sem_declaracoes(s):
                    match s:
                        case Block(inner):
                            novos.extend(inner)
                            mudou = True
                else:
                    novos.append(s)
            if not mudou:
                falha()
            return Block(novos)
        case _:
            falha()

def injeta_bloco_redundante(n, z, ctx):
    match n:
        case Block(stmts):
            for i, s in enumerate(stmts): # todas as instruções com índice i e instrução s
                if not isinstance(s, (*DECLS, Block)):
                    novos = list(stmts)
                    novos[i] = Block([s])
                    return Block(novos)
            falha()
        case _:
            falha()

# ---------------- B8: código inalcançável ---------------------------

SALTOS = (Return, Break, Continue)

def deteta_codigo_inalcancavel(n, ctx):
    match n:
        case Block(stmts): # detetar blocos
            for i in range(len(stmts) - 1): # percorre todas as instruções a ver se há código inalcansavel
                if isinstance(stmts[i], SALTOS): # se houver um salto antes de acabar o bloco entao depois dele tem codigo que nunca é executado
                    return True
            return False # se o salto for a ultima instrucao entao nao ha nada depois dele
        case _:
            return False

def corrige_codigo_inalcancavel(n, ctx):
    match n:
        case Block(stmts):
            for i in range(len(stmts) - 1):
                if isinstance(stmts[i], SALTOS):
                    return Block(stmts[:i + 1]) # fica só com tudo desde o inicio até à instrução i inclusive
            falha()
        case _:
            falha()

def injeta_codigo_inalcancavel(n, z, ctx):
    match n:
        case Block(stmts) if len(stmts) >= 1 and isinstance(stmts[-1], SALTOS):
            for i in range(len(stmts) - 1): # para não injetar o smell 2x no mesmo bloco senao nao conta
                if isinstance(stmts[i], SALTOS):
                    falha()
            return Block(stmts + [Print(IntLit(0))]) # colocar algo depois do salto
        case _:
            falha()

# ---------------- catálogo deste grupo -------------------------------

SMELLS = [
    Smell("B1", "condição constante", deteta_cond_const, corrige_cond_const, injeta_cond_const, 3),
    Smell("B2", "ramos iguais", deteta_ramos_iguais, corrige_ramos_iguais, injeta_ramos_iguais, 3),
    Smell("B3", "then vazio", deteta_empy_then, corrige_empty_then, injeta_empy_then, 2),
    Smell("B4", "else vazio", deteta_empy_else, corrige_empty_else, injeta_empy_else, 1),
    Smell("B5", "ramos bool", deteta_ramos_bool, corrige_ramos_bool, injeta_ramos_bool, 2),
    Smell("B6", "if redundante", deteta_if_redundante, corrige_if_redundante, injeta_if_redundante, 2),
    Smell("B7", "bloco redundante", deteta_bloco_redundante, corrige_bloco_redundante, injeta_bloco_redundante, 1),
    Smell("B8", "codigo inalcansavel", deteta_codigo_inalcancavel, corrige_codigo_inalcancavel, injeta_codigo_inalcancavel, 3)
]
