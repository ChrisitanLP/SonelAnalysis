"""
Módulo para ejecutar análisis de datos
"""

import time
import logging


class SonelExecutor:
    """Clase especializada para ejecutar análisis de datos"""
    
    def __init__(self, ventana_inicial, logger=None):
        self.ventana_inicial = ventana_inicial
        self.logger = logger or logging.getLogger(__name__)

    def ejecutar_analisis(self):
        """Hace clic en el botón 'Análisis de datos'"""
        try:
            self.logger.info("🎯 Ejecutando análisis de datos...")
            
            # Buscar botón "Análisis de datos"
            buttons = self.ventana_inicial.descendants(control_type="Button", title="Análisis de datos")
            if not buttons:
                buttons = self.ventana_inicial.descendants(control_type="Button", title="Data Analysis")
            
            if buttons:
                analysis_button = buttons[0]
                analysis_button.click()
                time.sleep(2)  # Esperar a que se abra la ventana de configuración
                
                self.logger.info("✅ Análisis de datos ejecutado")
                return True
            else:
                self.logger.error("❌ Botón 'Análisis de datos' no encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando análisis: {e}")
            return False