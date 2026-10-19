from dataclasses import dataclass
from parsy import generate, regex, string, ParseError
from declarations import identifier, variable_declaration, variable_declaration_core
from expressionParser import lexeme, pExp, whitespace


# Classes que representam as estruturas na árvore sintática (AST).
@dataclass
class Block:
    statements: list[object]


@dataclass
class IfStatement:
    condition: object
    then_branch: object
    else_branch: object | None = None


@dataclass
class WhileStatement:
    condition: object
    body: object


@dataclass
class ForStatement:
    initializer: object | None
    condition: object | None
    update: object | None
    body: object


@dataclass
class Assignment:
    target: str
    value: object


# Reconhece palavras reservadas completas, como "if" e "while".
def keyword(word):
    return lexeme(regex(rf"{word}\b"))


# Reconhece uma atribuição sem ponto e vírgula: i = i + 1.
@generate
def pAssignmentCore():
    target = yield identifier
    yield lexeme(string("="))
    value = yield pExp
    return Assignment(target, value)


# Cria parsers recursivos que partilham o mesmo parser de instruções.
# Os parsers opcionais podem ser substituídos na integração com os colegas.
def build_control_flow_parsers(
    simple_statement_parser,
    for_initializer_parser=None,
    for_update_parser=None,
):
    # O for aceita declarações ou atribuições na inicialização.
    if for_initializer_parser is None:
        for_initializer_parser = variable_declaration_core | pAssignmentCore

    # O for aceita atribuições ou expressões na atualização.
    if for_update_parser is None:
        for_update_parser = pAssignmentCore | pExp

    @generate
    def pStatement():
        yield whitespace
        return (yield (
            pBlock
            | pIfStatement
            | pWhileStatement
            | pForStatement
            | simple_statement_parser
        ))

    # Reconhece blocos de instruções entre chavetas.
    @generate
    def pBlock():
        yield whitespace
        yield lexeme(string("{"))
        statements = yield pStatement.many()
        yield lexeme(string("}"))
        return Block(statements)

    # Reconhece if com ou sem else.
    @generate
    def pIfStatement():
        yield whitespace
        yield keyword("if")
        yield lexeme(string("("))
        condition = yield pExp
        yield lexeme(string(")"))
        then_branch = yield pStatement
        else_branch = yield (keyword("else") >> pStatement).optional()
        return IfStatement(condition, then_branch, else_branch)

    # Reconhece ciclos while.
    @generate
    def pWhileStatement():
        yield whitespace
        yield keyword("while")
        yield lexeme(string("("))
        condition = yield pExp
        yield lexeme(string(")"))
        body = yield pStatement
        return WhileStatement(condition, body)

    # Reconhece ciclos for, incluindo i = i + 1 na atualização.
    @generate
    def pForStatement():
        yield whitespace
        yield keyword("for")
        yield lexeme(string("("))
        initializer = yield for_initializer_parser.optional()
        yield lexeme(string(";"))
        condition = yield pExp.optional()
        yield lexeme(string(";"))
        update = yield for_update_parser.optional()
        yield lexeme(string(")"))
        body = yield pStatement
        return ForStatement(initializer, condition, update, body)

    return pBlock, pIfStatement, pWhileStatement, pForStatement, pStatement


# Exemplos rápidos para executar este ficheiro isoladamente.
if __name__ == "__main__":
    # Instruções temporárias até à integração com o parser de instruções.
    pSimpleStatement = (
        variable_declaration
        | lexeme(string("print(1);"))
        | lexeme(string("print(2);"))
        | lexeme(string("break;"))
        | lexeme(string("continue;"))
    )

    pBlock, pIf, pWhile, pFor, pStatement = build_control_flow_parsers(
        pSimpleStatement
    )

    # Verifica as estruturas básicas e o novo formato de atribuição no for.
    tests = [
        ("Empty block", pBlock, "{}"),
        ("Nested blocks", pBlock, "{ { print(1); } }"),
        ("If with else", pIf, "if (x > 0) { print(1); } else { print(2); }"),
        ("While", pWhile, "while (x < 5) { print(1); }"),
        ("Empty for", pFor, "for (;;) { print(1); }"),
        ("For with declaration", pFor,
         "for (int i = 0; i < 5; i = i + 1) { print(1); }"),
        ("For with assignment", pFor,
         "for (i = 0; i < 5; i = i + 1) { print(1); }"),
        ("For with expression update", pFor,
         "for (int i = 0; i < 5; i + 1) { print(1); }"),
    ]

    for description, parser, source in tests:
        parser.parse(source)
        print(f"PASS - {description}")

    # Um bloco sem chaveta final tem de ser rejeitado.
    try:
        pBlock.parse("{ print(1);")
    except ParseError:
        print("PASS - Invalid block rejected")
    else:
        raise AssertionError("Invalid block was accepted")
