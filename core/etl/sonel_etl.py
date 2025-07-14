#sonel_etl.py
import os
from config.logger import logger
from config.settings import load_config
from core.database.operations import DataHandler
from core.utils.validators import extract_client_code
from core.database.connection import DatabaseConnection
from core.extractors.file_extractor import FileExtractor
from core.extractors.pygui_extractor import GUIExtractor
from core.transformers.voltage_transformer import VoltageTransformer
from core.utils.processing_registry import ProcessingRegistry, ProcessingStatus

class SonelETL:
    """Clase orquestadora del proceso ETL completo con control de procesamiento"""
    
    def __init__(self, config_file='config.ini', db_connection=None, registry_file=None):
        """
        Inicializa el orquestador ETL
       
        Args:
            config_file: Ruta al archivo de configuración
            db_connection: Conexión a base de datos existente (opcional)
            registry_file: Archivo de registro personalizado (opcional)
        """
        logger.info("🚀 Inicializando proceso ETL de Sonel")
        self.config = load_config(config_file)
        
        # Usar conexión proporcionada o crear una nueva
        if db_connection:
            self.db_connection = db_connection
        else:
            self.db_connection = DatabaseConnection(self.config)
        
        # Inicializar registro de procesamiento
        data_dir = self.config['PATHS']['data_dir']
        self.registry_file = registry_file or os.path.join(data_dir, "registro_procesamiento.json")
        self.registry = ProcessingRegistry(self.registry_file)
    
    def run(self, extraction_method='file', directory=None, file_path=None, force_reprocess=False):
        """
        Ejecuta el proceso completo de ETL con control de procesamiento
       
        Args:
            extraction_method: Método de extracción ('file' o 'gui')
            directory: Directorio específico a procesar (opcional)
            file_path: Ruta específica a un archivo a procesar (opcional)
            force_reprocess: Si True, ignora el registro y procesa todos los archivos
           
        Returns:
            bool: True si el proceso fue exitoso
        """
        logger.info(f"🔁 Iniciando ejecución de ETL con método: {extraction_method}")
        
        # Limpiar archivos inexistentes del registro al inicio
        cleaned_count = self.registry.cleanup_missing_files()
        if cleaned_count > 0:
            logger.info(f"🧹 Limpieza de registro: {cleaned_count} archivos inexistentes eliminados")

        # Si se proporciona un archivo específico, procesarlo directamente
        if file_path:
            logger.info(f"Procesando archivo específico: {file_path}")
            return self.process_file(file_path, force_reprocess=force_reprocess)
            
        # Si se proporciona directorio, procesarlo directamente
        if directory or extraction_method == 'file':
            process_dir = directory if directory else self.config['PATHS']['data_dir']
            
            if not os.path.exists(process_dir):
                logger.error(f"❌ El directorio {process_dir} no existe")
                return False
                
            return self.process_directory(process_dir, force_reprocess=force_reprocess)
        
        # Proceso ETL estándar con extractor
        # Paso 1: Extracción
        logger.info("📥 Iniciando extracción de datos")
        extracted_data = self._extract_data(extraction_method, force_reprocess)
        if extracted_data is None:
            logger.info("ℹ️ No hay datos nuevos para procesar")
            return True  # No es un error, simplemente no hay archivos nuevos
           
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
    
    def _extract_data(self, method, force_reprocess=False):
        """
        Ejecuta el paso de extracción según el método especificado
       
        Args:
            method: Método de extracción ('file' o 'gui')
            force_reprocess: Si True, ignora el registro y procesa todos los archivos
           
        Returns:
            DataFrame con los datos extraídos o None si hay error
        """
        if method == 'file':
            extractor = FileExtractor(self.config, self.registry_file)
            if force_reprocess:
                return extractor.extract_all_files(force_reprocess=True)
            else:
                return extractor.extract()
        elif method == 'gui':
            extractor = GUIExtractor(self.config)
            return extractor.extract()
        else:
            logger.error(f"Método de extracción no válido: {method}")
            return None
    
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

    def process_file(self, file_path, force_reprocess=False):
        """
        Procesa un archivo individual con control de registro
        
        Args:
            file_path: Ruta al archivo a procesar
            force_reprocess: Si True, ignora el registro y procesa el archivo
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        try:
            # Validar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"❌ El archivo {file_path} no existe")
                return False
            
            # Verificar si el archivo debe ser procesado (a menos que sea forzado)
            if not force_reprocess:
                should_process, reason = self.registry.should_process_file(file_path)
                if not should_process:
                    self.registry.register_processing_skipped(file_path, reason)
                    logger.info(f"⏭️  Archivo omitido: {os.path.basename(file_path)} - {reason}")
                    return True  # No es un error, simplemente se omitió
            
            # Registrar inicio del procesamiento
            cliente_codigo = extract_client_code(file_path)
            self.registry.register_processing_start(file_path, cliente_codigo)
            
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
                error_msg = f"Formato de archivo no soportado: {file_path}"
                self.registry.register_processing_error(file_path, error_msg)
                logger.error(f"⚠️ {error_msg}")
                return False
            
            if df is None or df.empty:
                error_msg = f"No se extrajeron datos del archivo: {file_path}"
                self.registry.register_processing_error(file_path, error_msg)
                logger.error(f"⚠️ {error_msg}")
                return False
                
            # Transformar datos al formato requerido
            transformed_data = self._transform_data(df)
            
            if transformed_data is None or transformed_data.empty:
                error_msg = f"Transformación de datos fallida para archivo: {file_path}"
                self.registry.register_processing_error(file_path, error_msg)
                logger.error(f"⚠️ {error_msg}")
                return False
            
            # En el nuevo sistema, la función extract_client_code siempre devuelve un código
            # ya sea extraído o generado automáticamente, pero verificamos por si acaso
            if cliente_codigo is None:
                error_msg = f"No se pudo obtener código de cliente desde el archivo {file_path}"
                self.registry.register_processing_error(file_path, error_msg)
                logger.error(f"❌ {error_msg}")
                return False
            
            logger.info(f"📌 Código de cliente extraído: {cliente_codigo}")
            success = self._load_data(transformed_data, cliente_codigo, file_path)

            if success:
                # Registrar éxito con información adicional
                additional_info = {
                    "rows_processed": len(transformed_data),
                    "columns_processed": len(transformed_data.columns) if hasattr(transformed_data, 'columns') else 0,
                    "client_code": cliente_codigo
                }
                self.registry.register_processing_success(file_path, additional_info)
                logger.info(f"✅ Archivo procesado exitosamente: {file_path} | Cliente: {cliente_codigo}")
                return True
            else:
                error_msg = f"Error al cargar datos desde archivo: {file_path}"
                self.registry.register_processing_error(file_path, error_msg)
                logger.error(f"❌ {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Error crítico al procesar archivo {file_path}: {e}"
            self.registry.register_processing_error(file_path, error_msg)
            logger.error(f"❌ {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def process_directory(self, directory=None, force_reprocess=False):
        """
        Procesa todos los archivos de un directorio con control de registro
        
        Args:
            directory: Directorio a procesar. Si es None, usa el configurado en config
            force_reprocess: Si True, ignora el registro y procesa todos los archivos
            
        Returns:
            bool: True si se procesaron archivos exitosamente (al menos uno)
        """
        if directory is None:
            directory = self.config['PATHS']['data_dir']
            
        if not os.path.exists(directory):
            logger.error(f"❌ El directorio {directory} no existe")
            return False
            
        # Buscar archivos usando el extractor con control de registro
        file_extractor = FileExtractor(self.config, self.registry_file)
        
        if force_reprocess:
            files = file_extractor.find_files_in_directory(directory)
            logger.info(f"🔄 Modo de reprocesamiento forzado: procesando todos los archivos")
        else:
            files = file_extractor.find_files_to_process(directory)
        
        if not files:
            if not force_reprocess:
                logger.info(f"ℹ️ No se encontraron archivos nuevos para procesar en {directory}")
                # Mostrar estadísticas del registro
                self.print_processing_summary()
            else:
                logger.warning(f"⚠️ No se encontraron archivos para procesar en {directory}")
            return True  # No hay archivos nuevos no es un error
            
        # Procesar cada archivo
        total_files = len(files)
        logger.info(f"📄 {total_files} archivos encontrados para procesamiento")

        success_count = 0
        for i, file_path in enumerate(files, start=1):
            logger.info(f"📂 ({i}/{total_files}) Procesando: {os.path.basename(file_path)}")
            if self.process_file(file_path, force_reprocess=force_reprocess):
                success_count += 1
            # No registramos errores aquí porque ya se hace en process_file

        logger.info(f"📈 Resultado final: {success_count}/{total_files} archivos procesados con éxito")
        
        # Mostrar resumen del registro
        self.print_processing_summary()
        
        return success_count > 0
    
    def print_processing_summary(self):
        """Imprime un resumen del estado del procesamiento"""
        stats = self.registry.get_processing_stats()
        
        logger.info("📊 === RESUMEN DE PROCESAMIENTO ===")
        logger.info(f"Total de archivos registrados: {stats['total_files']}")
        logger.info(f"Procesados exitosamente: {stats['successful']}")
        logger.info(f"Con errores: {stats['errors']}")
        logger.info(f"Pendientes: {stats['pending']}")
        
        # Mostrar archivos con errores recientes si los hay
        if stats['errors'] > 0:
            error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
            logger.info(f"❌ Archivos con errores recientes ({min(3, len(error_files))} de {len(error_files)}):")
            for file_path in error_files[:3]:
                file_data = self.registry.registry_data["files"][file_path]
                error_msg = file_data.get("error_message", "Sin mensaje")[:100]  # Limitar longitud
                logger.info(f"  - {os.path.basename(file_path)}: {error_msg}...")
    
    def reset_file_processing(self, file_path):
        """
        Reinicia el estado de procesamiento de un archivo específico
        
        Args:
            file_path: Ruta al archivo
        """
        file_extractor = FileExtractor(self.config, self.registry_file)
        file_extractor.reset_file_status(file_path)
        logger.info(f"🔄 Estado de procesamiento reiniciado para: {os.path.basename(file_path)}")
    
    def get_processing_report(self):
        """
        Obtiene un reporte detallado del procesamiento
        
        Returns:
            dict: Reporte con estadísticas y detalles
        """
        stats = self.registry.get_processing_stats()
        
        # Obtener archivos por estado
        from utils.processing_registry import ProcessingStatus
        error_files = self.registry.get_files_by_status(ProcessingStatus.ERROR)
        pending_files = self.registry.get_files_by_status(ProcessingStatus.PENDING)
        
        report = {
            "statistics": stats,
            "error_files": [
                {
                    "file": os.path.basename(f),
                    "error": self.registry.registry_data["files"][f].get("error_message", "Sin mensaje")
                } for f in error_files[:10]  # Solo los primeros 10
            ],
            "pending_files": [os.path.basename(f) for f in pending_files[:10]],
            "registry_file": self.registry_file
        }
        
        return report