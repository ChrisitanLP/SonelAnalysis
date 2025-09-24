"""
Módulo para manejar la conexión con la aplicación Sonel Analysis
"""
import os
import re
import sys
import time
import logging
import win32con
import subprocess
from pywinauto import Application
from config.logger import get_logger
from config.settings import get_full_config, get_window_title_translations


class SonelConnector:
    """Clase especializada para manejar conexiones con Sonel Analysis"""
    
    def __init__(self, archivo_pqm, ruta_exe, logger=None):
        self.archivo_pqm = archivo_pqm
        self.ruta_exe = ruta_exe
        self.app = None
        self.ventana_inicial = None

        config = get_full_config()
        self.logger = logger or get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

    # Reemplazar el método conectar() completo:
    def conectar(self):
        """Conecta con la vista inicial de análisis - VERSIÓN CON ENTORNO LIMPIO"""

        def _crear_entorno_limpio():
            """Crea un entorno sin variables Qt que interfieran con Sonel Analysis"""
            # Obtener entorno actual
            env_limpio = os.environ.copy()
            
            # Variables Qt que pueden causar conflictos con aplicaciones externas
            qt_vars_conflictivas = [
                'QT_PLUGIN_PATH',
                'QT_QPA_PLATFORM_PLUGIN_PATH', 
                'QT_QPA_PLATFORM',
                'QT_AUTO_SCREEN_SCALE_FACTOR',
                'QT_SCALE_FACTOR',
                'QT_SCREEN_SCALE_FACTORS',
                'QT_DEVICE_PIXEL_RATIO',
                'QT_LOGGING_RULES',
                'QT_OPENGL',
                'QT_QUICK_BACKEND',
                'QML_IMPORT_PATH',
                'QML2_IMPORT_PATH',
                'QT_STYLE_OVERRIDE',
                'QT_ACCESSIBILITY',
                'QT_IM_MODULE'
            ]
            
            # Eliminar variables problemáticas
            vars_eliminadas = []
            for var in qt_vars_conflictivas:
                if var in env_limpio:
                    self.logger.debug(f"Eliminando variable conflictiva: {var}={env_limpio[var]}")
                    del env_limpio[var]
                    vars_eliminadas.append(var)
            
            self.logger.info(f"Variables Qt eliminadas: {len(vars_eliminadas)}")
            
            # Si estamos en PyInstaller, limpiar PATH de DLLs de nuestra app
            if getattr(sys, 'frozen', False):
                path_dirs = env_limpio.get('PATH', '').split(os.pathsep)
                
                # Filtrar directorios que contengan DLLs de nuestra aplicación
                path_limpio = []
                pyinstaller_paths = []
                
                for path_dir in path_dirs:
                    path_lower = path_dir.lower()
                    # Excluir paths temporales de PyInstaller y Qt
                    if any(term in path_lower for term in ["_mei", "qt5", "qt6", "pyqt", "temp"]):
                        pyinstaller_paths.append(path_dir)
                        self.logger.debug(f"PATH excluido: {path_dir}")
                    else:
                        path_limpio.append(path_dir)
                
                env_limpio['PATH'] = os.pathsep.join(path_limpio)
                self.logger.info(f"PATH limpiado: {len(pyinstaller_paths)} directorios removidos")
                
                # Establecer directorio de trabajo al de Sonel Analysis
                sonel_dir = os.path.dirname(self.ruta_exe)
                if os.path.exists(sonel_dir):
                    env_limpio['SONEL_WORK_DIR'] = sonel_dir
                    self.logger.debug(f"Directorio de trabajo para Sonel: {sonel_dir}")
            
            # Asegurar que variables del sistema estén presentes
            system_vars = ['SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE']
            for var in system_vars:
                if var in os.environ and var not in env_limpio:
                    env_limpio[var] = os.environ[var]
            
            return env_limpio

        def _intentar_conexion():
            """Función interna que contiene la lógica original de conexión con inicio seguro"""
            try:
                self.logger.info("🔍 Conectando con vista inicial...")
                
                # Obtener traducciones de títulos de ventana para todos los idiomas
                window_translations = {}
                for lang in ['es', 'en', 'de', 'fr']:
                    translations = get_window_title_translations(lang)
                    for key, value in translations.items():
                        if key not in window_translations:
                            window_translations[key] = []
                        window_translations[key].append(value.lower())
                
                # Listas de palabras clave multiidioma
                analysis_keywords = list(set(window_translations.get('analysis_keyword', ['análisis'])))
                config_suffixes = list(set(window_translations.get('configuration_suffix', ['configuración 1'])))
                file_extension = '.pqm'
                
                self.logger.info(f"🌐 Buscando ventanas con palabras: {analysis_keywords}")
                self.logger.info(f"🌐 Excluyendo sufijos: {config_suffixes}")
                
                # Función auxiliar para normalizar texto
                def normalizar_texto(texto):
                    """Normaliza texto para comparación multiidioma"""
                    if not texto:
                        return ""
                    texto = texto.lower().strip()
                    import re
                    texto = re.sub(r'[^\w\s.]', '', texto)
                    return texto

                # Función para verificar si es ventana de análisis (NO configuración)
                def es_ventana(titulo):
                    """Verifica si el título corresponde a una ventana de análisis"""
                    titulo_norm = normalizar_texto(titulo)
                    
                    # Debe contener palabra clave de análisis y extensión .pqm
                    tiene_analisis = any(keyword in titulo_norm for keyword in analysis_keywords)
                    tiene_extension = file_extension in titulo_norm
                    
                    # NO debe terminar con sufijo de configuración
                    termina_con_config = any(titulo_norm.endswith(suffix.lower()) for suffix in config_suffixes)
                    
                    return tiene_analisis and tiene_extension and titulo_norm and not termina_con_config

                # Establecer conexión con la aplicación
                try:
                    # Buscar con diferentes patrones de título
                    connection_patterns = [f".*{keyword}.*" for keyword in analysis_keywords]
                    
                    for pattern in connection_patterns:
                        try:
                            self.app = Application(backend="uia").connect(title_re=pattern)
                            self.logger.info(f"✅ Conectado con aplicación existente (patrón: {pattern})")
                            break
                        except:
                            continue
                    
                    if not self.app:
                        raise Exception("No se pudo conectar con ningún patrón")
                            
                except:
                    self.logger.info("🚀 Iniciando nueva instancia con entorno limpio...")
                    
                    env_limpio = _crear_entorno_limpio()
                    
                    try:
                        # Validar que el ejecutable de Sonel existe
                        if not os.path.exists(self.ruta_exe):
                            raise FileNotFoundError(f"Sonel Analysis no encontrado en: {self.ruta_exe}")
                        
                        # Validar que el archivo PQM existe
                        if not os.path.exists(self.archivo_pqm):
                            raise FileNotFoundError(f"Archivo PQM no encontrado: {self.archivo_pqm}")
                        
                        # Directorio de trabajo = directorio del ejecutable de Sonel
                        work_dir = os.path.dirname(self.ruta_exe)
                        
                        self.logger.info(f"Ejecutable Sonel: {self.ruta_exe}")
                        self.logger.info(f"Archivo PQM: {self.archivo_pqm}")
                        self.logger.info(f"Directorio trabajo: {work_dir}")
                        
                        # Crear proceso con máximo aislamiento
                        startupinfo = None
                        if os.name == 'nt':  # Windows
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = win32con.SW_NORMAL
                        
                        # SOLUCIÓN CRÍTICA: subprocess.Popen con entorno completamente aislado
                        proceso_sonel = subprocess.Popen(
                            [self.ruta_exe, self.archivo_pqm],
                            env=env_limpio,  # Entorno sin variables Qt conflictivas
                            cwd=work_dir,    # Directorio de trabajo = directorio de Sonel
                            startupinfo=startupinfo,
                            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        self.logger.info(f"Proceso Sonel iniciado (PID: {proceso_sonel.pid})")
                        self.logger.info("Esperando que Sonel Analysis se cargue completamente...")
                        
                        # Esperar un tiempo inicial para que Sonel inicie
                        time.sleep(8)
                        
                        # Verificar que el proceso no haya terminado prematuramente
                        if proceso_sonel.poll() is not None:
                            stdout, stderr = proceso_sonel.communicate()
                            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Sin información de error"
                            self.logger.error(f"Sonel Analysis terminó prematuramente:")
                            self.logger.error(f"Código de salida: {proceso_sonel.returncode}")
                            self.logger.error(f"Error: {error_msg}")
                            raise Exception(f"Sonel falló al iniciar: {error_msg}")
                        
                        # Intentar conectar con pywinauto varias veces
                        conexion_exitosa = False
                        max_intentos_conexion = 15  # 15 intentos = 30 segundos máximo
                        
                        for intento_conn in range(max_intentos_conexion):
                            try:
                                self.logger.debug(f"Intento conexión pywinauto {intento_conn + 1}/{max_intentos_conexion}")
                                
                                # Probar conexión con diferentes patrones
                                connection_patterns = [
                                    f".*{analysis_keywords[0]}.*",
                                    ".*Analysis.*",
                                    ".*Sonel.*"
                                ]
                                
                                for pattern in connection_patterns:
                                    try:
                                        self.app = Application(backend="uia").connect(title_re=pattern)
                                        conexion_exitosa = True
                                        self.logger.info(f"✅ Conectado con Sonel (patrón: {pattern})")
                                        break
                                    except:
                                        continue
                                
                                if conexion_exitosa:
                                    break
                                    
                            except Exception as e:
                                self.logger.debug(f"Intento {intento_conn + 1} falló: {e}")
                            
                            time.sleep(2)  # Esperar 2 segundos entre intentos
                        
                        if not conexion_exitosa:
                            # Si no se pudo conectar, verificar si el proceso sigue corriendo
                            if proceso_sonel.poll() is None:
                                self.logger.warning("Sonel está corriendo pero pywinauto no puede conectar")
                                self.logger.warning("Intentando conexión genérica...")
                                try:
                                    self.app = Application(backend="uia").connect(process=proceso_sonel.pid)
                                    self.logger.info("✅ Conexión exitosa por PID")
                                except Exception as e:
                                    self.logger.error(f"Conexión por PID falló: {e}")
                                    raise Exception("No se pudo establecer conexión con Sonel Analysis")
                            else:
                                raise Exception("Sonel Analysis se cerró durante la conexión")

                    except FileNotFoundError as e:
                        self.logger.error(f"Archivo no encontrado: {e}")
                        raise
                    except subprocess.SubprocessError as e:
                        self.logger.error(f"Error ejecutando subprocess: {e}")
                        raise
                    except Exception as e:
                        self.logger.error(f"Error iniciando Sonel con entorno limpio: {e}")
                        # Fallback al método original solo si es absolutamente necesario
                        self.logger.warning("Intentando método de inicio alternativo...")
                        try:
                            self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
                            time.sleep(10)
                            self.logger.info("Método alternativo exitoso")
                        except Exception as e2:
                            self.logger.error(f"Método alternativo también falló: {e2}")
                            raise Exception(f"No se pudo iniciar Sonel Analysis: {e}")
                        
                if not self.app:
                    raise Exception("self.app es None después del proceso de conexión")

                # Obtener ventana inicial específica
                main_window = self.app.top_window()
                main_window.set_focus()
                
                # Buscar ventana de análisis (NO configuración)
                windows = main_window.descendants(control_type="Window")
                for window in windows:
                    try:
                        title = window.window_text()
                        if es_ventana(title):
                            self.ventana_inicial = window
                            self.logger.info(f"✅ Vista inicial encontrada: {title}")
                            return True
                    except Exception:
                        continue
                
                # Fallback: usar ventana principal si cumple criterios
                main_title = main_window.window_text()
                if es_ventana(main_title):
                    self.ventana_inicial = main_window
                    self.logger.info(f"✅ Vista inicial (main): {main_title}")
                    return True
                
                self.logger.error("⚠️ No se encontró vista inicial en ningún idioma en este intento")
                return False
                
            except Exception as e:
                self.logger.error(f"⚠️ Error conectando vista inicial: {e}")
                return False
        
        max_intentos = 5
        # Lógica de reintentos generalizable
        for intento in range(1, max_intentos + 1):
            self.logger.info(f"🔄 Intento {intento}/{max_intentos} de conexión...")
            
            if _intentar_conexion():
                self.logger.info(f"✅ Conexión exitosa en intento {intento}")
                return True
            
            if intento < max_intentos:
                tiempo_espera = intento * 2  # Espera progresiva: 2s, 4s, 6s, 8s
                self.logger.info(f"⏱️ Esperando {tiempo_espera}s antes del siguiente intento...")
                time.sleep(tiempo_espera)
        
        self.logger.error(f"❌ No se pudo conectar después de {max_intentos} intentos")
        return False

    def get_app_reference(self):
        """Retorna la referencia de la aplicación"""
        return self.app

    def get_ventana_inicial(self):
        """Retorna la referencia de la ventana inicial"""
        return self.ventana_inicial