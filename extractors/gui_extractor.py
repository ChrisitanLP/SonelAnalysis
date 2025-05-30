import os
import time
from config.logger import logger
from extractors.base import BaseExtractor
from .gui_automation.process_manager import ProcessManager
from .gui_automation.window_controller import WindowController
from .gui_automation.file_tracker import FileTracker
from .gui_automation.export_controller import ExportController
from utils.gui_helpers import GUIHelpers
from utils.file_helpers import FileHelpers


class GUIExtractor(BaseExtractor):
    """
    Orquestador principal para la automatización GUI de Sonel Analysis.
    Coordina todos los módulos especializados para el procesamiento masivo de archivos .pqm702
    """
    
    def __init__(self, config):
        """
        Inicializa el extractor GUI con todos sus módulos especializados
        
        Args:
            config: Configuración del sistema con paths, delays, etc.
        """
        super().__init__(config)
        
        self.config = config
        self.input_dir = config['PATHS'].get('input_dir', 
                                           'D:/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_pqm')
        self.debug_mode = config.get('debug_mode', False)
        
        # Inicializar módulos especializados
        self.process_manager = ProcessManager(config)
        self.window_controller = WindowController(config)
        self.file_tracker = FileTracker(config)
        self.export_controller = ExportController(config)
        
        # Configuraciones de procesamiento
        self.file_processing_delay = config.get('DELAYS', {}).get('between_files', 3)
        self.auto_close_enabled = config.get('GUI', {}).get('auto_close_sonel', False)
        
        GUIHelpers.debug_log("GUIExtractor inicializado correctamente", self.debug_mode)
        logger.info("🎯 GUIExtractor preparado para automatización")

    def get_pqm_files(self):
        """
        Obtiene lista de archivos .pqm702 en el directorio de entrada
        
        Returns:
            list: Lista de rutas de archivos .pqm702 ordenadas alfabéticamente
        """
        try:
            if not os.path.exists(self.input_dir):
                logger.error(f"❌ Directorio de entrada no existe: {self.input_dir}")
                return []
            
            pqm_files = FileHelpers.get_files_by_extension(
                self.input_dir, 
                '.pqm702', 
                sort_files=True
            )
            
            logger.info(f"📋 Encontrados {len(pqm_files)} archivos .pqm702 en {self.input_dir}")
            
            if self.debug_mode:
                for i, file in enumerate(pqm_files, 1):
                    GUIHelpers.debug_log(f"   {i}. {os.path.basename(file)}", self.debug_mode)
            
            return pqm_files
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos .pqm702: {e}")
            return []

    def process_single_file(self, pqm_file_path):
        """
        Procesa un archivo .pqm702 individual siguiendo el flujo completo de automatización
        
        Args:
            pqm_file_path: Ruta completa al archivo .pqm702
            
        Returns:
            str: Ruta del archivo CSV generado, "SKIPPED" si ya fue procesado, None si hay error
        """
        filename = os.path.basename(pqm_file_path)
        
        try:
            GUIHelpers.debug_log(f"Iniciando procesamiento: {filename}", self.debug_mode)
            
            # Paso 1: Verificar si ya fue procesado
            if self.file_tracker.ya_ha_sido_procesado(pqm_file_path):
                logger.info(f"⏭️  OMITIDO (ya procesado): {filename}")
                return "SKIPPED"
            
            logger.info(f"🔄 PROCESANDO: {filename}")
            
            # Paso 2: Cleanup inicial si está habilitado
            if self.auto_close_enabled:
                self.process_manager.cleanup_sonel_processes()
            
            # Paso 3: Abrir archivo con Sonel Analysis
            GUIHelpers.debug_log("Abriendo archivo con Sonel Analysis", self.debug_mode)
            if not self.process_manager.open_file_with_sonel(pqm_file_path):
                logger.error(f"❌ No se pudo abrir el archivo: {filename}")
                return None
            
            # Paso 4: Esperar y activar ventana de Sonel
            GUIHelpers.debug_log("Esperando y activando ventana de Sonel", self.debug_mode)
            if not self.window_controller.wait_for_window("sonel", timeout=30):
                logger.error(f"❌ Timeout esperando ventana de Sonel para: {filename}")
                return None
            
            if not self.window_controller.find_and_activate_sonel_window():
                logger.error(f"❌ No se pudo activar ventana de Sonel para: {filename}")
                return None
            
            # Paso 5: Configurar mediciones y exportar datos
            GUIHelpers.debug_log("Iniciando configuración y exportación", self.debug_mode)
            csv_file_path = self.export_controller.configure_measurements_and_export(pqm_file_path)
            
            if not csv_file_path:
                logger.error(f"❌ Falló la exportación para: {filename}")
                return None
            
            # Paso 6: Registrar archivo como procesado
            self.file_tracker.registrar_archivo_procesado(pqm_file_path)
            
            # Paso 7: Cerrar Sonel Analysis de forma segura
            GUIHelpers.debug_log("Cerrando Sonel Analysis", self.debug_mode)
            if not self.process_manager.close_sonel_analysis_safely():
                logger.warning(f"⚠️ No se pudo cerrar Sonel completamente para: {filename}")
            
            logger.info(f"✅ COMPLETADO: {filename} → {os.path.basename(csv_file_path)}")
            return csv_file_path
            
        except KeyboardInterrupt:
            logger.info(f"⛔ Procesamiento interrumpido por usuario: {filename}")
            self._emergency_cleanup()
            raise
        except Exception as e:
            logger.error(f"❌ Error procesando {filename}: {e}")
            self._handle_processing_error(pqm_file_path, e)
            return None

    def extract(self):
        """
        Orquesta la extracción masiva de todos los archivos .pqm702
        
        Returns:
            list: Lista de archivos CSV generados exitosamente
        """
        logger.info("🚀 INICIANDO EXTRACCIÓN MASIVA CON AUTOMATIZACIÓN GUI")
        start_time = time.time()
        
        try:
            # Obtener lista de archivos a procesar
            pqm_files = self.get_pqm_files()
            if not pqm_files:
                logger.warning("⚠️ No se encontraron archivos .pqm702 para procesar")
                return []
            
            # Mostrar estadísticas de archivos ya procesados
            self._show_processing_statistics()
            
            # Inicializar contadores
            processed_files = []
            successful_exports = 0
            failed_files = []
            skipped_files = []
            
            # Procesar cada archivo
            for i, pqm_file in enumerate(pqm_files, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"ARCHIVO {i}/{len(pqm_files)}: {os.path.basename(pqm_file)}")
                logger.info(f"{'='*60}")
                
                # Procesar archivo individual
                result = self.process_single_file(pqm_file)
                
                # Contabilizar resultado
                if result == "SKIPPED":
                    skipped_files.append(pqm_file)
                elif result:
                    processed_files.append(result)
                    successful_exports += 1
                else:
                    failed_files.append(pqm_file)
                
                # Pausa entre archivos (excepto el último)
                if i < len(pqm_files):
                    GUIHelpers.stabilization_pause(
                        self.file_processing_delay,
                        file_number=i,
                        total_files=len(pqm_files)
                    )
            
            # Mostrar resumen final
            self._show_final_summary(
                pqm_files, processed_files, skipped_files, 
                failed_files, start_time
            )
            
            return processed_files
            
        except KeyboardInterrupt:
            logger.info("\n⛔ PROCESO INTERRUMPIDO POR EL USUARIO")
            self._emergency_cleanup()
            return processed_files if 'processed_files' in locals() else []
        except Exception as e:
            logger.error(f"\n💥 ERROR CRÍTICO DURANTE LA AUTOMATIZACIÓN: {e}")
            self._emergency_cleanup()
            return processed_files if 'processed_files' in locals() else []
        finally:
            self._final_cleanup()

    def extract_single_file(self, pqm_file_path):
        """
        Interfaz pública para extraer datos de un solo archivo .pqm702
        
        Args:
            pqm_file_path: Ruta al archivo .pqm702
            
        Returns:
            str: Ruta del archivo CSV generado o None si hay errores
        """
        logger.info(f"🎯 EXTRACCIÓN INDIVIDUAL: {os.path.basename(pqm_file_path)}")
        
        try:
            result = self.process_single_file(pqm_file_path)
            
            if result == "SKIPPED":
                logger.info("⏭️ Archivo ya había sido procesado anteriormente")
                return None
            elif result:
                logger.info(f"✅ Extracción individual completada: {os.path.basename(result)}")
                return result
            else:
                logger.error("❌ Falló la extracción individual")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error en extracción individual: {e}")
            return None
        finally:
            self._final_cleanup()

    def enable_auto_close(self, enabled=True):
        """
        Habilita/deshabilita el cierre automático de Sonel Analysis
        
        Args:
            enabled: True para habilitar, False para deshabilitar
        """
        self.auto_close_enabled = enabled
        self.process_manager.auto_close_enabled = enabled
        logger.info(f"🔧 Cierre automático de Sonel: {'HABILITADO' if enabled else 'DESHABILITADO'}")

    def set_file_processing_delay(self, delay_seconds):
        """
        Configura el tiempo de espera entre procesamiento de archivos
        
        Args:
            delay_seconds: Tiempo en segundos (mínimo 1)
        """
        self.file_processing_delay = max(1, int(delay_seconds))
        logger.info(f"⏱️ Delay entre archivos configurado: {self.file_processing_delay}s")

    def get_processing_status(self):
        """
        Obtiene el estado actual del sistema de procesamiento
        
        Returns:
            dict: Estado del sistema con estadísticas de archivos y procesos
        """
        try:
            pqm_files = self.get_pqm_files()
            processed_stats = self.file_tracker.obtener_estadisticas_procesados()
            process_status = self.process_manager.get_process_status()
            export_stats = self.export_controller.get_export_statistics()
            
            status = {
                'total_pqm_files': len(pqm_files),
                'processed_files': processed_stats['total'],
                'pending_files': len(pqm_files) - processed_stats['total'],
                'last_processed': processed_stats.get('ultimo_procesado', 'N/A'),
                'sonel_windows_open': process_status['windows_count'],
                'sonel_processes_running': process_status['processes_running'],
                'auto_close_enabled': self.auto_close_enabled,
                'export_directory': export_stats['export_directory'],
                'total_csv_files': export_stats['total_files'],
                'total_export_size': export_stats['total_size_formatted']
            }
            
            GUIHelpers.debug_log(f"Estado del sistema: {status}", self.debug_mode)
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {e}")
            return {'error': str(e)}

    def _show_processing_statistics(self):
        """Muestra estadísticas de archivos ya procesados"""
        try:
            stats = self.file_tracker.obtener_estadisticas_procesados()
            if stats["total"] > 0:
                logger.info(f"📊 ARCHIVOS YA PROCESADOS: {stats['total']}")
                logger.info(f"   Último procesado: {stats['ultimo_procesado']}")
        except Exception as e:
            GUIHelpers.debug_log(f"Error mostrando estadísticas: {e}", self.debug_mode)

    def _show_final_summary(self, pqm_files, processed_files, skipped_files, failed_files, start_time):
        """Muestra resumen final de la extracción masiva"""
        try:
            total_time = time.time() - start_time
            
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 PROCESO COMPLETADO")
            logger.info(f"{'='*60}")
            logger.info(f"   📁 Total archivos: {len(pqm_files)}")
            logger.info(f"   ✅ Exitosos: {len(processed_files)}")
            logger.info(f"   ⏭️  Omitidos: {len(skipped_files)}")
            logger.info(f"   ❌ Fallidos: {len(failed_files)}")
            logger.info(f"   ⏱️  Tiempo total: {total_time:.1f}s")
            
            if processed_files:
                logger.info(f"\n📋 Archivos CSV generados ({len(processed_files)}):")
                for csv_file in processed_files:
                    if os.path.exists(csv_file):
                        file_size = FileHelpers.get_file_size_formatted(csv_file)
                        logger.info(f"   ✅ {os.path.basename(csv_file)} ({file_size})")
            
            if skipped_files:
                logger.info(f"\n⏭️  Archivos omitidos ({len(skipped_files)}):")
                for skipped_file in skipped_files:
                    logger.info(f"   ⏭️  {os.path.basename(skipped_file)}")
            
            if failed_files:
                logger.info(f"\n❌ Archivos que fallaron ({len(failed_files)}):")
                for failed_file in failed_files:
                    logger.info(f"   ❌ {os.path.basename(failed_file)}")
                    
        except Exception as e:
            logger.error(f"Error mostrando resumen final: {e}")

    def _handle_processing_error(self, pqm_file_path, error):
        """Maneja errores durante el procesamiento de archivos"""
        try:
            filename = os.path.basename(pqm_file_path)
            GUIHelpers.debug_log(f"Manejando error para {filename}: {error}", self.debug_mode)
            
            # Intentar cerrar Sonel si hay ventanas abiertas
            if self.window_controller.get_sonel_windows_count() > 0:
                self.process_manager.close_sonel_analysis_safely()
                
        except Exception as cleanup_error:
            logger.warning(f"Error durante cleanup de error: {cleanup_error}")

    def _emergency_cleanup(self):
        """Cleanup de emergencia en caso de interrupción"""
        try:
            logger.info("🚨 Ejecutando limpieza de emergencia...")
            self.process_manager.manual_close_all_sonel()
        except Exception as e:
            logger.error(f"Error en cleanup de emergencia: {e}")

    def _final_cleanup(self):
        """Cleanup final del sistema"""
        try:
            GUIHelpers.debug_log("Ejecutando cleanup final", self.debug_mode)
            
            if self.auto_close_enabled:
                self.process_manager.cleanup_sonel_processes()
                
            logger.info("🧹 Cleanup final completado")
            
        except Exception as e:
            logger.warning(f"Error en cleanup final: {e}")