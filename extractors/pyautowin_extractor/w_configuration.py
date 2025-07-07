"""
Clase principal que coordina la ventana de configuración de Sonel
"""

import logging
from config.logger import get_logger
from config.settings import get_full_config
from extractors.pyautowin_extractor.window_configuration.executor import SonelExecutor
from extractors.pyautowin_extractor.window_configuration.connector import SonelConnector
from extractors.pyautowin_extractor.window_configuration.navigator import SonelNavigator

class SonelConfiguracion:
    """Clase especializada para manejar la vista de configuración"""
    
    def __init__(self, app_reference=None):
        self.app_reference = app_reference
        
        # Configurar logger SOLO PARA CONSOLA
        config = get_full_config()
        self.logger = get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

        self.logger.info("="*60)
        self.logger.info("⚙️ EXTRACTOR VISTA CONFIGURACIÓN - SONEL ANALYSIS")
        self.logger.info("="*60)

        # Inicializar componentes
        self.connector = SonelConnector()
        self.navigator = None
        self.executor = None

    def conectar(self, app_reference=None):
        """Conecta con la vista de configuración"""
        result = self.connector.conectar(app_reference or self.app_reference)
        
        if result:
            # Inicializar navigator y executor con la ventana conectada
            ventana = self.connector.get_ventana_configuracion()
            self.navigator = SonelNavigator(ventana)
            self.executor = SonelExecutor(
                ventana, 
                self.connector.get_app(), 
                self.connector.get_main_window()
            )
        return result

    def extraer_navegacion_lateral(self):
        """Extrae y activa elementos de navegación lateral (Mediciones)"""
        if not self.navigator:
            self.logger.error("❌ Navigator no inicializado. Conectar primero.")
            return False
        return self.navigator.extraer_navegacion_lateral()

    def configurar_filtros_datos(self):
        """Configura filtros de datos (Usuario, Prom., etc.)"""
        if not self.navigator:
            self.logger.error("❌ Navigator no inicializado. Conectar primero.")
            return False
        return self.navigator.configurar_filtros_datos()
        
    def extraer_configuracion_principal_mediciones(self):
        """Busca y desactiva el checkbox 'Seleccionar todo' y hace clic en 'Expandir todo'"""
        if not self.executor:
            self.logger.error("❌ Executor no inicializado. Conectar primero.")
            return False
        return self.executor.extraer_configuracion_principal_mediciones()

    def extraer_componentes_arbol_mediciones(self):
        """
        Busca y desactiva el checkbox 'Seleccionar todo' si está activado,
        y hace clic en el botón 'Expandir todo'.
        """
        if not self.executor:
            self.logger.error("❌ Executor no inicializado. Conectar primero.")
            return False
        return self.executor.extraer_componentes_arbol_mediciones()
    
    def extraer_tabla_mediciones(self):
        """Extrae información de la tabla de mediciones inferior"""
        if not self.executor:
            self.logger.error("❌ Executor no inicializado. Conectar primero.")
            return False
        return self.executor.extraer_tabla_mediciones()

    def extraer_informes_graficos(self):
        """Extrae información específica de la sección 'Informes y gráficos'"""
        if not self.executor:
            self.logger.error("❌ Executor no inicializado. Conectar primero.")
            return
        return self.executor.extraer_informes_graficos()

    def guardar_archivo_csv(self, nombre_archivo: str):
        """Extrae información específica de la sección 'Informes y gráficos'"""
        if not self.executor:
            self.logger.error("❌ Executor no inicializado. Conectar primero.")
            return
        return self.executor.guardar_archivo_csv(nombre_archivo)
    
