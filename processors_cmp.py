"""Procesador específico para la pestaña CMP (Cambio de Modalidad de Pago)."""

from models import Empleado
from readers import ExcelReader
from config import CONFIG
from formulas import formula_largo_cuenta


class ProcesadorCMP:
    """Transforma una fila del libro carga en un Empleado para la pestaña CMP."""

    def __init__(self, reader: ExcelReader, idx_plantilla: dict):
        self.reader = reader
        self.idx_plantilla = idx_plantilla
        self.cfg = CONFIG

    def procesar(self, fila_datos: list, n_item: int, fila_excel: int) -> Empleado:
        """Pipeline: extracción → transformaciones → motivo CMP."""
        emp = self._extraer_campos_directos(fila_datos)
        emp.n_fila = n_item

        self._calcular_nombre(emp, fila_datos)
        self._calcular_nacionalidad(emp)
        self._calcular_horario(emp)
        self._calcular_especialidad(emp, fila_datos)
        self._calcular_motivo_cmp(emp)
        self._extraer_fecha_cmp(emp, fila_datos)
        self._inyectar_formulas(emp, fila_excel)

        emp.estado_region = self.cfg.estado_region_default

        return emp

    def _extraer_campos_directos(self, fila_datos: list) -> Empleado:
        """Extrae campos que tienen mapeo directo origen → destino."""
        emp = Empleado()
        for campo in self.cfg.campos_cmp:
            if campo.origen is not None:
                valor = self.reader.valor_celda(fila_datos, campo.origen, '')
                setattr(emp, campo.clave, valor)
        return emp

    def _calcular_nombre(self, emp: Empleado, fila_datos: list):
        """Construye nombre completo a partir de las 4 columnas."""
        partes = []
        for col in self.cfg.columnas_nombre:
            valor = self.reader.valor_celda(fila_datos, col)
            if valor:
                partes.append(str(valor).strip())
        emp.nombres_completos = ' '.join(partes).upper()

    def _calcular_nacionalidad(self, emp: Empleado):
        """Determina nacionalidad según patrón de cédula."""
        ced = str(emp.cedula).strip()
        emp.nac_calc = 'E' if ced.startswith('8') or ced == '604262' else 'V'

    def _calcular_horario(self, emp: Empleado):
        """Deduce horario laboral de la carga horaria."""
        carga = str(emp.carga_horaria).strip()
        for clave, horario in self.cfg.horarios.items():
            if clave in carga:
                emp.horario_laboral = horario
                return
        emp.horario_laboral = self.cfg.horario_default

    def _calcular_especialidad(self, emp: Empleado, fila_datos: list):
        """Extrae especialidad médica si existe."""
        valor = self.reader.valor_celda(fila_datos, 'ESPECIALIDAD MÉD 1')
        emp.especialidad = valor if valor else ''

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
        valor = self.reader.valor_celda(fila_datos, 'FECHA INACTIVACIÓN', '')
        emp.fecha_cmp = valor

    def _inyectar_formulas(self, emp: Empleado, fila_excel: int):
        """Genera fórmula de largo de cuenta."""
        col_cuenta = self.idx_plantilla.get('cuenta', 1)
        emp.largo_cuenta = formula_largo_cuenta(col_cuenta, fila_excel)