"""
Controlador principal del sistema Sonel Analysis

Este módulo encapsula toda la lógica de procesamiento que antes estaba en main.py,
permitiendo su uso tanto desde GUI como desde CLI de forma modular.

Autor: Refactorizado para arquitectura modular
Fecha: 2025
"""

import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from core.etl.sonel_etl import SonelETL
from config.logger import get_logger
from core.database.connection import DatabaseConnection
from core.extractors.pywin_extractor import SonelExtractorCompleto
from core.extractors.pygui_extractor import SonelGuiExtractorCompleto
from config.settings import get_full_config, validate_configuration, validate_screen_resolution, get_portable_paths, find_sonel_exe


class SonelController:
    """
    Controlador principal que maneja tanto la extracción PYWIN como el procesamiento ETL
    de forma modular y reutilizable desde cualquier interfaz (GUI o CLI)
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el controlador de forma portable
        
        Args:
            config_file: Ruta al archivo de configuración (opcional)
        """
        # MODIFICACIÓN: Usar ruta portable para config_file
        if config_file is None:
            from config.settings import get_application_directory
            app_dir = get_application_directory()
            config_file = os.path.join(app_dir, "config", "config.ini")
        
        self.config_file = config_file
        self.win_config = get_full_config()
        
        # Configurar logger
        self.logger = get_logger("sonel_controller", f"{__name__}_controller")
        self.logger.setLevel(getattr(logging, self.win_config['LOGGING']['level']))
        
        # Configurar rutas de forma portable
        self.rutas = self._configurar_rutas_portable()
        
        # NUEVO: Verificar y crear directorios necesarios
        self._asegurar_directorios()
        
        self.logger.info("🎯 Controlador Sonel inicializado correctamente")

    def _configurar_rutas_portable(self) -> Dict[str, str]:
        """
        Configura las rutas del sistema de forma portable
        
        Returns:
            dict: Diccionario con las rutas configuradas
        """
        
        # Obtener rutas portables
        portable_paths = get_portable_paths()
        
        # Verificar que el ejecutable de Sonel exista
        sonel_exe = portable_paths['sonel_exe_path']
        if not os.path.exists(sonel_exe):
            # Intentar encontrarlo nuevamente
            found_exe = find_sonel_exe()
            if found_exe:
                sonel_exe = found_exe
                self.logger.info(f"🔍 Ejecutable de Sonel encontrado en: {sonel_exe}")
            else:
                self.logger.warning(f"⚠️ Ejecutable de Sonel no encontrado. Configurado: {sonel_exe}")
        
        return {
            "input_directory": portable_paths['input_dir'],
            "output_directory": portable_paths['output_dir'],
            "sonel_exe_path": sonel_exe
        }
    
    def _asegurar_directorios(self):
        """
        NUEVO MÉTODO: Asegura que todos los directorios necesarios existan
        """
        directorios = [
            self.rutas["input_directory"],
            self.rutas["output_directory"],
            os.path.dirname(self.config_file)
        ]
        
        for directorio in directorios:
            if directorio and not os.path.exists(directorio):
                try:
                    os.makedirs(directorio, exist_ok=True)
                    self.logger.info(f"📁 Directorio creado: {directorio}")
                except Exception as e:
                    self.logger.error(f"❌ Error creando directorio {directorio}: {e}")

    def validate_environment(self) -> bool:
        """
        Valida que el entorno esté configurado correctamente (versión portable)
        
        Returns:
            bool: True si el entorno es válido
        """
        self.logger.info("🔍 Validando entorno de ejecución (modo portable)...")
        
        try:
            # Validar configuración general
            if not validate_configuration():
                self.logger.warning("⚠️ Algunas validaciones de configuración fallaron, continuando...")
            
            # Validar resolución de pantalla para GUI
            validate_screen_resolution()
            
            # MODIFICACIÓN: Asegurar que los directorios existan
            self._asegurar_directorios()
            
            # Validar ejecutable de Sonel (no crítico para el funcionamiento)
            sonel_exe = self.rutas["sonel_exe_path"]
            if not os.path.exists(sonel_exe):
                self.logger.warning(f"⚠️ Ejecutable de Sonel no encontrado: {sonel_exe}")
                self.logger.warning("   El procesamiento CSV se omitirá hasta que se configure correctamente")
                # No retornar False, permitir que continúe
            
            self.logger.info("✅ Entorno validado correctamente (modo portable)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error en validación de entorno: {e}")
            return False

    def run_pywinauto_extraction(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecuta la extracción GUI usando pywinauto
        
        Returns:
            tuple: (success: bool, extraction_summary: dict)
        """
        self.logger.info("🚀 === INICIANDO EXTRACCIÓN PYWIN ===")
        
        try:
            # Verificar requisitos
            if not self.validate_environment():
                self.logger.error("❌ No se pueden cumplir los requisitos del sistema")
                return False, self._get_empty_extraction_summary("Error en validación de entorno")
            
            # Crear instancia del extractor
            self.logger.info("🔧 Inicializando extractor...")
            pywin_extractor = SonelExtractorCompleto(
                input_dir=self.rutas["input_directory"],
                output_dir=self.rutas["output_directory"], 
                ruta_exe=self.rutas["sonel_exe_path"]
            )
            
            # Ejecutar procesamiento completo dinámico
            self.logger.info("🎯 Iniciando procesamiento completo...")
            resultados = pywin_extractor.ejecutar_extraccion_completa_dinamica()
            
            # Validar resultados
            if not self._validar_resultados_extraccion(resultados):
                return False, self._get_empty_extraction_summary("Error en validación de resultados")
            
            # Obtener resumen de extracción del extractor
            extraction_summary = pywin_extractor.get_extraction_summary_for_gui()
            
            # Procesar resultados y determinar éxito
            archivos_exitosos = resultados.get('procesados_exitosos', 0)
            archivos_saltados = resultados.get('saltados', 0)
            archivos_fallidos = resultados.get('procesados_fallidos', 0)
            
            # Determinar éxito basado en la lógica del negocio
            if archivos_exitosos > 0:
                success = True
                extracted_files = archivos_exitosos
            elif archivos_saltados > 0 and archivos_fallidos == 0:
                success = True
                extracted_files = 0  # Ya procesados previamente
            else:
                success = False
                extracted_files = 0
            
            # Agregar información adicional al resumen para la GUI
            extraction_summary.update({
                'success': success,
                'extracted_files': extracted_files,
                'procesados_exitosos': archivos_exitosos,
                'procesados_fallidos': archivos_fallidos,
                'saltados': archivos_saltados
            })
            
            self.logger.info(f"✅ Extracción completada - Éxito: {success}, Archivos: {extracted_files}")
            
            return success, extraction_summary
            
        except Exception as e:
            self.logger.error(f"❌ Error durante extracción PYWIN: {e}")
            self.logger.error(traceback.format_exc())
            return False, self._get_empty_extraction_summary(f"Error crítico: {str(e)}")
        
    def run_pyguiauto_extraction(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecuta recuperación de archivos con errores usando el extractor GUI.
        Maneja archivos desde múltiples directorios correctamente.
        
        Returns:
            tuple: (success: bool, extraction_summary: dict)
        """
        self.logger.info("🔧 === INICIANDO RECUPERACIÓN CON COORDENADAS GUI === ")

        try:
            # Verificar requisitos
            if not self.validate_environment():
                self.logger.error("❌ No se pueden cumplir los requisitos del sistema")
                return False, self._get_empty_extraction_summary("Error en validación de entorno")
            
            # MODIFICACIÓN: Crear instancia del extractor GUI con paths configurados correctamente
            self.logger.info("🔧 Inicializando extractor GUI...")
            pygui_extractor = SonelGuiExtractorCompleto(
                input_dir=self.rutas["input_directory"],
                output_dir=self.rutas["output_directory"], 
                ruta_exe=self.rutas["sonel_exe_path"]
            )
            
            # VERIFICACIÓN: Comprobar que el archivo de registro existe y es accesible
            registro_path = pygui_extractor.file_tracker.processed_files_json
            self.logger.info(f"📄 Verificando archivo de registro: {registro_path}")
            
            if not os.path.exists(registro_path):
                self.logger.warning(f"⚠️ Archivo de registro no existe: {registro_path}")
                return False, self._get_empty_extraction_summary("Archivo de registro no encontrado")
            
            try:
                # Intentar leer el archivo para verificar que es válido
                with open(registro_path, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                    files_count = len(test_data.get('files', {}))
                    self.logger.info(f"✅ Archivo de registro válido con {files_count} archivos registrados")
            except Exception as e:
                self.logger.error(f"❌ Error leyendo archivo de registro: {e}")
                return False, self._get_empty_extraction_summary("Archivo de registro corrupto o inaccesible")
            
            # Ejecutar recuperación de archivos con errores
            resultados_recuperacion = pygui_extractor.ejecutar_extraccion_archivos_con_errores()
            
            # Validar resultados
            if not self._validar_resultados_extraccion(resultados_recuperacion):
                return False, self._get_empty_extraction_summary("Error en validación de resultados")
            
            # Obtener resumen de extracción para GUI
            extraction_summary = pygui_extractor.get_extraction_summary_for_gui()
            
            # Procesar resultados y determinar éxito
            archivos_exitosos = resultados_recuperacion.get('procesados_exitosos', 0)
            archivos_saltados = resultados_recuperacion.get('saltados', 0)
            archivos_fallidos = resultados_recuperacion.get('procesados_fallidos', 0)

            if archivos_exitosos > 0:
                success = True
                extracted_files = archivos_exitosos
                self.logger.info(f"✅ Recuperación exitosa: {archivos_exitosos} archivos reprocesados")
            elif archivos_saltados > 0 and archivos_fallidos == 0:
                success = True
                extracted_files = 0  # Ya procesados previamente
                self.logger.info("ℹ️ No había archivos con errores que reprocesar")
            else:
                success = False
                extracted_files = 0
                self.logger.warning(f"⚠️ Recuperación completada con fallos: {archivos_fallidos}")

            # Agregar datos adicionales al resumen
            extraction_summary.update({
                'success': success,
                'extracted_files': extracted_files,
                'procesados_exitosos': archivos_exitosos,
                'procesados_fallidos': archivos_fallidos,
                'saltados': archivos_saltados,
                'modo_operacion': 'recuperacion_errores'
            })
            
            return success, extraction_summary
            
        except Exception as e:
            self.logger.error(f"❌ Error durante recuperación GUI: {e}")
            self.logger.error(traceback.format_exc())
            return False, self._get_empty_extraction_summary(f"Error crítico: {str(e)}")
        
    def _get_empty_extraction_summary(self, error_message: str = "") -> Dict[str, Any]:
        """Genera un resumen de extracción vacío para casos de error"""
        return {
            'processed_files': 0,
            'total_files': 0,
            'warnings': 0,
            'errors': 1 if error_message else 0,
            'csv_files_generated': 0,
            'execution_time': '0:00',
            'total_size': '0 MB',
            'files_detail': [],
            'success': False,
            'extracted_files': 0,
            'procesados_exitosos': 0,
            'procesados_fallidos': 1 if error_message else 0,
            'saltados': 0,
            'error_message': error_message
        }

    def run_etl_processing(self, force_reprocess: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecuta el procesamiento ETL de los archivos CSV
        
        Args:
            force_reprocess: Si True, reprocesa todos los archivos ignorando el registro
            
        Returns:
            tuple: (success: bool, summary_data: dict) - Estado y resumen detallado
        """
        self.logger.info("🚀 === INICIANDO PROCESAMIENTO ETL ===")
        
        db_connection = None
        etl = None
        
        try:
            # Inicializar conexión a base de datos
            from config.settings import load_config
            etl_config = load_config(self.config_file)
            
            db_connection = DatabaseConnection(etl_config)
            if not db_connection.connect():
                self.logger.error("❌ No se pudo establecer conexión con la base de datos")
                return False, self._get_error_summary("Error de conexión BD")
            
            self.logger.info("✅ Conexión a base de datos establecida")
            
            # Inicializar ETL
            etl = SonelETL(
                config_file=self.config_file,
                db_connection=db_connection
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
            return False, self._get_error_summary(f"Error ETL: {str(e)}")
            
        finally:
            # Limpieza de recursos
            if etl:
                etl.close()
            if db_connection:
                db_connection.close()
            self.logger.info("🧹 Recursos liberados correctamente")

    def run_complete_workflow(self, force_reprocess: bool = False, 
                             skip_gui: bool = False, skip_etl: bool = False) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecuta el flujo completo: extracción GUI + procesamiento ETL
        
        Args:
            force_reprocess: Fuerza el reprocesamiento en ETL
            skip_gui: Omite la extracción GUI
            skip_etl: Omite el procesamiento ETL
            
        Returns:
            tuple: (success: bool, complete_summary: dict) - Estado y resumen completo
        """
        self.logger.info("🎯 === INICIANDO FLUJO COMPLETO SONEL ===")
        start_time = time.time()
        
        # Validar entorno
        if not self.validate_environment():
            self.logger.error("❌ Validación de entorno fallida")
            return False, self._get_error_summary("Validación de entorno fallida")
        
        gui_success = True
        extraction_summary = {}
    
        # Paso 1: Extracción GUI (opcional)
        if not skip_gui:
            gui_success, extraction_summary = self.run_pywinauto_extraction()
            if not gui_success:
                self.logger.warning("⚠️ Extracción PYWIN falló, continuando con ETL...")
        else:
            self.logger.info("⏭️ Extracción PYWIN omitida por configuración")
            extraction_summary = self._get_empty_extraction_summary()
        
        # Log del resumen de extracción
        self._log_extraction_summary(extraction_summary)

        # Paso 2: Procesamiento ETL (opcional)
        etl_success = True
        db_summary = {}
        
        if not skip_etl:
            etl_success, db_summary = self.run_etl_processing(force_reprocess)
            if not etl_success:
                self.logger.error("❌ Procesamiento ETL falló")
        else:
            self.logger.info("⏭️ Procesamiento ETL omitido por configuración")
            db_summary = self._get_empty_db_summary()
        
        # Generar resumen final
        end_time = time.time()
        total_time = end_time - start_time
        
        overall_success = (gui_success or skip_gui) and (etl_success or skip_etl)
        
        # Log final
        self._log_workflow_completion(gui_success, extraction_summary.get('extracted_files', 0), 
                                 etl_success, total_time, overall_success)
    
        # Generar resumen completo
        complete_summary = self._build_complete_summary_with_extraction(
            gui_success, extraction_summary, etl_success, db_summary, total_time
        )
        
        return overall_success, complete_summary

    def _build_complete_summary_with_extraction(self, gui_success: bool, extraction_summary: Dict[str, Any], 
                                           etl_success: bool, db_summary: Dict[str, Any], 
                                           total_time: float) -> Dict[str, Any]:
        """Construye el resumen completo del flujo incluyendo detalles de extracción"""
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
            # Información general
            'overall_status': overall_status,
            'total_files': extraction_summary.get('total_files', 0),
            'total_time': time_str,
            'success_rate': db_summary.get('success_rate', 0),
            'connection_status': db_summary.get('connection_status', 'Desconocido'),
            'gui_success': gui_success,
            'etl_success': etl_success,
            
            # Información de extracción CSV
            'csv_extracted': extraction_summary.get('csv_files_generated', 0),
            'csv_processed_files': extraction_summary.get('processed_files', 0),
            'csv_warnings': extraction_summary.get('warnings', 0),
            'csv_errors': extraction_summary.get('errors', 0),
            'csv_execution_time': extraction_summary.get('execution_time', '0:00'),
            'csv_total_size': extraction_summary.get('total_size', '0 MB'),
            
            # Información de base de datos
            'db_uploaded': db_summary.get('uploaded_files', 0),
            'total_errors': db_summary.get('failed_uploads', 0),
            'data_processed': db_summary.get('inserted_records', 0),
            'data_size': db_summary.get('data_size', '0 bytes'),
            
            # Resúmenes detallados
            'extraction_summary': extraction_summary,
            'db_summary': db_summary,
            'files': db_summary.get('files', [])
        }

    def _log_extraction_summary(self, extraction_summary: Dict[str, Any]) -> None:
        """Log del resumen de extracción desde el controlador"""
        self.logger.info("\n" + "🎯" * 30)
        self.logger.info("📊 RESUMEN DE EXTRACCIÓN CSV DESDE CONTROLADOR")
        self.logger.info("🎯" * 30)
        self.logger.info(f"📁 Archivos procesados: {extraction_summary.get('processed_files', 0)} / {extraction_summary.get('total_files', 0)}")
        self.logger.info(f"⚠️ Advertencias: {extraction_summary.get('warnings', 0)}")
        self.logger.info(f"❌ Errores: {extraction_summary.get('errors', 0)}")
        self.logger.info(f"📄 CSVs generados: {extraction_summary.get('csv_files_generated', 0)}")
        self.logger.info(f"⏱️ Tiempo de extracción: {extraction_summary.get('execution_time', '0:00')}")
        self.logger.info(f"💾 Tamaño procesado: {extraction_summary.get('total_size', '0 MB')}")
        
        # Tasa de éxito
        total_files = extraction_summary.get('total_files', 0)
        csv_generated = extraction_summary.get('csv_files_generated', 0)
        if total_files > 0:
            success_rate = (csv_generated / total_files) * 100
            self.logger.info(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        self.logger.info("🎯" * 30)

    def get_folder_info(self, folder_path: str) -> Dict[str, Any]:
        """
        Obtiene información de una carpeta de archivos PQM (versión mejorada)
        
        Args:
            folder_path: Ruta de la carpeta
            
        Returns:
            dict: Información de la carpeta
        """
        try:
            if not folder_path or not os.path.exists(folder_path):
                return {"error": "La carpeta no existe o es inválida", "count": 0, "files": []}
            
            if not os.path.isdir(folder_path):
                return {"error": "La ruta no es una carpeta válida", "count": 0, "files": []}
            
            # Extensiones válidas
            valid_extensions = ('.pqm702', '.pqm710', '.pqm711')
            
            # Obtener archivos válidos de forma segura
            files = []
            try:
                for filename in os.listdir(folder_path):
                    if filename.lower().endswith(valid_extensions):
                        full_path = os.path.join(folder_path, filename)
                        if os.path.isfile(full_path):
                            files.append(filename)
            except PermissionError:
                return {"error": "Sin permisos para leer la carpeta", "count": 0, "files": []}
            except Exception as e:
                return {"error": f"Error leyendo carpeta: {str(e)}", "count": 0, "files": []}
            
            return {
                "count": len(files),
                "files": sorted(files),  # Ordenar alfabéticamente
                "path": folder_path,
                "valid_extensions": valid_extensions
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de carpeta: {e}")
            return {"error": f"Error inesperado: {str(e)}", "count": 0, "files": []}

    # Métodos auxiliares privados
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
    
    def export_mediciones_to_csv(self, file_path: str = None) -> Tuple[bool, str]:
        """
        Exporta todos los registros de mediciones_planas a CSV con formato empresarial EEASA
        
        Args:
            file_path: Ruta donde guardar el archivo CSV (opcional)
            
        Returns:
            tuple: (success: bool, message: str) - Estado y mensaje de resultado
        """
        self.logger.info("📊 Iniciando exportación de mediciones_planas a CSV")
        
        db_connection = None
        
        try:
            # Inicializar conexión a base de datos
            from config.settings import load_config
            etl_config = load_config(self.config_file)
            
            db_connection = DatabaseConnection(etl_config)
            if not db_connection.connect():
                self.logger.error("No se pudo establecer conexión con la base de datos")
                return False, "Error de conexión a la base de datos"
            
            # Generar nombre de archivo si no se proporciona
            if file_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_dir = self.rutas.get("output_directory", ".")
                file_path = os.path.join(output_dir, f"mediciones_planas_EEASA_{timestamp}.csv")
            
            # Extraer datos de la base de datos
            success, message = self._extract_and_save_eeasa_csv(db_connection, file_path)
            
            if success:
                self.logger.info(f"Exportación exitosa a: {file_path}")
            else:
                self.logger.error(f"Error en exportación: {message}")
            
            return success, message if success else f"Error: {message}"
            
        except Exception as e:
            self.logger.error(f"Error durante exportación CSV: {e}")
            return False, f"Error crítico durante exportación: {str(e)}"
            
        finally:
            if db_connection:
                db_connection.close()

    def _extract_and_save_eeasa_csv(self, db_connection: DatabaseConnection, file_path: str) -> Tuple[bool, str]:
        """
        Extrae datos de mediciones_planas y los guarda en formato CSV empresarial EEASA
        
        Args:
            db_connection: Conexión a la base de datos
            file_path: Ruta donde guardar el archivo CSV
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Query corregida para extraer datos ordenados por ID
            query = """
                SELECT 
                    mp.id,
                    c.codigo,
                    mp.fecha,
                    mp.time,
                    mp.utc_zone,
                    mp.u_l1_avg,
                    mp.u_l2_avg,
                    mp.u_l3_avg,
                    mp.u_l12_avg,
                    mp.i_l1_avg,
                    mp.i_l2_avg,
                    mp.p_l1_avg,
                    mp.p_l2_avg,
                    mp.p_l3_avg,
                    mp.p_e_avg,
                    mp.q1_l1_avg,
                    mp.q1_l2_avg,
                    mp.q1_e_avg,
                    mp.sn_l1_avg,
                    mp.sn_l2_avg,
                    mp.sn_e_avg,
                    mp.s_l1_avg,
                    mp.s_l2_avg,
                    mp.s_e_avg,
                    mp.fecha_subida
                FROM mediciones_planas mp
                LEFT JOIN codigo c ON mp.codigo_id = c.id
                ORDER BY mp.id ASC;
            """
            
            cursor = db_connection.execute_query(query, commit=False)
            
            if not cursor:
                return False, "No se pudo ejecutar la consulta de exportación"
            
            # Obtener datos
            rows = cursor.fetchall()
            cursor.close()
            
            if not rows:
                return True, "Exportación completada - No hay registros para exportar"
            
            # Escribir CSV con formato empresarial EEASA
            self._write_eeasa_format_csv(file_path, rows)
            
            return True, f"Exportación exitosa: {len(rows)} registros exportados"
            
        except Exception as e:
            self.logger.error(f"Error durante la exportación CSV: {e}")
            return False, f"Error técnico: {str(e)}"

    def _write_eeasa_format_csv(self, file_path: str, rows: list) -> None:
        """
        Escribe el archivo CSV siguiendo el formato empresarial de EEASA
        
        Args:
            file_path: Ruta del archivo CSV
            rows: Datos a escribir
        """
        import csv
        from datetime import datetime
        
        # CORRECCIÓN: Usar UTF-8 con BOM para compatibilidad completa
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            
            # ENCABEZADO CORPORATIVO EEASA
            writer.writerow(['EMPRESA ELÉCTRICA AMBATO REGIONAL CENTRO NORTE S.A.'])
            writer.writerow(['Reporte de Mediciones Eléctricas - Sistema de Monitoreo SONEL'])
            writer.writerow([])  # Línea en blanco
            
            # METADATOS DEL REPORTE
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([f'Fecha de Generación: {timestamp}'])
            writer.writerow([f'Total de Registros: {len(rows)}'])
            writer.writerow([f'Sistema: SONEL Extractor v2.0'])
            writer.writerow([])  # Línea en blanco
            
            # ENCABEZADOS CORREGIDOS
            headers = [
                'ID Registro',
                'Código Cliente', 
                'Fecha y Hora Completa',
                'Hora Local',
                'Zona UTC',
                'Voltaje L1 Promedio (V)',
                'Voltaje L2 Promedio (V)',
                'Voltaje L3 Promedio (V)',
                'Voltaje L12 Promedio (V)',
                'Corriente L1 Promedio (A)',
                'Corriente L2 Promedio (A)',
                'Potencia L1 Promedio (W)',
                'Potencia L2 Promedio (W)',
                'Potencia L3 Promedio (W)',
                'Potencia Total Promedio (W)',
                'Reactiva Q1 L1 Promedio (VAR)',
                'Reactiva Q1 L2 Promedio (VAR)',
                'Reactiva Q1 Total Promedio (VAR)',
                'Potencia Aparente L1 Promedio (VA)',
                'Potencia Aparente L2 Promedio (VA)',
                'Potencia Aparente Total Promedio (VA)',
                'Factor Potencia L1 Promedio',
                'Factor Potencia L2 Promedio',
                'Factor Potencia Total Promedio',
                'Fecha de Carga en Sistema'
            ]
            writer.writerow(headers)
            
            # DATOS CON MAPEO CORREGIDO
            for row in rows:
                # Mapeo correcto de las columnas:
                # row[0] = id, row[1] = codigo, row[2] = fecha (timestamp completo)
                # row[3] = time (hora local), row[4] = utc_zone
                formatted_row = []
                
                for i, value in enumerate(row):
                    if value is None:
                        formatted_row.append('')
                    elif i == 2:  # Columna 'fecha' - timestamp completo
                        # Mantener el timestamp completo como está
                        formatted_row.append(str(value))
                    elif i == 3:  # Columna 'time' - hora local
                        # Mantener la hora local como está
                        formatted_row.append(str(value))
                    elif i == 4:  # Columna 'utc_zone'
                        # Formatear zona UTC de manera más clara
                        if value:
                            formatted_row.append(f"UTC{value}")
                        else:
                            formatted_row.append('')
                    elif i in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]:  # Columnas numéricas
                        # Formatear números con 3 decimales para mayor precisión
                        try:
                            if value is not None and value != '':
                                formatted_row.append(f"{float(value):.3f}")
                            else:
                                formatted_row.append('')
                        except (ValueError, TypeError):
                            formatted_row.append(str(value))
                    else:
                        formatted_row.append(str(value))
                
                writer.writerow(formatted_row)
            
            # PIE DEL REPORTE
            writer.writerow([])
            writer.writerow([f'Fin del reporte - EEASA {datetime.now().year}'])
            writer.writerow(['Generado automáticamente por Sistema SONEL'])