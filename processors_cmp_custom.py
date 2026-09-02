"""Procesador específico para la pestaña de CMP Custom.

Para cada cédula ingresada (manual o masiva), busca la fila en el Libro de Carga,
setea el monto de cesta ticket en 0 y escribe el motivo en la columna correspondiente.
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

    def buscar_fila_por_cedula(self, cedula: str, max_columnas: int = 150) -> list | None:
        """Busca una cédula en el libro de carga y devuelve su fila."""
        for r in range(self.reader.fila_inicio_datos, self.reader.total_filas + 1):
            fila = self.reader.leer_fila(r, max_columnas)

            if not self.reader.fila_tiene_cedula(fila):
                break

            valor_cedula = str(self.reader.valor_celda(fila, 'CEDULA', '')).strip()
            if valor_cedula == cedula:
                return fila

        return None

    def procesar(self, fila_datos: list, entrada: EntradaCMPCustom, n_item: int, fila_excel: int) -> Empleado:
        emp = self._extraer_campos_directos(fila_datos, self.cfg.campos)
        emp.n_fila = n_item

        self._pre_procesar_comun(emp, fila_datos, self.cfg.campos)

        # Lo específico de CMP Custom:
        emp.monto_cesta = 0              # columna R → 0
        emp.motivo_cmp = entrada.motivo  # columna U → motivo

        self._inyectar_formulas(emp, fila_excel)
        return emp
