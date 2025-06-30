import time
import logging
from pywinauto import Application


class SonelConnector:
    """Maneja la conexión con la aplicación Sonel"""
    
    def __init__(self):
        self.app = None
        self.ventana_configuracion = None
        self.main_window = None
        
        # Configurar logger
        self.logger = logging.getLogger(f"{__name__}_connector")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - [CONNECTOR] %(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def conectar(self, app_reference=None):
        """Conecta con la vista de configuración"""
        try:
            self.logger.info("🔍 Conectando con vista de configuración...")
            
            if app_reference:
                self.app = app_reference
            
            if not self.app:
                # Fallback: conectar directamente si no hay referencia
                self.app = Application(backend="uia").connect(title_re=".*Análisis.*")
            
            # Esperar a que aparezca la ventana de configuración
            time.sleep(2)
            
            # Buscar ventana que termine en "Configuración 1"
            main_window = self.app.top_window()
            windows = main_window.descendants(control_type="Window")
            self.main_window = main_window
            
            for window in windows:
                try:
                    title = window.window_text()
                    if ("Análisis" in title and ".pqm" in title and title.strip() 
                        and title.strip().endswith("Configuración 1")):
                        self.ventana_configuracion = window
                        self.logger.info(f"✅ Vista configuración encontrada: {title}")
                        return True
                except Exception:
                    continue
            
            # Fallback: verificar ventana principal
            main_title = main_window.window_text()
            if ("Análisis" in main_title and ".pqm" in main_title and main_title.strip() 
                and main_title.strip().endswith("Configuración 1")):
                self.ventana_configuracion = main_window
                self.logger.info(f"✅ Vista configuración (main): {main_title}")
                return True
            
            self.logger.error("❌ No se encontró vista de configuración")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando configuración: {e}")
            return False

    def get_ventana_configuracion(self):
        """Retorna la ventana de configuración"""
        return self.ventana_configuracion
    
    def get_app(self):
        """Retorna la aplicación conectada"""
        return self.app
    
    def get_main_window(self):
        """Retorna la ventana principal"""
        return self.main_window