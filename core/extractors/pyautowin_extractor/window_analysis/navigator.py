"""
Módulo para manejar la navegación en el árbol de configuración
"""

import time
import logging
import pyautogui
from config.logger import get_logger
from core.utils.text_normalize import TextUtils
from core.utils.wait_handler import WaitHandler
from config.settings import get_full_config, get_all_possible_translations

class SonelNavigator:
    """Clase especializada para navegar por la configuración"""
    
    def __init__(self, ventana_inicial, logger=None):
        self.ventana_inicial = ventana_inicial

        self.wait_handler = WaitHandler()

        config = get_full_config()
        self.logger = logger or get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

    def navegar_configuracion(self):
        """Navega al árbol de configuración y expande 'Configuración 1' - ✅ VERSIÓN MULTIIDIOMA"""
        try:
            if not self.ventana_inicial:
                self.logger.error("❌ No hay ventana inicial conectada")
                return False

            self.logger.info("🌳 Navegando árbol de configuración...")

            # Obtener todas las traducciones posibles para 'configuration'
            configuration_texts = get_all_possible_translations('ui_controls', 'configuration')
            self.logger.info(f"🌐 Buscando 'Configuración 1' en: {configuration_texts}")

            # Esperar que los TreeItems estén disponibles
            if not self.wait_handler.esperar_controles_disponibles(self.ventana_inicial, 
                                                    ["TreeItem"], 
                                                    timeout=20):
                self.logger.error("❌ Timeout: TreeItems no disponibles")
                return False      
            
            # Buscar TreeItem con "Configuración 1" en cualquier idioma
            tree_controls = self.ventana_inicial.descendants(control_type="TreeItem")
            
            for tree in tree_controls:
                try:
                    texto = tree.window_text()
                    if texto and TextUtils.texto_coincide(texto, configuration_texts):
                        self.logger.info(f"✅ TreeItem 'Configuración 1' encontrado: '{texto}'")
                        return self._expandir_configuracion(tree)
                except Exception as e:
                    self.logger.debug(f"Error procesando TreeItem: {e}")
            
            self.logger.error("❌ TreeItem 'Configuración 1' no encontrado en ningún idioma")
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