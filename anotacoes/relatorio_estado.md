# Relatório de Estado – One Piece RPG (Livro de Regras)

**Data:** 13/10/2026  
**Documento analisado:** `livros/Livro Teste Para IA.pdf` (147 páginas)  
**Textos extraídos:** `texto/sistema_novo_p1-67.txt` e `texto/livro_antigo_p68-fim.txt`

---

## 1. O que entendi do sistema novo (Visão Geral)

O sistema novo adota uma mecânica elegante focada em d20 e graus de especialização:
- **Testes:** Rola-se uma quantidade de d20 definida pelo grau da Perícia e escolhe-se o maior dado rolado, somando o valor fixo do Atributo correspondente (fórmula: `Maior d20 + Atributo`). O resultado é comparado à CD (de 5 a 25) ou ao teste do adversário em Disputas.
- **Graus de Perícia:** São 4 graus: Grau 0 Leigo (1d20), Grau 1 Treinado (2d20), Grau 2 Especialista (3d20) e Grau 3 Mestre (4d20). Não há bônus numérico somado pelo grau.
- **Atributos:** Físico, Agilidade, Intelecto e Instinto. No Nível 1 são distribuídos 1, 1, 1 e 0 (mais bônus da Origem), com teto máximo de 5. Atributo 0 soma +0.
- **Vantagem e Desvantagem:** Vantagem concede +1d20 na rolagem; Desvantagem reduz 1d20. Se os dados caírem para 0 ou menos, rolam-se 2d20 e usa-se o menor. Não existem mais "Bônus de Treinamento" nem "Bônus de Nível".
- **Defesas:** Defesa Passiva (10 + Agilidade + Equipamentos), Bloqueio (10 + Físico + 2×Luta) e Esquiva (10 + Agilidade + 2×Acrobacia). Bloqueio e Esquiva custam a Reação do personagem.
- **Recursos:** Pontos de Esforço (PE Máximo = `4 + Nível + Maior Atributo`), usados para técnicas e potencializações. Pontos de Vida (PV) no nível 1 iniciam com a base da Raça + Físico.
- **Evolução:** A cada nível a partir do 2, escolhe-se exatamente 1 benefício: uma nova Habilidade OU subir 1 grau de Perícia (o grau Mestre exige treinamento com mentor ou momento crítico narrativo).

---

## 2. Divergências entre o PDF atual e as Decisões do AGENTS.md

Abaixo estão as inconsistências encontradas no texto atual do PDF (páginas 1 a 67) em relação ao que já foi consolidado como regra no `AGENTS.md`:

| Item | Texto no PDF Atual | Regra Decidida no `AGENTS.md` | Página no PDF |
| :--- | :--- | :--- | :--- |
| **Fórmula de Bloqueio** | `Bloqueio = 10 + Físico x Grau da Perícia Luta (0 a 3)` | `Bloqueio = 10 + Físico + (2 × grau da Luta)` | p. 22 e p. 39 |
| **Fórmula de Esquiva** | `Esquiva = 10 + Agilidade x Grau da Perícia Acrobacia (0 a 3)` | `Esquiva = 10 + Agilidade + (2 × grau da Acrobacia)` | p. 22 e p. 39 |
| **Resquício de Bônus de Treinamento** | Raça Polvo (Tinta): *"Essa característica tem um uso igual a seu Bônus de Treinamento e recupera com descanso total."* | Bônus de Treinamento foi extinto. O número de usos deve ser baseado em Atributo ou valor fixo. | p. 56 |
| **Tabela de Graus de Perícia** | Tabela listada com sinais de adição: `+0 (Leigo): 1d20`, `+1 (Treinado): 2d20`, `+2 (Especialista): 3d20`, `+3 (Mestre): 4d20`. | O correto é `Grau 0 (Leigo)`, `Grau 1 (Treinado)`, `Grau 2 (Especialista)` e `Grau 3 (Mestre)`. Não há bônus somado. | p. 13 |
| **Pontuação na Evolução** | *"A cada nível a partir do 2, o jogador escolhe uma destas opções"* (falta o caractere `:`). | Adicionar `:` ao final da frase antes dos marcadores. | p. 38 |
| **Resquício de "Dado de Vida"** | Raça Autômato: *"Você não recebe o dado de vida."* | Dado de vida pertencia ao sistema antigo e não existe mais. | p. 65 |
| **Recuperação de PV no Descanso** | Descanso Total cita recuperação de PV conforme regras, mas a fórmula de PV por nível ainda não está no livro. | Necessita confirmar e inserir a fórmula oficial de PV por nível e recuperação. | p. 36 e p. 39 |
| **Vantagens Permanentes em Origens e Raças** | O PDF concede "Vantagem em Testes de [Perícia]" em dezenas de traços permanentes. | Traços permanentes devem conceder bônus fixo de **+2** (e desvantagens **−2**). | p. 41 a 65 |

---

## 3. Contagem de Vantagens Permanentes em Origens e Raças (Páginas 40 a 67)

No sistema novo, "Vantagem" (+1 dado) foi reservada para circunstâncias dinâmicas e situacionais. Traços permanentes devem conceder **+2 fixo**.

Na análise automatizada do texto extraído, identificamos **40 ocorrências de características concedendo Vantagem em testes**:

### Origens (Páginas 41 a 47) – 17 características:
1. **Bêbado** (p. 41): *Estou de Boa* (Testes de Resistência contra álcool)
2. **Caçador** (p. 41): *Olho de Coletor* (Testes para encontrar ingredientes)
3. **Caçador de Tesouros** (p. 41): *Olho para o Valor* (Testes para valor/autenticidade)
4. **Caçador de Recompensas** (p. 42): *Rastreador Experiente* (Testes de Sobrevivência para rastrear)
5. **Carpinteiro** (p. 42): *Mestre Naval* (Testes de Ofício Carpintaria em navios)
6. **Cobaia de Laboratório** (p. 43): *Autossuficiente* (Testes de Resistência contra venenos/doenças)
7. **Diplomata** (p. 44): *Conhecimento Militar* (Testes de Cultura e testes sociais com Governo Mundial)
8. **Comerciante** (p. 44): *Barganha* (Testes de Persuasão para negociação)
9. **Ladrão** (p. 44): *Mãos Rápidas* (Testes de Prestidigitação para bater carteira/fechaduras)
10. **Médico** (p. 45): *Diagnóstico Rápido* (Testes de Medicina para estabilização/diagnóstico)
11. **Mentiroso** (p. 45): *Mentira Convincente* (Testes de Enganação)
12. **Músico** (p. 45): *Cativar Audiência* (Testes sociais contra audiência após apresentação)
13. **Navegador** (p. 45): *Sentido Climático* (Testes de Cultura/Sobrevivência de clima/mar)
14. **Pirata Veterano** (p. 46): *Histórias de Taverna* (Testes de Performance em tavernas)
15. **Sábio** (p. 46): *Experiência* (Testes de Cultura)
16. **Revolucionário** (p. 46): *Identidade Secreta* (Testes de Enganação para disfarce)
17. **Sobrevivente** (p. 47): *Instinto de Sobrevivência* (Testes para resistir a Amedrontado)

### Raças (Páginas 48 a 67) – 23 características:
18. **Anão** (p. 48): *Conhecimento da Natureza* (Testes relacionados à natureza)
19. **Humano Comum / Linhagem** (p. 49): *Força Bruta* (Testes de Atletismo com Físico)
20. **Humano Ciborgue** (p. 51): *Conhecimento Venenoso* (Testes de Resistência contra Envenenado)
21. **Kuja** (p. 52): *Selvagens* (Testes de Sobrevivência e Intimidação)
22. **Kuja** (p. 53): *Domadores* (Testes ao lidar com animais)
23. **Homem-Peixe Moreia** (p. 54): *Constritor* (Testes para agarrar/manter agarrado)
24. **Homem-Peixe Sapo** (p. 54): *Super Pulo* (Testes de Atletismo/Acrobacia para saltos)
25. **Homem-Peixe Comum** (p. 55): *Filhos do Mar* (Testes de Atletismo/Acrobacia submerso)
26. **Homem-Peixe Polvo** (p. 56): *Camuflagem* (Testes de Furtividade)
27. **Homem-Peixe Tubarão-Branco** (p. 56): *Intimidação* (Testes de Intimidação)
28. **Homem-Peixe Tubarão-Branco** (p. 56): *Percepção de Topo de Cadeia* (Testes de Percepção submerso)
29. **Mink Coelho** (p. 57): *Saltoelho* (Testes de Atletismo)
30. **Mink Lobo/Cão** (p. 57): *Sentidos Mais que Apurados* (Testes de Percepção e Iniciativa)
31. **Mink Bode/Carneiro** (p. 57): *Equilíbrio Caprino* (Testes de Acrobacia para equilíbrio)
32. **Mink Gato** (p. 58): *Mestre da Agilidade* (Testes de Acrobacia)
33. **Mink Touro** (p. 59): *Investida/Força* (Testes de Atletismo após uso)
34. **Skypiean** (p. 61): *Povo do Céu* (Testes para uso/funcionamento de Dials)
35. **Skypiean** (p. 61): *Habitante das Nuvens* (Testes de Acrobacia para equilíbrio)
36. **Tribo dos Três Olhos** (p. 63): *Olhar Penetrante* (Testes para perceber ilusões/disfarces)
37. **Tribo do Pescoço de Cobra** (p. 63): *Pescoço Extensível* (Testes de Percepção)
38. **Sereiano Comum** (p. 65): *Nadador Excepcional* (Testes de natação e movimento aquático)
39. **Sereiano Comum** (p. 65): *Nadador Excepcional* (Testes para escapar de agarrões na água)
40. **Mestiço** (p. 67): Herança de características que contenham Vantagem conforme as raças de origem.

---

## 4. Pendências do Projeto

### (a) Mecânicas já decididas e ainda não aplicadas no texto
- Atualizar a redação das fórmulas de Defesa nas páginas 22 e 39 para a soma com o dobro do grau (`+ 2 × grau`).
- Converter todas as 40 características de Origens e Raças de "Vantagem em Testes" para bônus fixo de **+2** (e desvantagens permanentes para **−2**).
- Substituir a menção de "Bônus de Treinamento" na característica *Tinta* do Polvo (p. 56).
- Corrigir a notação da tabela de graus na p. 13 (`Grau 0` a `Grau 3`).
- Remover a frase "Você não recebe o dado de vida" da p. 65 (Autômato).
- Inserir os dois pontos `:` na evolução por nível da p. 38.

### (b) Decisões que dependem de confirmação do autor
- **Pontos de Vida (PV):** Confirmar a proposta de cálculo de PV por nível (`PV da Raça + (Nível × Físico) + 5 × (Nível − 1)`) e a recuperação no Descanso Total.
- **Limite de Vantagens e Acúmulos:** Oficializar o limite de saldo de Vantagens/Desvantagens em ±2 dados e a regra de que bônus de Origem e Raça na mesma perícia não se acumulam (vale o maior).
- **Progressão de Atributos:** Definir se haverá ganho de atributos por nível (+1 ponto a cada 3 níveis, máximo 5).
- **Estrutura das Habilidades:** Aprovar a divisão em 4 patamares (Básica, Média nível 4+, Forte nível 8+, Suprema nível 12+) e o escalonamento de dados de dano.
- **Haki e Akuma no Mi:** Confirmar requisitos de nível (Haki nos níveis 8 e 14) e se o ganho consome uma escolha de nível.
- **Termos Citados sem Regras Definidas:** Pontos de Influência (PI), Alinhamento, Dials, Estilos de Combate e Cicatriz Permanente.

### (c) Livro antigo ainda não convertido (Páginas 68 a 147)
- **Equipamentos e Armas (p. 68-70):** Ainda usam a lógica antiga.
- **Regras de Evolução Antiga (p. 71-72):** Mecânica de Fragmentos de Sonho e Ameaça.
- **Árvore de Habilidades e Estilos (p. 73-118):** Mais de 45 páginas de técnicas de combate (Espadachim, Karatê Homem-Peixe, Perna Negra, Ciborgue, Músico, etc.) cheias de referências a "Bônus de Treinamento", modificadores antigos e dados de vida.
- **Haki (p. 119-122):** Descrições e regras no sistema antigo.
- **Akuma no Mi (p. 123-130):** Regras de frutas do diabo no sistema antigo.
- **Itens e Navegação (p. 131-144):** Regras de navios, itens e navegação.

---

## 5. Próximo Passo Recomendado

Recomendo iniciarmos pela **correção das fórmulas de Defesa e conversão das Vantagens de Origens (páginas 41 a 47) para o bônus fixo de +2**, entregando os textos prontos em **lotes de 5 origens**.  
Essa é uma mecânica já decidida e 100% clara, que deixará a primeira metade das regras do livro nova, coesa e pronta para ser copiada e colada.
