"""
Módulo para ejecutar análisis de datos
"""
import re
import time
import logging
from config.logger import get_logger
from config.settings import get_full_config, get_all_possible_translations

class SonelExecutor:
    """Clase especializada para ejecutar análisis de datos"""
    
    def __init__(self, ventana_inicial, logger=None):
        self.ventana_inicial = ventana_inicial

        config = get_full_config()
        self.logger = logger or get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

    def ejecutar_analisis(self):
        """Hace clic en el botón 'Análisis de datos' - ✅ VERSIÓN MULTIIDIOMA"""
        try:
            self.logger.info("🎯 Ejecutando análisis de datos...")

            # Obtener todas las traducciones posibles para 'analysis_data'
            analysis_data_texts = get_all_possible_translations('ui_controls', 'analysis_data')
            
            self.logger.info(f"🌐 Buscando 'Análisis de datos' en: {analysis_data_texts}")
            
            # Función auxiliar para normalizar texto
            def normalizar_texto_ui(texto):
                """Normaliza texto para comparación multiidioma"""
                if not texto:
                    return ""
                texto = texto.lower().strip()
                # Eliminar caracteres especiales comunes
                import re
                texto = re.sub(r'[^\w\s]', '', texto)
                return texto

            # Función para verificar coincidencia
            def texto_coincide(texto_control, lista_traducciones):
                """Verifica si el texto del control coincide con alguna traducción"""
                texto_normalizado = normalizar_texto_ui(texto_control)
                for traduccion in lista_traducciones:
                    if normalizar_texto_ui(traduccion) in texto_normalizado:
                        return True
                return False

            # Buscar botón con enfoque multiidioma
            analysis_button = None
            
            # Obtener todos los botones
            buttons = self.ventana_inicial.descendants(control_type="Button")
            
            for button in buttons:
                try:
                    texto_boton = button.window_text().strip()
                    if texto_boton and texto_coincide(texto_boton, analysis_data_texts):
                        analysis_button = button
                        self.logger.info(f"✅ Botón 'Análisis de datos' encontrado: '{texto_boton}'")
                        break
                except Exception as e:
                    self.logger.debug(f"Error procesando botón: {e}")
            
            if analysis_button:
                analysis_button.click()
                time.sleep(2)  # Esperar a que se abra la ventana de configuración
                
                self.logger.info("✅ Análisis de datos ejecutado")
                return True
            else:
                self.logger.error("❌ Botón 'Análisis de datos' no encontrado en ningún idioma")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando análisis: {e}")
            return False