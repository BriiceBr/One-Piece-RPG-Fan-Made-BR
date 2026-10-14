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
