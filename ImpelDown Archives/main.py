import customtkinter as ctk
from ui.app_main import GerenciadorAmeasApp

# Ajuste de nitidez para ecrãs de alta densidade no Windows
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

def main():
    root = ctk.CTk()
    app = GerenciadorAmeasApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()