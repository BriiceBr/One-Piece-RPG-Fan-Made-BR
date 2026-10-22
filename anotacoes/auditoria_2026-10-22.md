# Auditoria do ImpelDown Archives — Fases 1 e 2 (inventário e diagnóstico)

Data: 22/10/2026 · Responsável: DeepSeek (análise) + Usuário (decisões)

## 1. Inventário

### Estrutura
- `main.py` — ponto de entrada (CustomTkinter + `GerenciadorAmeasApp`).
- `config.py` — temas, fontes e o `ctk.set_appearance_mode("dark")` (efeito colateral no import).
- `core/` — regras e motores puros (sem Tkinter): `regras.py`, `dados.py`, `combate.py`, `desafio.py`, `condicoes.py`, `paleta.py`.
- `ui/` — interface: `app_main.py` (janela/árvore/tracker), `ficha_frame.py` (ficha), `widgets_custom.py`, `popups.py`.
- `utils/` — `arquivos.py` (persistência), `loot.py`, `golpes.py`, `historia.py`, `cartaz.py`, `encontros.py`, `importacao.py`.
- `tests/` — `test_core.py`, `test_utils.py` (29 testes, rodam via `unittest`).

### Camadas e responsabilidades
- **Regras:** centralizadas em `core/regras.py` (`calcular_atributos_derivados`) e `core/dados.py` (`rolar_teste_pericia`, `rolar_dados_seguro`). A UI chama essas funções; não reimplementa fórmulas.
- **Persistência:** `utils/arquivos.py` com SQLite (tabela única `dados_rpg`: estrutura + fichas + config em JSON).

### Bibliotecas
- Python 3.14.3, CustomTkinter 6.0.0, Pillow 12.2.0.

### SQLite — como é usado
- Gravação: `with closing(sqlite3.connect(tmp))` + `with conn:` (transação), depois `os.replace` (atômico) + backup `.db.bak`.
- Leitura: `mode=ro` (somente leitura), com migração leve (`ALTER TABLE ADD COLUMN config`).
- Consultas **parametrizadas** (`?`). Nenhum acesso concorrente: tudo roda na thread da UI, então não há risco de "database is locked".

## 2. Diagnóstico

| # | Gravidade | Problema | Arquivo / função | Consequência | Correção recomendada |
|---|---|---|---|---|---|
| C1 | **Alta** | Fórmula de PV **não confirmada** no livro: `(12+Fís)+(Nível−1)·(6+Maior)`. Não é a regra confirmada nem a proposta em AGENTS §7. | `core/regras.py:15` | PV calculado pode divergir do livro quando a regra for definida. | Confirmar a fórmula com o Mestre; até lá, manter centralizada e anotar como pendência. |
| C2 | **Alta** | CD usa `10+Maior+Nível//2`, sem fonte nas regras confirmadas. | `core/regras.py:21` | CD "inventado" pode desbalancear testes. | Confirmar a CD correta (ou remover o cálculo e usar CD manual). |
| A1 | **Alta** | Tracker **duplica** participantes: `add_tracker`, `rolar_iniciativa_pasta` e `lancar_bando_tracker` adicionam sem verificar se o id já está na lista. | `ui/app_main.py` (1539, 1558), `ui/ficha_frame.py` (1062) | Mesma ficha aparece 2+ vezes, infla desafio e turno. | Bloquear/avisar quando o id (ou nome) já está no `tracker_data`. |
| A2 | **Alta** | Gerador de encontros ainda usa a **regra de três antiga** (razão 60/100/140%) com rótulos Fácil/Médio/Difícil/Mortal. | `utils/encontros.py` | Divergente do Tracker (que já usa dano/rodada: Muito Fácil/Desafiador/Mortal). | Converter o gerador para a fórmula de dano/rodada (etapa 10.4). |
| A3 | **Alta** | Fallback da dificuldade chama `calcular_dificuldade_encontro` (regra antiga) quando não há HP. | `ui/app_main.py` `_dificuldade_atual` | Viola "não usar a regra de três antiga". | Sem HP → exibir "Sem HP vinculado" e sugerir vincular fichas; remover o fallback antigo. |
| M1 | Média | Graus de Perícia aceitam **−1..4**, mas o confirmado é **0..3**. | `core/regras.py:9-10` | Desvio consciente pedido anteriormente. | Confirmar se mantém −1..4 (decisão da mesa) ou volta para 0..3. |
| M2 | Média | Iniciativa = `1d20 + Agilidade` (não está nas regras confirmadas). | `ui/app_main.py:1574` | Conveniência de mesa; sem base no livro. | Documentar como ferramenta opcional (não é regra). |
| M3 | Média | **Sem testes automatizados** para a rolagem (`rolar_teste_pericia`) e para Vantagem/Desvantagem. | `tests/` | Etapa 8 pede testes das rolagens; hoje só regras/combate/persistência. | Criar `tests/test_dados.py` com RNG injetado. |
| M4 | Média | `rolar_dados_seguro` (dano) usa `random` sem injeção de RNG. | `core/dados.py:66` | Difícil testar de forma determinística. | Adicionar parâmetro `rng` opcional. |
| B1 | Baixa | `config.py` executa `ctk.set_appearance_mode("dark")` no import. | `config.py:4` | Efeito colateral ao importar. | Mover para a inicialização em `main.py`. |
| B2 | Baixa | Leitura detecta schema antigo por exceção genérica `OperationalError`. | `utils/arquivos.py:133` | Frágil (pode esconder erro real). | Consultar `PRAGMA table_info` antes de decidir as colunas. |
| B3 | Baixa | Backup é sempre o mesmo `.db.bak` (sem histórico). | `utils/arquivos.py:73` | Só guarda a última versão anterior. | Opcional: `.db.bak.1`, `.bak.2` (rotativo). |
| B4 | Baixa | `random` sem seed na iniciativa/dano. | vários | Sem impacto real em mesa. | Sem ação necessária. |

## 3. O que já está correto (não mexer)

- Rolagem nova (**Poça de d20**) correta: grau 0–3 → 1–4 d20, maior resultado, Vantagem +1 dado, Desvantagem −1, e 2d20-menor quando a poça zera. A UI usa `rolar_teste_pericia`.
- PV atual/máximo e PE atual/máximo **separados**; recalcular máximo não repõe PV (só clampa para baixo).
- Defesas (Passiva, Bloqueio, Esquiva) e PE Máximo (`4+Nível+Maior`) corretos.
- Persistência com `with`/transação/atômico/backup/parametrizado/migração — sem lock.
- Imagens mantêm referência (`self.foto`, `lbl_img.image`), sem sumir por garbage collector.
- Desafio do Tracker já usa a **nova fórmula** (dano/rodada) quando há HP.

## 4. Plano das próximas fases (aguardando confirmação)

1. **Fase 3** — corrigir rolagem/regras: confirmar PV e CD; manter centralizado em `core`.
2. **Fase 4** — Tracker: impedir duplicados; remover regra de três antiga do fallback.
3. **Fase 5** — converter o gerador de encontros para a fórmula de dano/rodada.
4. **Fase 6** — persistência: `PRAGMA table_info` explícito; mover efeitos do `config.py`.
5. **Fase 7** — testes: `tests/test_dados.py` (rolagens) + injeção de RNG no dano.
6. **Relatório final.**

### Decisões que preciso antes de implementar (máx. 3)
1. Qual é a **fórmula de PV** confirmada? (a atual, a proposta `Raça + Nível×Fís + 5×(Nível−1)`, ou outra).
2. Mantém **Graus −1..4** (pedido anterior) ou volta para o oficial **0..3**?
3. Mantém o **CD = 10+Maior+Nível//2** ou passa a usar CD definida manualmente pelo Mestre?

---

## 5. Implementado na rodada 1 (22/10)

Corrigidos sem tocar em regras: dedupe no Tracker, remoção da regra de três antiga no fallback, injeção de RNG em `rolar_dados_seguro`, `tests/test_dados.py` (41 testes no total), `PRAGMA table_info` na leitura SQLite e `set_appearance_mode` movido para `main.py`. Aguardando decisões do Mestre para PV, CD e faixa de Graus.

---

## 6. Implementado na rodada 2 (22/10)

Backup rotativo (3 versões), `busy_timeout` anti-lock, documentação da iniciativa e evidência de que a UI não embute fórmulas de regra. Total de testes: 42.

---

## 7. Fase 3 e 10.4 implementadas (22/10)

Decisões aplicadas: PV proposto, CD manual, Graus 0..3, gerador por HP/rodadas. C1/C2/M1/A2 encerrados; `core.combate` virou legado.
