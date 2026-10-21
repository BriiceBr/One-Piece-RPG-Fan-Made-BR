def calcular_dificuldade_encontro(tracker_data, dados_banco):
    if not tracker_data:
        return "Sem Inimigos", "#8b8c8f"
    
    soma_niveis = 0
    for item in tracker_data:
        item_id = item.get("id")
        if item_id in dados_banco:
            niv = int(dados_banco[item_id].get("nivel", 1))
        else:
            niv = 1
        soma_niveis += niv

    if soma_niveis <= 3:
        return f"Fácil (Nível Total: {soma_niveis})", "#6db35f"
    elif soma_niveis <= 8:
        return f"Médio (Nível Total: {soma_niveis})", "#e5b55e"
    elif soma_niveis <= 15:
        return f"Difícil (Nível Total: {soma_niveis})", "#e05353"
    else:
        return f"Mortal (Nível Total: {soma_niveis})", "#a82020"