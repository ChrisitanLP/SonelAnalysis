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

    def esperar_ventana_lista(self, ventana, timeout=30, check_interval=0.5):
        """
        Espera a que una ventana esté completamente lista para interactuar
        
        Args:
            ventana: Objeto de ventana a verificar
            timeout: Tiempo máximo de espera en segundos (default: 30)
            check_interval: Intervalo entre verificaciones en segundos (default: 0.5)
        
        Returns:
            bool: True si la ventana está lista, False si timeout
        """
        try:
            self.logger.info(f"⏳ Esperando ventana lista (timeout: {timeout}s)...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Verificar que la ventana existe y es visible
                    if not ventana.exists():
                        time.sleep(check_interval)
                        continue
                    
                    # Verificar que la ventana está habilitada
                    if not ventana.is_enabled():
                        time.sleep(check_interval)
                        continue
                    
                    # Verificar que la ventana está visible
                    if not ventana.is_visible():
                        time.sleep(check_interval)
                        continue
                    
                    # Verificar que la ventana tiene contenido (no está cargando)
                    try:
                        # Intentar obtener el texto de la ventana
                        ventana.window_text()
                        
                        # Verificar que tiene controles hijos
                        children = ventana.children()
                        if len(children) == 0:
                            time.sleep(check_interval)
                            continue
                        
                        # Verificar que al menos algunos controles están listos
                        controles_listos = 0
                        for child in children[:5]:  # Verificar solo los primeros 5
                            try:
                                if child.exists() and child.is_visible():
                                    controles_listos += 1
                            except:
                                pass
                        
                        if controles_listos == 0:
                            time.sleep(check_interval)
                            continue
                        
                        self.logger.info(f"✅ Ventana lista después de {time.time() - start_time:.2f}s")
                        return True
                        
                    except Exception as e:
                        self.logger.debug(f"Ventana aún no lista: {e}")
                        time.sleep(check_interval)
                        continue
                
                except Exception as e:
                    self.logger.debug(f"Error verificando ventana: {e}")
                    time.sleep(check_interval)
                    continue
            
            self.logger.warning(f"⚠️ Timeout esperando ventana ({timeout}s)")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error esperando ventana: {e}")
            return False

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

    def esperar_boton_especifico(self, ventana, texto_buscar, timeout=15, check_interval=0.5):
        """
        Espera a que un botón específico esté disponible y clickeable
        
        Args:
            ventana: Objeto de ventana a verificar
            texto_buscar: Lista de textos a buscar en los botones
            timeout: Tiempo máximo de espera en segundos
            check_interval: Intervalo entre verificaciones en segundos
        
        Returns:
            tuple: (bool, control) - (True/False, objeto del botón encontrado o None)
        """
        try:
            self.logger.info(f"⏳ Esperando botón con texto {texto_buscar} (timeout: {timeout}s)...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    buttons = ventana.descendants(control_type="Button")
                    
                    for button in buttons:
                        try:
                            texto_boton = button.window_text().strip()
                            
                            # Verificar coincidencia con cualquier texto de la lista
                            if isinstance(texto_buscar, list):
                                coincide = any(texto.lower() in texto_boton.lower() for texto in texto_buscar)
                            else:
                                coincide = texto_buscar.lower() in texto_boton.lower()
                            
                            if coincide and button.is_enabled() and button.is_visible():
                                self.logger.info(f"✅ Botón '{texto_boton}' listo después de {time.time() - start_time:.2f}s")
                                return True, button
                        except:
                            continue
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.debug(f"Error verificando botón: {e}")
                    time.sleep(check_interval)
                    continue
            
            self.logger.warning(f"⚠️ Timeout esperando botón ({timeout}s)")
            return False, None
            
        except Exception as e:
            self.logger.error(f"❌ Error esperando botón: {e}")
            return False, None
        
    def esperar_ventana_configuracion(self, app, timeout=30, check_interval=0.5):
        """
        Espera específicamente a que aparezca una ventana de configuración
        
        Args:
            app: Aplicación pywinauto
            timeout: Tiempo máximo de espera en segundos
            check_interval: Intervalo entre verificaciones en segundos
        
        Returns:
            tuple: (bool, ventana) - (True/False, objeto ventana encontrada o None)
        """
        try:
            self.logger.info(f"⏳ Esperando ventana de configuración (timeout: {timeout}s)...")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Obtener ventana principal
                    main_window = app.top_window()
                    
                    if not main_window.exists():
                        time.sleep(check_interval)
                        continue
                    
                    # Buscar ventanas que contengan patrones típicos de configuración
                    config_patterns = [
                        'configuración', 'configuration', 'config',
                        'settings', 'einstellungen', 'paramètres'
                    ]
                    
                    # Buscar en ventanas hijas
                    windows = main_window.descendants(control_type="Window")
                    
                    for window in windows:
                        try:
                            if not window.exists() or not window.is_visible():
                                continue
                                
                            title = window.window_text().lower()
                            
                            # Verificar patrones de configuración
                            if any(pattern in title for pattern in config_patterns):
                                # Verificar que la ventana tenga controles
                                if len(window.children()) > 0:
                                    elapsed_time = time.time() - start_time
                                    self.logger.info(f"✅ Ventana de configuración encontrada después de {elapsed_time:.2f}s: {window.window_text()}")
                                    return True, window
                        except Exception as e:
                            self.logger.debug(f"Error verificando ventana: {e}")
                            continue
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.debug(f"Error buscando ventana de configuración: {e}")
                    time.sleep(check_interval)
                    continue
            
            elapsed_time = time.time() - start_time
            self.logger.warning(f"⚠️ Timeout esperando ventana de configuración ({elapsed_time:.2f}s)")
            return False, None
            
        except Exception as e:
            self.logger.error(f"❌ Error esperando ventana de configuración: {e}")
            return False, None