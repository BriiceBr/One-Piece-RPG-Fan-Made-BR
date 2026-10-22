# Fluxos de navegação do Mestre — contagem de cliques

Medição feita na versão de 21/10/2026, antes e depois das melhorias de "mesa ao vivo".
"Clique" = clique de mouse; atalhos de teclado contam como 0.

| # | Fluxo | Antes | Depois | Como ficou |
|---|---|---:|---:|---|
| 1 | Saber de quem é o turno, PV, PE e defesas | 2 (abrir ficha na árvore + aba) | **0** | Painel do turno no Tracker mostra tudo |
| 2 | Aplicar dano em quem está jogando | 3 + N cliques no "−" (abrir ficha, achar campo, clicar) | **1 atalho** (`D`) + valor | Atalho → popup de valor |
| 3 | Curar | idem dano | **1 atalho** (`C`) + valor | idem |
| 4 | Passar o turno | 1 clique | **0 (Espaço)** | Atalho global |
| 5 | Marcar condição | 3 (botão direito → Condições → item) | **3** | Agora com duração e desconto automático |
| 6 | Ajustar duração de condição | não existia | **3** | Menu → +1/−1 turno, ou automático no turno |
| 7 | Selecionar 1ª a 9ª linha | 1 clique na linha | **0** (tecla 1–9) | Atalho |
| 8 | Rolar iniciativa da pasta | 2 (selecionar pasta + botão) | **1 + 0** (F5 com a pasta em foco) | Atalho |
| 9 | Abrir ficha | 2 (duplo clique antigo) | **1** | Clique único |
| 10 | Exportar ficha em Markdown | 3 (abrir ficha, Exportar, salvar) | **3** | Sem mudança |
| 11 | Gerar cartaz WANTED | não existia | **3** (abrir ficha, Cartaz, salvar) | Novo recurso |
| 12 | Gerar loot | 4 (abrir ficha, aba Loot, botão) | **3** | Aba Loot já aberta na sessão |
| 13 | Gerar golpe por patamar | não existia | **2** (Golpe → Gerar) | Novo recurso |
| 14 | Tocar efeito sonoro | não existia | **1** | Botão no Tracker |

## Leitura dos números

- O turno completo (ver, dano, condição, passar) caiu de **~12 cliques** para **1 atalho + 1 popup + 3 no menu de condição + 0**.
- O que ainda custa cliques é o que **exige escolha** (condição específica, exportar, salvar arquivo).
- Os fluxos 10 a 13 são os candidatos naturais para atalhos na próxima rodada.

## Propostas para reduzir mais (não implementadas)

1. `Ctrl+E` exporta a ficha aberta em Markdown sem diálogo (salva ao lado do cofre).
2. `Ctrl+L` gera loot da ficha aberta e já joga no log.
3. Duplo clique na linha já abre o popup (feito) e o popup poderia ter as 4 condições mais usadas.
4. Busca global (`Ctrl+K`) que abre a ficha direto pelo nome, sem passar pela árvore.
5. Um "modo combate" que abre o Tracker e a ficha do chefe automaticamente ao rolar iniciativa.
