#sonel_extractor/database/connection.py
import os
import psycopg2
from config.logger import logger

class DatabaseConnection:
    """Clase para gestionar la conexión a la base de datos PostgreSQL"""

    def __init__(self, config):
        """
        Inicializa el objeto de conexión a la base de datos
        
        Args:
            config: Objeto de configuración con parámetros de base de datos
        """
        self.config = config
        self.connection = None
        
    def connect(self):
        """
        Establece conexión con la base de datos PostgreSQL
        
        Returns:
            Connection: Objeto de conexión a la base de datos o None si hay error
        """
        try:
            # Priorizar variables de entorno si existen
            host = os.getenv('DB_HOST') or self.config['DATABASE']['host']
            port = os.getenv('DB_PORT') or self.config['DATABASE']['port']
            database = os.getenv('DB_NAME') or self.config['DATABASE']['database']
            user = os.getenv('DB_USER') or self.config['DATABASE']['user']
            password = os.getenv('DB_PASSWORD') or self.config['DATABASE']['password']
            
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            logger.info("Conexión exitosa a la base de datos PostgreSQL")
            return self.connection
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            return None

    def get_connection(self):
        """
        Devuelve la conexión existente o crea una nueva si no existe
        
        Returns:
            Connection: Objeto de conexión a la base de datos
        """
        if not self.connection:
            return self.connect()
        return self.connection

    def execute_query(self, query, params=None, commit=False):
        """
        Ejecuta una consulta SQL
        
        Args:
            query: String con la consulta SQL a ejecutar
            params: Parámetros para la consulta (opcional)
            commit: Si es True, hace commit de la transacción
            
        Returns:
            cursor: Cursor con resultado de la consulta o None si hay error
        """
        if not self.connection:
            self.connect()
            
        if not self.connection:
            logger.error("No hay conexión a la base de datos para ejecutar consulta")
            return None
            
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if commit:
                self.connection.commit()
                
            return cursor
        except Exception as e:
            logger.error(f"Error al ejecutar consulta: {e}")
            if commit:
                self.connection.rollback()
            return None

    def execute_transaction(self, query_list, commit=True):
        """
        Ejecuta múltiples consultas en una transacción
        
        Args:
            query_list: Lista de tuplas (query, params)
            commit: Si es True, hace commit de la transacción
            
        Returns:
            bool: True si la transacción fue exitosa
        """
        if not self.connection:
            self.connect()
            
        if not self.connection:
            logger.error("No hay conexión a la base de datos para la transacción")
            return False
            
        try:
            cursor = self.connection.cursor()
            
            for query, params in query_list:
                cursor.execute(query, params)
                
            if commit:
                self.connection.commit()
                
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Error en la transacción: {e}")
            if commit:
                self.connection.rollback()
            return False

    def close(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Conexión a la base de datos cerrada")