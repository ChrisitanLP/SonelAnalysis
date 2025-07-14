#sonel_extractor/extractors/file_extractor.py

import os
import glob
import pandas as pd
from config.logger import logger
from core.parser.csv_parser import CSVParser
from core.extractors.base import BaseExtractor
from core.parser.excel_parser import ExcelParser
from config.settings import FILE_SEARCH_PATTERNS
from core.utils.processing_registry import ProcessingRegistry

class FileExtractor(BaseExtractor):
    """Clase para extraer datos de archivos con control de procesamiento"""
    
    def __init__(self, config, registry_file=None):
        """
        Inicializa el extractor de archivos
        
        Args:
            config: Configuración con rutas de archivos
            registry_file: Archivo de registro personalizado (opcional)
        """
        super().__init__(config)
        self.data_dir = os.getenv('DATA_DIR') or config['PATHS']['data_dir']
        
        # Inicializar registro de procesamiento
        registry_file = registry_file or os.path.join(self.data_dir, "registro_procesamiento.json")
        self.registry = ProcessingRegistry(registry_file)
        
    def extract(self):
        """
        Extrae datos de un archivo por defecto en el directorio configurado
        
        Returns:
            DataFrame con los datos extraídos o None si hay error
        """
        # Intentar encontrar un archivo en el directorio configurado
        files = self.find_files_to_process()
        
        if not files:
            logger.info(f"ℹ️ No se encontraron archivos nuevos para procesar en {self.data_dir}")
            return None
        
        # Procesamos solo el primer archivo encontrado para compatibilidad hacia atrás
        logger.info(f"Procesando archivo por defecto: {files[0]}")
        return self.extract_from_file(files[0])
    
    def extract_from_file(self, file_path):
        """
        Extrae datos de un archivo específico
        
        Args:
            file_path: Ruta al archivo del que extraer datos
            
        Returns:
            DataFrame con los datos extraídos o None si hay error
        """
        if not os.path.exists(file_path):
            logger.error(f"El archivo {file_path} no existe")
            return None
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Determinar el parser adecuado según la extensión
        try:
            if file_ext == '.csv':
                df = CSVParser.parse(file_path)
                if df is not None:
                    return df
                    
            elif file_ext == '.xlsx':
                df = ExcelParser.parse(file_path)
                if df is not None:
                    return df
                
            elif file_ext == '.xml':
                # La lectura de XML depende de la estructura exacta
                logger.warning("Extracción de archivos XML no implementada completamente")
                try:
                    df = pd.read_xml(file_path)
                    from utils.validators import validate_voltage_columns
                    valid, _ = validate_voltage_columns(df)
                    if valid:
                        return df
                except Exception as e:
                    logger.error(f"Error al procesar archivo XML: {e}")
                
            elif file_ext == '.mdb':
                # Para MDB se requiere pyodbc y conexión ODBC
                logger.error("Extracción de archivos .mdb no implementada aún")
                
            elif file_ext == '.dat':
                # Los archivos .dat pueden tener diversos formatos
                logger.error("Extracción de archivos .dat requiere formato específico")
                
            else:
                logger.error(f"Formato de archivo no soportado: {file_ext}")
        except Exception as e:
            logger.error(f"Error al extraer datos del archivo {file_path}: {e}")
    
    def find_files_in_directory(self, directory=None):
        """
        Encuentra archivos en un directorio que coincidan con los patrones soportados
        
        Args:
            directory: Directorio donde buscar (usa el configurado por defecto si es None)
            
        Returns:
            list: Lista de rutas a archivos encontrados
        """
        if directory is None:
            directory = self.data_dir
        
        if not os.path.exists(directory):
            logger.error(f"El directorio {directory} no existe")
            return []
        
        all_files = []
        for pattern in FILE_SEARCH_PATTERNS:
            pattern_files = glob.glob(os.path.join(directory, pattern))
            all_files.extend(pattern_files)
        
        # Ordenar por fecha de modificación (más reciente primero)
        all_files.sort(key=os.path.getmtime, reverse=True)
        
        logger.info(f"Encontrados {len(all_files)} archivos en {directory}: {[os.path.basename(f) for f in all_files]}")
        return all_files
    
    def find_files_to_process(self, directory=None):
        """
        Encuentra archivos que necesitan ser procesados (nuevos o modificados)
        
        Args:
            directory: Directorio donde buscar (usa el configurado por defecto si es None)
            
        Returns:
            list: Lista de rutas a archivos que deben procesarse
        """
        all_files = self.find_files_in_directory(directory)
        
        if not all_files:
            return []
        
        files_to_process = []
        skipped_count = 0
        
        for file_path in all_files:
            should_process, reason = self.registry.should_process_file(file_path)
            
            if should_process:
                files_to_process.append(file_path)
                logger.debug(f"📄 Para procesar: {os.path.basename(file_path)} - {reason}")
            else:
                self.registry.register_processing_skipped(file_path, reason)
                skipped_count += 1
                logger.debug(f"⏭️ Omitido: {os.path.basename(file_path)} - {reason}")
        
        logger.info(f"📊 Archivos para procesar: {len(files_to_process)}, Omitidos: {skipped_count}")
        return files_to_process
    
    def extract_all_files(self, directory=None, force_reprocess=False):
        """
        Encuentra y extrae datos de archivos en un directorio, respetando el registro
        
        Args:
            directory: Directorio donde buscar (usa el configurado por defecto si es None)
            force_reprocess: Si True, procesa todos los archivos ignorando el registro
            
        Returns:
            dict: Diccionario con rutas de archivos como claves y DataFrames como valores
        """
        if force_reprocess:
            logger.info("🔄 Modo de reprocesamiento forzado activado")
            files = self.find_files_in_directory(directory)
        else:
            files = self.find_files_to_process(directory)
        
        if not files:
            if not force_reprocess:
                logger.info(f"ℹ️ No hay archivos nuevos para procesar en {directory or self.data_dir}")
            else:
                logger.warning(f"No se encontraron archivos para procesar en {directory or self.data_dir}")
            return {}
        
        results = {}
        processed_count = 0
        error_count = 0
        
        for file_path in files:
            try:
                # Registrar inicio del procesamiento
                self.registry.register_processing_start(file_path)
                
                df = self.extract_from_file(file_path)
                if df is not None and not df.empty:
                    results[file_path] = df
                    processed_count += 1
                    
                    # Registrar éxito con información adicional
                    additional_info = {
                        "rows_extracted": len(df),
                        "columns_extracted": len(df.columns) if hasattr(df, 'columns') else 0
                    }
                    self.registry.register_processing_success(file_path, additional_info)
                    
                    logger.info(f"✅ Extraído: {os.path.basename(file_path)} ({len(df)} filas, {len(df.columns)} columnas)")
                else:
                    error_count += 1
                    error_msg = "No se pudieron extraer datos del archivo o archivo vacío"
                    self.registry.register_processing_error(file_path, error_msg)
                    logger.warning(f"⚠️ Sin datos: {os.path.basename(file_path)}")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"Error al extraer datos: {str(e)}"
                self.registry.register_processing_error(file_path, error_msg)
                logger.error(f"❌ Error: {os.path.basename(file_path)} - {error_msg}")
        
        logger.info(f"📈 Resultados de extracción: {processed_count} exitosos, {error_count} errores de {len(files)} archivos")
        return results
    
    def get_registry_stats(self):
        """
        Obtiene estadísticas del registro de procesamiento
        
        Returns:
            dict: Estadísticas del registro
        """
        return self.registry.get_processing_stats()
    
    def cleanup_registry(self):
        """
        Limpia archivos inexistentes del registro
        
        Returns:
            int: Número de archivos eliminados del registro
        """
        return self.registry.cleanup_missing_files()
    
    def print_processing_report(self):
        """Imprime un reporte del estado del procesamiento"""
        self.registry.print_status_report()
    
    def reset_file_status(self, file_path, new_status=None):
        """
        Reinicia el estado de un archivo específico en el registro
        
        Args:
            file_path: Ruta al archivo
            new_status: Nuevo estado (opcional, por defecto lo elimina del registro)
        """
        file_key = os.path.abspath(file_path)
        
        if new_status is None:
            # Eliminar del registro para que se procese como nuevo
            if file_key in self.registry.registry_data["files"]:
                del self.registry.registry_data["files"][file_key]
                self.registry._save_registry()
                logger.info(f"🔄 Estado reiniciado: {os.path.basename(file_path)}")
        else:
            # Cambiar a un estado específico
            if file_key in self.registry.registry_data["files"]:
                self.registry.registry_data["files"][file_key]["status"] = new_status
                self.registry._save_registry()
                logger.info(f"🔄 Estado cambiado a {new_status}: {os.path.basename(file_path)}")