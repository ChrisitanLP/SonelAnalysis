import os
import time
from config.settings import get_delays
from config.logger import logger
from extractors.base import BaseExtractor
from extractors.pyautowin_extractor.process_manager import ProcessManager
from extractors.pyautowin_extractor.file_tracker import FileTracker
from extractors.pyautowin_extractor.export_controller import ExportController
from extractors.pyautowin_extractor.window_controller import WindowController
from extractors.pyautowin_extractor.window_analysis import SonelAnalisisInicial
from extractors.pyautowin_extractor.window_configuration import SonelConfiguracion

class PywinautoExtractor(BaseExtractor):
    """
    Extractor robusto que usa pywinauto para automatizar Sonel Analysis
    Incluye seguimiento de archivos procesados y manejo de errores mejorado
    """
    
    def __init__(self, config, archivo_pqm=None):
        """
        Inicializa el extractor con pywinauto
        
        Args:
            config: Configuración del sistema
        """
        super().__init__(config)
        self.config = config
        
        # Configuración de rutas
        self.process_file_dir = config['PATHS'].get('process_file_dir', 'D:\\Universidad\\8vo Semestre\\Practicas\\Sonel\\data\\archivos_pqm')
        self.export_dir = config['PATHS'].get('export_dir', 'D:/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_csv')
        self.input_dir = config['PATHS'].get('input_dir',  '.\\data\\archivos_pqm\\')
        self.sonel_exe_path = config['PATHS'].get('sonel_exe_path', 'D:/Wolfly/Sonel/SonelAnalysis.exe')
        
        # Configuración de control
        self.auto_close_enabled = config.get('GUI', {}).get('auto_close_sonel', False)
        self.file_processing_delay = config.get('GUI', {}).get('delay_between_files', 5)
        self.delays = get_delays()

        # Configuración de timeouts
        self.timeout_short = 5
        self.timeout_medium = 10  
        self.timeout_long = 30

        self.app = None
        self.main_window = None
        self.analysis_window = None
        self.current_analysis_window = None

        # Modo debug
        self.debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        # Normalizar ruta de exportación
        self.export_dir = os.path.normpath(self.export_dir)
        
        # Asegurar que los directorios existen
        for directory in [self.export_dir, self.input_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

        # Archivo PQM
        self.archivo_pqm = archivo_pqm
        if not self.archivo_pqm:
            archivos_disponibles = os.listdir(self.input_dir)
            if archivos_disponibles:
                self.archivo_pqm = os.path.join(self.input_dir, archivos_disponibles[0])
            else:
                logger.error("❌ No hay archivos PQM disponibles en el directorio de entrada")
                self.archivo_pqm = None
        
        # Inicializar componentes especializados
        self.process_manager = ProcessManager(self)
        self.window_controller = WindowController(self)
        self.file_tracker = FileTracker(self)
        self.export_controller = ExportController(self)

        # CORRECCIÓN: Pasar self (parent_extractor) a las nuevas clases
        self.window_analysis = SonelAnalisisInicial(self)
        self.window_configuration = SonelConfiguracion(self)

    def extract(self):
        """
        Método principal que procesa todos los archivos .pqm702 encontrados
        
        Returns:
            List: Lista de archivos CSV generados exitosamente
        """
        logger.info("🚀 INICIANDO EXTRACCIÓN CON PYWINAUTO")
        start_time = time.time()

        try:
            # Obtener lista de archivos .pqm702
            pqm_files = self.file_tracker.get_pqm_files()
            if not pqm_files:
                logger.warning("⚠️ No se encontraron archivos .pqm702 para procesar")
                return None
            
            # Mostrar estadísticas de procesados
            stats = self.file_tracker.obtener_estadisticas_procesados()
            if stats["total"] > 0:
                logger.info(f"📊 ARCHIVOS YA PROCESADOS: {stats['total']}")
                logger.info(f"   Último procesado: {stats['ultimo_procesado']}")
            
            processed_files = []
            successful_exports = 0
            failed_files = []
            skipped_files = []
            
            for i, pqm_file in enumerate(pqm_files, 1):
                logger.info(f"ARCHIVO {i}/{len(pqm_files)}: {os.path.basename(pqm_file)}")
                
                result = self.export_controller.process_single_file(pqm_file)
                
                if result == "SKIPPED":
                    skipped_files.append(pqm_file)
                elif result:
                    processed_files.append(result)
                    successful_exports += 1
                else:
                    failed_files.append(pqm_file)
                    logger.error(f"❌ Archivo {i}/{len(pqm_files)} falló")
                
                # Pausa entre archivos
                if i < len(pqm_files):
                    time.sleep(3)
            
            # Resumen final
            total_time = time.time() - start_time
            logger.info(f"PROCESO COMPLETADO:")
            logger.info(f"   ✅ Exitosos: {successful_exports}")
            logger.info(f"   ⏭️  Omitidos: {len(skipped_files)}")
            logger.info(f"   ❌ Fallidos: {len(failed_files)}")
            logger.info(f"   ⏱️  Tiempo total: {total_time:.1f}s")

            return processed_files
            
        except KeyboardInterrupt:
            logger.info("\n⛔ PROCESO INTERRUMPIDO POR EL USUARIO")
            self.process_manager.close_sonel_analysis_force()
            return processed_files if 'processed_files' in locals() else []
        except Exception as e:
            logger.error(f"\n💥 ERROR CRÍTICO DURANTE LA AUTOMATIZACIÓN: {e}")
            self.process_manager.close_sonel_analysis_force()
            return processed_files if 'processed_files' in locals() else []
        finally:
            try:
                self.process_manager.cleanup_sonel_processes()
                logger.info("🧹 Cleanup final completado")
            except:
                pass

    def enable_auto_close(self, enabled=True):
        """
        Método para habilitar/deshabilitar el cierre automático de Sonel
        
        Args:
            enabled: True para habilitar cierre automático, False para deshabilitarlo
        """
        self.auto_close_enabled = enabled
        logger.info(f"🔧 Cierre automático de Sonel: {'HABILITADO' if enabled else 'DESHABILITADO'}")


    def set_file_processing_delay(self, delay_seconds):
        """
        Configura el tiempo de espera entre archivos
        
        Args:
            delay_seconds: Tiempo en segundos para esperar entre archivos
        """
        self.file_processing_delay = max(1, int(delay_seconds))
    
    def extract_single_file(self, pqm_file_path):
        """
        Extrae datos de un solo archivo .pqm702
        
        Args:
            pqm_file_path: Ruta al archivo .pqm702
            
        Returns:
            Ruta del archivo CSV generado o None si hay errores
        """
        return self.export_controller.process_single_file(pqm_file_path)
    

    def cleanup(self):
        """
        Limpia recursos y cierra aplicaciones si es necesario
        """
        try:
            if hasattr(self, 'app') and self.app:
                # Opcional: cerrar aplicación si fue iniciada por nosotros
                logger.info("🧹 Limpiando recursos de pywinauto")
            
        except Exception as e:
            logger.debug(f"Error durante cleanup: {e}")

    def __del__(self):
        """Destructor para asegurar limpieza"""
        self.cleanup()