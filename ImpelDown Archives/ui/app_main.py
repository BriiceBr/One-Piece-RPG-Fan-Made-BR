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
from core.combate import calcular_dificuldade_encontro
from utils.arquivos import exportar_ficha_json, importar_ficha_json, salvar_banco_sqlite, carregar_banco_sqlite

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

        self.montar_menus()
        self.montar_layout_principal()
        self.inicializar_arvore_padrao()
        self.configurar_atalhos()

    def configurar_atalhos(self):
        self.root.bind("<Control-s>", lambda e: self.salvar_banco())
        self.root.bind("<Control-n>", lambda e: self.adicionar_personagem())
        self.root.bind("<Control-f>", lambda e: self.focar_pesquisa())

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
        menu_arq.add_command(label="Salvar (Ctrl+S)", command=self.salvar_banco)
        menu_arq.add_command(label="Salvar Como...", command=self.salvar_como_banco)
        menu_arq.add_separator()
        menu_arq.add_command(label="Sair", command=self.root.quit)
        self.menu_bar.add_cascade(label="Cofre", menu=menu_arq)

        menu_ferramentas = tk.Menu(self.menu_bar, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
        menu_ferramentas.add_command(label="📊 Estatísticas da Campanha", command=self.exibir_estatisticas_campanha)
        menu_ferramentas.add_command(label="👥 Gerar Lacaios em Massa", command=self.gerar_lacaios_massa)
        menu_ferramentas.add_command(label="📥 Importar Ficha (.json)", command=self.importar_ficha_individual)
        self.menu_bar.add_cascade(label="Ferramentas", menu=menu_ferramentas)

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
                "open": self.tree.item(child, "open"),
                "filhos": self.mapear_arvore_completa(child)
            })
        return res

    def pesquisar_arvore(self, *args):
        termo = self.var_pesquisa.get().lower().strip()
        
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
        self.tree.bind("<Button-3>", self.abrir_menu_contexto)
        self.tree.bind("<Delete>", lambda e: self.deletar_item())
        self.tree.bind("<Motion>", self.hover_treeview)
        self.tree.bind("<Leave>", lambda e: self.tooltip.hide_tip())
        self.tree.bind("<Double-1>", self.ao_dar_duplo_clique)
        self.item_arrastado = None

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
        
        ctk.CTkLabel(self.frame_tracker, text="COMBAT TRACKER", font=("Segoe UI", 12, "bold"), text_color="#8b8c8f", anchor="w").pack(fill=tk.X, padx=20, pady=(15, 2))
        
        self.lbl_dificuldade = ctk.CTkLabel(self.frame_tracker, text="Encontro: Sem Inimigos", font=("Segoe UI", 10, "bold"), text_color="#8b8c8f", anchor="w")
        self.lbl_dificuldade.pack(fill=tk.X, padx=20, pady=(0, 5))

        self.lbl_rodada = ctk.CTkLabel(self.frame_tracker, text="Rodada 1", font=("Segoe UI", 11, "bold"), text_color=self.tema_atual["accent"], anchor="w")
        self.lbl_rodada.pack(fill=tk.X, padx=20, pady=(0, 5))

        self.lista_iniciativa = tk.Listbox(self.frame_tracker, bg=self.tema_atual["bg_sidebar"], fg=self.tema_atual["text"], font=self.get_font('main'), selectbackground=self.tema_atual["accent"], bd=0, highlightthickness=0)
        self.lista_iniciativa.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.lista_iniciativa.bind("<Button-3>", self.menu_condicoes_tracker)
        self.lista_iniciativa.bind("<Motion>", self.hover_tracker)
        self.lista_iniciativa.bind("<Leave>", lambda e: self.tooltip.hide_tip())
        
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

        ctk.CTkLabel(self.frame_tracker, text="HISTÓRICO DE ROLAGENS", font=("Segoe UI", 11, "bold"), text_color="#8b8c8f", anchor="w").pack(fill=tk.X, padx=20, pady=(10, 0))
        self.caixa_log = ctk.CTkTextbox(self.frame_tracker, height=145, fg_color="#262626", text_color="#dcddde", font=self.get_font('main'), border_width=0, corner_radius=6)
        self.caixa_log.pack(fill=tk.X, padx=15, pady=(5, 15))
        self.caixa_log.configure(state="disabled")

    def proximo_turno(self):
        if not self.tracker_data:
            return
        self.turno_atual_idx += 1
        if self.turno_atual_idx >= len(self.tracker_data):
            self.turno_atual_idx = 0
            self.rodada_atual += 1
            self.registrar_log(f"--- Rodada {self.rodada_atual} iniciada ---")
        
        self.lbl_rodada.configure(text=f"Rodada {self.rodada_atual}")
        self.atualizar_tracker_view()
        
        atual = self.tracker_data[self.turno_atual_idx]
        self.registrar_log(f"Vez de: {atual['nome']}")

    def inicializar_arvore_padrao(self):
        cat_m = self.tree.insert("", "end", text=" Monstros", open=True, tags=("pasta",))
        cat_v = self.tree.insert("", "end", text=" Vilões", open=True, tags=("pasta",))
        
        id_arlong = self.tree.insert(cat_v, "end", text=" Arlong [Lv. 3]", tags=("ficha",))
        self.dados_banco[id_arlong] = {"nome": "Arlong", "pv": 100, "pe": 20, "agi": 3, "nivel": "3"}
        
        id_rei = self.tree.insert(cat_m, "end", text=" Rei dos Mares [Lv. 5]", tags=("ficha",))
        self.dados_banco[id_rei] = {"nome": "Rei dos Mares", "pv": 100, "pe": 20, "agi": 1, "nivel": "5"}

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
            menu.post(event.x_root, event.y_root)

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
            self.dados_banco[novo_id] = {"nome": nome_lacaio, "pv": 30, "pe": 10, "nivel": "1"}

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
                    niv = int(dados.get("nivel", 1))
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
        if self.bloquear_se_buscando():
            return
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
                if child in self.abas_abertas:
                    dados = self.abas_abertas[child].get_dados()
                else:
                    dados = self.dados_banco.get(child, {})
                    
                nome = dados.get("nome", re.sub(r" \[Lv\. .*?\]$", "", self.tree.item(child, "text").strip()))
                agi = dados.get("agi", 0)
                rolagem = random.randint(1, 20) + agi
                
                self.tracker_data.append({"ini": rolagem, "id": child, "nome": nome, "status": ""})
                self.registrar_log(f"Iniciativa: {nome} ➔ {rolagem}")
        
        self.atualizar_tracker_view()

    def limpar_tracker(self):
        self.tracker_data.clear()
        self.turno_atual_idx = 0
        self.rodada_atual = 1
        self.lbl_rodada.configure(text="Rodada 1")
        self.atualizar_tracker_view()
        self.registrar_log("Tracker de Combate limpo.")

    def menu_condicoes_tracker(self, event):
        idx = self.lista_iniciativa.nearest(event.y)
        if idx >= 0:
            self.lista_iniciativa.selection_clear(0, tk.END)
            self.lista_iniciativa.selection_set(idx)
            menu = tk.Menu(self.root, tearoff=0, bg="#262626", fg="#dcddde", bd=0)
            menu.add_command(label="⚔️ Aplicar Dano…", command=lambda: self.ajustar_pv_da_linha(idx, -1))
            menu.add_command(label="💚 Curar…", command=lambda: self.ajustar_pv_da_linha(idx, 1))
            menu.add_command(label="💀 Zerar PV", command=lambda: self.aplicar_pv_tracker(idx, -1000000))
            menu.add_separator()
            icones = ["☠️ Envenenado", "💤 Fadigado", "⚡ Haki Exausto", "🛡️ Protegido", "❌ Limpar Status"]
            for icone in icones:
                menu.add_command(label=icone, command=lambda i=icone, index=idx: self.aplicar_status_tracker(index, i))
            menu.post(event.x_root, event.y_root)

    def aplicar_status_tracker(self, index, icone_full):
        icone = icone_full.split(" ")[0] if "Limpar" not in icone_full else ""
        self.tracker_data[index]["status"] = icone
        self.atualizar_tracker_view()

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
            
            pv_atual, pv_max = self.obter_pv(t.get("id", ""))
            marcador = "▶ " if i == self.turno_atual_idx else "  "
            linha = f"{marcador}[{t['ini']:02d}] {nome_exib:<13} {pv_atual:>3}/{pv_max:<3} {t['status']}"
            self.lista_iniciativa.insert(tk.END, linha)
            self.lista_iniciativa.itemconfig(i, fg=self._cor_do_pv(pv_atual, pv_max))
            if i == self.turno_atual_idx:
                self.lista_iniciativa.itemconfig(i, bg=self.tema_atual["accent"], fg="white")

        if selecionado is not None:
            for i, t in enumerate(self.tracker_data):
                if t is selecionado:
                    self.lista_iniciativa.selection_set(i)
                    break

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
        if messagebox.askyesno("Novo Cofre", "Você iniciará uma nova campanha. Alterações não salvas serão perdidas. Continuar?"):
            self.arquivo_atual = None
            self.dados_banco.clear()
            for aba in self.abas_abertas.values():
                aba.master.destroy()
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
            estrutura = self.mapear_arvore_completa("")
            salvar_banco_sqlite(self.arquivo_atual, estrutura, self.dados_banco)
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
        if not caminho:
            return
        try:
            estrutura, fichas = carregar_banco_sqlite(caminho)
            if estrutura is not None:
                self.arquivo_atual = caminho
                self.atualizar_titulo()
                self.dados_banco = fichas
                for aba in self.abas_abertas.values():
                    aba.master.destroy()
                self.abas_abertas.clear()
                self.tree.delete(*self.tree.get_children())
                self.limpar_tracker()
                
                def restaurar(pai, nos):
                    for n in nos:
                        novo_id = self.tree.insert(pai, "end", iid=n["id"], text=n["text"], tags=n["tags"], open=n.get("open", True))
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
        self.dados_banco[novo_id] = {"nome": nome_unico, "pv": 100, "pe": 20, "nivel": "1"}
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
        if item:
            texto = self.tree.item(item, "text").strip()
            self.tooltip.show_tip(texto, event.x_root, event.y_root)
        else:
            self.tooltip.hide_tip()

    def hover_tracker(self, event):
        idx = self.lista_iniciativa.nearest(event.y)
        if idx >= 0 and idx < len(self.tracker_data):
            info = self.tracker_data[idx]
            texto_completo = f"{info['nome']} (Iniciativa: {info['ini']}) {info['status']}"
            self.tooltip.show_tip(texto_completo, event.x_root, event.y_root)
        else:
            self.tooltip.hide_tip()