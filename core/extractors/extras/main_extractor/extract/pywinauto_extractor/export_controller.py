import os
import time
from pathlib import Path
from config.logger import logger
from pywinauto import Application

class ExportController:
    """Maneja la configuración de mediciones y exportación a CSV"""
    
    def __init__(self, parent_extractor):
        """
        Inicializa el controlador de exportación
        
        Args:
            extractor: Instancia del GUIExtractor principal
        """
        self.parent_extractor = parent_extractor
        self.config = parent_extractor.config
        self.export_dir = parent_extractor.export_dir
        self.delays = parent_extractor.delays
        
        # Referencias a otros componentes
        self.file_tracker = parent_extractor.file_tracker
        self.process_manager = parent_extractor.process_manager
        self.window_controller = parent_extractor.window_controller

        self.sonel_exe_path = parent_extractor.sonel_exe_path
        self.archivo_pqm = parent_extractor.archivo_pqm

    def process_single_file(self, pqm_file_path):
        """
        Procesa un solo archivo .pqm702 con verificación de procesados
        
        Args:
            pqm_file_path: Ruta al archivo .pqm702
            
        Returns:
            str: Ruta del archivo CSV generado, "SKIPPED" si ya fue procesado, o None si hay error
        """
        start_time = time.time()
        
        try:
            file_name = Path(pqm_file_path).stem
            
            # Verificar si ya fue procesado
            if self.file_tracker.ya_ha_sido_procesado(pqm_file_path):
                logger.info(f"OMITIDO: {os.path.basename(pqm_file_path)} (ya procesado)")
                return "SKIPPED"  # Valor especial para indicar que se omitió
            
            logger.info(f"📁 PROCESANDO: {os.path.basename(pqm_file_path)}")
            
            # Verificar que el archivo existe
            if not os.path.exists(pqm_file_path):
                logger.error(f"❌ Archivo no encontrado: {pqm_file_path}")
                return None
            
            # Paso 1: Abrir archivo con Sonel Analysis
            if not self.process_manager.open_file_with_sonel(pqm_file_path):
                logger.error("❌ Falló apertura del archivo")
                return None
            
            # Paso 2: Configurar mediciones y exportar
            csv_path = self.configure_measurements_and_export(pqm_file_path)
            
            if not csv_path:
                logger.error("❌ Falló configuración y exportación")
            #    if self.parent_extractor.auto_close_enabled:
            #        self.process_manager.close_sonel_analysis_force()
                return None
            
            # Cierre condicional
            #if self.parent_extractor.auto_close_enabled:
            #    self.process_manager.close_sonel_analysis_force()
            #    time.sleep(self.delays.get('between_files', 2))
            else:
                logger.debug("🔄 Exportación completada, Sonel permanece abierto")
            
            # Verificación final y resumen
            expected_csv_path = os.path.join(self.export_dir, f"{file_name}.csv")
            if os.path.exists(expected_csv_path):
                elapsed_time = time.time() - start_time
                
                # Registrar archivo como procesado
                self.file_tracker.registrar_archivo_procesado(pqm_file_path, expected_csv_path)
                
                logger.info(f"🎉 ÉXITO: {os.path.basename(expected_csv_path)} ({elapsed_time:.1f}s)")
                return expected_csv_path
            else:
                logger.error(f"❌ Archivo CSV no encontrado después de procesamiento: {expected_csv_path}")
        except KeyboardInterrupt:
            logger.info("⛔ Procesamiento interrumpido por el usuario")
            if self.parent_extractor.auto_close_enabled:
                self.process_manager.close_sonel_analysis_force()
            return None
        except Exception as e:
            logger.error(f"❌ Error crítico procesando {pqm_file_path}: {e}")
            if self.parent_extractor.auto_close_enabled:
                self.process_manager.close_sonel_analysis_force()
            return None
        
    def configure_measurements_and_export(self, pqm_file_path):
        """
        Configura mediciones y ejecuta exportación completa
        
        Args:
            pqm_file_path: Ruta al archivo .pqm702
            
        Returns:
            str: Ruta del archivo CSV generado o None si hay error
        """
        try:
            # Conectar al controlador de ventanas
            if not self.window_controller.connect_to_sonel():
                logger.error("❌ No se pudo conectar a Sonel Analysis")
                return None
            
            # 1. Configurar primera ventana (Análisis inicial)
            logger.info("📊 Configurando primera ventana (Análisis inicial)...")
            extractor_inicial = self.parent_extractor.window_analysis
            
            # CORRECCIÓN: Llamar al método, no evaluar como atributo
            resultado_inicial = extractor_inicial.configuracion_primera_ventana()
            if not resultado_inicial:
                logger.error("❌ Falló configuración de primera ventana")
                return None
            logger.info("✅ Primera ventana configurada exitosamente")

            # 2. Configurar segunda ventana (Configuración de mediciones)
            logger.info("⚙️ Configurando segunda ventana (Configuración)...")
            extractor_config = self.parent_extractor.window_configuration
            
            # CORRECCIÓN: Llamar al método, no evaluar como atributo
            resultado_config = extractor_config.configuracion_segunda_ventana()
            if not resultado_config:
                logger.error("❌ Falló configuración de segunda ventana")
                return None
            logger.info("✅ Segunda ventana configurada exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error en configuración y exportación: {e}")
            return None