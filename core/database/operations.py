#sonel_extractor/database/operations.py

import re
from config.logger import logger
from core.utils.validators import extract_client_code
from config.settings import (
    CREATE_CODIGO_TABLE_QUERY, CREATE_MEDICIONES_TABLE_QUERY, 
    CREATE_VOLTAJE_MEDICIONES_TABLE_QUERY, CREATE_CORRIENTE_MEDICIONES_TABLE_QUERY, 
    CREATE_POTENCIA_MEDICIONES_TABLE_QUERY, INSERT_CODIGO_QUERY, GET_CODIGO_ID_QUERY,
    INSERT_MEDICION_QUERY, INSERT_VOLTAJE_QUERY, INSERT_CORRIENTE_QUERY, INSERT_POTENCIA_QUERY, 
    CREATE_TABLA_UNICA_QUERY, INSERT_TABLA_UNICA_QUERY
)

class DataHandler:
    """Clase para manejar operaciones de base de datos para la estructura relacional"""
    
    def __init__(self, db_connection):
        """
        Inicializa el manejador de datos
        
        Args:
            db_connection: Objeto de conexión a la base de datos
        """
        self.db_connection = db_connection
        self.ensure_tables_exist()

    def ensure_tables_exist(self):
        """
        Asegura que todas las tablas necesarias existan en la base de datos
        
        Returns:
            bool: True si todas las tablas existen o fueron creadas correctamente
        """
        queries = [
            CREATE_CODIGO_TABLE_QUERY,
            CREATE_MEDICIONES_TABLE_QUERY,
            CREATE_VOLTAJE_MEDICIONES_TABLE_QUERY,
            CREATE_CORRIENTE_MEDICIONES_TABLE_QUERY,
            CREATE_POTENCIA_MEDICIONES_TABLE_QUERY,
            CREATE_TABLA_UNICA_QUERY
        ]
        
        success = True
        for query in queries:
            cursor = self.db_connection.execute_query(query, commit=True)
            if cursor:
                cursor.close()
            else:
                success = False
                logger.error(f"Error al crear tabla con query: {query}")
        
        if success:
            logger.info("Todas las tablas fueron verificadas/creadas correctamente")
        else:
            logger.error("No se pudieron crear todas las tablas necesarias")
        
        return success
    
    def extract_client_code(self, file_path):
        """
        Extrae el código del cliente del nombre del archivo.
        El código siempre son los últimos 10 dígitos del nombre del archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            str: Código de cliente extraído o None si no se pudo extraer
        """
        # Utilizamos la función trasladada a validators.py para mantener consistencia
        return extract_client_code(file_path)
        
    def get_or_create_codigo_id(self, codigo, file_path=None, should_extract=True):
        """
        Obtiene o crea un registro en la tabla código. Si el código recibido es inválido,
        intenta extraerlo nuevamente del nombre del archivo si file_path está disponible.

        Args:
            codigo: Código del cliente (posiblemente extraído previamente)
            file_path: Ruta del archivo (usado si se necesita volver a extraer el código)
            should_extract: Indica si se debe intentar extraer el código del archivo
            
        Returns:
            int: ID del código o None si hay error
        """
        # Verificar si el código es válido
        if codigo is None:
            if should_extract and file_path:
                # Intentar extraer el código del archivo
                logger.warning("No se recibió código. Intentando extraer del archivo.")
                codigo = extract_client_code(file_path)
            
            # Si después del intento sigue siendo inválido
            if codigo is None:
                logger.error("No se pudo obtener un código válido del archivo.")
                return None
        
        # Para el caso del flujo estándar ETL (sin archivo)
        if codigo == "ETL_STANDARD" and not should_extract:
            logger.info(f"Utilizando código estándar ETL: {codigo}")
        else:
            # Con la nueva implementación, el código siempre es numérico
            # pero verificamos para asegurar que sea de 10 dígitos
            if not re.match(r'^\d{10}$', codigo):
                logger.warning(f"El código '{codigo}' no tiene el formato esperado de 10 dígitos.")
                
                if should_extract and file_path:
                    logger.info(f"Intentando extraer código nuevamente del archivo: {file_path}")
                    codigo = extract_client_code(file_path)
                    
                    if not codigo or not re.match(r'^\d{10}$', codigo):
                        logger.error(f"No se pudo obtener un código válido de 10 dígitos después de reintento.")
                        return None
                else:
                    return None

        logger.info(f"Intentando obtener/crear código en BD: '{codigo}'")

        # Primero verificar si ya existe
        cursor = self.db_connection.execute_query(
            GET_CODIGO_ID_QUERY,
            params=(codigo,),
            commit=False
        )

        if cursor:
            row = cursor.fetchone()
            cursor.close()
            if row:
                codigo_id = row[0]
                logger.info(f"Código existente encontrado con ID: {codigo_id}")
                return codigo_id

        # Si no existe, intentar insertarlo
        cursor = self.db_connection.execute_query(
            INSERT_CODIGO_QUERY,
            params=(codigo,),
            commit=True
        )

        if cursor:
            row = cursor.fetchone()
            cursor.close()
            if row:
                codigo_id = row[0]
                logger.info(f"Nuevo código creado con ID: {codigo_id}")
                return codigo_id

        logger.error(f"No se pudo obtener o crear el código: {codigo}")
        return None
    
    def insert_data(self, data, codigo, file_path, should_extract=True):
        """
        Inserta los datos en la estructura relacional de tablas
        
        Args:
            data: DataFrame con los datos transformados
            codigo: Código del cliente
            file_path: Ruta del archivo (para extraer código si es necesario)
            should_extract: Indica si se debe intentar extraer el código del archivo
            
        Returns:
            bool: True si la inserción fue exitosa
        """
        if data is None or data.empty:
            logger.error("No hay datos para cargar en la base de datos")
            return False
        
        # Obtener o crear el ID del código/cliente
        codigo_id = self.get_or_create_codigo_id(codigo, file_path, should_extract)
        if codigo_id is None:
            logger.error("No se pudo obtener un ID válido para el código. Datos no insertados.")
            return False
            
        # Utilizar la función para insertar datos con el código ya obtenido
        return self.insert_data_direct(data, codigo_id)
    
    def insert_data_direct(self, data, codigo_id):
        """
        Inserta datos utilizando un ID de código ya obtenido
        
        Args:
            data: DataFrame con los datos transformados
            codigo_id: ID del código/cliente ya obtenido
            
        Returns:
            bool: True si la inserción fue exitosa
        """
        if data is None or data.empty:
            logger.error("No hay datos para cargar en la base de datos")
            return False
                  
        # Contador de filas procesadas exitosamente
        successful_rows = 0
        
        # Procesar cada fila e insertarla en las tablas correspondientes
        for index, row in data.iterrows():
            try:
                # 1. Insertar en tabla mediciones y obtener ID
                medicion_cursor = self.db_connection.execute_query(
                    INSERT_MEDICION_QUERY,
                    params=(codigo_id, row.get('tiempo_utc'), ),
                    commit=False  # No hacemos commit aún
                )
                
                if not medicion_cursor:
                    logger.error(f"Error al insertar en tabla mediciones, fila {index}")
                    continue
                
                medicion_id = medicion_cursor.fetchone()[0]
                medicion_cursor.close()
                
                # 2. Insertar en tabla voltaje_mediciones
                voltaje_cursor = self.db_connection.execute_query(
                    INSERT_VOLTAJE_QUERY,
                    params=(
                        row.get('u_l1_avg_10min'),
                        row.get('u_l2_avg_10min'),
                        row.get('u_l3_avg_10min'),
                        row.get('u_l12_avg_10min'),
                        medicion_id
                    ),
                    commit=False
                )
                
                if not voltaje_cursor:
                    logger.error(f"Error al insertar en tabla voltaje_mediciones, fila {index}")
                    self.db_connection.connection.rollback()
                    continue
                
                voltaje_cursor.close()
                
                # 3. Insertar en tabla corriente_mediciones con valores predeterminados o nulos
                corriente_cursor = self.db_connection.execute_query(
                    INSERT_CORRIENTE_QUERY,
                    params=(
                        row.get('i_l1_avg', None),
                        row.get('i_l2_avg', None),
                        medicion_id
                    ),
                    commit=False
                )
                
                if not corriente_cursor:
                    logger.error(f"Error al insertar en tabla corriente_mediciones, fila {index}")
                    self.db_connection.connection.rollback()
                    continue
                
                corriente_cursor.close()
                
                # 4. Insertar en tabla potencia_mediciones con valores predeterminados o nulos
                potencia_cursor = self.db_connection.execute_query(
                    INSERT_POTENCIA_QUERY,
                    params= (
                        row.get('p_l1_avg', None),
                        row.get('p_l2_avg', None),
                        row.get('p_l3_avg', None),
                        row.get('p_e_avg', None),
                        row.get('q1_l1_avg', None),
                        row.get('q1_l2_avg', None),
                        row.get('q1_e_avg', None),
                        row.get('sn_l1_avg', None),
                        row.get('sn_l2_avg', None),
                        row.get('sn_e_avg', None),
                        row.get('s_l1_avg', None),
                        row.get('s_l2_avg', None),
                        row.get('s_e_avg', None),
                        medicion_id
                    ),
                    commit=False
                )
                
                if not potencia_cursor:
                    logger.error(f"Error al insertar en tabla potencia_mediciones, fila {index}")
                    self.db_connection.connection.rollback()
                    continue
                
                potencia_cursor.close()

                cursor = self.db_connection.execute_query(
                    INSERT_TABLA_UNICA_QUERY,
                    params=(
                        codigo_id,
                        row.get('tiempo_utc'),
                        row.get('u_l1_avg_10min'),
                        row.get('u_l2_avg_10min'),
                        row.get('u_l3_avg_10min'),
                        row.get('u_l12_avg_10min'),
                        row.get('i_l1_avg'),
                        row.get('i_l2_avg'),
                        row.get('p_l1_avg'),
                        row.get('p_l2_avg'),
                        row.get('p_l3_avg'),
                        row.get('p_e_avg'),
                        row.get('q1_l1_avg'),
                        row.get('q1_l2_avg'),
                        row.get('q1_e_avg'),
                        row.get('sn_l1_avg'),
                        row.get('sn_l2_avg'),
                        row.get('sn_e_avg'),
                        row.get('s_l1_avg'),
                        row.get('s_l2_avg'),
                        row.get('s_e_avg')
                    ),
                    commit=True
                )

                if not cursor:
                    logger.error(f"Fallo al insertar fila {index} en tabla única")
                    self.db_connection.connection.rollback()
                    continue
                
                cursor.close()

                # Hacer commit de toda la transacción para esta fila
                self.db_connection.connection.commit()
                successful_rows += 1
                
            except Exception as e:
                logger.error(f"Error al procesar la fila {index}: {e}")
                self.db_connection.connection.rollback()
        
        logger.info(f"Datos cargados exitosamente en la BD: {successful_rows}/{len(data)} filas")
        return successful_rows > 0