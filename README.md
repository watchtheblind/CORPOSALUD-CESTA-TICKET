

# README — CORPOSALUD CESTA TICKET

## ¿Qué hace este programa?

Lee un **Libro de Carga** (Excel con datos de empleados de nómina), filtra los empleados activos, les aplica reglas de negocio (montos, descuentos, encargadurías) y genera un **Reporte Excel** usando una plantilla predefinida.

---

## Estructura del Proyecto

```
CORPOSALUD-CESTA-TICKET/
│
├── main.py                  # 🚀 Punto de entrada. Ejecutas este.
├── ui.py                    # 🖥️  Ventanas emergentes (pedir monto, archivo, mostrar errores)
├── readers.py               # 📖 Lee los Excel (libro carga + plantilla)
├── processors.py            # 🧠 Lógica de transformación (arma cada empleado)
├── writers.py               # ✍️  Escribe empleados en la plantilla
├── formulas.py              # 📐 Genera fórmulas de Excel (DATEDIF, LEN)
├── models.py                # 📦 Estructura de datos del empleado (dataclass)
│
├── config/
│   ├── __init__.py          # Carga CONFIG automáticamente al importar
│   ├── loader.py            # Lee y valida el JSON
│   └── campos.json          # ⚙️  CONFIGURACIÓN MAESTRA (mapeo de columnas)
│
├── rules/
│   ├── __init__.py          # Lista de reglas activas
│   ├── base.py              # Contrato abstracto (interfaz de regla)
│   ├── alto_nivel.py        # Regla: personal alto nivel fijo
│   └── descuento_faltas.py  # Regla: resta faltas al monto
│
└── template2.xlsx           # 📄 Plantilla Excel de salida
```

---

## Flujo de Ejecución (qué pasa cuando corres `py main.py`)

```
PASO 1 → ui.py te pide:
         - Monto de cesta ticket (número)
         - Ruta del Libro de Carga (archivo .xlsx)

PASO 2 → readers.py abre el Libro de Carga:
         - Busca la fila que tiene "CEDULA" como cabecera
         - Mapea TODAS las columnas por nombre
         - Queda listo para leer fila por fila

PASO 3 → readers.py abre template2.xlsx:
         - Busca las cabeceras de la plantilla
         - Mapea qué columna de la plantilla corresponde a qué campo

PASO 4 → main.py recorre cada fila del Libro de Carga:
         - ¿Tiene cédula? → Si no, PARA (fin de datos)
         - ¿Tiene "SI"?   → Si no, SALTA (empleado inactivo)
         - Si pasa ambos filtros → processors.py lo transforma

PASO 5 → processors.py para CADA empleado:
         a) Extrae campos directos (cédula, género, cargo, etc.)
         b) Arma el nombre completo (4 columnas → 1 string)
         c) Calcula nacionalidad por patrón de cédula
         d) Deduce horario laboral por carga horaria
         e) Inyecta fórmulas de Excel (edad, años servicio, largo cuenta)
         f) Aplica TODAS las reglas de negocio registradas

PASO 6 → writers.py escribe el empleado en la fila correspondiente
         de la plantilla

PASO 7 → Guarda el archivo como REPORTE_COMPLETO_HH_MM_SS.xlsx
         y lo abre automáticamente
```

---

## Archivo por Archivo: Qué Hace y Cuándo Tocarlo

### `config/campos.json` — ⭐ EL MÁS IMPORTANTE

**Tocarlo cuando:** Cambia el nombre de una columna en el Libro de Carga o en la plantilla.

```json
{
  "clave": "cedula",          // Nombre interno (no tocar)
  "origen": "CEDULA",         // Nombre de la columna en el LIBRO DE CARGA
  "destino": "CEDULA"         // Nombre de la columna en la PLANTILLA
}
```

**Reglas:**
- `"origen": null` → El campo NO viene del libro de carga (se calcula)
- `"destino": null` → El campo NO va a la plantilla (solo uso interno)
- Si RRHH renombra una columna, **solo cambias el string aquí**

**Otras secciones del JSON:**

```json
"columnas_nombre": [...]      // Las 4 columnas que forman el nombre completo
"columnas_reglas": {...}      // Columnas que usan las reglas de negocio
"horarios": {...}             // Mapeo carga horaria → horario legible
"valores_default": {...}      // Estado/región, ruta plantilla, horario por defecto
```

---

### `models.py` — Estructura del Empleado

**Tocarlo cuando:** Agregas un campo NUEVO que no existía antes.

```python
@dataclass
class Empleado:
    cedula: Any = ''
    nombres_completos: str = ''
    # ... todos los campos ...
    # ¿Campo nuevo? Agrégalo aquí:
    telefono: str = ''
```

**Solo es una estructura de datos.** No tiene lógica, no hace cálculos. Es la "caja" donde viaja la información de cada empleado.

---

### `readers.py` — Lectura de Excel

**Tocarlo cuando:** Cambia la estructura fundamental de cómo leer los archivos (casi nunca).

**Tiene 2 clases:**

| Clase | Qué lee | Métodos importantes |
|---|---|---|
| `ExcelReader` | Libro de Carga | `leer_fila()`, `valor_celda()`, `fila_tiene_cedula()`, `fila_esta_activa()` |
| `PlantillaReader` | template2.xlsx | `indices` (diccionario columna→posición), `fila_inicio_datos` |

**Ejemplo de uso interno:**
```python
# Leer el valor de la columna "SEXO" de una fila
genero = reader.valor_celda(fila, "SEXO")

# Verificar si la fila tiene cédula
if not reader.fila_tiene_cedula(fila):
    break  # Fin de datos
```

---

### `processors.py` — Cerebro del Programa

**Tocarlo cuando:** Cambia la LÓGICA de cómo se transforma un campo (no el nombre, sino el cálculo).

**Métodos y qué hacen:**

| Método | Qué hace | Ejemplo de cuándo tocarlo |
|---|---|---|
| `_extraer_campos_directos()` | Copia valores tal cual del origen | Nunca (es automático por el JSON) |
| `_calcular_nombre()` | Une 4 columnas en 1 string | Si cambian a 3 columnas o 5 |
| `_calcular_nacionalidad()` | V o E según cédula | Si cambian las reglas de nacionalidad |
| `_calcular_horario()` | Deduce horario de carga horaria | Mejor tócalo en el JSON (sección `horarios`) |
| `_calcular_especialidad()` | Extrae especialidad médica | Si cambia el nombre origen de la columna |
| `_inyectar_formulas()` | Genera DATEDIF y LEN | Si necesitas nuevas fórmulas de Excel |
| `_aplicar_reglas()` | Ejecuta TODAS las reglas registradas | Nunca (agrega reglas en `rules/`) |

---

### `formulas.py` — Fórmulas de Excel

**Tocarlo cuando:** Necesitas una fórmula de Excel nueva.

```python
# Ya existen:
formula_edad(col, fila, fecha)          # → =DATEDIF(F9,DATE(2026,2,28),"Y")
formula_anos_servicio(col, fila, fecha) # → =DATEDIF(G9,DATE(2026,2,28),"Y")
formula_largo_cuenta(col, fila)         # → =LEN(K9)

# ¿Necesitas una nueva? Agrégala aquí:
def formula_suma_rango(col_inicio, col_fin, fila):
    letra_i = get_column_letter(col_inicio)
    letra_f = get_column_letter(col_fin)
    return f'=SUM({letra_i}{fila}:{letra_f}{fila})'
```

---

### `writers.py` — Escritura en la Plantilla

**Tocarlo cuando:** Casi nunca. Solo si cambia cómo se escribe en Excel.

```python
# Hace 2 cosas:
writer.escribir_empleado(emp, fila)     # Escribe todos los campos en la fila
PlantillaWriter.generar_nombre_salida() # Genera "REPORTE_COMPLETO_14_30_22.xlsx"
```

---

### `ui.py` — Interfaz de Usuario

**Tocarlo cuando:** Quieres cambiar las ventanas emergentes, agregar más campos de entrada, etc.

```python
# Métodos disponibles:
ui.solicitar_datos()    # Pide monto + archivo → devuelve EntradaUsuario o None
ui.mostrar_exito(n)     # Popup verde: "Se procesaron N registros"
ui.mostrar_error(msg)   # Popup rojo: "Error: ..."
ui.cerrar()             # Cierra tkinter
```

---

### `rules/` — Reglas de Negocio

**Tocarlo cuando:** Hay una regla NUEVA o cambia una existente.

#### Reglas actuales:

| Archivo | Qué hace | Cuándo aplica |
|---|---|---|
| `alto_nivel.py` | Si es Alto Nivel Fijo con sueldo 101 > 0, pone monto + "ENCARGADURÍA". Si no, monto = 0 | `tipo_personal` contiene "ALTO NIVEL FIJO" |
| `descuento_faltas.py` | Resta el valor de "DESCUENTO POR FALTAS" al monto | Columna de descuento > 0 |

#### Cómo agregar una regla nueva:

**Paso 1:** Crear archivo `rules/mi_regla.py`

```python
from rules.base import ReglaBase
from models import Empleado


class ReglaMiRegla(ReglaBase):

    def aplica(self, empleado, fila_datos, contexto):
        # ¿Cuándo se activa esta regla?
        return empleado.tipo_personal == "CONTRATADO"

    def ejecutar(self, empleado, fila_datos, contexto):
        # ¿Qué hace?
        empleado.monto_cesta *= 0.5
        empleado.observaciones = "CONTRATADO 50%"
        return empleado
```

**Paso 2:** Registrarla en `rules/__init__.py`

```python
from rules.alto_nivel import ReglaAltoNivel
from rules.descuento_faltas import ReglaDescuentoFaltas
from rules.mi_regla import ReglaMiRegla          # ← importar

REGLAS_REGISTRADAS = [
    ReglaAltoNivel(),
    ReglaDescuentoFaltas(),
    ReglaMiRegla(),                                # ← agregar
]
```

**Eso es todo.** No tocas main.py, ni processors.py, ni nada más.

---

## Tareas Comunes — Guía Rápida

| Necesito... | Toco... |
|---|---|
| Cambiar nombre de columna del libro carga | `config/campos.json` → campo `"origen"` |
| Cambiar nombre de columna de la plantilla | `config/campos.json` → campo `"destino"` |
| Agregar un campo nuevo al reporte | `campos.json` + `models.py` (agregar atributo) |
| Agregar una regla de negocio | Crear archivo en `rules/` + registrar en `rules/__init__.py` |
| Cambiar cómo se calcula la nacionalidad | `processors.py` → `_calcular_nacionalidad()` |
| Agregar una fórmula de Excel | `formulas.py` + llamarla desde `processors.py` → `_inyectar_formulas()` |
| Cambiar el monto por defecto | No aplica (se pide siempre por ventana) |
| Cambiar la plantilla de salida | Reemplazar `template2.xlsx` o cambiar ruta en `campos.json` → `valores_default.plantilla_path` |
| Cambiar el estado/región por defecto | `campos.json` → `valores_default.estado_region` |
| Cambiar mapeo de horarios | `campos.json` → `horarios` |

---

## Dependencias

```
pip install openpyxl
```

Python 3.10+ (por los type hints con `dict[str, int]` y `list[str]`).

---

## Ejecución

```bash
cd CORPOSALUD-CESTA-TICKET
py main.py
```

Sale la ventana pidiendo monto → seleccionas el archivo → genera el reporte → se abre solo.
