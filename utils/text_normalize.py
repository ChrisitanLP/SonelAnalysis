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
        texto = texto.lower().strip()
        # Eliminar caracteres especiales comunes
        texto = re.sub(r'[^\w\s.]', '', texto)
        return texto
    
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
    