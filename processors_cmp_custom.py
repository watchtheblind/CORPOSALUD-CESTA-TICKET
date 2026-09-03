"""Procesador específico para la pestaña de CMP Custom.

Para cada cédula ingresada (manual o masiva), busca en el Libro de Carga la fila
que coincida con la cédula y su dependencia, setea el monto de cesta ticket en 0
y escribe la observación en la columna correspondiente.
Opera sobre la hoja ACTIVOS del template.
"""

from models import Empleado
from readers import ExcelReader
from config import CONFIG
from ui_cmp import EntradaCMPCustom
from base_processor import ProcesadorBase


class ProcesadorCMPCustom(ProcesadorBase):
    """Marca empleados con monto 0 y motivo en la hoja ACTIVOS."""

    def __init__(self, reader: ExcelReader, idx_plantilla: dict, **kwargs):
        super().__init__(reader, CONFIG, idx_plantilla)
        self.reader = reader
        self.idx_plantilla = idx_plantilla
        self.cfg = CONFIG

    def buscar_fila(self, cedula: str, dependencia: str, max_columnas: int = 150) -> list | None:
        """Busca una cédula + dependencia en el libro de carga."""
        col_dep = self.reader.obtener_indice('NOMBRE CENTRO')
        for r in range(self.reader.fila_inicio_datos, self.reader.total_filas + 1):
            fila = self.reader.leer_fila(r, max_columnas)

            if not self.reader.fila_tiene_cedula(fila):
                break

            valor_cedula = str(self.reader.valor_celda(fila, 'CEDULA', '')).strip()
            if valor_cedula != cedula:
                continue

            if col_dep is not None and col_dep < len(fila):
                valor_dep = str(fila[col_dep] or '').strip()
                if valor_dep.upper() == dependencia.upper():
                    return fila

        return None

    def procesar(self, fila_datos: list, entrada: EntradaCMPCustom, n_item: int, fila_excel: int) -> Empleado:
        emp = self._extraer_campos_directos(fila_datos, self.cfg.campos)
        emp.n_fila = n_item

        self._pre_procesar_comun(emp, fila_datos, self.cfg.campos)

        emp.monto_cesta = 0
        emp.observaciones = entrada.observaciones

        self._inyectar_formulas(emp, fila_excel)
        return emp

    def _inyectar_formulas(self, emp: Empleado, fila_excel: int):
        self._inyectar_formulas_comunes(emp, fila_excel)
