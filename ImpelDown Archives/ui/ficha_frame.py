import os
import re
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

from core.dados import rolar_dados_seguro, rolar_teste_pericia
from core.regras import calcular_atributos_derivados
from core.paleta import (
    TEXTO_SUAVE as COR_TEXTO_SUAVE,
    INFO as COR_INFO,
    DESTAQUE as COR_DESTAQUE,
    PERIGO as COR_PERIGO,
    PERIGO_CLARO as COR_PERIGO_CLARO,
    AVISO as COR_AVISO,
    SUCESSO as COR_SUCESSO,
    HOVER as COR_HOVER,
    BOTAO_PERIGO as COR_BOTAO_PERIGO,
    BOTAO_PERIGO_HOVER as COR_BOTAO_PERIGO_HOVER,
    BOTAO_PERIGO_TEXTO as COR_BOTAO_PERIGO_TEXTO,
    BOTAO_SUCESSO as COR_BOTAO_SUCESSO,
    BOTAO_SUCESSO_HOVER as COR_BOTAO_SUCESSO_HOVER,
    BOTAO_SUCESSO_TEXTO as COR_BOTAO_SUCESSO_TEXTO,
)
from ui.widgets_custom import HabilidadeBloco, ListaBando
from utils.loot import gerar_loot_aleatorio
from utils.historia import gerar_historia
from utils.arquivos import exportar_ficha_markdown
from utils.cartaz import gerar_cartaz_png
from utils.golpes import (
    CATEGORIAS as CATEGORIAS_GOLPE,
    PATAMARES as PATAMARES_GOLPE,
    categoria_por_ficha,
    gerar_golpe,
    patamar_por_nivel,
    sabor_por_faccao,
)

#: Cache de imagens em memória (evita reler o arquivo ao reabrir a ficha).
_CACHE_IMAGENS: dict[str, Image.Image] = {}

#: Grau digitado no menu -> grau numérico usado pela Poça de d20.
MAPA_GRAUS_TESTE: dict[str, int] = {
    "Leigo": 0,
    "Treinado": 1,
    "Especialista": 2,
    "Mestre": 3,
}

#: Nome do Atributo no menu -> atributo da instância que guarda o valor.
MAPA_ATRIBUTOS_TESTE: dict[str, str] = {
    "Físico": "var_fis",
    "Agilidade": "var_agi",
    "Intelecto": "var_int",
    "Instinto": "var_inst",
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
        
        self.pv_atual = tk.IntVar(value=0)
        self.pe_atual = tk.IntVar(value=0)
        self.pv_max = tk.IntVar(value=0)
        self.pe_max = tk.IntVar(value=0)
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
        self.mod_pv = tk.IntVar(value=0)
        self.mod_pe = tk.IntVar(value=0)

        self.var_nome.trace_add("write", self._sincronizar_arvore)
        self.var_nivel.trace_add("write", self._sincronizar_arvore)
        
        self.var_recompensa = tk.StringVar(value="0")

        gatilhos = [
            self.var_nivel, self.var_fis, self.var_agi, self.var_int, self.var_inst, 
            self.var_luta, self.var_acro, self.mod_passiva, self.mod_bloq, self.mod_esq, self.mod_cd,
            self.mod_pv, self.mod_pe,
        ]
        self._calc_agendado = None
        for var in gatilhos:
            var.trace_add("write", self._agendar_calculo)

        self._limitando_pv = False
        self.pv_atual.trace_add("write", self._limitar_pv)
        self.pe_atual.trace_add("write", self._limitar_pe)
        self.bind("<Destroy>", self._ao_destruir)

        self.montar_interface()
        
        if dados_iniciais:
            self.carregar_dados(dados_iniciais)
        else:
            self.calcular_derivados()
            self.pv_atual.set(self.pv_max.get())
            self.pe_atual.set(self.pe_max.get())

    def formatar_recompensa(self, event=None) -> None:
        """Formata a recompensa só ao sair do campo.

        Antes, um trace reformatava a cada tecla e o cursor pulava no meio dos
        dígitos — por isso a digitação ficava "bugada".
        """
        nums = re.sub(r"\D", "", self.var_recompensa.get())
        self.var_recompensa.set(f"{int(nums):,}".replace(",", ".") if nums else "0")

    def _atualizar_labels_recurso(self, *args) -> None:
        """Mostra PV e PE no formato único ``atual / máximo``."""
        if hasattr(self, "lbl_pv"):
            self.lbl_pv.configure(text=f"{self.pv_atual.get()} / {self.pv_max.get()}")
        if hasattr(self, "lbl_pe"):
            self.lbl_pe.configure(text=f"{self.pe_atual.get()} / {self.pe_max.get()}")

    def _sincronizar_arvore(self, *args):
        self.sync_nome_callback(self.var_nome.get(), self._nivel_texto())

    def _nivel_texto(self) -> str:
        """Nível como texto numérico; campos vazios ou inválidos viram "1"."""
        texto = str(self.var_nivel.get()).strip()
        return texto if texto.isdigit() else "1"

    def montar_interface(self):
        frame_topo = ctk.CTkFrame(self, fg_color=self.tema["bg_card"], corner_radius=0, height=50)
        frame_topo.pack(side=tk.TOP, fill=tk.X)
        
        f_inner = ctk.CTkFrame(frame_topo, fg_color="transparent")
        f_inner.pack(fill=tk.X, padx=20, pady=10)

        # PV: rótulo → − → "atual / máx" → +
        ctk.CTkLabel(f_inner, text="PV:", text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('title')).pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkButton(f_inner, text="-", width=34, height=34, font=self.app_master.get_font('bold'), fg_color=self.tema["bg_input"], command=lambda: self.pv_atual.set(self.pv_atual.get()-1)).pack(side=tk.LEFT)
        self.lbl_pv = ctk.CTkLabel(f_inner, text="0 / 0", width=120, height=34, text_color=COR_PERIGO, font=self.app_master.get_font('number'))
        self.lbl_pv.pack(side=tk.LEFT, padx=6)
        ctk.CTkButton(f_inner, text="+", width=34, height=34, font=self.app_master.get_font('bold'), fg_color=self.tema["bg_input"], command=lambda: self.pv_atual.set(self.pv_atual.get()+1)).pack(side=tk.LEFT, padx=(0, 18))

        # PE: mesmo padrão, alinhado ao lado.
        ctk.CTkLabel(f_inner, text="PE:", text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('title')).pack(side=tk.LEFT, padx=(0, 6))
        ctk.CTkButton(f_inner, text="-", width=34, height=34, font=self.app_master.get_font('bold'), fg_color=self.tema["bg_input"], command=lambda: self.pe_atual.set(self.pe_atual.get()-1)).pack(side=tk.LEFT)
        self.lbl_pe = ctk.CTkLabel(f_inner, text="0 / 0", width=120, height=34, text_color=COR_INFO, font=self.app_master.get_font('number'))
        self.lbl_pe.pack(side=tk.LEFT, padx=6)
        ctk.CTkButton(f_inner, text="+", width=34, height=34, font=self.app_master.get_font('bold'), fg_color=self.tema["bg_input"], command=lambda: self.pe_atual.set(self.pe_atual.get()+1)).pack(side=tk.LEFT, padx=(0, 18))

        for var_recurso in (self.pv_atual, self.pv_max, self.pe_atual, self.pe_max):
            var_recurso.trace_add("write", self._atualizar_labels_recurso)
        self._atualizar_labels_recurso()

        self.lbl_defesas = ctk.CTkLabel(f_inner, text="Def: -- | Bloq: -- | Esq: -- | CD: --", text_color=COR_DESTAQUE, font=self.app_master.get_font('main'))
        self.lbl_defesas.pack(side=tk.LEFT)

        self.btn_rolar_dano = ctk.CTkButton(f_inner, text="🎲 Rolar", command=self.rolar_dano, fg_color=self.tema["accent"], text_color="white", width=80)
        self.btn_rolar_dano.pack(side=tk.RIGHT, padx=(5,0))

        self.var_rolagem = tk.StringVar(value="")
        self.entry_rolagem = ctk.CTkEntry(
            f_inner, textvariable=self.var_rolagem, width=92, height=30,
            placeholder_text="2d8+3", justify="center",
            fg_color=self.tema["bg_input"], text_color=self.tema["text"],
            border_width=0, font=self.app_master.get_font('small'),
        )
        self.entry_rolagem.pack(side=tk.RIGHT, padx=(5, 0))
        self.entry_rolagem.bind("<Return>", lambda e: self.rolar_dano())

        self.container_ficha = ctk.CTkFrame(self, fg_color="transparent")
        self.container_ficha.pack(fill=tk.BOTH, expand=True, pady=15, padx=15)

        self.painel_esquerdo = ctk.CTkFrame(self.container_ficha, width=340, fg_color="transparent")
        self.painel_esquerdo.pack_propagate(False)
        self.painel_esquerdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        self.painel_direito = ctk.CTkFrame(self.container_ficha, fg_color="transparent")
        self.painel_direito.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        frame_id = ctk.CTkFrame(self.painel_esquerdo, fg_color="transparent")
        frame_id.pack(fill=tk.X, pady=(0, 5))
        
        f_nome = ctk.CTkFrame(frame_id, fg_color="transparent")
        f_nome.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        f_lbl = ctk.CTkFrame(f_nome, fg_color="transparent")
        f_lbl.pack(fill=tk.X)
        ctk.CTkLabel(f_lbl, text="Nome da Ameaça", text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('small')).pack(side=tk.LEFT)
        ctk.CTkButton(f_lbl, text="🎲 Aleatório", width=20, height=15, fg_color="transparent", text_color=self.tema["accent"], hover_color=self.tema["bg_input"], font=self.app_master.get_font('small'), command=self.gerar_nome_pirata).pack(side=tk.LEFT, padx=(5,0))

        self.entrada_nome = ctk.CTkEntry(f_nome, textvariable=self.var_nome, font=self.app_master.get_font('title'), fg_color=self.tema["bg_input"], text_color=self.tema["text"], border_width=0, height=32)
        self.entrada_nome.pack(fill=tk.X)

        f_nivel = ctk.CTkFrame(frame_id, fg_color="transparent")
        f_nivel.pack(side=tk.RIGHT, padx=(10, 0))
        ctk.CTkLabel(f_nivel, text="Nível", text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('small')).pack(anchor="e")
        ctk.CTkEntry(f_nivel, textvariable=self.var_nivel, width=45, height=32, font=self.app_master.get_font('title'), justify="center", fg_color=self.tema["bg_input"], text_color=self.tema["text"], border_width=0).pack(side=tk.RIGHT)

        f_recomp = ctk.CTkFrame(self.painel_esquerdo, fg_color="transparent")
        f_recomp.pack(fill=tk.X, pady=(0, 10))
        ctk.CTkLabel(f_recomp, text="☠️ Recompensa:", text_color=COR_DESTAQUE, font=self.app_master.get_font('bold')).pack(side=tk.LEFT)
        self.entrada_recompensa = ctk.CTkEntry(f_recomp, textvariable=self.var_recompensa, font=self.app_master.get_font('bold'), fg_color="transparent", text_color=COR_DESTAQUE, border_width=0, justify="right")
        self.entrada_recompensa.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entrada_recompensa.bind("<FocusOut>", self.formatar_recompensa)
        self.entrada_recompensa.bind("<Return>", self.formatar_recompensa)
        ctk.CTkLabel(f_recomp, text="Berries", text_color=COR_DESTAQUE, font=self.app_master.get_font('bold')).pack(side=tk.LEFT, padx=(5,0))

        self.frame_imagem = tk.Frame(self.painel_esquerdo, width=180, height=180, bg=self.tema["bg_input"])
        self.frame_imagem.pack_propagate(False)
        self.frame_imagem.pack(anchor="center", pady=(0, 5)) 

        self.canvas_img = tk.Canvas(self.frame_imagem, bg=self.tema["bg_input"], highlightthickness=0)
        self.canvas_img.pack(fill=tk.BOTH, expand=True)
        self.txt_img_placeholder = self.canvas_img.create_text(90, 90, text="Arraste ou dê Scroll", fill=COR_TEXTO_SUAVE, font=self.app_master.get_font('small'))

        self.imagem_original = None
        self.foto = None
        self.escala_imagem = 1.0
        self.img_x, self.img_y = 90, 90
        
        self.canvas_img.bind("<ButtonPress-1>", self.iniciar_arraste)
        self.canvas_img.bind("<B1-Motion>", self.arrastar_imagem)
        self.canvas_img.bind("<MouseWheel>", self.zoom_imagem)

        ctk.CTkButton(self.painel_esquerdo, text="Procurar Imagem", command=self.carregar_imagem, fg_color=self.tema["bg_input"], hover_color=COR_HOVER, text_color=self.tema["text"]).pack(anchor="center", fill=tk.X, pady=(0, 10))

        self.tabview_esquerdo = ctk.CTkTabview(self.painel_esquerdo, fg_color="transparent", segmented_button_selected_color=self.tema["accent"], segmented_button_selected_hover_color=self.tema["accent"])
        self.tabview_esquerdo.pack(fill=tk.BOTH, expand=True)

        tab_attr = self.tabview_esquerdo.add("Atributos")
        tab_loot = self.tabview_esquerdo.add("Loot")
        tab_bg = self.tabview_esquerdo.add("História")
        tab_bando = self.tabview_esquerdo.add("Bando")

        def criar_mini_contador(master, label, var, width_val=28, minimo=None, maximo=None):
            def ajustar(delta: int, alvo=var) -> None:
                novo = alvo.get() + delta
                if minimo is not None:
                    novo = max(minimo, novo)
                if maximo is not None:
                    novo = min(maximo, novo)
                alvo.set(novo)

            f = ctk.CTkFrame(master, fg_color="transparent")
            f.pack(side=tk.LEFT, expand=True, padx=2)
            ctk.CTkLabel(f, text=label, text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('small')).pack()
            f_val = ctk.CTkFrame(f, fg_color="transparent")
            f_val.pack()
            ctk.CTkButton(f_val, text="-", width=22, height=22, fg_color=self.tema["bg_input"], command=lambda: ajustar(-1)).pack(side=tk.LEFT)
            ctk.CTkLabel(f_val, textvariable=var, width=width_val, font=self.app_master.get_font('bold')).pack(side=tk.LEFT)
            ctk.CTkButton(f_val, text="+", width=22, height=22, fg_color=self.tema["bg_input"], command=lambda: ajustar(1)).pack(side=tk.LEFT)

        frame_attrs1 = ctk.CTkFrame(tab_attr, fg_color="transparent")
        frame_attrs1.pack(fill=tk.X, pady=(5,0))
        criar_mini_contador(frame_attrs1, "Fís", self.var_fis, minimo=0, maximo=5)
        criar_mini_contador(frame_attrs1, "Agi", self.var_agi, minimo=0, maximo=5)
        criar_mini_contador(frame_attrs1, "Int", self.var_int, minimo=0, maximo=5)
        criar_mini_contador(frame_attrs1, "Inst", self.var_inst, minimo=0, maximo=5)

        frame_pericias = ctk.CTkFrame(tab_attr, fg_color="transparent")
        frame_pericias.pack(fill=tk.X, pady=(15, 5))
        criar_mini_contador(frame_pericias, "Grau Luta", self.var_luta, width_val=22, minimo=0, maximo=3)
        criar_mini_contador(frame_pericias, "Grau Acro", self.var_acro, width_val=22, minimo=0, maximo=3)
        criar_mini_contador(frame_pericias, "+PV Máx", self.mod_pv, width_val=22)
        criar_mini_contador(frame_pericias, "+PE Máx", self.mod_pe, width_val=22)
        
        ctk.CTkLabel(tab_attr, text="Bônus Extras Passivos", text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('small')).pack(anchor="w", pady=(15, 0))
        frame_mods = ctk.CTkFrame(tab_attr, fg_color="transparent")
        frame_mods.pack(fill=tk.X)
        criar_mini_contador(frame_mods, "+Pass", self.mod_passiva, width_val=22)
        criar_mini_contador(frame_mods, "+Bloq", self.mod_bloq, width_val=22)
        criar_mini_contador(frame_mods, "+Esq", self.mod_esq, width_val=22)
        criar_mini_contador(frame_mods, "+CD", self.mod_cd, width_val=22)

        # --- Teste de Perícia (Poça de d20) ---
        ctk.CTkLabel(tab_attr, text="Teste de Perícia (poça de d20)", text_color=COR_TEXTO_SUAVE,
                     font=self.app_master.get_font('small')).pack(anchor="w", pady=(15, 0))

        frame_teste = ctk.CTkFrame(tab_attr, fg_color=self.tema["bg_card"], corner_radius=6)
        frame_teste.pack(fill=tk.X, pady=(2, 0))

        self.var_teste_atributo = tk.StringVar(value="Físico")
        self.var_teste_grau = tk.StringVar(value="Treinado")
        self.var_teste_ajuste = tk.IntVar(value=0)
        self.var_teste_cd = tk.StringVar(value="")

        linha1 = ctk.CTkFrame(frame_teste, fg_color="transparent")
        linha1.pack(fill=tk.X, padx=6, pady=(6, 4))

        ctk.CTkOptionMenu(
            linha1, variable=self.var_teste_atributo, values=list(MAPA_ATRIBUTOS_TESTE),
            width=150, height=26, font=self.app_master.get_font('small'),
            fg_color=self.tema["bg_input"], button_color=self.tema["accent"],
            text_color=self.tema["text"],
        ).pack(side=tk.LEFT, expand=True, padx=(0, 4))

        ctk.CTkOptionMenu(
            linha1, variable=self.var_teste_grau, values=list(MAPA_GRAUS_TESTE),
            width=150, height=26, font=self.app_master.get_font('small'),
            fg_color=self.tema["bg_input"], button_color=self.tema["accent"],
            text_color=self.tema["text"],
        ).pack(side=tk.LEFT, expand=True)

        linha2 = ctk.CTkFrame(frame_teste, fg_color="transparent")
        linha2.pack(fill=tk.X, padx=6, pady=(0, 6))

        ctk.CTkButton(linha2, text="−", width=24, height=24, fg_color=self.tema["bg_input"],
                      hover_color=COR_HOVER, font=self.app_master.get_font('bold'),
                      command=lambda: self.ajustar_teste(-1)).pack(side=tk.LEFT)
        ctk.CTkLabel(linha2, textvariable=self.var_teste_ajuste, width=26,
                     font=self.app_master.get_font('bold')).pack(side=tk.LEFT)
        ctk.CTkButton(linha2, text="+", width=24, height=24, fg_color=self.tema["bg_input"],
                      hover_color=COR_HOVER, font=self.app_master.get_font('bold'),
                      command=lambda: self.ajustar_teste(1)).pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkLabel(linha2, text="CD", text_color=COR_TEXTO_SUAVE,
                     font=self.app_master.get_font('small')).pack(side=tk.LEFT, padx=(0, 4))
        ctk.CTkEntry(linha2, textvariable=self.var_teste_cd, width=42, height=24, placeholder_text="—",
                     justify="center", fg_color=self.tema["bg_input"], text_color=self.tema["text"],
                     border_width=0, font=self.app_master.get_font('small')).pack(side=tk.LEFT)

        ctk.CTkButton(linha2, text="🎯 Rolar", width=70, height=24, fg_color=self.tema["accent"],
                      hover_color=self.tema.get("accent_hover", self.tema["accent"]), text_color="white",
                      font=self.app_master.get_font('small'),
                      command=self.rolar_teste_pericia_ficha).pack(side=tk.RIGHT)

        self.lbl_teste_resultado = ctk.CTkLabel(frame_teste, text="", text_color=COR_DESTAQUE,
                                                font=self.app_master.get_font('small'),
                                                wraplength=290, justify="left")
        self.lbl_teste_resultado.pack(fill=tk.X, padx=8, pady=(0, 6))

        ctk.CTkButton(tab_loot, text="🎲 Gerar Loot Aleatório", command=self.sortear_loot, fg_color=self.tema["bg_input"], text_color=self.tema["text"]).pack(fill=tk.X, pady=(0, 5))
        self.texto_loot = ctk.CTkTextbox(tab_loot, fg_color=self.tema["bg_input"], text_color=self.tema["text"], font=self.app_master.get_font('main'), border_width=0, corner_radius=6)
        self.texto_loot.pack(fill=tk.BOTH, expand=True, pady=5)

        ctk.CTkButton(tab_bg, text="🧠 Gerar IA", command=self.gerar_ia_local, fg_color=self.tema["bg_input"], text_color=self.tema["text"]).pack(fill=tk.X, pady=(0,5))
        ctk.CTkButton(tab_bg, text="📖 Expandir História", command=self.expandir_historia, fg_color=self.tema["bg_input"], hover_color=COR_HOVER, text_color=self.tema["text"]).pack(fill=tk.X, pady=(0,5))
        self.texto_historia = ctk.CTkTextbox(tab_bg, fg_color=self.tema["bg_input"], text_color=self.tema["text"], font=self.app_master.get_font('main'), wrap=tk.WORD, border_width=0, corner_radius=6)
        self.texto_historia.pack(fill=tk.BOTH, expand=True)

        ctk.CTkLabel(tab_bando, text="Bando compartilhado entre fichas · duplo clique abre a ficha", text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('small')).pack(pady=(0,2))
        self.listbox_bando = ListaBando(
            tab_bando, self.app_master, self.tema,
            ao_abrir=self._abrir_ficha_do_bando,
            fonte=self.app_master.bando_global,
            ao_alterar=self.app_master._bando_alterado,
        )
        self.listbox_bando.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        f_btn_bando = ctk.CTkFrame(tab_bando, fg_color="transparent")
        f_btn_bando.pack(fill=tk.X, pady=5)
        ctk.CTkButton(f_btn_bando, text="⚔️ Jogar Esquadrão no Tracker", command=self.lancar_bando_tracker, fg_color=self.tema["accent"], text_color="white").pack(fill=tk.X, pady=(0,2))
        ctk.CTkButton(f_btn_bando, text="✖ Limpar Bando", command=lambda: self.listbox_bando.delete(0, tk.END), fg_color="transparent", hover_color=COR_BOTAO_PERIGO, text_color=COR_PERIGO).pack(fill=tk.X)

        frame_hab_topo = ctk.CTkFrame(self.painel_direito, fg_color="transparent")
        frame_hab_topo.pack(side=tk.TOP, fill=tk.X, pady=(0, 15), padx=10)
        
        ctk.CTkLabel(frame_hab_topo, text="Habilidades", text_color=self.tema["text"], font=self.app_master.get_font('title')).pack(side=tk.LEFT)
        
        self.btn_add_hab = ctk.CTkButton(frame_hab_topo, text="➕ Adicionar ▼", fg_color=self.tema["bg_input"], hover_color=COR_HOVER, text_color=self.tema["text"], font=self.app_master.get_font('bold'))
        self.menu_hab = tk.Menu(self.btn_add_hab, tearoff=0, bg=self.tema["bg_card"], fg=self.tema["text"], bd=0, activebackground=self.tema["accent"])
        for patamar in ["Básica", "Média", "Forte", "Suprema", "Outros"]:
            self.menu_hab.add_command(label=patamar, command=lambda p=patamar: self.inserir_habilidade(p))
        self.btn_add_hab.configure(command=lambda: self.menu_hab.post(self.btn_add_hab.winfo_rootx(), self.btn_add_hab.winfo_rooty() + self.btn_add_hab.winfo_height()))
        self.btn_add_hab.pack(side=tk.RIGHT)

        self.btn_golpe = ctk.CTkButton(frame_hab_topo, text="✨ Golpe", fg_color=self.tema["bg_input"], hover_color=COR_HOVER, text_color=self.tema["text"], font=self.app_master.get_font('bold'), width=70, command=self.abrir_gerador_golpe)
        self.btn_golpe.pack(side=tk.RIGHT, padx=(0, 6))

        self.var_filtro_hab = ctk.StringVar(value="Todas")
        opcoes_filtro = ["Todas", "Básica", "Média", "Forte", "Suprema", "1 Ação", "Reação", "Livre"]
        self.menu_filtro = ctk.CTkOptionMenu(frame_hab_topo, variable=self.var_filtro_hab, values=opcoes_filtro, command=self.filtrar_habilidades, fg_color=self.tema["bg_input"], text_color=self.tema["text"], button_color=self.tema["accent"], width=92, font=self.app_master.get_font('small'))
        self.menu_filtro.pack(side=tk.RIGHT, padx=(8, 8))

        self.canvas_hab = tk.Canvas(self.painel_direito, bg=self.tema["bg_main"], highlightthickness=0)
        self.scroll_hab = ttk.Scrollbar(self.painel_direito, orient="vertical", command=self.canvas_hab.yview)
        self.frame_lista_hab = tk.Frame(self.canvas_hab, bg=self.tema["bg_main"])

        self.frame_lista_hab.bind("<Configure>", lambda e: self.canvas_hab.configure(scrollregion=self.canvas_hab.bbox("all")))
        self.canvas_janela = self.canvas_hab.create_window((0, 0), window=self.frame_lista_hab, anchor="nw")
        self.canvas_hab.bind("<Configure>", lambda e: self.canvas_hab.itemconfig(self.canvas_janela, width=e.width))
        self.canvas_hab.configure(yscrollcommand=self.scroll_hab.set)
        
        self.canvas_hab.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_hab.pack(side=tk.RIGHT, fill=tk.Y)
        
        for alvo in (self.canvas_hab, self.frame_lista_hab):
            alvo.bind("<MouseWheel>", self._on_mousewheel_canvas)
        self.blocos_habilidades = []

    def _on_mousewheel_canvas(self, event) -> None:
        """Rola a lista de habilidades (o vínculo é local, não global)."""
        delta = getattr(event, "delta", 0)
        if delta:
            self.canvas_hab.yview_scroll(int(-delta / 120), "units")

    def _agendar_calculo(self, *args) -> None:
        """Debounce dos derivados: recalcula só quando o usuário para de digitar.

        Antes, cada tecla no Nível disparava o cálculo, o clamp de PV/PE e a
        reconfiguração de três labels; digitando rápido isso engasgava a UI.
        """
        if self._calc_agendado is not None:
            try:
                self.after_cancel(self._calc_agendado)
            except tk.TclError:
                pass
        self._calc_agendado = self.after(40, self.calcular_derivados)

    def _ao_destruir(self, event) -> None:
        """Cancela o cálculo agendado quando a aba é fechada."""
        if event.widget is not self:
            return
        if self._calc_agendado is not None:
            try:
                self.after_cancel(self._calc_agendado)
            except tk.TclError:
                pass
            self._calc_agendado = None

    def sincronizar_agora(self) -> None:
        """Descarta o debounce e recalcula imediatamente.

        Usado pelo Tracker antes de ler PV/PE, para não aplicar dano com um
        máximo desatualizado logo depois de mudar +PV/+PE.
        """
        if self._calc_agendado is not None:
            try:
                self.after_cancel(self._calc_agendado)
            except tk.TclError:
                pass
            self._calc_agendado = None
        self.calcular_derivados()

    def calcular_derivados(self, *args):
        self._calc_agendado = None
        try:
            res = calcular_atributos_derivados(
                self.var_nivel.get(),
                self.var_fis.get(),
                self.var_agi.get(),
                self.var_int.get(),
                self.var_inst.get(),
                self.var_luta.get(),
                self.var_acro.get(),
                self.mod_passiva.get(),
                self.mod_bloq.get(),
                self.mod_esq.get(),
                self.mod_cd.get(),
                self.mod_pv.get(),
                self.mod_pe.get(),
            )
            pv_max_anterior = self.pv_max.get()
            pe_max_anterior = self.pe_max.get()
            self.pv_max.set(res["pv"])
            self.pe_max.set(res["pe"])
            # Quem está com PV cheio continua cheio ao mudar Nível/Atributo;
            # quem está ferido mantém o dano, apenas limitado ao novo máximo.
            if pv_max_anterior > 0 and self.pv_atual.get() >= pv_max_anterior:
                self.pv_atual.set(res["pv"])
            else:
                self.pv_atual.set(min(self.pv_atual.get(), res["pv"]))
            if pe_max_anterior > 0 and self.pe_atual.get() >= pe_max_anterior:
                self.pe_atual.set(res["pe"])
            else:
                self.pe_atual.set(min(self.pe_atual.get(), res["pe"]))
            self.lbl_defesas.configure(
                text=f"Def: {res['passiva']} | Bloq: {res['bloqueio']} | Esq: {res['esquiva']} | CD: {res['cd']}"
            )
        except (ValueError, TypeError, tk.TclError):
            # Campo sendo digitado (vazio, texto solto): mantém os últimos valores.
            pass

    def _limitar_pv(self, *args) -> None:
        self._limitar_recurso(self.pv_atual, self.pv_max)

    def _limitar_pe(self, *args) -> None:
        self._limitar_recurso(self.pe_atual, self.pe_max)

    def _limitar_recurso(self, atual_var: tk.IntVar, max_var: tk.IntVar) -> None:
        """Mantém PV/PE entre 0 e o máximo, sem entrar em recursão de trace."""
        if self._limitando_pv:
            return
        maximo = max_var.get()
        atual = atual_var.get()
        if atual < 0 or (maximo > 0 and atual > maximo):
            self._limitando_pv = True
            try:
                atual_var.set(max(0, min(atual, maximo)) if maximo > 0 else 0)
            finally:
                self._limitando_pv = False

    def rolar_dano(self) -> None:
        """Rola a expressão digitada no cabeçalho, sem abrir popup."""
        expressao = self.var_rolagem.get().strip() or "1d20"
        try:
            resultado = rolar_dados_seguro(expressao)
        except ValueError as e:
            messagebox.showerror("Expressão inválida", str(e), parent=self)
            return
        self.app_master.registrar_log(f"⚔️ [{self.var_nome.get()}] {expressao} ➔ {resultado}")

    def ajustar_teste(self, delta: int) -> None:
        """Ajusta a poça em ±1 (positivo = Vantagem, negativo = Desvantagem)."""
        self.var_teste_ajuste.set(max(-3, min(3, int(self.var_teste_ajuste.get()) + delta)))

    def _valor_atributo_teste(self) -> int:
        """Lê o valor do Atributo escolhido no menu, direto dos contadores da ficha."""
        var = getattr(self, MAPA_ATRIBUTOS_TESTE.get(self.var_teste_atributo.get(), "var_fis"))
        return var.get()

    def rolar_teste_pericia_ficha(self) -> None:
        """Rola um Teste de Perícia (Poça de d20) com os valores atuais da ficha."""
        ajuste = int(self.var_teste_ajuste.get())
        cd_txt = self.var_teste_cd.get().strip()
        try:
            resultado = rolar_teste_pericia(
                atributo=self._valor_atributo_teste(),
                grau=MAPA_GRAUS_TESTE.get(self.var_teste_grau.get(), 0),
                vantagens=max(0, ajuste),
                desvantagens=max(0, -ajuste),
                cd=int(cd_txt) if cd_txt.isdigit() else None,
            )
        except ValueError as e:
            messagebox.showerror("Teste inválido", str(e), parent=self)
            return

        if resultado.sucesso is True:
            cor = COR_SUCESSO
        elif resultado.sucesso is False:
            cor = COR_PERIGO
        else:
            cor = self.tema["text"]

        self.lbl_teste_resultado.configure(text=resultado.detalhamento, text_color=cor)
        self.app_master.registrar_log(f"🎯 [{self.var_nome.get()}] {resultado.detalhamento}")

    def gerar_nome_pirata(self) -> None:
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

    def _abrir_ficha_do_bando(self, nome: str) -> None:
        """Duplo clique em um membro do bando abre a ficha dele na árvore."""
        abrir = getattr(self.app_master, "abrir_ficha_por_nome", None)
        if callable(abrir):
            abrir(nome)

    def lancar_bando_tracker(self):
        membros = list(self.listbox_bando.get(0, tk.END))
        if not membros:
            return

        # Se esta ficha está aberta em uma aba, usa o id real para o Tracker
        # conseguir ler e alterar o PV dela.
        item_id = next(
            (chave for chave, frame in self.app_master.abas_abertas.items() if frame is self),
            "chefe",
        )

        # Iniciativa 1d20 + Agilidade: conveniência de mesa (não é regra do livro).
        ini_chefe = random.randint(1, 20) + self.var_agi.get()
        nome_chefe = self.var_nome.get()
        ja_no_tracker = getattr(self.app_master, "_ja_esta_no_tracker", None)
        if ja_no_tracker is None or not ja_no_tracker(item_id, nome_chefe):
            self.app_master.tracker_data.append({"ini": ini_chefe, "id": item_id, "nome": nome_chefe, "status": [], "papel": "👑"})
            self.app_master.registrar_log(f"Iniciativa 👑 [{nome_chefe}]: {ini_chefe}")

        for m in membros:
            ini_bando = random.randint(1, 20)
            nome_limpo = re.sub(r" \[Lv\. .*?\]$", "", m)
            if ja_no_tracker is not None and ja_no_tracker("bando", nome_limpo):
                continue
            self.app_master.tracker_data.append({"ini": ini_bando, "id": "bando", "nome": nome_limpo, "status": [], "papel": "🛡️"})
            self.app_master.registrar_log(f"Iniciativa 🛡️ [{nome_limpo}]: {ini_bando}")
            
        self.app_master.atualizar_tracker_view()

    def exportar_markdown(self) -> None:
        caminho = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown", "*.md")], title="Salvar Ficha Markdown")
        if not caminho:
            return
        try:
            exportar_ficha_markdown(caminho, self.get_dados())
            messagebox.showinfo("Sucesso", "Ficha exportada com sucesso!", parent=self)
        except OSError as e:
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}", parent=self)

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
            ctk.CTkLabel(top, text="[ Sem Imagem ]", font=self.app_master.get_font('title'), text_color=COR_TEXTO_SUAVE).pack(expand=True)

    def expandir_historia(self) -> None:
        """Abre a história em um modal espaçoso, com Aplicar/Cancelar."""
        top = ctk.CTkToplevel(self)
        top.title(f"História — {self.var_nome.get()}")
        top.geometry("860x660")
        top.transient(self)
        top.configure(fg_color=self.tema["bg_main"])

        ctk.CTkLabel(
            top, text=f"História de {self.var_nome.get()}",
            font=self.app_master.get_font('title'), text_color=self.tema["accent"],
        ).pack(anchor="w", padx=18, pady=(14, 6))

        caixa = ctk.CTkTextbox(
            top, fg_color=self.tema["bg_input"], text_color=self.tema["text"],
            font=self.app_master.get_font('main'), wrap=tk.WORD,
            border_width=0, corner_radius=8,
        )
        caixa.pack(fill=tk.BOTH, expand=True, padx=18, pady=8)
        caixa.insert("1.0", self.texto_historia.get("1.0", tk.END).strip())

        barra = ctk.CTkFrame(top, fg_color="transparent")
        barra.pack(fill=tk.X, padx=18, pady=(0, 14))

        def aplicar() -> None:
            self.texto_historia.delete("1.0", tk.END)
            self.texto_historia.insert("1.0", caixa.get("1.0", tk.END).strip())
            top.destroy()

        ctk.CTkButton(barra, text="💾 Aplicar", command=aplicar, fg_color=self.tema["accent"], text_color="white", width=120).pack(side=tk.RIGHT)
        ctk.CTkButton(barra, text="Cancelar", command=top.destroy, fg_color=self.tema["bg_input"], hover_color=COR_HOVER, text_color=self.tema["text"], width=100).pack(side=tk.RIGHT, padx=(0, 8))

    def gerar_ia_local(self) -> None:
        """Gera (ou regera) a história do inimigo a partir dos dados da ficha."""
        perfil = {
            "nome": self.var_nome.get().strip() or "O desconhecido",
            "nivel": self._nivel_texto(),
            "fis": self.var_fis.get(),
            "agi": self.var_agi.get(),
            "int": self.var_int.get(),
            "inst": self.var_inst.get(),
            "luta": self.var_luta.get(),
            "acro": self.var_acro.get(),
            "recompensa": self.var_recompensa.get(),
        }
        historia = gerar_historia(perfil)

        # Substitui o bloco gerado anteriormente, em vez de empilhar histórias.
        if "inicio_ia" in self.texto_historia.mark_names():
            self.texto_historia.delete("inicio_ia", tk.END)

        inicio = self.texto_historia.index("end-1c")
        self.texto_historia.insert(tk.END, "\n\n--- IA Gerada ---\n" + historia)
        self.texto_historia.mark_set("inicio_ia", inicio)
        self.texto_historia.mark_gravity("inicio_ia", tk.LEFT)
        self.texto_historia.see(tk.END)
        self.app_master.registrar_log(f"🧠 História gerada para {perfil['nome']}.")

    def gerar_cartaz(self) -> None:
        """Gera o cartaz WANTED em PNG e abre a pré-visualização."""
        caminho = filedialog.asksaveasfilename(
            initialfile=f"WANTED_{self.var_nome.get()}.png",
            defaultextension=".png",
            filetypes=[("Imagem PNG", "*.png")],
            title="Salvar Cartaz de Procurado",
        )
        if not caminho:
            return
        try:
            gerar_cartaz_png(self.get_dados(), caminho, self.tema, self.imagem_original)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o cartaz: {e}", parent=self)
            return
        self._mostrar_cartaz(caminho)
        self.app_master.registrar_log(f"📜 Cartaz gerado para {self.var_nome.get()}.")

    def _mostrar_cartaz(self, caminho: str) -> None:
        """Pré-visualização do cartaz, com atalhos para abrir e copiar."""
        top = ctk.CTkToplevel(self)
        top.title("Cartaz de Procurado")
        top.geometry("520x780")
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema["bg_main"])

        foto = None
        try:
            imagem = Image.open(caminho)
            imagem.thumbnail((470, 650))
            foto = ImageTk.PhotoImage(imagem)
        except OSError:
            foto = None

        if foto is not None:
            rotulo = tk.Label(top, image=foto, bg=self.tema["bg_main"])
            rotulo.image = foto
            rotulo.pack(pady=12)

        acoes = ctk.CTkFrame(top, fg_color="transparent")
        acoes.pack(pady=6)
        if hasattr(os, "startfile"):
            ctk.CTkButton(acoes, text="📂 Abrir imagem", command=lambda: os.startfile(caminho)).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(
            acoes, text="📋 Copiar caminho",
            command=lambda: (self.clipboard_clear(), self.clipboard_append(caminho), top.destroy()),
        ).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(acoes, text="✖ Fechar", command=top.destroy, fg_color="transparent", text_color=COR_PERIGO, hover_color=COR_BOTAO_PERIGO).pack(side=tk.LEFT, padx=4)

    def carregar_imagem(self):
        caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.webp")])
        if caminho:
            try:
                self.caminho_imagem_salva = caminho
                self.imagem_original = _CACHE_IMAGENS.get(caminho)
                if self.imagem_original is None:
                    self.imagem_original = Image.open(caminho)
                    _CACHE_IMAGENS[caminho] = self.imagem_original
                self.escala_imagem = 180 / max(self.imagem_original.width, self.imagem_original.height)
                self.img_x, self.img_y = 90, 90
                self.atualizar_imagem()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao processar imagem.\n{str(e)}")

    def atualizar_imagem(self):
        if not self.imagem_original:
            return
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
        if not self.imagem_original:
            return
        self.img_x += event.x - self.last_mouse_x
        self.img_y += event.y - self.last_mouse_y
        self.last_mouse_x, self.last_mouse_y = event.x, event.y
        self.atualizar_imagem()

    def zoom_imagem(self, event):
        if not self.imagem_original:
            return
        if event.delta > 0 and self.escala_imagem < 10.0:
            self.escala_imagem *= 1.1 
        elif event.delta < 0 and self.escala_imagem > 0.05:
            self.escala_imagem *= 0.9
        self.atualizar_imagem()

    def _inserir_bloco_golpe(self, dados: dict) -> None:
        bloco = HabilidadeBloco(
            self.frame_lista_hab, dados, self.canvas_hab, self.painel_direito,
            self.app_master, ao_remover=self._remover_bloco,
        )
        self.blocos_habilidades.append(bloco)
        self.var_filtro_hab.set("Todas")
        self.filtrar_habilidades()
        self.app_master.registrar_log(f"✨ Golpe '{dados['titulo']}' ({dados['custo']}) gerado.")

    def abrir_gerador_golpe(self) -> None:
        """O Mestre escolhe o patamar; categoria e sabor saem da própria ficha."""
        item_id = next(
            (chave for chave, ficha in self.app_master.abas_abertas.items() if ficha is self),
            None,
        )
        faccao = self.app_master.faccao_do_item(item_id) if item_id else ""
        dados_ficha = self.get_dados()
        categoria = categoria_por_ficha(dados_ficha)
        sabor = sabor_por_faccao(faccao)
        sugestao = patamar_por_nivel(int(self._nivel_texto()))

        top = ctk.CTkToplevel(self)
        top.title("Gerar Golpe")
        top.geometry("400x320")
        top.transient(self)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema["bg_main"])

        ctk.CTkLabel(top, text="✨ Gerar Golpe", font=self.app_master.get_font('title'), text_color=self.tema["accent"]).pack(pady=(14, 4))
        ctk.CTkLabel(top, text="Escolha o patamar", font=self.app_master.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)

        var_patamar = tk.StringVar(value=sugestao)
        ctk.CTkSegmentedButton(
            top, variable=var_patamar, values=list(PATAMARES_GOLPE),
            fg_color=self.tema["bg_input"], selected_color=self.tema["accent"],
            selected_hover_color=self.tema.get("accent_hover", self.tema["accent"]),
            unselected_color=self.tema["bg_input"], text_color=self.tema["text"],
        ).pack(fill=tk.X, padx=20)

        ctk.CTkLabel(
            top,
            text=(f"Automático pela ficha: categoria {categoria}, sabor {sabor}.\n"
                  f"Sugestão para o Nível {self._nivel_texto()}: {sugestao}."),
            font=self.app_master.get_font('small'), text_color=COR_TEXTO_SUAVE,
            justify="left", wraplength=350,
        ).pack(anchor="w", padx=20, pady=(10, 0))

        def gerar() -> None:
            dados = gerar_golpe(var_patamar.get(), categoria, sabor, self.var_nome.get())
            self._inserir_bloco_golpe(dados)
            top.destroy()

        ctk.CTkButton(top, text="Gerar golpe", command=gerar, fg_color=self.tema["accent"], text_color="white").pack(fill=tk.X, padx=20, pady=18)

    def inserir_habilidade(self, patamar: str) -> None:
        """Insere um bloco em branco usando a tabela única de patamares."""
        alcances = {
            "Básica": "Corpo a corpo",
            "Média": "9 m",
            "Forte": "Cone 4,5 m",
            "Suprema": "Área 6 m",
            "Outros": "-",
        }
        base = PATAMARES_GOLPE.get(patamar)
        if base:
            dados = {
                "custo": str(base["custo"]),
                "limite": str(base["limite"]),
                "execucao": "1 Ação",
                "alcance": alcances.get(patamar, "Corpo a corpo"),
            }
        else:
            dados = {"custo": "X PE", "limite": "-", "execucao": "Reação", "alcance": "-"}
        dados["titulo"] = f"Nova Habilidade - {patamar}"
        dados["conteudo"] = ""
        bloco = HabilidadeBloco(
            self.frame_lista_hab, dados, self.canvas_hab, self.painel_direito,
            self.app_master, ao_remover=self._remover_bloco,
        )
        self.blocos_habilidades.append(bloco)
        self.var_filtro_hab.set("Todas")
        self.filtrar_habilidades()

    def _remover_bloco(self, bloco: HabilidadeBloco) -> None:
        """Remove da lista o bloco fechado pelo ✖ (chamado pelo próprio bloco)."""
        if bloco in self.blocos_habilidades:
            self.blocos_habilidades.remove(bloco)

    def filtrar_habilidades(self, escolha=None):
        escolha = self.var_filtro_hab.get().lower()
        for bloco in self.blocos_habilidades:
            if bloco.winfo_exists():
                bloco.pack_forget()
                
        for bloco in self.blocos_habilidades:
            if not bloco.winfo_exists():
                continue
            titulo = bloco.var_titulo.get().lower()
            execucao = bloco.var_exec.get().lower()
            
            if escolha == "todas" or escolha in titulo or escolha in execucao:
                bloco.pack(fill=tk.X, pady=8, padx=10)

    def get_dados(self):
        habs = [b.get_dados() for b in self.blocos_habilidades if b.winfo_exists()]
        return {
            "nome": self.var_nome.get(),
            "recompensa": re.sub(r"\D", "", self.var_recompensa.get()),
            "pv": self.pv_atual.get(),
            "pe": self.pe_atual.get(),
            "pv_max": self.pv_max.get(),
            "pe_max": self.pe_max.get(),
            "nivel": self._nivel_texto(),
            "fis": min(5, max(0, self.var_fis.get())),
            "agi": min(5, max(0, self.var_agi.get())),
            "int": min(5, max(0, self.var_int.get())),
            "inst": min(5, max(0, self.var_inst.get())),
            "luta": min(3, max(0, self.var_luta.get())),
            "acro": min(3, max(0, self.var_acro.get())),
            "mod_passiva": self.mod_passiva.get(),
            "mod_bloq": self.mod_bloq.get(),
            "mod_esq": self.mod_esq.get(),
            "mod_cd": self.mod_cd.get(),
            "mod_pv": self.mod_pv.get(),
            "mod_pe": self.mod_pe.get(),
            "historia": self.texto_historia.get("1.0", tk.END).strip(),
            "loot": self.texto_loot.get("1.0", tk.END).strip(),
            "bando": list(self.listbox_bando.get(0, tk.END)),
            "imagem": self.caminho_imagem_salva,
            "escala": self.escala_imagem,
            "img_x": self.img_x,
            "img_y": self.img_y,
            "habilidades": habs
        }

    def atualizar_dados_rapidos(self, d: dict) -> None:
        """Sincroniza só o essencial quando uma aba em cache é reaberta.

        Evita reconstruir imagem e habilidades (o que causava a travadinha).
        """
        self.var_nome.set(d.get("nome", self.var_nome.get()))
        self.var_nivel.set(str(d.get("nivel", self._nivel_texto())))
        self.sincronizar_agora()
        try:
            pv = int(d.get("pv", self.pv_atual.get()) or 0)
            pe = int(d.get("pe", self.pe_atual.get()) or 0)
        except (TypeError, ValueError):
            return
        self.pv_atual.set(max(0, min(pv, self.pv_max.get())))
        self.pe_atual.set(max(0, min(pe, self.pe_max.get())))

    def carregar_dados(self, d):
        # Copia antes de mexer nos campos: o trace de Nome/Nível grava de volta no
        # dicionário original da árvore e acabaria apagando o Nível salvo.
        d = dict(d)
        self.var_nome.set(d.get("nome", "Novo Inimigo"))
        recomp_salva = re.sub(r"\D", "", str(d.get("recompensa", "0")))
        self.var_recompensa.set(f"{int(recomp_salva):,}".replace(",", ".") if recomp_salva else "0")
        
        self.var_nivel.set(d.get("nivel", "1"))
        self.var_fis.set(max(0, min(5, int(d.get("fis", 1) or 1))))
        self.var_agi.set(max(0, min(5, int(d.get("agi", 1) or 1))))
        self.var_int.set(max(0, min(5, int(d.get("int", 1) or 1))))
        self.var_inst.set(max(0, min(5, int(d.get("inst", 1) or 1))))
        self.var_luta.set(max(0, min(3, int(d.get("luta", 0) or 0))))
        self.var_acro.set(max(0, min(3, int(d.get("acro", 0) or 0))))
        
        self.mod_passiva.set(d.get("mod_passiva", 0))
        self.mod_bloq.set(d.get("mod_bloq", 0))
        self.mod_esq.set(d.get("mod_esq", 0))
        self.mod_cd.set(d.get("mod_cd", 0))
        self.mod_pv.set(d.get("mod_pv", 0))
        self.mod_pe.set(d.get("mod_pe", 0))

        # Os traces acima apenas agendam o cálculo; força agora para que os
        # máximos estejam prontos antes de restaurar PV/PE.
        if self._calc_agendado is not None:
            try:
                self.after_cancel(self._calc_agendado)
            except tk.TclError:
                pass
            self._calc_agendado = None
        self.calcular_derivados()

        # PV e PE por último: os Atributos acima já recalcularam os máximos,
        # então o valor salvo não é mais limitado por um máximo parcial.
        pv_salvo = int(d.get("pv", self.pv_max.get()) or 0)
        pe_salvo = int(d.get("pe", self.pe_max.get()) or 0)
        self.pv_atual.set(max(0, min(pv_salvo, self.pv_max.get())))
        self.pe_atual.set(max(0, min(pe_salvo, self.pe_max.get())))

        self.texto_historia.insert(tk.END, d.get("historia", ""))
        self.texto_loot.insert(tk.END, d.get("loot", ""))
        
        # Bando compartilhado: fichas antigas contribuem com seus membros, mas
        # nunca apagam o bando global ao abrir.
        for minion in d.get("bando", []):
            if minion not in self.app_master.bando_global:
                self.app_master.bando_global.append(minion)
        self.listbox_bando.recarregar()
        if d.get("imagem") and os.path.exists(d["imagem"]):
            try:
                self.caminho_imagem_salva = d["imagem"]
                self.imagem_original = _CACHE_IMAGENS.get(self.caminho_imagem_salva)
                if self.imagem_original is None:
                    self.imagem_original = Image.open(self.caminho_imagem_salva)
                    _CACHE_IMAGENS[self.caminho_imagem_salva] = self.imagem_original
                self.escala_imagem = d.get("escala", 1.0)
                self.img_x, self.img_y = d.get("img_x", 90), d.get("img_y", 90)
                self.atualizar_imagem()
            except Exception:
                self.canvas_img.create_text(90, 90, text="[ Imagem Ausente ]", fill=COR_TEXTO_SUAVE)

        for hab in d.get("habilidades", []):
            bloco = HabilidadeBloco(
                self.frame_lista_hab, hab, self.canvas_hab, self.painel_direito,
                self.app_master, ao_remover=self._remover_bloco,
            )
            self.blocos_habilidades.append(bloco)

    def sortear_loot(self) -> None:
        """Gera loot considerando Nível, Atributos e a facção (pasta) da ficha."""
        item_id = next(
            (chave for chave, ficha in self.app_master.abas_abertas.items() if ficha is self),
            None,
        )
        faccao = self.app_master.faccao_do_item(item_id) if item_id else ""
        resultado = gerar_loot_aleatorio(self._nivel_texto(), dados=self.get_dados(), faccao=faccao)
        self.texto_loot.delete("1.0", tk.END)
        self.texto_loot.insert(tk.END, resultado)