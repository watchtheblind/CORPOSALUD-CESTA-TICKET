"""Procesador específico para la pestaña CMP (Cambio de Modalidad de Pago)."""

from models import Empleado
from readers import ExcelReader
from config import CONFIG
from formulas import formula_largo_cuenta
from base_processor import ProcesadorBase

class ProcesadorCMP(ProcesadorBase):
    """Transforma una fila del libro carga en un Empleado para la pestaña CMP."""

    def __init__(self, reader: ExcelReader, idx_plantilla: dict):
        self.reader = reader
        self.idx_plantilla = idx_plantilla
        self.cfg = CONFIG

    def procesar(self, fila_datos: list, n_item: int, fila_excel: int) -> Empleado:

        # 1. Creación del objeto Empleado (Extracción directa)
        emp = self._extraer_campos_directos(fila_datos, self.cfg.campos_cmp)
        emp.n_fila = n_item

        # 2. Limpieza de Cuenta
        cuenta_cruda = self.reader.valor_celda(fila_datos, self.cfg.columna_cuenta_bancaria)
        cuenta_limpia = self.limpiar_cuenta_bancaria(cuenta_cruda)
        
        # 3. Limpieza de Fecha
        fecha_cruda = self.reader.valor_celda(fila_datos, 'FECHA DESDE CUANDO ESTAN EN CAMBIO DE MODALIDAD DE PAGO')
        fecha_limpia = self.formatear_fecha(fecha_cruda)

        # --- AQUÍ ES DONDE USAS LAS VARIABLES LIMPIAS ---
        # Asignamos los valores procesados a los atributos del objeto 'emp'
        emp.cuenta_bancaria = cuenta_limpia
        emp.fecha_cambio_modalidad = fecha_limpia 
        # (Asegúrate de que estos nombres de atributos existan en tu clase Empleado)

        # 4. Resto de cálculos del Pipeline
        self._calcular_nombre(emp, fila_datos)
        self._calcular_nacionalidad(emp)
        self._calcular_horario(emp)
        self._calcular_especialidad(emp, fila_datos)
        self._calcular_motivo_cmp(emp)
        
        # OJO AQUÍ: 
        # Si ya limpiamos la fecha arriba, quizás quieras comentar o 
        # modificar 'self._extraer_fecha_cmp(emp, fila_datos)' 
        # para que no te sobrescriba la fecha limpia con la sucia otra vez.
        
        self._inyectar_formulas(emp, fila_excel)

        emp.estado_region = self.cfg.estado_region_default

        return emp

    def _calcular_motivo_cmp(self, emp: Empleado):
        """
        Determina el motivo del CMP según tipo de personal.
        
        - Alto Nivel Fijo → "CARGO COMO OBRERO/CONTRATADO"
        - Todos los demás  → "AUSENCIA LABORAL"
        """
        tipo = str(emp.tipo_personal).upper()
        motivos = self.cfg.motivos_cmp

        for clave_tipo, motivo in motivos.items():
            if clave_tipo != 'default' and clave_tipo.upper() in tipo:
                emp.motivo_cmp = motivo
                return

        emp.motivo_cmp = motivos.get('default', 'AUSENCIA LABORAL')

    def _extraer_fecha_cmp(self, emp: Empleado, fila_datos: list):
        """Extrae la fecha de inactivación del libro carga."""
        col_fecha = next(c.origen for c in self.cfg.campos_cmp if c.clave == 'fecha_cmp')
        valor_sucio = self.reader.valor_celda(fila_datos, col_fecha, '')
        #valor = self.reader.valor_celda(fila_datos, 'FECHA INACTIVACIÓN', '')
        emp.fecha_cmp = valor

    def _inyectar_formulas(self, emp: Empleado, fila_excel: int):
        self._inyectar_formulas_comunes(emp, fila_excel)