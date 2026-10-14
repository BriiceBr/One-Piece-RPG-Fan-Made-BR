# AGENTS.md – Projeto: RPG de mesa de One Piece (livro de regras)

Este arquivo contém as instruções permanentes do projeto. Leia-o por inteiro antes de qualquer tarefa.

## 1. O que é este projeto

Estou escrevendo (há 2 anos) e agora **recriando** o livro de regras de um RPG de mesa de **One Piece**, fã-made e em **português do Brasil**. O livro está em PDF. O sistema foi redesenhado; parte do livro já está no sistema novo e parte ainda está no sistema antigo.

## 2. Como você deve trabalhar comigo

- Sou **iniciante no Antigravity** e não programo. Explique tudo em **português simples**, passo a passo, sem jargão.
- Responda sempre em **português do Brasil**.
- **Nunca altere o PDF original.** Trabalhe em cópias de texto na pasta `texto/`.
- **Antes de criar, editar ou apagar qualquer arquivo, diga o que vai fazer e peça minha confirmação.** Exceção: pode criar arquivos novos em `texto/` e `anotacoes/` sem pedir.
- Quando eu pedir mudanças no livro, entregue **texto pronto para copiar e colar**, no estilo do livro (seção 5), **sem tabelas** (a menos que eu peça) e **em lotes de 5 itens**. Espere eu dizer "próximo lote".
- **Não invente regras.** Se faltar uma decisão minha, pergunte (no máximo 3 perguntas por vez) ou anote em `anotacoes/pendencias.md`.
- Para **probabilidades e balanceamento**, calcule com um script Python (não estime de cabeça) e me mostre um resumo simples dos resultados.
- Quando encontrar algo errado **fora do que pedi**, não corrija. Anote em `anotacoes/pendencias.md` e me avise.
- Se não tiver certeza sobre um trecho do livro, **cite o trecho** em vez de supor.

## 3. Estrutura da pasta

- `livro/` – o PDF do livro (somente leitura).
- `texto/` – texto extraído do PDF (você cria).
- `prompts/` – prompts que já escrevi para outras IAs (somente leitura).
- `anotacoes/` – relatórios, decisões e pendências (você cria e atualiza).
- `rascunhos/` – textos novos prontos para colar no livro (você cria).

## 4. O livro

- Arquivo: `livro/Livro_Teste_Para_IA.pdf` (147 páginas).
- **Páginas 1 a 67 = sistema NOVO:** introdução, testes, combate, condições, descansos e recursos, criação de personagem, Origens (25) e Raças (18, mais Mestiços).
- **Páginas 68 em diante = livro ANTIGO:** equipamentos, regras de evolução, Haki, habilidades e outras regras. Ainda usam o sistema antigo (Bônus de Treinamento, Xd20 por Atributo, dado de vida etc.) e **ainda não foram convertidas**.
- O PDF tem **duas colunas** e a extração de texto pode vir embaralhada. Reconstrua a ordem correta de leitura e avise se tiver dúvida.
- Cada vez que eu enviar uma versão nova do PDF, compare com a anterior e me diga o que mudou.

## 5. Estilo e formatação do livro (siga ao escrever textos)

- Os capítulos principais são numerados (ex.: "5. Criação de Personagem"). Dentro deles, as seções têm títulos simples, sem número.
- Termos de jogo com inicial maiúscula: Atributo, Perícia, Teste, Ação, Ação Extra, Reação, Movimento, Habilidade, Condição, Nível, CD, Disputa, Vantagem, Desvantagem, Descanso Parcial, Descanso Total.
- Listas com marcador "•". Falas de exemplo entre aspas, com traço "-".
- Exemplos com o rótulo **"Exemplo:"**, uma situação curta e a rolagem passo a passo em marcadores ("• Ele rola: ...", "• Os resultados são: ...", "• O resultado final do Teste é: ..."). Avisos com **"Importante:"**.
- Frases curtas e diretas; terceira pessoa ("o personagem") nas regras e "você" nas características de Origens e Raças.
- **Todo exemplo numérico deve ter a conta certa.** Refaça as contas.
- O livro já usa "o Mestre" para o **narrador**. Quando eu falar do **grau** de Perícia mais alto, escreva sempre **"grau Mestre"**.

## 6. Regras do sistema NOVO (decisões já tomadas)

**Testes**
- Resultado = o **maior dos d20 da Perícia + Atributo**. A combinação "Atributo + Perícia" é escolhida pela abordagem (ex.: Instinto + Sobrevivência). Ao ser bem-sucedida, a CD é comparada ao resultado.
- Graus de Perícia: Grau 0 Leigo (1d20), Grau 1 Treinado (2d20), Grau 2 Especialista (3d20), Grau 3 Mestre (4d20, **sem bônus fixo extra**). Todas as Perícias começam em Leigo. O livro tem 20 Perícias.
- Atributos: Físico, Agilidade, Intelecto, Instinto. Nível 1: distribuir 1, 1, 1 e 0, mais o bônus da Origem. **Máximo 5.** O Atributo é um **bônus fixo** (Atributo 0 soma 0, sem penalidade).
- **Vantagem = +1 dado** nos dados da Perícia; **Desvantagem = −1 dado.** Se o total chegar a 0 ou menos, rola 2d20 e usa o **menor**.
- **O Bônus de Treinamento e o Bônus de Nível não existem mais.** Qualquer menção restante é erro.

**Origens e Raças**
- Características permanentes que davam "Vantagem em Testes de X" viram **bônus fixo de +2** em Testes de X (mantendo condições). Desvantagem permanente em Testes vira **−2**. Em andamento: ver `prompts/prompt_vantagens_origens_racas.md`.

**Defesa (decidido; verifique se o PDF já reflete)**
- Defesa Passiva = 10 + Agilidade + Equipamentos.
- Bloqueio = 10 + Físico + (2 × grau da Luta).
- Esquiva = 10 + Agilidade + (2 × grau da Acrobacia).
- Os valores 0/2/4/6 mantêm o acerto em cerca de 70% entre personagens do mesmo patamar. **Cuidado:** o PDF já esteve com "x" (multiplicação) no lugar de "+", o que está errado.

**Recursos e evolução**
- **PE Máximo = 4 + Nível + Maior Atributo.** Não há nível máximo.
- A cada nível a partir do 2, o jogador escolhe **uma** opção: uma **Habilidade nova** ou **+1 grau de uma Perícia**.
- Para chegar ao **grau Mestre** é necessário ser treinado por alguém que já seja grau Mestre naquela Perícia (NPC ou personagem), ou o Mestre (narrador) pode conceder em uma batalha ou momento crítico. A escolha fica reservada até o treino acontecer.
- Estados de Morrendo: Ferimento Letal, Trauma Grave, Nocaute, Por um Fio e Inabalável, conforme o texto atual do livro.

## 7. Propostas ainda NÃO confirmadas (não trate como regra)

- Saldo de Vantagens menos Desvantagens limitado a **±2 dados**; bônus fixos de Origem e Raça na mesma Perícia **não se acumulam** (vale o maior).
- **PV:** PV da Raça + (Nível × Físico) + 5 × (Nível − 1).
- **Atributos:** +1 ponto a cada 3 níveis, máximo 5.
- **Habilidades:** quatro patamares (Básica, Média, Forte, Suprema); Média a partir do nível 4, Forte do 8, Suprema do 12. O dano das habilidades ganha +1 dado nos níveis 5, 11 e 17.
- **Haki:** Armamento e Observação a partir do nível 8, Rei a partir do 14, exigindo mentor ou momento crítico. Cada Haki consome uma escolha de nível.
- **Potencialização com PE:** o PE serve para melhorar habilidades (mais dano, mais CD, mais alcance, mais alvos voluntários). Limite de PE extra por uso: 2 + 1 a cada 4 níveis.
- **Habilidades básicas:** dano de arma (d4 a d12), ajustado por uma tabela (base d8; alcance médio −1, longo −2, vários alvos −2, condição leve −1, condição forte −2, pesada +1 a +2, exige condição do alvo +1). Suprema precisa de limitação extra (Exaustão, Força de Vontade ou uso por Descanso Total).
- **Itens para Mestres:** seção para criar itens com bônus em Perícias. Teto de **+3** no total, um item por Perícia, raridade +1 / +2 / +3.
- **Ataque Extra** com custo de PE crescente ou maior (a definir).
- **Recuperação:** Descanso Parcial recupera metade do PV e do PE máximos; Força de Vontade com 1 ponto no início de cada sessão.
- **Exaustão:** penalidade de −1 por nível em todos os Testes, no lugar de Desvantagem.
- **Níveis:** o sistema de Fragmentos de Sonho e Ameaça do livro antigo continua.

## 8. Pendências conhecidas (verifique no PDF antes de corrigir)

- Fórmulas de Defesa com "x" (p.22 e p.39).
- Raça Polvo, característica Tinta (p.56): cita "Bônus de Treinamento".
- Tabela de graus (p.13) escrita como "+0 (Leigo)... +3 (Mestre)"; o certo é "Grau 0 (Leigo)...".
- Falta o ":" em "escolhe uma destas opções" (p.38).
- Autômato (p.65): "Você não recebe o dado de vida".
- Descanso Total diz "recupera os Pontos de Vida conforme as...", mas a regra de PV não existe.
- Cerca de 40 Vantagens permanentes em Origens e Raças (p.41 a 65) ainda a converter.
- Tabela de Tamanho com faixas de altura que não batem com as Raças.
- Coisas citadas e ainda não definidas: Pontos de Influência, Alinhamento, Akuma no Mi, Dials, Estilo de Combate, Cicatriz Permanente.
- Toda a parte antiga (p.68+) precisa ser convertida ao sistema novo.

## 9. Fluxo de trabalho padrão

1. Ler este arquivo e `anotacoes/pendencias.md`.
2. Extrair o texto do PDF para `texto/` quando necessário.
3. Para cada tarefa: dizer o que vai fazer, fazer, entregar o texto pronto em `rascunhos/` e resumir no chat.
4. Registrar o que mudou em `anotacoes/historico.md` (data, o que mudou, em quais páginas).
5. Terminar sempre dizendo qual é o **próximo passo recomendado**.
