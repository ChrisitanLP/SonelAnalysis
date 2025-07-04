"""
Módulo para manejar la conexión con la aplicación Sonel Analysis
"""

import time
import logging
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
        """Conecta con la vista inicial de análisis - ✅ VERSIÓN MULTIIDIOMA"""
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
            def normalizar_texto_ventana(texto):
                """Normaliza texto para comparación multiidioma"""
                if not texto:
                    return ""
                texto = texto.lower().strip()
                import re
                texto = re.sub(r'[^\w\s.]', '', texto)
                return texto

            # Función para verificar si es ventana de análisis (NO configuración)
            def es_ventana_analisis(titulo):
                """Verifica si el título corresponde a una ventana de análisis"""
                titulo_norm = normalizar_texto_ventana(titulo)
                
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
                self.logger.info("🚀 Iniciando nueva instancia...")
                self.app = Application(backend="uia").start(f'"{self.ruta_exe}" "{self.archivo_pqm}"')
                time.sleep(10)
            
            # Obtener ventana inicial específica
            main_window = self.app.top_window()
            main_window.set_focus()
            
            # Buscar ventana de análisis (NO configuración)
            windows = main_window.descendants(control_type="Window")
            for window in windows:
                try:
                    title = window.window_text()
                    if es_ventana_analisis(title):
                        self.ventana_inicial = window
                        self.logger.info(f"✅ Vista inicial encontrada: {title}")
                        return True
                except Exception:
                    continue
            
            # Fallback: usar ventana principal si cumple criterios
            main_title = main_window.window_text()
            if es_ventana_analisis(main_title):
                self.ventana_inicial = main_window
                self.logger.info(f"✅ Vista inicial (main): {main_title}")
                return True
            
            self.logger.error("❌ No se encontró vista inicial en ningún idioma")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error conectando vista inicial: {e}")
            return False

    def get_app_reference(self):
        """Retorna la referencia de la aplicación"""
        return self.app

    def get_ventana_inicial(self):
        """Retorna la referencia de la ventana inicial"""
        return self.ventana_inicial