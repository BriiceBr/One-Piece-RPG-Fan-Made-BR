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
