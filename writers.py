"""Responsabilidad única: escribir datos en la plantilla Excel."""

from datetime import datetime
from openpyxl import Workbook

from models import Empleado


class PlantillaWriter:
    """Escribe empleados procesados en la plantilla destino."""

    def __init__(self, ws, idx_plantilla: dict):
        self.ws = ws
        self.idx_plantilla = idx_plantilla

    def escribir_empleado(self, empleado: Empleado, fila: int):
        """Escribe un empleado en la fila indicada."""
        datos = empleado.to_dict()
        for clave, col_idx in self.idx_plantilla.items():
            if clave in datos:
                self.ws.cell(row=fila, column=col_idx, value=datos[clave])

    @staticmethod
    def generar_nombre_salida() -> str:
        """Genera nombre de archivo con timestamp."""
        ts = datetime.now().strftime('%H_%M_%S')
        return f'REPORTE_COMPLETO_{ts}.xlsx'