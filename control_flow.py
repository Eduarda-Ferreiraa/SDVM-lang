
from dataclasses import dataclass
from parsy import generate, regex, string, ParseError
from declarations import variable_declaration, variable_declaration_core
from expressionParser import lexeme, pExp, whitespace


# AST nodes
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


# Recognize complete keywords
def keyword(word):
    return lexeme(regex(rf"{word}\b"))


# Build recursive control-flow parsers
def build_control_flow_parsers(
    simple_statement_parser,
    for_initializer_parser=variable_declaration_core,
    for_update_parser=pExp,
):

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

    @generate
    def pBlock():
        yield whitespace
        yield lexeme(string("{"))

        statements = yield pStatement.many()

        yield lexeme(string("}"))
        return Block(statements)

    @generate
    def pIfStatement():
        yield whitespace
        yield keyword("if")
        yield lexeme(string("("))

        condition = yield pExp

        yield lexeme(string(")"))

        then_branch = yield pStatement

        else_branch = yield (
            keyword("else") >> pStatement
        ).optional()

        return IfStatement(
            condition, then_branch, else_branch
        )

    @generate
    def pWhileStatement():
        yield whitespace
        yield keyword("while")
        yield lexeme(string("("))

        condition = yield pExp

        yield lexeme(string(")"))

        body = yield pStatement

        return WhileStatement(condition, body)

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

        return ForStatement(
            initializer, condition, update, body
        )

    return (
        pBlock,
        pIfStatement,
        pWhileStatement,
        pForStatement,
        pStatement,
    )


# Standalone tests
if __name__ == "__main__":

    # Temporary statements for testing
    pSimpleStatement = (
        variable_declaration
        | lexeme(string("print(1);"))
        | lexeme(string("print(2);"))
        | lexeme(string("break;"))
        | lexeme(string("continue;"))
    )

    (
        pBlock,
        pIfStatement,
        pWhileStatement,
        pForStatement,
        pStatement,
    ) = build_control_flow_parsers(pSimpleStatement)

    tests = [
        ("Empty block", pBlock, "{}"),

        ("Multiple statements", pBlock,
         "{ print(1); print(2); }"),

        ("Nested blocks", pBlock,
         "{ { print(1); } }"),

        ("Variable in block", pBlock,
         "{ int x = 1; print(1); }"),

        ("If without braces", pIfStatement,
         "if (x > 10) print(1);"),

        ("If with else", pIfStatement,
         "if (x > 10) { print(1); } else { print(2); }"),

        ("While", pWhileStatement,
         "while (x < 5) { print(1); }"),

        ("Nested control flow", pBlock,
         "{ while (x < 5) { if (x > 1) print(2); } }"),

        ("For with expression update", pForStatement,
         "for (int i = 0; i < 5; i + 1) { print(1); }"),

        ("For with empty fields", pForStatement,
         "for (;;) { print(1); }"),
    ]

    
    # Run valid tests
    for description, parser, source in tests:
        result = parser.parse(source)
        print(f"PASS - {description}: {result}")

    # Test a block with a missing closing brace
    try:
        pBlock.parse("{ print(1);")
        print("FAIL - Invalid block was accepted")
    except ParseError:
        print("PASS - Invalid block was rejected")
