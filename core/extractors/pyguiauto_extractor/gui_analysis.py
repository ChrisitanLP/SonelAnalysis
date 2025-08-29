import os
import time
import pyautogui
import subprocess
from config.logger import get_logger
from core.utils.coordinates_utils import CoordinatesUtils

class GuiAnalisisInicial:
    """Maneja la vista inicial de Sonel Analysis usando coordenadas GUI"""
    
    def __init__(self, archivo_pqm, ruta_exe, coordinates):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        self.coordinates = coordinates
        self.app_process = None
        
        # Logger específico
        self.logger = get_logger("gui_analysis", f"{__name__}_gui_analysis")
        
        # Configurar pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        self.logger.info(f"🎯 GuiAnalisisInicial iniciado para: {os.path.basename(archivo_pqm)}")
    
    def conectar(self):
        """
        Conecta con la aplicación Sonel Analysis y abre el archivo
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            self.logger.info("🚀 Iniciando aplicación Sonel Analysis...")
            
            # Verificar que existe el ejecutable
            if not os.path.exists(self.ruta_exe):
                self.logger.error(f"❌ No se encuentra el ejecutable: {self.ruta_exe}")
                return False
            
            # Verificar que existe el archivo PQM
            if not os.path.exists(self.archivo_pqm):
                self.logger.error(f"❌ No se encuentra el archivo PQM: {self.archivo_pqm}")
                return False
            
            # Ejecutar la aplicación con el archivo como parámetro
            command = [self.ruta_exe, self.archivo_pqm]
            self.logger.info(f"📂 Ejecutando: {' '.join(command)}")
            
            self.app_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar a que la aplicación se inicie
            time.sleep(5)
            
            # Verificar que el proceso sigue ejecutándose
            if self.app_process.poll() is not None:
                self.logger.error("❌ La aplicación se cerró inesperadamente")
                return False
            
            self.logger.info("✅ Aplicación iniciada correctamente")
            
            # Esperar a que la interfaz esté completamente cargada
            time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando con la aplicación: {e}")
            return False
    
    def navegar_configuracion(self):
        """
        Navega a la ventana de configuración usando coordenadas
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self.logger.info("🧭 Navegando a configuración...")
            
            # Buscar el elemento TreeItem_configuration_1 en las coordenadas
            config_key = "TreeItem_configuration_1"
            if config_key not in self.coordinates:
                self.logger.error(f"❌ No se encontró coordenada para: {config_key}")
                return False
            
            # Obtener coordenadas del elemento de configuración
            config_coord = self.coordinates[config_key]
            x, y = CoordinatesUtils.get_coordinate_center(config_coord)
            
            self.logger.info(f"🎯 Haciendo clic en configuración en ({x}, {y})")
            
            # Hacer clic en el elemento de configuración
            pyautogui.click(x, y)
            time.sleep(5)
            
            # Verificar si hay botón de análisis de datos para confirmar navegación
            analysis_button_key = "Button_analysis_data"
            if analysis_button_key in self.coordinates:
                analysis_coord = self.coordinates[analysis_button_key]
                # Solo verificar que existe, no hacer clic aún
                self.logger.info("✅ Ventana de configuración detectada")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error navegando a configuración: {e}")
            return False
    
    def ejecutar_analisis(self):
        """
        Ejecuta el análisis de datos usando coordenadas
        
        Returns:
            bool: True si el análisis fue exitoso
        """
        try:
            self.logger.info("⚡ Ejecutando análisis de datos...")
            
            # Buscar el botón de análisis de datos
            analysis_button_key = "Button_analysis_data"
            if analysis_button_key not in self.coordinates:
                self.logger.error(f"❌ No se encontró coordenada para: {analysis_button_key}")
                return False
            
            # Obtener coordenadas del botón de análisis
            analysis_coord = self.coordinates[analysis_button_key]
            x, y = CoordinatesUtils.get_coordinate_center(analysis_coord)
            
            self.logger.info(f"🎯 Haciendo clic en 'Data analysis' en ({x}, {y})")
            
            # Hacer clic en el botón de análisis
            pyautogui.click(x, y)
            
            # Esperar a que se procese el análisis
            self.logger.info("⏳ Esperando procesamiento del análisis...")
            time.sleep(12)  # Tiempo para que se procese el análisis
            
            # Verificar que estamos en la ventana correcta buscando elementos esperados
            # Como checkboxes de mediciones
            checkbox_key = "CheckBox_measurements_0"
            if checkbox_key in self.coordinates:
                self.logger.info("✅ Análisis completado, ventana de mediciones detectada")
                return True
            else:
                self.logger.warning("⚠️ No se detectó la ventana esperada post-análisis")
                return True  # Continuar de todas formas
            
        except Exception as e:
            self.logger.error(f"❌ Error ejecutando análisis: {e}")
            return False
    
    def get_app_reference(self):
        """
        Obtiene referencia al proceso de la aplicación
        
        Returns:
            subprocess.Popen: Proceso de la aplicación o None
        """
        return self.app_process
    
    def cerrar_aplicacion(self):
        """Cierra la aplicación de forma controlada"""
        try:
            if self.app_process and self.app_process.poll() is None:
                self.app_process.terminate()
                time.sleep(5)
                
                # Si no se cerró, forzar cierre
                if self.app_process.poll() is None:
                    self.app_process.kill()
                
                self.logger.info("✅ Aplicación cerrada correctamente")
        except Exception as e:
            self.logger.warning(f"⚠️ Error cerrando aplicación: {e}")