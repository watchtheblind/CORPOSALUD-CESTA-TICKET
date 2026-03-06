"""
Registro central de reglas. 
Para agregar una regla nueva:
  1. Crea el archivo en rules/
  2. Agrégala a esta lista
  
Eso es todo. No tocas nada más.
"""

from rules.alto_nivel import ReglaAltoNivel
from rules.descuento_faltas import ReglaDescuentoFaltas

# Orden importa: se ejecutan secuencialmente
REGLAS_REGISTRADAS = [
    ReglaAltoNivel(),
    ReglaDescuentoFaltas(),
]