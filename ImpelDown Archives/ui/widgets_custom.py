import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from core.paleta import (
    TEXTO_SUAVE as COR_TEXTO_SUAVE,
    PERIGO as COR_PERIGO,
    HOVER as COR_HOVER,
    ALCA as COR_ALCA,
    BOTAO_PERIGO as COR_BOTAO_PERIGO,
)

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
        if self._drag_data["index"] is None:
            return
        try:
            target_index = self.index(f"@{event.x},{event.y}")
            if target_index != self._drag_data["index"]:
                self.insert(target_index, self.tabs()[self._drag_data["index"]])
                self._drag_data["index"] = target_index
        except tk.TclError:
            pass


class ListaBando(ctk.CTkFrame):
    """Lista de lacaios do bando: ✖ por linha e duplo clique abre a ficha.

    Substitui o Listbox: além de aceitar drop de fichas da árvore, cada linha
    tem seu próprio botão de remover.
    """

    def __init__(self, master, app_master, tema, ao_abrir=None):
        super().__init__(master, fg_color=tema["bg_input"], corner_radius=6)
        self.app_master = app_master
        self.tema = tema
        self._ao_abrir = ao_abrir
        self._itens: list[str] = []
        self._linhas: list[ctk.CTkFrame] = []
        self.bando_tag = True

        self._canvas = tk.Canvas(self, bg=tema["bg_input"], highlightthickness=0)
        self._scroll = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._interior = tk.Frame(self._canvas, bg=tema["bg_input"])
        self._janela = self._canvas.create_window((0, 0), window=self._interior, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scroll.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._interior.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._janela, width=e.width))

        self._vazio = ctk.CTkLabel(
            self._interior, text="Arraste fichas para cá",
            text_color=COR_TEXTO_SUAVE, font=app_master.get_font('small'),
        )
        self._vazio.pack(pady=12)

    def insert(self, index, texto) -> None:
        nome = str(texto).strip()
        if not nome:
            return
        self._itens.append(nome)
        if self._vazio.winfo_manager():
            self._vazio.pack_forget()

        linha = ctk.CTkFrame(self._interior, fg_color=self.tema["bg_card"], corner_radius=4)
        linha.pack(fill=tk.X, padx=4, pady=2)
        linha.bando_tag = True
        self._linhas.append(linha)

        rotulo = ctk.CTkLabel(
            linha, text=nome, anchor="w",
            text_color=self.tema["text"], font=self.app_master.get_font('main'),
        )
        rotulo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4), pady=3)
        rotulo.bind("<Double-Button-1>", lambda e, n=nome: self._abrir(n))

        ctk.CTkButton(
            linha, text="✖", width=24, height=22,
            fg_color="transparent", hover_color=COR_BOTAO_PERIGO,
            text_color=COR_PERIGO,
            command=lambda n=nome, l=linha: self._remover(n, l),
        ).pack(side=tk.RIGHT, padx=(0, 4))

    def _abrir(self, nome: str) -> None:
        if self._ao_abrir is not None:
            self._ao_abrir(nome)

    def _remover(self, nome: str, linha: ctk.CTkFrame) -> None:
        if nome in self._itens:
            self._itens.remove(nome)
        if linha in self._linhas:
            self._linhas.remove(linha)
        linha.destroy()
        if not self._itens:
            self._vazio.pack(pady=12)

    def delete(self, first, last=None) -> None:
        for linha in self._linhas:
            linha.destroy()
        self._linhas.clear()
        self._itens.clear()
        self._vazio.pack(pady=12)

    def get(self, first, last=None):
        return tuple(self._itens)


class HabilidadeBloco(ctk.CTkFrame):
    def __init__(self, parent, dados_hab, canvas_mestre, painel_direito, app_master, ao_remover=None):
        self.app_master = app_master
        self._ao_remover = ao_remover
        self.tema = app_master.tema_atual
        super().__init__(parent, fg_color=self.tema["bg_card"], corner_radius=8)
        self.pack(fill=tk.X, pady=8, padx=10)
        self.canvas_mestre = canvas_mestre
        self.painel_direito = painel_direito

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill=tk.X, padx=10, pady=(8, 4))

        self.var_titulo = tk.StringVar(value=dados_hab.get("titulo", ""))
        self.entrada_titulo = ctk.CTkEntry(
            self.header, 
            textvariable=self.var_titulo, 
            fg_color="transparent", 
            text_color=self.tema["text"], 
            border_width=0, 
            font=self.app_master.get_font('bold')
        )

        # Botões primeiro (à direita) para nunca serem empurrados para fora.
        self.btn_deletar = ctk.CTkButton(
            self.header, 
            text="✖", 
            width=30, 
            height=26, 
            fg_color="transparent", 
            hover_color=COR_BOTAO_PERIGO, 
            text_color=COR_PERIGO, 
            command=self._remover
        )
        self.btn_deletar.pack(side=tk.RIGHT)

        self.btn_toggle = ctk.CTkButton(
            self.header, 
            text="▼▲", 
            width=30, 
            height=26, 
            fg_color="transparent", 
            hover_color=self.tema["bg_input"], 
            text_color=COR_TEXTO_SUAVE, 
            command=self.toggle
        )
        self.btn_toggle.pack(side=tk.RIGHT, padx=(0, 4))

        self.entrada_titulo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.pack(fill=tk.X, padx=10, pady=(0, 4))

        def add_meta_field(master, label, width, var_val):
            ctk.CTkLabel(master, text=label, text_color=COR_TEXTO_SUAVE, font=self.app_master.get_font('small')).pack(side=tk.LEFT, padx=(5,2))
            var = tk.StringVar(value=var_val)
            entry = ctk.CTkEntry(
                master, 
                textvariable=var, 
                width=width, 
                height=24, 
                fg_color=self.tema["bg_input"], 
                border_width=0, 
                font=self.app_master.get_font('small'), 
                text_color=self.tema["text"]
            )
            entry.pack(side=tk.LEFT)
            return var

        self.var_custo = add_meta_field(meta_frame, "Custo:", 40, dados_hab.get("custo", ""))
        self.var_limite = add_meta_field(meta_frame, "Lim:", 40, dados_hab.get("limite", ""))
        self.var_exec = add_meta_field(meta_frame, "Exec:", 60, dados_hab.get("execucao", ""))
        self.var_alcance = add_meta_field(meta_frame, "Alcance:", 80, dados_hab.get("alcance", ""))

        self.container_texto = ctk.CTkFrame(self, fg_color="transparent")
        self.container_texto.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Editor de PE: custo base + extra, com validação do limite do patamar.
        linha_pe = ctk.CTkFrame(self.container_texto, fg_color="transparent")
        linha_pe.pack(fill=tk.X, pady=(0, 4))
        ctk.CTkLabel(linha_pe, text="Potencialização (+PE):", font=self.app_master.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(side=tk.LEFT)
        self.var_extra = tk.StringVar(value=str(dados_hab.get("extra", "")))
        ctk.CTkEntry(
            linha_pe, textvariable=self.var_extra, width=46, height=22,
            fg_color=self.tema["bg_input"], border_width=0,
            font=self.app_master.get_font('small'), text_color=self.tema["text"],
        ).pack(side=tk.LEFT, padx=(4, 8))
        self.lbl_resumo = ctk.CTkLabel(
            linha_pe, text="", font=self.app_master.get_font('small'),
            text_color=COR_TEXTO_SUAVE, anchor="w",
        )
        self.lbl_resumo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for var_pe in (self.var_custo, self.var_limite, self.var_extra):
            var_pe.trace_add("write", self._atualizar_resumo)
        self._atualizar_resumo()

        self.texto = ctk.CTkTextbox(
            self.container_texto, 
            height=90, 
            fg_color=self.tema["bg_input"], 
            text_color=self.tema["text"], 
            font=self.app_master.get_font('main'), 
            wrap=tk.WORD, 
            border_width=0, 
            corner_radius=6
        )
        self.texto.insert(tk.END, dados_hab.get("conteudo", ""))
        self.texto.pack(fill=tk.X)

        self.grip = tk.Frame(self.container_texto, height=5, bg=COR_ALCA, cursor="sb_v_double_arrow")
        self.grip.pack(fill=tk.X, pady=(2,0))
        self.grip.bind("<ButtonPress-1>", self._iniciar_redimensionar)
        self.grip.bind("<B1-Motion>", self.redimensionar)
        self._aberto = True
        self._altura_inicial: float | None = None
        self._y_inicial = 0

    @staticmethod
    def _numero(texto: str) -> int | None:
        """Primeiro número inteiro do texto (None se não houver)."""
        digitos = "".join(caractere for caractere in str(texto) if caractere.isdigit())
        return int(digitos) if digitos else None

    def _atualizar_resumo(self, *args) -> None:
        """Mostra custo base + extra e acusa extra acima do limite do patamar."""
        base = self._numero(self.var_custo.get()) or 0
        limite = self._numero(self.var_limite.get())
        extra = self._numero(self.var_extra.get()) or 0

        if limite is None:
            self.lbl_resumo.configure(text=f"PE: {base} base + {extra} = {base + extra}")
            return

        if extra > limite:
            self.lbl_resumo.configure(
                text=f"⚠️ +{extra} passa do limite (+{limite})",
                text_color=COR_PERIGO,
            )
            return

        self.lbl_resumo.configure(
            text=f"+{extra} de +{limite} → total {base + extra} PE",
            text_color=COR_TEXTO_SUAVE,
        )

    def _iniciar_redimensionar(self, event) -> None:
        """Guarda a altura e a posição do ponteiro no começo do arrasto."""
        self._altura_inicial = self.texto.winfo_height()
        self._y_inicial = event.y_root

    def redimensionar(self, event) -> None:
        """Ajusta a altura pelo deslocamento total, não pelo delta de cada evento."""
        if self._altura_inicial is None:
            self._iniciar_redimensionar(event)
        nova_altura = self._altura_inicial + (event.y_root - self._y_inicial)
        self.texto.configure(height=max(60, int(nova_altura)))

    def _remover(self) -> None:
        """Avisa a ficha (para sair da lista) e destrói o bloco."""
        if self._ao_remover is not None:
            self._ao_remover(self)
        self.destroy()

    def toggle(self) -> None:
        if self._aberto:
            self.container_texto.pack_forget()
            self._aberto = False
        else:
            self.container_texto.pack(fill=tk.X, padx=10, pady=(0, 10))
            self._aberto = True
        
    def get_dados(self):
        return {
            "titulo": self.var_titulo.get().strip(),
            "custo": self.var_custo.get().strip(),
            "limite": self.var_limite.get().strip(),
            "execucao": self.var_exec.get().strip(),
            "alcance": self.var_alcance.get().strip(),
            "extra": self.var_extra.get().strip(),
            "conteudo": self.texto.get("1.0", tk.END).strip()
        }