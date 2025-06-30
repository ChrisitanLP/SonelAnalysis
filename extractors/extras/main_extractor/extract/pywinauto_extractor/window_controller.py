import os
import time
import pyautogui
import pygetwindow as gw
from config.logger import logger
from utils.gui_helpers import GUIHelpers
from pywinauto.timings import wait_until, TimeoutError
from utils.debug_options import WindowDebugHelper
from utils.validators import _get_search_variants
from pywinauto import Application, findwindows, Desktop

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
        self.delays = parent_extractor.delays
        self.debug_mode = parent_extractor.debug_mode
        self.sonel_exe_path = parent_extractor.sonel_exe_path
        self.archivo_pqm = parent_extractor.archivo_pqm
        self.debugger = WindowDebugHelper(self.parent)

        self.app = None
        self.main_window = None
        self.analysis_window = None
        self.current_analysis_window = None

    def connect_to_sonel(self):
        """
        Conecta a una instancia existente de Sonel Analysis o la inicia
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            # Intentar conectar a proceso existente
            try:
                processes = findwindows.find_elements(title_re=".*Análisis.*", backend="uia")
                if processes:
                    logger.info("🔗 Conectando a instancia existente de Sonel Analysis")
                    self.parent.app = Application(backend="uia").connect(handle=processes[0].handle)
                    return True
            except:
                pass
            
            # Si no hay proceso, intentar iniciar nuevo
            if os.path.exists(self.sonel_exe_path):
                logger.info("🚀 Iniciando nueva instancia de Sonel Analysis")
                self.parent.app = Application(backend="uia").start(self.sonel_exe_path)
                time.sleep(self.timeout_long)  # Esperar arranque completo
                return True
            else:
                logger.error(f"❌ Ejecutable no encontrado: {self.sonel_exe_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando a Sonel Analysis: {e}")
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
            sonel_windows = [w for w in all_windows if w.title and "SONEL" in w.title.lower()]
            
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
         