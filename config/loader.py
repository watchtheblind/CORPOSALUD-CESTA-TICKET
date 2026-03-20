"""Carga y valida la configuración desde JSON."""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CampoMapeo:
    """Un campo mapeado entre origen y destino."""
    clave: str
    origen: Optional[str]
    destino: Optional[str]


@dataclass(frozen=True)
class ColumnasReglas:
    """Nombres de columnas usadas por las reglas de negocio."""
    sueldo_101: str
    diferencia_117: str
    descuento_faltas: str


@dataclass(frozen=True)
class Configuracion:
    """Configuración completa del sistema, inmutable después de cargar."""
    campos: list[CampoMapeo]
    campos_cmp: list[CampoMapeo]
    campos_retroactivo: list[CampoMapeo]
    columnas_fecha: list[str]   
    columna_cuenta_bancaria: str  
    nombres_hojas: dict[str, str]
    columnas_nombre: list[str]
    columnas_reglas: ColumnasReglas
    umbral_extranjero: int          
    excepcion_cedula_e: str
    columna_cuenta_activa: str
    motivos_cmp: dict[str, str]
    motivos_retroactivo: list[str]
    meses_abreviados: dict[str, str]
    ruta_montos_retroactivos: str
    horarios: dict[str, str]
    horario_default: str
    estado_region_default: str
    plantilla_path: str


def cargar_configuracion(ruta: str = None) -> Configuracion:
    """Carga el JSON y devuelve un objeto Configuracion tipado."""
    if ruta is None:
        ruta = Path(__file__).parent / 'campos.json'

    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(
            f"Archivo de configuración no encontrado: {ruta}\n"
            f"Crea el archivo 'config/campos.json' con el mapeo de campos."
        )

    with open(ruta, encoding='utf-8') as f:
        datos = json.load(f)

    _validar_estructura(datos)

    campos = _parsear_campos(datos['campos'])
    campos_cmp = _parsear_campos(datos['campos_cmp'])
    campos_retro = _parsear_campos(datos['campos_retroactivo'])
    reglas = ColumnasReglas(**datos['columnas_reglas'])
    hojas = datos.get('nombres_hojas', {
        "activos": "ACTIVOS", 
        "cmp": "CMP", 
        "retroactivos": "RETROACTIVOS"
    })
    defaults = datos['valores_default']

    return Configuracion(
        campos=campos,
        campos_cmp=campos_cmp,
        campos_retroactivo=campos_retro,
        columnas_fecha=datos['columnas_fecha'],           # <-- FALTABA ESTE
        columna_cuenta_bancaria=datos['columna_cuenta_bancaria'], # <-- FALTABA ESTE
        nombres_hojas=hojas,
        columnas_nombre=datos['columnas_nombre'],
        columnas_reglas=reglas,
        umbral_extranjero=defaults['umbral_extranjero'],
        excepcion_cedula_e=defaults['excepcion_cedula_e'],
        columna_cuenta_activa=datos['columna_cuenta_activa'],
        motivos_cmp=datos['motivos_cmp'],
        motivos_retroactivo=datos['motivos_retroactivo'],
        meses_abreviados=datos['meses_abreviados'],
        ruta_montos_retroactivos=datos['ruta_montos_retroactivos'],
        horarios=datos['horarios'],
        horario_default=defaults['horario'],
        estado_region_default=defaults['estado_region'],
        plantilla_path=defaults['plantilla_path']
    )


def _parsear_campos(lista: list[dict]) -> list[CampoMapeo]:
    """Convierte lista de dicts en lista de CampoMapeo."""
    return [
        CampoMapeo(
            clave=c['clave'],
            origen=c.get('origen'),
            destino=c.get('destino'),
        )
        for c in lista
    ]


def _validar_estructura(datos: dict):
    """Valida que el JSON tenga las claves obligatorias."""
    claves_requeridas = [
        'campos', 'campos_cmp', 'campos_retroactivo',
        'columnas_nombre', 'columnas_reglas',
        'columna_cuenta_activa', 'motivos_cmp',
        'columnas_fecha',        
        'columna_cuenta_bancaria',
        'motivos_retroactivo', 'meses_abreviados',
        'ruta_montos_retroactivos',
        'horarios', 'valores_default',
    ]
    faltantes = [k for k in claves_requeridas if k not in datos]
    if faltantes:
        raise ValueError(
            f"Archivo de configuración incompleto. Faltan: {faltantes}"
        )

    for seccion in ['campos', 'campos_cmp', 'campos_retroactivo']:
        for i, campo in enumerate(datos[seccion]):
            if 'clave' not in campo:
                raise ValueError(
                    f"El campo #{i} en '{seccion}' no tiene 'clave' definida."
                )