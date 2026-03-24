"""Responsabilidad única: escribir datos en la plantilla Excel."""

from datetime import datetime
from models import Empleado
from readers import limpiar_texto


class PlantillaWriter:
    """Escribe empleados procesados en la plantilla destino."""

    def __init__(self, ws, idx_plantilla: dict):
        self.ws = ws
        self.idx_plantilla = idx_plantilla
        # Creamos un caché para no buscar en las cabeceras mil veces
        self._cache_columnas_retro = {}

    def escribir_empleado(self, empleado: Empleado, fila: int):
        """Escribe un empleado en la fila indicada."""
        datos = empleado.to_dict()
        for clave, col_idx in self.idx_plantilla.items():
            # PROTECCIÓN DE FÓRMULAS: 
            # Si la clave es del total, NO escribimos nada para dejar la fórmula intacta.
            if clave in ["total_retroactivo", "total_general"]: 
                continue
                
            if clave in datos and datos[clave] is not None:
                self.ws.cell(row=fila, column=col_idx, value=datos[clave])

    def escribir_retroactivos(
        self, empleado: Empleado, fila: int,
        meses_abreviados: dict[str, str], anio: str,
    ):
        """Escribe los montos en las columnas de retroactivo correspondientes."""
        # Si el caché está vacío, mapeamos la hoja una sola vez
        if not self._cache_columnas_retro:
            self._mapear_cabeceras_retroactivas(meses_abreviados, anio)

        for mes, monto in empleado.retroactivos.items():
            col = self._cache_columnas_retro.get(mes)
            if col:
                self.ws.cell(row=fila, column=col, value=monto)

    def _mapear_cabeceras_retroactivas(self, meses_abreviados: dict[str, str], anio: str):
        """Escanea la fila de cabeceras una sola vez y guarda las posiciones."""
        # Buscamos en la fila 1 (ajusta si tus cabeceras están en otra fila, ej: fila 2 o 3)
        fila_cabecera = 6
        for c in range(1, 150): # Escaneamos un rango amplio de columnas
            val = self.ws.cell(fila_cabecera, c).value
            if not val:
                continue
            
            val_txt = str(val).upper()
            # Si la columna es de RETROACTIVO
            if "RETRO" in val_txt:
                for num_mes, nombre_mes in meses_abreviados.items():
                    # Si el mes (ej: "ENE") está en la cabecera
                    if nombre_mes.upper() in val_txt:
                        self._cache_columnas_retro[num_mes] = c
                        break

    @staticmethod
    def generar_nombre_salida() -> str:
        ts = datetime.now().strftime('%H_%M_%S')
        return f'REPORTE_COMPLETO_{ts}.xlsx'