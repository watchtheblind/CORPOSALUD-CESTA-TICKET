"""Ventana de inicio para seleccionar qué procesadores ejecutar."""

import tkinter as tk
from tkinter import ttk


class LauncherUI:
    """Permite marcar/desmarcar procesadores y comenzar la ejecución."""

    def __init__(self, parent):
        self.resultado: dict[str, bool] = {}
        self.cancelado = False

        self.win = tk.Toplevel(parent)
        self.win.title("Selector de procesadores")
        self.win.grab_set()
        self.win.resizable(False, False)
        self.win.transient(parent)

        # --- Encabezado ---
        tk.Label(
            self.win,
            text="Seleccione los procesadores a ejecutar",
            font=('Segoe UI', 12, 'bold'),
            pady=12,
        ).pack()

        frame = tk.LabelFrame(self.win, text="Procesadores", padx=20, pady=12)
        frame.pack(padx=20, pady=5)

        self.vars: dict[str, tk.BooleanVar] = {}
        for clave, texto in [
            ('activos', 'Activos'),
            ('cmp', 'CMP'),
            ('cmp_custom', 'CMP Custom'),
            ('retro', 'Retroactivos'),
        ]:
            var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                frame, text=texto, variable=var,
                font=('Segoe UI', 10),
            ).pack(anchor='w', pady=3)
            self.vars[clave] = var

        # --- Botones ---
        btn_frame = tk.Frame(self.win, pady=14)
        btn_frame.pack()

        tk.Button(
            btn_frame, text="Comenzar", command=self._comenzar,
            bg='#2196F3', fg='white', width=14,
        ).pack(side='left', padx=5)
        tk.Button(
            btn_frame, text="Cancelar", command=self._cancelar,
            width=14,
        ).pack(side='left', padx=5)

        self.win.protocol("WM_DELETE_WINDOW", self._cancelar)
        self.win.wait_window()

    def _comenzar(self):
        if not any(v.get() for v in self.vars.values()):
            tk.messagebox.showwarning(
                "Atención",
                "Selecciona al menos un procesador.",
                parent=self.win,
            )
            return
        self.resultado = {k: v.get() for k, v in self.vars.items()}
        self.win.destroy()

    def _cancelar(self):
        self.cancelado = True
        self.resultado = {}
        self.win.destroy()
