import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import sqlite3
import json
import os
import random
import re
from PIL import Image, ImageTk
import customtkinter as ctk

# Configurações globais do CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- TEMAS DINÂMICOS PROFUNDOS E SUAVES ---
TEMAS = {
    "Obsidian (Padrão)": {"bg_sidebar": "#181818", "bg_main": "#1e1e1e", "bg_card": "#262626", "bg_input": "#363636", "accent": "#7852FF", "text": "#dcddde"},
    "Marinha (Azul)": {"bg_sidebar": "#11161d", "bg_main": "#171d26", "bg_card": "#1f2733", "bg_input": "#293342", "accent": "#4da6ff", "text": "#e6f0ff"},
    "Yonkou (Vermelho)": {"bg_sidebar": "#1a0e0e", "bg_main": "#241313", "bg_card": "#331b1b", "bg_input": "#422525", "accent": "#e05353", "text": "#ffe6e6"},
    "Pirata (Amarelo)": {"bg_sidebar": "#1c1811", "bg_main": "#262117", "bg_card": "#362e20", "bg_input": "#473c2a", "accent": "#e5b55e", "text": "#fff6e6"},
    "Exército Rev. (Verde)": {"bg_sidebar": "#101712", "bg_main": "#151f18", "bg_card": "#1d2b21", "bg_input": "#283b2d", "accent": "#6db35f", "text": "#e6ffe9"}
}

FONTES_DISPONIVEIS = ["Segoe UI", "Helvetica", "Consolas", "Roboto", "Courier New", "Comic Sans MS"]

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

def rolar_dados_seguro(expressao):
    texto = re.sub(r"\s+", "", expressao).lower()
    if not texto: raise ValueError("Informe uma expressão de dados.")
    termos = re.findall(r"[+-]?[^+-]+", texto)
    if "".join(termos) != texto: raise ValueError("Expressão inválida.")
    
    total = 0
    detalhes = []
    
    for termo in termos:
        sinal = -1 if termo.startswith("-") else 1
        corpo = termo.lstrip("+-")
        if not corpo: continue
        
        if "d" in corpo:
            partes = re.fullmatch(r"(\d*)d(\d+)", corpo)
            if not partes: raise ValueError(f"Formato inválido: {termo}")
            qtd = int(partes.group(1) or "1")
            lados = int(partes.group(2))
            if not 1 <= qtd <= 100: raise ValueError("Limite: 1 a 100 dados.")
            if not 2 <= lados <= 1000: raise ValueError("Limite: dados de 2 a 1000 faces.")
                
            rolagens = [random.randint(1, lados) for _ in range(qtd)]
            total += sum(rolagens) * sinal
            sinal_texto = "-" if sinal < 0 else "+"
            detalhes.append(f"{sinal_texto}({'+'.join(map(str, rolagens))})")
        else:
            if not re.fullmatch(r"\d+", corpo): raise ValueError(f"Modificador inválido: {termo}")
            valor = int(corpo) * sinal
            total += valor
            detalhes.append(f"{valor:+d}")
            
    return f"{total} 🎲 ({' '.join(detalhes).lstrip('+ ')})"


class DraggableNotebook(ttk.Notebook):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<ButtonPress-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        self._drag_data = {"index": None}

    def on_drag_start(self, event):
        try:
            index = self.index(f"@{event.x},{event.y}")
            self._drag_data["index"] = index
        except tk.TclError:
            self._drag_data["index"] = None

    def on_drag_motion(self, event):
        if self._drag_data["index"] is None: return
        try:
            target_index = self.index(f"@{event.x},{event.y}")
            if target_index != self._drag_data["index"]:
                self.insert(target_index, self.tabs()[self._drag_data["index"]])
                self._drag_data["index"] = target_index
        except tk.TclError:
            pass


class HabilidadeBloco(ctk.CTkFrame):
    def __init__(self, parent, dados_hab, canvas_mestre, painel_direito, app_master):
        self.app_master = app_master
        self.tema = app_master.tema_atual
        super().__init__(parent, fg_color=self.tema["bg_card"], corner_radius=8)
        self.pack(fill=tk.X, pady=8, padx=10)
        self.canvas_mestre = canvas_mestre
        self.painel_direito = painel_direito

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill=tk.X, padx=10, pady=8)

        self.var_titulo = tk.StringVar(value=dados_hab.get("titulo", ""))
        self.entrada_titulo = ctk.CTkEntry(self.header, textvariable=self.var_titulo, fg_color="transparent", text_color=self.tema["text"], border_width=0, font=self.app_master.get_font('bold'))
        self.entrada_titulo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        meta_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        meta_frame.pack(side=tk.LEFT, padx=10)

        def add_meta_field(master, label, width, var_val):
            ctk.CTkLabel(master, text=label, text_color="#8b8c8f", font=self.app_master.get_font('small')).pack(side=tk.LEFT, padx=(5,2))
            var = tk.StringVar(value=var_val)
            entry = ctk.CTkEntry(master, textvariable=var, width=width, height=24, fg_color=self.tema["bg_input"], border_width=0, font=self.app_master.get_font('small'), text_color=self.tema["text"])
            entry.pack(side=tk.LEFT)
            return var

        self.var_custo = add_meta_field(meta_frame, "Custo:", 40, dados_hab.get("custo", ""))
        self.var_limite = add_meta_field(meta_frame, "Lim:", 40, dados_hab.get("limite", ""))
        self.var_exec = add_meta_field(meta_frame, "Exec:", 60, dados_hab.get("execucao", ""))
        self.var_alcance = add_meta_field(meta_frame, "Alcance:", 80, dados_hab.get("alcance", ""))

        self.btn_toggle = ctk.CTkButton(self.header, text="▼▲", width=30, height=24, fg_color="transparent", hover_color=self.tema["bg_input"], text_color="#8b8c8f", command=self.toggle)
        self.btn_toggle.pack(side=tk.LEFT, padx=5)
        
        self.btn_deletar = ctk.CTkButton(self.header, text="✖", width=30, height=24, fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75", command=self.destroy)
        self.btn_deletar.pack(side=tk.LEFT)

        self.container_texto = ctk.CTkFrame(self, fg_color="transparent")
        self.container_texto.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.texto = ctk.CTkTextbox(self.container_texto, height=90, fg_color=self.tema["bg_input"], text_color=self.tema["text"], font=self.app_master.get_font('main'), wrap=tk.WORD, border_width=0, corner_radius=6)
        self.texto.insert(tk.END, dados_hab.get("conteudo", ""))
        self.texto.pack(fill=tk.X)

        self.grip = tk.Frame(self.container_texto, height=5, bg="#3a3a3a", cursor="sb_v_double_arrow")
        self.grip.pack(fill=tk.X, pady=(2,0))
        self.grip.bind("<B1-Motion>", self.redimensionar)

    def redimensionar(self, event):
        nova_altura = self.texto.winfo_height() + event.y
        if nova_altura > 40:
            self.texto.configure(height=nova_altura)

    def toggle(self):
        if self.container_texto.winfo_ismapped(): self.container_texto.pack_forget()
        else: self.container_texto.pack(fill=tk.X, padx=10, pady=(0, 10))
        
    def get_dados(self):
        return {
            "titulo": self.var_titulo.get().strip(),
            "custo": self.var_custo.get().strip(),
            "limite": self.var_limite.get().strip(),
            "execucao": self.var_exec.get().strip(),
            "alcance": self.var_alcance.get().strip(),
            "conteudo": self.texto.get("1.0", tk.END).strip()
        }


class FichaPersonagemFrame(ctk.CTkFrame):
    def __init__(self, parent, sync_nome_callback, app_master, dados_iniciais=None):
        self.app_master = app_master
        self.tema = app_master.tema_atual
        super().__init__(parent, fg_color=self.tema["bg_main"])
        self.sync_nome_callback = sync_nome_callback
        self.caminho_imagem_salva = ""

        self.var_nome = tk.StringVar(value="Novo Inimigo")
        self.var_nivel = tk.StringVar(value="1")
        
        self.pv_atual = tk.IntVar(value=100)
        self.pe_atual = tk.IntVar(value=20)
        self.var_fis = tk.IntVar(value=1)
        self.var_agi = tk.IntVar(value=1)
        self.var_int = tk.IntVar(value=1)
        self.var_inst = tk.IntVar(value=1)
        self.var_luta = tk.IntVar(value=0)
        self.var_acro = tk.IntVar(value=0)

        self.mod_passiva = tk.IntVar(value=0)
        self.mod_bloq = tk.IntVar(value=0)
        self.mod_esq = tk.IntVar(value=0)
        self.mod_cd = tk.IntVar(value=0)

        # Sincroniza tanto o nome quanto o nível na árvore em tempo real
        self.var_nome.trace_add("write", self._sincronizar_arvore)
        self.var_nivel.trace_add("write", self._sincronizar_arvore)
        
        self.var_recompensa = tk.StringVar(value="0")
        self.recompensa_bloqueio = False
        self.var_recompensa.trace_add("write", self.formatar_recompensa)

        gatilhos = [self.var_nivel, self.var_fis, self.var_agi, self.var_int, self.var_inst, self.var_luta, self.var_acro,
                    self.mod_passiva, self.mod_bloq, self.mod_esq, self.mod_cd]
        for var in gatilhos:
            var.trace_add("write", self.calcular_derivados)

        self.montar_interface()
        
        if dados_iniciais:
            self.carregar_dados(dados_iniciais)
        else:
            self.calcular_derivados()

    def formatar_recompensa(self, *args):
        if self.recompensa_bloqueio: return
        val = self.var_recompensa.get()
        nums = re.sub(r"\D", "", val)
        if not nums: 
            formatado = ""
        else:
            formatado = f"{int(nums):,}".replace(",", ".")
        
        self.recompensa_bloqueio = True
        self.var_recompensa.set(formatado)
        self.recompensa_bloqueio = False

    def _sincronizar_arvore(self, *args):
        self.sync_nome_callback(self.var_nome.get(), self.var_nivel.get())

    def montar_interface(self):
        # --- TOPO: STATUS ---
        frame_topo = ctk.CTkFrame(self, fg_color=self.tema["bg_card"], corner_radius=0, height=50)
        frame_topo.pack(side=tk.TOP, fill=tk.X)
        
        f_inner = ctk.CTkFrame(frame_topo, fg_color="transparent")
        f_inner.pack(fill=tk.X, padx=20, pady=10)

        ctk.CTkLabel(f_inner, text="PV:", text_color="#8b8c8f", font=self.app_master.get_font('bold')).pack(side=tk.LEFT, padx=(0, 5))
        ctk.CTkButton(f_inner, text="-", width=28, fg_color=self.tema["bg_input"], command=lambda: self.pv_atual.set(self.pv_atual.get()-1)).pack(side=tk.LEFT)
        ctk.CTkEntry(f_inner, textvariable=self.pv_atual, width=50, font=self.app_master.get_font('title'), text_color="#e06c75", justify="center", border_width=0, fg_color="transparent").pack(side=tk.LEFT)
        ctk.CTkButton(f_inner, text="+", width=28, fg_color=self.tema["bg_input"], command=lambda: self.pv_atual.set(self.pv_atual.get()+1)).pack(side=tk.LEFT, padx=(0, 15))

        ctk.CTkLabel(f_inner, text="PE:", text_color="#8b8c8f", font=self.app_master.get_font('bold')).pack(side=tk.LEFT, padx=(0, 5))
        ctk.CTkButton(f_inner, text="-", width=28, fg_color=self.tema["bg_input"], command=lambda: self.pe_atual.set(self.pe_atual.get()-1)).pack(side=tk.LEFT)
        ctk.CTkEntry(f_inner, textvariable=self.pe_atual, width=50, font=self.app_master.get_font('title'), text_color="#56b6c2", justify="center", border_width=0, fg_color="transparent").pack(side=tk.LEFT)
        ctk.CTkButton(f_inner, text="+", width=28, fg_color=self.tema["bg_input"], command=lambda: self.pe_atual.set(self.pe_atual.get()+1)).pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_defesas = ctk.CTkLabel(f_inner, text="Pass: -- | Bloq: -- | Esq: -- | CD: --", text_color="#e5c07b", font=self.app_master.get_font('main'))
        self.lbl_defesas.pack(side=tk.LEFT)

        self.btn_rolar_dano = ctk.CTkButton(f_inner, text="🎲 Rolar", command=self.rolar_dano, fg_color=self.tema["accent"], text_color="white", width=80)
        self.btn_rolar_dano.pack(side=tk.RIGHT, padx=(5,0))
        
        ctk.CTkButton(f_inner, text="📝 Exportar .md", command=self.exportar_markdown, fg_color=self.tema["bg_input"], hover_color="#4a4a4a", text_color=self.tema["text"], width=100).pack(side=tk.RIGHT, padx=(5,0))
        ctk.CTkButton(f_inner, text="🖥️ Tela Jogador", command=self.abrir_modo_jogador, fg_color=self.tema["bg_input"], hover_color="#4a4a4a", text_color=self.tema["text"], width=110).pack(side=tk.RIGHT)

        # --- CONTAINER PRINCIPAL ---
        self.container_ficha = ctk.CTkFrame(self, fg_color="transparent")
        self.container_ficha.pack(fill=tk.BOTH, expand=True, pady=15, padx=15)

        self.painel_esquerdo = ctk.CTkFrame(self.container_ficha, width=340, fg_color="transparent")
        self.painel_esquerdo.pack_propagate(False)
        self.painel_esquerdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        self.painel_direito = ctk.CTkFrame(self.container_ficha, fg_color="transparent")
        self.painel_direito.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- PAINEL ESQUERDO: INFOS E IMAGEM ---
        frame_id = ctk.CTkFrame(self.painel_esquerdo, fg_color="transparent")
        frame_id.pack(fill=tk.X, pady=(0, 5))
        
        f_nome = ctk.CTkFrame(frame_id, fg_color="transparent")
        f_nome.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        f_lbl = ctk.CTkFrame(f_nome, fg_color="transparent")
        f_lbl.pack(fill=tk.X)
        ctk.CTkLabel(f_lbl, text="Nome da Ameaça", text_color="#8b8c8f", font=self.app_master.get_font('small')).pack(side=tk.LEFT)
        ctk.CTkButton(f_lbl, text="🎲 Aleatório", width=20, height=15, fg_color="transparent", text_color=self.tema["accent"], hover_color=self.tema["bg_input"], font=self.app_master.get_font('small'), command=self.gerar_nome_pirata).pack(side=tk.LEFT, padx=(5,0))

        self.entrada_nome = ctk.CTkEntry(f_nome, textvariable=self.var_nome, font=self.app_master.get_font('title'), fg_color=self.tema["bg_input"], text_color=self.tema["text"], border_width=0, height=32)
        self.entrada_nome.pack(fill=tk.X)

        f_nivel = ctk.CTkFrame(frame_id, fg_color="transparent")
        f_nivel.pack(side=tk.RIGHT, padx=(10, 0))
        ctk.CTkLabel(f_nivel, text="Nível", text_color="#8b8c8f", font=self.app_master.get_font('small')).pack(anchor="e")
        ctk.CTkEntry(f_nivel, textvariable=self.var_nivel, width=45, height=32, font=self.app_master.get_font('title'), justify="center", fg_color=self.tema["bg_input"], text_color=self.tema["text"], border_width=0).pack(side=tk.RIGHT)

        f_recomp = ctk.CTkFrame(self.painel_esquerdo, fg_color="transparent")
        f_recomp.pack(fill=tk.X, pady=(0, 10))
        ctk.CTkLabel(f_recomp, text="☠️ Recompensa:", text_color="#e5c07b", font=self.app_master.get_font('bold')).pack(side=tk.LEFT)
        ctk.CTkEntry(f_recomp, textvariable=self.var_recompensa, font=self.app_master.get_font('bold'), fg_color="transparent", text_color="#e5c07b", border_width=0, justify="right").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ctk.CTkLabel(f_recomp, text="Berries", text_color="#e5c07b", font=self.app_master.get_font('bold')).pack(side=tk.LEFT, padx=(5,0))

        self.frame_imagem = tk.Frame(self.painel_esquerdo, width=180, height=180, bg=self.tema["bg_input"])
        self.frame_imagem.pack_propagate(False)
        self.frame_imagem.pack(anchor="center", pady=(0, 5)) 

        self.canvas_img = tk.Canvas(self.frame_imagem, bg=self.tema["bg_input"], highlightthickness=0)
        self.canvas_img.pack(fill=tk.BOTH, expand=True)
        self.txt_img_placeholder = self.canvas_img.create_text(90, 90, text="Arraste ou dê Scroll", fill="#8b8c8f", font=self.app_master.get_font('small'))

        self.imagem_original = None
        self.foto = None
        self.escala_imagem = 1.0
        self.img_x, self.img_y = 90, 90
        
        self.canvas_img.bind("<ButtonPress-1>", self.iniciar_arraste)
        self.canvas_img.bind("<B1-Motion>", self.arrastar_imagem)
        self.canvas_img.bind("<MouseWheel>", self.zoom_imagem)

        ctk.CTkButton(self.painel_esquerdo, text="Procurar Imagem", command=self.carregar_imagem, fg_color=self.tema["bg_input"], hover_color="#4a4a4a", text_color=self.tema["text"]).pack(anchor="center", fill=tk.X, pady=(0, 10))

        # --- PAINEL ESQUERDO: ABAS ---
        self.tabview_esquerdo = ctk.CTkTabview(self.painel_esquerdo, fg_color="transparent", segmented_button_selected_color=self.tema["accent"], segmented_button_selected_hover_color=self.tema["accent"])
        self.tabview_esquerdo.pack(fill=tk.BOTH, expand=True)

        tab_attr = self.tabview_esquerdo.add("Atributos")
        tab_loot = self.tabview_esquerdo.add("Loot")
        tab_bg = self.tabview_esquerdo.add("História")
        tab_bando = self.tabview_esquerdo.add("Bando") # <--- NOVO

        def criar_mini_contador(master, label, var, width_val=28):
            f = ctk.CTkFrame(master, fg_color="transparent")
            f.pack(side=tk.LEFT, expand=True, padx=2)
            ctk.CTkLabel(f, text=label, text_color="#8b8c8f", font=self.app_master.get_font('small')).pack()
            f_val = ctk.CTkFrame(f, fg_color="transparent")
            f_val.pack()
            ctk.CTkButton(f_val, text="-", width=22, height=22, fg_color=self.tema["bg_input"], command=lambda: var.set(var.get()-1)).pack(side=tk.LEFT)
            ctk.CTkLabel(f_val, textvariable=var, width=width_val, font=self.app_master.get_font('bold')).pack(side=tk.LEFT)
            ctk.CTkButton(f_val, text="+", width=22, height=22, fg_color=self.tema["bg_input"], command=lambda: var.set(var.get()+1)).pack(side=tk.LEFT)

        frame_attrs1 = ctk.CTkFrame(tab_attr, fg_color="transparent")
        frame_attrs1.pack(fill=tk.X, pady=(5,0))
        criar_mini_contador(frame_attrs1, "Fís", self.var_fis)
        criar_mini_contador(frame_attrs1, "Agi", self.var_agi)
        criar_mini_contador(frame_attrs1, "Int", self.var_int)
        criar_mini_contador(frame_attrs1, "Inst", self.var_inst)

        frame_pericias = ctk.CTkFrame(tab_attr, fg_color="transparent")
        frame_pericias.pack(fill=tk.X, pady=(15, 5))
        criar_mini_contador(frame_pericias, "Grau Luta", self.var_luta)
        criar_mini_contador(frame_pericias, "Grau Acro", self.var_acro)
        
        ctk.CTkLabel(tab_attr, text="Bônus Extras Passivos", text_color="#8b8c8f", font=self.app_master.get_font('small')).pack(anchor="w", pady=(15, 0))
        frame_mods = ctk.CTkFrame(tab_attr, fg_color="transparent")
        frame_mods.pack(fill=tk.X)
        criar_mini_contador(frame_mods, "+Pass", self.mod_passiva, width_val=22)
        criar_mini_contador(frame_mods, "+Bloq", self.mod_bloq, width_val=22)
        criar_mini_contador(frame_mods, "+Esq", self.mod_esq, width_val=22)
        criar_mini_contador(frame_mods, "+CD", self.mod_cd, width_val=22)

        self.texto_loot = ctk.CTkTextbox(tab_loot, fg_color=self.tema["bg_input"], text_color=self.tema["text"], font=self.app_master.get_font('main'), border_width=0, corner_radius=6)
        self.texto_loot.pack(fill=tk.BOTH, expand=True, pady=5)

        ctk.CTkButton(tab_bg, text="🧠 Gerar IA", command=self.gerar_ia_local, fg_color=self.tema["bg_input"], text_color=self.tema["text"]).pack(fill=tk.X, pady=(0,5))
        self.texto_historia = ctk.CTkTextbox(tab_bg, fg_color=self.tema["bg_input"], text_color=self.tema["text"], font=self.app_master.get_font('main'), wrap=tk.WORD, border_width=0, corner_radius=6)
        self.texto_historia.pack(fill=tk.BOTH, expand=True)

        # Tab Bando
        ctk.CTkLabel(tab_bando, text="Arraste as fichas dos lacaios para cá", text_color="#8b8c8f", font=self.app_master.get_font('small')).pack(pady=(0,2))
        self.listbox_bando = tk.Listbox(tab_bando, bg=self.tema["bg_input"], fg=self.tema["text"], font=self.app_master.get_font('main'), bd=0, highlightthickness=0)
        self.listbox_bando.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.listbox_bando.bando_tag = True 

        f_btn_bando = ctk.CTkFrame(tab_bando, fg_color="transparent")
        f_btn_bando.pack(fill=tk.X, pady=5)
        ctk.CTkButton(f_btn_bando, text="⚔️ Jogar Esquadrão no Tracker", command=self.lancar_bando_tracker, fg_color=self.tema["accent"], text_color="white").pack(fill=tk.X, pady=(0,2))
        ctk.CTkButton(f_btn_bando, text="✖ Limpar Bando", command=lambda: self.listbox_bando.delete(0, tk.END), fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75").pack(fill=tk.X)

        # --- CONTEÚDO PAINEL DIREITO ---
        frame_hab_topo = ctk.CTkFrame(self.painel_direito, fg_color="transparent")
        frame_hab_topo.pack(side=tk.TOP, fill=tk.X, pady=(0, 15), padx=10)
        
        ctk.CTkLabel(frame_hab_topo, text="Lista de Habilidades e Ações", text_color=self.tema["text"], font=self.app_master.get_font('title')).pack(side=tk.LEFT)
        
        self.btn_add_hab = ctk.CTkButton(frame_hab_topo, text="➕ Adicionar ▼", fg_color=self.tema["bg_input"], hover_color="#4a4a4a", text_color=self.tema["text"], font=self.app_master.get_font('bold'))
        self.menu_hab = tk.Menu(self.btn_add_hab, tearoff=0, bg=self.tema["bg_card"], fg=self.tema["text"], bd=0, activebackground=self.tema["accent"])
        for patamar in ["Básica", "Média", "Forte", "Suprema", "Outros"]:
            self.menu_hab.add_command(label=patamar, command=lambda p=patamar: self.inserir_habilidade(p))
        self.btn_add_hab.configure(command=lambda: self.menu_hab.post(self.btn_add_hab.winfo_rootx(), self.btn_add_hab.winfo_rooty() + self.btn_add_hab.winfo_height()))
        self.btn_add_hab.pack(side=tk.RIGHT)

        # Dropdown de Filtro de Habilidades
        self.var_filtro_hab = ctk.StringVar(value="Todas")
        opcoes_filtro = ["Todas", "Básica", "Média", "Forte", "Suprema", "1 Ação", "Reação", "Livre"]
        self.menu_filtro = ctk.CTkOptionMenu(frame_hab_topo, variable=self.var_filtro_hab, values=opcoes_filtro, command=self.filtrar_habilidades, fg_color=self.tema["bg_input"], text_color=self.tema["text"], width=110)
        self.menu_filtro.pack(side=tk.RIGHT, padx=(10, 10))

        self.canvas_hab = tk.Canvas(self.painel_direito, bg=self.tema["bg_main"], highlightthickness=0)
        self.scroll_hab = ttk.Scrollbar(self.painel_direito, orient="vertical", command=self.canvas_hab.yview)
        self.frame_lista_hab = tk.Frame(self.canvas_hab, bg=self.tema["bg_main"])

        self.frame_lista_hab.bind("<Configure>", lambda e: self.canvas_hab.configure(scrollregion=self.canvas_hab.bbox("all")))
        self.canvas_janela = self.canvas_hab.create_window((0, 0), window=self.frame_lista_hab, anchor="nw")
        self.canvas_hab.bind("<Configure>", lambda e: self.canvas_hab.itemconfig(self.canvas_janela, width=e.width))
        self.canvas_hab.configure(yscrollcommand=self.scroll_hab.set)
        
        self.canvas_hab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_hab.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas_hab.bind("<Enter>", lambda e: self.canvas_hab.bind_all("<MouseWheel>", self._on_mousewheel_canvas))
        self.canvas_hab.bind("<Leave>", lambda e: self.canvas_hab.unbind_all("<MouseWheel>"))
        self.blocos_habilidades = []

    def _on_mousewheel_canvas(self, event):
        try:
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if not widget or str(self.painel_direito) not in str(widget): return
            if isinstance(widget, tk.Text): return
            delta = event.delta if hasattr(event, 'delta') else 0
            if delta != 0: self.canvas_hab.yview_scroll(int(-1 * (delta / 120)), "units")
        except Exception:
            pass

    def calcular_derivados(self, *args):
        try:
            nivel_str = self.var_nivel.get()
            nivel = max(0, int(nivel_str)) if nivel_str.isdigit() else 0
            fis = max(0, self.var_fis.get())
            agi = max(0, self.var_agi.get())
            maior_attr = max(fis, agi, self.var_int.get(), self.var_inst.get())
            luta = max(0, self.var_luta.get())
            acro = max(0, self.var_acro.get())

            passiva = 10 + agi + self.mod_passiva.get()
            bloq = 10 + fis + (2 * luta) + self.mod_bloq.get()
            esq = 10 + agi + (2 * acro) + self.mod_esq.get()
            cd = 10 + maior_attr + (nivel // 2) + self.mod_cd.get()

            self.lbl_defesas.configure(text=f"Pass: {passiva}  |  Bloq: {bloq}  |  Esq: {esq}  |  CD: {cd}")
        except Exception:
            pass

    def rolar_dano(self):
        dano = simpledialog.askstring("Rolar Dano", "Digite a rolagem (ex: 2d8+3):", parent=self)
        if dano:
            try:
                resultado = rolar_dados_seguro(dano)
                # Removido o pop up chato! Agora vai tudo para o Log!
                self.app_master.registrar_log(f"⚔️ [{self.var_nome.get()}] Atacou: {dano} ➔ {resultado}")
            except Exception as e:
                messagebox.showerror("Expressão Inválida", str(e), parent=self)

    def gerar_nome_pirata(self):
        titulos = [
            # ===== ORIGINAIS =====
            "O Sanguinário", "Mão de Ferro", "Olho de Vidro", "O Terrível", "Alma Negra",
            "O Imortal", "Dente de Ouro", "O Açougueiro", "Sem Rosto", "O Rastejante",
            "Perna de Pau", "Coração Gelado", "O Furacão", "O Carrasco", "Veneno Negro",

            # ===== APARÊNCIA / MARCA =====
            "O Barba Rubra", "Cabeça de Caveira", "O Caolho", "Garra de Aço",
            "O Tatuado", "Cicatriz de Guerra", "O Careca", "Dentes de Tubarão",
            "O Corcunda", "Punho de Pedra", "O Cabelo de Fogo", "Nariz de Gancho",
            "O Gigante", "Pele de Bronze", "O Anão Furioso", "Sombra de Prata",
            "O Barba Negra", "O Barba Branca", "O Barba Grisalha", "O Barba de Fogo",
            "O Cabelo de Neve", "Olho de Âmbar", "Olho de Cobra", "Olho de Lobo",
            "O Manco", "O Mudo", "O Surdo", "O Cego de Um Olho",
            "Mão de Gancho", "Mão de Seda", "Pé de Ferro", "Costela de Aço",
            "O Queimado", "O Marcado", "O Tatuado de Guerra", "O Pintado",
            "O Alto", "O Baixo", "O Gordo", "O Magro", "O Esquelético",
            "O Musgoso", "O Coberto de Cicatrizes", "O Rosto Rachado",

            # ===== PERSONALIDADE / FAMA =====
            "O Impiedoso", "O Louco", "O Silencioso", "O Traiçoeiro",
            "O Sedento", "O Insaciável", "O Vingador", "O Maldito",
            "O Fantasma", "O Rei dos Mares", "O Senhor das Tempestades",
            "O Devorador", "O Estrangulador", "O Invencível", "O Cruel",
            "O Astuto", "O Mentiroso", "O Ladrão de Almas", "O Herege",
            "O Justo", "O Injusto", "O Generoso", "O Mesquinho",
            "O Ganancioso", "O Avarento", "O Pródigo", "O Esbanjador",
            "O Paciente", "O Impaciente", "O Vingativo", "O Rancoroso",
            "O Sangrento", "O Sedento de Ouro", "O Sedento de Sangue",
            "O Insano", "O Sábio", "O Tolo", "O Bêbado", "O Sóbrio",
            "O Fiel", "O Traidor", "O Leal", "O Desleal",
            "O Bravo", "O Covarde", "O Valente", "O Temido",
            "O Amado", "O Odiado", "O Adorado", "O Desprezado",
            "O Misericordioso", "O Sem Misericórdia", "O Piedoso", "O Ímpio",

            # ===== ELEMENTOS / NATUREZA =====
            "Filho do Trovão", "O Filho do Mar", "O Senhor do Vento",
            "Chama Eterna", "O Filho da Névoa", "Orelha de Coral",
            "O Escorpião", "A Serpente dos Mares", "O Lobo do Mar",
            "O Tubarão Branco", "O Polvo Negro", "O Dragão Afundado",
            "O Filho da Tempestade", "O Filho do Raio", "O Filho do Fogo",
            "O Filho do Gelo", "O Filho da Areia", "O Filho da Lua",
            "O Filho do Sol", "O Filho das Estrelas", "O Filho da Noite",
            "O Senhor do Fogo", "O Senhor do Gelo", "O Senhor da Chuva",
            "O Senhor da Névoa", "O Senhor das Sombras", "O Senhor da Luz",
            "A Fúria do Mar", "A Fúria do Vento", "A Fúria do Fogo",
            "O Raio", "O Trovão", "O Relâmpago", "O Ciclone", "O Tufão",
            "O Maremoto", "O Terremoto", "O Vulcão", "O Abismo",
            "O Mar Revolto", "A Onda Negra", "A Maré Vermelha", "A Maré de Sangue",

            # ===== ANIMAIS / FERAS =====
            "O Lobo", "O Urso", "O Tigre", "O Leão", "O Falcão",
            "O Corvo", "O Abutre", "A Águia", "O Gavião", "O Morcego",
            "O Tubarão", "A Orca", "O Polvo", "A Enguia", "O Caranguejo",
            "O Escorpião Negro", "A Aranha", "A Víbora", "A Jiboia", "O Crocodilo",
            "O Jacaré", "O Rinoceronte", "O Touro", "O Bode", "O Javali",
            "O Cão Selvagem", "O Lobo Faminto", "O Urso Polar", "A Pantera",
            "O Leopardo", "A Hiena", "O Chacal", "A Raposa", "O Lince",
            "O Dragão", "A Fênix", "O Grifo", "O Basilisco", "A Hidra",
            "O Kraken", "A Sereia", "O Tritão", "O Leviatã", "A Quimera",

            # ===== REFERÊNCIAS / EXÓTICOS =====
            "O Pirata Escarlate", "O Barão Vermelho", "O Corsário",
            "O Bucaneiro", "O Filibusteiro", "O Contrabandista",
            "O Rei Pirata", "O Almirante Negro", "O Capitão do Diabo",
            "O Afogado", "O Ressuscitado", "O Condenado",
            "O Rei do Caribe", "O Rei do Atlântico", "O Rei do Pacífico",
            "O Imperador dos Mares", "O Czar dos Piratas", "O Sultão do Mar",
            "O Xerife dos Mares", "O Juiz do Mar", "O Carrasco do Mar",
            "O Cão do Mar", "O Cão de Caça", "O Cão Raivoso",
            "O Anjo Negro", "O Anjo Caído", "O Demônio do Mar",
            "O Diabo Ruivo", "O Diabo Loira", "O Diabo de Olhos Verdes",
            "O Ceifador", "O Coveiro", "O Carniceiro", "O Açougueiro do Mar",
            "O Rei dos Ladrões", "O Rei dos Contrabandistas", "O Rei dos Assassinos",
            "O Senhor da Guerra", "O Senhor da Morte", "O Senhor do Caos",
            "O Mestre das Sombras", "O Mestre das Lâminas", "O Mestre dos Mares",

            # ===== TÍTULOS NOBRES / FALSOS =====
            "O Duque", "O Conde", "O Barão", "O Visconde", "O Marquês",
            "O Príncipe", "O Rei", "O Imperador", "O Sultão", "O Czar",
            "O Lorde", "O Cavaleiro", "O Sir", "O Almirante", "O General",
            "O Coronel", "O Capitão", "O Tenente", "O Sargento", "O Soldado",
            "O Papa Negro", "O Bispo", "O Cardeal", "O Arcebispo", "O Padre",
            "O Profeta", "O Messias", "O Salvador", "O Redentor", "O Santo",
            "O Rei Louco", "O Rei Cego", "O Rei Morto", "O Rei Vivo",
            "O Rei de Nada", "O Rei de Tudo", "O Rei Sem Coroa", "O Rei Sem Trono",
            "O Falso Rei", "O Rei Verdadeiro", "O Rei Eterno", "O Rei Passageiro",

            # ===== ADJETIVOS DE COR =====
            "O Vermelho", "O Negro", "O Branco", "O Cinza", "O Dourado",
            "O Prateado", "O Escarlate", "O Carmesim", "O Púrpura", "O Violeta",
            "O Verde", "O Azul", "O Amarelo", "O Laranja", "O Marrom",
            "O Cor de Sangue", "O Cor de Ferrugem", "O Cor de Vinho",
            "O Cor de Barro", "O Cor de Cinzas", "O Cor de Noite",
            "O Cor de Gelo", "O Cor de Fogo", "O Cor de Ouro",

            # ===== ADJETIVOS DE TAMANHO / FORÇA =====
            "O Pequeno", "O Grande", "O Enorme", "O Colossal", "O Titânico",
            "O Fraco", "O Forte", "O Poderoso", "O Indomável", "O Domável",
            "O Quebrado", "O Inteiro", "O Inquebrável", "O Destruído", "O Destruidor",
            "O Construtor", "O Demolidor", "O Aniquilador", "O Criador", "O Devastador",

            # ===== MISC / CRIATIVOS =====
            "O Sem Nome", "O Sem Passado", "O Sem Futuro", "O Sem Alma",
            "O Sem Coração", "O Sem Medo", "O Sem Piedade", "O Sem Lei",
            "O Fora da Lei", "O Fora do Tempo", "O Fora do Mundo", "O Fora do Mar",
            "O Estrangeiro", "O Estrangeiro do Mar", "O Viajante", "O Peregrino",
            "O Errante", "O Nômade", "O Exilado", "O Banido", "O Proscrito",
            "O Renegado", "O Desertor", "O Fugitivo", "O Caçado", "O Caçador",
            "O Predador", "O Presa", "O Algoz", "O Vítima", "O Algoz das Vítimas",
            "O Bicho-Papão", "O Pesadelo", "O Sonho", "O Pesadelo dos Mares",
            "O Terror dos Sete Mares", "O Terror do Caribe", "O Terror do Atlântico",
            "O Flagelo dos Mares", "O Flagelo de Deus", "O Flagelo do Mar",
            "O Anjo Vingador", "O Anjo da Morte", "O Anjo do Mar",
            "O Filho da Morte", "O Filho do Diabo", "O Filho de Deus",
            "O Neto do Diabo", "O Irmão do Diabo", "O Primo do Diabo",
        ]

        nomes = [
            # ===== ORIGINAIS =====
            "Morgan", "Zane", "Bones", "Kraken", "Vane",
            "Thatch", "Bartholomew", "Jack", "Drake", "Flint",
            "Teach", "Ragnar", "Silvers", "Kidd", "Hawkins",

            # ===== CLÁSSICOS PIRATAS =====
            "Blackbeard", "Calico", "Rackham", "Bonny", "Read",
            "Roberts", "Avery", "Bellamy", "Hornigold", "Sparrow",
            "Barbossa", "Davy", "Jones", "Hook", "Smee",
            "Bonnet", "England", "Low", "Lowther", "Taylor",
            "Tew", "Every", "Condent", "Fly", "Davis",
            "Williams", "Anstis", "Fenn", "Ward",

            # ===== NOMES MEDIEVAIS / CELTAS =====
            "Cormac", "Alistair", "Duncan", "Fergus", "Ewan",
            "Gideon", "Silas", "Ezra", "Malachi", "Amos",
            "Tobias", "Elias", "Caleb", "Josiah", "Levi",
            "Ronan", "Cedric", "Alaric", "Bram", "Gunnar",
            "Soren", "Bjorn", "Erik", "Leif", "Magnus",
            "Ragnvald", "Harald", "Olaf", "Sven", "Ivar",
            "Ulf", "Rolf", "Sigurd", "Hakon", "Halfdan",
            "Aiden", "Brennan", "Cian", "Declan", "Eamon",
            "Fionn", "Gareth", "Hugh", "Ivor", "Kieran",
            "Lorcan", "Maddox", "Niall", "Oisin", "Padraig",
            "Quinn", "Rowan", "Seamus", "Tadhg", "Uilliam",

            # ===== NOMES BÍBLICOS / ANTIGOS =====
            "Abraham", "Isaac", "Jacob", "Moses", "Joshua",
            "Samuel", "Saul", "David", "Solomon", "Rehoboam",
            "Jeroboam", "Ahab", "Jehu", "Hezekiah", "Josiah",
            "Jeremiah", "Isaiah", "Ezekiel", "Daniel", "Hosea",
            "Joel", "Obadiah", "Jonah", "Micah", "Nahum",
            "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
            "Matthew", "Mark", "Luke", "John", "Peter",
            "Paul", "James", "Andrew", "Thomas", "Philip",
            "Simon", "Judas", "Matthias",

            # ===== SOBRENOMES COMO NOMES =====
            "Blackwood", "Storm", "Ashford", "Grimm", "Cross",
            "Bane", "Crow", "Wolfe", "Stone", "Steele",
            "Frost", "Thorne", "Vale", "Graves", "Rivers",
            "Blackwater", "Blackstone", "Blackheart", "Blackmane",
            "Stormrider", "Stormbringer", "Stormwind", "Thunder", "Lightning",
            "Ash", "Ember", "Flame", "Blaze", "Scorch",
            "Ice", "Snow", "Winter", "Cold",
            "Shadow", "Shade", "Dark", "Night", "Dusk",
            "Dawn", "Light", "Sun", "Moon", "Star",

            # ===== NOMES EXÓTICOS / INTERNACIONAIS =====
            "Salazar", "Vega", "Cortez", "Rojas", "Mendoza",
            "Kuro", "Jin", "Ryu", "Sato", "Tanaka",
            "Amara", "Zara", "Nadia", "Kira", "Sasha",
            "Ismail", "Rashid", "Karim", "Omar", "Hakim",
            "Ali", "Hassan", "Hussein", "Ibrahim", "Yusuf",
            "Diego", "Rodrigo", "Alonso", "Hernan", "Pizarro",
            "Balboa", "Magellan", "Columbus", "Vespucci", "Cabot",
            "Raleigh", "Frobisher", "Hudson",
            "Cook", "Bligh", "Nelson", "Hood", "Rodney",

            # ===== NOMES CURTOS / FORTES =====
            "Rex", "Dax", "Max", "Jax", "Kai",
            "Ryo", "Ren", "Ken", "Ace",
            "Bran", "Cain", "Dane", "Finn",
            "Grey", "Hale", "Ike", "Jude", "Kane",
            "Lars", "Mace", "Nash", "Odin", "Pike",
            "Quill", "Rhys", "Sage", "Tate",
            "Vex", "Wade", "Xander", "Yale", "Zeke",

            # ===== NOMES FEMININOS (piratas lendárias) =====
            "Anne", "Mary", "Grace", "Ching", "Zheng",
            "Rachel", "Charlotte", "Eleanor", "Isabel", "Catalina",
            "Shih", "Cheng",
            "Morrigan", "Freya", "Helga", "Astrid", "Ingrid",
            "Sigrid", "Brenna", "Kara", "Lyra", "Nyx",

            # ===== NOMES COM APELIDO EMBUTIDO =====
            "Black Jack", "Red Jack", "Mad Jack", "Calico Jack", "Dread Pirate",
            "Black Sam", "Long Ben", "Gentleman Jim", "Scurvy Bob", "Blind Pew",
            "Peg Leg", "Iron Mike", "Steel Sam", "Bloody Bob", "Cutthroat Carl",
            "Scarface", "One-Eye", "Three-Fingers", "Nine-Toes", "Half-Hand",
            "Stump", "Peg", "Crutch", "Splinter",

            # ===== NOMES INVENTADOS / FANTASIA =====
            "Zephyr", "Zephyros", "Aeolus", "Boreas", "Notus",
            "Eurus", "Triton", "Poseidon", "Neptune", "Nereus",
            "Proteus", "Glaucus", "Phorcys", "Ceto", "Thaumas",
            "Leviathan", "Jormungandr", "Fenrir", "Nidhogg",
            "Aegir", "Ran", "Njord", "Tyr", "Loki",
            "Baldur", "Heimdall", "Vidar", "Vali", "Ullr",
            "Forseti", "Bragi", "Idunn", "Sif", "Skadi",

            # ===== NOVOS: NÓRDICOS / VIKINGS =====
            "Thorvald", "Thorstein", "Thorolf", "Thorir", "Thorbjorn",
            "Gunnbjorn", "Gunnolf", "Grim", "Grimar", "Grimolf",
            "Ketil", "Ketilbjorn", "Snorri", "Snorri", "Steinar",
            "Steinbjorn", "Steinulf", "Thorvald", "Thorleif", "Thorkel",
            "Eirik", "Eirikur", "Hrafn", "Hrafnkel", "Ketill",
            "Ingvar", "Ingimund", "Ingolf", "Viggo", "Vigfus",
            "Vigbjorn", "Vigmund", "Vigsterk", "Vighvat", "Vigmar",
            "Hrolf", "Hrolfr", "Hroar", "Hrani", "Hreidar",
            "Hreinn", "Hring", "Hroald", "Hrodgeir", "Hroar",

            # ===== NOVOS: GREGOS / ROMANOS =====
            "Achilles", "Ajax", "Odysseus", "Hector", "Paris",
            "Priam", "Agamemnon", "Menelaus", "Diomedes", "Nestor",
            "Patroclus", "Antilochus", "Idomeneus", "Meriones", "Teucer",
            "Aeneas", "Ascanius", "Anchises", "Latinus", "Turnus",
            "Romulus", "Remus", "Numitor", "Amulius", "Aventinus",
            "Aventinus", "Tiberinus", "Faunus", "Picus", "Saturnus",
            "Janus", "Mars", "Vulcan", "Pluto", "Apollo",
            "Bacchus", "Mercury", "Hercules", "Perseus", "Theseus",
            "Jason", "Orpheus", "Bellerophon", "Cadmus", "Peleus",

            # ===== NOVOS: EGÍPCIOS / AFRICANOS =====
            "Ramses", "Tutankhamun", "Akhenaten", "Thutmose", "Hatshepsut",
            "Nefertiti", "Cleopatra", "Nefertari", "Narmer", "Menes",
            "Khufu", "Khafre", "Menkaure", "Sneferu", "Djoser",
            "Imhotep", "Anubis", "Osiris", "Horus", "Set",
            "Sobek", "Thoth", "Ra", "Amun", "Ptah",
            "Shaka", "Zulu", "Mansa", "Musa", "Sundiata",
            "Toussaint", "Dessalines", "Boukman", "Makandal", "Ogou",

            # ===== NOVOS: ORIENTAIS =====
            "Takeda", "Uesugi", "Oda", "Toyotomi", "Tokugawa",
            "Date", "Mori", "Shimazu", "Hojo", "Imagawa",
            "Miyamoto", "Musashi", "Kojiro", "Yagyu", "Ito",
            "Sun", "Wu", "Yue", "Cao", "Liu",
            "Guan", "Zhang", "Zhao", "Ma", "Huang",
            "Chen", "Lin", "Wang", "Li", "Zhou",
            "Wei", "Han", "Qin", "Tang", "Song",
            "Yi", "Sejong", "Gwanggaeto", "Eulji", "Kim",
            "Genghis", "Kublai", "Batu", "Subutai", "Tamerlane",

            # ===== NOVOS: ÁRABES / PERSAS =====
            "Sinbad", "Aladdin", "Ali", "Harun", "Al-Rashid",
            "Saladin", "Baibars", "Qalawun", "Nur", "Baybars",
            "Khalid", "Tariq", "Musa", "Yusuf", "Suleiman",
            "Mehmed", "Selim", "Bayezid", "Murad", "Orhan",
            "Osman", "Ertugrul", "Turgut", "Barbarossa", "Hayreddin",
            "Cyrus", "Darius", "Xerxes", "Artaxerxes", "Cambyses",
            "Arsaces", "Mithridates", "Shapur", "Khosrow", "Yazdegerd",

            # ===== NOVOS: NOMES DE FAMÍLIA PIRATA =====
            "Blackwood", "Bloodworth", "Bloodgood", "Bloodaxe", "Bloodworth",
            "Cutler", "Cutthroat", "Cutlass", "Cuthbert", "Cutler",
            "Dagger", "Daggers", "Daggett", "Dagon", "Dagmar",
            "Fletcher", "Flintlock", "Flintstone", "Flintwood", "Flintheart",
            "Gunn", "Gunnar", "Gunnarson", "Gunther", "Gunhild",
            "Hacker", "Hackett", "Hackman", "Hacksaw", "Hackworth",
            "Ironwood", "Ironheart", "Ironfist", "Ironhand", "Ironfoot",
            "Ketch", "Ketcher", "Ketchum", "Ketchworth", "Ketcham",
            "Locker", "Lockwood", "Lockheart", "Lockman", "Lockridge",
            "Mast", "Master", "Masterson", "Mastwood", "Masterson",
            "Pike", "Piker", "Pikeman", "Pikewood", "Pikeheart",
            "Quill", "Quiller", "Quillman", "Quillworth", "Quillheart",
            "Rigger", "Rigging", "Riggs", "Rigby", "Rigley",
            "Sailor", "Saylor", "Saylor", "Sailor", "Sailor",
            "Timber", "Timberland", "Timberlake", "Timberman", "Timberwood",
            "Anchor", "Anchorman", "Anchorwood", "Anchorheart", "Anchorstone",

            # ===== NOVOS: NOMES DE ANIMAIS COMO SOBRENOME =====
            "Wolfsbane", "Wolfson", "Wolfwood", "Wolfheart", "Wolfstone",
            "Foxworth", "Foxwood", "Foxheart", "Foxman", "Foxley",
            "Hawkeye", "Hawksworth", "Hawkwood", "Hawkheart", "Hawkman",
            "Ravenscroft", "Ravenwood", "Ravenheart", "Ravenman", "Ravensworth",
            "Crowley", "Crowson", "Crowwood", "Crowheart", "Crowman",
            "Falconer", "Falconwood", "Falconheart", "Falconman", "Falconbridge",
            "Bearwood", "Bearheart", "Bearman", "Bearson", "Bearstone",
            "Lionheart", "Lionwood", "Lionman", "Lionson", "Lionstone",
            "Tigerwood", "Tigerheart", "Tigerman", "Tigerson", "Tigerstone",
            "Serpentine", "Serpentwood", "Serpentheart", "Serpentman", "Serpentson",
            "Dragonwood", "Dragonheart", "Dragonman", "Dragonson", "Dragonstone",
            "Sharkwood", "Sharkheart", "Sharkman", "Sharkson", "Sharkstone",
            "Whalebone", "Whalewood", "Whaleheart", "Whaleman", "Whaleson",

            # ===== NOVOS: NOMES DE ARMAS =====
            "Blade", "Bladewood", "Bladeheart", "Blademan", "Bladeson",
            "Sword", "Swordwood", "Swordheart", "Swordman", "Swordson",
            "Saber", "Saberwood", "Saberheart", "Saberman", "Saberson",
            "Rapier", "Rapierwood", "Rapierheart", "Rapierman", "Rapierstone",
            "Cutlass", "Cutlasswood", "Cutlassheart", "Cutlassman", "Cutlasson",
            "Dagger", "Daggerwood", "Daggerheart", "Daggerman", "Daggerson",
            "Axe", "Axewood", "Axeheart", "Axeman", "Axeson",
            "Hammer", "Hammerwood", "Hammerheart", "Hammerman", "Hammerson",
            "Spear", "Spearwood", "Spearheart", "Spearman", "Spearson",
            "Bow", "Bowwood", "Bowheart", "Bowman", "Bowson",
            "Arrow", "Arrowwood", "Arrowheart", "Arrowman", "Arrowson",
            "Cannon", "Cannonwood", "Cannonheart", "Cannonman", "Cannonson",
            "Musket", "Musketwood", "Musketheart", "Musketman", "Musketson",
            "Pistol", "Pistolwood", "Pistolheart", "Pistolman", "Pistolson",

            # ===== NOVOS: NOMES DE LUGARES =====
            "Tortuga", "Nassau", "Portobello", "Cartagena", "Maracaibo",
            "Havana", "Santiago", "Kingston", "Bridgetown", "Portsmouth",
            "Bristol", "Liverpool", "London", "Dover", "Plymouth",
            "Amsterdam", "Rotterdam", "Antwerp", "Bruges", "Ghent",
            "Lisbon", "Porto", "Cadiz", "Seville", "Barcelona",
            "Venice", "Genoa", "Naples", "Marseille", "Toulon",
            "Algiers", "Tunis", "Tripoli", "Alexandria", "Cairo",
            "Mogadishu", "Zanzibar", "Malindi", "Mombasa", "Sofala",
            "Goa", "Calicut", "Malacca", "Batavia", "Macau",

            # ===== NOVOS: NOMES DE NAVIOS =====
            "Revenge", "Victory", "Conqueror", "Defiance", "Resolute",
            "Vengeance", "Retribution", "Justice", "Liberty", "Freedom",
            "Sea Wolf", "Sea Serpent", "Sea Dragon", "Sea Hawk", "Sea Eagle",
            "Black Pearl", "Black Widow", "Black Death", "Black Plague", "Black Fury",
            "Red Dawn", "Red Storm", "Red Tide", "Red Blood", "Red Fire",
            "White Whale", "White Shark", "White Wolf", "White Death", "White Ghost",
            "Golden Hind", "Golden Dragon", "Golden Lion", "Golden Eagle", "Golden Phoenix",
            "Silver Bullet", "Silver Arrow", "Silver Sword", "Silver Star", "Silver Moon",
            "Storm Chaser", "Storm Rider", "Storm Breaker", "Storm Bringer", "Storm Caller",
            "Night Raven", "Night Stalker", "Night Hunter", "Night Shadow", "Night Terror",
            "Blood Moon", "Blood Hound", "Blood Eagle", "Blood Raven", "Blood Wolf",
            "Iron Maiden", "Iron Fist", "Iron Will", "Iron Heart", "Iron Soul",
            "Fire Storm", "Fire Drake", "Fire Bird", "Fire Fly", "Fire Brand",
            "Ice Breaker", "Ice Queen", "Ice King", "Ice Wolf", "Ice Bear",

            # ===== NOVOS: NOMES DE MITOLOGIA GREGA =====
            "Zeus", "Hades", "Poseidon", "Apollo", "Ares",
            "Hermes", "Hephaestus", "Dionysus", "Pan", "Eros",
            "Heracles", "Perseus", "Theseus", "Jason", "Achilles",
            "Odysseus", "Ajax", "Diomedes", "Hector", "Paris",
            "Atlas", "Prometheus", "Epimetheus", "Cronus", "Uranus",
            "Titan", "Hyperion", "Oceanus", "Coeus", "Crius",
            "Iapetus", "Themis", "Rhea", "Tethys", "Phoebe",
            "Mnemosyne", "Theia", "Leto", "Asteria", "Metis",

            # ===== NOVOS: NOMES DE MITOLOGIA NÓRDICA =====
            "Odin", "Thor", "Loki", "Freyr", "Tyr",
            "Baldr", "Hodr", "Vidar", "Vali", "Ullr",
            "Heimdall", "Bragi", "Forseti", "Njord", "Aegir",
            "Hel", "Fenrir", "Jormungandr", "Nidhogg", "Sleipnir",
            "Huginn", "Muninn", "Geri", "Freki", "Skoll",
            "Hati", "Ratatoskr", "Vedrfolnir", "Nidhug", "Fafnir",
            "Sigurd", "Siegfried", "Beowulf", "Hrolf", "Ragnar",
            "Bjorn", "Ivar", "Ubbe", "Halfdan", "Sigurd",

            # ===== NOVOS: NOMES DE MITOLOGIA CELTA =====
            "Cernunnos", "Dagda", "Lugh", "Nuada", "Ogma",
            "Brigid", "Morrigan", "Badb", "Nemain", "Macha",
            "Danu", "Lir", "Manannan", "Aengus", "Midir",
            "Bodb", "Aine", "Cliodhna", "Aoife", "Scathach",
            "Fionn", "Oisin", "Oscar", "Caoilte", "Goll",
            "Conall", "Cuchulainn", "Ferdiad", "Loch", "Laeg",
            "Bran", "Bres", "Tuatha", "Firbolg", "Fomorian",

            # ===== NOVOS: NOMES DE MITOLOGIA JAPONESA =====
            "Susanoo", "Amaterasu", "Tsukuyomi", "Izanagi", "Izanami",
            "Raijin", "Fujin", "Inari", "Hachiman", "Benzaiten",
            "Bishamonten", "Daikokuten", "Ebisu", "Fukurokuju", "Jurojin",
            "Hotei", "Kannon", "Jizo", "Emma", "Yama",
            "Oni", "Tengu", "Kappa", "Kitsune", "Tanuki",
            "Ryu", "Tatsu", "Orochi", "Yamata", "Kirin",

            # ===== NOVOS: NOMES DE MITOLOGIA EGÍPCIA =====
            "Ra", "Osiris", "Isis", "Horus", "Set",
            "Anubis", "Thoth", "Sekhmet", "Hathor", "Bastet",
            "Sobek", "Khnum", "Ptah", "Amun", "Mut",
            "Khonsu", "Montu", "Sopdu", "Wepwawet", "Anhur",
            "Nephthys", "Nut", "Geb", "Shu", "Tefnut",
            "Apep", "Ammit", "Babi", "Bes", "Hapi",

            # ===== NOVOS: NOMES DE MITOLOGIA ASTECA / MAIA =====
            "Quetzalcoatl", "Tezcatlipoca", "Huitzilopochtli", "Xipe", "Tlaloc",
            "Mictlantecuhtli", "Xolotl", "Xiuhtecuhtli", "Tonatiuh", "Metztli",
            "Coatlicue", "Cihuacoatl", "Tlazolteotl", "Xochiquetzal", "Mayahuel",
            "Itzamna", "Kukulkan", "Chaac", "Yum", "Ah",
            "Hunahpu", "Xbalanque", "Hun", "Vucub", "Zipacna",

            # ===== NOVOS: NOMES DE MITOLOGIA HINDU =====
            "Shiva", "Vishnu", "Brahma", "Indra", "Agni",
            "Varuna", "Vayu", "Yama", "Kubera", "Surya",
            "Chandra", "Ganesha", "Kartikeya", "Hanuman", "Rama",
            "Krishna", "Arjuna", "Bhima", "Yudhishthira", "Nakula",
            "Sahadeva", "Karna", "Duryodhana", "Drona", "Bhishma",
            "Ravana", "Kumbhakarna", "Vibhishana", "Sugriva", "Vali",

            # ===== NOVOS: NOMES DE FANTASIA / INVENTADOS =====
            "Aerith", "Aerion", "Aerith", "Aerith", "Aerith",
            "Zephyrion", "Zephyros", "Zephyrin", "Zephyrion", "Zephyrion",
            "Kael", "Kaelan", "Kaelen", "Kaelin", "Kaelor",
            "Thalion", "Thalor", "Thalos", "Thalos", "Thalos",
            "Draven", "Dravenor", "Dravenis", "Dravenar", "Dravenor",
            "Kaelthas", "Kaelthar", "Kaelthor", "Kaelthos", "Kaelthus",
            "Vexar", "Vexarian", "Vexarion", "Vexarius", "Vexarion",
            "Nyxar", "Nyxarian", "Nyxarion", "Nyxarius", "Nyxarion",
            "Zephar", "Zepharian", "Zepharion", "Zepharius", "Zepharion",
            "Krynn", "Krynna", "Krynnis", "Krynnar", "Krynnor",
            "Aethon", "Aethonar", "Aethonis", "Aethonor", "Aethonus",
            "Pyrrhus", "Pyrrhon", "Pyrrhos", "Pyrrhus", "Pyrrhos",
            "Xanthos", "Xanthar", "Xanthor", "Xanthis", "Xanthus",
            "Orin", "Orion", "Orik", "Orim", "Oris",
            "Varek", "Varen", "Vares", "Vareth", "Varex",
            "Thane", "Thanor", "Thanis", "Thanar", "Thanos",
            "Kael", "Kaen", "Kaer", "Kaes", "Kaeth",
            "Ryn", "Rynar", "Rynis", "Rynor", "Rynus",
            "Zar", "Zarek", "Zaren", "Zares", "Zareth",
            "Vor", "Vorek", "Voren", "Vores", "Voreth",
            "Drak", "Draken", "Drakes", "Draketh", "Drakon",
            "Kro", "Kron", "Kronar", "Kronis", "Kronos",
            "Mor", "Morek", "Moren", "Mores", "Moreth",
            "Tor", "Torek", "Toren", "Tores", "Toreth",
            "Fen", "Fenek", "Fenen", "Fenes", "Feneth",
            "Gal", "Galek", "Galen", "Gales", "Galeth",
            "Hal", "Halek", "Halen", "Hales", "Haleth",
            "Jor", "Jorek", "Joren", "Jores", "Joreth",
            "Kel", "Kelek", "Kelen", "Keles", "Kelth",
            "Lor", "Lorek", "Loren", "Lores", "Loreth",
            "Mal", "Malek", "Malen", "Males", "Maleth",
            "Nal", "Nalek", "Nalen", "Nales", "Naleth",
            "Pal", "Palek", "Palen", "Pales", "Paleth",
            "Ral", "Ralek", "Ralen", "Rales", "Raleth",
            "Sal", "Salek", "Salen", "Sales", "Saleth",
            "Tal", "Talek", "Talen", "Tales", "Taleth",
            "Val", "Valek", "Valen", "Vales", "Valeth",
            "Xal", "Xalek", "Xalen", "Xales", "Xaleth",
            "Zal", "Zalek", "Zalen", "Zales", "Zaleth",
        ]

        prefixos = [
            "Capitão", "Almirante", "Lorde", "Barão", "Comodoro", "Sir",
            "General", "Coronel", "Comandante", "Tenente", "Sargento",
            "Rei", "Rainha", "Príncipe", "Princesa", "Duque", "Duquesa",
            "Conde", "Condessa", "Visconde", "Marquês", "Czar", "Sultão",
            "Xerife", "Juiz", "Papa", "Bispo", "Cardeal", "Padre",
            "Mestre", "Grão-Mestre", "Chefe", "Líder", "Chefão",
            "Dread", "Old", "Young", "Mad", "Crazy", "Wild",
            "Black", "Red", "White", "Grey", "Dark", "Bright",
        ]

        sufixos = [
            "do Caribe", "do Atlântico", "do Pacífico", "do Norte", "do Sul",
            "do Leste", "do Oeste", "das Índias", "das Antilhas", "de Tortuga",
            "de Nassau", "de Port Royal", "de Madagascar", "da Ilha Caveira",
            "do Mar Vermelho", "do Mar Negro", "do Fim do Mundo", "do Inferno",
            "dos Sete Mares", "das Tempestades", "das Profundezas", "do Abismo",
            "da Morte", "da Guerra", "da Fome", "da Peste", "do Caos",
        ]

        nome = random.choice(nomes)
        titulo = random.choice(titulos)

        if random.random() < 0.35:
            nome = f"{random.choice(prefixos)} {nome}"

        if random.random() < 0.25:
            titulo = f"{titulo} {random.choice(sufixos)}"

        self.var_nome.set(f"{nome} {titulo}")

    def lancar_bando_tracker(self):
        membros = list(self.listbox_bando.get(0, tk.END))
        if not membros: return
        
        # Lança o Chefe
        ini_chefe = random.randint(1, 20) + self.var_agi.get()
        self.app_master.tracker_data.append({"ini": ini_chefe, "id": "chefe", "nome": self.var_nome.get(), "status": "👑 Chefe"})
        self.app_master.registrar_log(f"Iniciativa 👑 [{self.var_nome.get()}]: {ini_chefe}")

        # Lança o Bando
        for m in membros:
            ini_bando = random.randint(1, 20)
            nome_limpo = re.sub(r" \[Lv\. .*?\]$", "", m) # Remove o [Lv. 1] caso venha junto
            self.app_master.tracker_data.append({"ini": ini_bando, "id": "bando", "nome": nome_limpo, "status": "🛡️ Lacaio"})
            self.app_master.registrar_log(f"Iniciativa 🛡️ [{nome_limpo}]: {ini_bando}")
            
        self.app_master.atualizar_tracker_view()

    def exportar_markdown(self):
        caminho = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")], title="Salvar Ficha Markdown")
        if not caminho: return
        
        dados = self.get_dados()
        bounty_str = dados['recompensa'] + " Berries" if dados['recompensa'] else "0 Berries"
        md = f"# {dados['nome']}\n**Nível:** {dados['nivel']} | **Recompensa:** {bounty_str}\n"
        md += f"**PV:** {dados['pv']} | **PE:** {dados['pe']}\n\n"
        md += "## Atributos\n"
        md += f"- **Físico:** {dados['fis']} | **Agilidade:** {dados['agi']} | **Intelecto:** {dados['int']} | **Instinto:** {dados['inst']}\n"
        md += f"- **Grau Luta:** {dados['luta']} | **Grau Acro:** {dados['acro']}\n\n"
        md += "## Loot e Drops\n" + dados['loot'] + "\n\n"
        md += "## Habilidades\n"
        for hab in dados['habilidades']:
            md += f"### {hab['titulo']}\n"
            md += f"*Custo:* {hab['custo']} | *Limite:* {hab['limite']} | *Execução:* {hab['execucao']} | *Alcance:* {hab['alcance']}\n"
            md += f"{hab['conteudo']}\n\n"
        md += "## Notas e História\n" + dados['historia']
        
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(md)
            messagebox.showinfo("Sucesso", "Ficha exportada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")

    def abrir_modo_jogador(self):
        top = ctk.CTkToplevel(self)
        top.title(f"Apresentação - {self.var_nome.get()}")
        top.geometry("600x700")
        top.configure(bg=self.tema["bg_main"])
        top.attributes("-topmost", True)
        
        ctk.CTkLabel(top, text=self.var_nome.get(), font=(self.app_master.current_font, 28, "bold"), text_color=self.tema["accent"]).pack(pady=20)
        
        if self.imagem_original:
            w, h = self.imagem_original.size
            escala = 400 / max(w, h)
            img_resized = self.imagem_original.resize((int(w*escala), int(h*escala)), Image.Resampling.LANCZOS)
            foto_toplevel = ImageTk.PhotoImage(img_resized)
            lbl_img = tk.Label(top, image=foto_toplevel, bg=self.tema["bg_main"])
            lbl_img.image = foto_toplevel 
            lbl_img.pack(expand=True)
        else:
            ctk.CTkLabel(top, text="[ Sem Imagem ]", font=self.app_master.get_font('title'), text_color="#8b8c8f").pack(expand=True)

    def gerar_ia_local(self):
        prompt = f"Um inimigo chamado {self.var_nome.get()} focando em Físico {self.var_fis.get()}..."
        bounty_str = self.var_recompensa.get() + " Berries"
        historia_gerada = f"[{prompt}]\n\nNascido nos mares remotos, {self.var_nome.get()} desenvolveu uma força física formidável ({self.var_fis.get()}) lutando contra bestas marinhas. Sua recompensa de {bounty_str} reflete a ameaça que representa para os desavisados. Em combate, prefere usar abordagens brutais e táticas de força bruta para subjugar os inimigos antes que possam reagir."
        self.texto_historia.insert(tk.END, "\n\n--- IA Gerada ---\n" + historia_gerada)

    def carregar_imagem(self):
        caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.webp")])
        if caminho:
            try:
                self.caminho_imagem_salva = caminho
                self.imagem_original = Image.open(self.caminho_imagem_salva)
                self.escala_imagem = 180 / max(self.imagem_original.width, self.imagem_original.height)
                self.img_x, self.img_y = 90, 90
                self.atualizar_imagem()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao processar imagem.\n{str(e)}")

    def atualizar_imagem(self):
        if not self.imagem_original: return
        w, h = self.imagem_original.size
        novo_w = max(10, int(w * self.escala_imagem))
        novo_h = max(10, int(h * self.escala_imagem))
        img_resized = self.imagem_original.resize((novo_w, novo_h), Image.Resampling.LANCZOS)
        self.foto = ImageTk.PhotoImage(img_resized)
        self.canvas_img.delete("all")
        self.canvas_img.create_image(self.img_x, self.img_y, image=self.foto)

    def iniciar_arraste(self, event):
        self.last_mouse_x, self.last_mouse_y = event.x, event.y

    def arrastar_imagem(self, event):
        if not self.imagem_original: return
        self.img_x += event.x - self.last_mouse_x
        self.img_y += event.y - self.last_mouse_y
        self.last_mouse_x, self.last_mouse_y = event.x, event.y
        self.atualizar_imagem()

    def zoom_imagem(self, event):
        if not self.imagem_original: return
        if event.delta > 0 and self.escala_imagem < 10.0: self.escala_imagem *= 1.1 
        elif event.delta < 0 and self.escala_imagem > 0.05: self.escala_imagem *= 0.9
        self.atualizar_imagem()

    def inserir_habilidade(self, patamar):
        templates = {
            "Básica": {"custo": "0 PE", "limite": "+2", "execucao": "1 Ação", "alcance": "Corpo a corpo"},
            "Média": {"custo": "1 PE", "limite": "+3", "execucao": "1 Ação", "alcance": "9 m"},
            "Forte": {"custo": "3 PE", "limite": "+4", "execucao": "1 Ação", "alcance": "Cone 4,5m"},
            "Suprema": {"custo": "5 PE", "limite": "+5", "execucao": "1 Ação", "alcance": "Área 6m"},
            "Outros": {"custo": "X PE", "limite": "-", "execucao": "Reação", "alcance": "-"}
        }
        dados = templates.get(patamar, {})
        dados["titulo"] = f"Nova Habilidade - {patamar}"
        dados["conteudo"] = ""
        bloco = HabilidadeBloco(self.frame_lista_hab, dados, self.canvas_hab, self.painel_direito, self.app_master)
        self.blocos_habilidades.append(bloco)

    def filtrar_habilidades(self, escolha=None):
        escolha = self.var_filtro_hab.get().lower()
        # Esconde todas primeiro
        for bloco in self.blocos_habilidades:
            if bloco.winfo_exists():
                bloco.pack_forget()
                
        # Mostra apenas as que batem com o filtro mantendo a ordem
        for bloco in self.blocos_habilidades:
            if not bloco.winfo_exists(): continue
            titulo = bloco.var_titulo.get().lower()
            execucao = bloco.var_exec.get().lower()
            
            if escolha == "todas" or escolha in titulo or escolha in execucao:
                bloco.pack(fill=tk.X, pady=8, padx=10)

    # Note que na sua função inserir_habilidade existente, adicione estas 2 linhas no final dela:
    # self.var_filtro_hab.set("Todas")
    # self.filtrar_habilidades()

    def get_dados(self):
        habs = [b.get_dados() for b in self.blocos_habilidades if b.winfo_exists()]
        return {
            "nome": self.var_nome.get(),
            "recompensa": self.var_recompensa.get().replace(".", ""), 
            "pv": self.pv_atual.get(),
            "pe": self.pe_atual.get(),
            "nivel": self.var_nivel.get(),
            "fis": self.var_fis.get(),
            "agi": self.var_agi.get(),
            "int": self.var_int.get(),
            "inst": self.var_inst.get(),
            "luta": self.var_luta.get(),
            "acro": self.var_acro.get(),
            "mod_passiva": self.mod_passiva.get(),
            "mod_bloq": self.mod_bloq.get(),
            "mod_esq": self.mod_esq.get(),
            "mod_cd": self.mod_cd.get(),
            "historia": self.texto_historia.get("1.0", tk.END).strip(),
            "loot": self.texto_loot.get("1.0", tk.END).strip(),
            "bando": list(self.listbox_bando.get(0, tk.END)),
            "imagem": self.caminho_imagem_salva,
            "escala": self.escala_imagem,
            "img_x": self.img_x,
            "img_y": self.img_y,
            "habilidades": habs
        }

    def carregar_dados(self, d):
        self.var_nome.set(d.get("nome", "Novo Inimigo"))
        recomp_salva = d.get("recompensa", "0")
        self.var_recompensa.set(f"{int(recomp_salva):,}".replace(",", ".") if str(recomp_salva).isdigit() else "0")
        
        self.pv_atual.set(d.get("pv", 100))
        self.pe_atual.set(d.get("pe", 20))
        self.var_nivel.set(d.get("nivel", "1"))
        self.var_fis.set(d.get("fis", 1))
        self.var_agi.set(d.get("agi", 1))
        self.var_int.set(d.get("int", 1))
        self.var_inst.set(d.get("inst", 1))
        self.var_luta.set(d.get("luta", 0))
        self.var_acro.set(d.get("acro", 0))
        
        self.mod_passiva.set(d.get("mod_passiva", 0))
        self.mod_bloq.set(d.get("mod_bloq", 0))
        self.mod_esq.set(d.get("mod_esq", 0))
        self.mod_cd.set(d.get("mod_cd", 0))

        self.texto_historia.insert(tk.END, d.get("historia", ""))
        self.texto_loot.insert(tk.END, d.get("loot", ""))
        
        self.listbox_bando.delete(0, tk.END)
        for minion in d.get("bando", []):
            self.listbox_bando.insert(tk.END, minion)

        if d.get("imagem") and os.path.exists(d["imagem"]):
            try:
                self.caminho_imagem_salva = d["imagem"]
                self.imagem_original = Image.open(self.caminho_imagem_salva)
                self.escala_imagem = d.get("escala", 1.0)
                self.img_x, self.img_y = d.get("img_x", 90), d.get("img_y", 90)
                self.atualizar_imagem()
            except Exception:
                self.canvas_img.create_text(90, 90, text="[ Imagem Ausente ]", fill="#8b8c8f")

        for hab in d.get("habilidades", []):
            bloco = HabilidadeBloco(self.frame_lista_hab, hab, self.canvas_hab, self.painel_direito, self.app_master)
            self.blocos_habilidades.append(bloco)


class GerenciadorAmeasApp:
    def __init__(self, root):
        self.root = root
        self.arquivo_atual = None
        
        self.tema_atual = TEMAS["Obsidian (Padrão)"]
        self.current_font = "Segoe UI"
        
        self.atualizar_titulo()
        self.root.geometry("1300x800")
        self.root.configure(bg=self.tema_atual["bg_sidebar"])

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.aplicar_tema_style()

        self.dados_banco = {} 
        self.tracker_data = []

        self.montar_menus()
        self.montar_layout_principal()
        self.inicializar_arvore_padrao()

    def get_font(self, type_style="main"):
        if type_style == "bold": return (self.current_font, 12, "bold")
        if type_style == "title": return (self.current_font, 16, "bold")
        if type_style == "small": return (self.current_font, 10)
        return (self.current_font, 12)

    def aplicar_tema_style(self):
        self.style.configure("Treeview", background=self.tema_atual["bg_sidebar"], foreground=self.tema_atual["text"], fieldbackground=self.tema_atual["bg_sidebar"], borderwidth=0, font=self.get_font('main'), rowheight=32)
        self.style.map("Treeview", background=[('selected', self.tema_atual["accent"])], foreground=[('selected', 'white')])
        self.style.configure("TNotebook", background=self.tema_atual["bg_sidebar"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.tema_atual["bg_sidebar"], foreground="#8b8c8f", padding=[20, 8], font=self.get_font('main'), borderwidth=0)
        self.style.map("TNotebook.Tab", background=[('selected', self.tema_atual["bg_main"])], foreground=[('selected', self.tema_atual["text"])])

    def atualizar_titulo(self):
        if self.arquivo_atual:
            nome = os.path.basename(self.arquivo_atual)
            self.root.title(f"Cofre de Ameaças - One Piece RPG | {nome}")
        else:
            self.root.title("Cofre de Ameaças - One Piece RPG | Sem Título")

    def mudar_tema(self, escolha):
        self.tema_atual = TEMAS[escolha]
        self.root.configure(bg=self.tema_atual["bg_sidebar"])
        self.barra_ferramentas.configure(fg_color=self.tema_atual["bg_sidebar"])
        self.frame_tree.configure(fg_color=self.tema_atual["bg_sidebar"])
        self.frame_tracker.configure(fg_color=self.tema_atual["bg_sidebar"])
        self.notebook_frame.configure(fg_color=self.tema_atual["bg_main"])
        self.lista_iniciativa.configure(bg=self.tema_atual["bg_sidebar"], fg=self.tema_atual["text"], selectbackground=self.tema_atual["accent"])
        self.aplicar_tema_style()

    def mudar_fonte(self, escolha):
        self.current_font = escolha
        self.aplicar_tema_style()
        self.lista_iniciativa.configure(font=self.get_font('main'))

    def montar_menus(self):
        self.menu_bar = tk.Menu(self.root, bg="#262626", fg="#dcddde", bd=0)
        self.root.config(menu=self.menu_bar)

        menu_arq = tk.Menu(self.menu_bar, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
        menu_arq.add_command(label="Novo Cofre", command=self.novo_banco)
        menu_arq.add_command(label="Abrir Cofre...", command=self.carregar_banco)
        menu_arq.add_separator()
        menu_arq.add_command(label="Salvar", command=self.salvar_banco)
        menu_arq.add_command(label="Salvar Como...", command=self.salvar_como_banco)
        menu_arq.add_separator()
        menu_arq.add_command(label="Sair", command=self.root.quit)
        self.menu_bar.add_cascade(label="Cofre", menu=menu_arq)

        self.barra_ferramentas = ctk.CTkFrame(self.root, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.barra_ferramentas.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)
        
        self.btn_toggle_tree = ctk.CTkButton(self.barra_ferramentas, text="≡ Pastas", command=self.toggle_tree, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde", width=100)
        self.btn_toggle_tree.pack(side=tk.LEFT)
        self.tree_visivel = True

        var_tema = ctk.StringVar(value="Obsidian (Padrão)")
        menu_temas = ctk.CTkOptionMenu(self.barra_ferramentas, variable=var_tema, values=list(TEMAS.keys()), command=self.mudar_tema, fg_color="#363636", text_color="#dcddde", width=160)
        menu_temas.pack(side=tk.LEFT, padx=(20, 10))

        var_fonte = ctk.StringVar(value="Segoe UI")
        menu_fontes = ctk.CTkOptionMenu(self.barra_ferramentas, variable=var_fonte, values=FONTES_DISPONIVEIS, command=self.mudar_fonte, fg_color="#363636", text_color="#dcddde", width=130)
        menu_fontes.pack(side=tk.LEFT)
        
        self.btn_toggle_tracker = ctk.CTkButton(self.barra_ferramentas, text="≡ Tracker", command=self.toggle_tracker, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde", width=100)
        self.btn_toggle_tracker.pack(side=tk.RIGHT)
        self.tracker_visivel = False

    def mapear_arvore_completa(self, node=""):
        res = []
        for child in self.tree.get_children(node):
            item = self.tree.item(child)
            res.append({
                "id": child,
                "text": item["text"],
                "tags": item["tags"],
                "open": self.tree.item(child, "open"), # Salva se a pasta estava aberta
                "filhos": self.mapear_arvore_completa(child)
            })
        return res

    def pesquisar_arvore(self, *args):
        termo = self.var_pesquisa.get().lower().strip()
        
        # Inicia a busca salvando a árvore atual se não existir cache
        if not hasattr(self, 'arvore_cache') or self.arvore_cache is None:
            self.arvore_cache = self.mapear_arvore_completa("")
            
        if not termo:
            self.tree.delete(*self.tree.get_children())
            self.restaurar_arvore_busca(self.arvore_cache, "")
            self.arvore_cache = None 
            return
            
        def filtrar(nodes, manter_tudo=False):
            result = []
            for n in nodes:
                match_self = termo in n["text"].lower()
                # Se bater, mantém este e força manter todos os filhos (ex: pesquisa "pasta npc")
                if manter_tudo or match_self:
                    n_copy = n.copy()
                    n_copy["filhos"] = filtrar(n["filhos"], manter_tudo=True)
                    result.append(n_copy)
                else:
                    # Se não bater, checa se algum filho bate (pra manter a árvore ligada)
                    filhos_filtrados = filtrar(n["filhos"], manter_tudo=False)
                    if filhos_filtrados:
                        n_copy = n.copy()
                        n_copy["filhos"] = filhos_filtrados
                        result.append(n_copy)
            return result
            
        filtrada = filtrar(self.arvore_cache)
        self.tree.delete(*self.tree.get_children())
        self.restaurar_arvore_busca(filtrada, "", expand=True)

    def restaurar_arvore_busca(self, nos, pai, expand=None):
        for n in nos:
            # Se for uma pesquisa forçada (expand=True), abre. Se não, usa o estado salvo!
            estado_open = expand if expand is not None else n.get("open", False)
            self.tree.insert(pai, "end", iid=n["id"], text=n["text"], tags=n["tags"], open=estado_open)
            self.restaurar_arvore_busca(n["filhos"], n["id"], expand)

    def bloquear_se_buscando(self):
        if self.var_pesquisa.get().strip():
            messagebox.showwarning("Aviso", "Limpe a barra de pesquisa antes de adicionar, excluir ou renomear arquivos.")
            return True
        return False

    def montar_layout_principal(self):
        self.container_principal = ctk.CTkFrame(self.root, fg_color="transparent")
        self.container_principal.pack(fill=tk.BOTH, expand=True)

        self.frame_tree = ctk.CTkFrame(self.container_principal, width=280, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.frame_tree.pack_propagate(False)
        self.frame_tree.pack(side=tk.LEFT, fill=tk.Y)

        topo_tree = ctk.CTkFrame(self.frame_tree, fg_color="transparent")
        topo_tree.pack(fill=tk.X, padx=15, pady=(15, 5))
        ctk.CTkLabel(topo_tree, text="PASTAS", font=("Segoe UI", 12, "bold"), text_color="#8b8c8f").pack(side=tk.LEFT)
        
        self.var_pesquisa = tk.StringVar()
        self.var_pesquisa.trace_add("write", self.pesquisar_arvore)
        ctk.CTkEntry(topo_tree, textvariable=self.var_pesquisa, placeholder_text="🔍 Buscar...", height=24, fg_color="#363636", border_width=0).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10,0))
        
        self.tree = ttk.Treeview(self.frame_tree, selectmode="browse", show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

        self.tree.bind("<ButtonPress-1>", self.iniciar_drag_tree)
        self.tree.bind("<ButtonRelease-1>", self.soltar_drag_tree)
        self.tree.bind("<Button-3>", self.abrir_menu_contexto)
        self.item_arrastado = None

        f_botoes = ctk.CTkFrame(self.frame_tree, fg_color="transparent")
        f_botoes.pack(fill=tk.X, pady=15, padx=15)
        
        ctk.CTkButton(f_botoes, text="+ Pasta", command=self.adicionar_pasta, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="+ Ficha", command=self.adicionar_personagem, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="✎ Renomear", command=self.renomear_item, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="✖ Deletar", command=self.deletar_item, fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75").grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        f_botoes.columnconfigure(0, weight=1)
        f_botoes.columnconfigure(1, weight=1)
        
        self.tree.bind("<Double-1>", self.ao_dar_duplo_clique)

        self.notebook_frame = ctk.CTkFrame(self.container_principal, fg_color=self.tema_atual["bg_main"], corner_radius=0)
        self.notebook_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.notebook = DraggableNotebook(self.notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.abas_abertas = {}

        self.frame_tracker = ctk.CTkFrame(self.container_principal, width=280, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.frame_tracker.pack_propagate(False)
        ctk.CTkLabel(self.frame_tracker, text="COMBAT TRACKER", font=("Segoe UI", 12, "bold"), text_color="#8b8c8f", anchor="w").pack(fill=tk.X, padx=20, pady=(15, 5))
        
        self.lista_iniciativa = tk.Listbox(self.frame_tracker, bg=self.tema_atual["bg_sidebar"], fg=self.tema_atual["text"], font=self.get_font('main'), selectbackground=self.tema_atual["accent"], bd=0, highlightthickness=0)
        self.lista_iniciativa.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self.lista_iniciativa.bind("<Button-3>", self.menu_condicoes_tracker)
        
        f_trk_btn = ctk.CTkFrame(self.frame_tracker, fg_color="transparent")
        f_trk_btn.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkButton(f_trk_btn, text="Adicionar Ficha", command=self.add_tracker, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_trk_btn, text="🎲 Rolar Pasta", command=self.rolar_iniciativa_pasta, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_trk_btn, text="Limpar Tracker", command=self.limpar_tracker, fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75").pack(fill=tk.X, pady=2)

        # NOVO: Interface do Dice Log
        ctk.CTkLabel(self.frame_tracker, text="HISTÓRICO DE ROLAGENS", font=("Segoe UI", 10, "bold"), text_color="#8b8c8f", anchor="w").pack(fill=tk.X, padx=20, pady=(10, 0))
        self.caixa_log = ctk.CTkTextbox(self.frame_tracker, height=130, fg_color="#262626", text_color="#dcddde", font=self.get_font('small'), border_width=0, corner_radius=6)
        self.caixa_log.pack(fill=tk.X, padx=15, pady=(5, 15))
        self.caixa_log.configure(state="disabled")

    def inicializar_arvore_padrao(self):
        cat_m = self.tree.insert("", "end", text=" Monstros", open=True, tags=("pasta",))
        cat_v = self.tree.insert("", "end", text=" Vilões", open=True, tags=("pasta",))
        
        id_arlong = self.tree.insert(cat_v, "end", text=" Arlong", tags=("ficha",))
        self.dados_banco[id_arlong] = {"nome": "Arlong", "pv": 100, "pe": 20, "agi": 3}
        
        id_rei = self.tree.insert(cat_m, "end", text=" Rei dos Mares", tags=("ficha",))
        self.dados_banco[id_rei] = {"nome": "Rei dos Mares", "pv": 100, "pe": 20, "agi": 1}

    def abrir_menu_contexto(self, event):
        item = self.tree.identify_row(event.y)
        if item and "ficha" in self.tree.item(item, "tags"):
            self.tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
            menu.add_command(label="Duplicar Ficha", command=lambda: self.duplicar_ficha(item))
            menu.post(event.x_root, event.y_root)

    def duplicar_ficha(self, item_id):
        if self.bloquear_se_buscando(): return
        pai = self.tree.parent(item_id)
        dados_originais = self.dados_banco.get(item_id, {})
        novo_nome = self.gerar_nome_unico(f"{dados_originais.get('nome', 'Cópia')} (Cópia)", pai)
        novos_dados = json.loads(json.dumps(dados_originais))
        novos_dados["nome"] = novo_nome
        novo_id = self.tree.insert(pai, "end", text=f" {novo_nome}", tags=("ficha",))
        self.dados_banco[novo_id] = novos_dados

    def iniciar_drag_tree(self, event):
        if self.bloquear_se_buscando(): return
        item = self.tree.identify_row(event.y)
        if not item:
            if self.tree.selection():
                self.tree.selection_remove(self.tree.selection())
        self.item_arrastado = item

    def registrar_log(self, mensagem):
        self.caixa_log.configure(state="normal")
        self.caixa_log.insert(tk.END, f"• {mensagem}\n")
        self.caixa_log.see(tk.END)
        self.caixa_log.configure(state="disabled")

    def soltar_drag_tree(self, event):
        if not self.item_arrastado: return
        
        # NOVO: Intercepta o drag & drop se soltar em cima da lista de bando!
        x_root = self.tree.winfo_rootx() + event.x
        y_root = self.tree.winfo_rooty() + event.y
        widget_sob_mouse = self.root.winfo_containing(x_root, y_root)
        
        if widget_sob_mouse and hasattr(widget_sob_mouse, 'bando_tag'):
            if "ficha" in self.tree.item(self.item_arrastado, "tags"):
                nome_arrastado = self.tree.item(self.item_arrastado, "text").strip()
                widget_sob_mouse.insert(tk.END, nome_arrastado)
            self.item_arrastado = None
            return

        target = self.tree.identify_row(event.y)
        item = self.item_arrastado
        self.item_arrastado = None
        
        if not target:
            self.tree.move(item, "", "end")
            return
        if item == target: return
            
        def eh_descendente(pai, filho_potencial):
            filhos = self.tree.get_children(pai)
            if filho_potencial in filhos: return True
            for f in filhos:
                if eh_descendente(f, filho_potencial): return True
            return False

        if eh_descendente(item, target): return
            
        tags_alvo = self.tree.item(target, "tags")
        if "pasta" in tags_alvo:
            self.tree.move(item, target, "end")
            self.tree.item(target, open=True)
        else:
            pai_alvo = self.tree.parent(target)
            idx_alvo = self.tree.index(target)
            self.tree.move(item, pai_alvo, idx_alvo)

    def gerar_nome_unico(self, nome_base, pai):
        existentes = []
        for child in self.tree.get_children(pai):
            texto_puro = re.sub(r" \[Lv\. .*?\]$", "", self.tree.item(child, "text").strip())
            existentes.append(texto_puro)
        if nome_base not in existentes: return nome_base
        i = 1
        while f"{nome_base} ({i})" in existentes: i += 1
        return f"{nome_base} ({i})"

    def add_tracker(self):
        sel = self.tree.selection()
        if sel and "ficha" in self.tree.item(sel[0], "tags"):
            item_id = sel[0]
            nome = self.tree.item(item_id, "text").strip()
            ini = simpledialog.askinteger("Iniciativa", f"Iniciativa de {nome}:")
            if ini is not None:
                self.tracker_data.append({"ini": ini, "id": item_id, "nome": nome, "status": ""})
                self.atualizar_tracker_view()
                self.registrar_log(f"Iniciativa: {nome} ➔ {ini}")

    def rolar_iniciativa_pasta(self):
        sel = self.tree.selection()
        if not sel or "pasta" not in self.tree.item(sel[0], "tags"):
            messagebox.showwarning("Aviso", "Selecione uma pasta para rolar iniciativa em massa.")
            return
            
        pasta_id = sel[0]
        for child in self.tree.get_children(pasta_id):
            if "ficha" in self.tree.item(child, "tags"):
                dados = self.dados_banco.get(child, {})
                agi = dados.get("agi", 0)
                rolagem = random.randint(1, 20) + agi
                nome = self.tree.item(child, "text").strip()
                self.tracker_data.append({"ini": rolagem, "id": child, "nome": nome, "status": ""})
                self.registrar_log(f"Iniciativa: {nome} ➔ {rolagem}")
        
        self.atualizar_tracker_view()

    def limpar_tracker(self):
        self.tracker_data.clear()
        self.atualizar_tracker_view()
        self.registrar_log("Tracker de Combate limpo.")

    def menu_condicoes_tracker(self, event):
        idx = self.lista_iniciativa.nearest(event.y)
        if idx >= 0:
            self.lista_iniciativa.selection_clear(0, tk.END)
            self.lista_iniciativa.selection_set(idx)
            menu = tk.Menu(self.root, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
            icones = ["☠️ Envenenado", "💤 Fadigado", "⚡ Haki Exausto", "🛡️ Protegido", "❌ Limpar Status"]
            for icone in icones:
                menu.add_command(label=icone, command=lambda i=icone, index=idx: self.aplicar_status_tracker(index, i))
            menu.post(event.x_root, event.y_root)

    def aplicar_status_tracker(self, index, icone_full):
        icone = icone_full.split(" ")[0] if "Limpar" not in icone_full else ""
        self.tracker_data[index]["status"] = icone
        self.atualizar_tracker_view()

    def atualizar_tracker_view(self):
        self.lista_iniciativa.delete(0, tk.END)
        self.tracker_data.sort(key=lambda x: x["ini"], reverse=True)
        for t in self.tracker_data:
            linha = f"  [{t['ini']:02d}]   {t['nome']}  {t['status']}"
            self.lista_iniciativa.insert(tk.END, linha)
            
    def sync_nome_ficha(self, item_id, novo_nome, nivel="1"):
        self.tree.item(item_id, text=f" {novo_nome} [Lv. {nivel}]")
        if item_id in self.abas_abertas:
            self.notebook.tab(self.abas_abertas[item_id].master, text=f"   {novo_nome}   ")
        for i, t in enumerate(self.tracker_data):
            if t['id'] == item_id:
                self.tracker_data[i]['nome'] = novo_nome
        self.atualizar_tracker_view()

    def novo_banco(self):
        if messagebox.askyesno("Novo Cofre", "Você iniciará uma nova campanha. Alterações não salvas serão perdidas. Continuar?"):
            self.arquivo_atual = None
            self.dados_banco.clear()
            for aba in self.abas_abertas.values(): aba.master.destroy()
            self.abas_abertas.clear()
            self.tree.delete(*self.tree.get_children())
            self.limpar_tracker()
            self.inicializar_arvore_padrao()
            self.atualizar_titulo()

    def salvar_banco(self):
        if not self.arquivo_atual:
            self.salvar_como_banco()
            return
        for item_id, aba in self.abas_abertas.items():
            self.dados_banco[item_id] = aba.get_dados()
        try:
            conn = sqlite3.connect(self.arquivo_atual)
            c = conn.cursor()
            c.execute('CREATE TABLE IF NOT EXISTS dados_rpg (id INTEGER PRIMARY KEY, estrutura TEXT, fichas TEXT)')
            def mapear_arvore(node):
                res = []
                for child in self.tree.get_children(node):
                    item = self.tree.item(child)
                    res.append({
                        "id": child,
                        "text": item["text"],
                        "tags": item["tags"],
                        "filhos": mapear_arvore(child)
                    })
                return res
            c.execute('DELETE FROM dados_rpg')
            c.execute('INSERT INTO dados_rpg (id, estrutura, fichas) VALUES (1, ?, ?)', (json.dumps(mapear_arvore("")), json.dumps(self.dados_banco)))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", f"Cofre salvo com sucesso em:\n{self.arquivo_atual}")
        except Exception as e:
            messagebox.showerror("Erro de Gravação", str(e))

    def salvar_como_banco(self):
        caminho = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Banco SQLite", "*.db"), ("Todos os Arquivos", "*.*")], title="Salvar Cofre Como...")
        if caminho:
            self.arquivo_atual = caminho
            self.atualizar_titulo()
            self.salvar_banco()

    def carregar_banco(self):
        caminho = filedialog.askopenfilename(filetypes=[("Banco SQLite", "*.db"), ("Todos os Arquivos", "*.*")], title="Abrir Cofre")
        if not caminho: return
        try:
            conn = sqlite3.connect(caminho)
            c = conn.cursor()
            c.execute('SELECT estrutura, fichas FROM dados_rpg WHERE id=1')
            row = c.fetchone()
            conn.close()
            if row:
                self.arquivo_atual = caminho
                self.atualizar_titulo()
                estrutura = json.loads(row[0])
                self.dados_banco = json.loads(row[1])
                for aba in self.abas_abertas.values(): aba.master.destroy()
                self.abas_abertas.clear()
                self.tree.delete(*self.tree.get_children())
                self.limpar_tracker()
                def restaurar(pai, nos):
                    for n in nos:
                        novo_id = self.tree.insert(pai, "end", iid=n["id"], text=n["text"], tags=n["tags"], open=True)
                        restaurar(novo_id, n["filhos"])
                restaurar("", estrutura)
            else:
                messagebox.showwarning("Aviso", "Este arquivo não contém dados compatíveis.")
        except Exception as e:
            messagebox.showerror("Erro de Leitura", str(e))

    def toggle_tree(self):
        if self.tree_visivel:
            self.frame_tree.pack_forget()
            self.tree_visivel = False
        else:
            self.frame_tree.pack(side=tk.LEFT, fill=tk.Y, before=self.notebook_frame)
            self.tree_visivel = True

    def toggle_tracker(self):
        if self.tracker_visivel:
            self.frame_tracker.pack_forget()
            self.tracker_visivel = False
        else:
            self.frame_tracker.pack(side=tk.RIGHT, fill=tk.Y)
            self.tracker_visivel = True

    def adicionar_pasta(self):
        if self.bloquear_se_buscando(): return
        sel = self.tree.selection()
        pai = sel[0] if sel and "pasta" in self.tree.item(sel[0], "tags") else (self.tree.parent(sel[0]) if sel else "")
        nome_unico = self.gerar_nome_unico("Nova Categoria", pai)
        self.tree.insert(pai, "end", text=f" {nome_unico}", open=True, tags=("pasta",))

    def adicionar_personagem(self):
        if self.bloquear_se_buscando(): return
        sel = self.tree.selection()
        pai = sel[0] if sel and "pasta" in self.tree.item(sel[0], "tags") else (self.tree.parent(sel[0]) if sel else "")
        nome_unico = self.gerar_nome_unico("Novo Inimigo", pai)
        novo_id = self.tree.insert(pai, "end", text=f" {nome_unico}", tags=("ficha",))
        self.dados_banco[novo_id] = {"nome": nome_unico, "pv": 100, "pe": 20}
        self.abrir_aba_personagem(novo_id, nome_unico)

    def renomear_item(self):
        if self.bloquear_se_buscando(): return
        sel = self.tree.selection()
        if not sel: return
        item_id = sel[0]
        tags = self.tree.item(item_id, "tags")
        
        # Puxa o nome limpo do banco (ignora o "[Lv. 10]" pra não bugar a caixa de edição)
        if "ficha" in tags:
            nome_atual = self.dados_banco.get(item_id, {}).get("nome", "Inimigo")
            tipo = "a Ficha"
        else:
            nome_atual = self.tree.item(item_id, "text").strip()
            tipo = "a Pasta"
            
        novo_nome = simpledialog.askstring("Renomear", f"Digite um novo nome para {tipo}:", initialvalue=nome_atual)
        
        if novo_nome and novo_nome.strip():
            novo_nome = novo_nome.strip()
            
            if "ficha" in tags:
                nivel_atual = self.dados_banco.get(item_id, {}).get("nivel", "1")
                self.tree.item(item_id, text=f" {novo_nome} [Lv. {nivel_atual}]")
                if item_id in self.abas_abertas:
                    self.notebook.tab(self.abas_abertas[item_id].master, text=f"   {novo_nome}   ")
                    self.abas_abertas[item_id].var_nome.set(novo_nome)
                elif item_id in self.dados_banco:
                    self.dados_banco[item_id]["nome"] = novo_nome
                
                for i, t in enumerate(self.tracker_data):
                    if t['id'] == item_id:
                        self.tracker_data[i]['nome'] = novo_nome
                self.atualizar_tracker_view()
            else:
                self.tree.item(item_id, text=f" {novo_nome}")

    def deletar_item(self):
        if self.bloquear_se_buscando(): return
        sel = self.tree.selection()
        if not sel: return
        item_id = sel[0]
        if not messagebox.askyesno("Confirmar", f"Deseja excluir '{self.tree.item(item_id, 'text').strip()}' e todo seu conteúdo?"): return

        def excluir_recursivamente(node):
            for filho in self.tree.get_children(node):
                excluir_recursivamente(filho)
            if node in self.abas_abertas:
                aba = self.abas_abertas.pop(node)
                self.notebook.forget(aba.master)
                aba.master.destroy()
            self.dados_banco.pop(node, None)
            
            for t in list(self.tracker_data):
                if t['id'] == node:
                    self.tracker_data.remove(t)

        excluir_recursivamente(item_id)
        self.atualizar_tracker_view()
        self.tree.delete(item_id)

    def ao_dar_duplo_clique(self, event):
        sel = self.tree.selection()
        if sel and "ficha" in self.tree.item(sel[0], "tags"):
            self.abrir_aba_personagem(sel[0], self.tree.item(sel[0], "text").strip())

    def abrir_aba_personagem(self, item_id, nome):
        if item_id in self.abas_abertas:
            self.notebook.select(self.abas_abertas[item_id].master)
            return

        frame_aba = ctk.CTkFrame(self.notebook, fg_color=self.tema_atual["bg_main"], corner_radius=0)
        barra_topo = ctk.CTkFrame(frame_aba, fg_color="transparent")
        barra_topo.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)
        
        ctk.CTkButton(barra_topo, text="✖ Fechar Ficha", command=lambda: self.fechar_aba(item_id), fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75", width=120).pack(side=tk.RIGHT)

        dados = self.dados_banco.get(item_id, None)
        ficha = FichaPersonagemFrame(frame_aba, lambda nome, nivel: self.sync_nome_ficha(item_id, nome, nivel), app_master=self, dados_iniciais=dados)
        ficha.pack(fill=tk.BOTH, expand=True)

        self.notebook.add(frame_aba, text=f"   {nome}   ")
        self.notebook.select(frame_aba)
        self.abas_abertas[item_id] = ficha

    def fechar_aba(self, item_id):
        if item_id in self.abas_abertas:
            aba = self.abas_abertas.pop(item_id)
            self.dados_banco[item_id] = aba.get_dados() 
            self.notebook.forget(aba.master)
            aba.master.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    app = GerenciadorAmeasApp(root)
    root.mainloop()