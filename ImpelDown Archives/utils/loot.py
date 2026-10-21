import random

def gerar_loot_aleatorio(nivel_str):
    try:
        nivel = int(nivel_str) if str(nivel_str).isdigit() else 1
    except ValueError:
        nivel = 1

    berries_base = nivel * random.randint(150, 600)
    
    itens_comuns = ["Rações de Viagem (3 dias)", "Corda de Cânhamo (15m)", "Garrafa de Rum", "Vendas e Algemas", "Tocha Simples"]
    itens_incomuns = ["Bússola de Navegação", "Kit de Médicos Simples", "Pistola de Pederneira", "Mapa do Mar Local", "Luneta de Latão"]
    itens_raros = ["Log Pose Básico", "Lâmina de Aço Dobrado", "Kit de Veneno de Serpente", "Carta de Marque da Marinha", "Pedra de Amolar Especial"]
    itens_epicos = ["Pedaço de Vivre Card", "Projeto de Canhão Pesado", "Log Pose Triplo", "Frasco de Essência de Pós de Tritão"]

    loot_sorteado = [f"💰 Berries: {berries_base:,} B".replace(",", ".")]
    num_itens = max(1, random.randint(1, 2) + (nivel // 3))
    
    for _ in range(num_itens):
        d100 = random.randint(1, 100)
        if d100 <= 50:
            loot_sorteado.append("• " + random.choice(itens_comuns))
        elif d100 <= 80:
            loot_sorteado.append("• " + random.choice(itens_incomuns))
        elif d100 <= 95:
            loot_sorteado.append("• " + random.choice(itens_raros))
        else:
            loot_sorteado.append("• " + random.choice(itens_epicos))

    return "\n".join(loot_sorteado)