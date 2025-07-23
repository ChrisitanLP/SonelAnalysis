
# core/etl/sonel_etl_enhanced.py
"""
Versión mejorada de SonelETL con sistema de callbacks
"""
import os
import time
from datetime import datetime
from config.logger import logger
from core.etl.sonel_etl import SonelETL
from core.extractors.file_extractor import FileExtractor
from core.utils.callbacks import ProcessingCallbackManager, ProcessingEventType

class SonelETLEnhanced(SonelETL):
    """SonelETL mejorado con sistema de callbacks en tiempo real"""
    
    def __init__(self, config_file='config.ini', db_connection=None, registry_file=None, 
                 callback_manager: ProcessingCallbackManager = None):
        """
        Inicializa el ETL mejorado con callbacks
        
        Args:
            callback_manager: Gestor de callbacks para eventos en tiempo real
        """
        super().__init__(config_file, db_connection, registry_file)
        self.callback_manager = callback_manager
    
    def process_directory(self, directory=None, force_reprocess=False):
        """
        Versión mejorada que emite eventos durante el procesamiento
        """
        # Emitir evento de inicio
        if self.callback_manager:
            file_extractor = FileExtractor(self.config, self.registry_file)
            if force_reprocess:
                files = file_extractor.find_files_in_directory(directory or self.config['PATHS']['data_dir'])
            else:
                files = file_extractor.find_files_to_process(directory or self.config['PATHS']['data_dir'])
            
            self.callback_manager.emit_event(ProcessingEventType.PROCESS_STARTED, {
                'total_files': len(files),
                'directory': directory or self.config['PATHS']['data_dir'],
                'force_reprocess': force_reprocess
            })
        
        # Ejecutar procesamiento original pero con eventos
        return self._process_directory_with_callbacks(directory, force_reprocess)
    
    def _process_directory_with_callbacks(self, directory=None, force_reprocess=False):
        """Procesa directorio emitiendo eventos"""
        start_time = datetime.now()
        
        if directory is None:
            directory = self.config['PATHS']['data_dir']
            
        if not os.path.exists(directory):
            logger.error(f"❌ El directorio {directory} no existe")
            if self.callback_manager:
                self.callback_manager.emit_event(ProcessingEventType.PROCESS_FAILED, {
                    'error': f"El directorio {directory} no existe"
                })
            return False
        
        # Buscar archivos
        file_extractor = FileExtractor(self.config, self.registry_file)
        
        if force_reprocess:
            files = file_extractor.find_files_in_directory(directory)
        else:
            files = file_extractor.find_files_to_process(directory)
        
        if not files:
            logger.info(f"ℹ️ No se encontraron archivos para procesar en {directory}")
            if self.callback_manager:
                self.callback_manager.emit_event(ProcessingEventType.PROCESS_COMPLETED, {
                    'files_processed': 0,
                    'success_count': 0
                })
            return True
        
        # Procesar cada archivo
        total_files = len(files)
        success_count = 0
        
        for i, file_path in enumerate(files, start=1):
            filename = os.path.basename(file_path)
            
            # Emitir evento de inicio de archivo
            if self.callback_manager:
                self.callback_manager.emit_event(ProcessingEventType.FILE_STARTED, {
                    'filename': filename,
                    'file_path': file_path,
                    'current_index': i,
                    'total_files': total_files
                })
            
            # Procesar archivo
            file_start_time = time.time()
            success = self.process_file(file_path, force_reprocess=force_reprocess)
            processing_time = time.time() - file_start_time
            
            if success:
                success_count += 1
                # Emitir evento de éxito
                if self.callback_manager:
                    # Obtener información adicional del archivo
                    file_data = self.registry.registry_data.get("files", {}).get(file_path, {})
                    additional_info = file_data.get("additional_info", {})
                    
                    self.callback_manager.emit_event(ProcessingEventType.FILE_COMPLETED, {
                        'filename': filename,
                        'file_path': file_path,
                        'processing_time': processing_time,
                        'records_processed': additional_info.get('rows_processed', 0),
                        'current_index': i,
                        'total_files': total_files,
                        'success_count': success_count
                    })
            else:
                # Emitir evento de error
                if self.callback_manager:
                    file_data = self.registry.registry_data.get("files", {}).get(file_path, {})
                    error_message = file_data.get("error_message", "Error desconocido")
                    
                    self.callback_manager.emit_event(ProcessingEventType.FILE_FAILED, {
                        'filename': filename,
                        'file_path': file_path,
                        'processing_time': processing_time,
                        'error_message': error_message,
                        'current_index': i,
                        'total_files': total_files
                    })
            
            # Emitir evento de progreso
            if self.callback_manager:
                progress_percentage = (i / total_files) * 100
                self.callback_manager.emit_event(ProcessingEventType.PROGRESS_UPDATE, {
                    'processed_files': i,
                    'total_files': total_files,
                    'success_count': success_count,
                    'failed_count': i - success_count,
                    'progress_percentage': progress_percentage
                })
        
        # Evento de proceso completado
        total_time = (datetime.now() - start_time).total_seconds()
        if self.callback_manager:
            self.callback_manager.emit_event(ProcessingEventType.PROCESS_COMPLETED, {
                'files_processed': total_files,
                'success_count': success_count,
                'failed_count': total_files - success_count,
                'total_time': total_time
            })
        
        return success_count > 0
