from control_flow import build_control_flow_parsers, Block, IfStatement
from declarations import variable_declaration

# Build parsers using real variable declarations
pBlock, pIf, pWhile, pFor, pStatement = (
    build_control_flow_parsers(variable_declaration)
)

# Test integration with declarations and nested control flow
source = """
{
    int x = 1;

    if (x > 0) {
        int y = 2;
    }
}
"""

result = pBlock.parse(source)

assert isinstance(result, Block)
assert len(result.statements) == 2
assert isinstance(result.statements[1], IfStatement)

print("PASS - Control flow integration")
print(result)
