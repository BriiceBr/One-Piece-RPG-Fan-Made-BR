def calcular_atributos_derivados(nivel_str, fis, agi, intel, inst, luta, acro, mod_passiva=0, mod_bloq=0, mod_esq=0, mod_cd=0, bonus_pv=0, bonus_pe=0):
    nivel = max(1, int(nivel_str)) if str(nivel_str).isdigit() else 1
    fis = min(5, max(0, fis))
    agi = min(5, max(0, agi))
    intel = min(5, max(0, intel))
    inst = min(5, max(0, inst))
    maior_attr = max(fis, agi, intel, inst)
    # Graus aceitam -1 (penalidade) até 4 (acima de Mestre), conforme a mesa.
    luta = max(-1, min(4, luta))
    acro = max(-1, min(4, acro))

    # Cálculo oficial de PV e PE (One Piece RPG)
    # Nível 1: Base Humana (12) + Físico. Níveis extras: Média do Dado de Vida (6) + Maior Atributo.
    # bonus_pv/bonus_pe podem ser negativos: é assim que a ficha edita o máximo direto.
    pv_calculado = max(1, (12 + fis) + ((nivel - 1) * (6 + maior_attr)) + int(bonus_pv))
    pe_calculado = max(1, 4 + nivel + maior_attr + int(bonus_pe))

    passiva = 10 + agi + mod_passiva
    bloq = 10 + fis + (2 * luta) + mod_bloq
    esq = 10 + agi + (2 * acro) + mod_esq
    cd = 10 + maior_attr + (nivel // 2) + mod_cd

    return {
        "pv": pv_calculado,
        "pe": pe_calculado,
        "passiva": passiva,
        "bloqueio": bloq,
        "esquiva": esq,
        "cd": cd
    }