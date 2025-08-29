# ============================================
# core/etl/processors/directory_processor.py
# ============================================
import os
from datetime import datetime
from config.logger import logger
from core.extractors.file_extractor import FileExtractor
from core.utils.processing_registry import ProcessingStatus

class DirectoryProcessor:
    """Procesador especializado para directorios"""
    
    def __init__(self, config, registry, file_processor):
        self.config = config
        self.registry = registry
        self.file_processor = file_processor
        self.failed_files = None
    
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
        success_count, failed_files = self._process_files(files, force_reprocess, data_transformer, data_loader)
        
        # Registrar tiempo total del batch
        self._register_batch_time(start_time)
        
        # Log resultado final
        total_files = len(files)
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        logger.info(f"📈 Resultado final: {success_count}/{total_files} archivos procesados con éxito en {total_time:.2f} segundos")
        
        if failed_files:
            logger.warning(f"❌ Archivos que no se pudieron procesar ({len(failed_files)}):")
            for path in failed_files:
                logger.warning(f"   - {os.path.basename(path)}")

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
        failed_files = []

        for i, file_path in enumerate(files, start=1):
            logger.info(f"📂 ({i}/{total_files}) Procesando: {os.path.basename(file_path)}")
            if self.file_processor.process_file(file_path, force_reprocess, data_transformer, data_loader):
                success_count += 1
            else:
                failed_files.append(file_path)
                logger.warning(f"❌ Error al procesar: {os.path.basename(file_path)}")
                
                # NUEVA LÓGICA: Registrar el archivo como fallido en el registry
                # Solo si no está ya registrado con estado ERROR
                if not self.registry.is_file_registered_with_status(file_path, ProcessingStatus.ERROR):
                    # Registrar inicio si no existe
                    if os.path.abspath(file_path) not in self.registry.registry_data.get("files", {}):
                        self.registry.register_processing_start(file_path)
                    
                    # Registrar el error
                    error_message = f"Error en procesamiento de directorio - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    additional_info = {
                        "processing_time_seconds": 0,
                        "file_size_bytes": 0,
                        "error_type": "directory_processing_failure"
                    }
                    
                    try:
                        # Intentar obtener tamaño del archivo
                        if os.path.exists(file_path):
                            additional_info["file_size_bytes"] = os.path.getsize(file_path)
                    except:
                        pass
                    
                    self.registry.register_processing_error(file_path, error_message, additional_info)

        # Guardar o exponer lista de fallos si lo deseas externamente
        self.failed_files = failed_files
        
        return success_count, failed_files
    
    def _register_batch_time(self, start_time):
        """Registra el tiempo total del batch"""
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        self.registry.register_batch_processing_time(total_time, start_time, end_time)
