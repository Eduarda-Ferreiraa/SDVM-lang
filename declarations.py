from dataclasses import dataclass
from typing import Any

from parsy import generate, regex, string

from expressionParser import Exp, pExp, type_parser, lexeme


@dataclass
class VariableDeclaration:
    var_type: str
    name: str
    initializer: Exp | None = None


@dataclass
class ArrayDeclaration:
    var_type: str
    name: str
    size: int
    initializer: list[Exp] | None = None


@dataclass
class Parameter:
    param_type: str
    name: str


@dataclass
class FunctionDefinition:
    return_type: str
    name: str
    parameters: list[Parameter]
    body: Any


#palavras que não podem ser nomes 
RESERVED_WORDS = {
    "int", "double", "char", "bool", "void",
    "if", "else", "while", "for",
    "break", "continue", "return",
    "print", "read", "true", "false",
}

#reconhecem nomes
identifier_pattern = (
    r"(?!(?:"
    + "|".join(sorted(RESERVED_WORDS))
    + r")\b)[A-Za-z][A-Za-z0-9_]*"
)

identifier = lexeme(regex(identifier_pattern))

#função sem valor
return_type_parser = (
    type_parser
    | lexeme(regex(r"void\b"))
)

#tamanho array
integer_size = lexeme(regex(r"[0-9]+")).map(int)


#valores entre chavetas
array_initializer = (
    lexeme(string("{"))
    >> pExp.sep_by(lexeme(string(",")))
    << lexeme(string("}"))
)

#variável ou array([])
@generate
def variable_declaration_core():
    var_type = yield type_parser
    name = yield identifier

    bracket = yield lexeme(string("[")).optional()

    if bracket is not None:
        size = yield integer_size
        yield lexeme(string("]"))

        initializer = yield (
            lexeme(string("=")) >> array_initializer
        ).optional()

        return ArrayDeclaration(
            var_type=var_type,
            name=name,
            size=size,
            initializer=initializer,
        )

    initializer = yield (
        lexeme(string("=")) >> pExp
    ).optional()

    return VariableDeclaration(
        var_type=var_type,
        name=name,
        initializer=initializer,
    )


#reconhece a declaração completa
variable_declaration = (
    variable_declaration_core << lexeme(string(";"))
)



@generate
def parameter():
    param_type = yield type_parser
    name = yield identifier

    return Parameter(
        param_type=param_type,
        name=name,
    )


parameter_list = parameter.sep_by(lexeme(string(",")))


#parser de funções 
def make_function_definition(block_parser):
    @generate
    def function_definition():
        return_type = yield return_type_parser
        name = yield identifier

        yield lexeme(string("("))
        parameters = yield parameter_list
        yield lexeme(string(")"))

        body = yield block_parser

        return FunctionDefinition(
            return_type=return_type,
            name=name,
            parameters=parameters,
            body=body,
        )

    return function_definition