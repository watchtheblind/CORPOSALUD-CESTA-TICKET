"""Punto de entrada. Orquesta el flujo sin contener lógica de negocio."""

import os
import calendar
import warnings
from datetime import datetime

from config import CONFIG
from readers import ExcelReader, PlantillaReader
from writers import PlantillaWriter
from processors import ProcesadorEmpleado
from ui import DialogoUI

warnings.filterwarnings('ignore', category=UserWarning)

COLUMNAS_LECTURA_MAX = 150


def calcular_fecha_corte() -> str:
    """Calcula el último día del mes siguiente como dd/mm/yyyy."""
    hoy = datetime.now()
    mes = hoy.month + 1
    anio = hoy.year
    if mes > 12:
        mes = 1
        anio += 1
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return f'{ultimo_dia}/{mes:02d}/{anio}'


def main():
    ui = DialogoUI()

    try:
        # 1. Entrada del usuario
        entrada = ui.solicitar_datos()
        if entrada is None:
            return

        # 2. Abrir archivos
        reader = ExcelReader(entrada.ruta_carga)
        plantilla = PlantillaReader(CONFIG.plantilla_path, CONFIG.campos)
        writer = PlantillaWriter(plantilla.ws, plantilla.indices)

        # 3. Configurar procesador
        fecha_corte = calcular_fecha_corte()
        procesador = ProcesadorEmpleado(
            reader=reader,
            idx_plantilla=plantilla.indices,
            monto_base=entrada.monto,
        )

        # 4. Procesar fila por fila
        procesados = 0
        for r in range(reader.fila_inicio_datos, reader.total_filas + 1):
            fila = reader.leer_fila(r, COLUMNAS_LECTURA_MAX)

            # Sin cédula = fin de datos reales
            if not reader.fila_tiene_cedula(fila):
                break

            # Solo empleados activos (marcados con "SI")
            if not reader.fila_esta_activa(fila):
                continue

            fila_destino = plantilla.fila_inicio_datos + procesados

            emp = procesador.procesar(
                fila_datos=fila,
                n_item=procesados + 1,
                fila_excel=fila_destino,
                fecha_corte=fecha_corte,
            )

            writer.escribir_empleado(emp, fila_destino)
            procesados += 1

        # 5. Guardar y mostrar resultado
        reader.cerrar()
        nombre_salida = PlantillaWriter.generar_nombre_salida()
        plantilla.wb.save(nombre_salida)

        ui.mostrar_exito(procesados)
        os.startfile(nombre_salida)

    except Exception as e:
        ui.mostrar_error(str(e))

    finally:
        ui.cerrar()


if __name__ == '__main__':
    main()