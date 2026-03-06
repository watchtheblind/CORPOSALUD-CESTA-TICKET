"""Carga y valida la configuración desde JSON."""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CampoMapeo:
    """Un campo mapeado entre origen y destino."""
    clave: str
    origen: Optional[str]   # None = no viene del libro carga
    destino: Optional[str]  # None = no va a la plantilla


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
    columnas_nombre: list[str]
    columnas_reglas: ColumnasReglas
    horarios: dict[str, str]
    horario_default: str
    estado_region_default: str
    plantilla_path: str


def cargar_configuracion(ruta: str = None) -> Configuracion:
    """
    Carga el JSON y devuelve un objeto Configuracion tipado.
    
    Si no se pasa ruta, busca config/campos.json relativo al proyecto.
    """
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

    # Validación básica
    _validar_estructura(datos)

    # Construir objetos tipados
    campos = [
        CampoMapeo(
            clave=c['clave'],
            origen=c.get('origen'),      # null en JSON → None en Python
            destino=c.get('destino'),
        )
        for c in datos['campos']
    ]

    reglas = ColumnasReglas(**datos['columnas_reglas'])

    defaults = datos['valores_default']

    return Configuracion(
        campos=campos,
        columnas_nombre=datos['columnas_nombre'],
        columnas_reglas=reglas,
        horarios=datos['horarios'],
        horario_default=defaults['horario'],
        estado_region_default=defaults['estado_region'],
        plantilla_path=defaults['plantilla_path'],
    )


def _validar_estructura(datos: dict):
    """Valida que el JSON tenga las claves obligatorias."""
    claves_requeridas = [
        'campos', 'columnas_nombre', 'columnas_reglas',
        'horarios', 'valores_default',
    ]
    faltantes = [k for k in claves_requeridas if k not in datos]
    if faltantes:
        raise ValueError(
            f"El archivo de configuración está incompleto. "
            f"Faltan las claves: {faltantes}"
        )

    # Validar que cada campo tenga al menos 'clave'
    for i, campo in enumerate(datos['campos']):
        if 'clave' not in campo:
            raise ValueError(
                f"El campo #{i} en 'campos' no tiene 'clave' definida."
            )