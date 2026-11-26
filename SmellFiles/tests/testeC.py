"""Corre os testes de todos os smells C (testeC1.py ... testeC9.py).

    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeC
"""
import importlib
import sys

from projeto1.SDVM_lang.SmellFiles.tests.apoio_c import correr

resumo = []
for k in range(1, 10):
    m = importlib.import_module(f"projeto1.SDVM_lang.SmellFiles.tests.testeC{k}")
    resumo.append((m.CODIGO, correr(m.CODIGO, m.CASOS, m.TD)))

print("===== RESUMO =====")
for codigo, falhas in resumo:
    print(f"{codigo}: {'OK' if falhas == 0 else f'{falhas} FALHA(S)'}")
total = sum(f for _, f in resumo)
print("\n" + ("TUDO OK" if total == 0 else f"{total} FALHA(S) NO TOTAL"))
sys.exit(1 if total else 0)
