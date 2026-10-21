from pprint import pprint
from parser import program

# O teu código de exemplo
codigo_exemplo = """
int main() {
    int x = 0;
    if (x == 0) x = 1;
    else x = 2;
    while (x < 5) x = x + 1;
    for (int i = 0; i < 3; i = i + 1) print(i);
    if (x > 0) if (x > 1) x = 3; else x = 4;
    return 0;
}
"""

if __name__ == "__main__":
    try:
        # Executa o parser global definido em parser.py
        ast = program.parse(codigo_exemplo)
        print("--- AST Gerada com Sucesso ---")
        pprint(ast)
    except Exception as e:
        print(f"Erro ao fazer o parse do código: {e}")