"""Apoio partilhado pelos testes dos smells C (testeC1.py ... testeC9.py).

Cada teste define CODIGO, CASOS e TD e chama main(). Um caso é
(descrição, esperado, programa):
  - esperado int:   nº de ocorrências;
  - esperado lista: o que deve ser assinalado (nomes de variáveis, de
    funções ou valores de literais), por qualquer ordem.
TD = (programa, minutos esperados) ou None.
Para cada caso também se verifica que repetir a deteção dá o mesmo resultado.
"""
import sys

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import IntLit, FloatLit
from projeto1.SDVM_lang.ParserFiles.parser.declarations import FunctionDefinition
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty, stmt
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, relatorio
from projeto1.SDVM_lang.SmellFiles.smells.smells_1 import nome_declarado


# ------------------------------------------------------------ geradores de código

def prints(n):
    return " ".join("print(total);" for _ in range(n))


def funcao(corpo, nome="f"):
    return f"void {nome}(int total) {{ {corpo} }}"


def ifs_aninhados(n, dentro="print(total);"):
    s = dentro
    for _ in range(n):
        s = f"if (total > 0) {{ {s} }}"
    return s


def condicao(n_ops, op="&&"):
    """Condição com n_ops operadores (n_ops + 1 comparações)."""
    return f" {op} ".join(["total > 0"] * (n_ops + 1))


# ------------------------------------------------------------ execução

def rotulo(n):
    match n:
        case FunctionDefinition():
            return n.name
        case IntLit(v) | FloatLit(v):
            return str(v)
    nome = nome_declarado(n)
    if nome is not None:
        return nome
    try:
        return " ".join(stmt(n).split())[:80]
    except Exception:
        return type(n).__name__


def correr(codigo, casos, td=None):
    """Corre os casos de um smell; devolve o nº de falhas."""
    print(f"===== {codigo} =====")
    falhas = 0
    for descricao, esperado, src in casos:
        try:
            p = program.parse(src)
            achados = [rotulo(n) for c, n, _ in detetar(p, [codigo])]
            repetido = [rotulo(n) for c, n, _ in detetar(p, [codigo])]
        except Exception as e:
            falhas += 1
            print(f"ERRO {descricao}\n       {type(e).__name__}: {e}\n       programa: {src}")
            continue
        if isinstance(esperado, int):
            ok = len(achados) == esperado
            mostra_esp = esperado
        else:
            ok = sorted(achados) == sorted(map(str, esperado))
            mostra_esp = sorted(map(str, esperado))
        ok = ok and sorted(achados) == sorted(repetido)
        falhas += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {descricao}")
        print(f"       esperado {mostra_esp}, detetado {sorted(achados)}")
        if not ok:
            if sorted(achados) != sorted(repetido):
                print(f"       a deteção repetida deu outro resultado: {sorted(repetido)}")
            print("       programa:\n" + "\n".join("         " + l for l in pretty(p).splitlines()))
    if td is not None:
        src, minutos = td
        try:
            linhas = relatorio(program.parse(src), [codigo])
            obtido = next((l[5] for l in linhas if l[0] == codigo), 0)
        except Exception as e:
            obtido = f"{type(e).__name__}: {e}"
        ok = obtido == minutos
        falhas += not ok
        print(f"{'OK  ' if ok else 'FAIL'} TD = {minutos} min (detetado {obtido})")
    print(f"--> {codigo}: {'TUDO OK' if falhas == 0 else f'{falhas} FALHA(S)'}\n")
    return falhas


def main(codigo, casos, td=None):
    sys.exit(1 if correr(codigo, casos, td) else 0)
