from rules.base import ReglaBase
from models import Empleado


class ReglaDescuentoFaltas(ReglaBase):

    def aplica(self, empleado, fila_datos, contexto):
        reader = contexto['reader']
        col = contexto['config'].columnas_reglas.descuento_faltas
        descuento = reader.valor_celda(fila_datos, col, 0)
        return float(descuento) > 0

    def ejecutar(self, empleado, fila_datos, contexto):
        reader = contexto['reader']
        col = contexto['config'].columnas_reglas.descuento_faltas
        descuento = float(reader.valor_celda(fila_datos, col, 0))
        empleado.monto_cesta -= descuento
        return empleado