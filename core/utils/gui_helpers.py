import os
from config.logger import logger


class GUIHelpers:
    @staticmethod
    def debug_log(message, debug_mode=None):
        if debug_mode is None:
            debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        if debug_mode:
            print(f"[DEBUG] {message}")
            logger.debug(message)