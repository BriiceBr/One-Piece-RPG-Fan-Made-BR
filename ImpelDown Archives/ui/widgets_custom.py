import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

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
        self.entrada_titulo = ctk.CTkEntry(
            self.header, 
            textvariable=self.var_titulo, 
            fg_color="transparent", 
            text_color=self.tema["text"], 
            border_width=0, 
            font=self.app_master.get_font('bold')
        )
        self.entrada_titulo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        meta_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        meta_frame.pack(side=tk.LEFT, padx=10)

        def add_meta_field(master, label, width, var_val):
            ctk.CTkLabel(master, text=label, text_color="#8b8c8f", font=self.app_master.get_font('small')).pack(side=tk.LEFT, padx=(5,2))
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

        self.btn_toggle = ctk.CTkButton(
            self.header, 
            text="▼▲", 
            width=30, 
            height=24, 
            fg_color="transparent", 
            hover_color=self.tema["bg_input"], 
            text_color="#8b8c8f", 
            command=self.toggle
        )
        self.btn_toggle.pack(side=tk.LEFT, padx=5)
        
        self.btn_deletar = ctk.CTkButton(
            self.header, 
            text="✖", 
            width=30, 
            height=24, 
            fg_color="transparent", 
            hover_color="#5c2b29", 
            text_color="#e06c75", 
            command=self.destroy
        )
        self.btn_deletar.pack(side=tk.LEFT)

        self.container_texto = ctk.CTkFrame(self, fg_color="transparent")
        self.container_texto.pack(fill=tk.X, padx=10, pady=(0, 10))

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

        self.grip = tk.Frame(self.container_texto, height=5, bg="#3a3a3a", cursor="sb_v_double_arrow")
        self.grip.pack(fill=tk.X, pady=(2,0))
        self.grip.bind("<B1-Motion>", self.redimensionar)

    def redimensionar(self, event):
        nova_altura = self.texto.winfo_height() + event.y
        if nova_altura > 40:
            self.texto.configure(height=nova_altura)

    def toggle(self):
        if self.container_texto.winfo_ismapped():
            self.container_texto.pack_forget()
        else:
            self.container_texto.pack(fill=tk.X, padx=10, pady=(0, 10))
        
    def get_dados(self):
        return {
            "titulo": self.var_titulo.get().strip(),
            "custo": self.var_custo.get().strip(),
            "limite": self.var_limite.get().strip(),
            "execucao": self.var_exec.get().strip(),
            "alcance": self.var_alcance.get().strip(),
            "conteudo": self.texto.get("1.0", tk.END).strip()
        }