# ============================================
# core/etl/transformers/data_transformer.py
# ============================================
from core.transformers.voltage_transformer import VoltageTransformer

class DataTransformer:
    """Transformador de datos especializado"""
    
    def transform_data(self, data):
        """
        Ejecuta el paso de transformación de datos
        
        Args:
            data: DataFrame con los datos extraídos
            
        Returns:
            DataFrame transformado o None si hay error
        """
        return VoltageTransformer.transform(data)