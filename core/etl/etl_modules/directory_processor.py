# ============================================
# core/etl/processors/directory_processor.py
# ============================================
import os
from datetime import datetime
from config.logger import logger
from core.extractors.file_extractor import FileExtractor

class DirectoryProcessor:
    """Procesador especializado para directorios"""
    
    def __init__(self, config, registry, file_processor):
        self.config = config
        self.registry = registry
        self.file_processor = file_processor
    
    def process_directory(self, directory, force_reprocess, data_transformer, data_loader):
        """
        Procesa todos los archivos de un directorio con control de registro
        
        Args:
            directory: Directorio a procesar. Si es None, usa el configurado en config
            force_reprocess: Si True, ignora el registro y procesa todos los archivos
            data_transformer: Instancia del transformador de datos
            data_loader: Instancia del cargador de datos
            
        Returns:
            bool: True si se procesaron archivos exitosamente (al menos uno)
        """
        start_time = datetime.now()
        
        if directory is None:
            directory = self.config['PATHS']['data_dir']
            
        if not os.path.exists(directory):
            logger.error(f"❌ El directorio {directory} no existe")
            return False
        
        # Obtener archivos a procesar
        files = self._get_files_to_process(directory, force_reprocess)
        
        if not files:
            self._handle_no_files(directory, force_reprocess)
            return True
        
        # Procesar archivos
        success_count = self._process_files(files, force_reprocess, data_transformer, data_loader)
        
        # Registrar tiempo total del batch
        self._register_batch_time(start_time)
        
        # Log resultado final
        total_files = len(files)
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        logger.info(f"📈 Resultado final: {success_count}/{total_files} archivos procesados con éxito en {total_time:.2f} segundos")
        
        return success_count > 0
    
    def _get_files_to_process(self, directory, force_reprocess):
        """Obtiene la lista de archivos a procesar"""
        file_extractor = FileExtractor(self.config, self.registry.registry_file)
        
        if force_reprocess:
            files = file_extractor.find_files_in_directory(directory)
            logger.info(f"🔄 Modo de reprocesamiento forzado: procesando todos los archivos")
        else:
            files = file_extractor.find_files_to_process(directory)
        
        return files
    
    def _handle_no_files(self, directory, force_reprocess):
        """Maneja el caso cuando no hay archivos para procesar"""
        if not force_reprocess:
            logger.info(f"ℹ️ No se encontraron archivos nuevos para procesar en {directory}")
        else:
            logger.warning(f"⚠️ No se encontraron archivos para procesar en {directory}")
    
    def _process_files(self, files, force_reprocess, data_transformer, data_loader):
        """Procesa la lista de archivos"""
        total_files = len(files)
        logger.info(f"📄 {total_files} archivos encontrados para procesamiento")

        success_count = 0
        for i, file_path in enumerate(files, start=1):
            logger.info(f"📂 ({i}/{total_files}) Procesando: {os.path.basename(file_path)}")
            if self.file_processor.process_file(file_path, force_reprocess, data_transformer, data_loader):
                success_count += 1
        
        return success_count
    
    def _register_batch_time(self, start_time):
        """Registra el tiempo total del batch"""
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        self.registry.register_batch_processing_time(total_time, start_time, end_time)
