"""Responsabilidad única: escribir datos en la plantilla Excel."""

from datetime import datetime
from models import Empleado
from readers import limpiar_texto


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

    def escribir_retroactivos(
        self, empleado: Empleado, fila: int,
        meses_abreviados: dict[str, str], anio: str,
    ):
        """Escribe los montos en las columnas de retroactivo correspondientes."""
        for mes, monto in empleado.retroactivos.items():
            col = self._buscar_columna_retroactivo(mes, meses_abreviados, anio)
            if col is not None:
                self.ws.cell(row=fila, column=col, value=monto)

    def _buscar_columna_retroactivo(
        self, mes: str, meses_abreviados: dict[str, str], anio: str,
    ) -> int | None:
        """Encuentra la columna de la plantilla para un mes de retroactivo."""
        nombre_mes = meses_abreviados.get(mes, '').upper()
        # Busca en las primeras filas (cabeceras) de la hoja
        for r in range(1, 6):
            for c in range(1, 30):
                val = self.ws.cell(r, c).value
                if val is None:
                    continue
                val_limpio = str(val).upper()
                if nombre_mes in val_limpio and anio in val_limpio:
                    return c
        return None

    @staticmethod
    def generar_nombre_salida() -> str:
        """Genera nombre de archivo con timestamp."""
        ts = datetime.now().strftime('%H_%M_%S')
        return f'REPORTE_COMPLETO_{ts}.xlsx'