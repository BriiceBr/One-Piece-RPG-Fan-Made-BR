import tkinter as tk
import customtkinter as ctk
from typing import Optional

class ToolTip:
    """Legenda flutuante reutilizável.

    A janela e o label são criados uma única vez e apenas reposicionados. Criar
    um Toplevel por evento de ``<Motion>`` custava caro e fazia a legenda
    piscar; agora, quando o texto e a posição não mudam, a chamada retorna na
    hora.
    """

    def __init__(self, widget: tk.Misc) -> None:
        self.widget = widget
        self.tip_window: Optional[tk.Toplevel] = None
        self._label: Optional[tk.Label] = None
        self._texto = ""
        self._posicao = (0, 0)

    def _criar(self) -> None:
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.withdraw()
        tw.wm_overrideredirect(True)
        self._label = tk.Label(
            tw, text="", justify=tk.LEFT,
            background="#2b2b2b", foreground="#ffffff",
            relief=tk.SOLID, borderwidth=1,
            font=("Segoe UI", 10), padx=8, pady=4,
            wraplength=380,
        )
        self._label.pack()

    def _posicionar(self, x_root: int, y_root: int, largura: int, altura: int) -> str:
        largura_tela, altura_tela = self.tip_window.winfo_screenwidth(), self.tip_window.winfo_screenheight()

        x = x_root + 15
        if x + largura > largura_tela - 10:
            x = x_root - largura - 15
        x = min(max(10, x), max(10, largura_tela - largura - 10))

        y = y_root + 10
        if y + altura > altura_tela - 10:
            y = y_root - altura - 10
        y = min(max(10, y), max(10, altura_tela - altura - 10))
        return f"+{x}+{y}"

    def show_tip(self, text: str, x_root: int, y_root: int) -> None:
        if not text:
            self.hide_tip()
            return
        if self.tip_window is None or not self.tip_window.winfo_exists():
            self._criar()

        if text == self._texto and (x_root, y_root) == self._posicao and self.tip_window.winfo_viewable():
            return

        self._texto = text
        self._posicao = (x_root, y_root)

        assert self._label is not None and self.tip_window is not None
        self._label.configure(text=text)
        self.tip_window.update_idletasks()
        geometria = self._posicionar(
            x_root, y_root,
            self.tip_window.winfo_width(), self.tip_window.winfo_height(),
        )
        self.tip_window.wm_geometry(geometria)
        self.tip_window.deiconify()

    def hide_tip(self) -> None:
        self._texto = ""
        if self.tip_window is not None and self.tip_window.winfo_exists():
            self.tip_window.withdraw()

class CTkPopUpInput:
    @staticmethod
    def pedir_texto(titulo, mensagem):
        dialog = ctk.CTkInputDialog(text=mensagem, title=titulo)
        res = dialog.get_input()
        return res.strip() if res else None

    @staticmethod
    def pedir_numero(titulo, mensagem):
        dialog = ctk.CTkInputDialog(text=mensagem, title=titulo)
        res = dialog.get_input()
        if res and res.isdigit():
            return int(res)
        return None
