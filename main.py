"""Punto de entrada. Orquesta el flujo de ACTIVOS, CMP y RETROACTIVOS."""

import os
import warnings
from openpyxl import load_workbook
# Tus módulos
from config import CONFIG
from processor_fechas import ProcesadorFechas # <-- El nuevo encargado del tiempo
from readers import ExcelReader, PlantillaReader
from writers import PlantillaWriter
from processors_activos import ProcesadorEmpleado
from processors_cmp import ProcesadorCMP
from processors_retro import ProcesadorRetroactivo
from montos import GestorMontos
from ui import DialogoUI
from ui_retroactivos import DialogoRetroactivos, DialogoMontosNuevos

warnings.filterwarnings('ignore', category=UserWarning)

COLUMNAS_LECTURA_MAX = 150

def obtener_monto_cesta_ticket(ui, gestor):
    """
    Coordina la obtención del monto usando el Gestor para datos,
    el ProcesadorFechas para el tiempo y la UI para interacción.
    """
    anio, mes_num = ProcesadorFechas.obtener_periodo_actual()
    mes_nombre = ProcesadorFechas.obtener_nombre_mes(mes_num)

    monto_actual = gestor.obtener_monto(anio, mes_num)

    if monto_actual is not None:
        monto_final = ui.verificar_monto_mes_actual(mes_nombre, anio, monto_actual)
    else:
        monto_final = ui.solicitar_monto_mes_nuevo(mes_nombre, anio)

    if monto_final is not None:
        gestor.registrar_monto(anio, mes_num, monto_final)
    
    return monto_final


def ejecutar_pipeline(reader, ws, campos_cfg, ClaseProcesador, filtro_fn, **kwargs):
    """Orquestador genérico para procesar cualquier pestaña."""
    iterable = kwargs.pop('iterable', range(reader.fila_inicio_datos, reader.total_filas + 1))
    
    plantilla = PlantillaReader(ws, campos_cfg)
    writer = PlantillaWriter(ws, plantilla.indices)
    
    procesador = ClaseProcesador(
        reader=reader, 
        idx_plantilla=plantilla.indices, 
        **kwargs
    )

    procesados = 0
    no_encontrados = [] 

    for item in iterable:
        if isinstance(item, int): 
            fila_datos = reader.leer_fila(item, COLUMNAS_LECTURA_MAX)
        else: 
            fila_datos = procesador.buscar_fila_por_cedula(item.cedula, COLUMNAS_LECTURA_MAX)

        if fila_datos is None:
            if not isinstance(item, int): no_encontrados.append(item.cedula)
            continue
            
        if not reader.fila_tiene_cedula(fila_datos) or (filtro_fn and not filtro_fn(fila_datos, reader)):
            continue

        fila_destino = plantilla.fila_inicio_datos + procesados
        
        if ClaseProcesador == ProcesadorRetroactivo:
            emp = procesador.procesar(fila_datos, item, procesados + 1, fila_destino, kwargs.get('anio'))
            writer.escribir_empleado(emp, fila_destino)
            writer.escribir_retroactivos(emp, fila_destino, CONFIG.meses_abreviados, kwargs.get('anio'))
        else:
            emp = procesador.procesar(fila_datos, procesados + 1, fila_destino)
            writer.escribir_empleado(emp, fila_destino)
        
        procesados += 1

    return (procesados, no_encontrados) if ClaseProcesador == ProcesadorRetroactivo else procesados

# --- WRAPPERS DE PROCESAMIENTO ---

def procesar_activos(reader, ws_activos, fecha_corte, monto):
    def filtro(fila, rdr): 
        return rdr.cuenta_esta_activa(fila, CONFIG.columna_cuenta_activa) and rdr.fila_esta_activa(fila)
    return ejecutar_pipeline(reader, ws_activos, CONFIG.campos, ProcesadorEmpleado, filtro, 
                             monto_base=monto, fecha_corte=fecha_corte)

def procesar_cmp(reader, ws_cmp):
    def filtro(fila, rdr): 
        return not rdr.cuenta_esta_activa(fila, CONFIG.columna_cuenta_activa)
    return ejecutar_pipeline(reader, ws_cmp, CONFIG.campos_cmp, ProcesadorCMP, filtro)

def coordinar_retroactivos(ui, reader, wb_plantilla, gestor):
    anio_actual, _ = ProcesadorFechas.obtener_periodo_actual()
    dialogo = DialogoRetroactivos(ui.root, CONFIG.meses_abreviados, CONFIG.motivos_retroactivo, anio_actual)

    if dialogo.cancelado or not dialogo.resultado:
        return 0, []

    # Validar que tengamos los montos históricos necesarios
    meses_necesarios = sorted({m for r in dialogo.resultado for m in r.meses})
    faltantes = [m for m in meses_necesarios if not gestor.existe_monto(anio_actual, m)]

    if faltantes:
        dialogo_m = DialogoMontosNuevos(ui.root, faltantes, CONFIG.meses_abreviados, anio_actual)
        if dialogo_m.cancelado: return 0, []
        for m, val in dialogo_m.resultado.items():
            gestor.registrar_monto(anio_actual, m, val)

    ws_retro = wb_plantilla[CONFIG.nombres_hojas['retroactivos']]
    return ejecutar_pipeline(reader, ws_retro, CONFIG.campos_retroactivo, ProcesadorRetroactivo, None, 
                             gestor_montos=gestor, anio=anio_actual, iterable=dialogo.resultado)

def finalizar_proceso(reader, wb_plantilla, ui, n_activos, n_cmp, n_retro, no_encontrados):
    """Cierra recursos, genera nombre dinámico y guarda."""
    reader.cerrar()
    
    # Aquí usamos el ProcesadorFechas para el nombre del archivo
    anio, mes_num = ProcesadorFechas.obtener_periodo_actual()
    mes_nombre = ProcesadorFechas.obtener_nombre_mes(mes_num)
    
    nombre_sugerido = PlantillaWriter.generar_nombre_salida(mes_nombre, anio)
    nombre_salida = ui.solicitar_guardar_archivo(nombre_sugerido)

    if not nombre_salida:
        ui.mostrar_error("Guardado cancelado.")
        return

    try:
        wb_plantilla.save(nombre_salida)
        resumen = (f"📊 RESUMEN\nActivos: {n_activos}\nCMP: {n_cmp}\nRetro: {n_retro}")
        if no_encontrados: resumen += f"\n\n⚠️ No encontrados: {', '.join(no_encontrados)}"
        ui.mostrar_exito_detallado(resumen)
        os.startfile(nombre_salida)
    except Exception as e:
        ui.mostrar_error(f"Error al guardar: {e}")

# --- MAIN ---

def main():
    ui = DialogoUI()
    flags = {'activos': True, 'cmp': True, 'retro': True}

    try:
        gestor = GestorMontos(CONFIG.ruta_montos_retroactivos)
        monto = obtener_monto_cesta_ticket(ui, gestor)
        ruta = ui.solicitar_archivo()
        
        if not monto or not ruta: return

        reader = ExcelReader(ruta)
        wb_plantilla = load_workbook(CONFIG.plantilla_path)
        fecha_corte = ProcesadorFechas.calcular_fecha_corte()

        n_activos = procesar_activos(reader, wb_plantilla[CONFIG.nombres_hojas['activos']], fecha_corte, monto) if flags['activos'] else 0
        n_cmp = procesar_cmp(reader, wb_plantilla[CONFIG.nombres_hojas['cmp']]) if flags['cmp'] else 0
        n_retro, no_en = coordinar_retroactivos(ui, reader, wb_plantilla, gestor) if flags['retro'] else (0, [])

        finalizar_proceso(reader, wb_plantilla, ui, n_activos, n_cmp, n_retro, no_en)

    except Exception as e:
        ui.mostrar_error(f"Error crítico: {e}")
    finally:
        ui.cerrar()

if __name__ == '__main__':
    main()