from parsy import ParseError, string
from control_flow import (
    Assignment, Block, IfStatement, WhileStatement, ForStatement,
    build_control_flow_parsers,
)
from declarations import VariableDeclaration, variable_declaration
from expressionParser import lexeme


# Usamos declarações reais e instruções print temporárias.
simple_statement = (
    variable_declaration
    | lexeme(string("print(1);"))
    | lexeme(string("print(2);"))
)

pBlock, pIf, pWhile, pFor, pStatement = build_control_flow_parsers(simple_statement)


# Testar blocos vazios, com várias instruções e aninhados.
assert pBlock.parse("{}") == Block([])
assert pBlock.parse("{ print(1); print(2); }") == Block(["print(1);", "print(2);"])
assert pBlock.parse("{ { print(1); } }") == Block([Block(["print(1);"])])


# Testar if e if/else.
assert isinstance(pIf.parse("if (x > 0) print(1);"), IfStatement)
assert pIf.parse("if (x > 0) { print(1); } else { print(2); }").else_branch == Block(["print(2);"])


# Testar while e estruturas de controlo aninhadas.
assert isinstance(pWhile.parse("while (x < 5) { print(1); }"), WhileStatement)
assert isinstance(pBlock.parse("{ while (x < 5) { if (x > 0) print(1); } }").statements[0], WhileStatement)


# Testar o for vazio e a inicialização por declaração.
assert pFor.parse("for (;;) { print(1); }") == ForStatement(None, None, None, Block(["print(1);"]))

for_result = pFor.parse("for (int i = 0; i < 5; i = i + 1) { print(1); }")
assert isinstance(for_result.initializer, VariableDeclaration)
assert isinstance(for_result.update, Assignment)
assert for_result.update.target == "i"


# Testar atribuições na inicialização e na atualização do for.
for_result = pFor.parse("for (i = 0; i < 5; i = i + 1) { print(1); }")
assert isinstance(for_result.initializer, Assignment)
assert isinstance(for_result.update, Assignment)


# Confirmar que também se continua a aceitar uma expressão na atualização.
assert pFor.parse("for (; i < 5; i + 1) { print(1); }").update is not None


# Verificar a integração com o parser de declarações.
block = pBlock.parse("{ int x = 1; if (x > 0) { int y = 2; } }")
assert isinstance(block.statements[0], VariableDeclaration)
assert isinstance(block.statements[1], IfStatement)


# Verificar que código com erros de sintaxe é rejeitado.
invalid_cases = [
    (pBlock, "{ print(1);"),
    (pIf, "if (x >) print(1);"),
    (pFor, "for (int i = 0 i < 5; ) { print(1); }"),
    (pFor, "for (i = ; i < 5; i = i + 1) { print(1); }"),
]

for parser, source in invalid_cases:
    try:
        parser.parse(source)
    except ParseError:
        continue
    raise AssertionError(f"Invalid code was accepted: {source}")


print("Tests OK")
