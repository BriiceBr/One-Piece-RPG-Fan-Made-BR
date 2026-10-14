# Proposta de Balanceamento: Sistema de PE e Transmutações

Este documento registra o modelo matemático de economia de Pontos de Esforço (PE), custos por patamar de habilidade e opções de transmutação (potencialização).

---

## 1. Capacidade Máxima de PE

A fórmula base oficial é:
$$\text{PE Máximo} = 4 + \text{Nível} + \text{Maior Atributo}$$

### Progressão de PE ao longo dos Níveis:
- **Nível 1** (Atributo 2): **7 PE** (Recupera 3 no Descanso Parcial)
- **Nível 4** (Atributo 3): **11 PE** (Recupera 5 no Descanso Parcial)
- **Nível 8** (Atributo 4): **16 PE** (Recupera 8 no Descanso Parcial)
- **Nível 12** (Atributo 5): **21 PE** (Recupera 10 no Descanso Parcial)
- **Nível 16** (Atributo 5): **25 PE** (Recupera 12 no Descanso Parcial)
- **Nível 20** (Atributo 5): **29 a 31 PE** (Recupera 14 a 15 no Descanso Parcial)

> **Conclusão Matemática:** Ter cerca de 31 PE no Nível 20 é o valor ideal. Em combates de alto nível (4 a 6 turnos contra chefes e Yonkous), um personagem gasta facilmente entre 15 e 25 PE transmutando suas técnicas, ficando com uma margem segura sem esgotar seus poderes imediatamente no primeiro turno.

---

## 2. Custos Base por Patamar de Habilidade

| Patamar | Custo Base | Nível Mínimo | Descrição e Efeito Típico |
| :--- | :---: | :---: | :--- |
| **Básica** | **0 PE** | Nível 1 | Golpe de arma ou desarmado padrão, com efeito temático ou cosmético. Pode ser usado livremente a cada turno. |
| **Média** | **1 PE** | Nível 4 | Golpe aprimorado (2 dados de dano + atributo) ou com utilidade tática (empurrar, desarmar, alcance curto). |
| **Forte** | **3 PE** | Nível 8 | Golpe de impacto pesado (4 dados de dano + atributo), efeito em área moderada ou condição negativa importante. |
| **Suprema** | **5 PE** | Nível 12 | O golpe definitivo do personagem (6 dados de dano + atributo, área grande ou efeito de finalização). |

---

## 3. Tabela de Transmutações (Melhorias com PE)

Ao declarar o uso de uma Habilidade, o personagem pode gastar PE adicional para "transmutar" suas propriedades:

| Transmutação | Custo Adicional | Efeito |
| :--- | :---: | :--- |
| **Mais Dano** | **+1 PE** por dado | Adiciona +1 dado de dano ao ataque (máximo limitado pelo teto de transmutação). |
| **Mais Alvos** | **+1 PE** por alvo | Atinge 1 alvo extra dentro do mesmo alcance original. |
| **Mais Alcance** | **+1 PE** por passo | Aumenta o alcance em um estágio (ex.: Toque $\rightarrow$ 6m $\rightarrow$ 12m $\rightarrow$ 24m). |
| **Converter para Área** | **+2 PE** | Transforma um ataque de alvo único em uma explosão de 3m de raio ou cone de 4,5m. |
| **Aumentar CD** | **+1 PE** por +1 na CD | Dificulta o teste de resistência da vítima em +1 contra os efeitos da técnica. |
| **Condição Leve** | **+1 PE** | Adiciona uma condição situacional (ex.: Derrubado/Caído, Empurrado 3m, Desorientado). |
| **Condição Severa** | **+2 PE** | Adiciona uma condição debilitante forte (ex.: Amedrontado, Envenenado, Paralisado por 1 turno). |

---

## 4. Limite Fixo de Transmutação por Patamar

Em vez de fórmulas matemáticas durante o combate, cada patamar de habilidade já possui o seu **limite fixo de PE extra** que o jogador pode investir. Isso torna a consulta imediata na ficha:

| Patamar | Custo Base | Limite de PE Extra (Transmutação) | Custo Total Máximo do Golpe |
| :--- | :---: | :---: | :---: |
| **Básica** | **0 PE** | até **+2 PE** | **2 PE** |
| **Média** | **1 PE** | até **+3 PE** | **4 PE** |
| **Forte** | **3 PE** | até **+4 PE** | **7 PE** |
| **Suprema** | **5 PE** | até **+5 PE** | **10 PE** |

### Exemplo Prático de Aplicação:
Um espadachim decide usar uma habilidade **Forte** (custo base: 3 PE):
- Por ser uma habilidade Forte, a tabela indica que ele pode investir até **+4 PE** extras nela.
- Ele escolhe adicionar +2 dados de dano (+2 PE) e aumentar o alcance para atingir +1 alvo (+1 PE), somando **+3 PE** extras.
- Custo total da ação: 3 (base) + 3 (transmutação) = **6 PE** (dentro do limite permitido de 7 PE).
