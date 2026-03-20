"""Procesamiento de empleados. Lee configuración desde JSON."""

from models import Empleado
from readers import ExcelReader
from config import CONFIG
from formulas import formula_edad, formula_anos_servicio
from rules import REGLAS_REGISTRADAS
from base_processor import ProcesadorBase

class ProcesadorEmpleado(ProcesadorBase):
    def __init__(self, reader: ExcelReader, idx_plantilla: dict, monto_base: float):
        self.reader = reader
        self.idx_plantilla = idx_plantilla
        self.monto_base = monto_base
        self.cfg = CONFIG  # Configuración cargada del JSON

    def procesar(
        self, fila_datos: list, n_item: int, fila_excel: int, fecha_corte: str
    ) -> Empleado:
        emp = self._extraer_campos_directos(fila_datos, self.cfg.campos)
        emp.n_fila = n_item
        emp.monto_cesta = self.monto_base

        # 1. Obtenemos el valor del Excel (que trae las comillas '')
        cuenta_cruda = self.reader.valor_celda(fila_datos, 'CUENTA BANCARIA')
        
        # 2. Lo pasamos por el limpiador del padre y lo asignamos
        emp.cuenta_bancaria = self.limpiar_cuenta_bancaria(cuenta_cruda)
        # --- AQUÍ ES DONDE USAS LAS VARIABLES LIMPIAS ---
        # Asignamos los valores procesados a los atributos del objeto 'emp'
        emp.cuenta_bancaria = cuenta_limpia
        self._calcular_nombre(emp, fila_datos)
        self._calcular_nacionalidad(emp)
        self._calcular_horario(emp)
        self._calcular_especialidad(emp, fila_datos)
        self._inyectar_formulas(emp, fila_excel, fecha_corte)

        emp.estado_region = self.cfg.estado_region_default
        # 1. Obtienes la cuenta cruda del reader
        self._aplicar_reglas(emp, fila_datos)
        return emp

    def _inyectar_formulas(self, emp: Empleado, fila_excel: int, fecha_corte: str):
        # 1. Ejecutamos la lógica común (largo de cuenta)
        self._inyectar_formulas_comunes(emp, fila_excel)
        
        # 2. Añadimos lo específico de Activos
        col_nac = self.idx_plantilla.get('f_nac', 1)
        col_ing = self.idx_plantilla.get('f_ingre', 1)

        emp.edad = formula_edad(col_nac, fila_excel, fecha_corte)
        emp.anos_servicio = formula_anos_servicio(col_ing, fila_excel, fecha_corte)

    def _aplicar_reglas(self, emp: Empleado, fila_datos: list):
        contexto = {
            'reader': self.reader,
            'monto_base': self.monto_base,
            'config': self.cfg,                          # ← Reglas acceden al JSON
        }
        for regla in REGLAS_REGISTRADAS:
            if regla.aplica(emp, fila_datos, contexto):
                regla.ejecutar(emp, fila_datos, contexto)