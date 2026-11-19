# =====================================================================
# Pretty-printer: AST da SDVM-lang  ->  código fonte
# =====================================================================
# Serve para mostrar o resultado do refactoring / da injeção como código.
# Põe só os parênteses necessários, de acordo com a tabela de precedências
# do README. Propriedade testada: program.parse(pretty(ast)) == ast.

from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import (
    IntLit, FloatLit, BoolLit, CharLit, StringLit, Ident, Or, And, Equals, NotEquals, LessThan, LessEqual, GreaterThan,
    GreaterEqual, Add, Sub, Mul, Div, Mod, UnaryOp, Cast, Index, FuncCall,
)
from projeto1.SDVM_lang.ParserFiles.parser.declarations import VariableDeclaration, ArrayDeclaration, FunctionDefinition
from projeto1.SDVM_lang.ParserFiles.parser.statements import (
    Break, Continue, Return, Print, Read, Assignment, ArrayAssignment,
    FunctionCallStatement,
)
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import Block, IfStatement, WhileStatement, ForStatement

# operador e nível de precedência (README: 1 = mais fraco)
BINARIOS = {
    Or: ("||", 1), And: ("&&", 2),
    Equals: ("==", 3), NotEquals: ("!=", 3),
    LessThan: ("<", 4), LessEqual: ("<=", 4), GreaterThan: (">", 4), GreaterEqual: (">=", 4),
    Add: ("+", 5), Sub: ("-", 5),
    Mul: ("*", 6), Div: ("/", 6), Mod: ("%", 6),
}
UNARIO = 7

IND = "    "


def literal(e):
    match e:
        case BoolLit(v):
            return "true" if v else "false"
        case FloatLit(v):
            s = repr(v)                     # 1e-05 -> 1.0e-05: o parser exige o ponto
            if "e" in s and "." not in s.split("e")[0]:
                s = s.replace("e", ".0e", 1)
            return s
        case IntLit(v) | CharLit(v) | StringLit(v):     # char/string já trazem as aspas
            return str(v)


def exp(e, nivel=0):
    """nivel = precedência mínima exigida pelo contexto."""
    match e:
        case IntLit() | FloatLit() | BoolLit() | CharLit() | StringLit():
            return literal(e)
        case Ident(n):
            return n
        case Index(nome, i):
            return f"{nome}[{exp(i)}]"
        case FuncCall(n, args):
            return f"{n}({', '.join(exp(a) for a in args)})"
        case UnaryOp(op, x):
            s = exp(x, UNARIO)
            if op in "+-" and s[:1] in ("+", "-"):      # evita "--x"
                s = f"({s})"
            return _par(op + s, UNARIO, nivel)
        case Cast(t, x):
            return _par(f"({t}){exp(x, UNARIO)}", UNARIO, nivel)
        case _ if type(e) in BINARIOS:
            op, p = BINARIOS[type(e)]
            # associatividade à esquerda: o filho direito precisa de nível p+1
            return _par(f"{exp(e.left, p)} {op} {exp(e.right, p + 1)}", p, nivel)
    raise ValueError(f"expressão desconhecida: {e!r}")


def _par(s, p, nivel):
    return f"({s})" if p < nivel else s


def nucleo(s):
    """Declaração/atribuição sem ';' (usado também no for)."""
    match s:
        case VariableDeclaration(t, n, init):
            return f"{t} {n}" + (f" = {exp(init)}" if init is not None else "")
        case ArrayDeclaration(t, n, tam, init):
            ini = "" if init is None else " = {" + ", ".join(exp(x) for x in init) + "}"
            return f"{t} {n}[{tam}]{ini}"
        case Assignment(alvo, v):
            return f"{alvo} = {exp(v)}"
        case ArrayAssignment(alvo, i, v):
            return f"{alvo}[{exp(i)}] = {exp(v)}"
    return exp(s)          # update do for pode ser uma expressão


def corpo(s, ind):
    if isinstance(s, Block):
        return " " + stmt(s, ind)
    return "\n" + IND * (ind + 1) + stmt(s, ind + 1)


def stmt(s, ind=0):
    match s:
        case Block(ss):
            if not ss:
                return "{ }"
            dentro = "".join(IND * (ind + 1) + stmt(x, ind + 1) + "\n" for x in ss)
            return "{\n" + dentro + IND * ind + "}"
        case VariableDeclaration() | ArrayDeclaration() | Assignment() | ArrayAssignment():
            return nucleo(s) + ";"
        case IfStatement(c, then, els):
            if els is not None and isinstance(then, IfStatement):   # dangling else
                then = Block([then])
            r = f"if ({exp(c)})" + corpo(then, ind)
            if els is not None:
                r += " else" if isinstance(then, Block) else "\n" + IND * ind + "else"
                r += " " + stmt(els, ind) if isinstance(els, IfStatement) else corpo(els, ind)
            return r
        case WhileStatement(c, b):
            return f"while ({exp(c)})" + corpo(b, ind)
        case ForStatement(i, c, u, b):
            partes = [nucleo(i) if i is not None else "",
                      exp(c) if c is not None else "",
                      nucleo(u) if u is not None else ""]
            return "for (" + "; ".join(partes).rstrip() + ")" + corpo(b, ind)
        case Return(None):
            return "return;"
        case Return(v):
            return f"return {exp(v)};"
        case Print(v):
            return f"print({exp(v)});"
        case Read(t):
            return f"read({t});"
        case Break():
            return "break;"
        case Continue():
            return "continue;"
        case FunctionCallStatement(call):
            return exp(call) + ";"
    raise ValueError(f"instrução desconhecida: {s!r}")


def pretty(prog):
    partes = []
    for d in prog.declarations:
        if isinstance(d, FunctionDefinition):
            ps = ", ".join(f"{p.param_type} {p.name}" for p in d.parameters)
            partes.append(f"{d.return_type} {d.name}({ps}) " + stmt(d.body, 0))
        else:
            partes.append(stmt(d, 0))
    return "\n\n".join(partes) + "\n"