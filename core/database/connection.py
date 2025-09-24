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
        self._connection_attempts = 0
        self._max_attempts = 3
        
    def connect(self):
        """
        Establece conexión con la base de datos PostgreSQL de forma portable
        
        Returns:
            Connection: Objeto de conexión a la base de datos o None si hay error
        """
        try:
            # MODIFICACIÓN: Manejo más robusto de configuración
            db_config = self._get_database_config()
            
            self.connection = psycopg2.connect(
                host=db_config['host'],
                port=int(db_config['port']),
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                connect_timeout=15,  # Timeout de 10 segundos
                application_name="SonelExtractor_Portable"
            )
            
            # Verificar que la conexión funcione
            cursor = self.connection.cursor()
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()
            cursor.close()
            
            logger.info("✅ Conexión exitosa a PostgreSQL")
            
            # Resetear contador de intentos en caso de éxito
            self._connection_attempts = 0
            return self.connection
            
        except ImportError as e:
            logger.error("❌ Error de dependencias de base de datos")
            logger.error(f"Instala las dependencias necesarias: {e}")
            return None
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Mensajes de error específicos y amigables
            if "could not connect to server" in error_msg:
                logger.error("❌ No se pudo conectar al servidor PostgreSQL")
                logger.error("   Verifica que PostgreSQL esté ejecutándose")
                logger.error(f"   Host configurado: {db_config.get('host', 'N/A')}")
                logger.error(f"   Puerto configurado: {db_config.get('port', 'N/A')}")
            elif "authentication failed" in error_msg:
                logger.error("❌ Error de autenticación con la base de datos")
                logger.error("   Verifica usuario y contraseña en la configuración")
            elif "database" in error_msg and "does not exist" in error_msg:
                logger.error("❌ La base de datos especificada no existe")
                logger.error(f"   Base de datos: {db_config.get('database', 'N/A')}")
            elif "timeout" in error_msg:
                logger.error("❌ Timeout de conexión - El servidor no responde")
                logger.error("   Verifica conectividad de red y firewall")
            else:
                logger.error(f"❌ Error de conexión PostgreSQL: {e}")
                
            # Sugerir acciones según el número de intentos
            if self._connection_attempts < self._max_attempts:
                logger.info(f"Reintentando conexión... ({self._connection_attempts}/{self._max_attempts})")
            else:
                logger.error("❌ Se agotaron los intentos de conexión")
                logger.error("   La aplicación continuará sin funcionalidad de base de datos")
                
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
        if self.config and hasattr(self.config, 'sections'):
        # ConfigParser object
            if 'DATABASE' in self.config:
                for key in defaults.keys():
                    if key in self.config['DATABASE']:
                        value = self.config['DATABASE'][key]
                        if value and value.strip():  # Validar que no esté vacío
                            config[key] = value.strip()
        elif self.config and isinstance(self.config, dict):
            # Dictionary object
            if 'DATABASE' in self.config:
                for key in defaults.keys():
                    if key in self.config['DATABASE']:
                        value = self.config['DATABASE'][key]
                        if value and str(value).strip():
                            config[key] = str(value).strip()
        
        # Sobrescribir con variables de entorno (máxima prioridad)
        import os
        for key, env_var in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value and env_value.strip():
                config[key] = env_value.strip()
        
        # Validar configuración
        for key, value in config.items():
            if not value or not str(value).strip():
                logger.warning(f"⚠️ Configuración BD '{key}' vacía, usando valor por defecto")
                config[key] = defaults[key]
        
        # Validar puerto numérico
        try:
            port = int(config['port'])
            if port < 1 or port > 65535:
                raise ValueError(f"Puerto fuera de rango: {port}")
            config['port'] = str(port)
        except ValueError as e:
            logger.warning(f"⚠️ Puerto inválido ({config['port']}), usando 5432")
            config['port'] = '5432'
        
        return config

    def get_connection(self):
        """
        Devuelve la conexión existente o crea una nueva si no existe
        
        Returns:
            Connection: Objeto de conexión a la base de datos
        """
        if self.connection:
            try:
                # Test rápido de la conexión existente
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return self.connection
            except Exception as e:
                logger.warning(f"⚠️ Conexión existente inválida: {e}")
                self.connection = None
        
        # Si no hay conexión válida, intentar crear una nueva
        if not self.connection and self._connection_attempts < self._max_attempts:
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
            try:
                self.connection.close()
                self.connection = None
                logger.info("✅ Conexión a la base de datos cerrada")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando conexión BD: {e}")
        else:
            logger.debug("No hay conexión BD que cerrar")