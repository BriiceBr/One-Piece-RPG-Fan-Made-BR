# Histórico de Alterações – One Piece RPG

Registro contínuo de tarefas executadas no projeto.

---

### [13/10/2026] – Inicialização e Diagnóstico do Livro
- **Responsável:** Antigravity + Usuário
- **Ações Realizadas:**
  - Instalada a biblioteca `pymupdf` no ambiente Python local.
  - Extraído o texto integral do livro (`livros/Livro Teste Para IA.pdf`, 147 páginas) preservando a leitura por blocos/duas colunas:
    - Páginas 1 a 67 salvas em `texto/sistema_novo_p1-67.txt` (sistema novo).
    - Páginas 68 a 147 salvas em `texto/livro_antigo_p68-fim.txt` (livro antigo).
  - Analisado o arquivo Word atualizado (`livros/Livro One Piece RPG.docx`) e extraído para `texto/livro_word.txt`.
  - Descoberto que as fórmulas de Defesa e a característica *Tinta* já foram corrigidas no Word.
  - Esclarecido o funcionamento do **Dado de Vida** como aumento de PV acoplado à escolha de Habilidades por nível (`dX/2 + 1` ou rolagem + maior atributo).
  - Alinhada a decisão de manter a maioria das Vantagens em Origens, elegendo apenas algumas específicas para bônus de +2.
  - Gerado o primeiro relatório completo de diagnóstico em `anotacoes/relatorio_estado.md`.
  - Criado o arquivo de rastreamento de tarefas e decisões em `anotacoes/pendencias.md`.
- **Arquivos Criados:**
  - `texto/sistema_novo_p1-67.txt`
  - `texto/livro_antigo_p68-fim.txt`
  - `texto/livro_word.txt`
  - `anotacoes/relatorio_estado.md`
  - `anotacoes/pendencias.md`
  - `anotacoes/historico.md`
  - `anotacoes/regras_pe_transmutacao.md`
  - Criado o arquivo `rascunhos/Livro_One_Piece_Habilidades_Completo.docx` contendo todas as habilidades anteriores (*Arte do Tempo*, *Ataque Extra*, *Ambidestro*, *Mestre Espadachim*, *Casca-Grossa*) e a nova árvore unificada (*Artes Marciais*), todas 100% diagramadas no modelo novo.

---

### [21/10/2026] – ImpelDown Archives: Poça de d20 e Teste de Perícia na ficha
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - Padronizado o nome do sistema em `config.py` para **"ImpelDown Archives - One Piece RPG"**.
  - Adicionada a **Poça de d20** em `core/dados.py`, convivendo com o motor antigo de dados somados:
    - `rolar_dados_seguro` continua igual (dano e ataques, ex.: `2d8+3`), agora tipado.
    - Novas: `dados_do_grau`, `rolar_poca_d20`, `ResultadoTeste` e `rolar_teste_pericia`.
    - Regra: 1d20 (Leigo) a 4d20 (Mestre), usa o maior dado; Vantagem +1 dado e Desvantagem −1 dado; poça em 0 ou menos rola 2d20 e usa o menor; total = maior dado + Atributo + bônus fixo.
  - Adicionado o bloco **"Teste de Perícia (poça de d20)"** na aba Atributos de `ui/ficha_frame.py`, com menus de Atributo e Grau, ajuste de ±1 dado, campo de CD opcional, botão 🎯 Rolar, resultado colorido na ficha e registro no log de combate.
  - Testes: `py -m py_compile` em todos os 11 módulos (OK) e teste de instanciação da ficha em janela oculta, rolando Teste com e sem CD (OK).
  - Conferência de balanceamento por simulação (20.000 rolagens, Atributo 2, Treinado): CD 12 ≈ 79,6% e CD 15 ≈ 64,2%; com 1 Desvantagem, 55,3% e 40,1%.
- **Arquivos Alterados:**
  - `ImpelDown Archives/config.py`
  - `ImpelDown Archives/core/dados.py`
  - `ImpelDown Archives/ui/ficha_frame.py`
- **Decisão registrada:** para o aplicativo, a fórmula de PV oficial é `(12 + Fis) + (Nível - 1) * (6 + Maior Atributo)`, de `core/regras.py`. A proposta de PV do AGENTS.md (seção 7) fica descartada para o app.

---

### [21/10/2026] – ImpelDown Archives: PV atual/máximo e dano no Combat Tracker
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - Corrigido bug em que o PV danificado voltava ao máximo ao reabrir a ficha (os traces de Nível/Atributo sobrescreviam o PV atual).
    - `FichaPersonagemFrame` ganhou `pv_max` e `pe_max`; `calcular_derivados` recalcula só o máximo e limita o atual.
    - Quem está com PV cheio continua cheio ao subir Nível/Atributo; quem está ferido mantém o dano.
    - Cabeçalho da ficha mostra `PV atual / máximo` e `PE atual / máximo`; digitar valor acima do máximo ou negativo é limitado automaticamente.
    - `get_dados()` passou a gravar `pv_max` e `pe_max`.
  - Combat Tracker (`ui/app_main.py`):
    - Menu de contexto da lista ganhou **⚔️ Aplicar Dano…**, **💚 Curar…** e **💀 Zerar PV**, acima das condições.
    - Botões **⚔️ Dano** e **💚 Cura** abaixo de "Próximo Turno", agindo na linha selecionada ou em quem está jogando.
    - Lista mostra `PV atual/máximo` com cor: verde acima de 50%, âmbar até 50%, vermelho até 25%, cinza em 0.
    - Dano/cura atualiza a ficha aberta e o banco, registra no histórico (`⚔️ Nome levou 12 PV (34 → 22)`) e avisa quando chega a 0 PV.
    - A seleção da lista é preservada após cada atualização.
  - Testes: `py -m py_compile` em todos os módulos (OK); teste headless da aplicação completa verificando dano, cura limitada ao máximo, dano limitado a 0, persistência após reabrir a ficha, cores por gravidade e seleção preservada (OK).
- **Arquivos Alterados:**
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `anotacoes/pendencias.md` (seção 4, App ImpelDown Archives)

---

### [21/10/2026] – ImpelDown Archives: loot, história, condições e ajustes de interface
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **PV/PE maiores:** números do cabeçalho em fonte 26 negrito, campos e botões ± maiores, com `atual / máximo` ao lado. "Tela Jogador" e "Exportar .md" foram para a barra da aba, para o cabeçalho caber com o Tracker aberto.
  - **Loot ampliado (`utils/loot.py` reescrito):**
    - 5 raridades (Comum, Incomum, Raro, Épico, Lendário) e 56 itens com tipo descritivo: armas, equipamentos, consumíveis, navegação, ferramentas e tesouros.
    - Berries crescem por Nível (≈200 no Nv 1 e ≈45 mil no Nv 20) e a quantidade de itens vai de 1 a 7.
    - Pesos de raridade por Nível; a chance de Épico/Lendário sobe com o Nível. Limite em Nível 20 para simplificar.
  - **História por IA local (`utils/historia.py` novo):** 7 blocos (Origem, Aparência, Personalidade, Combate, Objetivo, Gancho e Ameaça) montados a partir de Atributos, Graus de Perícia, Nível e recompensa. Regerar substitui o bloco anterior em vez de empilhar.
  - **Condições do livro (`core/condicoes.py` novo):** as 15 condições de p. 28 a 31 com ícone, nome e resumo do efeito. O menu do Tracker virou o submenu "Condições", com marcação ✓ e várias condições por linha; tooltip mostra o efeito de cada uma.
  - **Tracker:** clique em área vazia desmarca a linha e o botão direito no vazio não abre menu.
  - **Árvore:** a ficha abre com **um clique**; arrastar continua funcionando e não abre aba.
  - **Correções encontradas no caminho:**
    - Painel do Tracker nascia espremido (ordem do `pack`); passou a entrar antes do notebook.
    - PV salvo era reduzido ao abrir a ficha (o callback da árvore gravava Nível de volta no dicionário em carga) — corrigido com cópia do dicionário e PV carregado por último.
    - Fichas de exemplo sem Atributos: Arlong agora é Nv 3 com PV 36, e Rei dos Mares Nv 5 com PV 61.
    - Ícone "🔥" saía como gota d'água no Tk; trocado por "♨" e "⬇️" por "▼".
- **Testes:** `py -m py_compile` em todos os módulos; teste de integração headless cobrindo clique único, arrasto, 15 condições, dano/cura, desseleção, loot, história e carga de PV; capturas de tela em `anotacoes/captura_tracker.png` e `anotacoes/captura_icones.png`.
- **Arquivos Alterados:**
  - `ImpelDown Archives/utils/loot.py` (reescrito)
  - `ImpelDown Archives/utils/historia.py` (novo)
  - `ImpelDown Archives/core/condicoes.py` (novo)
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `anotacoes/pendencias.md`

---

### [21/10/2026] – Ajustes no tooltip e no tamanho de PV/PE
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **Tooltip reposicionado (`ui/popups.py`):** a caixa é medida depois de montada e passa a abrir para a esquerda quando não cabe à direita do cursor, e para cima quando não cabe abaixo. Também fica presa dentro da tela e o texto ganhou quebra de linha (`wraplength=380`), em vez de virar uma faixa comprida.
  - **PV/PE em tamanho médio:** a fonte `number` caiu de 26 para 20 (negrito), deixando os dois recursos com o mesmo tamanho e sem estourar o cabeçalho.
- **Testes:** `py -m py_compile` em todos os módulos; teste do tooltip em 5 posições (bordas direita, inferior, esquerda, topo e centro) confirmando que a caixa nunca sai da tela; captura em `anotacoes/captura_tooltip.png`.
- **Arquivos Alterados:**
  - `ImpelDown Archives/ui/popups.py`
  - `ImpelDown Archives/ui/app_main.py`

---

### [21/10/2026] – Mesa ao Vivo: painel de turno, atalhos, WANTED, golpes e soundboard
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **Painel do turno no Tracker:** cartão fixo com nome, `PV atual/máximo`, `PE atual/máximo`, Defesas/CD e condições com duração. Atualiza junto com a lista, sem abrir ficha.
  - **Condições com duração:** aplicadas com **3 turnos** por padrão; `proximo_turno()` desconta as do combatente que começa o turno, remove no zero e registra no log. Menu ganhou `⏱ +1/-1 turno` e mostra o prazo de cada condição. Formato antigo (lista de strings) é aceito e migrado na leitura.
  - **Atalhos globais:** `Espaço` próximo turno, `D`/`C` dano/cura, `1–9` seleciona linha, `Esc` limpa seleção, `F5` rola iniciativa da pasta, `Ctrl+F` busca (já existia). Ignorados quando o foco está em campo de texto.
  - **Duplo clique na linha:** popup com Dano, Cura, Condições e Fechar, sem sair do painel.
  - **Cartaz WANTED (`utils/cartaz.py`):** PNG 900×1200 com moldura no tema do app, retrato da ficha, nome, "DEAD OR ALIVE", recompensa e nível; pré-visualização com "Abrir imagem" e "Copiar caminho". Botão "📜 Cartaz WANTED" na barra da aba.
  - **Gerador de golpes (`utils/golpes.py`):** popup com Patamar × Categoria × Sabor; usa os custos/limites de `anotacoes/regras_pe_transmutacao.md` (Básica 0/+2, Média 1/+3, Forte 3/+4, Suprema 5/+5, níveis 1/4/8/12) e o dano típico por patamar. Gera um bloco de habilidade completo na ficha.
  - **Soundboard (`utils/sons.py`):** quatro slots (Canhão, Navio, Impacto, Haki) e botão de mudo; toca WAV de `ImpelDown Archives/sons/` e fica em silêncio se o arquivo não existir.
  - **Documentação de UX:** `anotacoes/ux_fluxos.md` com 14 fluxos, contagem de cliques antes/depois e 5 propostas de redução.
- **Testes:** `py -m py_compile` em todos os módulos; teste headless verificando painel do turno, aplicação e expiração de condição (3→2→…→0), atalho numérico e Esc, golpe Suprema com custo/limite corretos, cartaz 900×1200 gerado, soundboard silencioso sem arquivos e popup de duplo clique.
- **Arquivos Alterados:**
  - `ImpelDown Archives/utils/cartaz.py` (novo)
  - `ImpelDown Archives/utils/golpes.py` (novo)
  - `ImpelDown Archives/utils/sons.py` (novo)
  - `ImpelDown Archives/sons/LEIA-ME.txt` (novo)
  - `ImpelDown Archives/ui/app_main.py`
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `anotacoes/ux_fluxos.md` (novo)

---

### [22/10/2026] – Histórico em janela, soundboard removido e fim do popup de duplo clique
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **Histórico de rolagens virou sobreposição:** o bloco fixo no rodapé do Tracker foi removido (ele estava sendo cortado). Agora há um botão **📜 Log** no topo do painel que abre/fecha uma janela no canto inferior direito, com até 500 linhas guardadas, botão **🧼 Limpar** e **✖**. O botão alterna entre "📜 Log" e "📜 Fechar".
  - **Soundboard retirado do Tracker:** os quatro botões (Canhão, Navio, Impacto, Haki) e o botão de mudo saíram da interface. `utils/sons.py` permanece no projeto, sem uso, caso o recurso volte.
  - **Duplo clique removido:** clicar duas vezes na linha do Tracker não abre mais o popup de ações; a linha apenas é selecionada, como um clique normal.
  - O espaço liberado no painel volta para a lista de iniciativa.
- **Testes:** `py -m py_compile` em todos os módulos; teste headless confirmando histórico guardado antes de abrir, janela criada com o conteúdo antigo, mensagens novas aparecendo com a janela aberta, fechar/reabrir, limpeza do log e ausência do vínculo de duplo clique e do soundboard. Captura em `anotacoes/captura_log.png`.
- **Arquivos Alterados:**
  - `ImpelDown Archives/ui/app_main.py`
  - `anotacoes/pendencias.md`

---

### [22/10/2026] – Refatoração: indentação, debounce, história, estatísticas, lacaios, loot e dificuldade
- **Responsável:** DeepSeek + Usuário
- **Correções:**
  - **`gerar_nome_pirata`:** corpo reindentado de 12 para 8 espaços (426 linhas normalizadas) e assinatura tipada (`-> None`). A lista de títulos não foi alterada.
  - **Debounce dos derivados:** os `trace_add` de Nível/Atributos/Mods agora chamam `_agendar_calculo` (40 ms) em vez de recalcular a cada tecla; `carregar_dados` força um cálculo síncrono para restaurar PV/PE com os máximos certos; o agendamento é cancelado no `<Destroy>`.
  - **História:** novo botão **📖 Expandir História** abre modal 860×660 com Aplicar/Cancelar.
- **Melhorias:**
  - **Estatísticas detalhadas:** distribuição por pasta/facção, faixas de perigo (1–3, 4–8, 9–14, 15+), maior Nível e maior Recompensa, total de habilidades e execução mais comum, soma de PV, PE e recompensas. Exibido em janela rolável (`_mostrar_relatorio`).
  - **Lacaios inteligentes:** diálogo com nome base (sugerido pela facção), quantidade e arquétipo (Esquadrão Balanceado, Bando de Atiradores, Vanguarda Pesada). Cada lacaio varia ±1 nos Atributos (0–5) e nos Graus (0–3).
  - **Loot contextual:** `gerar_loot_aleatorio` aceita `dados` e `faccao`, usa pools de Piratas/Marinha/Feras/Governo, favorece armas para Físico/Luta alto e mapas/ferramentas para Intelecto/Instinto alto, e tem 2%–5% de chance de Akuma no Mi desconhecida a partir do Nível 12.
  - **Dificuldade relativa:** `calcular_dificuldade_encontro` compara poder dos inimigos (soma de Níveis × multiplicador de horda) com o poder do grupo (jogadores × nível médio): Fácil ≤60%, Médio ≤100%, Difícil ≤140%, Mortal acima. Painel do Tracker ganhou os campos "Jogadores" e "Nível médio".
- **Testes:** `py -m py_compile` em todos os módulos; teste de debounce (PV só atualiza após 40 ms), carga de ficha (36/36), modal de história, dificuldade (1 inimigo Nv 10 vs 4×5 = 50% Fácil; 10 lacaios = 95% Médio; chefe Nv 20 = 100% Médio), loot por facção com item exclusivo, 5% de frutas em 4.000 loots de Nível 20, lacaios variados e relatório completo.
- **Arquivos Alterados:**
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `ImpelDown Archives/core/combate.py`
  - `ImpelDown Archives/utils/loot.py`
  - `anotacoes/pendencias.md`

---

### [22/10/2026] – Ajuda, rolagem inline, PV extra, lacaios por Nível, WANTED, multiseleção e golpes automáticos
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **Menu Ajuda:** cascata "Ajuda" com **⌨️ Atalhos** (lista completa em janela de leitura) e **ℹ️ Sobre**.
  - **Rolar sem popup:** o cabeçalho da ficha ganhou um campo de expressão (`2d8+3`, Enter também rola). O botão 🎲 Rolar usa o campo; vazio rola `1d20`.
  - **Log natural:** o histórico deixou de ser janela flutuante e virou painel embutido no rodapé do Tracker, aberto/fechado pelo botão 📜 Log (abre o Tracker se estiver escondido).
  - **PV/PE máximos extras:** `calcular_atributos_derivados` aceita `bonus_pv`/`bonus_pe`; a ficha ganhou os contadores **+PV Máx** e **+PE Máx**, persistidos em `get_dados`/`carregar_dados`.
  - **Lacaios por Nível:** o diálogo ganhou campo Nível; `_perfil_lacaio` escala Atributos (até 5) e Graus (até 3) pelo Nível e pelo arquétipo, mantendo a variação ±1.
  - **Inimigo caído em vermelho:** com PV 0 a linha fica `#e06c75`; se for o turno atual, usa `#ffb3b3` sobre o destaque.
  - **Cartaz WANTED refeito:** pergaminho com manchas discretas, moldura de tinta, "WANTED" em serifa ajustado à largura, retrato em moldura branca, "DEAD OR ALIVE", nome, `B$` com traço e selo **MARINE**.
  - **Exclusão múltipla:** árvore em `selectmode="extended"`; Ctrl/Shift selecionam sem abrir aba; `deletar_item` apaga todas as seleções com uma confirmação.
  - **Golpes automáticos:** `gerar_golpe_automatico` escolhe patamar pelo Nível (1/4/8/12), categoria pelos Atributos e sabor pela facção; o botão ✨ Golpe insere direto, sem popup.
- **Testes:** `py -m py_compile` em todos os módulos; testes de +PV máximo (36→46), rolagem sem popup, golpe automático sem Toplevel, log embutido, atalhos (15 linhas), cartaz 720×1060 com retrato, lacaio Nv 5 (PV 51), linha vermelha em 0 PV, `selectmode` extended e exclusão de 2 fichas de uma vez. Capturas em `anotacoes/captura_mesa.png` e `anotacoes/cartaz_teste.png`.
- **Arquivos Alterados:**
  - `ImpelDown Archives/core/regras.py`
  - `ImpelDown Archives/utils/golpes.py`
  - `ImpelDown Archives/utils/cartaz.py`
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `anotacoes/pendencias.md`

---

### [21/10/2026] – Auditoria completa e refatoração de desempenho/coerência
- **Responsável:** DeepSeek + Usuário
- **Achados corrigidos:**
  - **Tooltip caro:** criava um `Toplevel` a cada `<Motion>`; agora a janela é única, reutilizada, medida e só reposicionada quando o texto muda.
  - **Pesquisa reconstruía a árvore a cada tecla:** passou a ter debounce de 160 ms e só restaura quando havia filtro ativo.
  - **Menus acumulados:** cada clique direito criava um `tk.Menu` novo; agora o anterior é fechado e destruído.
  - **MouseWheel global:** `bind_all`/`unbind_all` na ficha podiam apagar vínculos de outros widgets; trocado por vínculo local no canvas e na lista.
  - **Salvamento não atômico:** o SQLite agora grava em `.tmp` e usa `os.replace`, com `closing` e modo somente leitura ao carregar. Falha no meio não corrompe o cofre.
  - **Perda de dados ao fechar:** `WM_DELETE_WINDOW` agora pergunta e salva antes de sair.
  - **Fichas pela metade:** `montar_ficha()` substitui os dicionários parciais (PV 100 sem Atributos) em fichas novas, lacaios e exemplos — Arlong e Rei dos Mares nascem completos.
  - **Estouro em texto:** Nível inválido não quebra mais `combate.py` nem as estatísticas (`nivel_seguro`); a ficha grava Nível sempre numérico.
  - **Guias órfãs:** "Novo Cofre"/"Abrir Cofre" destruíam o frame sem remover a aba do notebook.
  - **Abas ao trocar tema/fonte:** as abas são fechadas e reabertas com os mesmos dados, e botões do shell são repintados com o novo accent — o tema agora vale para a tela inteira.
  - **Exceções silenciosas:** `calcular_derivados` só ignora erros de digitação (`ValueError`/`TypeError`/`TclError`).
  - **Duplicação de Markdown:** a ficha usa `utils/arquivos.exportar_ficha_markdown` em vez de repetir a montagem.
- **Testes:** `py -m py_compile` em todos os módulos; testes de integração cobrindo ficha padrão, combate com Nível inválido, abertura por clique, busca com filtro/restauração, troca de tema e de fonte com abas abertas, gravação atômica e recarga do banco, e reutilização da janela de tooltip. Captura em `anotacoes/captura_refactor.png`.
- **Arquivos Alterados:**
  - `ImpelDown Archives/ui/popups.py`
  - `ImpelDown Archives/core/combate.py`
  - `ImpelDown Archives/utils/arquivos.py`
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/app_main.py`

---

### [22/10/2026] – +PV/+PE ao lado de Luta/Acro e log como sobreposição
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **Contadores +PV Máx / +PE Máx** saíram da linha extra no rodapé dos bônus (que era cortada) e agora ficam na mesma linha de **Grau Luta / Grau Acro**, com valor de 22 px para caber nos 340 px do painel.
  - **Histórico de rolagens** deixou de usar `pack` e passou a flutuar com `place` sobre o rodapé do Tracker (`relx=0, rely=1, anchor="sw", relwidth=1`). Antes o painel empurrava o log para fora da janela e só o título aparecia; agora ele aparece inteiro sobre os botões e não rouba espaço da lista.
- **Testes:** `py -m py_compile`; +PV/+PE aplicados (36→41 e 11→13); log aberto com `winfo_ismapped()=1`, altura 263, encostado no fim do painel (y+h = altura do Tracker) e mensagens visíveis. Captura em `anotacoes/captura_log2.png`.
- **Arquivos Alterados:**
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `anotacoes/pendencias.md`

---

### [22/10/2026] – Correção dos 10 bugs da auditoria
- **Responsável:** DeepSeek + Usuário
- **Correções:**
  1. **Log limitado:** o widget agora é cortado no mesmo teto de 500 linhas da lista.
  2. **Corrida do debounce:** `aplicar_pv_tracker` chama `sincronizar_agora()` antes de ler o máximo — dano logo após mudar +PV já usa o valor novo (56 em vez de 36).
  3. **combate.py tolerante:** jogadores/nível/inimigos aceitam texto sem estourar.
  4. **historia.py tolerante:** `_inteiro()` substitui os `int()` diretos; Nível "abc" não quebra.
  5. **Tracker com atualização de linha única:** `_render_linha` + `_atualizar_linha` substituem o rebuild total em dano/cura/condições.
  6. **sync_nome_ficha O(1):** usa `_mapa_tracker` (id → índices) montado no refresh, com fallback.
  7. **Tema preserva a aba selecionada:** `_reconstruir_abas` guarda o índice e reseleciona a mesma ficha.
  8. **Dificuldade sem duplicar ficha real:** o mesmo id conta uma vez; lacaios genéricos contam por linha.
  9. **HabilidadeBloco:** toggle por estado booleano e redimensionamento por altura inicial + deslocamento do ponteiro.
  10. **Arrastar em grupo:** soltar sobre pasta move todas as fichas selecionadas.
- **Extra:** cartaz.py não depende mais de `font.size` no laço do "WANTED".
- **Testes:** py_compile; log 500/500; combate com strings OK; história com Nível inválido OK; dano imediato após +20 PV usando máximo 56; 200 danos a 3,14 ms; renomear atualiza linha; duplicado conta 1 e dois lacaios contam 2; tema mantém aba 1; altura do bloco 112→232; arrasto move F1 e F2 juntos.

---

### [22/10/2026] – Limpeza: paleta semântica, tema ao vivo, patamares unificados e som removido
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **`core/paleta.py` criado:** cores por papel (`TEXTO_SUAVE`, `PERIGO`, `AVISO`, `SUCESSO`, `HOVER`, `ALCA`, botões de perigo/sucesso, cores de dificuldade e do tooltip).
  - **108 literais substituídos** por esses papéis ou pelas cores do tema: 74 em `app_main.py`, 34 em `ficha_frame.py`, 5 em `widgets_custom.py`. Sobraram apenas `"white"` (contraste proposital) e as definições da própria paleta.
  - **Tema ao vivo sem recriar abas:** `mudar_tema` agora percorre a árvore de widgets e troca as cores do tema antigo pelas do novo (`_reaplicar_visual` / `_repintar_widget`). Inclui os internos do `CTkTabview` (o botão segmentado não aparece em `winfo_children`).
  - **Fonte ao vivo sem recriar abas:** `_reaplicar_fonte` / `_trocar_fonte_widget` trocam só a família, preservando tamanho e estilo.
  - **`accent_hover` por tema** no `config.py`, usado no botão Rolar.
  - **PATAMARES unificados:** `inserir_habilidade` passou a ler `utils/golpes.PATAMARES` (fim da tabela duplicada).
  - **Código morto removido:** `utils/sons.py` e a pasta `sons/` apagados.
- **Testes:** `py -m py_compile` em todos os módulos; troca de tema mantendo a **mesma instância** de ficha (`is`), scroll preservado, botão e aba "Atributos" repintados (`#7852FF → #e05353`), filtro idem; troca de fonte Segoe UI → Consolas com a mesma aba; `inserir_habilidade("Média")` com custo `1 PE` e limite `+3 PE` vindos da tabela única. Captura em `anotacoes/captura_paleta.png`.
- **Arquivos Alterados:**
  - `ImpelDown Archives/core/paleta.py` (novo)
  - `ImpelDown Archives/core/combate.py`
  - `ImpelDown Archives/config.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/widgets_custom.py`
  - `ImpelDown Archives/ui/popups.py`
  - `ImpelDown Archives/utils/sons.py` e `ImpelDown Archives/sons/` (removidos)

---

### [22/10/2026] – Ganhos rápidos, testes e ferramentas de preparação
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  1. **Salvamento automático + backup:** `_agendar_autosave`/`_autosave` salvam a cada 3 minutos quando há cofre aberto; `salvar_banco_sqlite` copia a versão anterior para `.db.bak` antes de substituir.
  2. **Desfazer (Ctrl+Z):** pilha de até 50 ações para PV e condições; restaura ficha aberta/banco e redesenha a linha.
  3. **Configuração no cofre:** coluna `config` no SQLite guarda "Jogadores" e "Nível médio"; bancos antigos sem a coluna continuam abrindo (config vazia).
  4. **Busca global (Ctrl+K):** janela com filtro por nome, Enter/duplo clique abre a ficha direto.
  5. **Gerador de encontros (`utils/encontros.py`):** busca composições de chefe + lacaios que caem em Fácil/Médio/Difícil/Mortal e permite criá-las no cofre.
  6. **Bestiário:** cria Capanga, Elite ou Chefe por Nível com bônus de PV/PE e atributo reforçado.
  7. **Editor de habilidades:** campo "PE extra" com prévia de custo e alerta quando o extra passa do limite do patamar.
  8. **Importação em lote (`utils/importacao.py`):** JSON (ficha ou lista/`fichas`) e CSV (`;` ou `,`) com validação de nome, Nível 1+, Atributos 0–5 e Graus 0–3.
  9. **Tema por facção:** abrir ficha de pasta Marinha/Pirata/Monstros/Governo aplica o tema correspondente.
  10. **Testes automatizados:** `ImpelDown Archives/tests/test_core.py` e `test_utils.py` com 25 testes (unittest; também rodam no pytest).
- **Testes:** `py -m unittest discover -s tests` → **25 testes OK**; smoke do app cobrindo tema por facção, abertura dos três diálogos, gravação com config + `.bak`, aplicação da config e Ctrl+Z vazio.
- **Arquivos Alterados:**
  - `ImpelDown Archives/utils/arquivos.py`
  - `ImpelDown Archives/utils/encontros.py` (novo)
  - `ImpelDown Archives/utils/importacao.py` (novo)
  - `ImpelDown Archives/ui/widgets_custom.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `ImpelDown Archives/tests/test_core.py` (novo)
  - `ImpelDown Archives/tests/test_utils.py` (novo)
  - `anotacoes/pendencias.md`

---

### [22/10/2026] – Correções de UX: tema, arquétipos, habilidades, golpes e encontros
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **Tema não troca mais sozinho:** removida a troca automática ao abrir ficha. O tema por facção virou ação manual no menu de contexto (**🎨 Tema da facção**) de fichas e pastas.
  - **Arquétipos de lacaios mais claros:** o menu suspenso com nomes longos virou **botões segmentados** (Balanceado / Atiradores / Vanguarda) com uma descrição logo abaixo explicando cada estilo.
  - **Habilidades corrigidas:** o cabeçalho do bloco foi dividido em duas linhas (título + botões na primeira, custo/limite/execução/alcance na segunda), então o ✖ deixou de ser empurrado para fora. A exclusão agora usa um callback (`ao_remover`) — o evento `<Destroy>` não removia o bloco da lista.
  - **Campo de PE esclarecido:** "PE extra" passou a **Potencialização (+PE)**, com prévia `+2 de +4 → total 5 PE` e aviso vermelho quando passa do limite do patamar.
  - **Golpe com escolha de patamar:** o botão ✨ Golpe abre um diálogo com **Básica/Média/Forte/Suprema** (sugestão pelo Nível); categoria e sabor continuam automáticos pela ficha.
  - **Encontros organizados:** o gerador cria uma pasta **“Encontro Gerado — <dificuldade>”** com as subpastas **Chefes** e **Lacaios**, cada inimigo na pasta certa.
- **Testes:** `py -m unittest discover -s tests` → 25 testes OK; smoke confirmando tema inalterado ao abrir ficha, tema manual aplicado (Pirata), pastas do encontro com chefe/lacaios, exclusão de bloco 2→1 (inclusive bloco carregado), prévia de PE e diálogo de golpe.
- **Arquivos Alterados:**
  - `ImpelDown Archives/ui/app_main.py`
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/widgets_custom.py`
  - `anotacoes/pendencias.md`

---

### [22/10/2026] – Recompensa, faixa de graus, PV/PE digitáveis e reabertura em cache
- **Responsável:** DeepSeek + Usuário
- **Ações Realizadas:**
  - **Digitação da recompensa corrigida:** o trace que formatava a cada tecla (e movia o cursor) foi removido. O valor fica livre enquanto se digita e é formatado ao sair do campo/Enter; `get_dados` grava só dígitos.
  - **Graus de Luta/Acrobacia de -1 a 4:** os contadores da ficha foram limitados a esse intervalo, `core/regras.py` passou a aceitar -1..4 (mantendo PV/PE com piso 1) e a importação em lote valida a mesma faixa. Atributos continuam 0..5.
  - **PV Máx e PE Máx digitáveis:** os valores ao lado de `/` viraram campos de edição. Ao confirmar (Enter ou sair), a diferença em relação ao cálculo vira bônus em `mod_pv`/`mod_pe` — que agora aceita valores negativos.
  - **Reabertura de ficha em cache:** ao fechar uma aba, o frame não é mais destruído; ele fica em um cache de até 4 fichas. Reabrir reaproveita o frame e sincroniza só nome/Nível/PV/PE (`atualizar_dados_rapidos`). Imagens também ficam em cache por caminho.
  - **Ganho medido:** primeira abertura ~637 ms; reabertura pelo cache ~94 ms (≈6,8× mais rápida), mantendo tema/fonte aplicados porque o frame continua filho do notebook.
- **Testes:** `py -m unittest discover -s tests` → 25 OK; smoke confirmando digitação sem reformatar (`1234567` → sai → `1.234.567`), PV Máx digitado (50, mod +14), PE Máx (3, mod -8), grau -1 (Bloq 12) e grau 4 (Esq 20), cache devolvendo a mesma ficha.
- **Arquivos Alterados:**
  - `ImpelDown Archives/core/regras.py`
  - `ImpelDown Archives/utils/importacao.py`
  - `ImpelDown Archives/ui/ficha_frame.py`
  - `ImpelDown Archives/ui/app_main.py`
  - `ImpelDown Archives/tests/test_utils.py`
  - `anotacoes/pendencias.md`

