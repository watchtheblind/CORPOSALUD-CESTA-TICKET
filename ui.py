"""Interfaz gráfica. Solo captura datos del usuario, nada de lógica."""

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from typing import Optional
from dataclasses import dataclass


@dataclass
class EntradaUsuario:
    """Datos proporcionados por el usuario."""
    monto: float
    ruta_carga: str


class DialogoUI:
    """Gestiona la interacción con el usuario."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.attributes('-topmost', True)

    def solicitar_datos(self) -> Optional[EntradaUsuario]:
        """Pide monto y archivo al usuario. Retorna None si cancela."""
        monto = simpledialog.askfloat(
            'Monto', 'Monto Cesta:', minvalue=0.0, parent=self.root
        )
        if monto is None:
            return None

        ruta = filedialog.askopenfilename(
            title='Selecciona LIBRO CARGA', parent=self.root
        )
        if not ruta:
            return None

        return EntradaUsuario(monto=monto, ruta_carga=ruta)

    def mostrar_exito(self, registros: int):
        messagebox.showinfo(
            'Éxito', f'Se procesaron {registros} registros correctamente.'
        )

    def mostrar_error(self, mensaje: str):
        messagebox.showerror('Error', f'Error durante el proceso: {mensaje}')

    def cerrar(self):
        self.root.destroy()