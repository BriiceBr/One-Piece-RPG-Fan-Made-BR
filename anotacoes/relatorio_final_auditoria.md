# Relatório Final — Auditoria do ImpelDown Archives

Data: 22/10/2026 · Responsável: DeepSeek + Usuário

## Escopo
Auditar e corrigir o aplicativo preservando dados e funcionalidades, sem inventar regras de RPG. Fonte de regras: livro mais recente (p.1–67 = sistema novo) e decisões em `anotacoes/pendencias.md`/`AGENTS.md`.

## Fases concluídas

| Fase | Estado |
|---|---|
| 1 — Inventário | ✅ concluído |
| 2 — Diagnóstico | ✅ concluído (`anotacoes/auditoria_2026-10-22.md`) |
| 4 — Arquitetura regras/UI/persistência | ✅ já em camadas; varredura confirmou que a UI não embute fórmulas |
| 5 — SQLite (migrações + anti-lock) | ✅ corrigido |
| 6 — Testes automatizados | ✅ ampliado |
| 2/3 — Regras (PV/CD/graus) | ⛔ bloqueado (decisões pendentes) |
| 7 — Relatório final | ✅ este documento |

## Correções implementadas

1. **Rolagem (Poça de d20)** já estava correta; adicionada injeção de `rng` em `rolar_dados_seguro` para testes.
2. **Tracker:** `_ja_esta_no_tracker` impede participantes duplicados (ficha, iniciativa em massa e bando).
3. **Desafio:** removida a regra de três antiga do fallback — sem HP, o Tracker mostra `Sem HP vinculado aos inimigos`.
4. **Persistência:** leitura via `PRAGMA table_info` (sem exceção genérica); `PRAGMA busy_timeout` defensivo; backup rotativo `.db.bak` + `.bak.1` + `.bak.2`; gravação atômica e parametrizada já existiam.
5. **Config:** `set_appearance_mode`/`set_default_color_theme` movidos de `config.py` para `main.py`.
6. **Testes:** novo `tests/test_dados.py` (graus, Poça de d20, Vantagem/Desvantagem, menor-quando-zera, dano determinístico) e `test_backup_rotativo`. Total: **42 testes OK**.
7. **Documentação:** iniciativa marcada como conveniência de mesa (não é regra do livro).

## Verificação final
```
COMPILA OK
42 testes OK
main.py importa sem erro
config.py sem efeito colateral de import
```

## Bloqueios (aguardam decisão do Mestre — alterar sem isso seria inventar regra)

1. **Fórmula de PV** — qual é a confirmada? (atual `(12+Fís)+(Nível−1)·(6+Maior)`; proposta `Raça + Nível×Fís + 5×(Nível−1)`; ou outra).
2. **Fórmula de CD** — automática (`10+Maior+Nível//2`) ou manual?
3. **Graus de Perícia** — manter **−1..4** (pedido anterior) ou voltar ao oficial **0..3**?
4. **HP por Nível** — existe tabela oficial para converter o Gerador de Encontros (A2) da regra de três para a fórmula de dano/rodada?

## Próximo passo
Assim que essas 4 decisões forem respondidas: corrigir `core/regras.py` (PV/CD/graus), converter `utils/encontros.py` para a nova fórmula, atualizar os testes e fechar a meta.

---

## Fase 3 e 10.4 — concluídas (22/10)

PV pela fórmula confirmada (PV de Raça + Nível×Físico + 5×(Nível−1)), CD manual, Graus 0..3 e Gerador de Encontros por HP/rodadas. Migração preserva PV/CD de fichas antigas. 44 testes OK.
