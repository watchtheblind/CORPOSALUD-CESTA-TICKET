"""Procesador específico para la pestaña de Retroactivos."""

from models import Empleado
from readers import ExcelReader
from config import CONFIG
from formulas import formula_largo_cuenta
from montos import GestorMontos
from ui_retroactivos import EntradaRetroactivo


class ProcesadorRetroactivo:
    """Transforma datos de activos + entrada de retroactivo en Empleado."""

    def __init__(self, reader: ExcelReader, idx_plantilla: dict, gestor_montos: GestorMontos):
        self.reader = reader
        self.idx_plantilla = idx_plantilla
        self.gestor = gestor_montos
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

    def procesar(
        self,
        fila_datos: list,
        entrada: EntradaRetroactivo,
        n_item: int,
        fila_excel: int,
        anio: str,
    ) -> Empleado:
        """Pipeline: extracción → transformaciones → montos retroactivos."""
        emp = self._extraer_campos_directos(fila_datos)
        emp.n_fila = n_item

        self._calcular_nombre(emp, fila_datos)
        self._calcular_nacionalidad(emp)
        self._calcular_horario(emp)
        self._calcular_especialidad(emp, fila_datos)
        self._asignar_retroactivos(emp, entrada, anio)
        self._inyectar_formulas(emp, fila_excel)

        emp.estado_region = self.cfg.estado_region_default
        emp.motivo_retroactivo = entrada.motivo

        return emp

    def _extraer_campos_directos(self, fila_datos: list) -> Empleado:
        """Extrae campos con mapeo directo desde el libro carga."""
        emp = Empleado()
        for campo in self.cfg.campos_retroactivo:
            if campo.origen is not None:
                valor = self.reader.valor_celda(fila_datos, campo.origen, '')
                setattr(emp, campo.clave, valor)
        return emp

    def _calcular_nombre(self, emp: Empleado, fila_datos: list):
        partes = []
        for col in self.cfg.columnas_nombre:
            valor = self.reader.valor_celda(fila_datos, col)
            if valor:
                partes.append(str(valor).strip())
        emp.nombres_completos = ' '.join(partes).upper()

    def _calcular_nacionalidad(self, emp: Empleado):
        ced = str(emp.cedula).strip()
        emp.nac_calc = 'E' if ced.startswith('8') or ced == '604262' else 'V'

    def _calcular_horario(self, emp: Empleado):
        carga = str(emp.carga_horaria).strip()
        for clave, horario in self.cfg.horarios.items():
            if clave in carga:
                emp.horario_laboral = horario
                return
        emp.horario_laboral = self.cfg.horario_default

    def _calcular_especialidad(self, emp: Empleado, fila_datos: list):
        valor = self.reader.valor_celda(fila_datos, 'ESPECIALIDAD MÉD 1')
        emp.especialidad = valor if valor else ''

    def _asignar_retroactivos(self, emp: Empleado, entrada: EntradaRetroactivo, anio: str):
        """Asigna los montos del retroactivo según los meses seleccionados."""
        for mes in entrada.meses:
            monto = self.gestor.obtener_monto(anio, mes)
            if monto is not None:
                emp.retroactivos[mes] = monto

    def _inyectar_formulas(self, emp: Empleado, fila_excel: int):
        """Genera fórmula de largo de cuenta. El total lo calcula el writer."""
        col_cuenta = self.idx_plantilla.get('cuenta', 1)
        emp.largo_cuenta = formula_largo_cuenta(col_cuenta, fila_excel)