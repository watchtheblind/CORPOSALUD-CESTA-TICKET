# Archivo: base_processor.py
from models import Empleado
from formulas import formula_largo_cuenta
class ProcesadorBase:

    def _pre_procesar_comun(self, emp, fila_datos, campos_mapeo):
        """Ejecuta todas las limpiezas y cálculos básicos que comparten todos los procesadores."""
        
        # 1. Cuenta Bancaria (Busca el origen dinámicamente en el JSON)
        col_cuenta = next((c.origen for c in campos_mapeo if c.clave == "cuenta"), None)
        if col_cuenta:
            valor_cuenta = self.reader.valor_celda(fila_datos, col_cuenta)
            emp.cuenta = self.limpiar_cuenta_bancaria(valor_cuenta)

        # 2. Pipeline de cálculos básicos (Pasando el objeto emp completo)
        self._calcular_nombre(emp, fila_datos)
        emp.nac_calc = self._calcular_nacionalidad(emp.cedula)
        self._calcular_horario(emp)
        self._calcular_especialidad(emp, fila_datos)
        
        
        # 3. Valor por defecto
        emp.estado_region = self.cfg.estado_region_default
    
    def limpiar_cuenta_bancaria(self, valor) -> str:
        """
        Elimina comillas simples, dobles y espacios de los números de cuenta.
        """
        if not valor:
            return ""
        # Convertimos a string, quitamos espacios y reemplazamos ambos tipos de comillas
        limpio = str(valor).strip().replace("'", "").replace('"', "")
        return limpio

    def formatear_fecha(self, valor_fecha) -> str:
        """
        Toma cualquier cosa que parezca una fecha y la devuelve como DD/MM/YYYY.
        Si viene con hora, se la quita
        """
        if not valor_fecha:
            return ""
        
        try:
            # Si Excel ya lo leyó como un objeto datetime de Python
            if isinstance(valor_fecha, datetime):
                return valor_fecha.strftime('%d/%m/%Y')
            
            # Si viene como texto (ej: "2023-10-01 00:00:00" o "2023-10-01")
            # Tomamos solo los primeros 10 caracteres (la fecha)
            fecha_str = str(valor_fecha).split(' ')[0]
            
            # Intentamos parsear el formato ISO que suele traer Excel
            obj_fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
            return obj_fecha.strftime('%d/%m/%Y')
            
        except Exception:
            # Si todo falla (ej: es un texto loco), devolvemos el original
            # para no perder la información, pero convertido a string.
            return str(valor_fecha).split(' ')[0]

    def _calcular_horario(self, emp: Empleado):
        """Deduce horario laboral de la carga horaria."""
        carga = str(emp.carga_horaria).strip()
        for clave, horario in self.cfg.horarios.items():
            if clave in carga:
                emp.horario_laboral = horario
                return
        emp.horario_laboral = self.cfg.horario_default

    def _calcular_especialidad(self, emp: Empleado, fila_datos: list):
        """Extrae especialidad médica si existe."""

        # Buscamos el objeto que tiene la clave 'especialidad' en la lista de campos
        col_especialidad = next(c.origen for c in self.cfg.campos if c.clave == 'especialidad')
        #valor = self.reader.valor_celda(fila_datos, 'ESPECIALIDAD MÉD 1')
        valor = self.reader.valor_celda(fila_datos, col_especialidad)
        emp.especialidad = valor if valor else ''

    def _calcular_nombre(self, emp: Empleado, fila_datos: list):
        """Construye nombre completo a partir de las 4 columnas."""
        partes = []
        for col in self.cfg.columnas_nombre:
            valor = self.reader.valor_celda(fila_datos, col)
            if valor:
                partes.append(str(valor).strip())
        emp.nombres_completos = ' '.join(partes).upper()

    def _inyectar_formulas_comunes(self, emp, fila_excel: int):
        """Genera las fórmulas básicas presentes en todas las plantillas."""
        col_cuenta = self.idx_plantilla.get('cuenta', 1)
        emp.largo_cuenta = formula_largo_cuenta(col_cuenta, fila_excel)

    def _extraer_campos_directos(self, fila_datos: list, mapeo_campos: list) -> Empleado:
        """
        Extrae campos con mapeo directo desde el libro carga usando
        la lista de mapeo proporcionada (activos, cmp o retro).
        """
        emp = Empleado()
        for campo in mapeo_campos:
            if campo.origen is not None:
                valor = self.reader.valor_celda(fila_datos, campo.origen, '')
                setattr(emp, campo.clave, valor)
        return emp

    def _calcular_nacionalidad(self, cedula_valor):
        # Ahora 'cedula_valor' es el número directamente
        ced_str = str(cedula_valor).strip()
        try:
            ced_num = int(ced_str)
        except:
            ced_num = 0
        
        if ced_num >= self.cfg.umbral_extranjero:
            return 'E'
        return 'V'