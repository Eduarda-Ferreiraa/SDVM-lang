import pytest
from expressionParser import Val, Add, Ident, FuncCall
from statements import (
    pBreak,
    pContinue,
    pReturn,
    pPrint,
    pRead,
    pAssignment,
    pFunctionCallStatement,
    simple_statement,
    Break,
    Continue,
    Return,
    Print,
    Read,
    Assignment,
    ArrayAssignment,
    FunctionCallStatement,
)

# 1. Testes de instruções válidas e verificação da AST gerada
def test_break():
    assert pBreak.parse("break;") == Break()
    assert pBreak.parse("  break ; ") == Break()

def test_continue():
    assert pContinue.parse("continue;") == Continue()
    assert pContinue.parse(" continue ; ") == Continue()

def test_return():
    # Return sem valor
    assert pReturn.parse("return;") == Return(value=None)
    assert pReturn.parse(" return ; ") == Return(value=None)
    # Return com expressão
    assert pReturn.parse("return 5;") == Return(value=Val(5))
    assert pReturn.parse("return x + 1;") == Return(value=Add(Ident("x"), Val(1)))

def test_print():
    assert pPrint.parse("print(10);") == Print(value=Val(10))
    assert pPrint.parse("print(x + 2);") == Print(value=Add(Ident("x"), Val(2)))

def test_read():
    assert pRead.parse("read(idade);") == Read(target="idade")
    assert pRead.parse(" read ( x ) ; ") == Read(target="x")

def test_assignment():
    # Variável simples
    assert pAssignment.parse("x = 5;") == Assignment(target="x", value=Val(5))
    # Elemento de array
    assert pAssignment.parse("lista[0] = 5;") == ArrayAssignment(
        target="lista", index=Val(0), value=Val(5)
    )

def test_function_call():
    res = pFunctionCallStatement.parse("foo();")
    assert res == FunctionCallStatement(call=FuncCall(name="foo", args=[]))

# 2. Testes de casos que DEVEM falhar (sintaxe inválida)
@pytest.mark.parametrize("parser,source", [
    (pBreak, "break"),            # Falta ';'
    (pContinue, "continue"),      # Falta ';'
    (pPrint, "print();"),         # Print vazio
    (pPrint, "print(x)"),         # Falta ';'
    (pRead, "read();"),           # Read sem variável
    (pRead, "read(10);"),         # Read com literal numérico em vez de identificador
    (pAssignment, "x = ;"),       # Sem valor
    (pAssignment, "x[0 = 5;"),    # Falta ']'
    (pFunctionCallStatement, "foo;"),  # Não é chamada com '()'
])
def test_statements_invalid(parser, source):
    with pytest.raises(Exception):
        parser.parse(source)