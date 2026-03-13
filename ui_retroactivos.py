"""Interfaz para capturar datos de retroactivos."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class EntradaRetroactivo:
    """Datos de un empleado con retroactivo."""
    cedula: str
    motivo: str
    meses: list[str]  # ["01", "03", "05"] → Ene, Mar, May


class DialogoMontosNuevos:
    """Ventana para registrar montos de meses faltantes."""

    def __init__(self, parent, meses_faltantes: list[str], meses_nombres: dict[str, str], anio: str):
        self.resultado: dict[str, float] = {}
        self.cancelado = False

        self.win = tk.Toplevel(parent)
        self.win.title(f"Montos faltantes — {anio}")
        self.win.grab_set()
        self.win.resizable(False, False)

        # Encabezado
        tk.Label(
            self.win,
            text=f"Faltan montos de cesta ticket para {anio}.\nIngresa los valores:",
            font=('Segoe UI', 10, 'bold'),
            justify='left',
            padx=10, pady=10,
        ).pack()

        # Frame de entradas
        frame = tk.Frame(self.win, padx=20, pady=5)
        frame.pack()

        self.entries = {}
        for mes in meses_faltantes:
            nombre = meses_nombres.get(mes, mes)
            row = tk.Frame(frame)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=f"{nombre}/{anio}:", width=15, anchor='w').pack(side='left')
            entry = tk.Entry(row, width=15)
            entry.pack(side='left', padx=5)
            self.entries[mes] = entry

        # Botones
        btn_frame = tk.Frame(self.win, pady=10)
        btn_frame.pack()
        tk.Button(btn_frame, text="Guardar", command=self._guardar, width=12).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancelar", command=self._cancelar, width=12).pack(side='left', padx=5)

        self.win.wait_window()

    def _guardar(self):
        for mes, entry in self.entries.items():
            valor = entry.get().strip()
            if not valor:
                messagebox.showwarning("Atención", f"Falta el monto del mes {mes}.", parent=self.win)
                return
            try:
                self.resultado[mes] = float(valor)
            except ValueError:
                messagebox.showwarning("Atención", f"Valor inválido para mes {mes}.", parent=self.win)
                return
        self.win.destroy()

    def _cancelar(self):
        self.cancelado = True
        self.win.destroy()


class DialogoRetroactivos:
    """Ventana principal para capturar cédulas y meses de retroactivo."""

    def __init__(self, parent, meses_nombres: dict[str, str], motivos: list[str], anio: str):
        self.resultado: list[EntradaRetroactivo] = []
        self.cancelado = False

        self.meses_nombres = meses_nombres
        self.anio = anio

        self.win = tk.Toplevel(parent)
        self.win.title("Retroactivos")
        self.win.grab_set()
        self.win.resizable(False, False)
        self.win.minsize(500, 400)

        # --- Encabezado ---
        tk.Label(
            self.win,
            text="Ingresa las cédulas con retroactivo pendiente",
            font=('Segoe UI', 11, 'bold'),
            pady=10,
        ).pack()

        # --- Frame de entrada ---
        input_frame = tk.LabelFrame(self.win, text="Nuevo retroactivo", padx=10, pady=10)
        input_frame.pack(fill='x', padx=15, pady=5)

        # Cédula
        row_ced = tk.Frame(input_frame)
        row_ced.pack(fill='x', pady=3)
        tk.Label(row_ced, text="Cédula:", width=10, anchor='w').pack(side='left')
        self.entry_cedula = tk.Entry(row_ced, width=20)
        self.entry_cedula.pack(side='left', padx=5)

        # Motivo (combobox)
        row_mot = tk.Frame(input_frame)
        row_mot.pack(fill='x', pady=3)
        tk.Label(row_mot, text="Motivo:", width=10, anchor='w').pack(side='left')
        self.combo_motivo = ttk.Combobox(row_mot, values=motivos, width=45)
        self.combo_motivo.pack(side='left', padx=5)
        if motivos:
            self.combo_motivo.current(0)

        # Meses (burbujas seleccionables)
        row_meses = tk.LabelFrame(input_frame, text="Meses a pagar (máx. 3)", padx=5, pady=5)
        row_meses.pack(fill='x', pady=5)

        self.vars_meses: dict[str, tk.BooleanVar] = {}
        self.checks_meses: dict[str, tk.Checkbutton] = {}

        meses_ordenados = sorted(meses_nombres.keys())
        for i, mes_num in enumerate(meses_ordenados):
            var = tk.BooleanVar(value=False)
            nombre = meses_nombres[mes_num]
            chk = tk.Checkbutton(
                row_meses,
                text=nombre,
                variable=var,
                command=self._limitar_seleccion,
                width=5,
            )
            chk.grid(row=i // 6, column=i % 6, padx=3, pady=2)
            self.vars_meses[mes_num] = var
            self.checks_meses[mes_num] = chk

        # Botón agregar
        tk.Button(
            input_frame, text="+ Agregar", command=self._agregar,
            bg='#4CAF50', fg='white', width=15,
        ).pack(pady=8)

        # --- Lista de agregados ---
        list_frame = tk.LabelFrame(self.win, text="Retroactivos ingresados", padx=10, pady=5)
        list_frame.pack(fill='both', expand=True, padx=15, pady=5)

        self.listbox = tk.Listbox(list_frame, height=8, font=('Consolas', 9))
        self.listbox.pack(fill='both', expand=True)

        # Botón eliminar
        tk.Button(
            list_frame, text="Eliminar seleccionado", command=self._eliminar,
        ).pack(pady=3)

        # --- Botones finales ---
        btn_frame = tk.Frame(self.win, pady=10)
        btn_frame.pack()

        tk.Button(
            btn_frame, text="Procesar", command=self._procesar,
            bg='#2196F3', fg='white', width=15,
        ).pack(side='left', padx=5)
        tk.Button(
            btn_frame, text="Omitir retroactivos", command=self._omitir,
            width=15,
        ).pack(side='left', padx=5)

        self.win.wait_window()

    def _limitar_seleccion(self):
        """Solo permite hasta 3 meses seleccionados."""
        seleccionados = [m for m, v in self.vars_meses.items() if v.get()]
        if len(seleccionados) >= 3:
            for mes, var in self.vars_meses.items():
                if not var.get():
                    self.checks_meses[mes].config(state='disabled')
        else:
            for mes, chk in self.checks_meses.items():
                chk.config(state='normal')

    def _agregar(self):
        cedula = self.entry_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Atención", "Ingresa una cédula.", parent=self.win)
            return

        motivo = self.combo_motivo.get().strip()
        if not motivo:
            messagebox.showwarning("Atención", "Selecciona un motivo.", parent=self.win)
            return

        meses = sorted([m for m, v in self.vars_meses.items() if v.get()])
        if not meses:
            messagebox.showwarning("Atención", "Selecciona al menos un mes.", parent=self.win)
            return

        # Verificar duplicado
        for r in self.resultado:
            if r.cedula == cedula:
                messagebox.showwarning(
                    "Atención",
                    f"La cédula {cedula} ya fue agregada para este pedido.",
                    parent=self.win,
                )
                return

        entrada = EntradaRetroactivo(cedula=cedula, motivo=motivo, meses=meses)
        self.resultado.append(entrada)

        # Mostrar en la lista
        meses_txt = ", ".join(self.meses_nombres.get(m, m) for m in meses)
        self.listbox.insert(tk.END, f"C.I. {cedula} | {meses_txt} | {motivo}")

        # Limpiar
        self.entry_cedula.delete(0, tk.END)
        for var in self.vars_meses.values():
            var.set(False)
        self._limitar_seleccion()

    def _eliminar(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.listbox.delete(idx)
        self.resultado.pop(idx)

    def _procesar(self):
        if not self.resultado:
            messagebox.showwarning(
                "Atención", "No hay retroactivos ingresados.", parent=self.win
            )
            return
        self.win.destroy()

    def _omitir(self):
        self.resultado = []
        self.cancelado = True
        self.win.destroy()