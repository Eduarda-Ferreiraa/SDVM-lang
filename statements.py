from parsy import generate, regex, string
from dataclasses import dataclass
# imports dos outros ficheiros
from expressionParser import Exp, pExp, pPostfix, FuncCall, lexeme, whitespace
from declarations import identifier

def keyword(word: str):
    return lexeme(regex(rf"{word}\b")) 


# -----------Classes------------

@dataclass
class Break:
    pass

@dataclass
class Continue:
    pass

@dataclass
class Return:
    value: Exp | None = None

@dataclass
class Print:
    value: Exp

@dataclass
class Read:
    target: str

@dataclass
class Assignment: 
    target: str
    value: Exp

@dataclass
class ArrayAssignment:
    target: str
    index: Exp
    value: Exp

@dataclass
class FunctionCallStatement:
    call: FuncCall 

# ------------Funções------------

@generate
def pBreak():
    yield whitespace
    yield keyword("break")
    yield lexeme(string(";"))
    return Break()

@generate
def pContinue():
    yield whitespace
    yield keyword("continue")
    yield lexeme(string(";"))
    return Continue()

@generate
def pReturn():
    yield whitespace
    yield keyword("return")
    is_void = yield lexeme(string(";")).optional()
    if is_void is not None:
        return Return(value=None)

    val = yield pExp
    yield lexeme(string(";"))
    return Return(value=val)

@generate
def pPrint():
    yield whitespace
    yield keyword("print")
    yield lexeme(string("("))
    val = yield pExp
    yield lexeme(string(")"))
    yield lexeme(string(";"))
    return Print(value=val)

@generate
def pRead():
    yield whitespace
    yield keyword("read")
    yield lexeme(string("("))
    val = yield identifier
    yield lexeme(string(")"))
    yield lexeme(string(";"))
    return Read(target=val)

@generate
def pAssignment():
    yield whitespace
    variavel = yield lexeme(identifier)
    is_array = yield (lexeme(string("["))).optional()
    indice = None
    if is_array is not None:
        indice = yield pExp
        yield lexeme(string("]"))
    yield lexeme(string("="))
    val = yield pExp
    yield lexeme(string(";"))
    if indice is not None:
        return ArrayAssignment(target= variavel, index=indice, value=val)
    return(Assignment(target=variavel, value=val))

@generate
def pFunctionCallStatement():
    yield whitespace
    exp = yield pPostfix 
    if not isinstance(exp, FuncCall):
        return (yield string("__fail__"))
    yield lexeme(string(";"))
    return FunctionCallStatement(call=exp)

simple_statement = (
    pBreak
    | pContinue
    | pReturn
    | pPrint
    | pRead
    | pAssignment
    | pFunctionCallStatement
)

