# Guia: como acrescentar smells ao projeto

19/11/2026

## Visão geral

Para acrescentar smells só mexes em dois ficheiros: o ficheiro do teu grupo (ex.: `smells_controlo.py`) e duas linhas do `catalogo.py`. A deteção, o relatório, o TD, o refactoring e a injeção funcionam para qualquer smell do catálogo, sem alterações.

| ficheiro (em `SmellFiles/smells/`) | o que faz | mexes? |
| --- | --- | --- |
| `smell.py` | a classe `Smell`: código, nome, as três funções e o custo | não |
| `analise.py` | perguntas sobre expressões: `puro`, `tipos_de`, `eh_booleana`, ... e o `Contexto` | só para acrescentar uma pergunta que vários smells usem |
| `smells_expressao.py` | grupo A (A1–A7): o modelo a seguir | não |
| `smells_controlo.py`, `smells_design.py` | grupos B e C | **sim: é aqui que trabalhas** |
| `catalogo.py` | junta as listas `SMELLS` de todos os grupos | **sim: 2 linhas** |
| `detecao.py` | deteção (`adhocTU` + `seqTU` + `full_tdTU`), relatório e TD | não |
| `refactoring.py` | refactoring (`adhocTP` + `innermost`) | não |
| `injecao.py` | injeção (`full_buTP` + `adhocTPZ`) e a regra de nunca pôr dois smells no mesmo sítio | não |
| `prettyPrinter.py` | AST → código, para ver resultados e contar LOC | não |

Os testes estão em `SmellFiles/tests/`: `testeExpressoes.py` (exemplos do grupo A) e `testeProgramas.py` (propriedades sobre os programas de `examples/` e `ParserFiles/tests/valid/`).

## Preparar o ambiente

Tudo corre a partir da pasta `DVMS`, com `python3 -m` e o caminho do módulo com pontos. Nunca corras um ficheiro diretamente (`python3 ficheiro.py`): os imports deixam de funcionar.

Estrutura esperada:

```
DVMS/
  StrategicProg/pyztrategic/         zipper.py, strategy.py
  projeto1/SDVM_lang/
    examples/
    ParserFiles/parser/              parser.py, expressionParser.py, ...
    ParserFiles/tests/               check_parser.py, valid/, invalid/
    SmellFiles/smells/               smell.py, analise.py, catalogo.py, ...
    SmellFiles/tests/                testeExpressoes.py, testeProgramas.py
```

Preparar o terminal e correr os testes:

```bash
cd ~/DVMS
source venvDVMS/bin/activate        # o venv precisa do parsy: pip install parsy

python3 -m projeto1.SDVM_lang.ParserFiles.tests.check_parser projeto1/SDVM_lang/examples
python3 -m projeto1.SDVM_lang.ParserFiles.parser.check_ast
python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeExpressoes
python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeProgramas
```

Imports:

- **Dentro de `SmellFiles/smells/`**, os ficheiros importam-se uns aos outros com ponto: `from .analise import puro`.
- **O parser** importa-se com o caminho completo: `from projeto1.SDVM_lang.ParserFiles.parser.control_flow import IfStatement`.
- **As estratégias**: `from StrategicProg.pyztrategic import strategy as st`.
- **Nomes de pastas** não podem ter hífen nem espaços, e maiúsculas contam.

## Anatomia de um smell

Um smell é um `Smell(código, nome, deteta, corrige, injeta, custo_min)`. As três funções olham para **um único nó**, sem recursão: quem percorre a árvore são as estratégias dos motores.

```python
@dataclass
class Smell:
    codigo: str                 # "B2"
    nome: str                   # "ramos iguais"
    deteta: Callable            # deteta(n, ctx) -> bool
    corrige: Callable | None    # corrige(n, ctx) -> nó novo  (ou raise)
    injeta: Callable | None     # injeta(n, z, ctx) -> nó novo  (ou raise)
    custo_min: int              # minutos de TD por ocorrência
```

| função | recebe | devolve | quando não se aplica |
| --- | --- | --- | --- |
| `deteta(n, ctx)` | um nó e o contexto | `True` se o nó tem o smell | `False` |
| `corrige(n, ctx)` | um nó e o contexto | o nó já corrigido | `raise st.StrategicError` (use `falha()`) |
| `injeta(n, z, ctx)` | um nó, o zipper desse nó e o contexto | o nó com o smell | `raise st.StrategicError` (use `falha()`) |

Regras:

- **`corrige` só descreve os casos em que é seguro corrigir.** Tudo o resto cai no `case _: falha()`. Uma ocorrência detetada cujo `corrige` falha aparece no relatório como "não corrigível".
- **Nunca alteres o nó recebido.** Constrói um nó novo (`IfStatement(c, s, None)`), porque o original ainda é usado pela estratégia.
- **`z` (o zipper) só serve para saber onde o nó está:** o pai (`pai(z)`) ou a função onde está (`z.ancestor(...)`). Não é preciso mexer nele.
- **Smells só de reporte** (grupo C): `corrige=None` e `injeta=None`.
- **O contexto** (`ctx`) traz os tipos declarados no programa (`ctx.tipos`) e o gerador de números aleatórios da injeção (`ctx.rng`). Não o cries: os motores passam-to.

## Passo a passo: acrescentar um grupo de smells

O exemplo abaixo foi testado com os motores reais: deteção, relatório, refactoring e injeção funcionam sem mudar mais nada.

1. Cria `SmellFiles/smells/smells_controlo.py` com os imports, as funções de cada smell e uma lista `SMELLS`:

```python
from projeto1.SDVM_lang.ParserFiles.parser.expressionParser import IntLit
from projeto1.SDVM_lang.ParserFiles.parser.statements import Return, Break, Continue, Print
from projeto1.SDVM_lang.ParserFiles.parser.control_flow import Block, IfStatement

from .smell import Smell
from .analise import falha


# ---------------- B4: else vazio -------------------------------------
# if (c) S else { }  ->  if (c) S

def deteta_else_vazio(n, ctx):
    match n:
        case IfStatement(_, _, Block([])):
            return True
        case _:
            return False


def corrige_else_vazio(n, ctx):
    match n:
        case IfStatement(c, s, Block([])):
            return IfStatement(c, s, None)
        case _:
            falha()


def injeta_else_vazio(n, z, ctx):
    # só com o then entre chavetas: em if (a) while (b) if (c) S, um else
    # acrescentado ficava ligado ao if de dentro (dangling else)
    match n:
        case IfStatement(c, Block() as s, None):
            return IfStatement(c, s, Block([]))
        case _:
            falha()


# ---------------- B8: código morto -----------------------------------
# instruções num bloco depois de return / break / continue  ->  removidas

SALTOS = (Return, Break, Continue)


def deteta_codigo_morto(n, ctx):
    match n:
        case Block(ss) if any(isinstance(s, SALTOS) for s in ss[:-1]):
            return True
        case _:
            return False


def corrige_codigo_morto(n, ctx):
    match n:
        case Block(ss) if any(isinstance(s, SALTOS) for s in ss[:-1]):
            k = next(i for i, s in enumerate(ss) if isinstance(s, SALTOS))
            return Block(ss[:k + 1])
        case _:
            falha()


def injeta_codigo_morto(n, z, ctx):
    # só em blocos que já acabam num salto: acrescenta uma instrução depois
    match n:
        case Block([*_, Return() | Break() | Continue()] as ss):
            return Block(ss + [Print(IntLit(0))])
        case _:
            falha()


SMELLS = [
    Smell("B4", "else vazio",   deteta_else_vazio,   corrige_else_vazio,   injeta_else_vazio,   1),
    Smell("B8", "código morto", deteta_codigo_morto, corrige_codigo_morto, injeta_codigo_morto, 3),
]
```

2. No `catalogo.py`, tira o `#` às duas linhas do teu grupo:

```python
from . import smells_expressao
from . import smells_controlo

CATALOGO = (
    smells_expressao.SMELLS
    + smells_controlo.SMELLS
)
```

3. Corre os dois testes de smells (secção "Como testar"). O relatório passa logo a mostrar as linhas B4 e B8.

Cada smell vai pela ordem: primeiro `deteta`, depois `corrige` com as mesmas formas mais as condições de segurança, e por fim `injeta`, que faz o caminho inverso do `corrige`.

## Regras para cada função

### deteta

- **Escreve o padrão com `match`, como nas aulas.** Os literais têm classes próprias, por isso `IntLit(0)` dentro do padrão funciona e não apanha `BoolLit(False)`.
- **Deteta o padrão sem condições de segurança.** Um `f() * 0` é smell mesmo que não se possa corrigir; o relatório separa ocorrências de corrigíveis.
- **Cada ocorrência deve ser detetada num só nó.** Se o mesmo smell aparecer em dois nós encaixados (por exemplo o `Block` e a lista de instruções dele), conta a dobrar.

### corrige

- **Só os casos seguros, tudo o resto em `case _: falha()`.** É uma lista de casos permitidos: um caso esquecido fica por corrigir, em vez de ser corrigido mal.
- **Seguro quer dizer: o programa faz exatamente o mesmo.** Usa as perguntas do `analise.py`: `puro(e)` antes de apagar ou duplicar uma expressão, `tipos_de(e, ctx)` quando o tipo muda o resultado.
- **O resultado tem de deixar de ter o smell, ou ter um smell que se resolva a seguir.** O `innermost` repete até nenhum `corrige` se aplicar: um `corrige` que produza de novo o mesmo padrão nunca termina.
- **Nunca transformes A em B e B em A** entre dois smells diferentes: o `innermost` fica em ciclo infinito.

### injeta

- **É o inverso do `corrige`:** tem de valer `corrige(injeta(n)) == n`. O teste verifica que o refactoring desfaz exatamente a injeção.
- **Só em sítios onde o smell injetado é corrigível**, para essa propriedade valer. Por exemplo, o A4 só injeta em expressões bool.
- **Não cries outro smell ao mesmo tempo.** Por exemplo, o A2 não injeta `1 * 0`, que seria também um A3. O teste compara o número injetado com o detetado.
- **O resultado tem de ser código válido depois do pretty printer.** Cuidado com o *dangling else* (ver o B4) e com inicializações de globais, que têm de ser constantes.
- **Não precisas de verificar sobreposições.** A regra "nunca dois smells no mesmo sítio" já está no `injecao.py` e aplica-se a todos os smells.
- **Para escolher entre variantes, usa `ctx.rng`** (por exemplo `ctx.rng.choice([...])`), nunca o módulo `random` diretamente: assim a mesma seed dá sempre o mesmo resultado.

## Smells só de reporte (grupo C)

Um smell sem refactoring automático só precisa do `deteta`; `corrige` e `injeta` ficam `None`. Entra no relatório e no TD, aparece como "não corrigível", e o refactoring e a injeção ignoram-no. Exemplo testado, em `smells_design.py`:

```python
from projeto1.SDVM_lang.ParserFiles.parser.declarations import FunctionDefinition

from .smell import Smell

MAX_PARAMETROS = 3


# ---------------- C2: lista longa de parâmetros ----------------------

def deteta_muitos_parametros(n, ctx):
    match n:
        case FunctionDefinition(_, _, params, _) if len(params) > MAX_PARAMETROS:
            return True
        case _:
            return False


SMELLS = [
    Smell("C2", "lista longa de parâmetros", deteta_muitos_parametros, None, None, 10),
]
```

- **Limiares como constantes no topo do ficheiro** (`MAX_PARAMETROS`, `MAX_INSTRUCOES`, `MAX_PROFUNDIDADE`), para se poderem ajustar e citar no relatório.
- **Um smell que precisa de medir uma subárvore** (instruções de uma função, profundidade de `if`s) pode usar uma estratégia TU dentro do `deteta`, sobre esse nó: `st.full_tdTU(worker, toZipper(n.body))`. É o mesmo padrão do `puro` no `analise.py`.
- **Smells que comparam partes do programa** (Duplicated Code, variável não usada) precisam de ver mais do que um nó. Fazem-se em duas fases: primeiro recolhe-se a informação com TU (por exemplo, os nomes usados); depois o `deteta` consulta-a. Combinem antes quem acrescenta essa informação ao `Contexto`, porque é o sítio certo para ela.

## Ferramentas do analise.py

As condições de segurança usam estas perguntas. Importa-as com `from .analise import ...`.

| função | responde a | exemplo de uso |
| --- | --- | --- |
| `falha()` | lança `StrategicError` ("este nó não é comigo") | `case _: falha()` |
| `puro(e)` | `e` não tem chamadas de função nem divisões que possam ser por zero? | B2: `if (c) S else S` → `S` só se `c` for puro |
| `tipos_de(e, ctx)` | que tipos pode ter `e`? (`{"int"}`, `{"bool"}`, ...; vazio = desconhecido) | A7: `(t)e` é redundante se `tipos_de(e) == {t}` |
| `eh_booleana(e, ctx)` | `e` é de certeza bool? | A4: `x == true` → `x` |
| `eh_numerica(e, ctx)` | `e` é de certeza int ou double? | injeção do A1 |
| `eh_double(e, ctx)` | `e` é de certeza double? | A1: `x + 0.0` → `x` |
| `promovida(e, ctx)` | uma conta sobre `e` muda-lhe o tipo (char/bool → int)? | A1: `c + 0` não se corrige |
| `pai(z)` | o nó pai, a partir do zipper | injeção do A5 |
| `parametro_seguro(z, ctx)` | um parâmetro int/char/bool da função onde o nó está | injeção do A3 e A6 |
| `LITERAIS`, `RELACIONAIS`, `ARITMETICOS` | tuplos de classes, para `isinstance` | `isinstance(n, LITERAIS)` |

O `Contexto` tem dois campos: `ctx.tipos` (nome → conjunto de tipos declarados; um array `int a[3]` aparece como `"int[]"`) e `ctx.rng` (números aleatórios da injeção). A inferência ignora o âmbito: um nome declarado com tipos diferentes em funções diferentes fica com os dois, e as condições que dependem dele falham (opção conservadora).

Se criares uma pergunta nova de que mais de um grupo vai precisar, põe-na no `analise.py`; se só servir o teu grupo, deixa-a no teu ficheiro.

## Como testar

Depois de ligares o teu grupo ao catálogo, os testes que já existem passam a cobri-lo automaticamente:

```bash
cd ~/DVMS
python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeProgramas
python3 -m projeto1.SDVM_lang.SmellFiles.tests.testeExpressoes
```

O `testeProgramas` corre sobre os programas de `examples/` e `ParserFiles/tests/valid/` e verifica, para cada um:

1. o pretty printer é fiel: `parse(pretty(P)) == P`;
2. depois do refactoring não fica nenhum smell corrigível;
3. corrigir duas vezes dá o mesmo que corrigir uma;
4. em 10 injeções aleatórias, a deteção encontra exatamente os smells injetados, o programa injetado é válido e `corrigir(injetado) == corrigir(P)`.

Se um destes falhar, o `FAIL` diz qual. As causas mais comuns:

| sintoma | causa provável |
| --- | --- |
| "injetados 1, detetados 2 a mais" | a injeção criou também outro smell, ou o mesmo smell conta em dois nós |
| "corrigir(injetado) != corrigir(P)" | `corrige` não desfaz exatamente o `injeta`, ou injetou num sítio onde não é corrigível |
| "ficaram smells corrigíveis" | o `corrige` produz um nó que ainda tem o padrão |
| "programa injetado não volta a ser lido" | a injeção gerou algo que o pretty printer escreve de outra forma (ex.: dangling else) |
| o teste nunca termina | ciclo no refactoring: dois `corrige` que se desfazem um ao outro |

Acrescenta também um teste teu com casos dirigidos ao teu grupo, seguindo o `testeExpressoes.py`: um programa com cada smell, os casos que não devem ser corrigidos, o relatório antes e depois, e as injeções. Para os programas reais ficarem cobertos, junta a `ParserFiles/tests/valid/` um ou dois programas com os teus smells.

## Armadilhas comuns

**Or-pattern com condição sobre o literal.** `case Add(x, z) | Add(z, x) if z == IntLit(0)` nunca apanha `0 + x`: o Python fica com a primeira alternativa que encaixa e só depois testa o `if`. Põe o literal dentro do padrão: `case Add(x, IntLit(0)) | Add(IntLit(0), x)`.

**Erros escondidos.** O `adhocTU`, o `adhocTP` e o `adhocTPZ` apanham `AttributeError` e `TypeError` e tratam-nos como "este nó não tem o smell". Um erro no teu código (um campo mal escrito, por exemplo) não dá nenhuma mensagem: o smell simplesmente nunca é detetado. Se algo não aparece, chama a tua função diretamente num nó, fora das estratégias: `deteta_else_vazio(no, None)`.

**Nomes da AST.** Usa os nomes exatos do parser: `IfStatement(condition, then_branch, else_branch)`, `WhileStatement(condition, body)`, `ForStatement(initializer, condition, update, body)`, `Block(statements)`, `Assignment(target, value)`, `Index(target, index)`, `FuncCall(name, args)`. Em `Assignment`, `ArrayAssignment`, `Read`, `Index` e `FuncCall`, o nome é uma `str`, não um `Ident`. Os literais são `IntLit`, `FloatLit`, `BoolLit`, `CharLit` e `StringLit`.

**`None` vs bloco vazio.** Um `if` sem `else` tem `else_branch=None`; um `else { }` tem `Block([])`. No `for`, cada uma das três partes pode ser `None`, e o `initializer` pode ser uma declaração ou uma atribuição.

**As listas também são visitadas.** O zipper visita as listas da AST (as instruções de um bloco, os argumentos de uma chamada, os parâmetros) como nós. Um `case [ ... ]` apanha todas essas listas, não só as de instruções. Prefere fazer o padrão sobre o nó que contém a lista, como `Block(ss)`.

**Igualdade estrutural.** `a == b` entre nós compara a árvore inteira e é estrita (`IntLit(1) != BoolLit(True)`). Serve diretamente para smells como "ramos iguais" ou código duplicado.

**Dangling else.** `if (a) if (b) S else T` liga o `else` ao `if` de dentro. Uma injeção que acrescente um `else` a um `if` cujo ramo não está entre chavetas muda o significado. Exige `Block()` no ramo, como no B4.

**A regra de não sobrepor é por nó.** Um smell detetado num `Block` (como o B8) ocupa o bloco inteiro: depois de injetado, nada dentro desse bloco recebe outra injeção, e não se injeta num bloco que já tenha algum smell. É o comportamento esperado, mas reduz o número de sítios disponíveis. Os smells só de reporte não contam para esta regra.

**Globais.** Em C, uma variável global tem de ser inicializada com uma constante. Uma injeção fora de funções não pode usar variáveis nem chamadas.

## Checklist antes de entregar

- [ ] Cada smell tem `deteta`, e `corrige`/`injeta` ou `None`
- [ ] O `corrige` só tem casos seguros e acaba em `case _: falha()`
- [ ] O `injeta` é o inverso do `corrige` e não cria outros smells
- [ ] As escolhas aleatórias usam `ctx.rng`
- [ ] O grupo está ligado no `catalogo.py`
- [ ] Os limiares (grupo C) são constantes no topo do ficheiro
- [ ] `testeProgramas` e `testeExpressoes` dão `TUDO OK` / `OK`
- [ ] Há um teste do grupo com casos corrigíveis e não corrigíveis
- [ ] Há em `ParserFiles/tests/valid/` pelo menos um programa com os smells do grupo
- [ ] O `catalogo_smells.txt` está atualizado com o estado e os custos do grupo
