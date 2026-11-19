from pprint import pprint
from parsy import ParseError, string

from declarations import (
    VariableDeclaration,
    ArrayDeclaration,
    Parameter,
    FunctionDefinition,
    variable_declaration,
    parameter_list,
    return_type_parser,
    make_function_definition,
    lexeme,
)
from expressionParser import Val, Add, whitespace


def declarar(texto):
    return (whitespace >> variable_declaration).parse(texto)


assert declarar("int idade;") == VariableDeclaration(
    "int", "idade", None
)

assert declarar("double altura = 1.65;") == VariableDeclaration(
    "double", "altura", Val(1.65)
)

assert declarar("char letra = 'a';") == VariableDeclaration(
    "char", "letra", Val("'a'")
)

assert declarar("bool ativo = true;") == VariableDeclaration(
    "bool", "ativo", Val(True)
)

assert declarar("int total = 2 + 3;") == VariableDeclaration(
    "int", "total", Add(Val(2), Val(3))
)

assert declarar("int valores[5];") == ArrayDeclaration(
    "int", "valores", 5, None
)

assert declarar("int valores[3] = {1, 2, 3};") == ArrayDeclaration(
    "int", "valores", 3, [Val(1), Val(2), Val(3)]
)

assert declarar("int valores[3] = {};") == ArrayDeclaration(
    "int", "valores", 3, []
)

assert parameter_list.parse("int a, double b") == [
    Parameter("int", "a"),
    Parameter("double", "b"),
]

assert parameter_list.parse("") == []
assert return_type_parser.parse("void") == "void"


# Bloco vazio só para testar a parte das funções.
bloco = (
    lexeme(string("{")) >> lexeme(string("}"))
).result([])

funcao = make_function_definition(bloco)

assert funcao.parse("int soma(int a, int b) {}") == FunctionDefinition(
    "int",
    "soma",
    [Parameter("int", "a"), Parameter("int", "b")],
    [],
)

assert funcao.parse("void mostrar() {}") == FunctionDefinition(
    "void", "mostrar", [], []
)


invalidos = [
    "void idade;",
    "int return;",
    "int 2idade;",
    "int valores[x];",
    "int valores[-2];",
    "int idade = ;",
    "int idade",
    "int valores[3] = {1, 2,};",
]

for texto in invalidos:
    try:
        declarar(texto)
    except ParseError:
        continue
    raise AssertionError(f"Devia ter falhado: {texto}")


print("Testes OK")
pprint(declarar("int total = 2 + 3;"))