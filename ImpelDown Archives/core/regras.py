"""Cálculos derivados do sistema novo do One Piece RPG.

Regras confirmadas:
* Atributos 0..5 (bônus fixo, 0 não penaliza).
* Graus de Perícia 0..3 (Leigo, Treinado, Especialista, Mestre).
* Defesa Passiva = 10 + Agilidade + equipamentos.
* Bloqueio = 10 + Físico + 2 × grau de Luta.
* Esquiva = 10 + Agilidade + 2 × grau de Acrobacia.
* PE Máximo = 4 + Nível + maior Atributo.
* PV = Base Humana (12 + Físico) + (Nível − 1) × (6 + maior Atributo).
* CD automática = 10 + maior Atributo + Nível ÷ 2 (+ bônus manual).
"""

from __future__ import annotations


def calcular_atributos_derivados(
    nivel_str,
    fis,
    agi,
    intel,
    inst,
    luta,
    acro,
    mod_passiva=0,
    mod_bloq=0,
    mod_esq=0,
    mod_cd=0,
    bonus_pv=0,
    bonus_pe=0,
):
    """Devolve PV, PE, Defesas e CD a partir dos valores da ficha."""
    nivel = max(1, int(nivel_str)) if str(nivel_str).isdigit() else 1
    fis = min(5, max(0, fis))
    agi = min(5, max(0, agi))
    intel = min(5, max(0, intel))
    inst = min(5, max(0, inst))
    maior_attr = max(fis, agi, intel, inst)

    # Sistema oficial: Graus de Perícia vão de 0 (Leigo) a 3 (Mestre).
    luta = max(0, min(3, luta))
    acro = max(0, min(3, acro))

    # PV: Base Humana (12 + Físico) + (Nível − 1) × (6 + maior Atributo).
    pv_calculado = max(
        1, (12 + fis) + ((nivel - 1) * (6 + maior_attr)) + int(bonus_pv)
    )
    # PE Máximo = 4 + Nível + maior Atributo.
    pe_calculado = max(1, 4 + nivel + maior_attr + int(bonus_pe))

    passiva = 10 + agi + mod_passiva
    bloq = 10 + fis + (2 * luta) + mod_bloq
    esq = 10 + agi + (2 * acro) + mod_esq
    # CD automática, com bônus manual opcional (mod_cd).
    cd = 10 + maior_attr + (nivel // 2) + mod_cd

    return {
        "pv": pv_calculado,
        "pe": pe_calculado,
        "passiva": passiva,
        "bloqueio": bloq,
        "esquiva": esq,
        "cd": cd,
    }
