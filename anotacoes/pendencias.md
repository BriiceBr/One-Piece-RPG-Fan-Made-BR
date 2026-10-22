# Pendências do Projeto – One Piece RPG

Lista viva de itens a corrigir, decisões pendentes e conversões a realizar.  
*(Atualizada com base na análise do arquivo `livros/Livro One Piece RPG.docx`)*

---

## 1. Status do Livro e Sistema Novo (Comparações Word vs. PDF)

- [x] **Fórmulas de Defesa Ativa:**
  - *Status:* **Já corrigidas no Word!** No Word já consta a fórmula correta de soma: `10 + Atributo + (2 × Grau da Perícia)`.
- [x] **Característica Tinta (Raça Polvo):**
  - *Status:* **Já corrigida no Word!** O uso foi alterado de "Bônus de Treinamento" para "igual a seu Atributo de Físico".
- [x] **Dado de Vida Esclarecido:**
  - *Status:* **Regra confirmada pelo autor.** Não é dado de descanso de D&D; é o aumento de PV concedido por cada Habilidade ao subir de nível (o jogador escolhe rolar o dX da habilidade ou pegar a média `dX/2 + 1`, somando seu maior atributo). No nível 1, habilidades raciais (como Ciborgue no Autômato) não concedem esse dado de vida porque a vida inicial vem da Raça.
- [ ] **Tabela de Graus de Perícia:**
  - Ajustar para a notação sem sinal de soma: `Grau 0 (Leigo): 1d20`, `Grau 1 (Treinado): 2d20`, `Grau 2 (Especialista): 3d20`, `Grau 3 (Mestre): 4d20`.
- [ ] **Pontuação na Escolha de Nível:**
  - Inserir dois pontos `:` na frase: *"A cada nível a partir do 2, o jogador escolhe uma destas opções:"*
- [ ] **Eliminação dos Resquícios de Bônus de Treinamento no Livro:**
  - Restam cerca de 12 menções no Word (ex.: habilidades *Casca-Grossa*, *Nuvens Artificiais/Combo*, *Pistola da Água*, *Arte da Substituição*, etc.) que precisam de novo critério de usos/bônus.
- [ ] **Seleção de Vantagens vs. Bônus (+2) nas Origens:**
  - Conforme alinhado com o autor: manter a maioria das Origens com Vantagem e selecionar pontualmente aquelas em que um bônus fixo de +2 seja mais equilibrado.

---

## 2. Decisões do Autor em Andamento

- [x] **Balanceamento de Pontos de Esforço (PE):**
  - *Status:* Estruturado com valores fixos e documentado em `anotacoes/regras_pe_transmutacao.md`. Custos base: Básica 0, Média 1, Forte 3, Suprema 5. Limites fixos de transmutação: Básica até +2, Média até +3, Forte até +4, Suprema até +5.
- [ ] **Recuperação de Recursos em Descansos:**
  - Confirmar a recuperação: Descanso Parcial recupera metade do PE máximo (até o limite de 50%); Descanso Total recupera 100% de PV e PE.
- [ ] **Haki e Akuma no Mi:**
  - Confirmar requisitos de nível (Haki nos níveis 8 e 14) e integração com o custo de PE.

---

## 3. Conversão do Livro Antigo (Habilidades, Equipamentos e Regras Avançadas)

- [ ] **Equipamentos e Armas:** Atualizar tabela de armas, armaduras e propriedades.
- [ ] **Habilidades de Classes e Estilos (p. 73 a 118 do PDF / seções do Word):**
  - Substituir o antigo Bônus de Treinamento e custos antigos por custos de PE e Atributos fixos.
- [ ] **Haki e Akuma no Mi:** Adequar as frutas e poderes aos graus de perícia e PE.
- [ ] **Itens, Dials e Regras Navais:** Revisar CDs e estatísticas de navios.

---

## 4. Aplicativo ImpelDown Archives

- [x] **PV máximo separado do PV atual:** `ficha_frame.py` passou a ter `pv_max`/`pe_max`; mudar Nível ou Atributo não cura mais o dano (e o dano sobrevive a salvar/reabrir).
- [x] **Dano e cura no Combat Tracker:** menu de contexto (⚔️/💚/💀) e botões rápidos aplicam PV na ficha aberta e no banco, com PV `atual/máximo` e cor por gravidade na lista.
- [x] **Condições do Tracker conforme o livro:** `core/condicoes.py` traz as 15 condições (p. 28 a 31), com ícone, nome e resumo; o menu virou submenu com ✓ e permite várias condições na mesma linha.
- [x] **Fichas de exemplo:** `inicializar_arvore_padrao` agora cria Arlong (Nv 3, PV 36) e Rei dos Mares (Nv 5, PV 61) com todos os Atributos, Graus e recursos.
- [ ] **Estados de Morrendo:** Ferimento Letal, Trauma Grave, Nocaute, Por um Fio e Inabalável têm regras próprias de Morte e Inconsciência, não são Condições. Decidir se entram no Tracker como painel separado.
- [ ] **PE no Tracker:** o dano/cura rápida cobre só PV; avaliar se PE também precisa de botões.
- [ ] **Duração das condições:** o livro exige que a fonte informe a duração; hoje o Tracker marca a condição sem prazo. Estudar um contador de Turnos por condição.
- [ ] **Loot sem equipamento:** os itens gerados têm tipo descritivo (arma, tesouro etc.), mas não alteram Atributos nem Defesas. Falta a tabela de equipamento do sistema novo.
- [ ] **História gerada sem Habilidades:** `utils/historia.py` usa Atributos, Graus, Nível e recompensa, mas ainda ignora as Habilidades da ficha e a imagem.
- [ ] **Ícones das condições:** no Tk eles saem monocromáticos e alguns emojis (🔥, ⬇️) não renderizam; os atuais foram trocados por símbolos compatíveis, mas vale revisar em outros temas.

### 4.1 Mesa ao Vivo (21/10/2026)

- [ ] **Soundboard fora da interface (22/10):** os botões de Canhão/Navio/Impacto/Haki e o mudo foram removidos do Tracker a pedido. `utils/sons.py` e a pasta `sons/` continuam no projeto, sem uso; se voltar, precisa de botão e de arquivos WAV.
- [ ] **Janela do histórico:** agora é uma sobreposição (`place`) no rodapé do Tracker, com ~215 px fixos. Enquanto aberta, cobre os botões de Dano/Cura/Próximo Turno; se incomodar, permitir arrastar/redimensionar ou abrir em altura menor.
- [ ] **Duração padrão das condições:** hoje 3 turnos fixos ao aplicar. Decidir se o padrão deve variar por condição (ex.: Atordoado 1, Envenenado 5) ou se o Mestre define no momento.
- [ ] **Golpes usam a tabela de PE da nota interna:** custos, limites e dados por patamar vêm de `anotacoes/regras_pe_transmutacao.md`, não do PDF. Precisa bater com a versão final do livro.
- [ ] **Cartaz WANTED:** usa fontes do Windows (Georgia/Times/Arial) com fallback para a fonte padrão do Pillow; em outra máquina o desenho pode mudar.
- [ ] **Atalhos × menus:** `Espaço` e letras são globais; se um dia houver menu aberto, o Tk pode consumir a tecla antes. Testar com menus abertos quando surgir necessidade.
- [ ] **Fluxos de UX:** as propostas de `anotacoes/ux_fluxos.md` (Ctrl+E exportar, Ctrl+L loot, busca global Ctrl+K, modo combate) ainda não foram implementadas.

### 4.3 Ajustes de 22/10/2026 (segunda rodada)

- [x] **Menu Ajuda:** cascata com "Atalhos" e "Sobre".
- [x] **Rolagem sem popup:** campo de expressão no cabeçalho da ficha.
- [x] **PV/PE máximos extras:** `bonus_pv`/`bonus_pe` em `regras.py` e contadores `+PV Máx`/`+PE Máx` na ficha.
- [x] **Lacaios por Nível:** perfis escalam Atributos e Graus conforme o Nível escolhido.
- [x] **Inimigo com 0 PV em vermelho** no Tracker.
- [x] **Cartaz no estilo do mangá:** pergaminho, WANTED, retrato, DEAD OR ALIVE, nome, recompensa e MARINE.
- [x] **Exclusão múltipla:** Ctrl/Shift na árvore; uma confirmação para todas.
- [x] **Golpes automáticos:** patamar por Nível, categoria por Atributos e sabor pela facção.
- [ ] **Golpe automático sem memória:** pode repetir título entre cliques; guardar os títulos já gerados na ficha evitaria repetição.
- [ ] **Golpe automático sem confirmação:** se o resultado não agradar, é preciso fechar o bloco (✖) e gerar de novo.
- [ ] **Cartaz sem retrato:** hoje mostra "SEM IMAGEM"; poderia usar um ícone genérico de silhueta.
- [ ] **Multiseleção e arrastar:** com vários itens selecionados, o arrasto move só a linha pressionada; definir comportamento esperado.

### 4.2 Refatoração de 22/10/2026

- [x] **Dificuldade fixa por soma de Níveis:** substituída pela comparação com o poder do grupo (jogadores × nível médio) e multiplicador de horda.
- [x] **Estatísticas detalhadas:** relatório com facções, faixas, destaques, habilidades e recursos.
- [x] **Lacaios variados:** arquétipos + flutuação de ±1 e nomes por facção.
- [x] **Loot contextual:** pools por facção, peso por Atributos e Akuma no Mi rara.
- [ ] **Akuma no Mi no loot:** é só gancho narrativo; nenhuma regra é aplicada automaticamente (o Mestre define o poder).
- [ ] **Facção inferida pelo nome da pasta:** pastas com nomes fora das palavras-chave (pirata, marinha, monstro/fera, governo) caem em "outros" e usam só o loot base.
- [ ] **Campos "Jogadores" e "Nível médio":** são de sessão e não são salvos no cofre; se quiser persistir, criar coluna/tabela de configuração.
- [ ] **Debounce de 40 ms:** cada tecla ainda agenda/atualiza depois do intervalo; se surgir travamento em máquinas lentas, aumentar o intervalo.
- [ ] **Entrada de Nível aceita texto:** `_nivel_texto` sanitiza ao salvar, mas o campo continua livre; validar com `validatecommand` seria mais rígido.

### 4.4 Correções de 22/10/2026 (auditoria)

- [x] Log limitado a 500 linhas no widget.
- [x] Dano no Tracker usa o PV máximo atualizado (fim da corrida do debounce).
- [x] combate.py e historia.py tolerantes a texto no lugar de números.
- [x] Tracker atualiza linha única em dano/cura/condições.
- [x] sync_nome_ficha usa mapa id → índices.
- [x] Tema preserva a aba selecionada.
- [x] Duplicata de ficha real não infla a dificuldade.
- [x] HabilidadeBloco com toggle por estado e resize estável.
- [x] Arrastar em grupo move todas as fichas selecionadas.
- [ ] Troca de tema ainda recria as abas (perde scroll dentro da ficha); resolver com registro de widgets por papel de cor.
- [ ] Cores fixas continuam espalhadas (73 em app_main.py e 35 em ficha_frame.py); criar papéis semânticos no config.py.
- [ ] PATAMARES duplicados entre utils/golpes.py e ficha_frame.inserir_habilidade; unificar em uma fonte.
- [ ] utils/sons.py e a pasta sons/ seguem sem uso (soundboard removido da UI).

### 4.5 Limpeza de 22/10/2026

- [x] Paleta semântica em `core/paleta.py`; literais de cor eliminados da UI.
- [x] Troca de tema ao vivo sem recriar abas (repintura por mapa de cores).
- [x] Troca de fonte ao vivo sem recriar abas.
- [x] `accent_hover` por tema.
- [x] PATAMARES unificados em `utils/golpes.py`.
- [x] `utils/sons.py` e `sons/` removidos.
- [ ] Repintura por mapa depende de o valor atual bater com a paleta antiga; widgets com cor fora da paleta (ex.: `"white"`) não mudam por design.
- [ ] `HabilidadeBloco` recriado dentro de uma aba já aberta nasce com o tema atual (correto), mas blocos com cores personalizadas no futuro precisariam de registro.
- [ ] Tema/fonte continuam sem persistência entre sessões: ao abrir o app volta para Obsidian/Segoe UI.

### 4.6 Ganhos rápidos e preparação (22/10/2026)

- [x] Salvamento automático (3 min) + backup rotativo `.db.bak`.
- [x] Ctrl+Z para PV e condições no Tracker.
- [x] "Jogadores" e "Nível médio" persistidos no cofre.
- [x] Ctrl+K abrindo ficha por nome.
- [x] Gerador de encontros balanceado (com criação das fichas).
- [x] Bestiário (Capanga/Elite/Chefe por Nível).
- [x] Editor de habilidade com prévia de PE e validação do limite.
- [x] Importação em lote JSON/CSV com validação.
- [x] Tema automático por facção.
- [x] Suíte de 25 testes automatizados.
- [ ] Autosave salva sempre, mesmo sem mudanças; um controle de "sujo" evitaria gravações desnecessárias.
- [ ] Desfazer cobre só PV e condições; renomear/excluir/arrastar continuam sem undo.
- [ ] Tema por facção sobrescreve a escolha manual sempre que uma ficha é aberta; avaliar um botão "fixar tema".
- [ ] Importação em lote assume CSV com cabeçalho `nome`; documentar as colunas aceitas para o Mestre.
- [ ] `modo campanha` (sessões/XP) continua fora do escopo.

### 4.7 Correções de UX (22/10/2026)

- [x] Tema por facção deixou de ser automático; agora é ação manual no menu de contexto.
- [x] Seletor de arquétipo com botões segmentados e descrição.
- [x] Exclusão de habilidade funcionando (callback em vez de `<Destroy>`).
- [x] Cabeçalho do bloco de habilidade em duas linhas (botões nunca somem).
- [x] Campo de Potencialização (+PE) renomeado e com prévia clara.
- [x] Escolha manual do patamar na geração de golpe.
- [x] Encontros em pasta própria com subpastas Chefes/Lacaios.
- [ ] A potencialização registrada no bloco ainda não é descontada automaticamente do PE no combate; hoje é informativa.
- [ ] O tema por facção manual não fica salvo por pasta; se quiser, guardar a preferência no cofre.
- [ ] Nomes padrão do encontro ("Chefe (Nv X)") podem ser editados depois; não há campo de nome no gerador.

### 4.8 Ajustes de 22/10/2026 (recompensa, graus, PV/PE e cache)

- [x] Recompensa não reformata mais durante a digitação.
- [x] Graus de Luta/Acrobacia aceitam -1 a 4 (UI, regras e importação).
- [x] PV Máx e PE Máx podem ser digitados; a diferença vira bônus no mod.
- [x] Abas fechadas ficam em cache (até 4) e reabrem ~6,8× mais rápido.
- [ ] Graus -1 e 4 estão fora da tabela oficial 0..3 do livro: é uma decisão da mesa, registrada aqui.
- [ ] PV/PE máximo digitado pode gerar bônus negativo (máximo abaixo do cálculo). O sistema aceita, mas o livro não prevê isso; usar com consciência.
- [ ] O cache reaproveita a ficha fechada e sincroniza só nome/Nível/PV/PE; mudanças externas em História/Habilidades exigiriam reabrir pela árvore e recarregar.
- [ ] Imagens ficam em memória por caminho; se o arquivo mudar no disco, o cache continua com a versão antiga até reiniciar.

### 4.9 Desafio por dano e Tracker (22/10/2026)

- [x] Cálculo de desafio por dano médio da party (rodadas + classes Muito Fácil/Desafiador/Mortal).
- [x] Jogadores não contam no desafio (pastas Player/Jogadores/Party/Grupo/Aliados).
- [x] Calculadora de Dano no menu Ferramentas.
- [x] Mensagem de salvo manual + status discreto (salvo/auto).
- [x] Bando com ✖ por membro e duplo clique para abrir a ficha.
- [x] Delete remove linha do Combat Tracker.
- [ ] O desafio por HP só funciona para inimigos com ficha vinculada; lacaios genéricos caem no cálculo antigo por Nível e aparecem como "(sem HP)".
- [ ] Pastas de jogadores fora dos nomes reconhecidos contam como inimigos; basta renomear para Player/Jogadores.
- [ ] Delete no Tracker não tem Ctrl+Z (o desfazer atual cobre PV e condições).
- [ ] A calculadora de dano é uma janela de consulta; não salva o cálculo no cofre.
- [ ] O cálculo usa o HP máximo, não o HP atual (mede o encontro cheio).

### 5.0 Auditoria — estado (22/10/2026)

- [x] A1 — Tracker sem participantes duplicados.
- [x] A3 — Fallback da dificuldade sem regra de três antiga.
- [x] M3/M4 — Testes da rolagem + injeção de RNG no dano.
- [x] B1 — Efeito visual do CustomTkinter movido para `main.py`.
- [x] B2 — Leitura SQLite com `PRAGMA table_info`.
- [ ] A2 — Gerador de encontros ainda usa a regra de três antiga (depende de uma tabela de HP por Nível, a confirmar).
- [ ] C1 — Fórmula de PV: confirmar a versão oficial antes de mudar.
- [ ] C2 — Fórmula de CD: confirmar (automática vs manual).
- [ ] M1 — Graus −1..4 vs oficial 0..3: decisão pendente.
- [ ] M2 — Iniciativa 1d20+Agi: documentar como ferramenta opcional.
- [ ] B3 — Backup `.db.bak` único (sem histórico rotativo).

### 5.1 Auditoria — rodada 2 (22/10/2026)

- [x] B3 — Backup rotativo `.db.bak` + `.bak.1` + `.bak.2`.
- [x] Anti-lock defensivo (`busy_timeout`) na persistência.
- [x] M2 — Iniciativa documentada como conveniência de mesa.
- [x] Evidência de que a UI não embute fórmulas de regra.
- [ ] A2 — Gerador de encontros: aguarda tabela de HP por Nível (ou decisão do Mestre).
- [ ] C1 — Fórmula de PV: confirmar a versão oficial.
- [ ] C2 — Fórmula de CD: confirmar (automática vs manual).
- [ ] M1 — Graus −1..4 vs oficial 0..3: decisão pendente.

### 5.2 Fases 3 e 10.4 concluídas (22/10/2026)

- [x] C1 — PV = PV de Raça + Nível×Físico + 5×(Nível−1); campo PV Raça (padrão 12).
- [x] C2 — CD manual (campo CD), com fallback automático só para fichas antigas.
- [x] M1 — Graus de Perícia 0..3 (UI, regras e importação).
- [x] A2 — Gerador de Encontros por HP/rodadas; `core.combate` marcado como legado.
- [x] Migração de fichas antigas preserva PV e CD.
- [ ] O PV de Raça padrão 12 é uma compatibilidade (Base Humana); raças específicas ainda não têm valor próprio.
- [ ] O Gerador estima o PV pelos arquétipos e pela fórmula; os lacaios criados variam ±1 Atributo, então o HP real pode diferir um pouco do previsto.
- [ ] `core.combate` continua no repositório apenas para compatibilidade/testes.

### 5.3 Ajustes de mesa (22/10/2026)

- [x] PV voltou à fórmula anterior; CD automática com bônus (+CD).
- [x] Ficha indica PV/PE **atual** e **máx**.
- [x] Bando compartilhado entre todas as fichas, salvo no cofre.
- [x] "Bestiário" renomeado para **Gerar Inimigo** (Nível + Classe).
- [x] Condições com duração em turnos **ou** minutos (1 min = 10 turnos).
- [x] Removido o destaque colorido do turno no Tracker (só a flecha ▶).
- [ ] Bandos antigos são mesclados ao carregar; nomes repetidos não duplicam.
- [ ] O inimigo gerado usa os arquétipos existentes (Atirador pode ter Físico 0 em Níveis baixos).

### 5.4 Layout de PV/PE (22/10/2026)

- [x] PV/PE em uma única Label `atual / máx`, com − e + agrupados.
- [x] Removidas as caixas de edição soltas do cabeçalho.
- [x] Label sincronizada com dano/cura do Tracker.
- [ ] PV/PE atual e máximo não são mais digitáveis no cabeçalho (máximo pelos contadores +PV Máx/+PE Máx; atual pelos botões ou Tracker).

