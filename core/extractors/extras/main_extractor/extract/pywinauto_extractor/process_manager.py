import os
import time
import psutil
import pyautogui
import subprocess
import pygetwindow as gw
from config.logger import logger

class ProcessManager:
    """Maneja procesos y ventanas de Sonel Analysis"""
    
    def __init__(self, parent_extractor):
        """
        Inicializa el gestor de procesos
        
        Args:
            parent_extractor: Referencia al extractor pywin principal
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
            return
        
        try:
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
        Abre un archivo .pqm702 con Sonel Analysis
        
        Args:
            file_path: Ruta al archivo .pqm702
            
        Returns:
            bool: True si se abre correctamente
        """
        try:
            logger.info(f"🔓 Abriendo archivo: {os.path.basename(pqm_file_path)}")
            
            # Verificar que el archivo existe
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
                # Usar subprocess con configuración más segura
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )

            except Exception as e:
                logger.warning(f"Fallo subprocess, intentando con os.startfile: {e}")
                os.startfile(pqm_file_path)
            
            time.sleep(self.delays['startup_wait'])
            
            # Buscar y activar la ventana
            if self.find_and_activate_sonel_window():
                return True
            else:
                logger.error(f"❌ No se pudo activar la ventana con el archivo {filename}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error abriendo archivo con Sonel: {e}")
            return False
        
    
    def find_and_activate_sonel_window(self):
        """
        Busca y activa la ventana de Sonel Analysis
        
        Returns:
            True si logra activar la ventana, False en caso contrario
        """
        try:
            # Buscar ventanas que contengan "Sonel" en el título
            all_windows = gw.getAllWindows()
            sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
            
            if not sonel_windows:
                logger.error("❌ No se encontró ventana de Sonel Analysis")
                return False
            
            # Usar la primera ventana de Sonel encontrada
            target_window = sonel_windows[0]

            # Activar y maximizar la ventana
            target_window.activate()
            time.sleep(self.delays['window_activation'])
            
            try:
                target_window.maximize()
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
