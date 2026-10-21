import customtkinter as ctk

# Configurações globais do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- TEMAS DINÂMICOS PROFUNDOS E SUAVES ---
TEMAS = {
    "Obsidian (Padrão)": {
        "bg_sidebar": "#181818",
        "bg_main": "#1e1e1e",
        "bg_card": "#262626",
        "bg_input": "#363636",
        "accent": "#7852FF",
        "text": "#dcddde"
    },
    "Marinha (Azul)": {
        "bg_sidebar": "#11161d",
        "bg_main": "#171d26",
        "bg_card": "#1f2733",
        "bg_input": "#293342",
        "accent": "#4da6ff",
        "text": "#e6f0ff"
    },
    "Yonkou (Vermelho)": {
        "bg_sidebar": "#1a0e0e",
        "bg_main": "#241313",
        "bg_card": "#331b1b",
        "bg_input": "#422525",
        "accent": "#e05353",
        "text": "#ffe6e6"
    },
    "Pirata (Amarelo)": {
        "bg_sidebar": "#1c1811",
        "bg_main": "#262117",
        "bg_card": "#362e20",
        "bg_input": "#473c2a",
        "accent": "#e5b55e",
        "text": "#fff6e6"
    },
    "Exército Rev. (Verde)": {
        "bg_sidebar": "#101712",
        "bg_main": "#151f18",
        "bg_card": "#1d2b21",
        "bg_input": "#283b2d",
        "accent": "#6db35f",
        "text": "#e6ffe9"
    }
}

FONTES_DISPONIVEIS = [
    "Segoe UI",
    "Helvetica",
    "Consolas",
    "Roboto",
    "Courier New",
    "Comic Sans MS"
]

NOME_SISTEMA = "ImpelDown Archives - One Piece RPG"