"""Modelo de datos del empleado. Sin lógica, solo estructura."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Empleado:
    """Representa un registro de empleado procesado."""
    n_fila: int = 0
    cedula: Any = ''
    nombres_completos: str = ''
    nac_calc: str = ''
    edad: Any = ''
    f_nac: Any = ''
    f_ingre: Any = ''
    anos_servicio: Any = ''
    genero: str = ''
    cuenta: Any = ''
    tipo_personal: str = ''
    denom_cargo: str = ''
    horario_laboral: str = ''
    carga_horaria: Any = ''
    dependencia: str = ''
    estado_region: str = ''
    monto_cesta: float = 0.0
    observaciones: str = ''
    largo_cuenta: Any = ''
    especialidad: str = ''
    # --- Campos CMP ---
    motivo_cmp: str = ''
    fecha_cmp: Any = ''
    # --- Campos Retroactivo ---
    retroactivos: dict = field(default_factory=dict)  # {"01": 2120, "03": 2579}
    total_retroactivo: Any = ''
    motivo_retroactivo: str = ''

    def to_dict(self) -> dict:
        """Convierte a diccionario para escritura genérica."""
        return {k: v for k, v in self.__dict__.items()}