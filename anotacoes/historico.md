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
