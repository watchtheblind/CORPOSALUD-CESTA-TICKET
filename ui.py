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
        """Pide monto Y archivo. Para cuando se necesitan ambos."""
        monto = simpledialog.askfloat(
            'Monto', 'Monto Cesta Ticket del mes:', minvalue=0.0, parent=self.root
        )
        if monto is None:
            return None

        ruta = filedialog.askopenfilename(
            title='Selecciona LIBRO CARGA', parent=self.root
        )
        if not ruta:
            return None

        return EntradaUsuario(monto=monto, ruta_carga=ruta)

    def solicitar_archivo(self) -> Optional[str]:
        """Pide solo el archivo de carga."""
        ruta = filedialog.askopenfilename(
            title='Selecciona LIBRO CARGA', parent=self.root
        )
        return ruta if ruta else None

    def verificar_monto_mes_actual(
        self, mes_nombre: str, anio: str, monto_actual: float
    ) -> Optional[float]:
        """
        Monto ya existe: pregunta mantener o cambiar.
        SÍ = cambiar, NO = mantener, X = cancelar todo.
        """
        respuesta = messagebox.askyesnocancel(
            'Monto del mes actual',
            f'El monto de cesta ticket para {mes_nombre}/{anio} '
            f'ya está registrado como {monto_actual} Bs.\n\n'
            f'¿Deseas cambiarlo?\n\n'
            f'SÍ = Ingresar nuevo monto\n'
            f'NO = Mantener {monto_actual} Bs.',
            parent=self.root,
        )

        if respuesta is None:
            return None

        if respuesta:
            nuevo = simpledialog.askfloat(
                'Nuevo monto',
                f'Ingresa el nuevo monto para {mes_nombre}/{anio}:',
                minvalue=0.0,
                parent=self.root,
            )
            return nuevo

        return monto_actual

    def solicitar_monto_mes_nuevo(self, mes_nombre: str, anio: str) -> Optional[float]:
        """Mes actual no tiene monto. Pide ingresarlo."""
        return simpledialog.askfloat(
            'Monto no registrado',
            f'No hay monto de cesta ticket para {mes_nombre}/{anio}.\n'
            f'Ingresa el monto:',
            minvalue=0.0,
            parent=self.root,
        )

    def mostrar_exito(self, registros: int):
        messagebox.showinfo(
            'Éxito', f'Se procesaron {registros} registros correctamente.'
        )

    def mostrar_exito_detallado(self, resumen: str):
        messagebox.showinfo('Proceso Completado', resumen)

    def mostrar_error(self, mensaje: str):
        messagebox.showerror('Error', f'Error durante el proceso: {mensaje}')

    def cerrar(self):
        self.root.destroy()