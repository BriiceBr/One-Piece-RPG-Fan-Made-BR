"""Cartaz de Procurado (WANTED) gerado a partir da ficha.

O cartaz é montado com Pillow, no tema atual do aplicativo, e salvo em PNG para
ser mostrado na mesa. Se a ficha não tiver imagem, o cartaz sai com um espaço
reservado — nunca dá erro.
"""

from __future__ import annotations

import os
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont

LARGURA, ALTURA = 900, 1200

FONTES_NEGRITO = (
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
)
FONTES_SERIFA = (
    r"C:\Windows\Fonts\georgiab.ttf",
    r"C:\Windows\Fonts\timesbd.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
)


def _fonte(candidatas: tuple[str, ...], tamanho: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Carrega a primeira fonte disponível, com fallback embutido."""
    for caminho in candidatas:
        if os.path.exists(caminho):
            try:
                return ImageFont.truetype(caminho, tamanho)
            except OSError:
                continue
    return ImageFont.load_default()


def _recompensa_texto(valor: str | int) -> str:
    digitos = re.sub(r"\D", "", str(valor))
    if not digitos:
        return "SEM RECOMPENSA"
    return f"B$ {int(digitos):,}".replace(",", ".")


def gerar_cartaz_png(
    dados: dict[str, Any],
    caminho: str,
    tema: dict[str, str],
    imagem: Image.Image | None = None,
) -> str:
    """Desenha o cartaz e grava em ``caminho``; devolve o caminho gravado."""
    fundo = tema.get("bg_sidebar", "#181818")
    carta = tema.get("bg_card", "#262626")
    destaque = tema.get("accent", "#7852FF")
    texto = tema.get("text", "#dcddde")
    suave = "#8b8c8f"

    cartaz = Image.new("RGB", (LARGURA, ALTURA), fundo)
    desenho = ImageDraw.Draw(cartaz)

    # Moldura dupla
    desenho.rectangle([18, 18, LARGURA - 18, ALTURA - 18], outline=destaque, width=6)
    desenho.rectangle([40, 40, LARGURA - 40, ALTURA - 40], outline=carta, width=3)

    fonte_wanted = _fonte(FONTES_SERIFA, 118)
    fonte_nome = _fonte(FONTES_NEGRITO, 52)
    fonte_selo = _fonte(FONTES_NEGRITO, 30)
    fonte_premio = _fonte(FONTES_NEGRITO, 44)
    fonte_rodape = _fonte(FONTES_NEGRITO, 22)

    desenho.text((LARGURA // 2, 120), "WANTED", font=fonte_wanted, fill=texto, anchor="mm")
    desenho.text((LARGURA // 2, 205), "DEAD OR ALIVE", font=fonte_selo, fill=destaque, anchor="mm")

    # Retrato
    topo, base = 250, 770
    lado = base - topo
    esquerda = (LARGURA - lado) // 2
    moldura = [esquerda - 8, topo - 8, esquerda + lado + 8, base + 8]
    desenho.rectangle(moldura, outline=destaque, width=4)

    if imagem is not None:
        copia = imagem.convert("RGB")
        copia.thumbnail((lado, lado), Image.Resampling.LANCZOS)
        x = esquerda + (lado - copia.width) // 2
        y = topo + (lado - copia.height) // 2
        cartaz.paste(copia, (x, y))
    else:
        desenho.rectangle([esquerda, topo, esquerda + lado, base], fill=carta)
        desenho.text((LARGURA // 2, (topo + base) // 2), "SEM IMAGEM",
                     font=fonte_selo, fill=suave, anchor="mm")

    nome = str(dados.get("nome", "Desconhecido")).strip() or "Desconhecido"
    # Quebra nomes longos em duas linhas
    if len(nome) > 22:
        corte = nome.rfind(" ", 0, 22)
        if corte > 0:
            nome = f"{nome[:corte]}\n{nome[corte + 1:]}"
    desenho.multiline_text((LARGURA // 2, 880), nome, font=fonte_nome, fill=texto, anchor="mm", align="center")

    premio = _recompensa_texto(dados.get("recompensa", "0"))
    desenho.text((LARGURA // 2, 1000), premio, font=fonte_premio, fill=destaque, anchor="mm")

    nivel = dados.get("nivel", "1")
    desenho.text((LARGURA // 2, 1080), f"Nível {nivel}  •  Marinha",
                 font=fonte_rodape, fill=suave, anchor="mm")
    desenho.text((LARGURA // 2, 1120), "ImpelDown Archives",
                 font=fonte_rodape, fill=suave, anchor="mm")

    cartaz.save(caminho, "PNG")
    return caminho
