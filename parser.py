from dataclasses import dataclass
from parsy import eof

from expressionParser import whitespace
from declarations import (
    variable_declaration,
    make_function_definition,
    VariableDeclaration,
    ArrayDeclaration,
    FunctionDefinition,
)
from control_flow import build_control_flow_parsers
from statements import simple_statement

local_statement = variable_declaration | simple_statement


pBlock, pIfStatement, pWhileStatement, pForStatement, pStatement = build_control_flow_parsers(
    simple_statement_parser=local_statement
)

function_definition = make_function_definition(pBlock) # parser de definição de funções


declaration = variable_declaration | function_definition

@dataclass
class Program:
    declarations: list

program = (
    whitespace 
    >> declaration.many()
    << eof 
).map(Program)

