"""Punto de entrada. Orquesta el flujo de ACTIVOS, CMP y RETROACTIVOS."""

import os
import calendar
import warnings
from datetime import datetime

from config import CONFIG
from readers import ExcelReader, PlantillaReader
from writers import PlantillaWriter
from processors_activos import ProcesadorEmpleado
from processors_cmp import ProcesadorCMP
from processors_retro import ProcesadorRetroactivo
from montos import GestorMontos
from ui import DialogoUI
from ui_retroactivos import DialogoRetroactivos, DialogoMontosNuevos
from openpyxl import load_workbook

warnings.filterwarnings('ignore', category=UserWarning)

COLUMNAS_LECTURA_MAX = 150


def calcular_fecha_corte() -> str:
    hoy = datetime.now()
    mes = hoy.month + 1
    anio = hoy.year
    if mes > 12:
        mes = 1
        anio += 1
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return f'{ultimo_dia}/{mes:02d}/{anio}'


def obtener_monto_cesta(ui, gestor):
    """
    Obtiene el monto de cesta ticket del mes.
    Si ya existe en el JSON: pregunta mantener o cambiar.
    Si no existe: pide ingresarlo.
    En ambos casos queda registrado en el JSON.
    Retorna el monto o None si cancela.
    """
    anio, mes = gestor.obtener_mes_actual()
    mes_nombre = CONFIG.meses_abreviados.get(mes, mes)

    if gestor.existe_monto(anio, mes):
        monto_actual = gestor.obtener_monto(anio, mes)
        monto_final = ui.verificar_monto_mes_actual(mes_nombre, anio, monto_actual)

        if monto_final is None:
            return None

        if monto_final != monto_actual:
            gestor.registrar_monto(anio, mes, monto_final)

        return monto_final
    else:
        monto_nuevo = ui.solicitar_monto_mes_nuevo(mes_nombre, anio)

        if monto_nuevo is None:
            return None

        gestor.registrar_monto(anio, mes, monto_nuevo)
        return monto_nuevo


def procesar_activos(reader, ws_activos, fecha_corte, monto):
    plantilla = PlantillaReader(ws_activos, CONFIG.campos)
    writer = PlantillaWriter(ws_activos, plantilla.indices)
    procesador = ProcesadorEmpleado(
        reader=reader,
        idx_plantilla=plantilla.indices,
        monto_base=monto,
    )

    procesados = 0
    for r in range(reader.fila_inicio_datos, reader.total_filas + 1):
        fila = reader.leer_fila(r, COLUMNAS_LECTURA_MAX)

        if not reader.fila_tiene_cedula(fila):
            break

        if not reader.cuenta_esta_activa(fila, CONFIG.columna_cuenta_activa):
            continue

        if not reader.fila_esta_activa(fila):
            continue

        fila_destino = plantilla.fila_inicio_datos + procesados
        emp = procesador.procesar(fila, procesados + 1, fila_destino, fecha_corte)
        writer.escribir_empleado(emp, fila_destino)
        procesados += 1

    return procesados


def procesar_cmp(reader, ws_cmp):
    plantilla = PlantillaReader(ws_cmp, CONFIG.campos_cmp)
    writer = PlantillaWriter(ws_cmp, plantilla.indices)
    procesador = ProcesadorCMP(
        reader=reader,
        idx_plantilla=plantilla.indices,
    )

    procesados = 0
    for r in range(reader.fila_inicio_datos, reader.total_filas + 1):
        fila = reader.leer_fila(r, COLUMNAS_LECTURA_MAX)

        if not reader.fila_tiene_cedula(fila):
            continue # <-- Cambiado de break a continue para no rendirse si hay un hueco

        if reader.cuenta_esta_activa(fila, CONFIG.columna_cuenta_activa):
            # Si entramos aquí, es un empleado activo normal. 
            # Lo saltamos porque esta función SOLO es para los que NO son activos.
            continue 

        # Si el programa llega a este punto, significa que encontró un CMP
        print(f"DEBUG: ¡Encontré un CMP! Cédula: {reader.valor_celda(fila, 'CEDULA')}")

        fila_destino = plantilla.fila_inicio_datos + procesados
        emp = procesador.procesar(fila, procesados + 1, fila_destino)
        writer.escribir_empleado(emp, fila_destino)
        procesados += 1

    return procesados


def verificar_montos_retroactivos(root, gestor, anio, meses_necesarios):
    faltantes = [m for m in meses_necesarios if not gestor.existe_monto(anio, m)]

    if not faltantes:
        return True

    dialogo = DialogoMontosNuevos(
        root, faltantes, CONFIG.meses_abreviados, anio,
    )

    if dialogo.cancelado:
        return False

    for mes, monto in dialogo.resultado.items():
        gestor.registrar_monto(anio, mes, monto)

    return True


def procesar_retroactivos(reader, ws_retro, entradas, gestor, anio):
    plantilla = PlantillaReader(ws_retro, CONFIG.campos_retroactivo)
    writer = PlantillaWriter(ws_retro, plantilla.indices)
    procesador = ProcesadorRetroactivo(
        reader=reader,
        idx_plantilla=plantilla.indices,
        gestor_montos=gestor,
    )

    procesados = 0
    no_encontrados = []

    for entrada in entradas:
        fila_datos = procesador.buscar_fila_por_cedula(entrada.cedula, COLUMNAS_LECTURA_MAX)

        if fila_datos is None:
            no_encontrados.append(entrada.cedula)
            continue

        fila_destino = plantilla.fila_inicio_datos + procesados
        emp = procesador.procesar(
            fila_datos, entrada, procesados + 1, fila_destino, anio,
        )

        writer.escribir_empleado(emp, fila_destino)
        writer.escribir_retroactivos(emp, fila_destino, CONFIG.meses_abreviados, anio)
        procesados += 1

    return procesados, no_encontrados


def main():
    ui = DialogoUI()

    try:
        # 1. Obtener monto del mes (verifica JSON, pregunta si cambiar, o pide nuevo)
        gestor = GestorMontos(CONFIG.ruta_montos_retroactivos)
        monto = obtener_monto_cesta(ui, gestor)
        if monto is None:
            return

        # 2. Pedir solo el archivo de carga (el monto ya lo tenemos)
        ruta = ui.solicitar_archivo()
        if ruta is None:
            return

        # 3. Abrir libro de carga
        reader = ExcelReader(ruta)

        # 4. Abrir plantilla
        wb_plantilla = load_workbook(CONFIG.plantilla_path)
        ws_activos = wb_plantilla[CONFIG.nombres_hojas['activos']]
        ws_cmp = wb_plantilla[CONFIG.nombres_hojas['cmp']]

        # 5. Procesar activos y CMP
        fecha_corte = calcular_fecha_corte()
        n_activos = procesar_activos(reader, ws_activos, fecha_corte, monto)
        n_cmp = procesar_cmp(reader, ws_cmp)

        # 6. Retroactivos (con opción de omitir)
        anio_actual, _ = gestor.obtener_mes_actual()

        dialogo_retro = DialogoRetroactivos(
            ui.root,
            CONFIG.meses_abreviados,
            CONFIG.motivos_retroactivo,
            anio_actual,
        )

        n_retro = 0
        no_encontrados = []

        if not dialogo_retro.cancelado and dialogo_retro.resultado:
            todos_meses = set()
            for r in dialogo_retro.resultado:
                todos_meses.update(r.meses)

            montos_ok = verificar_montos_retroactivos(
                ui.root, gestor, anio_actual, sorted(todos_meses)
            )

            if montos_ok:
                ws_retro = wb_plantilla[CONFIG.nombres_hojas['retroactivos']]
                n_retro, no_encontrados = procesar_retroactivos(
                    reader, ws_retro, dialogo_retro.resultado, gestor, anio_actual,
                )

        # 7. Guardar y mostrar resultado
        reader.cerrar()
        nombre_salida = PlantillaWriter.generar_nombre_salida()
        wb_plantilla.save(nombre_salida)

        resumen = (
            f"Activos: {n_activos} registros\n"
            f"CMP: {n_cmp} registros\n"
            f"Retroactivos: {n_retro} registros"
        )

        if no_encontrados:
            resumen += f"\n\n⚠️ Cédulas no encontradas:\n" + "\n".join(no_encontrados)

        resumen += f"\n\nTotal: {n_activos + n_cmp + n_retro}"

        ui.mostrar_exito_detallado(resumen)
        os.startfile(nombre_salida)

    except Exception as e:
        ui.mostrar_error(str(e))

    finally:
        ui.cerrar()


if __name__ == '__main__':
    main()