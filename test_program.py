import pytest
from parsy import ParseError
from parser import program, Program
from declarations import VariableDeclaration, ArrayDeclaration, FunctionDefinition
from statements import Assignment, Return, Print
from control_flow import WhileStatement, IfStatement

def test_empty_program():
    ast = program.parse("")
    assert isinstance(ast, Program)
    assert ast.declarations == []

def test_global_variables_and_arrays():
    code = """
    int contador = 0;
    double notas[3] = {10.5, 14.0, 18.2};
    bool ativo = true;
    """
    ast = program.parse(code)
    assert len(ast.declarations) == 3
    assert isinstance(ast.declarations[0], VariableDeclaration)
    assert isinstance(ast.declarations[1], ArrayDeclaration)

def test_full_program():
    code = """
    int total = 0;

    int soma(int a, int b) {
        return a + b;
    }

    void main() {
        int i = 0;
        while (i < 5) {
            if (i % 2 == 0) {
                total = soma(total, i);
            }
            i = i + 1;
        }
        print(total);
    }
    """
    ast = program.parse(code)
    assert isinstance(ast, Program)
    assert len(ast.declarations) == 3
    assert ast.declarations[0].name == "total"
    assert ast.declarations[1].name == "soma"
    assert ast.declarations[2].name == "main"

def test_invalid_syntax_rejected():
    invalid_code = """
    int x = 1;
    print(x);
    """
    with pytest.raises(ParseError):
        program.parse(invalid_code)