# core/controller/sonel_controller_enhanced.py
"""
Controlador mejorado con sistema de callbacks para tiempo real
"""

import os
import sys
import time
import logging
import traceback
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, Callable

from core.etl.sonel_etl_enhanced import SonelETLEnhanced
from core.utils.callbacks import ProcessingCallbackManager, ProcessingEventType, ProcessingEvent
from config.logger import get_logger
from core.database.connection import DatabaseConnection
from core.extractors.pywin_extractor import SonelExtractorCompleto
from config.settings import get_full_config, validate_configuration, validate_screen_resolution, load_config


class SonelControllerEnhanced:
    """
    Controlador mejorado con sistema de callbacks para actualizaciones en tiempo real
    """

    def __init__(self, config_file: Optional[str] = None, summary_file_path: Optional[str] = None):
        """
        Inicializa el controlador mejorado
        
        Args:
            config_file: Ruta al archivo de configuración (opcional)
            summary_file_path: Ruta donde guardar el archivo de resumen
        """

        self.config_file = config_file or os.path.join("config", "config.ini")
        self.win_config = get_full_config()
        
        # Configurar logger
        self.logger = get_logger("sonel_controller_enhanced", f"{__name__}_controller")
        self.logger.setLevel(getattr(logging, self.win_config['LOGGING']['level']))
        
        # Configurar rutas
        self.rutas = self._configurar_rutas()
        
        # Inicializar gestor de callbacks
        default_summary_path = os.path.join(self.rutas["output_directory"], "processing_summary.json")
        self.callback_manager = ProcessingCallbackManager(summary_file_path or default_summary_path)
        
        # Callbacks externos registrados
        self.external_callbacks = []
        
        self.logger.info("🎯 Controlador Sonel Enhanced inicializado correctamente")

    def _configurar_rutas(self) -> Dict[str, str]:
        """Configura las rutas de trabajo"""
        base_dir = Path.cwd()
        
        rutas = {
            "input_directory": str(base_dir / self.win_config['PATHS']['input_dir']),
            "output_directory": str(base_dir / self.win_config['PATHS']['output_dir'])
        }
        
        # Crear directorios si no existen
        for ruta in rutas.values():
            os.makedirs(ruta, exist_ok=True)
        
        return rutas

    def register_progress_callback(self, callback: Callable[[ProcessingEvent], None]):
        """
        Registra un callback para recibir actualizaciones en tiempo real
        
        Args:
            callback: Función que será llamada cuando ocurra un evento
        """
        self.callback_manager.register_callback(callback)
        self.external_callbacks.append(callback)
        self.logger.info("📡 Callback de progreso registrado")

    def unregister_progress_callback(self, callback: Callable[[ProcessingEvent], None]):
        """
        Desregistra un callback
        
        Args:
            callback: Función a desregistrar
        """
        self.callback_manager.unregister_callback(callback)
        if callback in self.external_callbacks:
            self.external_callbacks.remove(callback)
        self.logger.info("📡 Callback de progreso desregistrado")

    def run_etl_processing_with_callbacks(self, force_reprocess: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecuta el procesamiento ETL con callbacks en tiempo real
        
        Args:
            force_reprocess: Si True, reprocesa todos los archivos ignorando el registro
            
        Returns:
            tuple: (success: bool, summary_data: dict) - Estado y resumen detallado
        """
        self.logger.info("🚀 === INICIANDO PROCESAMIENTO ETL CON CALLBACKS ===")
        
        # Emitir evento de inicio de fase
        self.callback_manager.emit_event(ProcessingEventType.PHASE_STARTED, {
            'phase_name': 'ETL_PROCESSING',
            'description': 'Procesamiento ETL de archivos CSV'
        })
        
        db_connection = None
        etl = None

        csv_directory = self.rutas["output_directory"]
        csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]
        total_csv_files = len(csv_files)
        
        # NUEVO: Emitir evento con archivos encontrados
        self.callback_manager.emit_event(ProcessingEventType.FILES_DISCOVERED, {
            'total_files': total_csv_files,
            'file_list': csv_files,
            'phase': 'ETL_PROCESSING'
        })
        
        try:
            # Inicializar conexión a base de datos
            etl_config = load_config(self.config_file)
            
            db_connection = DatabaseConnection(etl_config)
            if not db_connection.connect():
                self.logger.error("❌ No se pudo establecer conexión con la base de datos")
                self.callback_manager.emit_event(ProcessingEventType.PROCESS_FAILED, {
                    'error': 'No se pudo establecer conexión con la base de datos',
                    'phase': 'ETL_PROCESSING'
                })
                return False, self._get_error_summary("Error de conexión BD")
            
            self.logger.info("✅ Conexión a base de datos establecida")
            
            # Inicializar ETL mejorado con callbacks
            etl = SonelETLEnhanced(
                config_file=self.config_file,
                db_connection=db_connection,
                callback_manager=self.callback_manager
            )
            
            # Directorio donde están los CSV
            csv_directory = self.rutas["output_directory"]
            self.logger.info(f"📂 Procesando archivos CSV desde: {csv_directory}")
            
            # Ejecutar procesamiento ETL
            success = etl.run(
                extraction_method='file',
                directory=csv_directory,
                force_reprocess=force_reprocess
            )
            
            # Emitir evento de fase completada
            self.callback_manager.emit_event(ProcessingEventType.PHASE_COMPLETED, {
                'phase_name': 'ETL_PROCESSING',
                'success': success,
                'files_processed': etl.registry.get_processing_stats()['total_files']
            })
            
            # Generar resumen
            if success:
                self.logger.info("✅ Procesamiento ETL completado exitosamente")
                summary_data = etl.get_complete_summary_for_gui()
                self._log_summary(summary_data)
                return True, summary_data
            else:
                self.logger.warning("⚠️ El procesamiento ETL se completó con advertencias")
                summary_data = etl.get_complete_summary_for_gui()
                self._log_summary(summary_data)
                return True, summary_data
                    
        except Exception as e:
            self.logger.error(f"❌ Error durante procesamiento ETL: {e}")
            self.logger.error(traceback.format_exc())
            
            # Emitir evento de error
            self.callback_manager.emit_event(ProcessingEventType.PROCESS_FAILED, {
                'error': str(e),
                'phase': 'ETL_PROCESSING',
                'traceback': traceback.format_exc()
            })
            
            return False, self._get_error_summary(f"Error ETL: {str(e)}")
            
        finally:
            # Limpieza de recursos
            if etl:
                etl.close()
            if db_connection:
                db_connection.close()
            self.logger.info("🧹 Recursos liberados correctamente")

    def run_pywinauto_extraction_with_callbacks(self) -> Tuple[bool, int]:
        """
        Ejecuta la extracción GUI usando pywinauto con callbacks
        
        Returns:
            tuple: (success: bool, extracted_files: int)
        """
        self.logger.info("🚀 === INICIANDO EXTRACCIÓN PYWIN CON CALLBACKS ===")
        
        # Emitir evento de inicio de fase
        self.callback_manager.emit_event(ProcessingEventType.PHASE_STARTED, {
            'phase_name': 'PYWIN_EXTRACTION',
            'description': 'Extracción de archivos usando PyWinAuto'
        })
        
        try:
            # Verificar requisitos
            if not self.validate_environment():
                self.logger.error("❌ No se pueden cumplir los requisitos del sistema")
                self.callback_manager.emit_event(ProcessingEventType.PROCESS_FAILED, {
                    'error': 'No se pueden cumplir los requisitos del sistema',
                    'phase': 'PYWIN_EXTRACTION'
                })
                return False, 0
            
            # NUEVO: Obtener información de archivos antes del procesamiento
            folder_info = self.get_folder_info(self.rutas["input_directory"])
            total_files = folder_info.get('count', 0)
            
            # NUEVO: Emitir evento con total de archivos
            self.callback_manager.emit_event(ProcessingEventType.FILES_DISCOVERED, {
                'total_files': total_files,
                'file_list': folder_info.get('files', [])
            })
            
            # Crear instancia del extractor
            self.logger.info("🔧 Inicializando extractor...")
            
            # NUEVO: Crear wrapper del extractor que emita eventos
            extractor = SonelExtractorCompleto(
                input_dir=self.rutas["input_directory"],
                output_dir=self.rutas["output_directory"], 
                ruta_exe=self.win_config['PATHS']['sonel_exe_path']
            )
            
            # MODIFICADO: Ejecutar con monitoreo de archivos individuales
            self.logger.info("🎯 Iniciando procesamiento completo...")
            
            # Simular procesamiento archivo por archivo para demos en tiempo real
            if hasattr(extractor, 'ejecutar_con_callbacks'):
                # Si el extractor soporta callbacks nativos, usarlos
                resultados = extractor.ejecutar_con_callbacks(self.callback_manager)
            else:
                # Fallback: ejecutar normal pero simular eventos para la GUI
                resultados = self._ejecutar_extraccion_con_eventos_simulados(extractor, total_files)
            
            # Validar resultados
            if not self._validar_resultados_extraccion(resultados):
                self.callback_manager.emit_event(ProcessingEventType.PROCESS_FAILED, {
                    'error': 'Resultados de extracción inválidos',
                    'phase': 'PYWIN_EXTRACTION'
                })
                return False, 0
            
            # Procesar resultados
            success, extracted_files = self._procesar_resultados_extraccion(resultados)
            
            # Emitir evento de fase completada
            self.callback_manager.emit_event(ProcessingEventType.PHASE_COMPLETED, {
                'phase_name': 'PYWIN_EXTRACTION',
                'success': success,
                'files_processed': extracted_files,
                'total_files': total_files
            })
            
            return success, extracted_files
            
        except Exception as e:
            self.logger.error(f"❌ Error durante extracción PYWIN: {e}")
            self.logger.error(traceback.format_exc())
            
            # Emitir evento de error
            self.callback_manager.emit_event(ProcessingEventType.PROCESS_FAILED, {
                'error': str(e),
                'phase': 'PYWIN_EXTRACTION',
                'traceback': traceback.format_exc()
            })
            
            return False, 0

    def run_complete_workflow_with_callbacks(self, force_reprocess: bool = False, 
                                            skip_gui: bool = False, skip_etl: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecuta el flujo completo con callbacks: extracción GUI + procesamiento ETL
        
        Args:
            force_reprocess: Fuerza el reprocesamiento en ETL
            skip_gui: Omite la extracción GUI
            skip_etl: Omite el procesamiento ETL
            
        Returns:
            tuple: (success: bool, complete_summary: dict) - Estado y resumen completo
        """
        self.logger.info("🎯 === INICIANDO FLUJO COMPLETO SONEL CON CALLBACKS ===")
        start_time = time.time()
        
        # Emitir evento de inicio del proceso completo
        self.callback_manager.emit_event(ProcessingEventType.PROCESS_STARTED, {
            'workflow_type': 'complete',
            'skip_gui': skip_gui,
            'skip_etl': skip_etl,
            'force_reprocess': force_reprocess
        })
        
        # Validar entorno
        if not self.validate_environment():
            self.logger.error("❌ Validación de entorno fallida")
            self.callback_manager.emit_event(ProcessingEventType.PROCESS_FAILED, {
                'error': 'Validación de entorno fallida'
            })
            return False, self._get_error_summary("Validación de entorno fallida")
        
        gui_success = True
        extracted_files = 0
        
        # Paso 1: Extracción GUI (opcional)
        if not skip_gui:
            gui_success, extracted_files = self.run_pywinauto_extraction_with_callbacks()
            if not gui_success:
                self.logger.warning("⚠️ Extracción PYWIN falló, continuando con ETL...")
        else:
            self.logger.info("⏭️ Extracción PYWIN omitida por configuración")
        
        # Paso 2: Procesamiento ETL (opcional)
        etl_success = True
        db_summary = {}
        
        if not skip_etl:
            etl_success, db_summary = self.run_etl_processing_with_callbacks(force_reprocess)
            if not etl_success:
                self.logger.error("❌ Procesamiento ETL falló")
        else:
            self.logger.info("⏭️ Procesamiento ETL omitido por configuración")
            db_summary = self._get_empty_db_summary()
        
        # Generar resumen final
        end_time = time.time()
        total_time = end_time - start_time
        
        overall_success = (gui_success or skip_gui) and (etl_success or skip_etl)
        
        # Emitir evento de proceso completado
        self.callback_manager.emit_event(ProcessingEventType.PROCESS_COMPLETED, {
            'overall_success': overall_success,
            'gui_success': gui_success,
            'etl_success': etl_success,
            'extracted_files': extracted_files,
            'total_time': total_time
        })
        
        # Log final
        self._log_workflow_completion(gui_success, extracted_files, etl_success, total_time, overall_success)
        
        # Generar resumen completo
        complete_summary = self._build_complete_summary(
            gui_success, extracted_files, etl_success, db_summary, total_time
        )
        
        return overall_success, complete_summary

    def validate_environment(self) -> bool:
        """
        Valida que el entorno esté configurado correctamente
        
        Returns:
            bool: True si el entorno es válido
        """
        self.logger.info("🔍 Validando entorno de ejecución...")
        
        try:
            # Validar configuración general
            if not validate_configuration():
                self.logger.error("❌ Configuración general inválida")
                return False
            
            # Validar resolución de pantalla para GUI
            validate_screen_resolution()
            
            # Crear directorios necesarios si no existen
            for directory in self.rutas.values():
                os.makedirs(directory, exist_ok=True)
            
            self.logger.info("✅ Entorno validado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en validación de entorno: {e}")
            return False

    def get_current_progress(self) -> Dict[str, Any]:
        """
        Obtiene el progreso actual del procesamiento
        
        Returns:
            dict: Información del progreso actual
        """
        return self.callback_manager.get_current_progress()

    def get_folder_info(self, folder_path: str) -> Dict[str, Any]:
        """
        Obtiene información de una carpeta de archivos PQM
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            dict: Información de la carpeta
        """
        try:
            if not os.path.exists(folder_path):
                return {"error": "La carpeta no existe", "count": 0, "files": []}
            
            # Extensiones válidas basadas en la configuración
            valid_extensions = ('.pqm702', '.pqm710', '.pqm711')
            
            # Obtener archivos válidos
            files = [f for f in os.listdir(folder_path) 
                    if f.lower().endswith(valid_extensions)]
            
            return {
                "count": len(files),
                "files": files,
                "path": folder_path,
                "valid_extensions": valid_extensions
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de carpeta: {e}")
            return {"error": str(e), "count": 0, "files": []}

    # Métodos auxiliares privados que necesitan ser añadidos o corregidos

    def _validar_resultados_extraccion(self, resultados: Any) -> bool:
        """Valida que los resultados de extracción sean válidos"""
        if resultados is None:
            self.logger.error("❌ El extractor devolvió None - procesamiento fallido")
            return False
        
        if not isinstance(resultados, dict):
            self.logger.error(f"❌ El extractor devolvió tipo inválido: {type(resultados)}")
            return False
        
        # Verificar claves requeridas
        claves_requeridas = ['procesados_exitosos', 'procesados_fallidos', 'saltados', 'csvs_verificados']
        for clave in claves_requeridas:
            if clave not in resultados:
                self.logger.warning(f"⚠️ Clave faltante en resultados: {clave}, usando valor por defecto 0")
                resultados[clave] = 0
        
        if 'detalles' not in resultados:
            resultados['detalles'] = []
        
        return True

    def _procesar_resultados_extraccion(self, resultados: Dict[str, Any]) -> Tuple[bool, int]:
        """Procesa los resultados de extracción y determina el éxito"""
        archivos_exitosos = resultados.get('procesados_exitosos', 0)
        archivos_saltados = resultados.get('saltados', 0)
        archivos_fallidos = resultados.get('procesados_fallidos', 0)
        
        self._mostrar_resumen_extraccion(resultados)
        
        # Lógica de éxito
        if archivos_exitosos > 0:
            self.logger.info(f"✅ Extracción PYWIN exitosa: {archivos_exitosos} archivos procesados")
            return True, archivos_exitosos
        elif archivos_saltados > 0 and archivos_fallidos == 0:
            self.logger.info(f"✅ Extracción PYWIN exitosa: Todos los archivos ya procesados ({archivos_saltados} saltados)")
            return True, 0
        elif archivos_saltados == 0 and archivos_exitosos == 0 and archivos_fallidos == 0:
            self.logger.info("ℹ️ No se encontraron archivos para procesar")
            return True, 0
        else:
            self.logger.warning(f"⚠️ Extracción PYWIN completada con {archivos_fallidos} fallos")
            return False, archivos_exitosos

    def _mostrar_resumen_extraccion(self, resultados: Dict[str, Any]) -> None:
        """Muestra el resumen de extracción"""
        procesados_exitosos = resultados.get('procesados_exitosos', 0)
        procesados_fallidos = resultados.get('procesados_fallidos', 0)
        saltados = resultados.get('saltados', 0)
        csvs_verificados = resultados.get('csvs_verificados', 0)
        
        # Determinar mensaje de estado
        if procesados_exitosos > 0:
            estado_mensaje = "✅ PROCESAMIENTO EXITOSO"
        elif saltados > 0 and procesados_fallidos == 0:
            estado_mensaje = "✅ PROCESAMIENTO COMPLETO - TODOS LOS ARCHIVOS YA PROCESADOS"
        elif procesados_fallidos > 0:
            estado_mensaje = "⚠️ PROCESAMIENTO COMPLETADO CON ERRORES"
        else:
            estado_mensaje = "ℹ️ NO SE ENCONTRARON ARCHIVOS PARA PROCESAR"
        
        self.logger.info(f"\n{'='*50}")
        self.logger.info(estado_mensaje)
        self.logger.info(f"{'='*50}")
        self.logger.info(f"📊 Exitosos:        {procesados_exitosos}")
        self.logger.info(f"📄 CSVs verificados: {csvs_verificados}")
        self.logger.info(f"❌ Fallidos:        {procesados_fallidos}")
        self.logger.info(f"⏭️  Saltados:        {saltados}")
        self.logger.info(f"{'='*50}")

    def _log_summary(self, summary: Dict[str, Any]) -> None:
        """Log del resumen ETL"""
        self.logger.info("📊 Resumen del flujo:")
        for k, v in summary.items():
            self.logger.info(f"   • {k:15}: {v}")

    def _log_workflow_completion(self, gui_success: bool, extracted_files: int, 
                                etl_success: bool, total_time: float, overall_success: bool) -> None:
        """Log de finalización del workflow"""
        self.logger.info("🏁 === RESUMEN DEL FLUJO COMPLETO ===")
        self.logger.info(f"⏱️ Tiempo total de ejecución: {total_time:.2f} segundos")
        
        if gui_success and extracted_files > 0:
            self.logger.info(f"🔄 Extracción PYWIN: ✅ Exitosa - {extracted_files} archivos nuevos procesados")
        elif gui_success and extracted_files == 0:
            self.logger.info("🔄 Extracción PYWIN: ✅ Exitosa - Todos los archivos ya procesados")
        else:
            self.logger.info("🔄 Extracción PYWIN: ❌ Falló")
        
        self.logger.info(f"📊 Archivos extraídos: {extracted_files}")
        self.logger.info(f"💾 Procesamiento ETL: {'✅ Exitoso' if etl_success else '❌ Falló'}")
        self.logger.info(f"🎯 Resultado general: {'✅ ÉXITO' if overall_success else '❌ FALLO'}")

    def _get_error_summary(self, error_message: str) -> Dict[str, Any]:
        """Genera un resumen de error estándar"""
        return {
            'total_files': 0,
            'uploaded_files': 0,
            'failed_uploads': 1,
            'conflicts': 0,
            'inserted_records': 0,
            'success_rate': 0,
            'upload_time': '0:00',
            'updated_indexes': 0,
            'connection_status': 'Error',
            'files': [],
            'error_message': error_message
        }

    def _get_empty_db_summary(self) -> Dict[str, Any]:
        """Genera un resumen vacío para cuando se omite ETL"""
        return {
            'total_files': 0,
            'uploaded_files': 0,
            'failed_uploads': 0,
            'conflicts': 0,
            'inserted_records': 0,
            'success_rate': 0,
            'upload_time': '0:00',
            'updated_indexes': 0,
            'connection_status': 'Omitido',
            'files': []
        }

    def _build_complete_summary(self, gui_success: bool, extracted_files: int, 
                            etl_success: bool, db_summary: Dict[str, Any], 
                            total_time: float) -> Dict[str, Any]:
        """Construye el resumen completo del flujo"""
        # Formatear tiempo
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        time_str = f"{minutes}:{seconds:02d}"
        
        # Determinar estado general
        if gui_success and etl_success:
            overall_status = "✅ Completado"
        elif gui_success or etl_success:
            overall_status = "⚠️ Parcial"
        else:
            overall_status = "❌ Fallido"
        
        return {
            'overall_status': overall_status,
            'total_files': db_summary.get('total_files', 0),
            'csv_extracted': extracted_files,
            'db_uploaded': db_summary.get('uploaded_files', 0),
            'total_errors': db_summary.get('failed_uploads', 0),
            'total_time': time_str,
            'success_rate': db_summary.get('success_rate', 0),
            'data_processed': db_summary.get('inserted_records', 0),
            'connection_status': db_summary.get('connection_status', 'Desconocido'),
            'gui_success': gui_success,
            'etl_success': etl_success,
            'db_summary': db_summary
        }

    def get_processing_progress(self) -> Dict[str, Any]:
        """
        Obtiene el progreso actual detallado del procesamiento
        
        Returns:
            dict: Información detallada del progreso
        """
        return {
            'current_phase': self.callback_manager.current_phase,
            'files_processed': self.callback_manager.files_processed,
            'total_files': self.callback_manager.total_files,
            'percentage': self.callback_manager.get_progress_percentage(),
            'estimated_remaining_time': self.callback_manager.get_estimated_time(),
            'last_event': self.callback_manager.get_last_event()
        }