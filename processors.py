"""Procesamiento de empleados. Lee configuración desde JSON."""

from models import Empleado
from readers import ExcelReader
from config import CONFIG
from formulas import formula_edad, formula_anos_servicio, formula_largo_cuenta
from rules import REGLAS_REGISTRADAS


class ProcesadorEmpleado:

    def __init__(self, reader: ExcelReader, idx_plantilla: dict, monto_base: float):
        self.reader = reader
        self.idx_plantilla = idx_plantilla
        self.monto_base = monto_base
        self.cfg = CONFIG  # Configuración cargada del JSON

    def procesar(
        self, fila_datos: list, n_item: int, fila_excel: int, fecha_corte: str
    ) -> Empleado:
        emp = self._extraer_campos_directos(fila_datos)
        emp.n_fila = n_item
        emp.monto_cesta = self.monto_base

        self._calcular_nombre(emp, fila_datos)
        self._calcular_nacionalidad(emp)
        self._calcular_horario(emp)
        self._calcular_especialidad(emp, fila_datos)
        self._inyectar_formulas(emp, fila_excel, fecha_corte)

        emp.estado_region = self.cfg.estado_region_default

        self._aplicar_reglas(emp, fila_datos)
        return emp

    def _extraer_campos_directos(self, fila_datos: list) -> Empleado:
        emp = Empleado()
        for campo in self.cfg.campos:                    # ← Del JSON
            if campo.origen is not None:
                valor = self.reader.valor_celda(fila_datos, campo.origen, '')
                setattr(emp, campo.clave, valor)
        return emp

    def _calcular_nombre(self, emp: Empleado, fila_datos: list):
        partes = []
        for col in self.cfg.columnas_nombre:             # ← Del JSON
            valor = self.reader.valor_celda(fila_datos, col)
            if valor:
                partes.append(str(valor).strip())
        emp.nombres_completos = ' '.join(partes).upper()

    def _calcular_nacionalidad(self, emp: Empleado):
        ced = str(emp.cedula).strip()
        emp.nac_calc = 'E' if ced.startswith('8') or ced == '604262' else 'V'

    def _calcular_horario(self, emp: Empleado):
        carga = str(emp.carga_horaria).strip()
        for clave, horario in self.cfg.horarios.items(): # ← Del JSON
            if clave in carga:
                emp.horario_laboral = horario
                return
        emp.horario_laboral = self.cfg.horario_default   # ← Del JSON

    def _calcular_especialidad(self, emp: Empleado, fila_datos: list):
        valor = self.reader.valor_celda(fila_datos, 'ESPECIALIDAD MÉD 1')
        emp.especialidad = valor if valor else ''

    def _inyectar_formulas(self, emp: Empleado, fila_excel: int, fecha_corte: str):
        col_nac = self.idx_plantilla.get('f_nac', 1)
        col_ing = self.idx_plantilla.get('f_ingre', 1)
        col_cuenta = self.idx_plantilla.get('cuenta', 1)

        emp.edad = formula_edad(col_nac, fila_excel, fecha_corte)
        emp.anos_servicio = formula_anos_servicio(col_ing, fila_excel, fecha_corte)
        emp.largo_cuenta = formula_largo_cuenta(col_cuenta, fila_excel)

    def _aplicar_reglas(self, emp: Empleado, fila_datos: list):
        contexto = {
            'reader': self.reader,
            'monto_base': self.monto_base,
            'config': self.cfg,                          # ← Reglas acceden al JSON
        }
        for regla in REGLAS_REGISTRADAS:
            if regla.aplica(emp, fila_datos, contexto):
                regla.ejecutar(emp, fila_datos, contexto)