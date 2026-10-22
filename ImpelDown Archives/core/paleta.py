"""Paleta semântica do ImpelDown Archives.

Cores com significado fixo, independentes do tema escolhido. Tudo que é
"perigo", "aviso", "sucesso" ou "texto suave" deve vir daqui em vez de um
literal hexadecimal espalhado pelo código.
"""

from __future__ import annotations

#: Texto secundário (rótulos, legendas, dicas).
TEXTO_SUAVE = "#8b8c8f"
#: Valor de PE e informações neutras.
INFO = "#56b6c2"
#: Destaques de defesa/CD e recompensa.
DESTAQUE = "#e5c07b"
#: Erros, dano, inimigo caído.
PERIGO = "#e06c75"
#: Texto de perigo sobre fundo destacado.
PERIGO_CLARO = "#ffb3b3"
#: Atenção, condições, avisos.
AVISO = "#e5b55e"
#: cura, sucesso, PV saudável.
SUCESSO = "#6db35f"
#: Hover neutro dos botões.
HOVER = "#4a4a4a"
#: Alça de redimensionamento dos blocos de habilidade.
ALCA = "#3a3a3a"
#: Legenda flutuante (contraste fixo sobre qualquer tema).
TOOLTIP_FUNDO = "#2b2b2b"
TOOLTIP_TEXTO = "#ffffff"

#: Botões de perigo (Dano, Deletar).
BOTAO_PERIGO = "#5c2b29"
BOTAO_PERIGO_HOVER = "#7a3a37"
BOTAO_PERIGO_TEXTO = "#ffdede"

#: Botões de sucesso (Cura).
BOTAO_SUCESSO = "#2f4a2f"
BOTAO_SUCESSO_HOVER = "#3d5f3d"
BOTAO_SUCESSO_TEXTO = "#e6ffe6"

#: Dificuldade do encontro.
DIFICULDADE_FACIL = "#6db35f"
DIFICULDADE_MEDIA = "#e5b55e"
DIFICULDADE_DIFICIL = "#e05353"
DIFICULDADE_MORTAL = "#a82020"
DIFICULDADE_SEM_INIMIGOS = "#8b8c8f"
