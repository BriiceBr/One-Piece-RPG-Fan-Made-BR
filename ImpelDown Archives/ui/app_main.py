import os
import json
import random
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from config import TEMAS, FONTES_DISPONIVEIS, NOME_SISTEMA
from ui.popups import ToolTip, CTkPopUpInput
from ui.widgets_custom import DraggableNotebook
from ui.ficha_frame import FichaPersonagemFrame
from core.combate import calcular_dificuldade_encontro, nivel_seguro
from core.condicoes import CONDICOES, icone as icone_condicao, nome as nome_condicao, resumo as resumo_condicao
from core.regras import calcular_atributos_derivados
from utils.arquivos import exportar_ficha_json, importar_ficha_json, salvar_banco_sqlite, carregar_banco_sqlite

#: Duração padrão (em turnos) ao aplicar uma condição no Tracker.
TURNOS_PADRAO = 3


def montar_ficha(
    nome: str,
    nivel: int = 1,
    fis: int = 1,
    agi: int = 1,
    intel: int = 1,
    inst: int = 1,
    luta: int = 0,
    acro: int = 0,
    recompensa: str = "0",
) -> dict:
    """Ficha completa, com Atributos e recursos já calculados.

    Evita o problema de fichas criadas "pela metade" (sem Físico/Intelecto), que
    depois abriam com PV limitado a um máximo calculado com Atributos zerados.
    """
    res = calcular_atributos_derivados(nivel, fis, agi, intel, inst, luta, acro)
    return {
        "nome": nome, "nivel": str(nivel), "recompensa": recompensa,
        "fis": fis, "agi": agi, "int": intel, "inst": inst,
        "luta": luta, "acro": acro,
        "pv": res["pv"], "pv_max": res["pv"],
        "pe": res["pe"], "pe_max": res["pe"],
        "historia": "", "loot": "", "bando": [],
    }

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
        self.turno_atual_idx = 0
        self.rodada_atual = 1

        self._busca_agendada = None
        self.arvore_cache = None
        self._menu_aberto = None
        self._hover_arvore = None
        self._hover_tracker_chave = None
        self._log_linhas: list[str] = []
        self.janela_log = None
        self.caixa_log = None

        self.montar_menus()
        self.montar_layout_principal()
        self.inicializar_arvore_padrao()
        self.configurar_atalhos()
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

    def ao_fechar(self) -> None:
        """Pergunta se quer salvar antes de fechar (evita perder o progresso)."""
        tem_dados = bool(self.abas_abertas or self.tracker_data)
        if not tem_dados:
            self.root.destroy()
            return

        if self.arquivo_atual:
            resposta = messagebox.askyesnocancel("Sair", "Salvar o cofre antes de fechar?")
            if resposta is None:
                return
            if resposta and not self.salvar_banco():
                return
            self.root.destroy()
            return

        resposta = messagebox.askyesnocancel(
            "Sair", "O cofre ainda não foi salvo. Deseja salvar antes de fechar?"
        )
        if resposta is None:
            return
        if resposta and not self.salvar_como_banco():
            return
        self.root.destroy()

    def configurar_atalhos(self):
        self.root.bind("<Control-s>", lambda e: self.salvar_banco())
        self.root.bind("<Control-n>", lambda e: self.adicionar_personagem())
        self.root.bind("<Control-f>", lambda e: self.focar_pesquisa())
        self.root.bind("<F5>", self._atalho_rolar_pasta)
        self.root.bind("<space>", self._atalho_proximo_turno)
        self.root.bind("<Key-d>", lambda e: self._atalho_pv(-1))
        self.root.bind("<Key-D>", lambda e: self._atalho_pv(-1))
        self.root.bind("<Key-c>", lambda e: self._atalho_pv(1))
        self.root.bind("<Key-C>", lambda e: self._atalho_pv(1))
        self.root.bind("<Escape>", self._atalho_limpar_selecao)
        for numero in range(1, 10):
            self.root.bind(str(numero), lambda e, n=numero: self._atalho_selecionar(n))

    def _editando_texto(self) -> bool:
        """True quando o foco está em um campo de texto (atalhos não devem agir)."""
        foco = self.root.focus_get()
        if foco is None:
            return False
        try:
            return foco.winfo_class() in ("Entry", "TEntry", "Text", "Spinbox")
        except tk.TclError:
            return False

    def _atalho_proximo_turno(self, event=None):
        if self._editando_texto():
            return
        self.proximo_turno()
        return "break"

    def _atalho_pv(self, sinal: int):
        if self._editando_texto():
            return
        self.ajustar_pv_do_turno(sinal)
        return "break"

    def _atalho_rolar_pasta(self, event=None):
        if self._editando_texto():
            return
        self.rolar_iniciativa_pasta()
        return "break"

    def _atalho_limpar_selecao(self, event=None):
        if self._editando_texto():
            return
        self.lista_iniciativa.selection_clear(0, tk.END)
        return "break"

    def _atalho_selecionar(self, numero: int):
        if self._editando_texto():
            return
        indice = numero - 1
        if 0 <= indice < self.lista_iniciativa.size():
            self.lista_iniciativa.selection_clear(0, tk.END)
            self.lista_iniciativa.selection_set(indice)
        return "break"

    def focar_pesquisa(self):
        if not self.tree_visivel:
            self.toggle_tree()
        self.entry_pesquisa.focus_set()

    def get_font(self, type_style="main"):
        if type_style == "bold":
            return (self.current_font, 12, "bold")
        if type_style == "title":
            return (self.current_font, 16, "bold")
        if type_style == "small":
            return (self.current_font, 10)
        if type_style == "number":
            return (self.current_font, 20, "bold")
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
            self.root.title(f"{NOME_SISTEMA} | {nome}")
        else:
            self.root.title(f"{NOME_SISTEMA} | Sem Título")

    def mudar_tema(self, escolha: str) -> None:
        """Troca a paleta e reaplica em todo o shell e nas abas abertas."""
        anterior = self.tema_atual
        self.tema_atual = TEMAS[escolha]
        if hasattr(self, "var_tema") and self.var_tema.get() != escolha:
            self.var_tema.set(escolha)
        self.root.configure(bg=self.tema_atual["bg_sidebar"])
        self.barra_ferramentas.configure(fg_color=self.tema_atual["bg_sidebar"])
        self.frame_tree.configure(fg_color=self.tema_atual["bg_sidebar"])
        self.frame_tracker.configure(fg_color=self.tema_atual["bg_sidebar"])
        self.notebook_frame.configure(fg_color=self.tema_atual["bg_main"])
        self.lista_iniciativa.configure(
            bg=self.tema_atual["bg_sidebar"], fg=self.tema_atual["text"],
            selectbackground=self.tema_atual["accent"],
        )
        self.frame_turno.configure(fg_color=self.tema_atual["bg_card"])
        self.lbl_turno_nome.configure(text_color=self.tema_atual["accent"])
        self.lbl_turno_recursos.configure(text_color=self.tema_atual["text"])
        self.btn_log.configure(text_color=self.tema_atual["text"])
        if self.janela_log is not None and self.janela_log.winfo_exists() and self.caixa_log is not None:
            self.janela_log.configure(fg_color=self.tema_atual["bg_card"])
            self.caixa_log.configure(fg_color=self.tema_atual["bg_sidebar"], text_color=self.tema_atual["text"])
        for botao in getattr(self, "_botoes_barra", []):
            botao.configure(fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"])
        for menu_topo in getattr(self, "_menus_barra", []):
            menu_topo.configure(fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"])
        for menu_tk in (self.menu_bar, self.menu_arq, self.menu_ferramentas):
            menu_tk.configure(
                bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"],
                activebackground=self.tema_atual["accent"],
            )
        self.aplicar_tema_style()
        self._reaplicar_cores_botoes(anterior)
        self._reconstruir_abas()

    def _reaplicar_cores_botoes(self, anterior: dict) -> None:
        """Repinta botões das laterais que nasceram com as cores do tema antigo."""
        mapa = {
            anterior["accent"]: self.tema_atual["accent"],
            anterior["bg_input"]: self.tema_atual["bg_input"],
            anterior["bg_card"]: self.tema_atual["bg_card"],
            anterior["bg_sidebar"]: self.tema_atual["bg_sidebar"],
            "#363636": self.tema_atual["bg_input"],
            "#4a4a4a": self.tema_atual["bg_input"],
        }
        mapa_texto = {anterior["text"]: self.tema_atual["text"], "#dcddde": self.tema_atual["text"]}

        def repintar(widget: tk.Misc) -> None:
            for filho in widget.winfo_children():
                if isinstance(filho, ctk.CTkButton):
                    try:
                        cor = filho.cget("fg_color")
                        if isinstance(cor, str) and cor in mapa:
                            filho.configure(fg_color=mapa[cor])
                        cor_texto = filho.cget("text_color")
                        if isinstance(cor_texto, str) and cor_texto in mapa_texto:
                            filho.configure(text_color=mapa_texto[cor_texto])
                    except (ValueError, tk.TclError):
                        pass
                repintar(filho)

        for raiz in (self.frame_tree, self.frame_tracker):
            repintar(raiz)

    def mudar_fonte(self, escolha: str) -> None:
        self.current_font = escolha
        self.aplicar_tema_style()
        self.lista_iniciativa.configure(font=self.get_font('main'))
        self._reconstruir_abas()

    def _reconstruir_abas(self) -> None:
        """Fecha e reabre as abas para aplicar tema/fonte em todos os widgets.

        O CustomTkinter não tem "herança" de tema: cada widget guarda as cores do
        momento em que foi criado. Reabrir as abas é a forma barata de manter a
        coerência sem um registro gigante de widgets.
        """
        if not self.abas_abertas:
            return
        dados = {item_id: ficha.get_dados() for item_id, ficha in self.abas_abertas.items()}
        self._fechar_todas_as_abas()
        self.dados_banco.update(dados)
        for item_id, info in dados.items():
            if self.tree.exists(item_id):
                self.abrir_aba_personagem(item_id, info.get("nome", "Ficha"))

    def montar_menus(self):
        self.menu_bar = tk.Menu(self.root, bg="#262626", fg="#dcddde", bd=0)
        self.root.config(menu=self.menu_bar)

        self.menu_arq = tk.Menu(self.menu_bar, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
        self.menu_arq.add_command(label="Novo Cofre", command=self.novo_banco)
        self.menu_arq.add_command(label="Abrir Cofre...", command=self.carregar_banco)
        self.menu_arq.add_separator()
        self.menu_arq.add_command(label="Salvar (Ctrl+S)", command=self.salvar_banco)
        self.menu_arq.add_command(label="Salvar Como...", command=self.salvar_como_banco)
        self.menu_arq.add_separator()
        self.menu_arq.add_command(label="Sair", command=self.ao_fechar)
        self.menu_bar.add_cascade(label="Cofre", menu=self.menu_arq)

        self.menu_ferramentas = tk.Menu(self.menu_bar, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
        self.menu_ferramentas.add_command(label="📊 Estatísticas da Campanha", command=self.exibir_estatisticas_campanha)
        self.menu_ferramentas.add_command(label="👥 Gerar Lacaios em Massa", command=self.gerar_lacaios_massa)
        self.menu_ferramentas.add_command(label="📥 Importar Ficha (.json)", command=self.importar_ficha_individual)
        self.menu_bar.add_cascade(label="Ferramentas", menu=self.menu_ferramentas)

        self.barra_ferramentas = ctk.CTkFrame(self.root, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.barra_ferramentas.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        self._botoes_barra: list[ctk.CTkButton] = []
        self._menus_barra: list[ctk.CTkOptionMenu] = []

        self.btn_toggle_tree = ctk.CTkButton(self.barra_ferramentas, text="≡ Pastas", command=self.toggle_tree, fg_color=self.tema_atual["bg_input"], hover_color="#4a4a4a", text_color=self.tema_atual["text"], width=100)
        self.btn_toggle_tree.pack(side=tk.LEFT)
        self._botoes_barra.append(self.btn_toggle_tree)
        self.tree_visivel = True

        self.var_tema = ctk.StringVar(value="Obsidian (Padrão)")
        self.menu_temas = ctk.CTkOptionMenu(self.barra_ferramentas, variable=self.var_tema, values=list(TEMAS.keys()), command=self.mudar_tema, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], width=160)
        self.menu_temas.pack(side=tk.LEFT, padx=(20, 10))
        self._menus_barra.append(self.menu_temas)

        self.var_fonte = ctk.StringVar(value="Segoe UI")
        self.menu_fontes = ctk.CTkOptionMenu(self.barra_ferramentas, variable=self.var_fonte, values=FONTES_DISPONIVEIS, command=self.mudar_fonte, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], width=130)
        self.menu_fontes.pack(side=tk.LEFT)
        self._menus_barra.append(self.menu_fontes)

        self.btn_toggle_tracker = ctk.CTkButton(self.barra_ferramentas, text="≡ Tracker", command=self.toggle_tracker, fg_color=self.tema_atual["bg_input"], hover_color="#4a4a4a", text_color=self.tema_atual["text"], width=100)
        self.btn_toggle_tracker.pack(side=tk.RIGHT)
        self._botoes_barra.append(self.btn_toggle_tracker)
        self.tracker_visivel = False

    def mapear_arvore_completa(self, node=""):
        res = []
        for child in self.tree.get_children(node):
            item = self.tree.item(child)
            res.append({
                "id": child,
                "text": item["text"],
                "tags": item["tags"],
                "open": self.tree.item(child, "open"),
                "filhos": self.mapear_arvore_completa(child)
            })
        return res

    def pesquisar_arvore(self, *args) -> None:
        """Agenda a pesquisa (debounce): não reconstrói a árvore a cada tecla."""
        if self._busca_agendada is not None:
            try:
                self.root.after_cancel(self._busca_agendada)
            except tk.TclError:
                pass
        self._busca_agendada = self.root.after(160, self._aplicar_pesquisa)

    def _aplicar_pesquisa(self) -> None:
        self._busca_agendada = None
        termo = self.var_pesquisa.get().lower().strip()

        if not termo and self.arvore_cache is None:
            # Nada foi filtrado ainda: não há por que reconstruir a árvore.
            return
        
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
                if manter_tudo or match_self:
                    n_copy = n.copy()
                    n_copy["filhos"] = filtrar(n["filhos"], manter_tudo=True)
                    result.append(n_copy)
                else:
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

        self.tooltip = ToolTip(self.root)

        self.frame_tree = ctk.CTkFrame(self.container_principal, width=280, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.frame_tree.pack_propagate(False)
        self.frame_tree.pack(side=tk.LEFT, fill=tk.Y)

        topo_tree = ctk.CTkFrame(self.frame_tree, fg_color="transparent")
        topo_tree.pack(fill=tk.X, padx=15, pady=(15, 5))
        ctk.CTkLabel(topo_tree, text="PASTAS", font=("Segoe UI", 12, "bold"), text_color="#8b8c8f").pack(side=tk.LEFT)
        
        self.var_pesquisa = tk.StringVar()
        self.var_pesquisa.trace_add("write", self.pesquisar_arvore)
        self.entry_pesquisa = ctk.CTkEntry(topo_tree, textvariable=self.var_pesquisa, placeholder_text="🔍 Buscar (Ctrl+F)...", height=24, fg_color="#363636", border_width=0)
        self.entry_pesquisa.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10,0))
        
        self.tree = ttk.Treeview(self.frame_tree, selectmode="browse", show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

        self.tree.bind("<ButtonPress-1>", self.iniciar_drag_tree)
        self.tree.bind("<ButtonRelease-1>", self.soltar_drag_tree)
        self.tree.bind("<ButtonRelease-1>", self.ao_clicar_arvore, add="+")
        self.tree.bind("<Button-3>", self.abrir_menu_contexto)
        self.tree.bind("<Delete>", lambda e: self.deletar_item())
        self.tree.bind("<Motion>", self.hover_treeview)
        self.tree.bind("<Leave>", self.sair_da_arvore)
        self.item_arrastado = None
        self._press_xy = None

        f_botoes = ctk.CTkFrame(self.frame_tree, fg_color="transparent")
        f_botoes.pack(fill=tk.X, pady=15, padx=15)
        
        ctk.CTkButton(f_botoes, text="+ Pasta", command=self.adicionar_pasta, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="+ Ficha", command=self.adicionar_personagem, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="✎ Renomear", command=self.renomear_item, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="✖ Deletar", command=self.deletar_item, fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75").grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        f_botoes.columnconfigure(0, weight=1)
        f_botoes.columnconfigure(1, weight=1)

        self.notebook_frame = ctk.CTkFrame(self.container_principal, fg_color=self.tema_atual["bg_main"], corner_radius=0)
        self.notebook_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.notebook = DraggableNotebook(self.notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Button-2>", self.fechar_aba_com_click_meio)
        self.abas_abertas = {}

        self.frame_tracker = ctk.CTkFrame(self.container_principal, width=280, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.frame_tracker.pack_propagate(False)
        
        topo_trk = ctk.CTkFrame(self.frame_tracker, fg_color="transparent")
        topo_trk.pack(fill=tk.X, padx=20, pady=(15, 2))
        ctk.CTkLabel(topo_trk, text="COMBAT TRACKER", font=("Segoe UI", 12, "bold"), text_color="#8b8c8f", anchor="w").pack(side=tk.LEFT)
        self.btn_log = ctk.CTkButton(topo_trk, text="📜 Log", width=64, height=22, fg_color="transparent", hover_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], command=self.alternar_log)
        self.btn_log.pack(side=tk.RIGHT)
        
        self.lbl_dificuldade = ctk.CTkLabel(self.frame_tracker, text="Encontro: Sem Inimigos", font=("Segoe UI", 10, "bold"), text_color="#8b8c8f", anchor="w")
        self.lbl_dificuldade.pack(fill=tk.X, padx=20, pady=(0, 5))

        self.lbl_rodada = ctk.CTkLabel(self.frame_tracker, text="Rodada 1", font=("Segoe UI", 11, "bold"), text_color=self.tema_atual["accent"], anchor="w")
        self.lbl_rodada.pack(fill=tk.X, padx=20, pady=(0, 5))

        # Painel do turno atual: tudo o que o Mestre precisa, sem abrir ficha.
        self.frame_turno = ctk.CTkFrame(self.frame_tracker, fg_color=self.tema_atual["bg_card"], corner_radius=8)
        self.frame_turno.pack(fill=tk.X, padx=15, pady=(0, 4))
        self.lbl_turno_nome = ctk.CTkLabel(self.frame_turno, text="Sem combate", font=self.get_font('bold'), text_color=self.tema_atual["accent"], anchor="w")
        self.lbl_turno_nome.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.lbl_turno_recursos = ctk.CTkLabel(self.frame_turno, text="PV —    PE —", font=self.get_font('small'), text_color=self.tema_atual["text"], anchor="w")
        self.lbl_turno_recursos.pack(fill=tk.X, padx=10)
        self.lbl_turno_defesas = ctk.CTkLabel(self.frame_turno, text="Def: — | Bloq: — | Esq: — | CD: —", font=self.get_font('small'), text_color="#8b8c8f", anchor="w")
        self.lbl_turno_defesas.pack(fill=tk.X, padx=10)
        self.lbl_turno_condicoes = ctk.CTkLabel(self.frame_turno, text="Sem condições.", font=self.get_font('small'), text_color="#e5b55e", anchor="w", justify="left", wraplength=230)
        self.lbl_turno_condicoes.pack(fill=tk.X, padx=10, pady=(0, 4))

        self.lista_iniciativa = tk.Listbox(self.frame_tracker, bg=self.tema_atual["bg_sidebar"], fg=self.tema_atual["text"], font=self.get_font('main'), selectbackground=self.tema_atual["accent"], bd=0, highlightthickness=0, exportselection=False, activestyle="none")
        self.lista_iniciativa.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.lista_iniciativa.bind("<Button-3>", self.menu_condicoes_tracker)
        self.lista_iniciativa.bind("<Button-1>", self.clicar_tracker_vazio)
        self.lista_iniciativa.bind("<Motion>", self.hover_tracker)
        self.lista_iniciativa.bind("<Leave>", self.sair_do_tracker)
        
        f_trk_btn = ctk.CTkFrame(self.frame_tracker, fg_color="transparent")
        f_trk_btn.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkButton(f_trk_btn, text="▶ Próximo Turno", command=self.proximo_turno, fg_color=self.tema_atual["accent"], text_color="white").pack(fill=tk.X, pady=2)

        f_pv_btn = ctk.CTkFrame(f_trk_btn, fg_color="transparent")
        f_pv_btn.pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_pv_btn, text="⚔️ Dano", command=lambda: self.ajustar_pv_do_turno(-1), fg_color="#5c2b29", hover_color="#7a3a37", text_color="#ffdede").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        ctk.CTkButton(f_pv_btn, text="💚 Cura", command=lambda: self.ajustar_pv_do_turno(1), fg_color="#2f4a2f", hover_color="#3d5f3d", text_color="#e6ffe6").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        ctk.CTkButton(f_trk_btn, text="Adicionar Ficha", command=self.add_tracker, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_trk_btn, text="🎲 Rolar Pasta", command=self.rolar_iniciativa_pasta, fg_color="#363636", hover_color="#4a4a4a", text_color="#dcddde").pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_trk_btn, text="Limpar Tracker", command=self.limpar_tracker, fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75").pack(fill=tk.X, pady=2)

    def proximo_turno(self):
        if not self.tracker_data:
            return
        self.turno_atual_idx += 1
        if self.turno_atual_idx >= len(self.tracker_data):
            self.turno_atual_idx = 0
            self.rodada_atual += 1
            self.registrar_log(f"--- Rodada {self.rodada_atual} iniciada ---")
        
        self.lbl_rodada.configure(text=f"Rodada {self.rodada_atual}")
        self._temporizar_turno()
        self.atualizar_tracker_view()
        
        atual = self.tracker_data[self.turno_atual_idx]
        self.registrar_log(f"Vez de: {atual['nome']}")

    def _temporizar_turno(self) -> None:
        """Desconta 1 turno das condições de quem está começando o turno."""
        if not self.tracker_data:
            return
        alvo = self.tracker_data[self.turno_atual_idx]
        restantes: list[dict] = []
        for cond in self._condicoes_linha(alvo):
            if cond["turnos"] is None:
                restantes.append(cond)
                continue
            cond["turnos"] -= 1
            if cond["turnos"] > 0:
                restantes.append(cond)
            else:
                self.registrar_log(f"⏱ {nome_condicao(cond['chave'])} terminou em {alvo['nome']}.")
        alvo["status"] = restantes

    def inicializar_arvore_padrao(self):
        cat_m = self.tree.insert("", "end", text=" Monstros", open=True, tags=("pasta",))
        cat_v = self.tree.insert("", "end", text=" Vilões", open=True, tags=("pasta",))

        id_arlong = self.tree.insert(cat_v, "end", text=" Arlong [Lv. 3]", tags=("ficha",))
        self.dados_banco[id_arlong] = montar_ficha("Arlong", 3, 4, 2, 1, 2, 2, 0, "20000000")

        id_rei = self.tree.insert(cat_m, "end", text=" Rei dos Mares [Lv. 5]", tags=("ficha",))
        self.dados_banco[id_rei] = montar_ficha("Rei dos Mares", 5, 5, 1, 1, 3, 1, 0)

    def abrir_menu_contexto(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            tags = self.tree.item(item, "tags")
            menu = tk.Menu(self.root, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
            menu.add_command(label="✎ Renomear", command=self.renomear_item)
            if "ficha" in tags:
                menu.add_command(label="📋 Duplicar Ficha", command=lambda: self.duplicar_ficha(item))
                menu.add_command(label="📤 Exportar Ficha (.json)", command=lambda: self.exportar_ficha_individual(item))
            elif "pasta" in tags:
                menu.add_command(label="📁 Nova Pasta", command=self.adicionar_pasta)
                menu.add_command(label="📄 Nova Ficha", command=self.adicionar_personagem)
            menu.add_separator()
            menu.add_command(label="✖ Deletar (Del)", command=self.deletar_item)
            self._postar_menu(menu, event.x_root, event.y_root)

    def exportar_ficha_individual(self, item_id):
        if item_id in self.abas_abertas:
            dados = self.abas_abertas[item_id].get_dados()
        else:
            dados = self.dados_banco.get(item_id, {})
            
        nome = dados.get("nome", "Ficha")
        caminho = filedialog.asksaveasfilename(initialfile=f"{nome}.json", defaultextension=".json", filetypes=[("Arquivo JSON", "*.json")], title="Exportar Ficha")
        if caminho:
            exportar_ficha_json(caminho, dados)
            messagebox.showinfo("Sucesso", f"Ficha {nome} exportada com sucesso!")

    def importar_ficha_individual(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivo JSON", "*.json")], title="Importar Ficha")
        if caminho:
            try:
                dados = importar_ficha_json(caminho)
                sel = self.tree.selection()
                pai = sel[0] if sel and "pasta" in self.tree.item(sel[0], "tags") else ""
                nome_unico = self.gerar_nome_unico(dados.get("nome", "Importado"), pai)
                dados["nome"] = nome_unico
                nivel = dados.get("nivel", "1")
                novo_id = self.tree.insert(pai, "end", text=f" {nome_unico} [Lv. {nivel}]", tags=("ficha",))
                self.dados_banco[novo_id] = dados
                messagebox.showinfo("Sucesso", f"Ficha {nome_unico} importada com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao importar ficha: {e}")

    def duplicar_ficha(self, item_id):
        if self.bloquear_se_buscando():
            return
        pai = self.tree.parent(item_id)
        dados_originais = self.dados_banco.get(item_id, {})
        novo_nome = self.gerar_nome_unico(f"{dados_originais.get('nome', 'Cópia')} (Cópia)", pai)
        novos_dados = json.loads(json.dumps(dados_originais))
        novos_dados["nome"] = novo_nome
        nivel = novos_dados.get("nivel", "1")
        novo_id = self.tree.insert(pai, "end", text=f" {novo_nome} [Lv. {nivel}]", tags=("ficha",))
        self.dados_banco[novo_id] = novos_dados

    def gerar_lacaios_massa(self):
        sel = self.tree.selection()
        pai = sel[0] if sel and "pasta" in self.tree.item(sel[0], "tags") else ""
        
        nome_base = CTkPopUpInput.pedir_texto("Gerar Lacaios", "Nome base dos lacaios (ex: Marinheiro):")
        if not nome_base:
            return
        qtd = CTkPopUpInput.pedir_numero("Quantidade", "Quantos lacaios criar?")
        if not qtd:
            return

        for i in range(1, qtd + 1):
            nome_lacaio = f"{nome_base} {i:02d}"
            novo_id = self.tree.insert(pai, "end", text=f" {nome_lacaio} [Lv. 1]", tags=("ficha",))
            self.dados_banco[novo_id] = montar_ficha(nome_lacaio)

        self.registrar_log(f"Gerados {qtd}x lacaios '{nome_base}'.")

    def exibir_estatisticas_campanha(self):
        total_fichas = 0
        total_pastas = 0
        soma_recompensas = 0
        soma_niveis = 0

        def percorrer(node):
            nonlocal total_fichas, total_pastas, soma_recompensas, soma_niveis
            for child in self.tree.get_children(node):
                tags = self.tree.item(child, "tags")
                if "pasta" in tags:
                    total_pastas += 1
                elif "ficha" in tags:
                    total_fichas += 1
                    dados = self.dados_banco.get(child, {})
                    rec = int(re.sub(r"\D", "", str(dados.get("recompensa", 0))) or 0)
                    niv = nivel_seguro(dados.get("nivel", 1))
                    soma_recompensas += rec
                    soma_niveis += niv
                percorrer(child)

        percorrer("")
        media_nivel = (soma_niveis / total_fichas) if total_fichas > 0 else 0

        msg = f"📊 Resumo do Cofre de Ameaças:\n\n"
        msg += f"• Total de Ameaças: {total_fichas}\n"
        msg += f"• Total de Pastas: {total_pastas}\n"
        msg += f"• Nível Médio dos Inimigos: {media_nivel:.1f}\n"
        msg += f"• Soma Total das Recompensas: {soma_recompensas:,} Berries\n".replace(",", ".")

        messagebox.showinfo("Estatísticas da Campanha", msg)

    def iniciar_drag_tree(self, event):
        self._press_xy = (event.x, event.y)
        if self.bloquear_se_buscando():
            return
        item = self.tree.identify_row(event.y)
        if not item:
            if self.tree.selection():
                self.tree.selection_remove(self.tree.selection())
        self.item_arrastado = item

    def ao_clicar_arvore(self, event):
        """Abre a ficha da linha com um clique, sem abrir quando o clique foi arrasto."""
        press = self._press_xy
        self._press_xy = None
        if press is not None and (abs(event.x - press[0]) > 5 or abs(event.y - press[1]) > 5):
            return

        item = self.tree.identify_row(event.y)
        if not item or "ficha" not in self.tree.item(item, "tags"):
            return
        self.abrir_aba_personagem(item, self.tree.item(item, "text").strip())

    def clicar_tracker_vazio(self, event) -> None:
        """Clique em área vazia da lista do Tracker tira a seleção do inimigo."""
        if self._indice_sob_o_mouse(event.y) is None:
            self.lista_iniciativa.selection_clear(0, tk.END)

    def sair_do_tracker(self, event=None) -> None:
        self._hover_tracker_chave = None
        self.tooltip.hide_tip()

    def _postar_menu(self, menu: tk.Menu, x: int, y: int) -> None:
        """Fecha o menu anterior antes de abrir outro, para não acumular janelas."""
        anterior = self._menu_aberto
        if anterior is not None:
            try:
                anterior.unpost()
                anterior.destroy()
            except tk.TclError:
                pass
        self._menu_aberto = menu
        menu.post(x, y)

    def _pv_da_linha(self, item_id: str) -> str:
        """PV formatado para a lista, ou um traço quando não há ficha vinculada."""
        if item_id in self.abas_abertas or item_id in self.dados_banco:
            atual, maximo = self.obter_pv(item_id)
            return f"{atual:>3}/{maximo}"
        return "  —  "

    def registrar_log(self, mensagem: str) -> None:
        """Guarda a mensagem e, se o painel de histórico estiver aberto, mostra."""
        self._log_linhas.append(mensagem)
        if len(self._log_linhas) > 500:
            self._log_linhas = self._log_linhas[-500:]
        if self.caixa_log is not None and self.caixa_log.winfo_exists():
            self.caixa_log.configure(state="normal")
            self.caixa_log.insert(tk.END, f"• {mensagem}\n")
            self.caixa_log.see(tk.END)
            self.caixa_log.configure(state="disabled")

    def alternar_log(self) -> None:
        """Abre/fecha o histórico de rolagens numa janela no canto da tela."""
        if self.janela_log is not None and self.janela_log.winfo_exists():
            if self.janela_log.winfo_viewable():
                self.janela_log.withdraw()
                self.btn_log.configure(text="📜 Log")
                return
            self._posicionar_janela_log()
            self.janela_log.deiconify()
            self.janela_log.lift()
            self.btn_log.configure(text="📜 Fechar")
            return

        self._criar_janela_log()
        self.btn_log.configure(text="📜 Fechar")

    def _posicionar_janela_log(self) -> None:
        """Encosta a janela do log no canto inferior direito do app."""
        largura, altura = 420, 240
        x = self.root.winfo_rootx() + self.root.winfo_width() - largura - 24
        y = self.root.winfo_rooty() + self.root.winfo_height() - altura - 24
        self.janela_log.geometry(f"{largura}x{altura}+{max(0, x)}+{max(0, y)}")

    def _criar_janela_log(self) -> None:
        self.janela_log = ctk.CTkToplevel(self.root)
        self.janela_log.title("Histórico de Rolagens")
        self.janela_log.transient(self.root)
        self.janela_log.attributes("-topmost", True)
        self.janela_log.configure(fg_color=self.tema_atual["bg_card"])
        self._posicionar_janela_log()

        topo = ctk.CTkFrame(self.janela_log, fg_color="transparent")
        topo.pack(fill=tk.X, padx=10, pady=(8, 0))
        ctk.CTkLabel(topo, text="Histórico", font=self.get_font('bold'), text_color=self.tema_atual["text"]).pack(side=tk.LEFT)
        ctk.CTkButton(topo, text="🧼 Limpar", width=70, height=22, fg_color=self.tema_atual["bg_input"], hover_color="#4a4a4a", text_color=self.tema_atual["text"], command=self.limpar_log).pack(side=tk.RIGHT)
        ctk.CTkButton(topo, text="✖", width=28, height=22, fg_color="transparent", hover_color="#5c2b29", text_color="#e06c75", command=self.alternar_log).pack(side=tk.RIGHT, padx=(0, 6))

        self.caixa_log = ctk.CTkTextbox(self.janela_log, fg_color=self.tema_atual["bg_sidebar"], text_color=self.tema_atual["text"], font=self.get_font('main'), border_width=0, corner_radius=6)
        self.caixa_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.caixa_log.configure(state="normal")
        for linha in self._log_linhas:
            self.caixa_log.insert(tk.END, f"• {linha}\n")
        self.caixa_log.configure(state="disabled")

    def limpar_log(self) -> None:
        self._log_linhas.clear()
        if self.caixa_log is not None and self.caixa_log.winfo_exists():
            self.caixa_log.configure(state="normal")
            self.caixa_log.delete("1.0", tk.END)
            self.caixa_log.configure(state="disabled")

    def soltar_drag_tree(self, event):
        if not self.item_arrastado:
            return
        
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
        if item == target:
            return
            
        def eh_descendente(pai, filho_potencial):
            filhos = self.tree.get_children(pai)
            if filho_potencial in filhos:
                return True
            for f in filhos:
                if eh_descendente(f, filho_potencial):
                    return True
            return False

        if eh_descendente(item, target):
            return
            
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
        if nome_base not in existentes:
            return nome_base
        i = 1
        while f"{nome_base} ({i})" in existentes:
            i += 1
        return f"{nome_base} ({i})"

    def add_tracker(self):
        sel = self.tree.selection()
        if sel and "ficha" in self.tree.item(sel[0], "tags"):
            item_id = sel[0]
            
            if item_id in self.abas_abertas:
                nome = self.abas_abertas[item_id].var_nome.get()
            elif item_id in self.dados_banco and "nome" in self.dados_banco[item_id]:
                nome = self.dados_banco[item_id]["nome"]
            else:
                texto_arvore = self.tree.item(item_id, "text").strip()
                nome = re.sub(r" \[Lv\. .*?\]$", "", texto_arvore)

            ini = CTkPopUpInput.pedir_numero("Iniciativa", f"Iniciativa de {nome}:")
            if ini is not None:
                self.tracker_data.append({"ini": ini, "id": item_id, "nome": nome, "status": []})
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
                if child in self.abas_abertas:
                    dados = self.abas_abertas[child].get_dados()
                else:
                    dados = self.dados_banco.get(child, {})
                    
                nome = dados.get("nome", re.sub(r" \[Lv\. .*?\]$", "", self.tree.item(child, "text").strip()))
                agi = dados.get("agi", 0)
                rolagem = random.randint(1, 20) + agi
                
                self.tracker_data.append({"ini": rolagem, "id": child, "nome": nome, "status": []})
                self.registrar_log(f"Iniciativa: {nome} ➔ {rolagem}")
        
        self.atualizar_tracker_view()

    def limpar_tracker(self):
        self.tracker_data.clear()
        self.turno_atual_idx = 0
        self.rodada_atual = 1
        self.lbl_rodada.configure(text="Rodada 1")
        self.atualizar_tracker_view()
        self.registrar_log("Tracker de Combate limpo.")

    def _indice_sob_o_mouse(self, y: int) -> int | None:
        """Índice da linha do Tracker sob o Y informado, ou ``None`` no vazio."""
        idx = self.lista_iniciativa.nearest(y)
        if idx is None or idx < 0:
            return None
        caixa = self.lista_iniciativa.bbox(idx)
        if not caixa:
            return None
        _, topo, _, altura = caixa
        if topo <= y < topo + altura:
            return idx
        return None

    def menu_condicoes_tracker(self, event):
        idx = self._indice_sob_o_mouse(event.y)
        if idx is None:
            # Botão direito no vazio: limpa a seleção e não abre menu.
            self.lista_iniciativa.selection_clear(0, tk.END)
            return
        self.lista_iniciativa.selection_clear(0, tk.END)
        self.lista_iniciativa.selection_set(idx)
        self._menu_condicoes(idx, event.x_root, event.y_root)

    def _menu_condicoes(self, idx: int, x: int, y: int) -> None:
        """Monta o menu de PV/condições para a linha indicada."""
        menu = tk.Menu(self.root, tearoff=0, bg="#262626", fg="#dcddde", bd=0, activebackground=self.tema_atual["accent"])
        menu.add_command(label="⚔️ Aplicar Dano…", command=lambda: self.ajustar_pv_da_linha(idx, -1))
        menu.add_command(label="💚 Curar…", command=lambda: self.ajustar_pv_da_linha(idx, 1))
        menu.add_command(label="💀 Zerar PV", command=lambda: self.aplicar_pv_tracker(idx, -1000000))
        menu.add_separator()

        ativas = {cond["chave"]: cond for cond in self._condicoes_linha(self.tracker_data[idx])}
        submenu = tk.Menu(menu, tearoff=0, bg="#262626", fg="#dcddde", bd=0, activebackground=self.tema_atual["accent"])
        for chave, (icone, nome, _efeito) in CONDICOES.items():
            ativa = ativas.get(chave)
            if ativa:
                prazo = f" ({ativa['turnos']}t)" if ativa["turnos"] else " (∞)"
                marcado = "✓ "
            else:
                prazo, marcado = "", "      "
            submenu.add_command(label=f"{marcado}{icone} {nome}{prazo}", command=lambda c=chave: self.alternar_condicao(idx, c))
        submenu.add_separator()
        submenu.add_command(label="⏱ +1 turno nas condições", command=lambda: self.ajustar_turnos_condicoes(idx, 1))
        submenu.add_command(label="⏱ -1 turno nas condições", command=lambda: self.ajustar_turnos_condicoes(idx, -1))
        submenu.add_command(label="❌ Limpar todas as condições", command=lambda: self.limpar_condicoes(idx))
        menu.add_cascade(label="🩹 Condições", menu=submenu)
        self._postar_menu(menu, x, y)

    def _condicoes_linha(self, linha: dict) -> list[dict]:
        """Condições ativas normalizadas: ``[{'chave': str, 'turnos': int|None}]``.

        Aceita o formato antigo (lista de strings) para não perder cofres
        salvos antes da duração existir.
        """
        status = linha.get("status")
        if not isinstance(status, list):
            return []

        normalizadas: list[dict] = []
        for item in status:
            if isinstance(item, dict):
                chave = item.get("chave")
                turnos = item.get("turnos")
            elif isinstance(item, str):
                chave, turnos = item, None
            else:
                continue
            if chave in CONDICOES:
                normalizadas.append({
                    "chave": chave,
                    "turnos": turnos if isinstance(turnos, int) else None,
                })
        return normalizadas

    def alternar_condicao(self, index: int, chave: str, turnos: int | None = TURNOS_PADRAO) -> None:
        """Liga ou desliga uma condição do livro na linha indicada."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        ativas = self._condicoes_linha(alvo)
        chaves = [cond["chave"] for cond in ativas]

        if chave in chaves:
            ativas = [cond for cond in ativas if cond["chave"] != chave]
            self.registrar_log(f"{icone_condicao(chave)} {nome_condicao(chave)} removida de {alvo['nome']}.")
        else:
            ativas.append({"chave": chave, "turnos": turnos})
            prazo = f" ({turnos} turnos)" if turnos else ""
            self.registrar_log(f"{icone_condicao(chave)} {nome_condicao(chave)} aplicada em {alvo['nome']}{prazo}.")

        alvo["status"] = ativas
        self.atualizar_tracker_view()

    def ajustar_turnos_condicoes(self, index: int, delta: int) -> None:
        """Soma ou tira 1 turno de todas as condições com prazo da linha."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        novas = []
        for cond in self._condicoes_linha(alvo):
            if cond["turnos"] is None:
                novas.append(cond)
                continue
            cond["turnos"] += delta
            if cond["turnos"] > 0:
                novas.append(cond)
            else:
                self.registrar_log(f"⏱ {nome_condicao(cond['chave'])} terminou em {alvo['nome']}.")
        alvo["status"] = novas
        self.atualizar_tracker_view()

    def limpar_condicoes(self, index: int) -> None:
        """Remove todas as condições da linha."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        alvo["status"] = []
        self.atualizar_tracker_view()
        self.registrar_log(f"🧼 Condições removidas de {alvo['nome']}.")

    def _sufixo_status(self, linha: dict) -> str:
        """Ícones de papel e de condições ativas, para o fim da linha."""
        partes: list[str] = []
        papel = linha.get("papel")
        if papel:
            partes.append(str(papel))
        ativas = self._condicoes_linha(linha)
        if ativas:
            visiveis = "".join(icone_condicao(cond["chave"]) for cond in ativas[:2])
            if len(ativas) > 2:
                visiveis += f"+{len(ativas) - 2}"
            partes.append(visiveis)
        return "".join(partes)

    def atualizar_tracker_view(self):
        selecionado = None
        selecao = self.lista_iniciativa.curselection()
        if selecao and selecao[0] < len(self.tracker_data):
            selecionado = self.tracker_data[selecao[0]]

        self.lista_iniciativa.delete(0, tk.END)
        self.tracker_data.sort(key=lambda x: x["ini"], reverse=True)
        
        texto_dif, cor_dif = calcular_dificuldade_encontro(self.tracker_data, self.dados_banco)
        self.lbl_dificuldade.configure(text=f"Encontro: {texto_dif}", text_color=cor_dif)

        for i, t in enumerate(self.tracker_data):
            nome_exib = t['nome']
            if len(nome_exib) > 13:
                nome_exib = nome_exib[:11] + "..."

            item_id = t.get("id", "")
            pv_texto = self._pv_da_linha(item_id)
            marcador = "▶ " if i == self.turno_atual_idx else "  "
            linha = f"{marcador}[{t['ini']:02d}] {nome_exib:<13} {pv_texto:<7}"
            sufixo = self._sufixo_status(t)
            if sufixo:
                linha += " " + sufixo
            self.lista_iniciativa.insert(tk.END, linha)

            if item_id in self.abas_abertas or item_id in self.dados_banco:
                pv_atual, pv_max = self.obter_pv(item_id)
                cor = self._cor_do_pv(pv_atual, pv_max)
            else:
                cor = "#8b8c8f"
            self.lista_iniciativa.itemconfig(i, fg=cor)
            if i == self.turno_atual_idx:
                self.lista_iniciativa.itemconfig(i, bg=self.tema_atual["accent"], fg="white")

        if selecionado is not None:
            for i, t in enumerate(self.tracker_data):
                if t is selecionado:
                    self.lista_iniciativa.selection_set(i)
                    break

        self._atualizar_painel_turno()

    def _recursos_do_turno(self, item_id: str) -> tuple[str, str]:
        """(texto de PV, texto de PE) da ficha em jogo."""
        if item_id in self.abas_abertas:
            aba = self.abas_abertas[item_id]
            return f"{aba.pv_atual.get()}/{aba.pv_max.get()}", f"{aba.pe_atual.get()}/{aba.pe_max.get()}"
        dados = self.dados_banco.get(item_id, {})
        if not dados:
            return "—", "—"
        pv = int(dados.get("pv", 0) or 0)
        pv_max = int(dados.get("pv_max") or pv or 1)
        pe = int(dados.get("pe", 0) or 0)
        pe_max = int(dados.get("pe_max") or pe or 1)
        return f"{pv}/{max(1, pv_max)}", f"{pe}/{max(1, pe_max)}"

    def _defesas_texto(self, item_id: str) -> str:
        """Linha de defesas pronta para o painel do turno."""
        if item_id in self.abas_abertas:
            return self.abas_abertas[item_id].lbl_defesas.cget("text")
        dados = self.dados_banco.get(item_id)
        if not dados:
            return "Def: — | Bloq: — | Esq: — | CD: —"
        res = calcular_atributos_derivados(
            dados.get("nivel", 1), dados.get("fis", 1), dados.get("agi", 1),
            dados.get("int", 1), dados.get("inst", 1), dados.get("luta", 0), dados.get("acro", 0),
            dados.get("mod_passiva", 0), dados.get("mod_bloq", 0), dados.get("mod_esq", 0), dados.get("mod_cd", 0),
        )
        return (f"Def: {res['passiva']} | Bloq: {res['bloqueio']} | "
                f"Esq: {res['esquiva']} | CD: {res['cd']}")

    def _atualizar_painel_turno(self) -> None:
        """Mantém o cartão do turno atual sincronizado com a lista."""
        if not self.tracker_data:
            self.lbl_turno_nome.configure(text="Sem combate", text_color=self.tema_atual["accent"])
            self.lbl_turno_recursos.configure(text="PV —    PE —")
            self.lbl_turno_defesas.configure(text="Def: — | Bloq: — | Esq: — | CD: —")
            self.lbl_turno_condicoes.configure(text="Sem condições.", text_color="#8b8c8f")
            return

        indice = min(max(0, self.turno_atual_idx), len(self.tracker_data) - 1)
        alvo = self.tracker_data[indice]
        item_id = alvo.get("id", "")
        pv_texto, pe_texto = self._recursos_do_turno(item_id)

        self.lbl_turno_nome.configure(text=f"▶ {alvo['nome']}")
        self.lbl_turno_recursos.configure(text=f"PV {pv_texto}    PE {pe_texto}")
        self.lbl_turno_defesas.configure(text=self._defesas_texto(item_id))

        ativas = self._condicoes_linha(alvo)
        if not ativas:
            self.lbl_turno_condicoes.configure(text="Sem condições.", text_color="#8b8c8f")
            return

        pedacos = []
        for cond in ativas:
            prazo = f" ({cond['turnos']}t)" if cond["turnos"] else ""
            pedacos.append(f"{icone_condicao(cond['chave'])} {nome_condicao(cond['chave'])}{prazo}")
        self.lbl_turno_condicoes.configure(text="  ".join(pedacos), text_color="#e5b55e")

    def _cor_do_pv(self, atual: int, maximo: int) -> str:
        """Verde acima de 50%, âmbar até 50%, vermelho até 25% e cinza em 0."""
        if atual <= 0:
            return "#8b8c8f"
        proporcao = atual / maximo if maximo else 0.0
        if proporcao > 0.5:
            return "#6db35f"
        if proporcao > 0.25:
            return "#e5b55e"
        return "#e06c75"

    def obter_pv(self, item_id: str) -> tuple[int, int]:
        """Devolve (PV atual, PV máximo). A aba aberta manda; senão, o banco."""
        aba = self.abas_abertas.get(item_id)
        if aba is not None:
            return aba.pv_atual.get(), max(1, aba.pv_max.get())
        dados = self.dados_banco.get(item_id, {})
        atual = int(dados.get("pv", 0) or 0)
        maximo = int(dados.get("pv_max") or dados.get("pv") or 1)
        return atual, max(1, maximo)

    def aplicar_pv_tracker(self, index: int, delta: int) -> None:
        """Soma (cura) ou subtrai (dano) PV da ficha que está na linha ``index``."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        item_id = alvo.get("id")
        if not item_id:
            return
        if item_id not in self.abas_abertas and item_id not in self.dados_banco:
            self.registrar_log(f"⚠️ {alvo['nome']} não tem ficha vinculada, então não há PV para alterar.")
            return

        atual, maximo = self.obter_pv(item_id)
        novo = max(0, min(maximo, atual + delta))
        if novo == atual:
            return

        aba = self.abas_abertas.get(item_id)
        if aba is not None:
            aba.pv_atual.set(novo)

        dados = self.dados_banco.setdefault(item_id, {})
        dados["pv"] = novo
        dados.setdefault("pv_max", maximo)
        dados.setdefault("nome", alvo.get("nome", ""))

        self.atualizar_tracker_view()
        icone = "⚔️" if delta < 0 else "💚"
        acao = "levou" if delta < 0 else "curou"
        self.registrar_log(f"{icone} {alvo['nome']} {acao} {abs(novo - atual)} PV ({atual} → {novo})")
        if novo == 0:
            self.registrar_log(f"💀 {alvo['nome']} chegou a 0 PV.")

    def ajustar_pv_da_linha(self, index: int, sinal: int) -> None:
        """Pergunta o valor e aplica dano (sinal -1) ou cura (sinal +1) na linha."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        if sinal < 0:
            valor = CTkPopUpInput.pedir_numero("Dano", f"Dano recebido por {alvo['nome']}:")
        else:
            valor = CTkPopUpInput.pedir_numero("Cura", f"Cura em {alvo['nome']}:")
        if valor:
            self.aplicar_pv_tracker(index, -valor if sinal < 0 else valor)

    def ajustar_pv_do_turno(self, sinal: int) -> None:
        """Dano/Cura na linha selecionada ou, sem seleção, em quem está jogando."""
        if not self.tracker_data:
            return
        selecao = self.lista_iniciativa.curselection()
        index = selecao[0] if selecao else self.turno_atual_idx
        self.ajustar_pv_da_linha(index, sinal)

    def sync_nome_ficha(self, item_id, novo_nome, nivel="1"):
        self.tree.item(item_id, text=f" {novo_nome} [Lv. {nivel}]")
        
        if item_id in self.dados_banco:
            self.dados_banco[item_id]["nome"] = novo_nome
            self.dados_banco[item_id]["nivel"] = nivel
            
        if item_id in self.abas_abertas:
            self.notebook.tab(self.abas_abertas[item_id].master, text=f"   {novo_nome}   ")
            
        for i, t in enumerate(self.tracker_data):
            if t['id'] == item_id:
                self.tracker_data[i]['nome'] = novo_nome
        self.atualizar_tracker_view()

    def novo_banco(self):
        if not messagebox.askyesno("Novo Cofre", "Você iniciará uma nova campanha. Alterações não salvas serão perdidas. Continuar?"):
            return
        self.arquivo_atual = None
        self.dados_banco.clear()
        self._fechar_todas_as_abas()
        self.tree.delete(*self.tree.get_children())
        self.limpar_tracker()
        self.inicializar_arvore_padrao()
        self._reiniciar_pesquisa()
        self.atualizar_titulo()

    def _fechar_todas_as_abas(self) -> None:
        """Fecha as abas de ficha sem deixar guias órfãs no notebook."""
        for aba in list(self.abas_abertas.values()):
            self.notebook.forget(aba.master)
            aba.master.destroy()
        self.abas_abertas.clear()

    def _reiniciar_pesquisa(self) -> None:
        """Limpa a busca e o cache da árvore após trocar de cofre."""
        self.arvore_cache = None
        if self.var_pesquisa.get():
            self.var_pesquisa.set("")

    def _gravar_banco(self, caminho: str) -> bool:
        """Grava o cofre no caminho indicado; devolve se deu certo."""
        for item_id, aba in self.abas_abertas.items():
            self.dados_banco[item_id] = aba.get_dados()
        try:
            estrutura = self.mapear_arvore_completa("")
            salvar_banco_sqlite(caminho, estrutura, self.dados_banco)
        except Exception as e:
            messagebox.showerror("Erro de Gravação", str(e))
            return False
        return True

    def salvar_banco(self) -> bool:
        if not self.arquivo_atual:
            return self.salvar_como_banco()
        if self._gravar_banco(self.arquivo_atual):
            self.registrar_log(f"💾 Cofre salvo em {self.arquivo_atual}")
            return True
        return False

    def salvar_como_banco(self) -> bool:
        caminho = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Banco SQLite", "*.db"), ("Todos os Arquivos", "*.*")], title="Salvar Cofre Como...")
        if not caminho:
            return False
        if self._gravar_banco(caminho):
            self.arquivo_atual = caminho
            self.atualizar_titulo()
            self.registrar_log(f"💾 Cofre salvo em {caminho}")
            return True
        return False

    def carregar_banco(self):
        caminho = filedialog.askopenfilename(filetypes=[("Banco SQLite", "*.db"), ("Todos os Arquivos", "*.*")], title="Abrir Cofre")
        if not caminho:
            return
        try:
            estrutura, fichas = carregar_banco_sqlite(caminho)
        except Exception as e:
            messagebox.showerror("Erro de Leitura", str(e))
            return

        if estrutura is None or fichas is None:
            messagebox.showwarning("Aviso", "Este arquivo não contém dados compatíveis.")
            return

        self.arquivo_atual = caminho
        self.atualizar_titulo()
        self.dados_banco = fichas
        self._fechar_todas_as_abas()
        self.tree.delete(*self.tree.get_children())
        self.limpar_tracker()

        def restaurar(pai, nos):
            for n in nos:
                novo_id = self.tree.insert(pai, "end", iid=n["id"], text=n["text"], tags=n["tags"], open=n.get("open", True))
                restaurar(novo_id, n.get("filhos", []))
        restaurar("", estrutura)
        self._reiniciar_pesquisa()
        self.registrar_log(f"📂 Cofre carregado: {caminho}")

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
            # Precisa entrar antes do notebook na ordem do pack, senão o notebook
            # (que expande) consome todo o espaço e o painel fica espremido.
            self.frame_tracker.pack(side=tk.RIGHT, fill=tk.Y, before=self.notebook_frame)
            self.tracker_visivel = True

    def adicionar_pasta(self):
        if self.bloquear_se_buscando():
            return
        sel = self.tree.selection()
        pai = sel[0] if sel and "pasta" in self.tree.item(sel[0], "tags") else (self.tree.parent(sel[0]) if sel else "")
        nome_unico = self.gerar_nome_unico("Nova Categoria", pai)
        self.tree.insert(pai, "end", text=f" {nome_unico}", open=True, tags=("pasta",))

    def adicionar_personagem(self):
        if self.bloquear_se_buscando():
            return
        sel = self.tree.selection()
        pai = sel[0] if sel and "pasta" in self.tree.item(sel[0], "tags") else (self.tree.parent(sel[0]) if sel else "")
        nome_unico = self.gerar_nome_unico("Novo Inimigo", pai)
        novo_id = self.tree.insert(pai, "end", text=f" {nome_unico} [Lv. 1]", tags=("ficha",))
        self.dados_banco[novo_id] = montar_ficha(nome_unico)
        self.abrir_aba_personagem(novo_id, nome_unico)

    def renomear_item(self):
        if self.bloquear_se_buscando():
            return
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        tags = self.tree.item(item_id, "tags")
        
        if "ficha" in tags:
            nome_atual = self.dados_banco.get(item_id, {}).get("nome", "Inimigo")
            tipo = "Ficha"
        else:
            nome_atual = self.tree.item(item_id, "text").strip()
            tipo = "Pasta"
            
        novo_nome = CTkPopUpInput.pedir_texto(f"Renomear {tipo}", f"Digite um novo nome para {tipo}:")
        
        if novo_nome:
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
        if self.bloquear_se_buscando():
            return
        sel = self.tree.selection()
        if not sel:
            return
        item_id = sel[0]
        if not messagebox.askyesno("Confirmar", f"Deseja excluir '{self.tree.item(item_id, 'text').strip()}' e todo seu conteúdo?"):
            return

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

        # Ações secundárias ficam na barra da aba, para o cabeçalho da ficha
        # não estourar quando o painel do Tracker está aberto.
        ctk.CTkButton(barra_topo, text="📝 Exportar .md", command=ficha.exportar_markdown, fg_color=self.tema_atual["bg_input"], hover_color="#4a4a4a", text_color=self.tema_atual["text"], width=100).pack(side=tk.RIGHT, padx=(0, 5))
        ctk.CTkButton(barra_topo, text="📜 Cartaz WANTED", command=ficha.gerar_cartaz, fg_color=self.tema_atual["bg_input"], hover_color="#4a4a4a", text_color=self.tema_atual["text"], width=130).pack(side=tk.RIGHT, padx=(0, 5))
        ctk.CTkButton(barra_topo, text="🖥️ Tela Jogador", command=ficha.abrir_modo_jogador, fg_color=self.tema_atual["bg_input"], hover_color="#4a4a4a", text_color=self.tema_atual["text"], width=110).pack(side=tk.RIGHT, padx=(0, 5))

        self.notebook.add(frame_aba, text=f"   {nome}   ")
        self.notebook.select(frame_aba)
        self.abas_abertas[item_id] = ficha

    def fechar_aba(self, item_id):
        if item_id in self.abas_abertas:
            aba = self.abas_abertas.pop(item_id)
            self.dados_banco[item_id] = aba.get_dados() 
            self.notebook.forget(aba.master)
            aba.master.destroy()

    def fechar_aba_com_click_meio(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            tab_id = self.notebook.tabs()[index]
            for item_id, aba in list(self.abas_abertas.items()):
                if str(aba.master) == str(tab_id):
                    self.fechar_aba(item_id)
                    break
        except tk.TclError:
            pass

    def hover_treeview(self, event):
        item = self.tree.identify_row(event.y)
        if item == self._hover_arvore:
            return
        self._hover_arvore = item
        if item:
            texto = self.tree.item(item, "text").strip()
            self.tooltip.show_tip(texto, event.x_root, event.y_root)
        else:
            self.tooltip.hide_tip()

    def sair_da_arvore(self, event=None) -> None:
        self._hover_arvore = None
        self.tooltip.hide_tip()

    def hover_tracker(self, event):
        idx = self._indice_sob_o_mouse(event.y)
        if idx is None or idx >= len(self.tracker_data):
            self._hover_tracker_chave = None
            self.tooltip.hide_tip()
            return

        info = self.tracker_data[idx]
        pv_texto = self._pv_da_linha(info.get("id", ""))
        ativas = self._condicoes_linha(info)

        chave = (idx, tuple((c["chave"], c["turnos"]) for c in ativas), pv_texto, info["ini"], info["nome"])
        if chave == self._hover_tracker_chave:
            return
        self._hover_tracker_chave = chave

        linhas = [f"{info['nome']} — Iniciativa {info['ini']} — PV {pv_texto.strip()}"]
        if ativas:
            linhas.append("")
            for cond in ativas:
                prazo = f" ({cond['turnos']} turnos)" if cond["turnos"] else ""
                linhas.append(
                    f"{icone_condicao(cond['chave'])} {nome_condicao(cond['chave'])}{prazo}: "
                    f"{resumo_condicao(cond['chave'])}"
                )
        else:
            linhas.append("Sem condições ativas.")

        self.tooltip.show_tip("\n".join(linhas), event.x_root, event.y_root)