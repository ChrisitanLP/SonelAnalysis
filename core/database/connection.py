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
        Establece conexión con la base de datos PostgreSQL de forma portable
        
        Returns:
            Connection: Objeto de conexión a la base de datos o None si hay error
        """
        try:
            # MODIFICACIÓN: Manejo más robusto de configuración
            db_config = self._get_database_config()
            
            logger.info(f"Intentando conectar a la base de datos: {db_config['host']}:{db_config['port']}")
            
            self.connection = psycopg2.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                connect_timeout=10  # Timeout de 10 segundos
            )
            
            # Verificar que la conexión funcione
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            logger.info("✅ Conexión exitosa a la base de datos PostgreSQL")
            return self.connection
            
        except psycopg2.OperationalError as e:
            error_msg = str(e)
            if "could not connect to server" in error_msg.lower():
                logger.error("❌ No se pudo conectar al servidor PostgreSQL")
                logger.error("   Verifica que PostgreSQL esté ejecutándose y sea accesible")
            elif "authentication failed" in error_msg.lower():
                logger.error("❌ Error de autenticación con la base de datos")
                logger.error("   Verifica las credenciales de usuario y contraseña")
            elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
                logger.error("❌ La base de datos especificada no existe")
                logger.error("   Verifica que la base de datos 'sonel_data' exista")
            else:
                logger.error(f"❌ Error de conexión PostgreSQL: {e}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error inesperado al conectar a la base de datos: {e}")
            return None

    def _get_database_config(self) -> dict:
        """
        NUEVO MÉTODO: Obtiene la configuración de base de datos de forma portable
        
        Returns:
            dict: Configuración de base de datos
        """
        # Prioridad: Variables de entorno > Archivo de configuración > Valores por defecto
        
        # Valores por defecto
        defaults = {
            'host': 'localhost',
            'port': '5432',
            'database': 'sonel_data',
            'user': 'postgres',
            'password': '123456'
        }
        
        # Mapeo de variables de entorno
        env_mapping = {
            'host': 'DB_HOST',
            'port': 'DB_PORT',
            'database': 'DB_NAME',
            'user': 'DB_USER',
            'password': 'DB_PASSWORD'
        }
        
        config = {}
        
        # 1. Partir de valores por defecto
        config.update(defaults)
        
        # 2. Sobrescribir con valores del archivo de configuración si existen
        if self.config and 'DATABASE' in self.config:
            for key in defaults.keys():
                if key in self.config['DATABASE']:
                    config[key] = self.config['DATABASE'][key]
        
        # 3. Sobrescribir con variables de entorno si existen (máxima prioridad)
        for key, env_var in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value:
                config[key] = env_value
                logger.info(f"Usando variable de entorno {env_var} para {key}")
        
        return config

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