"""Cartaz de Procurado (WANTED) no estilo do mangá de One Piece.

Fundo de pergaminho, "WANTED" em serifa, retrato emoldurado em branco,
"DEAD OR ALIVE", nome, recompensa e o selo MARINE. O tema do aplicativo não é
usado de propósito: o cartaz precisa parecer papel, não interface.
"""

from __future__ import annotations

import os
import random
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont

LARGURA, ALTURA = 720, 1060

FONTES_SERIFA = (
    r"C:\Windows\Fonts\georgiab.ttf",
    r"C:\Windows\Fonts\timesbd.ttf",
    r"C:\Windows\Fonts\constanb.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
)
FONTES_TEXTO = (
    r"C:\Windows\Fonts\georgia.ttf",
    r"C:\Windows\Fonts\times.ttf",
    r"C:\Windows\Fonts\arial.ttf",
)

PERGAMINHO = (232, 220, 192)
PERGAMINHO_ESCURO = (205, 190, 158)
TINTA = (28, 24, 20)
TINTA_SUAVE = (70, 60, 48)


def _fonte(candidatas: tuple[str, ...], tamanho: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for caminho in candidatas:
        if os.path.exists(caminho):
            try:
                return ImageFont.truetype(caminho, tamanho)
            except OSError:
                continue
    return ImageFont.load_default()


def _texto_recompensa(valor: str | int) -> str:
    digitos = re.sub(r"\D", "", str(valor))
    if not digitos:
        return "SEM RECOMPENSA"
    return f"B$ {int(digitos):,} -".replace(",", ".")


def _fundo_pergaminho() -> Image.Image:
    """Pergaminho com manchas e vinheta, gerado de forma determinística."""
    rng = random.Random(7)
    cartaz = Image.new("RGB", (LARGURA, ALTURA), PERGAMINHO)
    desenho = ImageDraw.Draw(cartaz)

    for _ in range(700):
        x = rng.randint(0, LARGURA)
        y = rng.randint(0, ALTURA)
        raio = rng.randint(1, 6)
        cor = (226, 214, 186) if rng.random() < 0.5 else (238, 230, 208)
        desenho.ellipse([x - raio, y - raio, x + raio, y + raio], fill=cor)

    # Vinheta (bordas mais escuras)
    for i in range(40):
        tom = tuple(int(c * (1 - i * 0.006)) for c in PERGAMINHO_ESCURO)
        desenho.rectangle([i, i, LARGURA - 1 - i, ALTURA - 1 - i], outline=tom)

    # Moldura de tinta
    desenho.rectangle([14, 14, LARGURA - 15, ALTURA - 15], outline=TINTA_SUAVE, width=3)
    desenho.rectangle([26, 26, LARGURA - 27, ALTURA - 27], outline=TINTA_SUAVE, width=1)
    return cartaz


def gerar_cartaz_png(
    dados: dict[str, Any],
    caminho: str,
    tema: dict[str, str] | None = None,
    imagem: Image.Image | None = None,
) -> str:
    """Desenha o cartaz no estilo One Piece e grava em ``caminho``."""
    cartaz = _fundo_pergaminho()
    desenho = ImageDraw.Draw(cartaz)

    fonte_wanted = _fonte(FONTES_SERIFA, 150)
    fonte_selo = _fonte(FONTES_SERIFA, 44)
    fonte_nome = _fonte(FONTES_SERIFA, 58)
    fonte_premio = _fonte(FONTES_SERIFA, 50)
    fonte_marinha = _fonte(FONTES_SERIFA, 34)
    fonte_miuda = _fonte(FONTES_TEXTO, 13)

    centro = LARGURA // 2

    # WANTED (dimensiona a fonte para caber na largura do cartaz)
    tamanho_wanted = 150
    fonte_wanted = _fonte(FONTES_SERIFA, tamanho_wanted)
    while desenho.textlength("WANTED", font=fonte_wanted) > LARGURA - 90 and tamanho_wanted > 48:
        tamanho_wanted -= 6
        fonte_wanted = _fonte(FONTES_SERIFA, tamanho_wanted)
    desenho.text((centro, 110), "WANTED", font=fonte_wanted, fill=TINTA, anchor="mm")

    # Retrato emoldurado em branco
    moldura = [70, 200, LARGURA - 70, 690]
    desenho.rectangle(moldura, fill=(250, 247, 238), outline=TINTA, width=3)
    area = [moldura[0] + 10, moldura[1] + 10, moldura[2] - 10, moldura[3] - 10]

    if imagem is not None:
        retrato = imagem.convert("RGB")
        largura_area = area[2] - area[0]
        altura_area = area[3] - area[1]
        retrato.thumbnail((largura_area, altura_area), Image.Resampling.LANCZOS)
        x = area[0] + (largura_area - retrato.width) // 2
        y = area[1] + (altura_area - retrato.height) // 2
        cartaz.paste(retrato, (x, y))
    else:
        desenho.rectangle(area, fill=(236, 231, 219))
        desenho.text(((area[0] + area[2]) // 2, (area[1] + area[3]) // 2),
                     "SEM IMAGEM", font=fonte_selo, fill=TINTA_SUAVE, anchor="mm")

    # DEAD OR ALIVE com floreios
    y_selo = 745
    desenho.text((centro, y_selo), "DEAD OR ALIVE", font=fonte_selo, fill=TINTA, anchor="mm")
    desenho.line([70, y_selo, 150, y_selo], fill=TINTA, width=2)
    desenho.line([LARGURA - 150, y_selo, LARGURA - 70, y_selo], fill=TINTA, width=2)

    # Nome
    nome = str(dados.get("nome", "DESCONHECIDO")).strip().upper() or "DESCONHECIDO"
    while desenho.textlength(nome, font=fonte_nome) > LARGURA - 120 and len(nome) > 3:
        fonte_nome = _fonte(FONTES_SERIFA, getattr(fonte_nome, "size", 58) - 3)
    desenho.text((centro, 815), nome, font=fonte_nome, fill=TINTA, anchor="mm")

    # Recompensa
    desenho.text((centro, 890), _texto_recompensa(dados.get("recompensa", "0")),
                 font=fonte_premio, fill=TINTA, anchor="mm")

    # Rodapé: selo MARINE e nota
    desenho.text((LARGURA - 80, 985), "MARINE", font=fonte_marinha, fill=TINTA, anchor="rm")
    desenho.text(
        (70, 985),
        "IMPERIAL MARINE  •  DEPARTAMENTO DE JUSTIÇA  •  NÍVEL "
        f"{dados.get('nivel', 1)}",
        font=fonte_miuda, fill=TINTA_SUAVE, anchor="lm",
    )

    cartaz.save(caminho, "PNG")
    return caminho
