import os
import time
import subprocess
import psutil
import pyautogui
import pygetwindow as gw
from config.logger import logger
from config.settings import get_delays
from utils.gui_helpers import GUIHelpers


class ProcessManager:
    def __init__(self, config):
        self.config = config
        self.sonel_exe_path = config['PATHS'].get('sonel_exe_path', 
                                                 'D:/Wolfly/Sonel/SonelAnalysis.exe')
        self.delays = get_delays()
        self.process_config = config.get('PROCESS', {})
        self.auto_close_enabled = config.get('GUI', {}).get('auto_close_sonel', False)
        self.current_process = None
        self.debug_mode = config.get('debug_mode', False)

    def open_file_with_sonel(self, pqm_file_path):
        """
        Abre un archivo .pqm con la aplicación Sonel
        
        Args:
            pqm_file_path: Ruta completa al archivo .pqm
            
        Returns:
            True si se abre correctamente, False en caso contrario
        """
        try:
            if not os.path.exists(self.sonel_exe_path):
                logger.error(f"❌ No se encuentra el ejecutable: {self.sonel_exe_path}")
                return False
            
            if not os.path.exists(pqm_file_path):
                logger.error(f"❌ No se encuentra el archivo: {pqm_file_path}")
                return False
            
            filename = os.path.basename(pqm_file_path)
            logger.info(f"🚀 Abriendo archivo: {filename}")
            
            try:
                cmd = [self.sonel_exe_path, pqm_file_path]
                GUIHelpers.debug_log(f"Ejecutando comando: {' '.join(cmd)}", self.debug_mode)
                
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )
                
                GUIHelpers.debug_log(f"Proceso iniciado con PID: {self.current_process.pid}", self.debug_mode)
                
            except Exception as e:
                logger.warning(f"Fallo subprocess, intentando con os.startfile: {e}")
                os.startfile(pqm_file_path)
            
            # Esperar tiempo de inicio configurado
            time.sleep(self.delays['startup_wait'])
            logger.info(f"✅ Archivo abierto con Sonel: {filename}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Error abriendo archivo con Sonel: {e}")
            return False

    def cleanup_sonel_processes(self):
        """
        Mata procesos de Sonel si hay residuos antes de iniciar nuevo proceso
        """
        if not self.auto_close_enabled:
            GUIHelpers.debug_log("Cleanup de procesos deshabilitado por configuración", self.debug_mode)
            return
        
        try:
            GUIHelpers.debug_log("Limpiando procesos de Sonel...", self.debug_mode)
            logger.info("🧹 Iniciando cleanup de procesos de Sonel")
            
            sonel_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and 'sonel' in proc.info['name'].lower():
                        sonel_processes.append(proc)
                    elif proc.info['exe'] and 'sonel' in proc.info['exe'].lower():
                        sonel_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not sonel_processes:
                GUIHelpers.debug_log("No se encontraron procesos de Sonel para limpiar", self.debug_mode)
                return
            
            logger.info(f"🔍 Encontrados {len(sonel_processes)} procesos de Sonel para terminar")
            
            # Terminar procesos de forma ordenada
            for proc in sonel_processes:
                try:
                    GUIHelpers.debug_log(f"Terminando proceso: {proc.info['name']} (PID: {proc.pid})", self.debug_mode)
                    proc.terminate()
                    proc.wait(timeout=self.process_config.get('force_kill_timeout', 10))
                    logger.info(f"✅ Proceso terminado: {proc.info['name']} (PID: {proc.pid})")
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    try:
                        GUIHelpers.debug_log(f"Forzando terminación del proceso {proc.pid}", self.debug_mode)
                        proc.kill()
                        logger.warning(f"🔴 Proceso forzado a terminar: PID {proc.pid}")
                    except psutil.NoSuchProcess:
                        pass
                except Exception as e:
                    logger.warning(f"Error terminando proceso {proc.pid}: {e}")
            
            # Pausa post-cleanup
            time.sleep(self.delays['process_cleanup'])
            logger.info("✅ Cleanup de procesos completado")
            
        except Exception as e:
            logger.error(f"Error en cleanup de procesos: {e}")

    def close_sonel_analysis_safely(self):
        """
        Cierra Sonel de forma controlada desde la GUI
        
        Returns:
            True si logra cerrar correctamente, False en caso contrario
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
                GUIHelpers.debug_log("No se encontraron ventanas de Sonel para cerrar", self.debug_mode)
                return True

            logger.info(f"📋 Cerrando {len(sonel_windows)} ventana(s) de Sonel")

            for window in sonel_windows:
                try:
                    GUIHelpers.debug_log(f"Cerrando ventana: {window.title}", self.debug_mode)
                    window.activate()
                    time.sleep(0.5)
                    pyautogui.hotkey('alt', 'f4')
                    time.sleep(1)
                    logger.info(f"✅ Ventana cerrada: {window.title}")
                except Exception as e:
                    logger.warning(f"Error cerrando ventana {window.title}: {e}")

            # Pausa para permitir que las ventanas se cierren completamente
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
        Devuelve cuántas ventanas de Sonel están activas (para control)
        
        Returns:
            int: Número de ventanas de Sonel detectadas
        """
        try:
            all_windows = gw.getAllWindows()
            sonel_windows = [w for w in all_windows if w.title and "sonel" in w.title.lower()]
            count = len(sonel_windows)
            GUIHelpers.debug_log(f"Ventanas de Sonel detectadas: {count}", self.debug_mode)
            return count
        except Exception as e:
            logger.error(f"Error contando ventanas de Sonel: {e}")
            return 0

    def manual_close_all_sonel(self):
        """
        Opción de cierre forzado para todos los procesos (por emergencia)
        
        Returns:
            bool: True si logra cerrar todas las ventanas y procesos
        """
        try:
            logger.info("🚨 CIERRE MANUAL DE EMERGENCIA - Cerrando todo Sonel")
            
            initial_count = self.get_sonel_windows_count()
            if initial_count == 0:
                logger.info("✅ No hay ventanas de Sonel abiertas")
            else:
                logger.info(f"📋 Detectadas {initial_count} ventanas de Sonel para cerrar")
            
            # Intentar cerrar ventanas de forma segura
            closed_count = 0
            max_attempts = 3
            
            for attempt in range(max_attempts):
                GUIHelpers.debug_log(f"Intento {attempt + 1}/{max_attempts} de cierre de ventanas", self.debug_mode)
                
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
            
            # Forzar cleanup de procesos (sin importar configuración)
            logger.info("🔧 Forzando cleanup de procesos...")
            original_auto_close = self.auto_close_enabled
            self.auto_close_enabled = True  # Temporalmente habilitar para cleanup
            self.cleanup_sonel_processes()
            self.auto_close_enabled = original_auto_close  # Restaurar configuración
            
            # Verificar resultado final
            final_count = self.get_sonel_windows_count()
            
            if final_count == 0:
                logger.info("✅ Cierre manual completado - No quedan ventanas de Sonel")
                return True
            else:
                logger.warning(f"⚠️ Cierre parcial - Quedan {final_count} ventanas de Sonel")
                return False
                
        except Exception as e:
            logger.error(f"Error en cierre manual de emergencia: {e}")
            return False

    def is_sonel_running(self):
        """
        Verifica si hay procesos de Sonel ejecutándose
        
        Returns:
            bool: True si hay procesos de Sonel activos
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and 'sonel' in proc.info['name'].lower():
                        return True
                    elif proc.info['exe'] and 'sonel' in proc.info['exe'].lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"Error verificando procesos de Sonel: {e}")
            return False

    def get_process_status(self):
        """
        Obtiene el estado actual de procesos y ventanas de Sonel
        
        Returns:
            dict: Información del estado actual
        """
        try:
            windows_count = self.get_sonel_windows_count()
            is_running = self.is_sonel_running()
            
            status = {
                'windows_count': windows_count,
                'processes_running': is_running,
                'auto_close_enabled': self.auto_close_enabled,
                'current_process_pid': self.current_process.pid if self.current_process else None
            }
            
            GUIHelpers.debug_log(f"Estado de procesos: {status}", self.debug_mode)
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de procesos: {e}")
            return {
                'windows_count': 0,
                'processes_running': False,
                'auto_close_enabled': self.auto_close_enabled,
                'current_process_pid': None,
                'error': str(e)
            }