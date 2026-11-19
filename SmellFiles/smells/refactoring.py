# =====================================================================
# Refactoring (innermost)
# =====================================================================
# Cadeia aninhada, como nas aulas:
#     failTP `adhocTP` corrige_A1 `adhocTP` corrige_A2 ...
# - failTP (e não idTP): o innermost repete enquanto a worker tem sucesso;
#   com idTP teria sempre sucesso e nunca parava.
# - Aqui "o 1.º que acerta ganha" não é problema: o innermost volta a
#   aplicar a worker ao resultado, por isso um 2.º smell no mesmo nó é
#   corrigido na volta seguinte.

from collections import Counter
from functools import reduce

from StrategicProg.pyztrategic.zipper import toZipper
from StrategicProg.pyztrategic import strategy as st

from .analise import contexto
from .catalogo import seleciona


def corrigir(prog, codigos=None):
    """Devolve (programa corrigido, Counter de refactorings aplicados)."""
    ctx = contexto(prog)
    aplicados = Counter()

    def contado(s):
        def g(n):
            novo = s.corrige(n, ctx)                # raise se não se aplica
            aplicados[s.codigo] += 1
            return novo
        return g

    def encadeia(anterior, s):
        return lambda z: st.adhocTP(anterior, contado(s), z)

    corrigiveis = [s for s in seleciona(codigos) if s.corrige is not None]
    passo = reduce(encadeia, reversed(corrigiveis), st.failTP)
    return st.innermost(passo, toZipper(prog)).node(), aplicados