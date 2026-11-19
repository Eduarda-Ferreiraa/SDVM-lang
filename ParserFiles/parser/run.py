from pprint import pprint
from .parser import program

# O teu código de exemplo
codigo_exemplo = """
int main() {
    int year;
    bool divisible_by_four;
    bool divisible_by_hundred;
    bool divisible_by_four_hundred;

    read(year);
    divisible_by_four = year % 4 == 0;
    divisible_by_hundred = year % 100 == 0;
    divisible_by_four_hundred = year % 400 == 0;

    if (divisible_by_four && (!divisible_by_hundred || divisible_by_four_hundred)) {
        print("leap year");
    } else {
        print("common year");
    }

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