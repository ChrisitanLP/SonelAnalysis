# ============================================
# core/etl/extractors/data_extractor.py
# ============================================
from config.logger import logger
from core.extractors.file_extractor import FileExtractor
from core.extractors.pygui_extractor import GUIExtractor

class DataExtractor:
    """Extractor de datos especializado"""
    
    def __init__(self, config, registry_file):
        self.config = config
        self.registry_file = registry_file
    
    def extract_data(self, method, force_reprocess=False):
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