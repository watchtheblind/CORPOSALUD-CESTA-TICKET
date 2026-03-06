"""Sistema de reglas de negocio. Abierto a extensión, cerrado a modificación."""

from abc import ABC, abstractmethod
from models import Empleado


class ReglaBase(ABC):
    """Contrato que toda regla de negocio debe cumplir."""

    @abstractmethod
    def aplica(self, empleado: Empleado, fila_datos: list, contexto: dict) -> bool:
        """¿Esta regla aplica al empleado actual?"""
        ...

    @abstractmethod
    def ejecutar(self, empleado: Empleado, fila_datos: list, contexto: dict) -> Empleado:
        """Modifica el empleado según la regla."""
        ...