"""Procesador específico para la pestaña de Retroactivos."""

from models import Empleado
from readers import ExcelReader
from config import CONFIG
from formulas import formula_largo_cuenta
from montos import GestorMontos
from ui_retroactivos import EntradaRetroactivo
from base_processor import ProcesadorBase

class ProcesadorRetroactivo(ProcesadorBase):
    """Transforma datos de activos + entrada de retroactivo en Empleado."""

    def __init__(self, reader: ExcelReader, idx_plantilla: dict, gestor_montos: GestorMontos, anio=None, **kwargs):        
        super().__init__(reader, CONFIG, idx_plantilla)
        self.reader = reader
        self.idx_plantilla = idx_plantilla
        self.gestor = gestor_montos
        self.anio = anio
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

    def procesar(self, fila_datos: list, entrada: EntradaRetroactivo, n_item: int, fila_excel: int, anio: str) -> Empleado:
        emp = self._extraer_campos_directos(fila_datos, self.cfg.campos_retroactivo)
        emp.n_fila = n_item

        # Llamamos al método maestro del padre
        self._pre_procesar_comun(emp, fila_datos, self.cfg.campos_retroactivo)

        # Lo específico de Retroactivo
        self._asignar_retroactivos(emp, entrada, anio)
        self._inyectar_formulas(emp, fila_excel)
        emp.motivo_retroactivo = entrada.motivo
        return emp

    def _asignar_retroactivos(self, emp: Empleado, entrada: EntradaRetroactivo, anio: str):
        """Asigna los montos del retroactivo según los meses seleccionados."""
        for mes in entrada.meses:
            monto = self.gestor.obtener_monto(anio, mes)
            if monto is not None:
                emp.retroactivos[mes] = monto

    def _inyectar_formulas(self, emp: Empleado, fila_excel: int):
        self._inyectar_formulas_comunes(emp, fila_excel)