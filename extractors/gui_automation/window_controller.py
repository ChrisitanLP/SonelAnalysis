import time
import pyautogui
import pygetwindow as gw
from config.logger import logger
from utils.gui_helpers import GUIHelpers

class WindowController:
    """Controla ventanas y acciones de GUI"""
    
    def __init__(self, parent_extractor):
        """
        Inicializa el controlador de ventanas
        
        Args:
            parent_extractor: Referencia al extractor GUI principal
        """
        self.parent = parent_extractor
        self.config = parent_extractor.config
        self.coordinates = parent_extractor.coordinates
        self.delays = parent_extractor.delays
        self.debug_mode = parent_extractor.debug_mode
        
        # Configurar pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = self.config['GUI']['safety']['pause_between_actions']
    
    def safe_click(self, x, y, description="", delay_after=None):
        """
        Realiza un clic de forma segura con logging y debug
        
        Args:
            x, y: Coordenadas
            description: Descripción de la acción
            delay_after: Tiempo de espera después del clic (usa default si es None)
            
        Returns:
            True si el clic fue exitoso, False en caso contrario
        """
        try:
            GUIHelpers.debug_log(self.debug_mode, f"Haciendo clic en ({x}, {y}) - {description}")
            
            # Mover mouse a la posición y hacer clic
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click(x, y)
            
            # Esperar después del clic
            wait_time = delay_after if delay_after is not None else self.delays['between_clicks']
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error haciendo clic en ({x}, {y}) - {description}: {e}")
            return False
    
    def wait_for_window(self, window_title, timeout=30, partial_match=True):
        """
        Espera a que aparezca una ventana con el título especificado
        
        Args:
            window_title: Título de la ventana a esperar
            timeout: Tiempo máximo de espera en segundos
            partial_match: Si buscar coincidencias parciales en el título
            
        Returns:
            True si encuentra la ventana, False si se agota el tiempo
        """
        start_time = time.time()
        GUIHelpers.debug_log(self.debug_mode, f"Esperando ventana: '{window_title}' (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            try:
                # Buscar ventanas con título exacto
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    GUIHelpers.debug_log(self.debug_mode, f"Ventana encontrada: {window_title}")
                    return True
                
                # Buscar ventanas que contengan parte del título si partial_match=True
                if partial_match:
                    all_windows = gw.getAllWindows()
                    for window in all_windows:
                        if window.title and window_title.lower() in window.title.lower():
                            GUIHelpers.debug_log(self.debug_mode, f"Ventana encontrada por coincidencia parcial: {window.title}")
                            return True
                        
            except Exception as e:
                logger.debug(f"Error buscando ventana: {e}")
            
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:  # Log cada 5 segundos
                GUIHelpers.debug_log(self.debug_mode, f"Esperando ventana... ({elapsed}s/{timeout}s)")
        
        logger.error(f"Timeout esperando ventana: {window_title}")
        return False
    
    def find_and_activate_sonel_window(self):
        """
        Busca y activa la ventana de Sonel Analysis
        
        Returns:
            True si logra activar la ventana, False en caso contrario
        """
        try:
            GUIHelpers.debug_log(self.debug_mode, "Buscando ventana de Sonel Analysis...")
            
            # Buscar ventanas que contengan "Sonel" en el título
            all_windows = gw.getAllWindows()
            sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
            
            if not sonel_windows:
                logger.error("❌ No se encontró ventana de Sonel Analysis")
                return False
            
            # Usar la primera ventana de Sonel encontrada
            target_window = sonel_windows[0]
            GUIHelpers.debug_log(self.debug_mode, f"Activando ventana: {target_window.title}")
            
            # Activar y maximizar la ventana
            target_window.activate()
            time.sleep(self.delays['window_activation'])
            
            try:
                target_window.maximize()
                GUIHelpers.debug_log(self.debug_mode, "Ventana maximizada correctamente")
            except Exception as e:
                logger.warning(f"No se pudo maximizar automáticamente: {e}")

                # Intentar maximizar con teclas
                pyautogui.hotkey('alt', 'space')
                time.sleep(0.5)
                pyautogui.press('x')
                time.sleep(1)
            
            time.sleep(2)  # Esperar estabilización
            return True
                
        except Exception as e:
            logger.error(f"❌ Error activando ventana de Sonel: {e}")
            return False
    
    def stabilization_pause(self, file_number, total_files):
        """
        Pausa de estabilización entre archivos
        
        Args:
            file_number: Número del archivo actual
            total_files: Total de archivos a procesar
        """
        if file_number < total_files:
            time.sleep(self.parent.file_processing_delay)