import os
import time
import psutil
import pyautogui
import subprocess
import pygetwindow as gw
from config.logger import logger
from utils.gui_helpers import GUIHelpers

class ProcessManager:
    """Maneja procesos y subprocesos de Sonel Analysis"""
    
    def __init__(self, parent_extractor):
        """
        Inicializa el gestor de procesos
        
        Args:
            parent_extractor: Referencia al extractor GUI principal
        """
        self.parent = parent_extractor
        self.config = parent_extractor.config
        self.sonel_exe_path = parent_extractor.sonel_exe_path
        self.auto_close_enabled = parent_extractor.auto_close_enabled
        self.delays = parent_extractor.delays
        self.debug_mode = parent_extractor.debug_mode
        
        # Configuración de proceso
        self.process_config = self.config.get('PROCESS', {})
        self.current_process = None
    
    def cleanup_sonel_processes(self):
        """
        Limpia procesos de Sonel de forma segura para evitar crashes
        """
        if not self.auto_close_enabled:
            GUIHelpers.debug_log(self.debug_mode, "Cleanup de procesos deshabilitado por configuración")
            return
        
        try:
            GUIHelpers.debug_log(self.debug_mode, "Limpiando procesos de Sonel...")
            
            # Buscar procesos de Sonel
            sonel_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and 'SonelAnalysis' in proc.info['name'].lower():
                        sonel_processes.append(proc)
                    elif proc.info['exe'] and 'SonelAnalysis' in proc.info['exe'].lower():
                        sonel_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Terminar procesos de forma ordenada
            for proc in sonel_processes:
                try:
                    GUIHelpers.debug_log(self.debug_mode, f"Terminando proceso: {proc.info['name']} (PID: {proc.pid})")
                    proc.terminate()
                    proc.wait(timeout=self.process_config.get('force_kill_timeout', 10))
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    try:
                        proc.kill()  # Force kill si no responde
                    except psutil.NoSuchProcess:
                        pass
                except Exception as e:
                    logger.warning(f"Error terminando proceso {proc.pid}: {e}")
            
            time.sleep(self.delays['process_cleanup'])
            
        except Exception as e:
            logger.error(f"Error en cleanup de procesos: {e}")
    
    def open_file_with_sonel(self, pqm_file_path):
        """
        Abre un archivo .pqm702 directamente con Sonel Analysis
        
        Args:
            pqm_file_path: Ruta completa al archivo .pqm702
            
        Returns:
            True si se abre correctamente, False en caso contrario
        """
        try:
            # Verificar que los archivos existen
            if not os.path.exists(self.sonel_exe_path):
                logger.error(f"❌ No se encuentra el ejecutable: {self.sonel_exe_path}")
                return False
            
            if not os.path.exists(pqm_file_path):
                logger.error(f"❌ No se encuentra el archivo: {pqm_file_path}")
                return False
            
            filename = os.path.basename(pqm_file_path)
            
            try:
                # Abrir archivo con el programa
                cmd = [self.sonel_exe_path, pqm_file_path]
                GUIHelpers.debug_log(self.debug_mode, f"Ejecutando comando: {' '.join(cmd)}")
                
                # Usar subprocess con configuración más segura
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )
                
                GUIHelpers.debug_log(self.debug_mode, f"Proceso iniciado con PID: {self.current_process.pid}")
                
            except Exception as e:
                logger.warning(f"Fallo subprocess, intentando con os.startfile: {e}")
                os.startfile(pqm_file_path)
            
            time.sleep(self.delays['startup_wait'])
            
            # Buscar y activar la ventana
            if self.parent.window_controller.find_and_activate_sonel_window():
                return True
            else:
                logger.error(f"❌ No se pudo activar la ventana con el archivo {filename}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error abriendo archivo con Sonel: {e}")
            return False
    
    def close_sonel_analysis_safely(self):
        """
        Cierre condicional de Sonel Analysis
        Solo se ejecuta si auto_close_enabled=True
        """
        if not self.auto_close_enabled:
            logger.info("🔒 Cierre automático de Sonel deshabilitado - Continuando al siguiente archivo")
            return True
            
        try:
            logger.info("🔒 Cerrando Sonel Analysis de forma segura...")
            
            # Obtener todas las ventanas que parezcan de Sonel
            all_windows = gw.getAllWindows()
            sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]

            if not sonel_windows:
                GUIHelpers.debug_log(self.debug_mode, "No se encontraron ventanas de Sonel para cerrar")
                return True

            for window in sonel_windows:
                try:
                    GUIHelpers.debug_log(self.debug_mode, f"Cerrando ventana: {window.title}")
                    window.activate()
                    time.sleep(0.5)
                    pyautogui.hotkey('alt', 'f4')
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Error cerrando ventana {window.title}: {e}")

            time.sleep(2)

            # Cleanup de procesos si es necesario
            if self.process_config.get('process_cleanup_enabled', True):
                self.cleanup_sonel_processes()
            
            # Verificación final
            remaining_windows = [w for w in gw.getAllWindows() if w.title and "sonel" in w.title.lower()]
            if not remaining_windows:
                logger.info("✅ Sonel Analysis cerrado correctamente")
                return True
            else:
                logger.warning(f"⚠️ Quedan {len(remaining_windows)} ventanas de Sonel abiertas")
                return False

        except Exception as e:
            logger.error(f"Error cerrando Sonel Analysis: {e}")
            return False
    
    def get_sonel_windows_count(self):
        """
        Cuenta las ventanas de Sonel abiertas
        
        Returns:
            int: Número de ventanas de Sonel detectadas
        """
        try:
            all_windows = gw.getAllWindows()
            sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
            count = len(sonel_windows)
            GUIHelpers.debug_log(self.debug_mode, f"Ventanas de Sonel detectadas: {count}")
            return count
        except Exception as e:
            logger.error(f"Error contando ventanas de Sonel: {e}")
            return 0

    def manual_close_all_sonel(self):
        """
        Método manual para cerrar todas las ventanas de Sonel
        
        Returns:
            bool: True si logra cerrar todas las ventanas
        """
        try:
            initial_count = self.get_sonel_windows_count()
            if initial_count == 0:
                logger.info("✅ No hay ventanas de Sonel abiertas")
                return True
            
            logger.info(f"📋 Detectadas {initial_count} ventanas de Sonel para cerrar")
            
            # Intentar cerrar ventanas de forma segura
            closed_count = 0
            max_attempts = 3
            
            for attempt in range(max_attempts):
                all_windows = gw.getAllWindows()
                sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
                
                if not sonel_windows:
                    break
                
                for window in sonel_windows:
                    try:
                        GUIHelpers.debug_log(self.debug_mode, f"Cerrando ventana: {window.title}")
                        window.activate()
                        time.sleep(0.5)
                        pyautogui.hotkey('alt', 'f4')
                        time.sleep(1)
                        closed_count += 1
                    except Exception as e:
                        logger.warning(f"Error cerrando ventana {window.title}: {e}")
                
                time.sleep(2)
            
            # Verificar resultado
            final_count = self.get_sonel_windows_count()
            
            if final_count == 0:
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error en cierre manual de Sonel: {e}")
            return False

    def close_sonel_analysis_force(self):
        """
        Cierra todos los procesos relacionados con Sonel Analysis de forma forzada.
        """
        sonel_keywords = ['SonelAnalysis.exe', 'sonelanalysis.exe'] # Ajusta según el nombre real del proceso
        closed = 0

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                if any(keyword in proc_name for keyword in sonel_keywords):
                    proc.kill()
                    logger.info(f"💀 Proceso Sonel terminado: {proc.info['name']} (PID: {proc.info['pid']})")
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if closed == 0:
            logger.info("✅ No se encontraron procesos de Sonel para cerrar.")
        else:
            logger.info(f"✅ Se cerraron {closed} procesos de Sonel.")
