import time
import logging
from config.logger import get_logger
from pywinauto.timings import TimeoutError
from config.settings import get_full_config

class WaitHandler:
    def __init__(self):
        config = get_full_config()
        self.logger = get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

    def esperar_controles_disponibles(self, ventana, control_types, timeout=20, check_interval=0.5):
        """
        Espera a que ciertos tipos de controles estén disponibles en la ventana
        
        Args:
            ventana: Objeto de ventana a verificar
            control_types: Lista de tipos de controles a esperar ["Button", "CheckBox", etc.]
            timeout: Tiempo máximo de espera en segundos
            check_interval: Intervalo entre verificaciones en segundos
        
        Returns:
            bool: True si los controles están disponibles, False si timeout
        """
        try:
            self.logger.info(f"⏳ Esperando controles {control_types} (timeout: {timeout}s)...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    controles_encontrados = {}
                    
                    for control_type in control_types:
                        try:
                            controls = ventana.descendants(control_type=control_type)
                            controles_encontrados[control_type] = len(controls)
                        except:
                            controles_encontrados[control_type] = 0
                    
                    # Verificar que todos los tipos de controles tienen al menos 1 elemento
                    if all(count > 0 for count in controles_encontrados.values()):
                        self.logger.info(f"✅ Controles disponibles después de {time.time() - start_time:.2f}s")
                        self.logger.info(f"📊 Controles encontrados: {controles_encontrados}")
                        return True
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.debug(f"Error verificando controles: {e}")
                    time.sleep(check_interval)
                    continue
            
            self.logger.warning(f"⚠️ Timeout esperando controles ({timeout}s)")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error esperando controles: {e}")
            return False
