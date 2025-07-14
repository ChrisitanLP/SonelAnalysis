import time
import logging
from pywinauto import Application
from config.logger import get_logger
from config.settings import get_full_config, get_window_title_translations

class SonelConnector:
    """Maneja la conexión con la aplicación Sonel"""
    
    def __init__(self):
        self.app = None
        self.ventana_configuracion = None
        self.main_window = None
        
        # Configurar logger
        config = get_full_config()
        self.logger = get_logger("pywinauto", f"{__name__}_pywinauto")
        self.logger.setLevel(getattr(logging, config['LOGGING']['level']))

    def conectar(self, app_reference=None):
        """Conecta con la vista de configuración - ✅ VERSIÓN MULTIIDIOMA CON REINTENTOS"""
        
        def _intentar_conexion():
            """Función interna que contiene la lógica original de conexión"""
            try:
                self.logger.info("🔍 Conectando con vista de configuración...")
                
                if app_reference:
                    self.app = app_reference
                
                if not self.app:
                    # Fallback: conectar directamente si no hay referencia
                    # Obtener palabras clave de análisis para todos los idiomas
                    analysis_keywords = []
                    for lang in ['es', 'en', 'de', 'fr']:
                        translations = get_window_title_translations(lang)
                        analysis_keywords.append(translations.get('analysis_keyword', 'análisis'))
                    
                    # Intentar conectar con diferentes patrones
                    for keyword in set(analysis_keywords):
                        try:
                            self.app = Application(backend="uia").connect(title_re=f".*{keyword}.*")
                            break
                        except:
                            continue

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
                
                self.logger.info(f"🌐 Buscando ventana de configuración con sufijos: {config_suffixes}")
                
                # Función auxiliar para normalizar texto
                def normalizar_texto(texto):
                    """Normaliza texto para comparación multiidioma"""
                    if not texto:
                        return ""
                    texto = texto.lower().strip()
                    import re
                    texto = re.sub(r'[^\w\s.]', '', texto)
                    return texto

                # Función para verificar si es ventana de configuración
                def es_ventana(titulo):
                    """Verifica si el título corresponde a una ventana de configuración"""
                    titulo_norm = normalizar_texto(titulo)
                    
                    # Debe contener palabra clave de análisis y extensión .pqm
                    tiene_analisis = any(keyword in titulo_norm for keyword in analysis_keywords)
                    tiene_extension = file_extension in titulo_norm
                    
                    # DEBE terminar con sufijo de configuración
                    termina_con_config = any(titulo_norm.endswith(suffix.lower()) for suffix in config_suffixes)
                    
                    return tiene_analisis and tiene_extension and titulo_norm and termina_con_config

                # Buscar ventana que termine en sufijo de configuración
                main_window = self.app.top_window()
                windows = main_window.descendants(control_type="Window")
                self.main_window = main_window
                
                for window in windows:
                    try:
                        title = window.window_text()
                        if es_ventana(title):
                            self.ventana_configuracion = window
                            self.logger.info(f"✅ Vista configuración encontrada: {title}")
                            return True
                    except Exception:
                        continue
                
                # Fallback: verificar ventana principal
                main_title = main_window.window_text()
                if es_ventana(main_title):
                    self.ventana_configuracion = main_window
                    self.logger.info(f"✅ Vista configuración (main): {main_title}")
                    return True
                
                self.logger.warning("⚠️ No se encontró vista de configuración en este intento")
                return False
                
            except Exception as e:
                self.logger.warning(f"⚠️ Error en intento de conexión: {e}")
                return False
        
        max_intentos=5
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

    def get_ventana_configuracion(self):
        """Retorna la ventana de configuración"""
        return self.ventana_configuracion
    
    def get_app(self):
        """Retorna la aplicación conectada"""
        return self.app
    
    def get_main_window(self):
        """Retorna la ventana principal"""
        return self.main_window