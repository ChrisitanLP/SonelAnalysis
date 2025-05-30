#sonel_etl.py
import os
import glob
from config.logger import logger
from config.settings import load_config
from database.connection import DatabaseConnection
from database.operations import DataHandler
from extractors.file_extractor import FileExtractor
from extractors.gui_extractor import GUIExtractor
from transformers.voltage_transformer import VoltageTransformer
from utils.validators import extract_client_code

class SonelETL:
    """Clase orquestadora del proceso ETL completo"""
    
    def __init__(self, config_file='config.ini', db_connection=None):
        """
        Inicializa el orquestador ETL
       
        Args:
            config_file: Ruta al archivo de configuración
            db_connection: Conexión a base de datos existente (opcional)
        """
        logger.info("🚀 Inicializando proceso ETL de Sonel")
        self.config = load_config(config_file)
        
        # Usar conexión proporcionada o crear una nueva
        if db_connection:
            self.db_connection = db_connection
        else:
            self.db_connection = DatabaseConnection(self.config)
    
    def run(self, extraction_method='file', directory=None, file_path=None):
        """
        Ejecuta el proceso completo de ETL
       
        Args:
            extraction_method: Método de extracción ('file' o 'gui')
            directory: Directorio específico a procesar (opcional)
            file_path: Ruta específica a un archivo a procesar (opcional)
           
        Returns:
            bool: True si el proceso fue exitoso
        """
        logger.info(f"🔁 Iniciando ejecución de ETL con método: {extraction_method}")

        # Si se proporciona un archivo específico, procesarlo directamente
        if file_path:
            logger.info(f"Procesando archivo específico: {file_path}")
            return self.process_file(file_path)
            
        # Si se proporciona directorio, procesarlo directamente
        if directory or extraction_method == 'file':
            process_dir = directory if directory else self.config['PATHS']['data_dir']
            
            if not os.path.exists(process_dir):
                logger.error(f"❌ El directorio {process_dir} no existe")
                return False
                
            return self.process_directory(process_dir)
        
        # Proceso ETL estándar
        # Paso 1: Extracción
        logger.info("📥 Iniciando extracción de datos")
        extracted_data = self._extract_data(extraction_method)
        if extracted_data is None:
            logger.error("❌ Fallo en la fase de extracción de datos")
            return False
           
        # Paso 2: Transformación
        logger.info("🔧 Iniciando transformación de datos")
        transformed_data = self._transform_data(extracted_data)
        if transformed_data is None:
            logger.error("❌ Fallo en la fase de transformación de datos")
            return False
           
        # Paso 3: Carga
        # En el flujo estándar, usamos un código genérico ya que no tenemos archivo
        # del cual extraer el código
        cliente_codigo = "ETL_STANDARD"
        # Importante: Como no hay archivo, no intentamos extraer código de él
        handler = DataHandler(self.db_connection)
        cliente_id = handler.get_or_create_codigo_id(cliente_codigo, None, should_extract=False)
        
        if not cliente_id:
            logger.error("❌ No se pudo obtener/crear el ID del cliente")
            return False
            
        # Ahora cargamos los datos con el ID ya obtenido
        logger.info(f"⬆️ Cargando datos transformados a la base de datos para cliente {cliente_codigo}")
        load_success = handler.insert_data_direct(transformed_data, cliente_id)
        if not load_success:
            logger.error("❌ Fallo en la fase de carga de datos")
            return False
           
        logger.info("✅ Proceso ETL completado exitosamente")
        return True
    
    def _extract_data(self, method):
        """
        Ejecuta el paso de extracción según el método especificado
       
        Args:
            method: Método de extracción ('file' o 'gui')
           
        Returns:
            DataFrame con los datos extraídos o None si hay error
        """
        if method == 'file':
            extractor = FileExtractor(self.config)
        elif method == 'gui':
            extractor = GUIExtractor(self.config)
        else:
            logger.error(f"Método de extracción no válido: {method}")
            return None
           
        return extractor.extract()
    
    def _transform_data(self, data):
        """
        Ejecuta el paso de transformación de datos
        
        Args:
            data: DataFrame con los datos extraídos
            
        Returns:
            DataFrame transformado o None si hay error
        """
        return VoltageTransformer.transform(data)
    
    def _load_data(self, data, codigo, file_path):
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
    
    def close(self):
        """Cierra las conexiones y recursos"""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()
            logger.info("🧹 Recursos de ETL liberados correctamente")

    def process_file(self, file_path):
        """
        Procesa un archivo individual
        
        Args:
            file_path: Ruta al archivo a procesar
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            # Validar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"❌ El archivo {file_path} no existe")
                return False
                
            # Registrar la ruta completa para diagnóstico
            logger.info(f"📄 Procesando archivo: {file_path}")
                
            # Extraer datos del archivo según su tipo
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.xlsx':
                from parser.excel_parser import ExcelParser
                df = ExcelParser.parse(file_path)
            elif file_ext == '.csv':
                from parser.csv_parser import CSVParser
                df = CSVParser.parse(file_path)
            else:
                logger.error(f"⚠️ Formato de archivo no soportado: {file_path}")
                return False
            
            if df is None or df.empty:
                logger.error(f"⚠️ No se extrajeron datos del archivo: {file_path}")
                return False
                
            # Transformar datos al formato requerido
            transformed_data = self._transform_data(df)
            
            if transformed_data is None or transformed_data.empty:
                logger.error(f"⚠️ Transformación de datos fallida para archivo: {file_path}")
                return False
                
            # Extraer código del cliente del nombre del archivo
            cliente_codigo = extract_client_code(file_path)
            
            # En el nuevo sistema, la función extract_client_code siempre devuelve un código
            # ya sea extraído o generado automáticamente, pero verificamos por si acaso
            if cliente_codigo is None:
                logger.error(f"❌ No se pudo obtener código de cliente desde el archivo {file_path}")
                return False
            
            logger.info(f"📌 Código de cliente extraído: {cliente_codigo}")
            success = self._load_data(transformed_data, cliente_codigo, file_path)

            if success:
                logger.info(f"✅ Archivo procesado exitosamente: {file_path} | Cliente: {cliente_codigo}")
                return True
            else:
                logger.error(f"❌ Error al cargar datos desde archivo: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error crítico al procesar archivo {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def process_directory(self, directory=None):
        """
        Procesa todos los archivos de un directorio
        
        Args:
            directory: Directorio a procesar. Si es None, usa el configurado en config
            
        Returns:
            bool: True si se procesaron todos los archivos exitosamente
        """
        if directory is None:
            directory = self.config['PATHS']['data_dir']
            
        if not os.path.exists(directory):
            logger.error(f"❌ El directorio {directory} no existe")
            return False
            
        # Buscar todos los archivos compatibles usando el extractor
        file_extractor = FileExtractor(self.config)
        files = file_extractor.find_files_in_directory(directory)
        
        if not files:
            logger.warning(f"⚠️ No se encontraron archivos para procesar en {directory}")
            return True
            
        # Procesar cada archivo - corregido para asegurar que se procesen todos
        total_files = len(files)
        logger.info(f"📄 {total_files} archivos encontrados para procesamiento")

        success_count = 0
        for i, file_path in enumerate(files, start=1):
            logger.info(f"📂 ({i}/{total_files}) Procesando: {os.path.basename(file_path)}")
            if self.process_file(file_path):
                success_count += 1
            else:
                logger.error(f"❌ Fallo al procesar archivo: {file_path}")

        logger.info(f"📈 Resultado final: {success_count}/{total_files} archivos procesados con éxito")
        return success_count > 0