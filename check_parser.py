"""Verifica o parser: programas válidos têm de ser aceites, inválidos têm de ser rejeitados.

Colocar este ficheiro na mesma pasta que parser.py, expressionParser.py, declarations.py,
statements.py e control_flow.py. Requisitos: Python >= 3.12 e `pip install parsy`.

    python check_parser.py                      # corre tests/valid e tests/invalid
    python check_parser.py ../examples          # + os exemplos do repositório (têm de ser aceites)
    python check_parser.py --reject outra_pasta # + pasta de programas que têm de ser rejeitados
"""
import argparse
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from parsy import ParseError   # noqa: E402
from parser import program     # noqa: E402


def files_in(folder):
    return sorted(p for p in glob.glob(os.path.join(folder, "*")) if os.path.isfile(p))


def parses(path):
    # newline="" preserva \r\n tal como está no ficheiro
    with open(path, encoding="utf-8", newline="") as f:
        src = f.read()
    try:
        program.parse(src)
        return True, ""
    except ParseError as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accept", nargs="*", help="pastas cujos programas têm de ser aceites")
    ap.add_argument("--reject", action="append", default=[],
                    help="pastas cujos programas têm de ser rejeitados")
    args = ap.parse_args()

    accept = args.accept + [os.path.join(HERE, "tests", "valid")]
    reject = args.reject + [os.path.join(HERE, "tests", "invalid")]
    failures = 0

    for folder in accept:
        paths = files_in(folder)
        if not paths:
            print(f"(sem ficheiros em {folder})")
            continue
        print(f"\n== devem ser ACEITES: {folder}")
        for p in paths:
            ok, err = parses(p)
            print(f"  {'OK  ' if ok else 'FAIL'} {os.path.basename(p)}" + ("" if ok else f"   -> {err[:110]}"))
            failures += not ok

    for folder in reject:
        paths = files_in(folder)
        if not paths:
            print(f"(sem ficheiros em {folder})")
            continue
        print(f"\n== devem ser REJEITADOS: {folder}")
        for p in paths:
            ok, _ = parses(p)
            if ok:
                print(f"  FAIL {os.path.basename(p)}   -> foi aceite e devia ser rejeitado")
                failures += 1
        print(f"  {len(paths)} programas, {sum(1 for p in paths if parses(p)[0])} aceites indevidamente")

    print("\n" + ("TUDO OK" if failures == 0 else f"{failures} FALHA(S)"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
