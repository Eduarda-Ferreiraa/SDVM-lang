"""Programas de demonstração para a apresentação.

Cada programa tem, linha a linha, um comentário com os smells que lá estão,
e as contagens esperadas antes e depois de corrigir (corrigir com todos os
smells do catálogo). O testeDemo.py confirma estas contagens.

  notas     smells de expressão (A1-A7, incluindo não corrigíveis) + C5, C6, C7
  stock     smells de controlo (B1-B8) + C2, C4, C8; corrigir o B2 faz
            desaparecer um C5
  relatorio smells de design (C1, C3, C9); corrigir os A cria um C7 e um C9
            e faz desaparecer um C5

Contagens: {código: n} para os C e os B, {código: (n, corrigíveis)} para os A.
Os códigos que não aparecem são 0.
"""

# =====================================================================
# notas: média e aprovação de alunos
# =====================================================================
NOTAS = """
int NOTA_MINIMA = 10;

int arredonda(double valor) {
    return (int) valor;                              // conversão a sério: não é A7
}

double media(int soma, int quantos) {
    if (quantos == 0) {
        return 0.0;
    }
    return (double) soma / quantos * 1;              // A2
}

bool aprovado(int nota) {
    bool passou = nota >= NOTA_MINIMA;
    return passou == true;                           // A4
}

void main() {
    int soma = 0;
    int n = 0;                                       // C6
    int nota = 0;
    int bonus = 0;                                   // C7 (nunca usado)
    bool ok = false;
    read(n);
    for (int i = 0; i < n; i = i + 1) {              // i: contador do for, não é C6
        read(nota);
        soma = soma + nota + 0;                      // A1
        ok = !!aprovado(nota);                       // A5
        if (ok == false) {                           // A4 -> !ok
            print(nota * 0 + 20);                    // A3 (corrigido dá 0 + 20: um A1) e C5 (20)
        }
    }
    print(media(soma, n) * 1.0);                     // A2
    print(arredonda(media(soma, n)) * 0);            // A3 NÃO corrigível (perdia a chamada)
    print((int) soma);                               // A7
    print(media(soma, n) == media(soma, n));         // A6 NÃO corrigível (chama media duas vezes)
}
"""

NOTAS_ANTES = {
    "A1": (1, 1), "A2": (2, 2), "A3": (2, 1), "A4": (2, 2), "A5": (1, 1), "A6": (1, 0), "A7": (1, 1),
    "C5": 1, "C6": 1, "C7": 1,
}
NOTAS_DEPOIS = {"A3": (1, 0), "A6": (1, 0), "C5": 1, "C6": 1, "C7": 1}


# =====================================================================
# stock: gestão de stock com variáveis globais
# =====================================================================
STOCK = """
int stock[5] = {0, 0, 0, 0, 0};
int vendas = 0;

void regista_venda(int produto, int quantidade, int preco, bool urgente) {       // C2, C8
    if (quantidade > 0 && produto >= 0 && produto < 5 && preco > 0 && stock[produto] >= quantidade) {
        stock[produto] = stock[produto] - quantidade;                             // (if de cima: C4 e C5 5)
        vendas = vendas + quantidade * preco;
    } else {
    }                                                                             // B4
    if (urgente) {                                                                // B6
        if (vendas > 0) {
            print(vendas);
        }
    }
}

bool tem_stock(int produto) {
    if (stock[produto] > 0) {                                                     // B5
        return true;
    } else {
        return false;
    }
}

void repoe(int produto, int quantidade) {                                         // C8
    if (true) {                                                                   // B1
        stock[produto] = stock[produto] + quantidade;
    }
    if (quantidade > 0) {                                                         // B3
    } else {
        print(quantidade);
    }
    if (produto > 2) {                                                            // B2 e C5 (2)
        print(produto);
    } else {
        print(produto);
    }
}

int total_vendas() {
    {                                                                             // B7
        print(vendas);
    }
    return vendas;
    print(0);                                                                     // B8
}

void main() {
    repoe(1, 10);                                                                 // C5 (10)
    regista_venda(1, 3, 2, true);                                                 // C5 (3, 2)
    print(tem_stock(1));
    print(total_vendas());
}
"""

STOCK_ANTES = {
    "B1": 1, "B2": 1, "B3": 1, "B4": 1, "B5": 1, "B6": 1, "B7": 1, "B8": 1,
    "C2": 1, "C4": 1, "C5": 5, "C8": 2,
}
STOCK_DEPOIS = {"C2": 1, "C4": 1, "C5": 4, "C8": 2}      # o B2 corrigido leva o "produto > 2"


# =====================================================================
# relatorio: função longa, aninhamento profundo e blocos repetidos
# =====================================================================
RELATORIO = """
int LIMITE = 100;

void relatorio(int dias, int vendas, int devolucoes) {          // C1 (32 instruções), C3 (4 níveis)
    int lixo = 3;                                                // depois de corrigir: C7 (sem usos)
    int total = 0;
    int media = 0;
    print(lixo * 0);                                             // A3
    total = vendas - devolucoes;
    media = total / dias;
    print(total);
    print(media);
    if (dias > 0) {
        while (total > 0) {
            if (total > LIMITE) {
                print(total);
                if (media > 0) {                                 // 4.º nível
                    print(media);
                }
            }
            total = total - 1;
        }
    }
    if (vendas > devolucoes) {
        print(vendas); print(devolucoes); total = vendas - devolucoes;
    }
    if (vendas < devolucoes) {
        print(vendas); print(devolucoes); total = vendas - devolucoes;     // C9
    }
    if (vendas == devolucoes) {
        print(total); total = total + 1; print(media);
    }
    if (vendas != devolucoes) {
        print(total); total = total + 1 + 0; print(media);      // A1; depois de corrigir: C9
    }
    print(7 * 0);                                                // A3 e C5 (7); corrigido: print(0)
}

void main() {
    int dias = 0;
    int vendas = 0;
    int devolucoes = 0;
    read(dias);
    read(vendas);
    read(devolucoes);
    relatorio(dias, vendas, devolucoes);
}
"""

RELATORIO_ANTES = {"A1": (1, 1), "A3": (2, 2), "C1": 1, "C3": 1, "C5": 1, "C9": 1}
RELATORIO_DEPOIS = {"C1": 1, "C3": 1, "C7": 1, "C9": 2}


DEMOS = [
    ("notas", NOTAS, NOTAS_ANTES, NOTAS_DEPOIS),
    ("stock", STOCK, STOCK_ANTES, STOCK_DEPOIS),
    ("relatorio", RELATORIO, RELATORIO_ANTES, RELATORIO_DEPOIS),
]
