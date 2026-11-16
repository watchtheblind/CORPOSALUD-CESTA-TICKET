"""Comparador de columnas entre dos archivos Excel o CSV.

Ejecutar:
    python comparar_columnas.py

Permite elegir libremente dos archivos (A y B), la hoja, la fila de encabezado
y la columna a comparar de cada uno. Genera un .txt con:

  - los valores que están en A pero NO están en B
  - los valores que están en B pero NO están en A

La comparación ignora espacios al inicio/fin y valores vacíos. Los números se
normalizan (por ejemplo, 123 y 123.0 se consideran el mismo valor).
"""

import os
import re
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd


EXT_EXCEL = ('.xlsx', '.xlsm', '.xltx', '.xltm', '.xls')
ENCODINGS = ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252')


# ---------------------------------------------------------------------------
# Lectura de archivos
# ---------------------------------------------------------------------------

def es_excel(ruta: str) -> bool:
    return ruta.lower().endswith(EXT_EXCEL)


def limpiar_valor(valor) -> str:
    """Convierte un valor de celda a texto comparable."""
    if valor is None:
        return ''
    try:
        if pd.isna(valor):
            return ''
    except (TypeError, ValueError):
        pass
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    texto = str(valor).strip()
    # Excel/CSV a veces leen los enteros como "123.0"
    if re.fullmatch(r'-?\d+\.0', texto):
        texto = texto[:-2]
    return texto


def leer_csv(ruta: str, header, nrows=None) -> pd.DataFrame:
    """Lee un CSV probando varias codificaciones y autodetectando separador."""
    ultimo_error = None
    for enc in ENCODINGS:
        try:
            return pd.read_csv(
                ruta,
                header=header,
                dtype=object,
                nrows=nrows,
                sep=None,
                engine='python',
                encoding=enc,
                on_bad_lines='skip',
            )
        except Exception as ex:  # probamos con la siguiente codificación
            ultimo_error = ex
    raise ultimo_error


def leer_dataframe(ruta: str, hoja, header: int, nrows=None) -> pd.DataFrame:
    if es_excel(ruta):
        return pd.read_excel(
            ruta, sheet_name=hoja, header=header, dtype=object, nrows=nrows
        )
    return leer_csv(ruta, header=header, nrows=nrows)


def detectar_fila_encabezado(ruta: str, hoja) -> int:
    """Devuelve (1-based) la fila con más celdas no vacías en las primeras filas.

    Sirve para archivos donde la cabecera no está en la fila 1. Si falla,
    devuelve 1.
    """
    try:
        df = leer_dataframe(ruta, hoja, header=None, nrows=20)
        mejor, mejor_conteo = 0, -1
        for i in range(len(df)):
            conteo = sum(1 for v in df.iloc[i] if limpiar_valor(v) != '')
            if conteo > mejor_conteo:
                mejor, mejor_conteo = i, conteo
        return mejor + 1
    except Exception:
        return 1


def clave_orden(texto: str):
    """Ordena números numéricamente y el resto alfabéticamente."""
    try:
        return (0, float(texto), '')
    except ValueError:
        return (1, 0.0, texto.upper())


# ---------------------------------------------------------------------------
# Panel para un archivo (A o B)
# ---------------------------------------------------------------------------

class Lado:
    def __init__(self, parent, titulo: str):
        self.ruta = None
        self.hojas = []
        self.columnas = []

        self.frame = tk.LabelFrame(parent, text=titulo, padx=8, pady=8)

        # Archivo
        fila = tk.Frame(self.frame)
        fila.pack(fill='x', pady=2)
        tk.Label(fila, text='Archivo:', width=12, anchor='w').pack(side='left')
        self.var_ruta = tk.StringVar()
        tk.Entry(fila, textvariable=self.var_ruta, state='readonly').pack(
            side='left', fill='x', expand=True, padx=4
        )
        tk.Button(fila, text='Seleccionar...', command=self.seleccionar).pack(side='left')

        # Hoja
        fila = tk.Frame(self.frame)
        fila.pack(fill='x', pady=2)
        tk.Label(fila, text='Hoja:', width=12, anchor='w').pack(side='left')
        self.var_hoja = tk.StringVar()
        self.cmb_hoja = ttk.Combobox(
            fila, textvariable=self.var_hoja, state='disabled', width=32
        )
        self.cmb_hoja.pack(side='left', padx=4)
        self.cmb_hoja.bind('<<ComboboxSelected>>', self._cambiar_hoja)

        # Fila de encabezado
        fila = tk.Frame(self.frame)
        fila.pack(fill='x', pady=2)
        tk.Label(fila, text='Fila encabezado:', width=12, anchor='w').pack(side='left')
        self.var_header = tk.IntVar(value=1)
        self.spn_header = tk.Spinbox(
            fila, from_=1, to=100, textvariable=self.var_header,
            width=6, command=self.cargar_columnas,
        )
        self.spn_header.pack(side='left', padx=4)
        self.spn_header.bind('<Return>', lambda e: self.cargar_columnas())
        self.spn_header.bind('<FocusOut>', lambda e: self.cargar_columnas())
        tk.Label(
            fila, text='(cámbiala si la cabecera no está en la fila 1)',
            fg='#777777',
        ).pack(side='left', padx=4)

        # Columna
        fila = tk.Frame(self.frame)
        fila.pack(fill='x', pady=2)
        tk.Label(fila, text='Columna:', width=12, anchor='w').pack(side='left')
        self.var_col = tk.StringVar()
        self.cmb_col = ttk.Combobox(
            fila, textvariable=self.var_col, state='readonly', width=32
        )
        self.cmb_col.pack(side='left', padx=4)

    # -- acciones ----------------------------------------------------------

    def seleccionar(self):
        ruta = filedialog.askopenfilename(
            title='Seleccionar archivo',
            filetypes=[
                ('Excel o CSV', '*.xlsx *.xlsm *.xls *.csv *.txt'),
                ('Todos los archivos', '*.*'),
            ],
            parent=self.frame.winfo_toplevel(),
        )
        if not ruta:
            return

        self.ruta = ruta
        self.var_ruta.set(ruta)

        if es_excel(ruta):
            try:
                self.hojas = pd.ExcelFile(ruta).sheet_names
            except Exception as ex:
                self.hojas = []
                messagebox.showerror(
                    'Error', f'No se pudo abrir el archivo:\n{ex}',
                    parent=self.frame.winfo_toplevel(),
                )
                return
            self.cmb_hoja.config(state='readonly')
            self.cmb_hoja['values'] = self.hojas
            if self.var_hoja.get() not in self.hojas:
                self.var_hoja.set(self.hojas[0] if self.hojas else '')
        else:
            self.hojas = []
            self.cmb_hoja['values'] = ['(CSV)']
            self.var_hoja.set('(CSV)')
            self.cmb_hoja.config(state='disabled')

        self._auto_header()
        self.cargar_columnas()

    def _cambiar_hoja(self, _evento=None):
        self._auto_header()
        self.cargar_columnas()

    def _auto_header(self):
        if not self.ruta:
            return
        hoja = self.var_hoja.get() if es_excel(self.ruta) else None
        self.var_header.set(detectar_fila_encabezado(self.ruta, hoja))

    def cargar_columnas(self):
        if not self.ruta:
            return

        try:
            header = max(0, int(self.var_header.get()) - 1)
        except (tk.TclError, ValueError):
            header = 0

        hoja = self.var_hoja.get() if es_excel(self.ruta) else None

        try:
            df = leer_dataframe(self.ruta, hoja, header=header, nrows=5)
        except Exception as ex:
            self.columnas = []
            self.cmb_col['values'] = []
            self.var_col.set('')
            messagebox.showerror(
                'Error',
                f'No se pudieron leer las columnas:\n{ex}',
                parent=self.frame.winfo_toplevel(),
            )
            return

        self.columnas = [str(c) for c in df.columns]
        self.cmb_col['values'] = [
            f'{i + 1}. {nombre}' for i, nombre in enumerate(self.columnas)
        ]
        if self.cmb_col.current() < 0 and self.columnas:
            self.cmb_col.current(0)

    def nombre_columna(self) -> str:
        idx = self.cmb_col.current()
        if 0 <= idx < len(self.columnas):
            return self.columnas[idx]
        return self.var_col.get()

    def leer_columna(self) -> pd.Series:
        if not self.ruta:
            raise ValueError('Falta seleccionar el archivo.')
        idx = self.cmb_col.current()
        if idx < 0 or not self.columnas:
            raise ValueError('Falta seleccionar la columna.')

        try:
            header = max(0, int(self.var_header.get()) - 1)
        except (tk.TclError, ValueError):
            header = 0

        hoja = self.var_hoja.get() if es_excel(self.ruta) else None
        df = leer_dataframe(self.ruta, hoja, header=header)

        if idx >= df.shape[1]:
            raise ValueError(
                'La columna seleccionada ya no existe. Vuelve a cargar el archivo.'
            )
        return df.iloc[:, idx]


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------

class ComparadorApp:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title('Comparador de columnas - Excel / CSV')
        self.win.geometry('780x460')
        self.win.minsize(720, 430)

        tk.Label(
            self.win,
            text='Compara una columna del Archivo A con una del Archivo B',
            font=('Segoe UI', 12, 'bold'),
            pady=10,
        ).pack()

        contenedor = tk.Frame(self.win)
        contenedor.pack(fill='both', expand=True, padx=14, pady=4)

        self.lado_a = Lado(contenedor, 'Archivo A')
        self.lado_a.frame.pack(fill='x', pady=5)

        self.lado_b = Lado(contenedor, 'Archivo B')
        self.lado_b.frame.pack(fill='x', pady=5)

        tk.Label(
            self.win,
            text='Se ignoran celdas vacías y espacios. Los números 123 y 123.0 se tratan igual.',
            fg='#777777',
        ).pack(pady=(6, 0))

        tk.Button(
            self.win,
            text='Comparar y generar TXT',
            command=self.comparar,
            bg='#2196F3',
            fg='white',
            width=28,
            height=2,
        ).pack(pady=12)

        self.win.mainloop()

    def comparar(self):
        try:
            serie_a = self.lado_a.leer_columna()
            serie_b = self.lado_b.leer_columna()
        except Exception as ex:
            messagebox.showerror(
                'Error', f'No se pudieron leer las columnas:\n{ex}', parent=self.win
            )
            return

        valores_a = [v for v in (limpiar_valor(x) for x in serie_a) if v]
        valores_b = [v for v in (limpiar_valor(x) for x in serie_b) if v]

        if not valores_a and not valores_b:
            messagebox.showwarning(
                'Sin datos',
                'Las columnas seleccionadas están vacías.',
                parent=self.win,
            )
            return

        set_a, set_b = set(valores_a), set(valores_b)
        solo_a = sorted(set_a - set_b, key=clave_orden)
        solo_b = sorted(set_b - set_a, key=clave_orden)
        coincidencias = len(set_a & set_b)

        contenido = self._generar_reporte(
            valores_a, valores_b, set_a, set_b, solo_a, solo_b, coincidencias
        )

        ruta_salida = filedialog.asksaveasfilename(
            parent=self.win,
            title='Guardar reporte de comparación',
            defaultextension='.txt',
            initialfile=f'comparacion_columnas_{datetime.now():%Y%m%d_%H%M%S}.txt',
            filetypes=[('Archivo de texto', '*.txt')],
        )
        if not ruta_salida:
            return

        try:
            with open(ruta_salida, 'w', encoding='utf-8-sig') as f:
                f.write(contenido)
        except Exception as ex:
            messagebox.showerror(
                'Error', f'No se pudo guardar el TXT:\n{ex}', parent=self.win
            )
            return

        resumen = (
            f'Reporte generado:\n{ruta_salida}\n\n'
            f'Solo en A (faltan en B): {len(solo_a)}\n'
            f'Solo en B (faltan en A): {len(solo_b)}\n'
            f'Coincidencias: {coincidencias}'
        )
        messagebox.showinfo('Comparación terminada', resumen, parent=self.win)

        try:
            os.startfile(ruta_salida)
        except Exception:
            pass

    def _generar_reporte(
        self, valores_a, valores_b, set_a, set_b, solo_a, solo_b, coincidencias
    ) -> str:
        a, b = self.lado_a, self.lado_b
        lineas = []
        lineas.append('COMPARACIÓN DE COLUMNAS')
        lineas.append('=' * 62)
        lineas.append(f'Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}')
        lineas.append('')
        lineas.append(f'A) Archivo : {a.ruta}')
        lineas.append(f'   Hoja    : {a.var_hoja.get()}')
        lineas.append(f'   Encabez.: fila {a.var_header.get()}')
        lineas.append(f'   Columna : {a.nombre_columna()}')
        lineas.append('')
        lineas.append(f'B) Archivo : {b.ruta}')
        lineas.append(f'   Hoja    : {b.var_hoja.get()}')
        lineas.append(f'   Encabez.: fila {b.var_header.get()}')
        lineas.append(f'   Columna : {b.nombre_columna()}')
        lineas.append('')
        lineas.append('RESUMEN')
        lineas.append(f'  Valores no vacíos en A : {len(valores_a)} (únicos: {len(set_a)})')
        lineas.append(f'  Valores no vacíos en B : {len(valores_b)} (únicos: {len(set_b)})')
        lineas.append(f'  Coincidencias          : {coincidencias}')
        lineas.append(f'  Solo en A (faltan en B): {len(solo_a)}')
        lineas.append(f'  Solo en B (faltan en A): {len(solo_b)}')
        lineas.append('')

        lineas.append(f'=== VALORES EN A QUE NO ESTÁN EN B ({len(solo_a)}) ===')
        if solo_a:
            lineas.extend(f'  {v}' for v in solo_a)
        else:
            lineas.append('  (ninguno)')
        lineas.append('')

        lineas.append(f'=== VALORES EN B QUE NO ESTÁN EN A ({len(solo_b)}) ===')
        if solo_b:
            lineas.extend(f'  {v}' for v in solo_b)
        else:
            lineas.append('  (ninguno)')
        lineas.append('')

        return '\n'.join(lineas)


if __name__ == '__main__':
    ComparadorApp()
