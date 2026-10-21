def calcular_atributos_derivados(nivel_str, fis, agi, intel, inst, luta, acro, mod_passiva=0, mod_bloq=0, mod_esq=0, mod_cd=0):
    nivel = max(1, int(nivel_str)) if str(nivel_str).isdigit() else 1
    fis = max(0, fis)
    agi = max(0, agi)
    intel = max(0, intel)
    inst = max(0, inst)
    maior_attr = max(fis, agi, intel, inst)
    luta = max(0, luta)
    acro = max(0, acro)

    # Cálculo oficial de PV e PE (One Piece RPG)
    # Nível 1: Base Humana (12) + Físico. Níveis extras: Média do Dado de Vida (6) + Maior Atributo.
    pv_calculado = (12 + fis) + ((nivel - 1) * (6 + maior_attr))
    pe_calculado = 4 + nivel + maior_attr

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