import os
import time
import pyautogui
from config.logger import logger


class GUIHelpers:
    @staticmethod
    def debug_log(message, debug_mode=None):
        if debug_mode is None:
            debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        if debug_mode:
            print(f"[DEBUG] {message}")
            logger.debug(message)

    @staticmethod
    def safe_click(x, y, description="", delay_after=None, default_delay=0.5, debug_mode=None):
        try:
            GUIHelpers.debug_log(f"Haciendo clic en ({x}, {y}) - {description}", debug_mode)
            
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.click(x, y)
            
            wait_time = delay_after if delay_after is not None else default_delay
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error haciendo clic en ({x}, {y}) - {description}: {e}")
            return False

    @staticmethod
    def stabilization_pause(delay_seconds, file_number=None, total_files=None):
        if file_number is not None and total_files is not None:
            if file_number < total_files:
                time.sleep(delay_seconds)
        else:
            time.sleep(delay_seconds)

    @staticmethod
    def write_text_safely(text, clear_first=True, delay_after=0.5):
        try:
            if clear_first:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.3)
            
            pyautogui.write(text)
            time.sleep(delay_after)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error escribiendo texto '{text}': {e}")
            return False

    @staticmethod
    def send_hotkey(key_combination, delay_after=0.5):
        try:
            if isinstance(key_combination, str):
                pyautogui.press(key_combination)
            elif isinstance(key_combination, (list, tuple)):
                pyautogui.hotkey(*key_combination)
            else:
                raise ValueError("key_combination debe ser string o lista/tupla")
            
            time.sleep(delay_after)
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando tecla(s) {key_combination}: {e}")
            return False