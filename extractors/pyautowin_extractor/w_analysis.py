"""
Clase principal que coordina la ventana de análisis de Sonel
"""

import logging
from extractors.pyautowin_extractor.window_analysis.connector import SonelConnector
from extractors.pyautowin_extractor.window_analysis.navigator import SonelNavigator
from extractors.pyautowin_extractor.window_analysis.executor import SonelExecutor

class SonelAnalisisInicial:
    """Clase especializada para manejar la vista inicial de análisis"""
    
    def __init__(self, archivo_pqm, ruta_exe="D:/Wolfly/Sonel/SonelAnalysis.exe"):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        
        # Configurar logger SOLO PARA CONSOLA
        self.logger = logging.getLogger(f"{__name__}_inicial")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - [INICIAL] %(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
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