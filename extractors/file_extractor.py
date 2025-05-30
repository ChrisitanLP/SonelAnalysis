#sonel_extractor/extractors/file_extractor.py

import os
import glob
import pandas as pd
from pathlib import Path
from config.logger import logger
from config.settings import FILE_SEARCH_PATTERNS
from parser.excel_parser import ExcelParser
from parser.csv_parser import CSVParser
from extractors.base import BaseExtractor

class FileExtractor(BaseExtractor):
    """Clase para extraer datos de archivos"""
    
    def __init__(self, config):
        """
        Inicializa el extractor de archivos
        
        Args:
            config: Configuración con rutas de archivos
        """
        super().__init__(config)
        self.data_dir = os.getenv('DATA_DIR') or config['PATHS']['data_dir']
        
    def extract(self):
        """
        Extrae datos de un archivo por defecto en el directorio configurado
        
        Returns:
            DataFrame con los datos extraídos o None si hay error
        """
        # Intentar encontrar un archivo en el directorio configurado
        files = self.find_files_in_directory()
        
        if not files:
            logger.error(f"No se encontraron archivos para procesar en {self.data_dir}")
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
    
    def extract_all_files(self, directory=None):
        """
        Encuentra y extrae datos de todos los archivos en un directorio
        
        Args:
            directory: Directorio donde buscar (usa el configurado por defecto si es None)
            
        Returns:
            dict: Diccionario con rutas de archivos como claves y DataFrames como valores
        """
        files = self.find_files_in_directory(directory)
        
        if not files:
            logger.warning(f"No se encontraron archivos para procesar en {directory or self.data_dir}")
            return {}
        
        results = {}
        for file_path in files:
            try:
                df = self.extract_from_file(file_path)
                if df is not None and not df.empty:
                    results[file_path] = df
                else:
                    logger.warning(f"No se pudieron extraer datos del archivo: {file_path}")
            except Exception as e:
                logger.error(f"Error al extraer datos del archivo {file_path}: {e}")
                
        logger.info(f"Extraídos datos de {len(results)}/{len(files)} archivos exitosamente")
        return results