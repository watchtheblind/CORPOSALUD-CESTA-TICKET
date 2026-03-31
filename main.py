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


def ejecutar_pipeline(reader, ws, campos_cfg, ClaseProcesador, filtro_fn, **kwargs):
    """
    Orquestador genérico para procesar cualquier pestaña.
    """
    # Sacamos el iterable de kwargs para que no ensucie la instancia del procesador
    iterable = kwargs.pop('iterable', range(reader.fila_inicio_datos, reader.total_filas + 1))
    
    plantilla = PlantillaReader(ws, campos_cfg)
    writer = PlantillaWriter(ws, plantilla.indices)
    
    # IMPORTANTE: Instanciamos el procesador con los kwargs que SI necesita
    procesador = ClaseProcesador(
        reader=reader, 
        idx_plantilla=plantilla.indices, 
        **kwargs
    )

    procesados = 0
    no_encontrados = [] # Para el caso de retroactivos

    for item in iterable:
        if isinstance(item, int): 
            fila_datos = reader.leer_fila(item, COLUMNAS_LECTURA_MAX)
        else: 
            fila_datos = procesador.buscar_fila_por_cedula(item.cedula, COLUMNAS_LECTURA_MAX)

        if fila_datos is None:
            if not isinstance(item, int): no_encontrados.append(item.cedula)
            continue
            
        if not reader.fila_tiene_cedula(fila_datos):
            continue
            
        if filtro_fn and not filtro_fn(fila_datos, reader):
            continue

        fila_destino = plantilla.fila_inicio_datos + procesados
        
        # Lógica de procesamiento según la clase
        if ClaseProcesador == ProcesadorRetroactivo:
            # Para retroactivos pasamos el objeto 'item' (que es la Entrada)
            emp = procesador.procesar(fila_datos, item, procesados + 1, fila_destino, kwargs.get('anio'))
            writer.escribir_empleado(emp, fila_destino)
            writer.escribir_retroactivos(emp, fila_destino, CONFIG.meses_abreviados, kwargs.get('anio'))
        else:
            # PARA ACTIVOS Y CMP: 
            # Ya no pasamos *extra_args porque el procesador ya tiene la fecha en su 'self'
            emp = procesador.procesar(fila_datos, procesados + 1, fila_destino)
            writer.escribir_empleado(emp, fila_destino)
        
        procesados += 1

    # Si es retroactivo, devolvemos la tupla que espera el main
    if ClaseProcesador == ProcesadorRetroactivo:
        return procesados, no_encontrados
    
    return procesados

def procesar_activos(reader, ws_activos, fecha_corte, monto):
    def filtro(fila, rdr): 
        return rdr.cuenta_esta_activa(fila, CONFIG.columna_cuenta_activa) and rdr.fila_esta_activa(fila)
    
    return ejecutar_pipeline(reader, ws_activos, CONFIG.campos, ProcesadorEmpleado, filtro, 
                             monto_base=monto, fecha_corte=fecha_corte)

def procesar_cmp(reader, ws_cmp):
    def filtro(fila, rdr): 
        return not rdr.cuenta_esta_activa(fila, CONFIG.columna_cuenta_activa)
    
    return ejecutar_pipeline(reader, ws_cmp, CONFIG.campos_cmp, ProcesadorCMP, filtro)

def procesar_retroactivos(reader, ws_retro, entradas, gestor, anio):
    return ejecutar_pipeline(reader, ws_retro, CONFIG.campos_retroactivo, ProcesadorRetroactivo, None, 
                             gestor_montos=gestor, anio=anio, iterable=entradas)


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

def coordinar_retroactivos(ui, reader, wb_plantilla, gestor):
    """Encapsula toda la validación y proceso de retroactivos."""
    anio_actual, _ = gestor.obtener_mes_actual()
    dialogo = DialogoRetroactivos(ui.root, CONFIG.meses_abreviados, CONFIG.motivos_retroactivo, anio_actual)

    if dialogo.cancelado or not dialogo.resultado:
        return 0, []

    todos_meses = sorted({m for r in dialogo.resultado for m in r.meses})
    
    if verificar_montos_retroactivos(ui.root, gestor, anio_actual, todos_meses):
        ws_retro = wb_plantilla[CONFIG.nombres_hojas['retroactivos']]
        return procesar_retroactivos(reader, ws_retro, dialogo.resultado, gestor, anio_actual)
    
    return 0, []

def finalizar_proceso(reader, wb_plantilla, ui, n_activos, n_cmp, n_retro, no_encontrados, gestor):
    """Cierra recursos, pide ubicación, muestra resumen y guarda el Excel."""
    
    # 1. Liberar el archivo de carga (Cierra el Excel que leímos)
    reader.cerrar()
    
    # Obtenemos mes y año del gestor para el nombre del archivo
    mes_nombre, anio_actual = gestor.obtener_mes_actual()
    
    # Generamos el nombre sugerido: "ARAGUA PEDIDO DE TICKET MARZO 2026.xlsx"
    nombre_sugerido = PlantillaWriter.generar_nombre_salida(mes_nombre, anio_actual)
    
    # Le pedimos a la UI que abra el diálogo de guardado
    nombre_salida = ui.solicitar_guardar_archivo(nombre_sugerido)

    # Si el usuario cierra la ventana o presiona "Cancelar"
    if not nombre_salida:
        ui.mostrar_error("Guardado cancelado. No se generó el archivo de salida.")
        return

    # 4. Intentar guardar en la ruta elegida por el usuario
    try:
        wb_plantilla.save(nombre_salida)
        
        # 5. Si guardó bien, mostramos el resumen
        resumen = (
            f"📊 PROCESO FINALIZADO\n"
            f"{'-'*30}\n"
            f"✅ Activos: {n_activos}\n"
            f"✅ CMP: {n_cmp}\n"
            f"✅ Retroactivos: {n_retro}\n"
            f"{'-'*30}\n"
            f"Total: {n_activos + n_cmp + n_retro}"
        )

        if no_encontrados:
            resumen += f"\n\n⚠️ Cédulas no encontradas:\n" + "\n".join(no_encontrados)

        ui.mostrar_exito_detallado(resumen)
        
        # 6. Abrir el archivo automáticamente para que lo veas
        os.startfile(nombre_salida)
        
    except Exception as e:
        ui.mostrar_error(f"Error al guardar el archivo: {e}")

def main():
    ui = DialogoUI()
    
    # PANEL DE CONTROL (Interruptores)
    flags = {
        'procesar_activos': True,
        'procesar_cmp': True,
        'procesar_retroactivos': True
    }

    try:
        # 1. Inicialización de datos
        gestor = GestorMontos(CONFIG.ruta_montos_retroactivos)
        monto = obtener_monto_cesta(ui, gestor)
        ruta = ui.solicitar_archivo()
        
        if not monto or not ruta: 
            return

        # 2. Carga de recursos (Abrir archivos)
        reader = ExcelReader(ruta)
        wb_plantilla = load_workbook(CONFIG.plantilla_path)
        fecha_corte = calcular_fecha_corte()

        # --- AQUÍ ESTABA EL ERROR: DEFINIR LAS HOJAS ---
        # Definimos las hojas inmediatamente para que 'ws_activos' y 'ws_cmp' EXISTAN
        ws_activos = wb_plantilla[CONFIG.nombres_hojas['activos']]
        ws_cmp = wb_plantilla[CONFIG.nombres_hojas['cmp']]n
        # -----------------------------------------------

        # 3. Inicializar contadores (Para que el resumen final no falle)
        n_activos = 0
        n_cmp = 0
        n_retro = 0
        no_encontrados = []

        # 4. Ejecución modular (Uso de los flags)
        if flags['procesar_activos']:
            n_activos = procesar_activos(reader, ws_activos, fecha_corte, monto)
        
        if flags['procesar_cmp']:
            n_cmp = procesar_cmp(reader, ws_cmp)

        if flags['procesar_retroactivos']:
            # Nota: coordinar_retroactivos busca su propia hoja ws_retro adentro
            n_retro, no_encontrados = coordinar_retroactivos(ui, reader, wb_plantilla, gestor)

        # 5. Cierre y Salida (El guardado y el resumen)
        finalizar_proceso(reader, wb_plantilla, ui, n_activos, n_cmp, n_retro, no_encontrados, gestor)

    except Exception as e:
        ui.mostrar_error(f"Error crítico: {e}")
    finally:
        ui.cerrar()


if __name__ == '__main__':
    main()