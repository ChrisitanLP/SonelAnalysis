import os
import time
import logging
from pathlib import Path
from config.settings import get_delays
from pywinauto import Application, findwindows
from pywinauto.controls.uia_controls import TreeItemWrapper, ButtonWrapper
from pywinauto.timings import wait_until
from config.logger import logger
from extractors.base import BaseExtractor
from datetime import datetime
from extractors.pyautowin_extractor.process_manager import ProcessManager
from extractors.pyautowin_extractor.file_tracker import FileTracker

class PywinautoExtractor(BaseExtractor):
    """
    Extractor robusto que usa pywinauto para automatizar Sonel Analysis
    Incluye seguimiento de archivos procesados y manejo de errores mejorado
    """
    
    def __init__(self, config):
        """
        Inicializa el extractor con pywinauto
        
        Args:
            config: Configuración del sistema
        """
        super().__init__(config)
        self.config = config
        
        # Configuración de rutas
        self.process_file_dir = config['PATHS'].get('process_file_dir', 'D:/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_pqm')
        self.export_dir = config['PATHS'].get('export_dir', 'D:/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_csv')
        self.input_dir = config['PATHS'].get('input_dir', './data/archivos_pqm/')
        self.sonel_exe_path = config['PATHS'].get('sonel_exe_path', 'D:/Wolfly/Sonel/SonelAnalysis.exe')
        
        # Configuración de control
        self.auto_close_enabled = config.get('GUI', {}).get('auto_close_sonel', False)
        self.file_processing_delay = config.get('GUI', {}).get('delay_between_files', 5)
        self.delays = get_delays()

        # Configuración de timeouts
        self.timeout_short = 5
        self.timeout_medium = 10  
        self.timeout_long = 30
        
        # Normalizar ruta de exportación
        self.export_dir = os.path.normpath(self.export_dir)
        
        # Asegurar que los directorios existen
        for directory in [self.export_dir, self.input_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        # Inicializar componentes especializados
        self.process_manager = ProcessManager(self)
        self.file_tracker = FileTracker(self)
    
    def get_pqm_files(self):
        """
        Obtiene lista de archivos .pqm702 en el directorio de entrada
        
        Returns:
            Lista de rutas de archivos .pqm702
        """
        try:
            if not os.path.exists(self.input_dir):
                logger.error(f"❌ Directorio de entrada no existe: {self.input_dir}")
                return []
            
            pqm_files = []
            for file in os.listdir(self.input_dir):
                if file.lower().endswith('.pqm702'):
                    pqm_files.append(os.path.join(self.input_dir, file))
            
            # Ordenar archivos para procesamiento consistente
            pqm_files.sort()
            
            logger.info(f"📋 Encontrados {len(pqm_files)} archivos .pqm702 en {self.input_dir}")
            for i, file in enumerate(pqm_files, 1):
                logger.info(f"   {i}. {os.path.basename(file)}")
            
            return pqm_files
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos .pqm702: {e}")
            return []
    
    def connect_to_sonel(self):
        """
        Conecta a una instancia existente de Sonel Analysis o la inicia
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            # Intentar conectar a proceso existente
            try:
                processes = findwindows.find_elements(title_re=".*Análisis.*", backend="uia")
                if not processes:
                    processes = findwindows.find_elements(title_re=".*Analysis.*", backend="uia")
                
                if processes:
                    logger.info("🔗 Conectando a instancia existente de Sonel Analysis")
                    self.app = Application(backend="uia").connect(handle=processes[0].handle)
                    return True
            except:
                pass
            
            # Si no hay proceso, intentar iniciar nuevo
            if os.path.exists(self.sonel_exe_path):
                logger.info("🚀 Iniciando nueva instancia de Sonel Analysis")
                self.app = Application(backend="uia").start(self.sonel_exe_path)
                time.sleep(self.timeout_long)  # Esperar arranque completo
                return True
            else:
                logger.error(f"❌ Ejecutable no encontrado: {self.sonel_exe_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando a Sonel Analysis: {e}")
            return False
    
    def find_analysis_window(self):
        """
        Busca y selecciona la ventana de análisis activa
        
        Returns:
            bool: True si encuentra la ventana
        """
        try:
            # Buscar ventana que contenga "Análisis" en el título
            windows = self.app.windows()
            
            for window in windows:
                try:
                    title = window.window_text()
                    if ("Análisis" in title or "Analysis" in title) and "[/" in title:
                        logger.info(f"📋 Ventana de análisis encontrada: {title}")
                        self.current_analysis_window = window
                        
                        # Asegurar que la ventana esté activa
                        if window.is_minimized():
                            window.restore()
                        window.set_focus()
                        time.sleep(self.delays['window_activation'])
                        
                        return True
                except Exception as e:
                    logger.debug(f"Error examinando ventana: {e}")
                    continue
            
            logger.warning("⚠️ No se encontró ventana de análisis")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error buscando ventana de análisis: {e}")
            return False
    
    
    def configure_second_window(self):
        """
        Configura la segunda ventana de análisis con las opciones requeridas
        
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            # Esperar a que aparezca la nueva ventana
            time.sleep(self.delays['ui_response'])
            
            # Buscar nueva ventana de análisis (con "Norma, Usuario" en título)
            if not self.find_analysis_window():
                logger.error("❌ No se encontró la segunda ventana de análisis")
                return False
            
            logger.info("🔧 Configurando segunda ventana de análisis")
            
            # 1. Activar checkbox "Mediciones"
            if not self._activate_checkbox("Mediciones"):
                if not self._activate_checkbox("Measurements"):
                    logger.warning("⚠️ No se pudo activar 'Mediciones/Measurements'")
            
            # 2. Activar radiobutton "Usuario" 
            if not self._activate_radiobutton("Usuario"):
                if not self._activate_radiobutton("User"):
                    logger.warning("⚠️ No se pudo activar 'Usuario/User'")
            
            # 3. Activar checkbox "Máx." en grupo "Mostrar valores"
            if not self._activate_checkbox("Máx."):
                if not self._activate_checkbox("Max."):
                    logger.warning("⚠️ No se pudo activar 'Máx./Max.'")
            
            # 4. Activar checkbox "Mín." si está disponible
            if not self._activate_checkbox("Mín."):
                if not self._activate_checkbox("Min."):
                    logger.info("ℹ️ 'Mín./Min.' no disponible o ya activado")
            
            logger.info("✅ Configuración de segunda ventana completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando segunda ventana: {e}")
            return False
    
    