import os
import json
import random
import re
import tkinter as tk
from collections import Counter
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from config import TEMAS, FONTES_DISPONIVEIS, NOME_SISTEMA
from ui.popups import ToolTip, CTkPopUpInput
from ui.widgets_custom import DraggableNotebook
from ui.ficha_frame import FichaPersonagemFrame
from core.combate import nivel_seguro
from core.condicoes import CONDICOES, icone as icone_condicao, nome as nome_condicao, resumo as resumo_condicao
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
from core.desafio import analisar as analisar_desafio
from utils.arquivos import exportar_ficha_json, importar_ficha_json, salvar_banco_sqlite, carregar_banco_sqlite
from utils.loot import normalizar_faccao
from utils.encontros import encontrar_para_alvo, perfil_lacaio, sugerir_encontros
from utils.importacao import ler_lote

#: Duração padrão (em turnos) ao aplicar uma condição no Tracker.
TURNOS_PADRAO = 3
#: Intervalo do salvamento automático (minutos).
AUTOSAVE_MINUTOS = 3
#: Tema aplicado automaticamente ao abrir ficha de cada facção.
TEMAS_FACCAO: dict[str, str] = {
    "marinha": "Marinha (Azul)",
    "pirata": "Pirata (Amarelo)",
    "fera": "Yonkou (Vermelho)",
    "governo": "Obsidian (Padrão)",
}

#: Pastas cujas fichas são jogadores (não contam no desafio do encontro).
PASTAS_JOGADOR: set[str] = {
    "player", "players", "jogador", "jogadores", "party", "grupo", "aliados",
}


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
    mod_pv: int = 0,
    mod_pe: int = 0,
) -> dict:
    """Ficha completa, com Atributos e recursos já calculados.

    Evita o problema de fichas criadas "pela metade" (sem Físico/Intelecto), que
    depois abriam com PV limitado a um máximo calculado com Atributos zerados.
    """
    res = calcular_atributos_derivados(
        nivel, fis, agi, intel, inst, luta, acro, bonus_pv=mod_pv, bonus_pe=mod_pe
    )
    return {
        "nome": nome, "nivel": str(nivel), "recompensa": recompensa,
        "fis": fis, "agi": agi, "int": intel, "inst": inst,
        "luta": luta, "acro": acro,
        "pv": res["pv"], "pv_max": res["pv"],
        "pe": res["pe"], "pe_max": res["pe"],
        "mod_pv": mod_pv, "mod_pe": mod_pe,
        "historia": "", "loot": "", "bando": [],
    }


#: Perfis-base por arquétipo: cada lacaio sorteia um e varia ±1 nos Atributos.
ARQUETIPOS_LACAIOS: dict[str, list[dict[str, int]]] = {
    "Esquadrão Balanceado": [
        {"fis": 2, "agi": 2, "intel": 1, "inst": 1, "luta": 1, "acro": 0},
        {"fis": 1, "agi": 3, "intel": 1, "inst": 2, "luta": 0, "acro": 2},
        {"fis": 3, "agi": 1, "intel": 1, "inst": 1, "luta": 2, "acro": 0},
    ],
    "Bando de Atiradores": [
        {"fis": 1, "agi": 3, "intel": 1, "inst": 2, "luta": 0, "acro": 2},
        {"fis": 1, "agi": 4, "intel": 1, "inst": 1, "luta": 0, "acro": 1},
    ],
    "Vanguarda Pesada": [
        {"fis": 4, "agi": 1, "intel": 1, "inst": 1, "luta": 2, "acro": 0},
        {"fis": 3, "agi": 1, "intel": 1, "inst": 2, "luta": 3, "acro": 0},
    ],
}

#: Nomes temáticos conforme a facção (pasta) onde os lacaios nascem.
NOMES_LACAIOS: dict[str, list[str]] = {
    "marinha": ["Recruta da Marinha", "Fuzileiro", "Cabo de Patrulha"],
    "pirata": ["Pirata de Abordagem", "Grumete", "Saqueador"],
    "fera": ["Fera Menor", "Besta de Caça", "Filhote Marinho"],
    "governo": ["Agente do Governo", "Guarda Nobre", "Escolta"],
    "outros": ["Lacaio", "Capanga", "Comparsa"],
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
        self.caixa_log = None
        self._log_aberto = False
        self._undo: list[dict] = []

        self.montar_menus()
        self.montar_layout_principal()
        self.inicializar_arvore_padrao()
        self.configurar_atalhos()
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)
        self._agendar_autosave()

    def ao_fechar(self) -> None:
        """Pergunta se quer salvar antes de fechar (evita perder o progresso)."""
        if getattr(self, "_autosave_id", None) is not None:
            try:
                self.root.after_cancel(self._autosave_id)
            except tk.TclError:
                pass
            self._autosave_id = None
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
        self.root.bind("<Control-k>", self.abrir_busca_global)
        self.root.bind("<Control-z>", self.desfazer)
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
        self.style.configure("TNotebook.Tab", background=self.tema_atual["bg_sidebar"], foreground=COR_TEXTO_SUAVE, padding=[20, 8], font=self.get_font('main'), borderwidth=0)
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
        if self.caixa_log is not None and self.caixa_log.winfo_exists():
            self.frame_log.configure(fg_color=self.tema_atual["bg_card"])
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
        self._reaplicar_visual(anterior)
        self.atualizar_tracker_view()

    def _mapa_visual(self, anterior: dict) -> dict[str, str]:
        """Cores do tema antigo -> cores equivalentes do tema novo."""
        return {anterior[chave]: valor for chave, valor in self.tema_atual.items() if anterior.get(chave) != valor}

    def _reaplicar_visual(self, anterior: dict) -> None:
        """Repinta todos os widgets criados com as cores do tema antigo.

        Evita fechar e reabrir as abas: percorre a árvore de widgets e troca
        somente valores que batem com a paleta anterior.
        """
        mapa = self._mapa_visual(anterior)

        def repintar(widget: tk.Misc) -> None:
            for filho in widget.winfo_children():
                self._repintar_widget(filho, mapa)
                # CTkTabview esconde o botão segmentado fora de winfo_children.
                interno = getattr(filho, "_segmented_button", None)
                if interno is not None:
                    self._repintar_widget(interno, mapa)
                repintar(filho)

        repintar(self.root)

    def _repintar_widget(self, widget: tk.Misc, mapa: dict[str, str]) -> None:
        """Aplica o mapa de cores em todas as opções de cor que o widget tiver."""
        for opcao in (
            "fg_color", "text_color", "hover_color", "border_color",
            "button_color", "bg_color", "progress_color",
            "selected_color", "selected_hover_color",
            "unselected_color", "unselected_hover_color",
            "text_color_disabled", "dropdown_hover_color",
            "bg", "fg", "background", "foreground", "selectbackground",
            "highlightbackground", "activebackground",
        ):
            try:
                valor = widget.cget(opcao)
            except (tk.TclError, ValueError, TypeError):
                continue
            if isinstance(valor, str) and valor in mapa:
                try:
                    widget.configure(**{opcao: mapa[valor]})
                except (tk.TclError, ValueError, TypeError):
                    pass

    def mudar_fonte(self, escolha: str) -> None:
        """Troca a família de fonte de todos os widgets, sem recriar abas."""
        self.current_font = escolha
        self.aplicar_tema_style()
        self.lista_iniciativa.configure(font=self.get_font('main'))
        self._reaplicar_fonte(escolha)

    def _reaplicar_fonte(self, familia: str) -> None:
        def repintar(widget: tk.Misc) -> None:
            for filho in widget.winfo_children():
                self._trocar_fonte_widget(filho, familia)
                interno = getattr(filho, "_segmented_button", None)
                if interno is not None:
                    self._trocar_fonte_widget(interno, familia)
                repintar(filho)

        repintar(self.root)

    def _trocar_fonte_widget(self, widget: tk.Misc, familia: str) -> None:
        """Mantém tamanho/estilo e troca só a família da fonte."""
        try:
            fonte = widget.cget("font")
        except (tk.TclError, ValueError, TypeError):
            return

        try:
            if isinstance(fonte, tuple) and len(fonte) >= 2:
                widget.configure(font=(familia, *fonte[1:]))
            elif isinstance(fonte, str) and fonte.strip():
                partes = fonte.split()
                widget.configure(font=" ".join([familia] + partes[1:]) if len(partes) > 1 else familia)
            elif hasattr(fonte, "configure"):
                fonte.configure(family=familia)
        except (tk.TclError, ValueError, TypeError):
            pass

    def _registrar_undo(self, acao: dict) -> None:
        """Empilha uma ação reversível (máximo de 50)."""
        self._undo.append(acao)
        if len(self._undo) > 50:
            self._undo.pop(0)

    def desfazer(self, event=None):
        """Ctrl+Z: desfaz o último dano/cura ou mudança de condições."""
        if not self._undo:
            self.registrar_log("↩️ Nada para desfazer.")
            return "break"

        acao = self._undo.pop()
        if acao["tipo"] == "pv":
            item_id = acao["id"]
            valor = acao["pv"]
            aba = self.abas_abertas.get(item_id)
            if aba is not None:
                aba.pv_atual.set(valor)
            self.dados_banco.setdefault(item_id, {})["pv"] = valor
            for indice, linha in enumerate(self.tracker_data):
                if linha.get("id") == item_id:
                    self._atualizar_linha(indice)
            self.registrar_log(f"↩️ PV de {acao['nome']} restaurado para {valor}.")

        elif acao["tipo"] == "cond":
            indice = acao["indice"]
            if 0 <= indice < len(self.tracker_data):
                self.tracker_data[indice]["status"] = [dict(c) for c in acao["status"]]
                self._atualizar_linha(indice)
                self.registrar_log(f"↩️ Condições de {acao['nome']} restauradas.")
        return "break"

    def _fichas_para_busca(self) -> list[tuple[str, str, str]]:
        resultado: list[tuple[str, str, str]] = []

        def percorrer(node: str, faccao: str) -> None:
            for child in self.tree.get_children(node):
                tags = self.tree.item(child, "tags")
                texto = re.sub(r" \[Lv\. .*?\]$", "", self.tree.item(child, "text").strip())
                if "pasta" in tags:
                    percorrer(child, faccao or texto)
                elif "ficha" in tags:
                    resultado.append((child, texto, faccao or "Sem pasta"))
                    percorrer(child, faccao)

        percorrer("", "")
        return resultado

    def abrir_ficha_por_nome(self, nome: str) -> None:
        """Abre a ficha cujo nome bate (exato ou início), usada pelo bando."""
        alvo = str(nome or "").strip().lower()
        if not alvo:
            return
        fichas = self._fichas_para_busca()
        escolhida = next((f for f in fichas if f[1].lower() == alvo), None)
        if escolhida is None:
            escolhida = next((f for f in fichas if f[1].lower().startswith(alvo)), None)
        if escolhida is None:
            messagebox.showinfo("Bando", f"Ficha '{nome}' não encontrada na árvore.", parent=self.root)
            return
        item_id, nome_ficha, _faccao = escolhida
        self.tree.selection_set(item_id)
        self.tree.see(item_id)
        self.abrir_aba_personagem(item_id, nome_ficha)

    def abrir_busca_global(self, event=None):
        """Ctrl+K: procura qualquer ficha pelo nome e abre direto."""
        janela = getattr(self, "_janela_busca", None)
        if janela is not None and janela.winfo_exists():
            janela.lift()
            return "break"

        top = ctk.CTkToplevel(self.root)
        self._janela_busca = top
        top.title("Busca global")
        top.geometry("480x460")
        top.transient(self.root)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema_atual["bg_main"])

        ctk.CTkLabel(top, text="🔎 Buscar ficha (Ctrl+K)", font=self.get_font('title'), text_color=self.tema_atual["accent"]).pack(anchor="w", padx=14, pady=(14, 4))
        var = tk.StringVar()
        entrada = ctk.CTkEntry(top, textvariable=var, placeholder_text="Nome da ficha...", fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0)
        entrada.pack(fill=tk.X, padx=14, pady=(0, 8))

        lista = tk.Listbox(top, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], selectbackground=self.tema_atual["accent"], bd=0, highlightthickness=0, exportselection=False)
        lista.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        fichas = self._fichas_para_busca()
        resultados: list[str] = []

        def filtrar(*_args) -> None:
            termo = var.get().strip().lower()
            resultados.clear()
            lista.delete(0, tk.END)
            for item_id, nome, faccao in fichas:
                if termo in nome.lower():
                    resultados.append(item_id)
                    lista.insert(tk.END, f"{nome}   ·   {faccao}")

        def abrir(_evento=None) -> None:
            selecao = lista.curselection()
            if not selecao:
                return
            item_id = resultados[selecao[0]]
            self.tree.selection_set(item_id)
            self.tree.see(item_id)
            self.abrir_aba_personagem(item_id, self.tree.item(item_id, "text").strip())
            top.destroy()

        var.trace_add("write", filtrar)
        lista.bind("<Double-Button-1>", abrir)
        lista.bind("<Return>", abrir)
        entrada.bind("<Return>", lambda e: (lista.selection_set(0), abrir()) if lista.size() else None)
        top.bind("<Escape>", lambda e: top.destroy())
        filtrar()
        entrada.focus_set()
        return "break"

    def _inserir_ficha(self, pai: str, nome: str, nivel: int, perfil: dict[str, int],
                       mod_pv: int = 0, mod_pe: int = 0) -> str:
        """Cria ficha na árvore já com os recursos calculados."""
        nome_unico = self.gerar_nome_unico(nome, pai)
        novo_id = self.tree.insert(pai, "end", text=f" {nome_unico} [Lv. {nivel}]", tags=("ficha",))
        self.dados_banco[novo_id] = montar_ficha(
            nome_unico, nivel, **perfil, mod_pv=mod_pv, mod_pe=mod_pe
        )
        return novo_id

    def abrir_calculadora_dano(self) -> None:
        """Calculadora de desafio por dano médio da party."""
        top = ctk.CTkToplevel(self.root)
        top.title("Calculadora de Dano")
        top.geometry("420x520")
        top.transient(self.root)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema_atual["bg_main"])

        ctk.CTkLabel(top, text="🧮 Calculadora de Dano", font=self.get_font('title'), text_color=self.tema_atual["accent"]).pack(pady=(14, 6))

        var_jogadores = tk.StringVar(value=str(self._inteiro_positivo(self.var_jogadores, 4)))
        var_nivel = tk.StringVar(value=str(self._inteiro_positivo(self.var_nivel_grupo, 1)))
        var_inimigos = tk.StringVar(value="4")
        var_hp = tk.StringVar(value="40")
        campos = (
            ("Jogadores", var_jogadores),
            ("Nível médio da party", var_nivel),
            ("Quantidade de inimigos", var_inimigos),
            ("HP médio dos inimigos", var_hp),
        )
        for rotulo, var in campos:
            ctk.CTkLabel(top, text=rotulo, font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)
            ctk.CTkEntry(top, textvariable=var, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(fill=tk.X, padx=20, pady=(0, 4))

        resultado = ctk.CTkTextbox(top, height=190, fg_color=self.tema_atual["bg_card"], text_color=self.tema_atual["text"], border_width=0, font=self.get_font('small'))
        resultado.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        def calcular() -> None:
            def inteiro(var: tk.StringVar, padrao: int) -> int:
                texto = str(var.get()).strip()
                return int(texto) if texto.isdigit() and int(texto) > 0 else padrao

            jogadores = inteiro(var_jogadores, 4)
            nivel = inteiro(var_nivel, 1)
            inimigos = inteiro(var_inimigos, 1)
            hp_medio = inteiro(var_hp, 1)
            dados = analisar_desafio(jogadores, nivel, inimigos * hp_medio)
            linhas = [
                f"Patamar: {dados['patamar']} ({dados['dano_jogador']}/jogador)",
                f"Dano da party: {dados['dano_party']}/rodada",
                f"HP total: {dados['hp_total']}",
                f"Rodadas: {dados['rodadas']:.1f} → {dados['rodadas_inteiras']}",
                f"Desafio: {dados['rotulo']}",
                "",
            ]
            linhas += [f"• {s}" for s in dados["sugestoes"]]
            resultado.configure(state="normal")
            resultado.delete("1.0", tk.END)
            resultado.insert("1.0", "\n".join(linhas))
            resultado.configure(state="disabled")

        ctk.CTkButton(top, text="Calcular", command=calcular, fg_color=self.tema_atual["accent"], text_color="white").pack(fill=tk.X, padx=20, pady=(0, 14))

    def abrir_gerador_encontros(self) -> None:
        """Sugere composições de encontro e permite criá-las no cofre."""
        top = ctk.CTkToplevel(self.root)
        top.title("Gerador de Encontros")
        top.geometry("430x480")
        top.transient(self.root)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema_atual["bg_main"])

        ctk.CTkLabel(top, text="🎯 Gerador de Encontros", font=self.get_font('title'), text_color=self.tema_atual["accent"]).pack(pady=(14, 6))

        var_jogadores = tk.StringVar(value=str(self._inteiro_positivo(self.var_jogadores, 4)))
        var_nivel = tk.StringVar(value=str(self._inteiro_positivo(self.var_nivel_grupo, 1)))
        for rotulo, var in (("Jogadores", var_jogadores), ("Nível médio do grupo", var_nivel)):
            ctk.CTkLabel(top, text=rotulo, font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)
            ctk.CTkEntry(top, textvariable=var, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(fill=tk.X, padx=20, pady=(0, 4))

        var_alvo = tk.StringVar(value="Desafiador")
        ctk.CTkLabel(top, text="Dificuldade desejada", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)
        ctk.CTkOptionMenu(top, variable=var_alvo, values=["Fácil", "Desafiador", "Mortal"], fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], button_color=self.tema_atual["accent"]).pack(fill=tk.X, padx=20)

        resultado = ctk.CTkTextbox(top, height=150, fg_color=self.tema_atual["bg_card"], text_color=self.tema_atual["text"], border_width=0, font=self.get_font('small'))
        resultado.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        sugestao_atual: dict[str, object] = {}

        def calcular() -> None:
            jogadores = int(var_jogadores.get()) if var_jogadores.get().isdigit() else 4
            nivel = int(var_nivel.get()) if var_nivel.get().isdigit() else 1
            sugestoes = sugerir_encontros(jogadores, nivel)
            resultado.configure(state="normal")
            resultado.delete("1.0", tk.END)

            hp_tracker = 0
            for linha in self.tracker_data:
                if not self._item_e_jogador(linha.get("id", "")):
                    hp_tracker += self.obter_pv(linha.get("id", ""))[0]
            if hp_tracker > 0:
                atual = analisar_desafio(jogadores, nivel, hp_tracker)
                resultado.insert(tk.END, f"Tracker atual: {hp_tracker} HP → {atual['resumo']}\n\n")

            for sugestao in sugestoes:
                resultado.insert(tk.END, f"• {sugestao.resumo}\n")
            escolhida = encontrar_para_alvo(jogadores, nivel, var_alvo.get())
            sugestao_atual["valor"] = escolhida
            resultado.configure(state="disabled")

        def criar() -> None:
            escolhida = sugestao_atual.get("valor")
            if escolhida is None:
                messagebox.showinfo("Encontro", "Clique em Calcular primeiro.", parent=top)
                return
            selecao = self.tree.selection()
            pai = selecao[0] if selecao and "pasta" in self.tree.item(selecao[0], "tags") else ""
            faccao = normalizar_faccao(self.tree.item(pai, "text") if pai else "")
            self._criar_encontro(pai, escolhida, faccao)
            top.destroy()

        botoes = ctk.CTkFrame(top, fg_color="transparent")
        botoes.pack(fill=tk.X, padx=20, pady=(0, 14))
        ctk.CTkButton(botoes, text="Calcular", command=calcular, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"]).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ctk.CTkButton(botoes, text="Criar no cofre", command=criar, fg_color=self.tema_atual["accent"], text_color="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

    def _criar_encontro(self, pai: str, sugestao, faccao: str) -> None:
        """Cria uma pasta de encontro com subpastas de chefes e lacaios."""
        nome_pasta = self.gerar_nome_unico(f"Encontro Gerado — {sugestao.classificacao}", pai)
        pasta = self.tree.insert(pai, "end", text=f" {nome_pasta}", open=True, tags=("pasta",))
        pasta_chefes = self.tree.insert(pasta, "end", text=" Chefes", open=True, tags=("pasta",))
        pasta_lacaios = self.tree.insert(pasta, "end", text=" Lacaios", open=True, tags=("pasta",))

        perfil_chefe = self._perfil_lacaio(sugestao.chefe_nivel, "Vanguarda Pesada", 1)
        self._inserir_ficha(
            pasta_chefes, f"Chefe (Nv {sugestao.chefe_nivel})", sugestao.chefe_nivel, perfil_chefe, mod_pv=10
        )
        base = NOMES_LACAIOS.get(faccao, ["Lacaio"])[0]
        for indice in range(1, sugestao.lacaios + 1):
            perfil = self._perfil_lacaio(sugestao.lacaio_nivel, "Esquadrão Balanceado", indice)
            self._inserir_ficha(pasta_lacaios, f"{base} {indice:02d}", sugestao.lacaio_nivel, perfil)

        self.tree.item(pasta, open=True)
        self.registrar_log(f"🎯 {nome_pasta}: {sugestao.resumo}")

    def _aplicar_tema_faccao_item(self, item_id: str) -> None:
        """Aplica o tema da facção só quando o Mestre pedir (menu de contexto)."""
        faccao = normalizar_faccao(self.faccao_do_item(item_id))
        tema = TEMAS_FACCAO.get(faccao)
        if not tema:
            messagebox.showinfo("Tema da facção", "Esta pasta não tem uma facção com tema definido.", parent=self.root)
            return
        self.mudar_tema(tema)
        self.registrar_log(f"🎨 Tema da facção aplicado manualmente: {tema}")

    def abrir_gerador_inimigo(self) -> None:
        """Cria um inimigo por Nível e classe (Balanceado/Atiradores/Vanguarda)."""
        top = ctk.CTkToplevel(self.root)
        top.title("Gerar Inimigo")
        top.geometry("380x360")
        top.transient(self.root)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema_atual["bg_main"])

        ctk.CTkLabel(top, text="🐲 Gerar Inimigo", font=self.get_font('title'), text_color=self.tema_atual["accent"]).pack(pady=(14, 6))

        ctk.CTkLabel(top, text="Nome", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)
        var_nome = tk.StringVar(value="Inimigo")
        ctk.CTkEntry(top, textvariable=var_nome, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(fill=tk.X, padx=20)

        ctk.CTkLabel(top, text="Nível", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20, pady=(6, 0))
        var_nivel = tk.StringVar(value="5")
        ctk.CTkEntry(top, textvariable=var_nivel, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(fill=tk.X, padx=20)

        ctk.CTkLabel(top, text="Classe", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20, pady=(6, 0))
        classes = {
            "Balanceado": "Esquadrão Balanceado",
            "Atiradores": "Bando de Atiradores",
            "Vanguarda": "Vanguarda Pesada",
        }
        var_classe = tk.StringVar(value="Balanceado")
        ctk.CTkSegmentedButton(
            top, variable=var_classe, values=list(classes),
            fg_color=self.tema_atual["bg_input"], selected_color=self.tema_atual["accent"],
            selected_hover_color=self.tema_atual.get("accent_hover", self.tema_atual["accent"]),
            unselected_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"],
        ).pack(fill=tk.X, padx=20)

        def criar() -> None:
            nivel = int(var_nivel.get()) if var_nivel.get().isdigit() else 1
            selecao = self.tree.selection()
            pai = selecao[0] if selecao and "pasta" in self.tree.item(selecao[0], "tags") else ""
            faccao = normalizar_faccao(self.tree.item(pai, "text") if pai else "")
            arquetipo = classes[var_classe.get()]
            self._gerar_inimigo(pai, var_nome.get().strip() or "Inimigo", max(1, nivel), arquetipo, faccao)
            top.destroy()

        ctk.CTkButton(top, text="Criar", command=criar, fg_color=self.tema_atual["accent"], text_color="white").pack(fill=tk.X, padx=20, pady=16)

    def _gerar_inimigo(self, pai: str, nome: str, nivel: int, arquetipo: str, faccao: str) -> None:
        """Cria o inimigo usando o mesmo perfil de arquétipo dos lacaios."""
        perfil = self._perfil_lacaio(nivel, arquetipo, 1)
        self._inserir_ficha(pai, nome, nivel, perfil)
        self.registrar_log(f"🐲 Inimigo '{nome}' (Nv {nivel}, {arquetipo}) criado em {faccao}.")

    def importar_lote(self) -> None:
        """Importa várias fichas de um JSON/CSV, validando cada uma."""
        caminho = filedialog.askopenfilename(
            filetypes=[("Fichas", "*.json *.csv"), ("JSON", "*.json"), ("CSV", "*.csv")],
            title="Importar fichas em lote",
        )
        if not caminho:
            return
        try:
            fichas, erros = ler_lote(caminho)
        except Exception as erro:
            messagebox.showerror("Importação", f"Falha ao ler o arquivo: {erro}")
            return

        selecao = self.tree.selection()
        pai = selecao[0] if selecao and "pasta" in self.tree.item(selecao[0], "tags") else ""
        for dados in fichas:
            nivel = int(dados.get("nivel", 1))
            base = montar_ficha(
                dados["nome"], nivel, dados.get("fis", 1), dados.get("agi", 1),
                dados.get("int", 1), dados.get("inst", 1),
                dados.get("luta", 0), dados.get("acro", 0),
                str(dados.get("recompensa", "0")),
            )
            base.update(dados)
            base["nivel"] = str(nivel)
            nome_unico = self.gerar_nome_unico(base["nome"], pai)
            base["nome"] = nome_unico
            novo_id = self.tree.insert(pai, "end", text=f" {nome_unico} [Lv. {nivel}]", tags=("ficha",))
            self.dados_banco[novo_id] = base

        resumo = f"{len(fichas)} ficha(s) importada(s)."
        if erros:
            resumo += "\n\nIgnoradas:\n" + "\n".join(erros[:8])
        messagebox.showinfo("Importação em lote", resumo)
        self.registrar_log(f"📥 Importação em lote: {len(fichas)} ficha(s), {len(erros)} erro(s).")

    def montar_menus(self):
        self.menu_bar = tk.Menu(self.root, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], bd=0)
        self.root.config(menu=self.menu_bar)

        self.menu_arq = tk.Menu(self.menu_bar, tearoff=0, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], bd=0)
        self.menu_arq.add_command(label="Novo Cofre", command=self.novo_banco)
        self.menu_arq.add_command(label="Abrir Cofre...", command=self.carregar_banco)
        self.menu_arq.add_separator()
        self.menu_arq.add_command(label="Salvar (Ctrl+S)", command=self.salvar_banco)
        self.menu_arq.add_command(label="Salvar Como...", command=self.salvar_como_banco)
        self.menu_arq.add_separator()
        self.menu_arq.add_command(label="Sair", command=self.ao_fechar)
        self.menu_bar.add_cascade(label="Cofre", menu=self.menu_arq)

        self.menu_ferramentas = tk.Menu(self.menu_bar, tearoff=0, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], bd=0)
        self.menu_ferramentas.add_command(label="📊 Estatísticas da Campanha", command=self.exibir_estatisticas_campanha)
        self.menu_ferramentas.add_command(label="👥 Gerar Lacaios em Massa", command=self.gerar_lacaios_massa)
        self.menu_ferramentas.add_command(label="🐲 Gerar Inimigo", command=self.abrir_gerador_inimigo)
        self.menu_ferramentas.add_command(label="🎯 Gerador de Encontros", command=self.abrir_gerador_encontros)
        self.menu_ferramentas.add_command(label="🧮 Calculadora de Dano", command=self.abrir_calculadora_dano)
        self.menu_ferramentas.add_separator()
        self.menu_ferramentas.add_command(label="📥 Importar Ficha (.json)", command=self.importar_ficha_individual)
        self.menu_ferramentas.add_command(label="📦 Importar em Lote (JSON/CSV)", command=self.importar_lote)
        self.menu_bar.add_cascade(label="Ferramentas", menu=self.menu_ferramentas)

        self.menu_ajuda = tk.Menu(self.menu_bar, tearoff=0, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], bd=0)
        self.menu_ajuda.add_command(label="⌨️ Atalhos", command=self.mostrar_atalhos)
        self.menu_ajuda.add_command(label="ℹ️ Sobre", command=self.mostrar_sobre)
        self.menu_bar.add_cascade(label="Ajuda", menu=self.menu_ajuda)

        self.barra_ferramentas = ctk.CTkFrame(self.root, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.barra_ferramentas.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        self._botoes_barra: list[ctk.CTkButton] = []
        self._menus_barra: list[ctk.CTkOptionMenu] = []

        self.btn_toggle_tree = ctk.CTkButton(self.barra_ferramentas, text="≡ Pastas", command=self.toggle_tree, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"], width=100)
        self.btn_toggle_tree.pack(side=tk.LEFT)
        self._botoes_barra.append(self.btn_toggle_tree)
        self.tree_visivel = True

        self.var_tema = ctk.StringVar(value="Obsidian (Padrão)")
        self.menu_temas = ctk.CTkOptionMenu(self.barra_ferramentas, variable=self.var_tema, values=list(TEMAS.keys()), command=self.mudar_tema, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], button_color=self.tema_atual["accent"], width=160)
        self.menu_temas.pack(side=tk.LEFT, padx=(20, 10))
        self._menus_barra.append(self.menu_temas)

        self.var_fonte = ctk.StringVar(value="Segoe UI")
        self.menu_fontes = ctk.CTkOptionMenu(self.barra_ferramentas, variable=self.var_fonte, values=FONTES_DISPONIVEIS, command=self.mudar_fonte, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], button_color=self.tema_atual["accent"], width=130)
        self.menu_fontes.pack(side=tk.LEFT)
        self._menus_barra.append(self.menu_fontes)

        self.btn_toggle_tracker = ctk.CTkButton(self.barra_ferramentas, text="≡ Tracker", command=self.toggle_tracker, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"], width=100)
        self.btn_toggle_tracker.pack(side=tk.RIGHT)
        self._botoes_barra.append(self.btn_toggle_tracker)

        # Status discreto do último salvamento (manual ou automático).
        self.lbl_status = ctk.CTkLabel(
            self.barra_ferramentas, text="",
            font=self.get_font('small'), text_color=COR_TEXTO_SUAVE,
        )
        self.lbl_status.pack(side=tk.RIGHT, padx=(0, 12))
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
        ctk.CTkLabel(topo_tree, text="PASTAS", font=("Segoe UI", 12, "bold"), text_color=COR_TEXTO_SUAVE).pack(side=tk.LEFT)
        
        self.var_pesquisa = tk.StringVar()
        self.var_pesquisa.trace_add("write", self.pesquisar_arvore)
        self.entry_pesquisa = ctk.CTkEntry(topo_tree, textvariable=self.var_pesquisa, placeholder_text="🔍 Buscar (Ctrl+F)...", height=24, fg_color=self.tema_atual["bg_input"], border_width=0)
        self.entry_pesquisa.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10,0))
        
        self.tree = ttk.Treeview(self.frame_tree, selectmode="extended", show="tree")
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
        
        ctk.CTkButton(f_botoes, text="+ Pasta", command=self.adicionar_pasta, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"]).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="+ Ficha", command=self.adicionar_personagem, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"]).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="✎ Renomear", command=self.renomear_item, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"]).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(f_botoes, text="✖ Deletar", command=self.deletar_item, fg_color="transparent", hover_color=COR_BOTAO_PERIGO, text_color=COR_PERIGO).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        f_botoes.columnconfigure(0, weight=1)
        f_botoes.columnconfigure(1, weight=1)

        self.notebook_frame = ctk.CTkFrame(self.container_principal, fg_color=self.tema_atual["bg_main"], corner_radius=0)
        self.notebook_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.notebook = DraggableNotebook(self.notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Button-2>", self.fechar_aba_com_click_meio)
        self.abas_abertas = {}
        #: Fichas fechadas ficam em cache para reabrir instantaneamente.
        self._abas_cache: dict[str, tuple[ctk.CTkFrame, FichaPersonagemFrame]] = {}
        #: Bando compartilhado por todas as fichas (persistido no cofre).
        self.bando_global: list[str] = []

        self.frame_tracker = ctk.CTkFrame(self.container_principal, width=280, fg_color=self.tema_atual["bg_sidebar"], corner_radius=0)
        self.frame_tracker.pack_propagate(False)
        
        topo_trk = ctk.CTkFrame(self.frame_tracker, fg_color="transparent")
        topo_trk.pack(fill=tk.X, padx=20, pady=(15, 2))
        ctk.CTkLabel(topo_trk, text="COMBAT TRACKER", font=("Segoe UI", 12, "bold"), text_color=COR_TEXTO_SUAVE, anchor="w").pack(side=tk.LEFT)
        self.btn_log = ctk.CTkButton(topo_trk, text="📜 Log", width=64, height=22, fg_color="transparent", hover_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], command=self.alternar_log)
        self.btn_log.pack(side=tk.RIGHT)
        
        self.lbl_dificuldade = ctk.CTkLabel(self.frame_tracker, text="Encontro: Sem Inimigos", font=("Segoe UI", 10, "bold"), text_color=COR_TEXTO_SUAVE, anchor="w", wraplength=250, justify="left")
        self.lbl_dificuldade.pack(fill=tk.X, padx=20, pady=(0, 4))

        # Contexto do grupo: sem isso a dificuldade era um número solto.
        f_grupo = ctk.CTkFrame(self.frame_tracker, fg_color="transparent")
        f_grupo.pack(fill=tk.X, padx=15, pady=(0, 4))
        ctk.CTkLabel(f_grupo, text="Jogadores", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(side=tk.LEFT)
        self.var_jogadores = tk.StringVar(value="4")
        self.var_nivel_grupo = tk.StringVar(value="1")
        ctk.CTkEntry(f_grupo, textvariable=self.var_jogadores, width=34, height=22, justify="center", fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(side=tk.LEFT, padx=(4, 8))
        ctk.CTkLabel(f_grupo, text="Nível médio", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(side=tk.LEFT)
        ctk.CTkEntry(f_grupo, textvariable=self.var_nivel_grupo, width=34, height=22, justify="center", fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(side=tk.LEFT, padx=(4, 0))
        for var_grupo in (self.var_jogadores, self.var_nivel_grupo):
            var_grupo.trace_add("write", lambda *_: self.atualizar_dificuldade())

        self.lbl_rodada = ctk.CTkLabel(self.frame_tracker, text="Rodada 1", font=("Segoe UI", 11, "bold"), text_color=self.tema_atual["accent"], anchor="w")
        self.lbl_rodada.pack(fill=tk.X, padx=20, pady=(0, 5))

        # Painel do turno atual: tudo o que o Mestre precisa, sem abrir ficha.
        self.frame_turno = ctk.CTkFrame(self.frame_tracker, fg_color=self.tema_atual["bg_card"], corner_radius=8)
        self.frame_turno.pack(fill=tk.X, padx=15, pady=(0, 4))
        self.lbl_turno_nome = ctk.CTkLabel(self.frame_turno, text="Sem combate", font=self.get_font('bold'), text_color=self.tema_atual["accent"], anchor="w")
        self.lbl_turno_nome.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.lbl_turno_recursos = ctk.CTkLabel(self.frame_turno, text="PV —    PE —", font=self.get_font('small'), text_color=self.tema_atual["text"], anchor="w")
        self.lbl_turno_recursos.pack(fill=tk.X, padx=10)
        self.lbl_turno_defesas = ctk.CTkLabel(self.frame_turno, text="Def: — | Bloq: — | Esq: — | CD: —", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE, anchor="w")
        self.lbl_turno_defesas.pack(fill=tk.X, padx=10)
        self.lbl_turno_condicoes = ctk.CTkLabel(self.frame_turno, text="Sem condições.", font=self.get_font('small'), text_color=COR_AVISO, anchor="w", justify="left", wraplength=230)
        self.lbl_turno_condicoes.pack(fill=tk.X, padx=10, pady=(0, 4))

        self.lista_iniciativa = tk.Listbox(self.frame_tracker, bg=self.tema_atual["bg_sidebar"], fg=self.tema_atual["text"], font=self.get_font('main'), selectbackground=self.tema_atual["accent"], bd=0, highlightthickness=0, exportselection=False, activestyle="none")
        self.lista_iniciativa.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.lista_iniciativa.bind("<Button-3>", self.menu_condicoes_tracker)
        self.lista_iniciativa.bind("<Button-1>", self.clicar_tracker_vazio)
        self.lista_iniciativa.bind("<Delete>", self.remover_do_tracker)
        self.lista_iniciativa.bind("<Motion>", self.hover_tracker)
        self.lista_iniciativa.bind("<Leave>", self.sair_do_tracker)
        
        f_trk_btn = ctk.CTkFrame(self.frame_tracker, fg_color="transparent")
        f_trk_btn.pack(fill=tk.X, padx=15, pady=5)
        ctk.CTkButton(f_trk_btn, text="▶ Próximo Turno", command=self.proximo_turno, fg_color=self.tema_atual["accent"], text_color="white").pack(fill=tk.X, pady=2)

        f_pv_btn = ctk.CTkFrame(f_trk_btn, fg_color="transparent")
        f_pv_btn.pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_pv_btn, text="⚔️ Dano", command=lambda: self.ajustar_pv_do_turno(-1), fg_color=COR_BOTAO_PERIGO, hover_color=COR_BOTAO_PERIGO_HOVER, text_color=COR_BOTAO_PERIGO_TEXTO).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        ctk.CTkButton(f_pv_btn, text="💚 Cura", command=lambda: self.ajustar_pv_do_turno(1), fg_color=COR_BOTAO_SUCESSO, hover_color=COR_BOTAO_SUCESSO_HOVER, text_color=COR_BOTAO_SUCESSO_TEXTO).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        ctk.CTkButton(f_trk_btn, text="Adicionar Ficha", command=self.add_tracker, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"]).pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_trk_btn, text="🎲 Rolar Pasta", command=self.rolar_iniciativa_pasta, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"]).pack(fill=tk.X, pady=2)
        ctk.CTkButton(f_trk_btn, text="Limpar Tracker", command=self.limpar_tracker, fg_color="transparent", hover_color=COR_BOTAO_PERIGO, text_color=COR_PERIGO).pack(fill=tk.X, pady=2)

        # Histórico embutido (começa escondido; o botão 📜 Log mostra).
        self.frame_log = ctk.CTkFrame(self.frame_tracker, fg_color=self.tema_atual["bg_card"], corner_radius=8, height=215)
        topo_log = ctk.CTkFrame(self.frame_log, fg_color="transparent")
        topo_log.pack(fill=tk.X, padx=8, pady=(6, 0))
        ctk.CTkLabel(topo_log, text="Histórico", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(side=tk.LEFT)
        ctk.CTkButton(topo_log, text="🧼", width=24, height=20, fg_color="transparent", hover_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], command=self.limpar_log).pack(side=tk.RIGHT)
        self.caixa_log = ctk.CTkTextbox(self.frame_log, height=165, fg_color=self.tema_atual["bg_sidebar"], text_color=self.tema_atual["text"], font=self.get_font('small'), border_width=0, corner_radius=6)
        self.caixa_log.pack(fill=tk.X, padx=8, pady=(4, 8))
        self.caixa_log.configure(state="disabled")

    def faccao_do_item(self, item_id: str | None) -> str:
        """Nome da pasta de topo onde a ficha está (usado pelo loot contextual)."""
        if not item_id or not self.tree.exists(item_id):
            return ""
        pai = self.tree.parent(item_id)
        while pai:
            avo = self.tree.parent(pai)
            if not avo:
                return self.tree.item(pai, "text").strip()
            pai = avo
        return ""

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
            menu = tk.Menu(self.root, tearoff=0, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], bd=0)
            menu.add_command(label="✎ Renomear", command=self.renomear_item)
            if "ficha" in tags:
                menu.add_command(label="📋 Duplicar Ficha", command=lambda: self.duplicar_ficha(item))
                menu.add_command(label="📤 Exportar Ficha (.json)", command=lambda: self.exportar_ficha_individual(item))
            elif "pasta" in tags:
                menu.add_command(label="📁 Nova Pasta", command=self.adicionar_pasta)
                menu.add_command(label="📄 Nova Ficha", command=self.adicionar_personagem)
            menu.add_command(label="🎨 Tema da facção", command=lambda: self._aplicar_tema_faccao_item(item))
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

    def gerar_lacaios_massa(self) -> None:
        """Abre o assistente de lacaios (nome, quantidade e arquétipo)."""
        sel = self.tree.selection()
        pai = sel[0] if sel and "pasta" in self.tree.item(sel[0], "tags") else ""
        pasta = self.tree.item(pai, "text").strip() if pai else ""
        faccao = normalizar_faccao(pasta)

        top = ctk.CTkToplevel(self.root)
        top.title("Gerar Lacaios")
        top.geometry("380x470")
        top.transient(self.root)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema_atual["bg_main"])

        ctk.CTkLabel(top, text="👥 Gerar Lacaios", font=self.get_font('title'), text_color=self.tema_atual["accent"]).pack(pady=(14, 6))

        ctk.CTkLabel(top, text="Nome base", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)
        var_nome = tk.StringVar(value=NOMES_LACAIOS.get(faccao, NOMES_LACAIOS["outros"])[0])
        ctk.CTkEntry(top, textvariable=var_nome, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(fill=tk.X, padx=20)

        ctk.CTkLabel(top, text="Quantidade", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20, pady=(8, 0))
        var_qtd = tk.StringVar(value="4")
        ctk.CTkEntry(top, textvariable=var_qtd, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(fill=tk.X, padx=20)

        ctk.CTkLabel(top, text="Arquétipo", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20, pady=(8, 0))
        arquetipos_curtos = {
            "Balanceado": ("Esquadrão Balanceado", "Mistura de soldado, atirador e brute. Bom para qualquer situação."),
            "Atiradores": ("Bando de Atiradores", "Agilidade/Instinto e Acrobacia altos; fraco no corpo a corpo."),
            "Vanguarda": ("Vanguarda Pesada", "Físico e Luta altos; mais lento e sem Acrobacia."),
        }
        var_arquetipo = tk.StringVar(value="Balanceado")
        lbl_descricao = ctk.CTkLabel(
            top, text=arquetipos_curtos["Balanceado"][1], wraplength=320, justify="left",
            font=self.get_font('small'), text_color=COR_TEXTO_SUAVE,
        )
        ctk.CTkSegmentedButton(
            top, variable=var_arquetipo, values=list(arquetipos_curtos),
            command=lambda escolha: lbl_descricao.configure(text=arquetipos_curtos[escolha][1]),
            fg_color=self.tema_atual["bg_input"], selected_color=self.tema_atual["accent"],
            selected_hover_color=self.tema_atual.get("accent_hover", self.tema_atual["accent"]),
            unselected_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"],
        ).pack(fill=tk.X, padx=20)
        lbl_descricao.pack(fill=tk.X, padx=20, pady=(2, 0))

        ctk.CTkLabel(top, text="Nível dos lacaios", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20, pady=(8, 0))
        var_nivel = tk.StringVar(value="1")
        ctk.CTkEntry(top, textvariable=var_nivel, fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"], border_width=0).pack(fill=tk.X, padx=20)

        def criar() -> None:
            base = var_nome.get().strip() or "Lacaio"
            texto_qtd = str(var_qtd.get()).strip()
            if not texto_qtd.isdigit() or int(texto_qtd) <= 0:
                messagebox.showwarning("Aviso", "Informe uma quantidade válida.", parent=top)
                return
            texto_nivel = str(var_nivel.get()).strip()
            nivel = int(texto_nivel) if texto_nivel.isdigit() and int(texto_nivel) > 0 else 1
            arquetipo = arquetipos_curtos[var_arquetipo.get()][0]
            self._criar_lacaios(pai, base, int(texto_qtd), arquetipo, faccao, nivel)
            top.destroy()

        ctk.CTkButton(top, text="Gerar", command=criar, fg_color=self.tema_atual["accent"], text_color="white").pack(fill=tk.X, padx=20, pady=16)

    @staticmethod
    def _perfil_lacaio(nivel: int, arquetipo: str, indice: int) -> dict[str, int]:
        """Atributos/Graus coerentes com o Nível, moldados pelo arquétipo."""
        return perfil_lacaio(nivel, arquetipo, indice)

    def _criar_lacaios(self, pai: str, base: str, quantidade: int, arquetipo: str,
                       faccao: str, nivel: int = 1) -> None:
        """Cria as fichas no Nível pedido, com variação de Atributos e Graus."""
        nivel = max(1, nivel)
        for i in range(1, quantidade + 1):
            perfil = self._perfil_lacaio(nivel, arquetipo, i)
            for chave in ("fis", "agi", "intel", "inst"):
                variacao = random.choice((-1, 0, 0, 1))
                perfil[chave] = max(0, min(5, perfil.get(chave, 1) + variacao))
            for chave in ("luta", "acro"):
                variacao = random.choice((-1, 0, 0, 1))
                perfil[chave] = max(0, min(3, perfil.get(chave, 0) + variacao))

            nome_lacaio = f"{base} {i:02d}"
            novo_id = self.tree.insert(pai, "end", text=f" {nome_lacaio} [Lv. {nivel}]", tags=("ficha",))
            self.dados_banco[novo_id] = montar_ficha(nome_lacaio, nivel, **perfil)

        self.registrar_log(f"👥 Gerados {quantidade}x '{base}' Nv {nivel} ({arquetipo}, {faccao}).")

    def _mostrar_relatorio(self, titulo: str, texto: str) -> None:
        top = ctk.CTkToplevel(self.root)
        top.title(titulo)
        top.geometry("560x620")
        top.transient(self.root)
        top.configure(fg_color=self.tema_atual["bg_main"])
        caixa = ctk.CTkTextbox(top, fg_color=self.tema_atual["bg_card"], text_color=self.tema_atual["text"], font=self.get_font('main'), border_width=0, corner_radius=8)
        caixa.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        caixa.insert("1.0", texto)
        caixa.configure(state="disabled")
        ctk.CTkButton(top, text="Fechar", command=top.destroy, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"]).pack(pady=(0, 12))

    def exibir_estatisticas_campanha(self) -> None:
        """Relatório do cofre: facções, faixas de perigo, destaques e recursos."""
        fichas: list[tuple[str, dict]] = []
        total_pastas = 0

        def inteiro(valor, padrao: int = 0) -> int:
            try:
                return max(0, int(str(valor).strip()))
            except (TypeError, ValueError):
                return padrao

        def percorrer(node: str, faccao: str) -> None:
            nonlocal total_pastas
            for child in self.tree.get_children(node):
                tags = self.tree.item(child, "tags")
                if "pasta" in tags:
                    total_pastas += 1
                    nome_pasta = re.sub(r" \[Lv\. .*?\]$", "", self.tree.item(child, "text").strip())
                    percorrer(child, faccao or nome_pasta)
                elif "ficha" in tags:
                    dados = self.abas_abertas[child].get_dados() if child in self.abas_abertas else self.dados_banco.get(child, {})
                    fichas.append((faccao or "Sem pasta", dados))
                    percorrer(child, faccao)

        percorrer("", "")

        if not fichas:
            messagebox.showinfo("Estatísticas", "O cofre está vazio.")
            return

        por_faccao = Counter(faccao for faccao, _ in fichas)
        faixas = {"Iniciantes (1–3)": 0, "Veteranos (4–8)": 0, "Elite (9–14)": 0, "Lendas (15+)": 0}
        soma_niveis = soma_recompensas = soma_pv = soma_pe = 0
        maior_nivel: tuple[str, int] | None = None
        maior_recompensa: tuple[str, int] | None = None
        total_habilidades = 0
        execucoes: Counter = Counter()

        for _faccao, dados in fichas:
            nivel = nivel_seguro(dados.get("nivel", 1))
            soma_niveis += nivel
            if nivel <= 3:
                faixas["Iniciantes (1–3)"] += 1
            elif nivel <= 8:
                faixas["Veteranos (4–8)"] += 1
            elif nivel <= 14:
                faixas["Elite (9–14)"] += 1
            else:
                faixas["Lendas (15+)"] += 1

            recompensa = inteiro(re.sub(r"\D", "", str(dados.get("recompensa", 0))) or 0)
            soma_recompensas += recompensa
            soma_pv += inteiro(dados.get("pv_max") or dados.get("pv", 0))
            soma_pe += inteiro(dados.get("pe_max") or dados.get("pe", 0))

            nome = str(dados.get("nome", "?"))
            if maior_nivel is None or nivel > maior_nivel[1]:
                maior_nivel = (nome, nivel)
            if maior_recompensa is None or recompensa > maior_recompensa[1]:
                maior_recompensa = (nome, recompensa)

            habilidades = dados.get("habilidades", []) or []
            total_habilidades += len(habilidades)
            for hab in habilidades:
                execucoes[(hab.get("execucao") or "—").strip() or "—"] += 1

        linhas = [
            "📊 RESUMO DO COFRE",
            "",
            f"Fichas: {len(fichas)}    Pastas: {total_pastas}",
            f"Nível médio: {soma_niveis / len(fichas):.1f}",
            "",
            "🏴 POR FACÇÃO",
        ]
        for faccao, quantidade in por_faccao.most_common():
            linhas.append(f"• {faccao}: {quantidade}")

        linhas += ["", "☠️ FAIXAS DE PERIGO"]
        for rotulo, quantidade in faixas.items():
            linhas.append(f"• {rotulo}: {quantidade}")

        linhas += ["", "⭐ DESTAQUES"]
        if maior_nivel:
            linhas.append(f"• Maior Nível: {maior_nivel[0]} (Nv {maior_nivel[1]})")
        if maior_recompensa:
            linhas.append("• Maior Recompensa: " + f"{maior_recompensa[0]} (B$ {maior_recompensa[1]:,})".replace(",", "."))

        linhas += ["", "✨ HABILIDADES", f"• Total cadastradas: {total_habilidades}"]
        if execucoes:
            comum, vezes = execucoes.most_common(1)[0]
            linhas.append(f"• Execução mais comum: {comum} ({vezes}x)")
            for execucao, quantidade in execucoes.most_common():
                linhas.append(f"    - {execucao}: {quantidade}")

        linhas += [
            "",
            "❤️ RECURSOS",
            "• PV somados: " + f"{soma_pv:,}".replace(",", "."),
            "• PE somados: " + f"{soma_pe:,}".replace(",", "."),
            "• Recompensas somadas: B$ " + f"{soma_recompensas:,}".replace(",", "."),
        ]

        self._mostrar_relatorio("Estatísticas da Campanha", "\n".join(linhas))

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
        """Abre a ficha com um clique; Ctrl/Shift só selecionam (seleção múltipla)."""
        press = self._press_xy
        self._press_xy = None
        if press is not None and (abs(event.x - press[0]) > 5 or abs(event.y - press[1]) > 5):
            return
        if event.state & 0x0005:  # Shift (0x1) ou Control (0x4): não abre aba
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

            # Mantém o widget no mesmo teto da lista (antes ele crescia sem fim).
            total = int(self.caixa_log.index("end-1c").split(".")[0]) - 1
            if total > 500:
                self.caixa_log.delete("1.0", f"{total - 500 + 1}.0")

            self.caixa_log.see(tk.END)
            self.caixa_log.configure(state="disabled")

    def mostrar_atalhos(self) -> None:
        """Lista todos os atalhos em uma janela de leitura."""
        atalhos = [
            ("Ctrl + S", "Salvar o cofre"),
            ("Ctrl + N", "Criar ficha nova"),
            ("Ctrl + F", "Ir para a busca de fichas"),
            ("F5", "Rolar iniciativa da pasta selecionada"),
            ("Espaço", "Próximo turno no Combat Tracker"),
            ("D", "Aplicar dano em quem está jogando (ou na linha selecionada)"),
            ("C", "Curar quem está jogando (ou na linha selecionada)"),
            ("1 – 9", "Selecionar a 1ª a 9ª linha do Tracker"),
            ("Esc", "Limpar a seleção do Tracker"),
            ("Clique", "Abrir a ficha na árvore"),
            ("Clique direito", "Menu de dano, cura e condições no Tracker"),
        ]
        texto = "\n".join(f"{tecla:<16} {descricao}" for tecla, descricao in atalhos)
        texto += "\n\nDicas:\n• Segure Ctrl ou Shift para selecionar várias fichas e apagar de uma vez.\n• No cabeçalho da ficha, digite a rolagem (ex.: 2d8+3) e clique em Rolar."
        self._mostrar_relatorio("Atalhos", texto)

    def mostrar_sobre(self) -> None:
        self._mostrar_relatorio(
            "Sobre",
            "ImpelDown Archives — One Piece RPG\n\n"
            "Gerenciador de fichas, banco de ameaças e Combat Tracker para o sistema "
            "de One Piece RPG.\n\n"
            "Camadas:\n• core/ — regras, dados e combate\n• ui/ — telas e widgets\n"
            "• utils/ — persistência, loot, história, cartaz e golpes",
        )

    def remover_do_tracker(self, event=None):
        """Delete: tira a linha selecionada (ou o turno atual) do Tracker."""
        selecao = self.lista_iniciativa.curselection()
        indice = selecao[0] if selecao else self.turno_atual_idx
        if not 0 <= indice < len(self.tracker_data):
            return "break"
        removido = self.tracker_data.pop(indice)
        if self.turno_atual_idx >= len(self.tracker_data):
            self.turno_atual_idx = max(0, len(self.tracker_data) - 1)
        self.atualizar_tracker_view()
        self.registrar_log(f"🗑️ {removido['nome']} removido do Tracker.")
        return "break"

    def alternar_log(self) -> None:
        """Mostra/oculta o histórico flutuando sobre o rodapé do Tracker."""
        if not self.tracker_visivel:
            self.toggle_tracker()
        if self._log_aberto:
            self.frame_log.place_forget()
            self._log_aberto = False
            self.btn_log.configure(text="📜 Log")
            return
        # place (e não pack) para o painel não roubar espaço da lista nem
        # ser empurrado para fora da janela em telas baixas.
        self.frame_log.place(relx=0.0, rely=1.0, anchor="sw", relwidth=1.0)
        self.frame_log.lift()
        self._log_aberto = True
        self.btn_log.configure(text="📜 Fechar")
        self.caixa_log.see(tk.END)

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
        
        # Procura a lista de bando subindo na hierarquia (rótulo/botão -> linha -> lista).
        alvo_bando = widget_sob_mouse
        while alvo_bando is not None and not hasattr(alvo_bando, "bando_tag"):
            alvo_bando = getattr(alvo_bando, "master", None)
        if alvo_bando is not None:
            if "ficha" in self.tree.item(self.item_arrastado, "tags"):
                nome_arrastado = re.sub(
                    r" \[Lv\. .*?\]$", "", self.tree.item(self.item_arrastado, "text").strip()
                )
                alvo_bando.insert(tk.END, nome_arrastado)
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
            # Move também as outras fichas selecionadas (Ctrl/Shift), sem
            # tentar mover uma pasta para dentro dela mesma.
            selecionados = [i for i in self.tree.selection() if self.tree.exists(i)]
            movidos = selecionados if item in selecionados and len(selecionados) > 1 else [item]
            for movido in movidos:
                if not self.tree.exists(movido) or movido == target:
                    continue
                if eh_descendente(movido, target):
                    continue
                self.tree.move(movido, target, "end")
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

    def _ja_esta_no_tracker(self, item_id, nome) -> bool:
        """Evita duplicar a mesma ficha (ou lacaio) na iniciativa."""
        return any(
            linha.get("id") == item_id and linha.get("nome") == nome
            for linha in self.tracker_data
        )

    def _bando_alterado(self, origem) -> None:
        """Mantém todas as abas abertas sincronizadas com o bando compartilhado."""
        for ficha in self.abas_abertas.values():
            lista = getattr(ficha, "listbox_bando", None)
            if lista is not None and lista is not origem:
                lista.recarregar()

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

            if self._ja_esta_no_tracker(item_id, nome):
                self.registrar_log(f"⚠️ {nome} já está no Tracker.")
                return

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
                if self._ja_esta_no_tracker(child, nome):
                    self.registrar_log(f"⚠️ {nome} já estava no Tracker (ignorado).")
                    continue
                agi = dados.get("agi", 0)
                # Iniciativa 1d20 + Agilidade: conveniência de mesa (não é regra do livro).
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
        menu = tk.Menu(self.root, tearoff=0, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], bd=0, activebackground=self.tema_atual["accent"])
        menu.add_command(label="⚔️ Aplicar Dano…", command=lambda: self.ajustar_pv_da_linha(idx, -1))
        menu.add_command(label="💚 Curar…", command=lambda: self.ajustar_pv_da_linha(idx, 1))
        menu.add_command(label="💀 Zerar PV", command=lambda: self.aplicar_pv_tracker(idx, -1000000))
        menu.add_separator()

        ativas = {cond["chave"]: cond for cond in self._condicoes_linha(self.tracker_data[idx])}
        submenu = tk.Menu(menu, tearoff=0, bg=self.tema_atual["bg_card"], fg=self.tema_atual["text"], bd=0, activebackground=self.tema_atual["accent"])
        for chave, (icone, nome, _efeito) in CONDICOES.items():
            ativa = ativas.get(chave)
            if ativa:
                prazo = f" ({ativa['turnos']}t)" if ativa["turnos"] else " (∞)"
                marcado = "✓ "
            else:
                prazo, marcado = "", "      "
            submenu.add_command(label=f"{marcado}{icone} {nome}{prazo}", command=lambda c=chave: self._aplicar_condicao_com_duracao(idx, c))
        submenu.add_separator()
        submenu.add_command(label="⏱ +1 turno nas condições", command=lambda: self.ajustar_turnos_condicoes(idx, 1))
        submenu.add_command(label="⏱ -1 turno nas condições", command=lambda: self.ajustar_turnos_condicoes(idx, -1))
        submenu.add_command(label="⏱ +1 minuto (10 turnos)", command=lambda: self.ajustar_turnos_condicoes(idx, 10))
        submenu.add_command(label="⏱ -1 minuto (10 turnos)", command=lambda: self.ajustar_turnos_condicoes(idx, -10))
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
        self._registrar_undo({"tipo": "cond", "indice": index, "nome": alvo["nome"],
                              "status": [dict(cond) for cond in ativas]})

        if chave in chaves:
            ativas = [cond for cond in ativas if cond["chave"] != chave]
            self.registrar_log(f"{icone_condicao(chave)} {nome_condicao(chave)} removida de {alvo['nome']}.")
        else:
            ativas.append({"chave": chave, "turnos": turnos})
            prazo = f" ({turnos} turnos)" if turnos else ""
            self.registrar_log(f"{icone_condicao(chave)} {nome_condicao(chave)} aplicada em {alvo['nome']}{prazo}.")

        alvo["status"] = ativas
        self._atualizar_linha(index)

    def _aplicar_condicao_com_duracao(self, index: int, chave: str) -> None:
        """Abre a escolha de duração (turnos ou minutos) antes de aplicar."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        if chave in [cond["chave"] for cond in self._condicoes_linha(alvo)]:
            self.alternar_condicao(index, chave)
            return

        top = ctk.CTkToplevel(self.root)
        top.title("Duração da condição")
        top.geometry("360x250")
        top.transient(self.root)
        top.attributes("-topmost", True)
        top.configure(fg_color=self.tema_atual["bg_main"])

        ctk.CTkLabel(
            top, text=f"{icone_condicao(chave)} {nome_condicao(chave)}",
            font=self.get_font('title'), text_color=self.tema_atual["accent"],
        ).pack(pady=(14, 4))
        ctk.CTkLabel(top, text="Duração", font=self.get_font('small'), text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)

        var_modo = tk.StringVar(value="Turnos")
        var_valor = tk.StringVar(value=str(TURNOS_PADRAO))
        linha = ctk.CTkFrame(top, fg_color="transparent")
        linha.pack(fill=tk.X, padx=20, pady=(4, 6))
        ctk.CTkSegmentedButton(
            linha, variable=var_modo, values=["Turnos", "Minutos"],
            fg_color=self.tema_atual["bg_input"], selected_color=self.tema_atual["accent"],
            selected_hover_color=self.tema_atual.get("accent_hover", self.tema_atual["accent"]),
            unselected_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"],
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ctk.CTkEntry(linha, textvariable=var_valor, width=60, fg_color=self.tema_atual["bg_input"],
                     text_color=self.tema_atual["text"], border_width=0, justify="center").pack(side=tk.LEFT, padx=(8, 0))

        ctk.CTkLabel(top, text="1 minuto = 10 turnos (1 turno = 6 s)", font=self.get_font('small'),
                     text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=20)

        def confirmar() -> None:
            texto = str(var_valor.get()).strip()
            if not texto.isdigit() or int(texto) <= 0:
                messagebox.showwarning("Duração", "Informe um número maior que zero.", parent=top)
                return
            valor = int(texto)
            if var_modo.get() == "Minutos":
                turnos = valor * 10
                self.registrar_log(f"⏱ {valor} min = {turnos} turnos")
            else:
                turnos = valor
            self.alternar_condicao(index, chave, turnos)
            top.destroy()

        botoes = ctk.CTkFrame(top, fg_color="transparent")
        botoes.pack(fill=tk.X, padx=20, pady=12)
        ctk.CTkButton(botoes, text="Aplicar", command=confirmar, fg_color=self.tema_atual["accent"], text_color="white").pack(side=tk.LEFT, expand=True, fill=tk.X)
        ctk.CTkButton(botoes, text="Sem prazo (∞)", command=lambda: (self.alternar_condicao(index, chave, None), top.destroy()), fg_color=self.tema_atual["bg_input"], text_color=self.tema_atual["text"]).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))

    def ajustar_turnos_condicoes(self, index: int, delta: int) -> None:
        """Soma ou tira 1 turno de todas as condições com prazo da linha."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        self._registrar_undo({"tipo": "cond", "indice": index, "nome": alvo["nome"],
                              "status": [dict(cond) for cond in self._condicoes_linha(alvo)]})
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
        self._atualizar_linha(index)

    def limpar_condicoes(self, index: int) -> None:
        """Remove todas as condições da linha."""
        if not 0 <= index < len(self.tracker_data):
            return
        alvo = self.tracker_data[index]
        self._registrar_undo({"tipo": "cond", "indice": index, "nome": alvo["nome"],
                              "status": [dict(cond) for cond in self._condicoes_linha(alvo)]})
        alvo["status"] = []
        self._atualizar_linha(index)
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
        
        texto_dif, cor_dif = self._dificuldade_atual()
        self.lbl_dificuldade.configure(text=f"Encontro: {texto_dif}", text_color=cor_dif)

        self._mapa_tracker: dict[str, list[int]] = {}
        for i, t in enumerate(self.tracker_data):
            texto, cor, morto = self._render_linha(i, t)
            self.lista_iniciativa.insert(tk.END, texto)
            self.lista_iniciativa.itemconfig(i, fg=cor)
            self._mapa_tracker.setdefault(t.get("id", ""), []).append(i)

        if selecionado is not None:
            for i, t in enumerate(self.tracker_data):
                if t is selecionado:
                    self.lista_iniciativa.selection_set(i)
                    break

        self._atualizar_painel_turno()

    def _render_linha(self, indice: int, t: dict) -> tuple[str, str, bool]:
        """Monta (texto, cor, morto) de uma linha do Tracker."""
        nome_exib = t["nome"]
        if len(nome_exib) > 13:
            nome_exib = nome_exib[:11] + "..."

        item_id = t.get("id", "")
        pv_texto = self._pv_da_linha(item_id)
        marcador = "▶ " if indice == self.turno_atual_idx else "  "
        texto = f"{marcador}[{t['ini']:02d}] {nome_exib:<13} {pv_texto:<7}"
        sufixo = self._sufixo_status(t)
        if sufixo:
            texto += " " + sufixo

        morto = False
        if item_id in self.abas_abertas or item_id in self.dados_banco:
            pv_atual, pv_max = self.obter_pv(item_id)
            cor = self._cor_do_pv(pv_atual, pv_max)
            morto = pv_atual <= 0
        else:
            cor = COR_TEXTO_SUAVE
        return texto, cor, morto

    def _atualizar_linha(self, indice: int) -> None:
        """Redesenha só uma linha do Tracker (dano/condição), sem rebuild total."""
        if not 0 <= indice < len(self.tracker_data):
            return
        if indice >= self.lista_iniciativa.size():
            self.atualizar_tracker_view()
            return

        selecao = self.lista_iniciativa.curselection()
        texto, cor, morto = self._render_linha(indice, self.tracker_data[indice])
        self.lista_iniciativa.delete(indice)
        self.lista_iniciativa.insert(indice, texto)
        self.lista_iniciativa.itemconfig(indice, fg=cor, bg=self.tema_atual["bg_sidebar"])
        for i in selecao:
            if i < self.lista_iniciativa.size():
                self.lista_iniciativa.selection_set(i)
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
            self.lbl_turno_condicoes.configure(text="Sem condições.", text_color=COR_TEXTO_SUAVE)
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
            self.lbl_turno_condicoes.configure(text="Sem condições.", text_color=COR_TEXTO_SUAVE)
            return

        pedacos = []
        for cond in ativas:
            prazo = f" ({cond['turnos']}t)" if cond["turnos"] else ""
            pedacos.append(f"{icone_condicao(cond['chave'])} {nome_condicao(cond['chave'])}{prazo}")
        self.lbl_turno_condicoes.configure(text="  ".join(pedacos), text_color=COR_AVISO)

    @staticmethod
    def _inteiro_positivo(var: tk.StringVar, padrao: int) -> int:
        """Lê um campo numérico do painel, com fallback para o padrão."""
        texto = str(var.get()).strip()
        return int(texto) if texto.isdigit() and int(texto) > 0 else padrao

    @staticmethod
    def _pasta_normalizada(texto: str) -> str:
        return str(texto or "").strip().lower()

    def _item_e_jogador(self, item_id: str) -> bool:
        """Ficha de jogador (pasta Player/Jogadores/Party) não entra no desafio."""
        if not item_id:
            return False
        return self._pasta_normalizada(self.faccao_do_item(item_id)) in PASTAS_JOGADOR

    def _dificuldade_atual(self) -> tuple[str, str]:
        """Desafio por dano/rodada contra o HP total dos inimigos (sem players)."""
        inimigos = [
            linha for linha in self.tracker_data
            if not self._item_e_jogador(linha.get("id", ""))
        ]
        if not inimigos:
            return "Sem Inimigos", COR_TEXTO_SUAVE

        jogadores = self._inteiro_positivo(self.var_jogadores, 4)
        nivel = self._inteiro_positivo(self.var_nivel_grupo, 1)

        hp_total = 0
        for linha in inimigos:
            item_id = linha.get("id", "")
            if item_id in self.abas_abertas or item_id in self.dados_banco:
                # PV atual: mede quantas rodadas faltam para zerar o combate.
                hp_total += self.obter_pv(item_id)[0]

        if hp_total <= 0:
            return "Inimigos derrotados", COR_TEXTO_SUAVE

        dados = analisar_desafio(jogadores, nivel, hp_total)
        return dados["resumo"], dados["cor"]

    def atualizar_dificuldade(self) -> None:
        """Recalcula só o rótulo do encontro (sem reconstruir a lista)."""
        texto, cor = self._dificuldade_atual()
        self.lbl_dificuldade.configure(text=f"Encontro: {texto}", text_color=cor)

    def _cor_do_pv(self, atual: int, maximo: int) -> str:
        """Verde acima de 50%, âmbar até 50%, vermelho até 25% e em 0."""
        if atual <= 0:
            return COR_PERIGO
        proporcao = atual / maximo if maximo else 0.0
        if proporcao > 0.5:
            return COR_SUCESSO
        if proporcao > 0.25:
            return COR_AVISO
        return COR_PERIGO

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

        aba = self.abas_abertas.get(item_id)
        if aba is not None:
            aba.sincronizar_agora()  # evita ler um máximo ainda preso no debounce

        atual, maximo = self.obter_pv(item_id)
        novo = max(0, min(maximo, atual + delta))
        if novo == atual:
            return

        self._registrar_undo({"tipo": "pv", "id": item_id, "nome": alvo["nome"], "pv": atual})

        if aba is not None:
            aba.pv_atual.set(novo)

        dados = self.dados_banco.setdefault(item_id, {})
        dados["pv"] = novo
        dados.setdefault("pv_max", maximo)
        dados.setdefault("nome", alvo.get("nome", ""))

        self._atualizar_linha(index)
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
            
        indices = list(getattr(self, "_mapa_tracker", {}).get(item_id, []))
        if not indices:
            indices = [i for i, t in enumerate(self.tracker_data) if t.get("id") == item_id]
        for i in indices:
            if 0 <= i < len(self.tracker_data) and self.tracker_data[i].get("id") == item_id:
                self.tracker_data[i]["nome"] = novo_nome
                self._atualizar_linha(i)

    def novo_banco(self):
        if not messagebox.askyesno("Novo Cofre", "Você iniciará uma nova campanha. Alterações não salvas serão perdidas. Continuar?"):
            return
        self.arquivo_atual = None
        self.dados_banco.clear()
        self.bando_global.clear()
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
        self._destruir_cache_abas()

    def _destruir_cache_abas(self) -> None:
        """Descarta as fichas guardadas em cache (troca de cofre/exclusão)."""
        for frame, _ficha in self._abas_cache.values():
            if frame.winfo_exists():
                frame.destroy()
        self._abas_cache.clear()

    def _guardar_aba_em_cache(self, item_id: str, ficha) -> None:
        """Guarda a ficha fechada para reabrir sem reconstruir tudo."""
        self._abas_cache[item_id] = (ficha.master, ficha)
        excedentes = [chave for chave in self._abas_cache if chave != item_id]
        while len(self._abas_cache) > 4 and excedentes:
            antiga = excedentes.pop(0)
            frame, _ = self._abas_cache.pop(antiga)
            if frame.winfo_exists():
                frame.destroy()

    def _reiniciar_pesquisa(self) -> None:
        """Limpa a busca e o cache da árvore após trocar de cofre."""
        self.arvore_cache = None
        if self.var_pesquisa.get():
            self.var_pesquisa.set("")

    def _configuracao_sessao(self) -> dict:
        """Dados de configuração que viajam dentro do cofre."""
        return {
            "jogadores": self._inteiro_positivo(self.var_jogadores, 4),
            "nivel_grupo": self._inteiro_positivo(self.var_nivel_grupo, 1),
            "bando": list(self.bando_global),
        }

    def _aplicar_configuracao(self, config: dict) -> None:
        if not config:
            return
        jogadores = config.get("jogadores")
        if str(jogadores).isdigit():
            self.var_jogadores.set(str(jogadores))
        nivel_grupo = config.get("nivel_grupo")
        if str(nivel_grupo).isdigit():
            self.var_nivel_grupo.set(str(nivel_grupo))
        bando = config.get("bando")
        if isinstance(bando, list):
            self.bando_global = [str(nome).strip() for nome in bando if str(nome).strip()]
        self.atualizar_dificuldade()

    def _gravar_banco(self, caminho: str) -> bool:
        """Grava o cofre no caminho indicado; devolve se deu certo."""
        for item_id, aba in self.abas_abertas.items():
            self.dados_banco[item_id] = aba.get_dados()
        try:
            # Com a busca ativa a árvore está filtrada: salvar o cache completo.
            if self.var_pesquisa.get().strip() and self.arvore_cache:
                estrutura = self.arvore_cache
            else:
                estrutura = self.mapear_arvore_completa("")
            salvar_banco_sqlite(caminho, estrutura, self.dados_banco, self._configuracao_sessao())
        except Exception as e:
            messagebox.showerror("Erro de Gravação", str(e))
            return False
        return True

    def _agendar_autosave(self) -> None:
        self._autosave_id = self.root.after(AUTOSAVE_MINUTOS * 60_000, self._autosave)

    def _autosave(self) -> None:
        """Salva o cofre em silêncio a cada AUTOSAVE_MINUTOS (se já houver arquivo)."""
        try:
            if self.arquivo_atual:
                for item_id, aba in self.abas_abertas.items():
                    self.dados_banco[item_id] = aba.get_dados()
                if self.var_pesquisa.get().strip() and self.arvore_cache:
                    estrutura = self.arvore_cache
                else:
                    estrutura = self.mapear_arvore_completa("")
                salvar_banco_sqlite(
                    self.arquivo_atual, estrutura, self.dados_banco, self._configuracao_sessao()
                )
                self._marcar_status_salvo(auto=True)
                self.registrar_log("💾 Salvamento automático concluído.")
        except Exception as erro:
            self.registrar_log(f"⚠️ Falha no salvamento automático: {erro}")
        finally:
            try:
                if self.root.winfo_exists():
                    self._agendar_autosave()
            except tk.TclError:
                pass

    def _marcar_status_salvo(self, auto: bool = False) -> None:
        """Rodapé discreto com a hora do último salvamento."""
        try:
            from datetime import datetime
            hora = datetime.now().strftime("%H:%M")
            self.lbl_status.configure(text=f"💾 {'auto' if auto else 'salvo'} {hora}")
        except (tk.TclError, AttributeError):
            pass

    def salvar_banco(self) -> bool:
        if not self.arquivo_atual:
            return self.salvar_como_banco()
        if self._gravar_banco(self.arquivo_atual):
            self.registrar_log(f"💾 Cofre salvo em {self.arquivo_atual}")
            self._marcar_status_salvo()
            messagebox.showinfo("Salvo", f"Cofre salvo com sucesso em:\n{self.arquivo_atual}", parent=self.root)
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
            self._marcar_status_salvo()
            messagebox.showinfo("Salvo", f"Cofre salvo com sucesso em:\n{caminho}", parent=self.root)
            return True
        return False

    def carregar_banco(self):
        caminho = filedialog.askopenfilename(filetypes=[("Banco SQLite", "*.db"), ("Todos os Arquivos", "*.*")], title="Abrir Cofre")
        if not caminho:
            return
        try:
            estrutura, fichas, config = carregar_banco_sqlite(caminho)
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
        self._aplicar_configuracao(config)
        # Fichas antigas guardavam o bando individualmente: junta tudo no bando
        # compartilhado, sem duplicar nomes.
        for dados in fichas.values():
            membros = dados.get("bando", []) if isinstance(dados, dict) else []
            if not isinstance(membros, list):
                continue
            for nome in membros:
                if nome and nome not in self.bando_global:
                    self.bando_global.append(nome)

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
        """Exclui uma ou várias fichas/pastas selecionadas (Ctrl/Shift)."""
        if self.bloquear_se_buscando():
            return
        selecionados = list(self.tree.selection())
        if not selecionados:
            return

        if len(selecionados) == 1:
            pergunta = f"Deseja excluir '{self.tree.item(selecionados[0], 'text').strip()}' e todo seu conteúdo?"
        else:
            pergunta = f"Deseja excluir as {len(selecionados)} seleções e todo o conteúdo delas?"

        if not messagebox.askyesno("Confirmar", pergunta):
            return

        ids_unicos = [i for i in selecionados if self.tree.exists(i)]

        def excluir_recursivamente(node: str) -> None:
            for filho in self.tree.get_children(node):
                excluir_recursivamente(filho)
            if node in self.abas_abertas:
                aba = self.abas_abertas.pop(node)
                self.notebook.forget(aba.master)
                aba.master.destroy()
            if node in self._abas_cache:
                frame, _ficha = self._abas_cache.pop(node)
                if frame.winfo_exists():
                    frame.destroy()
            self.dados_banco.pop(node, None)
            for t in list(self.tracker_data):
                if t["id"] == node:
                    self.tracker_data.remove(t)

        # Remove primeiro os que não estão dentro de outro selecionado.
        for item_id in ids_unicos:
            if self.tree.exists(item_id):
                excluir_recursivamente(item_id)
                self.tree.delete(item_id)

        self.atualizar_tracker_view()
        self.registrar_log(f"🗑️ {len(ids_unicos)} item(ns) excluído(s).")

    def abrir_aba_personagem(self, item_id, nome):
        if item_id in self.abas_abertas:
            self.notebook.select(self.abas_abertas[item_id].master)
            return

        # Reabre instantaneamente uma ficha que foi fechada (cache de abas).
        if item_id in self._abas_cache:
            frame_cache, ficha_cache = self._abas_cache.pop(item_id)
            if frame_cache.winfo_exists():
                dados = self.dados_banco.get(item_id, {})
                ficha_cache.atualizar_dados_rapidos(dados)
                self.notebook.add(frame_cache, text=f"   {dados.get('nome', nome)}   ")
                self.notebook.select(frame_cache)
                self.abas_abertas[item_id] = ficha_cache
                return

        frame_aba = ctk.CTkFrame(self.notebook, fg_color=self.tema_atual["bg_main"], corner_radius=0)
        barra_topo = ctk.CTkFrame(frame_aba, fg_color="transparent")
        barra_topo.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)
        
        ctk.CTkButton(barra_topo, text="✖ Fechar Ficha", command=lambda: self.fechar_aba(item_id), fg_color="transparent", hover_color=COR_BOTAO_PERIGO, text_color=COR_PERIGO, width=120).pack(side=tk.RIGHT)

        dados = self.dados_banco.get(item_id, None)
        ficha = FichaPersonagemFrame(frame_aba, lambda nome, nivel: self.sync_nome_ficha(item_id, nome, nivel), app_master=self, dados_iniciais=dados)
        ficha.pack(fill=tk.BOTH, expand=True)

        # Ações secundárias ficam na barra da aba, para o cabeçalho da ficha
        # não estourar quando o painel do Tracker está aberto.
        ctk.CTkButton(barra_topo, text="📝 Exportar .md", command=ficha.exportar_markdown, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"], width=100).pack(side=tk.RIGHT, padx=(0, 5))
        ctk.CTkButton(barra_topo, text="📜 Cartaz WANTED", command=ficha.gerar_cartaz, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"], width=130).pack(side=tk.RIGHT, padx=(0, 5))
        ctk.CTkButton(barra_topo, text="🖥️ Tela Jogador", command=ficha.abrir_modo_jogador, fg_color=self.tema_atual["bg_input"], hover_color=COR_HOVER, text_color=self.tema_atual["text"], width=110).pack(side=tk.RIGHT, padx=(0, 5))

        self.notebook.add(frame_aba, text=f"   {nome}   ")
        self.notebook.select(frame_aba)
        self.abas_abertas[item_id] = ficha

    def fechar_aba(self, item_id):
        if item_id in self.abas_abertas:
            aba = self.abas_abertas.pop(item_id)
            self.dados_banco[item_id] = aba.get_dados()
            self.notebook.forget(aba.master)
            self._guardar_aba_em_cache(item_id, aba)

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