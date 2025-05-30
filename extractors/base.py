#sonel_extractor/extractors/base.py
from abc import ABC, abstractmethod
class BaseExtractor(ABC):
    """Clase base abstracta para los extractores de datos"""
    def __init__(self, config):
        """
        Inicializa el extractor base
        
        Args:
            config: Configuración para el extractor
        """
        self.config = config

    @abstractmethod
    def extract(self):
        """
        Método abstracto para extraer datos
        
        Returns:
            DataFrame: Datos extraídos o None si hay un error
        """
        pass