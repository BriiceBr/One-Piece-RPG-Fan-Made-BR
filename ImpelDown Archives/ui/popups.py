import tkinter as tk
import customtkinter as ctk

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, text, x_root, y_root):
        self.hide_tip()
        if not text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x_root + 15}+{y_root + 10}")
        label = tk.Label(
            tw, text=text, justify=tk.LEFT,
            background="#2b2b2b", foreground="#ffffff",
            relief=tk.SOLID, borderwidth=1,
            font=("Segoe UI", 10), padx=8, pady=4
        )
        label.pack()

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

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