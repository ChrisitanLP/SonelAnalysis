import os
import time
import pyautogui
import pyperclip
from pathlib import Path
from config.logger import logger
from core.utils.gui_helpers import GUIHelpers

class ExportController:
    """Maneja la configuración de mediciones y exportación a CSV"""
    
    def __init__(self, extractor):
        """
        Inicializa el controlador de exportación
        
        Args:
            extractor: Instancia del GUIExtractor principal
        """
        self.extractor = extractor
        self.config = extractor.config
        self.export_dir = extractor.export_dir
        self.coordinates = extractor.coordinates
        self.delays = extractor.delays
        
        # Referencias a otros componentes
        self.window_controller = extractor.window_controller
        self.file_tracker = extractor.file_tracker
        self.process_manager = extractor.process_manager
    
    def configure_measurements_and_export(self, pqm_file_path):
        """
        Configura las mediciones y exporta a CSV usando las coordenadas exactas
        
        Args:
            pqm_file_path: Ruta del archivo .pqm702 original
            
        Returns:
            str: Ruta del archivo CSV generado o None si hay error
        """
        try:
            csv_base_name = self.file_tracker.generate_csv_filename(pqm_file_path)
            csv_filename = f"{csv_base_name}.csv"
            csv_path = os.path.join(self.export_dir, csv_filename)
            
            if not self.window_controller.find_and_activate_sonel_window():
                logger.error("No se pudo activar ventana para configurar")
                return None
            
            # Configuración de mediciones (simplificado en logs)
            main_steps = [
                (self.coordinates['config_1'], "Config 1", self.delays['after_menu']),
                (self.coordinates['analisis_datos'], "Análisis de Datos", self.delays['after_menu']),
                (self.coordinates['mediciones'], "Mediciones", self.delays['after_menu']),
                (self.coordinates['check_usuario'], "Checkbox usuario", self.delays['between_clicks']),
            ]
            
            for coords, description, delay in main_steps:
                if not self.window_controller.safe_click(coords[0], coords[1], description, delay):
                    logger.error(f"❌ Falló paso crítico: {description}")
                    return None
            
            # Continuar con exportación
            export_steps = [
                (self.coordinates['tabla_esquina'], "Confirmar selección", self.delays['before_export']),
                (self.coordinates['informes'], "Menú Informes", self.delays['after_menu']),
                (self.coordinates['exportar_csv'], "Exportar CSV", self.delays['after_menu']),
            ]
            
            for coords, description, delay in export_steps:
                if not self.window_controller.safe_click(coords[0], coords[1], description, delay):
                    logger.error(f"❌ Falló paso de exportación: {description}")
                    return None
            
            # Escribir nombre del archivo con el nombre correcto
            if not self.window_controller.safe_click(
                self.coordinates['dialogo_nombre'][0], 
                self.coordinates['dialogo_nombre'][1], 
                "Campo nombre archivo", 
                self.delays['file_naming']
            ):
                logger.error("❌ No se pudo acceder al campo de nombre")
                return None
            
            # Limpiar campo y escribir ruta completa
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            
            # Escribir ruta completa usando path normalizado
            full_path = os.path.normpath(csv_path)   
            pyperclip.copy(full_path)
            pyautogui.hotkey('ctrl', 'v')

            time.sleep(0.5)
            
            logger.info(f"💾 Guardando archivo como: {csv_filename}")
            pyautogui.press('enter')
            
            # Esperar y verificar creación del archivo
            time.sleep(self.delays['after_export'])
            
            # Verificar que el archivo se haya creado
            if self._verify_file_creation(csv_path):
                file_size = os.path.getsize(csv_path)
                logger.info(f"✅ Archivo verificado: {csv_filename} ({file_size:,} bytes)")
                return csv_path
            else:
                logger.error(f"❌ No se pudo verificar la creación del archivo: {csv_path}")
                return None
            
        except Exception as e:
            logger.error(f"Error durante configuración y exportación: {e}")
            return None
    
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
                GUIHelpers.debug_log(f"OMITIDO: {os.path.basename(pqm_file_path)} (ya procesado)")
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
                if self.extractor.auto_close_enabled:
                    self.process_manager.close_sonel_analysis_force()
                return None
            
            # Cierre condicional
            if self.extractor.auto_close_enabled:
                self.process_manager.close_sonel_analysis_force()
                time.sleep(self.delays.get('between_files', 2))
            else:
                GUIHelpers.debug_log("🔄 Exportación completada, Sonel permanece abierto")
            
            # Verificación final y resumen
            if os.path.exists(csv_path):
                elapsed_time = time.time() - start_time
                
                # Registrar archivo como procesado
                self.file_tracker.registrar_archivo_procesado(pqm_file_path)
                
                logger.info(f"🎉 ÉXITO: {os.path.basename(csv_path)} ({elapsed_time:.1f}s)")
                return csv_path
            else:
                logger.error(f"❌ Archivo CSV no encontrado después de procesamiento: {csv_path}")
                return None
                
        except KeyboardInterrupt:
            logger.info("⛔ Procesamiento interrumpido por el usuario")
            if self.extractor.auto_close_enabled:
                self.process_manager.close_sonel_analysis_force()
            return None
        except Exception as e:
            logger.error(f"❌ Error crítico procesando {pqm_file_path}: {e}")
            if self.extractor.auto_close_enabled:
                self.process_manager.close_sonel_analysis_force()
            return None
        

    def _verify_file_creation(self, csv_path, max_attempts=8):
        """
        Verifica la creación del archivo CSV
        
        Args:
            csv_path: Ruta del archivo a verificar
            max_attempts: Número máximo de intentos de verificación
            
        Returns:
            bool: True si el archivo fue creado exitosamente
        """
        verification_attempts = 0
        
        while verification_attempts < max_attempts:
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                if file_size > 100:  # Archivo debe tener contenido mínimo
                    return True
                else:
                    GUIHelpers.debug_log(f"⚠️ Archivo existe pero muy pequeño ({file_size} bytes)")
            
            verification_attempts += 1
            time.sleep(self.delays['file_verification'])
            GUIHelpers.debug_log(f"Verificación {verification_attempts}/{max_attempts} - Buscando: {csv_path}")
        
        return False
