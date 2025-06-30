"""
Módulo para manejar la navegación en el árbol de configuración
"""

import time
import logging
import pyautogui

class SonelNavigator:
    """Clase especializada para navegar por la configuración"""
    
    def __init__(self, ventana_inicial, logger=None):
        self.ventana_inicial = ventana_inicial
        self.logger = logger or logging.getLogger(__name__)

    def navegar_configuracion(self):
        """Navega al árbol de configuración y expande 'Configuración 1'"""
        try:
            self.logger.info("🌳 Navegando árbol de configuración...")
            
            if not self.ventana_inicial:
                self.logger.error("❌ No hay ventana inicial conectada")
                return False
            
            # Buscar TreeItem con "Configuración 1"
            tree_controls = self.ventana_inicial.descendants(control_type="TreeItem")
            
            for tree in tree_controls:
                texto = tree.window_text()
                if "Configuración 1" in texto or "Configuration 1" in texto:
                    self.logger.info(f"✅ TreeItem encontrado: {texto}")
                    return self._expandir_configuracion(tree)
            
            self.logger.error("❌ TreeItem 'Configuración 1' no encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error navegando configuración: {e}")
            return False

    def _expandir_configuracion(self, config_item):
        """Expande el elemento de configuración"""
        try:
            rect = config_item.rectangle()
            center_x = (rect.left + rect.right) // 2
            center_y = (rect.top + rect.bottom) // 2
            
            pyautogui.click(center_x, center_y)
            time.sleep(0.5)
            
            self.logger.info(f"🔓 Click en configuración ({center_x}, {center_y})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error expandiendo configuración: {e}")
            return False