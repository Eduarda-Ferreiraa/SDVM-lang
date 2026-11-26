"""C4 (condição complexa): mais de MAX_OPERADORES_LOGICOS && / || numa condição.

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC4
"""
from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import main, funcao, condicao
from projeto1.SDVM_lang.SmellFiles.smells.smells_design import MAX_OPERADORES_LOGICOS as O

CODIGO = "C4"
H = "bool h(bool b) { return b; }"

CASOS = [
    (f"if com {O} operadores -> 0", 0, funcao(f"if ({condicao(O)}) {{ print(total); }}")),
    (f"if com {O + 1} operadores -> 1", 1, funcao(f"if ({condicao(O + 1)}) {{ print(total); }}")),
    (f"só || ({O + 1}) -> 1", 1, funcao(f"if ({condicao(O + 1, '||')}) {{ print(total); }}")),
    ("&& e || misturados contam os dois -> 1", 1,
     funcao("if (total > 0 && total < 9 || total == 20 && total != 5 || total == 30) { print(total); }")),
    ("parênteses não mudam a contagem -> 1", 1,
     funcao("if ((total > 0 && total < 9) && (total != 5 && total != 6) && total != 7) { print(total); }")),
    ("o ! não conta como operador -> 0", 0,
     funcao(" && ".join(["!(total > 0)"] * (O + 1)).join(["if (", ") { print(total); }"]))),
    ("while com condição complexa -> 1", 1,
     funcao(f"while ({condicao(O + 1)}) {{ total = total - 1; }}")),
    ("for com condição complexa -> 1", 1,
     funcao(f"for (int i = 0; {condicao(O + 1)}; i = i + 1) {{ print(i); }}")),
    ("for sem condição -> 0 (sem erro)", 0,
     funcao("for (;;) { break; }")),
    ("condição complexa num else if -> 1", 1,
     funcao(f"if (total > 0) {{ print(1); }} else if ({condicao(O + 1)}) {{ print(2); }}")),
    ("if e else if, ambos complexos -> 2", 2,
     funcao(f"if ({condicao(O + 1)}) {{ print(1); }} else if ({condicao(O + 1)}) {{ print(2); }}")),
    ("if complexo com outro if complexo dentro -> 2", 2,
     funcao(f"if ({condicao(O + 1)}) {{ if ({condicao(O + 1)}) {{ print(total); }} }}")),
    ("expressão complexa numa atribuição -> 0 (não é condição)", 0,
     f"void f(int total) {{ bool ok = false; ok = {condicao(O + 2)}; print(ok); }}"),
    ("expressão complexa num return -> 0", 0,
     f"bool f(int total) {{ return {condicao(O + 2)}; }}"),
    ("operadores dentro do argumento de uma função na condição -> 1 (contam)", 1,
     H + f" void f(int total) {{ if (h({condicao(O + 1)})) {{ print(total); }} }}"),
]

TD = (funcao(f"if ({condicao(O + 1)}) {{ print(1); }} while ({condicao(O + 1)}) {{ break; }}"), 20)

if __name__ == "__main__":
    main(CODIGO, CASOS, TD)
