from datetime import datetime
from config import CONFIG
import calendar 
class ProcesadorFechas:
    """Encargado de la lógica temporal y formatos de fecha para la nómina."""

    @staticmethod
    def obtener_periodo_actual() -> tuple[str, str]:
        """Retorna (anio_str, mes_num_str) -> ('2026', '04')"""
        ahora = datetime.now()
        return str(ahora.year), f"{ahora.month:02d}"

    @staticmethod
    def obtener_nombre_mes(mes_num: str) -> str:
        """Convierte '04' -> 'ABRIL' usando CONFIG."""
        idx = int(mes_num)
        return CONFIG.meses_abreviados.get(idx, f"MES_{mes_num}")

    @staticmethod
    def calcular_fecha_corte() -> str:
        hoy = datetime.now()
        mes = hoy.month + 1
        anio = hoy.year
        if mes > 12:
            mes = 1
            anio += 1
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        return f'{ultimo_dia}/{mes:02d}/{anio}'
