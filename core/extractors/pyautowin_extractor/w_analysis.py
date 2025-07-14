"""
Clase principal que coordina la ventana de análisis de Sonel
"""

import logging
from config.logger import get_logger
from config.settings import PATHS, get_full_config
from core.extractors.pyautowin_extractor.window_analysis.executor import SonelExecutor
from core.extractors.pyautowin_extractor.window_analysis.connector import SonelConnector
from core.extractors.pyautowin_extractor.window_analysis.navigator import SonelNavigator

class SonelAnalisisInicial:
    """Clase especializada para manejar la vista inicial de análisis"""
    
    def __init__(self, archivo_pqm, ruta_exe=None):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe or PATHS['sonel_exe_path']
        config = get_full_config()
        
        # Configurar logger usando configuración centralizada
        self.logger = get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))
        
        self.logger.info("="*60)
        self.logger.info("🎯 EXTRACTOR VISTA INICIAL - SONEL ANALYSIS")
        self.logger.info(f"📁 Archivo PQM: {archivo_pqm}")
        self.logger.info("="*60)

        # Inicializar componentes
        self.connector = SonelConnector(archivo_pqm, ruta_exe, self.logger)
        self.navigator = None
        self.executor = None

    def conectar(self):
        """Conecta con la vista inicial de análisis"""
        result = self.connector.conectar()
        if result:
            # Inicializar navegador y ejecutor con la ventana inicial
            ventana = self.connector.get_ventana_inicial()
            self.navigator = SonelNavigator(ventana, self.logger)
            self.executor = SonelExecutor(ventana, self.logger)
        return result

    def navegar_configuracion(self):
        """Navega al árbol de configuración y expande 'Configuración 1'"""
        if not self.navigator:
            self.logger.error("❌ Navigator no inicializado")
            return False
        return self.navigator.navegar_configuracion()

    def ejecutar_analisis(self):
        """Hace clic en el botón 'Análisis de datos'"""
        if not self.executor:
            self.logger.error("❌ Executor no inicializado")
            return False
        return self.executor.ejecutar_analisis()

    def get_app_reference(self):
        """Retorna la referencia de la aplicación para usar en la segunda clase"""
        return self.connector.get_app_reference()