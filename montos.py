"""Gestión de montos históricos de cesta ticket por mes."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class GestorMontos:
    """Lee, consulta y actualiza el JSON de montos retroactivos."""

    def __init__(self, ruta: str):
        self._ruta = Path(ruta)
        self._datos: dict[str, dict[str, float]] = {}
        self.cargar_desde_disco()

    def cargar_desde_disco(self):
        """Carga el JSON. Si no existe, crea uno vacío."""
        if self._ruta.exists():
            with open(self._ruta, encoding='utf-8') as f:
                raw = json.load(f)
            self._datos = {}
            for anio, meses in raw.items():
                self._datos[anio] = {
                    mes: monto
                    for mes, monto in meses.items()
                    if monto is not None
                }
        else:
            self._datos = {}

    def guardar_en_disco(self):
        """Guarda el estado actual del caché en el archivo físico."""
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(self._ruta, 'w', encoding='utf-8') as f:
            json.dump(self._datos, f, indent=2, ensure_ascii=False)

    def obtener_monto(self, anio: str, mes: str) -> Optional[float]:
        return self._datos.get(anio, {}).get(mes)

    def existe_monto(self, anio: str, mes: str) -> bool:
        return self.obtener_monto(anio, mes) is not None

    def registrar_monto(self, anio: str, mes: str, monto: float):
        if anio not in self._datos:
            self._datos[anio] = {}
        self._datos[anio][mes] = monto
        self.guardar_en_disco()

    def meses_sin_monto(self, anio: str, hasta_mes: str) -> list[str]:
        faltantes = []
        for m in range(1, int(hasta_mes) + 1):
            mes_str = f"{m:02d}"
            if not self.existe_monto(anio, mes_str):
                faltantes.append(mes_str)
        return faltantes
        
    @property
    def get_datos(self):
        """Acceso de solo lectura a los datos cargados."""
        return self._datos
