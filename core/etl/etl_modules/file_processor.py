# ============================================
# core/etl/processors/file_processor.py
# ============================================
import os
from datetime import datetime
from config.logger import logger
from core.parser.csv_parser import CSVParser
from core.parser.excel_parser import ExcelParser
from core.utils.validators import extract_client_code
from core.utils.processing_registry import ProcessingStatus

class FileProcessor:
    """Procesador especializado para archivos individuales"""
    
    def __init__(self, config, registry):
        self.config = config
        self.registry = registry
    
    def process_file(self, file_path, force_reprocess, data_transformer, data_loader):
        """
        Procesa un archivo individual con control de registro
        
        Args:
            file_path: Ruta al archivo a procesar
            force_reprocess: Si True, ignora el registro y procesa el archivo
            data_transformer: Instancia del transformador de datos
            data_loader: Instancia del cargador de datos
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        start_time = datetime.now()
        
        try:
            # Validar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"❌ El archivo {file_path} no existe")
                return False
            
            # Verificar si el archivo debe ser procesado
            if not self._should_process_file(file_path, force_reprocess):
                return True
            
            # Registrar inicio del procesamiento
            cliente_codigo = extract_client_code(file_path)
            self.registry.register_processing_start(file_path, cliente_codigo)
            
            logger.info(f"📄 Procesando archivo: {file_path}")
            
            # Extraer datos del archivo
            df = self._extract_file_data(file_path, start_time)
            if df is None:
                return False
                
            # Transformar datos
            transformed_data = data_transformer.transform_data(df)
            if not self._validate_transformed_data(transformed_data, file_path, start_time):
                return False
            
            # Validar código de cliente
            if not self._validate_client_code(cliente_codigo, file_path, start_time):
                return False
            
            logger.info(f"📌 Código de cliente extraído: {cliente_codigo}")
            
            # Cargar datos
            success = data_loader.load_data(transformed_data, cliente_codigo, file_path)
            
            return self._finalize_processing(success, file_path, cliente_codigo, 
                                           transformed_data, start_time)
                
        except Exception as e:
            return self._handle_processing_error(e, file_path, start_time)
    
    def _should_process_file(self, file_path, force_reprocess):
        """Determina si un archivo debe ser procesado"""
        if not force_reprocess:
            should_process, reason = self.registry.should_process_file(file_path)
            if not should_process:
                self.registry.register_processing_skipped(file_path, reason)
                logger.info(f"⏭️  Archivo omitido: {os.path.basename(file_path)} - {reason}")
                return False
        return True
    
    def _extract_file_data(self, file_path, start_time):
        """Extrae datos del archivo según su tipo"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.xlsx':
                return ExcelParser.parse(file_path)
            elif file_ext == '.csv':
                return CSVParser.parse(file_path)
            else:
                error_msg = f"Formato de archivo no soportado: {file_path}"
                self._register_error(file_path, error_msg, start_time)
                logger.error(f"⚠️ {error_msg}")
                return None
        except Exception as e:
            error_msg = f"Error extrayendo datos de {file_path}: {e}"
            self._register_error(file_path, error_msg, start_time)
            logger.error(f"⚠️ {error_msg}")
            return None
    
    def _validate_transformed_data(self, transformed_data, file_path, start_time):
        """Valida los datos transformados"""
        if transformed_data is None or transformed_data.empty:
            error_msg = f"Transformación de datos fallida para archivo: {file_path}"
            self._register_error(file_path, error_msg, start_time)
            logger.error(f"⚠️ {error_msg}")
            return False
        return True
    
    def _validate_client_code(self, cliente_codigo, file_path, start_time):
        """Valida el código de cliente"""
        if cliente_codigo is None:
            error_msg = f"No se pudo obtener código de cliente desde el archivo {file_path}"
            self._register_error(file_path, error_msg, start_time)
            logger.error(f"❌ {error_msg}")
            return False
        return True
    
    def _finalize_processing(self, success, file_path, cliente_codigo, transformed_data, start_time):
        """Finaliza el procesamiento registrando el resultado"""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        if success:
            additional_info = {
                "rows_processed": len(transformed_data),
                "columns_processed": len(transformed_data.columns) if hasattr(transformed_data, 'columns') else 0,
                "client_code": cliente_codigo,
                "processing_time_seconds": processing_time,
                "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }
            self.registry.register_processing_success(file_path, additional_info)
            logger.info(f"✅ Archivo procesado exitosamente: {file_path} | Cliente: {cliente_codigo} | Tiempo: {processing_time:.2f}s | Registros: {len(transformed_data)}")
            return True
        else:
            error_msg = f"Error al cargar datos desde archivo: {file_path}"
            self._register_error(file_path, error_msg, start_time, cliente_codigo)
            logger.error(f"❌ {error_msg}")
            return False
    
    def _handle_processing_error(self, exception, file_path, start_time):
        """Maneja errores críticos durante el procesamiento"""
        error_msg = f"Error crítico al procesar archivo {file_path}: {exception}"
        self._register_error(file_path, error_msg, start_time)
        logger.error(f"❌ {error_msg}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    def _register_error(self, file_path, error_msg, start_time, cliente_codigo=None):
        """Registra un error en el procesamiento"""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        error_info = {
            "processing_time_seconds": processing_time,
            "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
        if cliente_codigo:
            error_info["client_code"] = cliente_codigo
            
        self.registry.register_processing_error(file_path, error_msg, error_info)
    
    def reset_file_processing(self, file_path):
        """Reinicia el estado de procesamiento de un archivo específico"""
        from core.extractors.file_extractor import FileExtractor
        file_extractor = FileExtractor(self.config, self.registry.registry_file)
        file_extractor.reset_file_status(file_path)
        logger.info(f"🔄 Estado de procesamiento reiniciado para: {os.path.basename(file_path)}")
