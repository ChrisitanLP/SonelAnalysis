"""
Aplicación principal - Sonel Data Extractor
Versión portable compatible con PyInstaller
"""

import os
import sys
import logging
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from gui.window.application import SonelDataExtractorGUI

def configure_qt_for_portable():
    """
    Configura Qt para ejecutables portables SIN afectar aplicaciones externas
    VERSIÓN CORREGIDA: Aislamiento completo de variables Qt
    """
    try:
        if getattr(sys, 'frozen', False):
            # Estamos ejecutando desde un ejecutable PyInstaller
            bundle_dir = sys._MEIPASS
            
            # CONFIGURACIÓN AISLADA para nuestra aplicación únicamente
            qt_plugins_path = os.path.join(bundle_dir, 'PyQt5', 'Qt5', 'plugins')
            
            if os.path.exists(qt_plugins_path):
                # CRÍTICO: Solo configurar para nuestra instancia
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugins_path
                
                # NUEVO: Configurar variables adicionales para mayor aislamiento
                os.environ['QT_PLUGIN_PATH'] = qt_plugins_path
                
                # Configurar directorio de bibliotecas Qt
                qt_lib_path = os.path.join(bundle_dir, 'PyQt5', 'Qt5', 'lib')
                if os.path.exists(qt_lib_path):
                    os.environ['QT_LIBRARY_PATH'] = qt_lib_path
                
                print(f"Qt plugins configurados para app principal: {qt_plugins_path}")
                
                # Verificar plugins críticos
                platforms_path = os.path.join(qt_plugins_path, 'platforms')
                if os.path.exists(platforms_path):
                    critical_plugins = ['qwindows.dll', 'qminimal.dll', 'qoffscreen.dll']
                    existing_plugins = os.listdir(platforms_path)
                    
                    plugins_found = 0
                    for plugin in critical_plugins:
                        if plugin in existing_plugins:
                            print(f"Plugin crítico encontrado: {plugin}")
                            plugins_found += 1
                        else:
                            print(f"Plugin crítico faltante: {plugin}")
                    
                    if plugins_found == 0:
                        print("ADVERTENCIA: No se encontraron plugins críticos de Qt")
            else:
                print(f"Advertencia: No se encontraron plugins Qt en {qt_plugins_path}")
                
        else:
            print("Modo desarrollo: configuración Qt no necesaria")
            
    except Exception as e:
        print(f"Error configurando Qt para portable: {e}")

def setup_portable_environment():
    """
    Configura el entorno para ejecución portable desde PyInstaller
    VERSIÓN CORREGIDA: Configuración mínima que no interfiere con subprocesos
    """
    if getattr(sys, 'frozen', False):
        # Ejecutándose desde PyInstaller
        bundle_dir = sys._MEIPASS
        
        # SOLO configurar lo mínimo necesario para PyQt5
        qt_plugins_path = os.path.join(bundle_dir, 'PyQt5', 'Qt5', 'plugins')
        if os.path.exists(qt_plugins_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugins_path

        # Configurar path de trabajo al directorio del ejecutable
        app_dir = os.path.dirname(sys.executable)
        os.chdir(app_dir)
        
        # Crear directorios necesarios si no existen
        required_dirs = [
            'data/archivos_csv',
            'data/archivos_pqm', 
            'logs',
            'temp',
            'config'
        ]
        
        for dir_path in required_dirs:
            full_path = os.path.join(app_dir, dir_path)
            os.makedirs(full_path, exist_ok=True)
        
        print(f"Modo portable activado. Directorio base: {app_dir}")
        print("✅ Configuración aislada: no interfiere con aplicaciones externas")
    else:
        # Desarrollo normal
        print("Modo desarrollo activado")

def configure_logging_portable():
    """Configura logging para modo portable"""
    try:
        if getattr(sys, 'frozen', False):
            # Ejecutable - logs en directorio del ejecutable
            log_dir = os.path.join(os.path.dirname(sys.executable), 'logs')
        else:
            # Desarrollo - logs en directorio del proyecto
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar logging básico
        log_file = os.path.join(log_dir, 'sonel_app.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configurado. Archivo: {log_file}")
        
    except Exception as e:
        print(f"Error configurando logging: {e}")

def handle_exception(exc_type, exc_value, exc_traceback):
    """Maneja excepciones no capturadas"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.critical("Excepción no capturada", exc_info=(exc_type, exc_value, exc_traceback))

def main():
    """Función principal de la aplicación"""
    try:
        # PASO 1: Configurar Qt para portable ANTES de cualquier cosa
        configure_qt_for_portable()
        
        # PASO 2: Configurar entorno portable
        setup_portable_environment()
        
        # PASO 3: Configurar logging
        configure_logging_portable()
        logger = logging.getLogger(__name__)
        
        # PASO 4: Configurar manejo de excepciones
        sys.excepthook = handle_exception
        
        logger.info("=== INICIANDO SONEL DATA EXTRACTOR ===")
        logger.info(f"Python: {sys.version}")
        logger.info(f"Modo portable: {getattr(sys, 'frozen', False)}")
        
        # PASO 5: Crear aplicación Qt
        app = QApplication(sys.argv)
        
        # Configuraciones adicionales de la aplicación
        app.setApplicationName("Sonel Data Extractor")
        app.setApplicationVersion("1.2.0")
        app.setApplicationDisplayName("EEASA - Sonel Data Extractor")
        
        # Configurar estilo y tema
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        logger.info("Aplicación Qt creada exitosamente")
        
        # PASO 6: Crear e inicializar ventana principal
        try:
            window = SonelDataExtractorGUI()
            window.show()
            logger.info("Ventana principal inicializada")
            
            # Mostrar información de la ventana
            logger.info(f"Geometría ventana: {window.geometry()}")
            logger.info(f"Tema actual: {'Oscuro' if hasattr(window, 'is_dark_mode') and window.is_dark_mode else 'Claro'}")
            
        except Exception as e:
            logger.error(f"Error inicializando ventana principal: {e}")
            logger.error("Detalles:", exc_info=True)
            return 1
        
        # PASO 7: Ejecutar aplicación
        logger.info("Iniciando loop principal de la aplicación")
        exit_code = app.exec_()
        
        logger.info(f"Aplicación terminada con código: {exit_code}")
        return exit_code
        
    except ImportError as e:
        error_msg = f"Error de importación: {e}"
        print(error_msg)
        if 'PyQt5' in str(e):
            print("ERROR CRÍTICO: PyQt5 no está disponible.")
            print("Solución: Reinstala PyQt5 o verifica la configuración de PyInstaller")
        return 1
        
    except Exception as e:
        error_msg = f"Error crítico en la aplicación: {e}"
        print(error_msg)
        try:
            logger = logging.getLogger(__name__)
            logger.critical(error_msg, exc_info=True)
        except:
            pass
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)