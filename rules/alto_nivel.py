from rules.base import ReglaBase
from models import Empleado


class ReglaAltoNivel(ReglaBase):

    def aplica(self, empleado, fila_datos, contexto):
        return 'ALTO NIVEL FIJO' in str(empleado.tipo_personal).upper()

    def ejecutar(self, empleado, fila_datos, contexto):
        reader = contexto['reader']
        cfg = contexto['config']
        monto_base = contexto['monto_base']

        # Nombres de columna vienen del JSON
        col_101 = cfg.columnas_reglas.sueldo_101
        col_117 = cfg.columnas_reglas.diferencia_117

        val_101 = float(reader.valor_celda(fila_datos, col_101, 0))

        if val_101 > 0:
            empleado.monto_cesta = monto_base
            empleado.observaciones = 'ENCARGADURÍA'
        else:
            empleado.monto_cesta = 0
            empleado.observaciones = ''

        return empleado