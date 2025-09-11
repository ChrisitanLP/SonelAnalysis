# ============================================
# core/etl/loaders/data_loader.py
# ============================================
from config.logger import logger
from core.database.operations import DataHandler

class DataLoader:
    """Cargador de datos especializado"""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
    
    def load_data(self, data, codigo, file_path):
        """
        Ejecuta el paso de carga de datos a la base de datos
       
        Args:
            data: DataFrame con los datos transformados
            codigo: Código del cliente
            file_path: Ruta al archivo original (para extraer código si es necesario)
           
        Returns:
            bool: True si la carga fue exitosa
        """
        logger.info(f"📦 Cargando datos para el código: {codigo}")
        connection = self.db_connection.get_connection()
        if not connection:
            return False
           
        handler = DataHandler(self.db_connection)
        
        # Determinar si debemos intentar extraer el código del archivo
        should_extract = file_path is not None
        return handler.insert_data(data, codigo, file_path, should_extract=should_extract)
    
    def load_data_standard(self, data, codigo, nombre_archivo="ETL_STANDARD"):
        """
        Carga datos en modo estándar sin archivo específico
        
        Args:
            data: DataFrame con los datos transformados
            codigo: Código del cliente
            nombre_archivo: Nombre del archivo (por defecto ETL_STANDARD)
            
        Returns:
            bool: True si la carga fue exitosa
        """
        handler = DataHandler(self.db_connection)
        
        # Para el modo estándar, pasar un file_path simulado para el nombre
        simulated_path = nombre_archivo if nombre_archivo != "ETL_STANDARD" else None
        cliente_id = handler.get_or_create_codigo_id(codigo, simulated_path, should_extract=False)
        
        if not cliente_id:
            logger.error("No se pudo obtener/crear el ID del cliente")
            return False
            
        return handler.insert_data_direct(data, cliente_id)
