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
- [ ] **Janela do histórico:** abre no canto inferior direito no momento do clique; se a janela principal for movida depois, o log não acompanha. Avaliar reposicionar em `<Configure>`.
- [ ] **Duração padrão das condições:** hoje 3 turnos fixos ao aplicar. Decidir se o padrão deve variar por condição (ex.: Atordoado 1, Envenenado 5) ou se o Mestre define no momento.
- [ ] **Golpes usam a tabela de PE da nota interna:** custos, limites e dados por patamar vêm de `anotacoes/regras_pe_transmutacao.md`, não do PDF. Precisa bater com a versão final do livro.
- [ ] **Cartaz WANTED:** usa fontes do Windows (Arial/Georgia/Segoe UI) com fallback para a fonte padrão do Pillow; em outra máquina pode mudar o desenho. Falta opção de papel "pergaminho" claro.
- [ ] **Atalhos × menus:** `Espaço` e letras são globais; se um dia houver menu aberto, o Tk pode consumir a tecla antes. Testar com menus abertos quando surgir necessidade.
- [ ] **Fluxos de UX:** as propostas de `anotacoes/ux_fluxos.md` (Ctrl+E exportar, Ctrl+L loot, busca global Ctrl+K, modo combate) ainda não foram implementadas.
