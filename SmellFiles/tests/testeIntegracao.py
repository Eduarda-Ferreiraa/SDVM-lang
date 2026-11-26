"""Teste de integração: programas grandes com smells A e C misturados, vários
smells no mesmo sítio, e a correção (refactoring) por cima.

Para cada programa verifica:
  1. antes de corrigir: nº de ocorrências de cada smell A/C (e, nos A,
     quantas são corrigíveis);
  2. o TD antes (calculado a partir das contagens esperadas e dos custos
     do catálogo);
  3. depois de corrigir: as contagens outra vez (sobram os A não corrigíveis,
     e a correção pode criar C novos: um C7 ou um C9);
  4. o programa corrigido volta a dar a mesma árvore depois de pretty + parse;
  5. corrigir outra vez não aplica mais nada.

  6. injetar A no programa corrigido: tudo é detetado e corrigir volta atrás.

Os comentários nos programas dizem que smells há em cada linha.
Assume MIN_INSTRUCOES <= 3 (C9) e os limites atuais dos C.

    cd ~/DVMS
    python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeIntegracao
"""
import sys
from collections import Counter

from projeto1.SDVM_lang.ParserFiles.parser.parser import program
from projeto1.SDVM_lang.SmellFiles.smells.prettyPrinter import pretty
from projeto1.SDVM_lang.SmellFiles.smells.detecao import detetar, divida_tecnica
from projeto1.SDVM_lang.SmellFiles.smells.refactoring import corrigir
from projeto1.SDVM_lang.SmellFiles.smells.injecao import injetar_aleatorio
from projeto1.SDVM_lang.SmellFiles.smells.catalogo import seleciona
from projeto1.SDVM_lang.SmellFiles.smells.analise_c import MIN_INSTRUCOES

A = ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]
C = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]
CODIGOS = A + C


# =====================================================================
# Programa 1: expressões (A1-A7 empilhados, não corrigíveis) + C2, C5, C6, C7
# =====================================================================
P1 = """
int LIMITE = 50;                                   // C7 (nunca usado)

int soma(int a, int b, int c, int d) {             // C2 (4 parâmetros); C6 a, b, c, d
    int resultado = (a + 0) * 1;                   // A1 dentro de A2
    resultado = resultado + b - 0;                 // A1
    resultado = resultado + c * 1 + 0 * d;         // A2, A3 (ao corrigir, o 0 que fica dá um A1)
    return resultado + (int)(int)(d + 0);          // A7 dentro de A7, A1 lá dentro
}

bool valida(bool ativo, int total) {
    bool ok = ativo == true;                       // A4
    ok = !!(ok == true);                           // A5 com A4 dentro
    if (total == total && total < total) {         // A6, A6
        ok = ok != false;                          // A4
    }
    if (total >= total || ativo != true) {         // A6, A4
        ok = false == ativo;                       // A4 (o literal à esquerda)
    }
    return ok;
}

int ler(int total) {
    int valor = 0;
    read(valor);
    return valor + total;
}

double mistura(int total, double taxa) {
    int x = ler(total) * 0;                        // A3 NÃO corrigível (chamada); C6 x
    int y = (total / x) * 0;                       // A3 NÃO corrigível (divisão); C6 y
    bool igual = ler(total) == ler(total);         // A6 NÃO corrigível (chamada)
    double z = taxa * 1.0 + 0.0;                   // A2 dentro de A1; C6 z
    double w = -(-taxa) / 1;                       // A5 dentro de A2; C6 w
    if (igual) {
        print(x + y);
    }
    return z + w * 2.5;                            // C5 2.5
}

void main() {
    int contador = 0;
    contador = soma(1, 2, 3, 4);                   // C5 2, 3, 4
    bool estado = valida(contador > 0, contador);
    print(mistura(contador, 0.5));                 // C5 0.5
    print(estado);
}
"""

P1_ANTES = {
    "A1": (4, 4), "A2": (4, 4), "A3": (3, 1), "A4": (5, 5), "A5": (2, 2), "A6": (4, 3), "A7": (2, 2),
    "C2": 1, "C5": 5, "C6": 8, "C7": 1,
}
P1_DEPOIS = {"A3": (2, 0), "A6": (1, 0), "C2": 1, "C5": 5, "C6": 8, "C7": 1}


# =====================================================================
# Programa 2: design (C1, C3, C4, C6, C8, C9) com A dentro;
# a correção dos A cria um C7 e um C9 novos
# =====================================================================
LONGA = "\n".join("    print(TOTAL_GLOBAL);" if k % 2 == 0 else "    print(historico[0]);"
                  for k in range(31))

P2 = """
int TOTAL_GLOBAL = 0;
int historico[10];

void regista(int valor) {                          // C8
    TOTAL_GLOBAL = TOTAL_GLOBAL + valor;
    historico[0] = valor + 0;                      // A1
}

void reinicia() {                                  // C8 (read para um global)
    read(TOTAL_GLOBAL);
}

void processa(int valor, int limite) {             // C3
    int lixo = 5;                                  // depois de corrigir o A3 fica sem usos: C7
    int k = 0;                                     // C6 (não é contador de for)
    print(lixo * 0);                               // A3
    if (valor > 0 && valor < limite && valor != limite && limite > 0 && valor == valor) {   // C4, A6
        while (valor > 0) {
            for (int i = 0; i < limite; i = i + 1) {          // i isento (contador de for)
                if (i == valor) {                              // 4.º nível
                    print(i + 0);                              // A1
                }
            }
            valor = valor - 1;
        }
    }
    while (k < limite) {
        k = k + 1;
    }
    if (valor > limite) {
        print(valor); print(limite); valor = valor - 1;
    }
    if (limite > valor) {
        print(valor); print(limite); valor = valor - 1;        // C9 (cópia do bloco de cima)
    }
    if (valor == limite) {
        print(valor); limite = limite - 1; print(limite);
    }
    if (valor != limite) {
        print(valor); limite = limite - 1 + 0; print(limite);  // A1; depois de corrigir: C9
    }
}

void longa() {                                     // C1 (31 instruções)
""" + LONGA + """
}

void main() {
    regista(1);
    reinicia();
    processa(TOTAL_GLOBAL, 1);
    longa();
}
"""

P2_ANTES = {
    "A1": (3, 3), "A3": (1, 1), "A6": (1, 1),
    "C1": 1, "C3": 1, "C4": 1, "C6": 1, "C8": 2, "C9": 1,
}
P2_DEPOIS = {"C1": 1, "C3": 1, "C4": 1, "C6": 1, "C7": 1, "C8": 2, "C9": 2}


# =====================================================================
# Programa 3: uma função com quase tudo, muitos smells no mesmo sítio
# =====================================================================
P3 = """
int estado = 0;

int tudo(int n, int m, bool flag, double taxa) {   // C2, C3, C8; C6 n, m
    int q = 0;                                     // C6 e C7 na mesma declaração
    int resultado = (int)((n + 0) * 1);            // A7 > A2 > A1
    bool teste = !!((n == n) == true);             // A5 > A4 > A6
    estado = resultado * 7 * 1;                    // A2 com C5 (7) dentro; altera um global
    resultado = -(-(-(-resultado)));               // A5 x3 (três pares sobrepostos)
    flag = !!!flag;                                // A5 x2
    taxa = (double) taxa + 0.0;                    // A1 com A7 dentro
    if (flag == true && teste && n > m && m > 0 && resultado != m) {   // C4 com A4 dentro
        if (teste != false) {                      // A4
            while (m > 0) {
                if (n > m) {                       // 4.º nível
                    m = m - 1;
                }
                m = m - 1;
            }
        }
    }
    return resultado + m * 0;                      // A3 (ao corrigir, o 0 que fica dá um A1)
}

void main() {
    print(tudo(1, 0, true, 0.0));
}
"""

P3_ANTES = {
    "A1": (2, 2), "A2": (2, 2), "A3": (1, 1), "A4": (3, 3), "A5": (6, 6), "A6": (1, 1), "A7": (2, 2),
    "C2": 1, "C3": 1, "C4": 1, "C5": 1, "C6": 3, "C7": 1, "C8": 1,
}
P3_DEPOIS = {"C2": 1, "C3": 1, "C4": 1, "C5": 1, "C6": 3, "C7": 1, "C8": 1}


# =====================================================================
# Programa 4: corrigir os A faz DESAPARECER smells C (o TD dos C desce)
# =====================================================================
COND = "total > 0 && total < base && base > 0 && total != base && base != 0"   # 4 operadores

P4 = """
int calcula(int total, int base) {
    int resultado = total;
    resultado = resultado + 7 * 0;     // C5 (7) e A3; corrigido: resultado + 0 -> A1 -> resultado (o C5 desaparece)
    if ((""" + COND + """) == (""" + COND + """)) {   // base só é usado aqui
        print(resultado);              // o if de cima: C4 (8 operadores) com A6; corrigido: if (true) (o C4 desaparece)
    }
    return resultado * 3;              // C5 (3): fica
}
"""

P4_ANTES = {"A3": (1, 1), "A6": (1, 1), "C4": 1, "C5": 2}
P4_DEPOIS = {"C5": 1, "C7": 1}     # o base só era usado na condição: corrigida, fica sem usos (C7)


PROGRAMAS = [
    ("Programa 1 (expressões)", P1, P1_ANTES, P1_DEPOIS),
    ("Programa 2 (design)", P2, P2_ANTES, P2_DEPOIS),
    ("Programa 3 (tudo no mesmo sítio)", P3, P3_ANTES, P3_DEPOIS),
    ("Programa 4 (a correção faz desaparecer C)", P4, P4_ANTES, P4_DEPOIS),
]


# =====================================================================

CUSTO = {s.codigo: s.custo_min for s in seleciona(CODIGOS)}


def contagens(prog):
    achados = detetar(prog, CODIGOS)
    total = Counter(c for c, _, _ in achados)
    corr = Counter(c for c, _, ok in achados if ok)
    return {c: ((total[c], corr[c]) if c in A else total[c]) for c in CODIGOS}


def normaliza(esperado):
    return {c: esperado.get(c, (0, 0) if c in A else 0) for c in CODIGOS}


def compara(titulo, esperado, obtido):
    print(f"   {titulo}")
    print(f"     {'smell':<6}{'esperado':>12}{'detetado':>12}")
    falhas = 0
    for c in CODIGOS:
        e, o = esperado[c], obtido[c]
        if e == o and e in ((0, 0), 0):
            continue                                  # não mostra os que são 0 e 0
        ok = e == o
        falhas += not ok
        fmt = (lambda v: f"{v[0]} ({v[1]} corr.)") if c in A else str
        print(f"     {c:<6}{fmt(e):>12}{fmt(o):>12}  {'OK' if ok else 'FAIL'}")
    return falhas


def verifica(descricao, ok, detalhe=""):
    print(f"   {'OK  ' if ok else 'FAIL'} {descricao}{'  ' + detalhe if detalhe and not ok else ''}")
    return 0 if ok else 1


def correr(nome, src, antes, depois):
    print(f"===== {nome} =====")
    falhas = 0
    try:
        p = program.parse(src)
    except Exception as e:
        print(f"   ERRO no parse: {type(e).__name__}: {e}\n")
        return 1

    antes, depois = normaliza(antes), normaliza(depois)
    falhas += compara("antes de corrigir", antes, contagens(p))

    td_esp = sum((v[0] if c in A else v) * CUSTO[c] for c, v in antes.items())
    td = divida_tecnica(p, CODIGOS)
    falhas += verifica(f"TD antes = {td_esp} min", td == td_esp, f"(detetado {td})")

    corrigido, aplicados = corrigir(p, CODIGOS)
    print(f"   refactorings aplicados: {dict(sorted(aplicados.items()))}")
    falhas += compara("depois de corrigir", depois, contagens(corrigido))

    td_dep_esp = sum((v[0] if c in A else v) * CUSTO[c] for c, v in depois.items())
    td_dep = divida_tecnica(corrigido, CODIGOS)
    falhas += verifica(f"TD depois = {td_dep_esp} min (desceu {td_esp - td_dep_esp})",
                       td_dep == td_dep_esp, f"(detetado {td_dep})")

    try:
        volta = program.parse(pretty(corrigido))
        ok = volta == corrigido
    except Exception as e:
        ok = False
    falhas += verifica("pretty + parse do programa corrigido dá a mesma árvore", ok)

    _, outra_vez = corrigir(corrigido, CODIGOS)
    falhas += verifica("corrigir outra vez não aplica nada", not outra_vez, f"(aplicou {dict(outra_vez)})")

    # injetar A no programa corrigido (que ainda tem os A não corrigíveis e os C):
    # tudo o que se injeta é detetado, e corrigir volta ao programa corrigido
    base = contagens(corrigido)
    ok_det, ok_volta, injetados = True, True, Counter()
    for seed in range(10):
        p_inj, feitos = injetar_aleatorio(corrigido, seed=seed, limite=2, tipos=A)
        injetados.update(feitos)
        obtido = contagens(p_inj)
        ok_det &= all(obtido[c][0] == base[c][0] + feitos.get(c, 0) for c in A)
        volta = corrigir(p_inj, CODIGOS)[0]
        if volta != corrigido and ok_volta:          # mostra só o 1.º caso que falha
            print(f"   seed {seed}: injetados {feitos}; o programa injetado e o que a correção deu:")
            print("\n".join("     | " + l for l in pretty(p_inj).splitlines()))
            print("\n".join("     > " + l for l in pretty(volta).splitlines()))
        ok_volta &= volta == corrigido
    print(f"   injetados em 10 seeds: {dict(sorted(injetados.items()))}")
    falhas += verifica("injetar A no corrigido: detetados = os que havia + os injetados", ok_det)
    falhas += verifica("injetar A no corrigido: corrigir volta ao programa corrigido", ok_volta)

    if falhas:
        print("\n   programa corrigido:")
        print("\n".join("     " + l for l in pretty(corrigido).splitlines()))
    print(f"--> {'TUDO OK' if falhas == 0 else f'{falhas} FALHA(S)'}\n")
    return falhas


def main():
    if MIN_INSTRUCOES > 3:
        print(f"Aviso: MIN_INSTRUCOES = {MIN_INSTRUCOES}; os blocos do programa 2 têm 3 instruções.\n")
    total = sum(correr(*p) for p in PROGRAMAS)
    print("TUDO OK" if total == 0 else f"{total} FALHA(S) NO TOTAL")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()