"""
Módulo para manejar la conexión con la aplicación Sonel Analysis
"""

import time
import logging
from pywinauto import Application


class SonelConnector:
    """Clase especializada para manejar conexiones con Sonel Analysis"""
    
    def __init__(self, archivo_pqm, ruta_exe, logger=None):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        self.app = None
        self.ventana_inicial = None
        self.logger = logger or logging.getLogger(__name__)

    def conectar(self):
        """Conecta con la vista inicial de análisis"""
        try:
            self.logger.info("🔍 Conectando con vista inicial...")
            
            # Establecer conexión con la aplicación
            try:
                self.app = Application(backend="uia").connect(title_re=".*Análisis.*")
                self.logger.info("✅ Conectado con aplicación existente")
            except:
                self.logger.info("🚀 Iniciando nueva instancia...")
                self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
                time.sleep(10)
            
            # Obtener ventana inicial específica
            main_window = self.app.top_window()
            main_window.set_focus()
            
            # Buscar ventana que NO termine en "Configuración 1"
            windows = main_window.descendants(control_type="Window")
            for window in windows:
                try:
                    title = window.window_text()
                    if ("Análisis" in title and ".pqm" in title and title.strip() 
                        and not title.strip().endswith("Configuración 1")):
                        self.ventana_inicial = window
                        self.logger.info(f"✅ Vista inicial encontrada: {title}")
                        return True
                except Exception:
                    continue
            
            # Fallback: usar ventana principal si cumple criterios
            main_title = main_window.window_text()
            if ("Análisis" in main_title and ".pqm" in main_title and main_title.strip() 
                and not main_title.strip().endswith("Configuración 1")):
                self.ventana_inicial = main_window
                self.logger.info(f"✅ Vista inicial (main): {main_title}")
                return True
            
            self.logger.error("❌ No se encontró vista inicial")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando vista inicial: {e}")
            return False

    def get_app_reference(self):
        """Retorna la referencia de la aplicación"""
        return self.app

    def get_ventana_inicial(self):
        """Retorna la referencia de la ventana inicial"""
        return self.ventana_inicial