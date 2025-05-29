import time
import pygetwindow as gw
import pyautogui
from config.logger import logger
from config.settings import get_delays
from utils.gui_helpers import GUIHelpers


class WindowController:
    def __init__(self, config):
        self.config = config
        self.delays = get_delays()
        self.debug_mode = config.get('debug_mode', False)

    def wait_for_window(self, window_title, timeout=30, partial_match=True):
        start_time = time.time()
        GUIHelpers.debug_log(f"Esperando ventana: '{window_title}' (timeout: {timeout}s)", self.debug_mode)
        
        while time.time() - start_time < timeout:
            try:
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    GUIHelpers.debug_log(f"Ventana encontrada: {window_title}", self.debug_mode)
                    return True
                
                if partial_match:
                    all_windows = gw.getAllWindows()
                    for window in all_windows:
                        if window.title and window_title.lower() in window.title.lower():
                            GUIHelpers.debug_log(f"Ventana encontrada por coincidencia parcial: {window.title}", self.debug_mode)
                            return True
                        
            except Exception as e:
                logger.debug(f"Error buscando ventana: {e}")
            
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                GUIHelpers.debug_log(f"Esperando ventana... ({elapsed}s/{timeout}s)", self.debug_mode)
        
        logger.error(f"Timeout esperando ventana: {window_title}")
        return False

    def find_and_activate_sonel_window(self):
        try:
            GUIHelpers.debug_log("Buscando ventana de Sonel Analysis...", self.debug_mode)
            
            all_windows = gw.getAllWindows()
            sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
            
            if not sonel_windows:
                logger.error("❌ No se encontró ventana de Sonel Analysis")
                return False
            
            target_window = sonel_windows[0]
            GUIHelpers.debug_log(f"Activando ventana: {target_window.title}", self.debug_mode)
            
            target_window.activate()
            time.sleep(self.delays['window_activation'])
            
            try:
                target_window.maximize()
                GUIHelpers.debug_log("Ventana maximizada correctamente", self.debug_mode)
            except Exception as e:
                logger.warning(f"No se pudo maximizar automáticamente: {e}")

                pyautogui.hotkey('alt', 'space')
                time.sleep(0.5)
                pyautogui.press('x')
                time.sleep(1)
            
            time.sleep(2)
            return True
                
        except Exception as e:
            logger.error(f"❌ Error activando ventana de Sonel: {e}")
            return False

    def get_sonel_windows_count(self):
        try:
            all_windows = gw.getAllWindows()
            sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
            count = len(sonel_windows)
            GUIHelpers.debug_log(f"Ventanas de Sonel detectadas: {count}", self.debug_mode)
            return count
        except Exception as e:
            logger.error(f"Error contando ventanas de Sonel: {e}")
            return 0

    def close_all_sonel_windows(self):
        try:
            initial_count = self.get_sonel_windows_count()
            if initial_count == 0:
                logger.info("✅ No hay ventanas de Sonel abiertas")
                return True
            
            logger.info(f"📋 Detectadas {initial_count} ventanas de Sonel para cerrar")
            
            closed_count = 0
            max_attempts = 3
            
            for attempt in range(max_attempts):
                all_windows = gw.getAllWindows()
                sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
                
                if not sonel_windows:
                    break
                
                for window in sonel_windows:
                    try:
                        GUIHelpers.debug_log(f"Cerrando ventana: {window.title}", self.debug_mode)
                        window.activate()
                        time.sleep(0.5)
                        pyautogui.hotkey('alt', 'f4')
                        time.sleep(1)
                        closed_count += 1
                    except Exception as e:
                        logger.warning(f"Error cerrando ventana {window.title}: {e}")
                
                time.sleep(2)
            
            final_count = self.get_sonel_windows_count()
            
            if final_count == 0:
                logger.info("✅ Todas las ventanas de Sonel cerradas correctamente")
                return True
            else:
                logger.warning(f"⚠️ Quedan {final_count} ventanas de Sonel abiertas")
                return False
                
        except Exception as e:
            logger.error(f"Error cerrando ventanas de Sonel: {e}")
            return False

    def activate_window_by_title(self, window_title, partial_match=True):
        try:
            all_windows = gw.getAllWindows()
            
            target_window = None
            if partial_match:
                for window in all_windows:
                    if window.title and window_title.lower() in window.title.lower():
                        target_window = window
                        break
            else:
                windows = gw.getWindowsWithTitle(window_title)
                if windows:
                    target_window = windows[0]
            
            if target_window:
                target_window.activate()
                time.sleep(self.delays.get('window_activation', 1))
                return True
            else:
                logger.error(f"No se encontró ventana: {window_title}")
                return False
                
        except Exception as e:
            logger.error(f"Error activando ventana {window_title}: {e}")
            return False