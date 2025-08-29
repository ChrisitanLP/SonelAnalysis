import os
from datetime import datetime
from config.logger import logger
from config.settings import load_config
from core.database.connection import DatabaseConnection
from core.utils.processing_registry import ProcessingRegistry
from core.etl.etl_modules.file_processor import FileProcessor
from core.etl.etl_modules.directory_processor import DirectoryProcessor
from core.etl.etl_modules.data_extractor import DataExtractor
from core.etl.etl_modules.data_transformer import DataTransformer
from core.etl.etl_modules.data_loader import DataLoader
from core.etl.etl_modules.summary_generator import SummaryGenerator

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
        export_dir = self.config['PATHS']['export_dir']
        self.registry_file = registry_file or os.path.join(export_dir, "registro_procesamiento.json")
        self.registry = ProcessingRegistry(self.registry_file)
        
        # Inicializar componentes especializados
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa los componentes especializados del ETL"""
        self.data_extractor = DataExtractor(self.config, self.registry_file)
        self.data_transformer = DataTransformer()
        self.data_loader = DataLoader(self.db_connection)
        self.file_processor = FileProcessor(self.config, self.registry)
        self.directory_processor = DirectoryProcessor(self.config, self.registry, self.file_processor)
        self.summary_generator = SummaryGenerator(self.registry, self.config)
    
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
        return self._run_standard_etl(extraction_method, force_reprocess)
    
    def _run_standard_etl(self, extraction_method, force_reprocess):
        """Ejecuta el proceso ETL estándar"""
        # Paso 1: Extracción
        logger.info("📥 Iniciando extracción de datos")
        extracted_data = self.data_extractor.extract_data(extraction_method, force_reprocess)
        if extracted_data is None:
            logger.info("ℹ️ No hay datos nuevos para procesar")
            return True
           
        # Paso 2: Transformación
        logger.info("🔧 Iniciando transformación de datos")
        transformed_data = self.data_transformer.transform_data(extracted_data)
        if transformed_data is None:
            logger.error("❌ Fallo en la fase de transformación de datos")
            return False
           
        # Paso 3: Carga
        logger.info("⬆️ Cargando datos transformados a la base de datos")
        cliente_codigo = "ETL_STANDARD"
        load_success = self.data_loader.load_data_standard(transformed_data, cliente_codigo)
        if not load_success:
            logger.error("❌ Fallo en la fase de carga de datos")
            return False
           
        logger.info("✅ Proceso ETL completado exitosamente")
        return True
    
    def process_file(self, file_path, force_reprocess=False):
        """Procesa un archivo individual"""
        return self.file_processor.process_file(file_path, force_reprocess, 
                                               self.data_transformer, self.data_loader)
    
    def process_directory(self, directory=None, force_reprocess=False):
        """Procesa todos los archivos de un directorio"""
        result = self.directory_processor.process_directory(directory, force_reprocess, 
                                                           self.data_transformer, self.data_loader)
        
        # Generar y guardar resumen después del procesamiento
        output_file = self.save_processing_summary_to_file()
        if output_file:
            print(f"Resumen guardado en: {output_file}")
        
        # Mostrar resumen del registro
        self.print_processing_summary()
        
        return result
    
    def print_processing_summary(self):
        """Imprime un resumen del estado del procesamiento"""
        self.summary_generator.print_processing_summary()
    
    def reset_file_processing(self, file_path):
        """Reinicia el estado de procesamiento de un archivo específico"""
        self.file_processor.reset_file_processing(file_path)
    
    def get_processing_report(self):
        """Obtiene un reporte detallado del procesamiento"""
        return self.summary_generator.get_processing_report()
    
    def get_db_summary_for_gui(self):
        """Genera un resumen estructurado para la GUI después del procesamiento ETL"""
        return self.summary_generator.get_db_summary_for_gui()

    def get_csv_summary_for_gui(self):
        """Genera un resumen estructurado para CSV/extracción GUI"""
        return self.summary_generator.get_csv_summary_for_gui()

    def get_complete_summary_for_gui(self):
        """Genera un resumen completo combinando CSV y BD"""
        return self.summary_generator.get_complete_summary_for_gui()

    def save_processing_summary_to_file(self, output_file=None, include_files_detail=True):
        """Guarda un resumen completo del procesamiento ETL en un archivo JSON"""
        return self.summary_generator.save_processing_summary_to_file(output_file, include_files_detail)
    
    def close(self):
        """Cierra las conexiones y recursos"""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()
            logger.info("🧹 Recursos de ETL liberados correctamente")
