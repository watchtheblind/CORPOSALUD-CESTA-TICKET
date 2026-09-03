"""Interfaz para capturar cédulas de CMP Custom (manual + importación masiva)."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class EntradaCMPCustom:
    """Datos de un empleado con CMP custom."""
    cedula: str
    dependencia: str
    observaciones: str


class DialogoCMPCustom:
    """Ventana principal para capturar cédulas y motivos de CMP custom."""

    def __init__(self, parent):
        self.resultado: list[EntradaCMPCustom] = []
        self.cancelado = False

        self.win = tk.Toplevel(parent)
        self.win.title("CMP Custom — Cédulas con monto 0")
        self.win.grab_set()
        self.win.resizable(True, True)
        self.win.minsize(580, 500)

        # --- Encabezado ---
        tk.Label(
            self.win,
            text="Cédulas con monto cesta ticket = 0",
            font=('Segoe UI', 11, 'bold'),
            pady=10,
        ).pack()

        # --- Entrada manual ---
        input_frame = tk.LabelFrame(self.win, text="Agregar manualmente", padx=10, pady=10)
        input_frame.pack(fill='x', padx=15, pady=5)

        # Cédula
        row_ced = tk.Frame(input_frame)
        row_ced.pack(fill='x', pady=3)
        tk.Label(row_ced, text="Cédula:", width=14, anchor='w').pack(side='left')
        self.entry_cedula = tk.Entry(row_ced, width=20)
        self.entry_cedula.pack(side='left', padx=5)

        # Dependencia
        row_dep = tk.Frame(input_frame)
        row_dep.pack(fill='x', pady=3)
        tk.Label(row_dep, text="Dependencia:", width=14, anchor='w').pack(side='left')
        self.entry_dependencia = tk.Entry(row_dep, width=45)
        self.entry_dependencia.pack(side='left', padx=5)

        # Observaciones
        row_obs = tk.Frame(input_frame)
        row_obs.pack(fill='x', pady=3)
        tk.Label(row_obs, text="Observaciones:", width=14, anchor='w').pack(side='left')
        self.entry_observaciones = tk.Entry(row_obs, width=45)
        self.entry_observaciones.pack(side='left', padx=5)

        # Botón agregar
        tk.Button(
            input_frame, text="+ Agregar", command=self._agregar,
            bg='#4CAF50', fg='white', width=15,
        ).pack(pady=8)

        # --- Botón importar masivo ---
        tk.Button(
            self.win,
            text="Importar cédulas y motivos desde Excel",
            command=self._importar_desde_excel,
            bg='#FF9800', fg='white', width=35, height=2,
        ).pack(pady=8)

        # --- Lista de agregados ---
        list_frame = tk.LabelFrame(self.win, text="Cédulas ingresadas", padx=10, pady=5)
        list_frame.pack(fill='both', expand=True, padx=15, pady=5)

        self.listbox = tk.Listbox(list_frame, height=8, font=('Consolas', 9))
        self.listbox.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(self.listbox, orient='vertical', command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)

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
            btn_frame, text="Omitir CMP Custom", command=self._omitir,
            width=15,
        ).pack(side='left', padx=5)

        self.win.protocol("WM_DELETE_WINDOW", self._omitir)
        self.win.wait_window()

    # --- Acciones manuales ---

    def _agregar(self):
        cedula = self.entry_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Atención", "Ingresa una cédula.", parent=self.win)
            return

        dependencia = self.entry_dependencia.get().strip()
        if not dependencia:
            messagebox.showwarning("Atención", "Ingresa la dependencia.", parent=self.win)
            return

        observaciones = self.entry_observaciones.get().strip()

        for r in self.resultado:
            if r.cedula == cedula and r.dependencia == dependencia:
                messagebox.showwarning(
                    "Atención",
                    f"La cédula {cedula} ya fue agregada para {dependencia}.",
                    parent=self.win,
                )
                return

        entrada = EntradaCMPCustom(cedula=cedula, dependencia=dependencia, observaciones=observaciones)
        self.resultado.append(entrada)

        self.listbox.insert(tk.END, f"C.I. {cedula} | {dependencia}")

        self.entry_cedula.delete(0, tk.END)
        self.entry_dependencia.delete(0, tk.END)
        self.entry_observaciones.delete(0, tk.END)

    def _eliminar(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.listbox.delete(idx)
        self.resultado.pop(idx)

    # --- Importación masiva ---

    def _importar_desde_excel(self):
        ruta = filedialog.askopenfilename(
            title='Seleccionar Excel con cédulas y motivos',
            filetypes=[("Excel", "*.xlsx *.xls")],
            parent=self.win,
        )
        if not ruta:
            return

        try:
            xl = pd.ExcelFile(ruta)
            hojas = xl.sheet_names
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{ex}", parent=self.win)
            return

        if not hojas:
            messagebox.showwarning("Atención", "El archivo no tiene hojas.", parent=self.win)
            return

        # --- Paso 1: Seleccionar hoja ---
        hoja_sel = self._dialogo_seleccion_hoja(hojas)
        if hoja_sel is None:
            return

        try:
            df = pd.read_excel(ruta, sheet_name=hoja_sel, dtype=str)
            df = df.fillna('')
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo cargar la hoja:\n{ex}", parent=self.win)
            return

        if df.empty:
            messagebox.showwarning("Atención", "La hoja está vacía.", parent=self.win)
            return

        # --- Paso 2: Seleccionar columnas ---
        resultado_cols = self._dialogo_seleccion_columnas(df)
        if resultado_cols is None:
            return

        col_cedula, col_dependencia, col_observaciones = resultado_cols
        self._procesar_importacion(df, col_cedula, col_dependencia, col_observaciones)

    def _dialogo_seleccion_hoja(self, hojas: list[str]) -> Optional[str]:
        dlg = tk.Toplevel(self.win)
        dlg.title("Seleccionar hoja")
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.protocol("WM_DELETE_WINDOW", lambda: dlg.destroy())

        tk.Label(
            dlg,
            text="Elija la hoja que contiene las cédulas y motivos:",
            font=('Segoe UI', 10, 'bold'),
            padx=15, pady=10,
        ).pack()

        var_hoja = tk.StringVar(value=hojas[0])
        combo = ttk.Combobox(dlg, values=hojas, textvariable=var_hoja, state='readonly', width=35)
        combo.pack(padx=15, pady=5)

        resultado = [None]

        def aceptar():
            resultado[0] = var_hoja.get()
            dlg.destroy()

        tk.Button(dlg, text="Aceptar", command=aceptar, width=12).pack(pady=10)
        dlg.wait_window()
        return resultado[0]

    def _dialogo_seleccion_columnas(self, df: pd.DataFrame) -> Optional[tuple[str, str, str]]:
        columnas = list(df.columns)

        dlg = tk.Toplevel(self.win)
        dlg.title("Seleccionar columnas")
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.protocol("WM_DELETE_WINDOW", lambda: dlg.destroy())

        tk.Label(
            dlg,
            text="Identifique las columnas del archivo:",
            font=('Segoe UI', 10, 'bold'),
            padx=15, pady=10,
        ).pack()

        # Columna de cédulas
        frame_ced = tk.Frame(dlg)
        frame_ced.pack(fill='x', padx=15, pady=3)
        tk.Label(frame_ced, text="Columna de cédulas:", width=18, anchor='w').pack(side='left')
        var_cedula = tk.StringVar(value=columnas[0])
        ttk.Combobox(frame_ced, values=columnas, textvariable=var_cedula, state='readonly', width=30).pack(side='left', padx=5)

        # Columna de dependencia
        frame_dep = tk.Frame(dlg)
        frame_dep.pack(fill='x', padx=15, pady=3)
        tk.Label(frame_dep, text="Columna de dependencia:", width=18, anchor='w').pack(side='left')
        var_dependencia = tk.StringVar(value=columnas[1] if len(columnas) > 1 else columnas[0])
        ttk.Combobox(frame_dep, values=columnas, textvariable=var_dependencia, state='readonly', width=30).pack(side='left', padx=5)

        # Columna de observaciones
        frame_obs = tk.Frame(dlg)
        frame_obs.pack(fill='x', padx=15, pady=3)
        tk.Label(frame_obs, text="Columna de observaciones:", width=18, anchor='w').pack(side='left')
        var_observaciones = tk.StringVar(value=columnas[2] if len(columnas) > 2 else columnas[0])
        ttk.Combobox(frame_obs, values=columnas, textvariable=var_observaciones, state='readonly', width=30).pack(side='left', padx=5)

        # Vista previa
        preview_frame = tk.LabelFrame(dlg, text="Vista previa (primeras 5 filas)", padx=8, pady=5)
        preview_frame.pack(fill='x', padx=15, pady=8)

        preview_text = tk.Text(preview_frame, height=6, width=55, font=('Consolas', 9), state='disabled')
        preview_text.pack()

        def actualizar_preview(*_args):
            col_ced = var_cedula.get()
            col_dep = var_dependencia.get()
            col_obs = var_observaciones.get()
            preview_text.config(state='normal')
            preview_text.delete('1.0', tk.END)
            if not col_ced or not col_dep:
                preview_text.insert(tk.END, "Seleccione al menos cédula y dependencia.")
            else:
                total = len(df)
                preview_text.insert(tk.END, f"Total: {total} filas\n\n")
                for _, row in df.head(5).iterrows():
                    ced_val = str(row.get(col_ced, "")).strip()
                    dep_val = str(row.get(col_dep, "")).strip()
                    obs_val = str(row.get(col_obs, "")).strip() if col_obs else ""
                    preview_text.insert(tk.END, f"  {ced_val} | {dep_val} | {obs_val}\n")
            preview_text.config(state='disabled')

        var_cedula.trace_add('write', actualizar_preview)
        var_dependencia.trace_add('write', actualizar_preview)
        var_observaciones.trace_add('write', actualizar_preview)
        actualizar_preview()

        resultado = [None]

        def aceptar():
            ced = var_cedula.get()
            dep = var_dependencia.get()
            obs = var_observaciones.get()
            if not ced or not dep:
                messagebox.showwarning("Atención", "Seleccione al menos cédula y dependencia.", parent=dlg)
                return
            resultado[0] = (ced, dep, obs)
            dlg.destroy()

        tk.Button(dlg, text="Importar", command=aceptar, width=12, bg='#2196F3', fg='white').pack(pady=10)
        dlg.wait_window()
        return resultado[0]

    def _procesar_importacion(self, df: pd.DataFrame, col_cedula: str, col_dependencia: str, col_observaciones: str):
        cedulas_nuevas = 0
        cedulas_duplicadas = 0
        cedulas_vacias = 0

        cedulas_existentes = {(e.cedula, e.dependencia) for e in self.resultado}

        for _, row in df.iterrows():
            ced_val = str(row.get(col_cedula, "")).strip()
            dep_val = str(row.get(col_dependencia, "")).strip()
            obs_val = str(row.get(col_observaciones, "")).strip() if col_observaciones else ""

            if not ced_val or ced_val == 'nan':
                cedulas_vacias += 1
                continue

            if (ced_val, dep_val) in cedulas_existentes:
                cedulas_duplicadas += 1
                continue

            entrada = EntradaCMPCustom(cedula=ced_val, dependencia=dep_val, observaciones=obs_val)
            self.resultado.append(entrada)
            cedulas_existentes.add((ced_val, dep_val))
            cedulas_nuevas += 1

        self._refrescar_lista()

        partes = [f"Importadas: {cedulas_nuevas} cédula(s)"]
        if cedulas_duplicadas > 0:
            partes.append(f"{cedulas_duplicadas} duplicada(s) omitida(s)")
        if cedulas_vacias > 0:
            partes.append(f"{cedulas_vacias} fila(s) vacía(s) omitida(s)")

        messagebox.showinfo("Importación completada", " | ".join(partes), parent=self.win)

    def _refrescar_lista(self):
        self.listbox.delete(0, tk.END)
        for e in self.resultado:
            self.listbox.insert(tk.END, f"C.I. {e.cedula} | {e.dependencia}")

    # --- Finales ---

    def _procesar(self):
        if not self.resultado:
            messagebox.showwarning(
                "Atención", "No hay cédulas ingresadas.", parent=self.win
            )
            return
        self.win.destroy()

    def _omitir(self):
        self.resultado = []
        self.cancelado = True
        self.win.destroy()
