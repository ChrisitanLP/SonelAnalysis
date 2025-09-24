"""
Utilidades para normalización y comparación de texto multiidioma
"""
import re

class TextUtils:
    """Clase utilitaria para operaciones de texto multiidioma"""
    
    @staticmethod
    def normalizar_texto(texto):
        """
        Normaliza texto para comparación multiidioma
        
        Args:
            texto (str): Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        if not texto:
            return ""
        
        # Eliminar etiquetas HTML
        texto = re.sub(r"<sub>(.*?)</sub>", r"\1", texto, flags=re.IGNORECASE)
        texto = re.sub(r"<.*?>", "", texto)
        
        # Eliminar símbolos y caracteres especiales
        texto = re.sub(r"[<>_/\-\(\)\[\]{}]", " ", texto)
        
        # Normalizar espacios y convertir a minúsculas
        texto = re.sub(r'\s+', ' ', texto)
        
        return texto.lower().strip()
    
    @staticmethod
    def texto_coincide(texto_control, lista_traducciones):
        """
        Verifica si el texto del control coincide con alguna traducción
        
        Args:
            texto_control (str): Texto del control a verificar
            lista_traducciones (list): Lista de traducciones posibles
            
        Returns:
            bool: True si hay coincidencia, False en caso contrario
        """
        texto_normalizado = TextUtils.normalizar_texto(texto_control)
        for traduccion in lista_traducciones:
            if TextUtils.normalizar_texto(traduccion) in texto_normalizado:
                return True
        return False
    
    @staticmethod
    def contiene_termino_excluido(texto, terminos_excluidos):
        """
        Verifica si el texto contiene algún término que debe ser excluido
        
        Args:
            texto (str): Texto a verificar
            terminos_excluidos (list): Lista de términos excluidos
            
        Returns:
            bool: True si contiene término excluido, False en caso contrario
        """
        texto_normalizado = TextUtils.normalizar_texto(texto)
        for termino in terminos_excluidos:
            termino_normalizado = TextUtils.normalizar_texto(termino)
            if termino_normalizado in texto_normalizado:
                return True
        return False