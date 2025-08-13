import os
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime
from config.logger import get_logger
from core.utils.csv_summary import CSVSummaryUtils
from config.settings import get_full_config, create_directories, load_config
from core.extractors.pywin_extractor import SonelExtractorCompleto
from core.utils.coordinates_utils import CoordinatesUtils

# Imports de los módulos modularizados (reutilizando)
from .pywin_modules.file_manager import FileManager
from .pywin_modules.file_tracker import FileTracker
from .pywin_modules.process_manager import ProcessManager
from .pywin_modules.csv_generator import CSVGenerator

# Imports de los nuevos módulos para coordenadas
from .pyguiauto_extractor.gui_analysis import GuiAnalisisInicial
from .pyguiauto_extractor.gui_configuration import GuiConfiguracion

class SonelGuiExtractorCompleto:
    """Coordinador principal que maneja extracción basada en coordenadas para archivos con errores"""
    
    def __init__(self, input_dir=None, output_dir=None, ruta_exe=None, coordinates_file=None):
        # Configuración de rutas (reutilizando lógica existente)
        config = get_full_config()
        config_file = 'config.ini'
        self.config = load_config(config_file)

        # Configuración de paths por defecto
        self.PATHS = {
            'input_dir': input_dir or config['PATHS']['input_dir'],
            'output_dir': output_dir or config['PATHS']['output_dir'],
            'export_dir': output_dir or config['PATHS']['output_dir'],
            'sonel_exe_path': ruta_exe or config['PATHS']['sonel_exe_path'],
            'temp_dir': config['PATHS']['temp_dir'],
            'process_file_dir': Path(input_dir or config['PATHS']['input_dir']).resolve(),
            'coordinates_file': coordinates_file or os.path.join(config['PATHS']['output_dir'], 'component_positions.json')
        }
        
        # Configuración de delays para verificación (reutilizando)
        self.delays = {
            'file_verification': config['GUI']['delays']['file_verification'],
            'ui_response': config['GUI']['delays']['ui_response'],
            'between_files': config['GUI']['delays']['between_files']
        }
        
        # Crear directorios usando función centralizada
        create_directories()
        os.makedirs(self.PATHS['output_dir'], exist_ok=True)
        os.makedirs(self.PATHS['process_file_dir'], exist_ok=True)
        os.makedirs(self.PATHS['temp_dir'], exist_ok=True)
    
        # Logger específico para GUI extractor
        self.gui_logger = get_logger("pygui", f"{__name__}_pygui")
        self.gui_logger.setLevel(getattr(logging, config['LOGGING']['level']))
        
        self.gui_logger.info("="*80)
        self.gui_logger.info("🎯 EXTRACTOR GUI SONEL ANALYSIS - INICIO (Coordenadas)")
        self.gui_logger.info(f"📁 Directorio entrada: {self.PATHS['input_dir']}")
        self.gui_logger.info(f"📁 Directorio salida: {self.PATHS['output_dir']}")
        self.gui_logger.info(f"📍 Archivo coordenadas: {self.PATHS['coordinates_file']}")
        self.gui_logger.info("="*80)

        self.process_start_time = None
        self.total_files_attempted = 0
        self.total_size_bytes = 0

        # Cargar coordenadas
        self.coordinates = self._load_coordinates()
        
        # Inicializar módulos (reutilizando existentes)
        self._init_modules()

    def _load_coordinates(self):
        """Carga las coordenadas desde el archivo JSON"""
        coordinates = CoordinatesUtils.load_coordinates(self.PATHS['coordinates_file'])
        
        if not coordinates:
            self.gui_logger.error("❌ No se pudieron cargar las coordenadas. Extractor GUI no funcionará.")
            return {}
        
        # Validar estructura de coordenadas
        is_valid, errors = CoordinatesUtils.validate_coordinates_structure(coordinates)
        if not is_valid:
            self.gui_logger.error(f"❌ Coordenadas inválidas: {errors}")
            return {}
        
        summary = CoordinatesUtils.get_coordinates_summary(coordinates)
        self.gui_logger.info(f"✅ Coordenadas cargadas: {summary['total_elements']} elementos")
        self.gui_logger.info(f"   - Con texto: {summary['elements_with_text']}")
        self.gui_logger.info(f"   - Con rectángulo: {summary['elements_with_rect']}")
        self.gui_logger.info(f"   - Tipos: {summary['element_types']}")
        
        return coordinates

    def _init_modules(self):
        """Inicializa los módulos modularizados (reutilizando existentes)"""
        self.file_manager = FileManager(self.PATHS, self.gui_logger)
        self.file_tracker = FileTracker(self.PATHS, self.gui_logger)
        self.process_manager = ProcessManager(self.gui_logger)
        self.csv_generator = CSVGenerator(self.PATHS, self.delays, self.gui_logger)

    # Métodos reutilizados del extractor original
    def get_pqm_files(self):
        """Obtiene lista de archivos .pqm702 en el directorio de entrada"""
        return self.file_manager.get_pqm_files()

    def obtener_estadisticas_procesados(self):
        """Obtiene estadísticas de archivos procesados"""
        return self.file_tracker.get_processing_statistics()

    def ya_ha_sido_procesado(self, file_path):
        """Verifica si un archivo ya ha sido procesado anteriormente"""
        return self.file_tracker.is_already_processed(file_path)

    def registrar_archivo_procesado(self, file_path, resultado_exitoso=True, csv_path=None, 
                                  processing_time=None, error_message=None, additional_info=None):
        """Registra un archivo como procesado"""
        return self.file_tracker.register_processed_file(
            file_path, resultado_exitoso, csv_path, processing_time, error_message, additional_info
        )

    def close_sonel_analysis_force(self):
        """Cierra todos los procesos relacionados con Sonel Analysis"""
        return self.process_manager.close_sonel_analysis_force()

    def get_archivos_con_errores(self):
        """
        Obtiene lista de archivos que han sido procesados con errores o advertencias
        
        Returns:
            list: Lista de rutas de archivos con errores
        """
        try:
            archivos_pqm = self.get_pqm_files()
            processed_data = self.file_tracker._load_processed_files_data()
            archivos_con_errores = []
            
            for archivo_pqm in archivos_pqm:
                file_path_normalized = os.path.abspath(archivo_pqm)
                
                if file_path_normalized in processed_data:
                    processed_info = processed_data[file_path_normalized]
                    status = processed_info.get('status', '')
                    csv_output = processed_info.get('csv_output', {})
                    csv_verified = csv_output.get('verified', False)
                    
                    # Archivo tiene error si:
                    # 1. Status no es exitoso
                    # 2. Status es exitoso pero CSV no verificado
                    if status != "exitoso" or (status == "exitoso" and not csv_verified):
                        archivos_con_errores.append(archivo_pqm)
            
            self.gui_logger.info(f"📋 Archivos con errores encontrados: {len(archivos_con_errores)}")
            for archivo in archivos_con_errores:
                self.gui_logger.info(f"   ⚠️ {os.path.basename(archivo)}")
            
            return archivos_con_errores
            
        except Exception as e:
            self.gui_logger.error(f"❌ Error obteniendo archivos con errores: {e}")
            return []

    def ejecutar_extraccion_archivo_gui(self, archivo_pqm):
        """
        Ejecuta el flujo completo para un archivo específico usando coordenadas GUI
        Reutiliza la lógica centralizada de pywin_extractor pero con implementación GUI
        
        Args:
            archivo_pqm: Ruta del archivo .pqm702 a procesar
            
        Returns:
            bool: True si fue exitoso, False si falló
        """
        nombre_archivo = os.path.basename(archivo_pqm)
        csv_path_generado = None
        proceso_exitoso = False
        error_message = None
        start_time = datetime.now()

        if not self.coordinates:
            self.gui_logger.error("❌ No hay coordenadas disponibles")
            error_message = "No hay coordenadas disponibles"
            self.registrar_archivo_procesado(
                file_path=archivo_pqm,
                resultado_exitoso=False,
                csv_path=None,
                processing_time=0,
                error_message=error_message,
                additional_info={
                    "extraccion": "completa",
                    "herramienta": "gui",
                    "tipo_archivo": "sonel_pqm"
                }
            )
            return False

        try:
            self.gui_logger.info(f"\n🎯 Procesando con GUI: {nombre_archivo}")

            extractor_principal = SonelExtractorCompleto(
                input_dir=self.PATHS['input_dir'],
                output_dir=self.PATHS['output_dir'],
                ruta_exe=self.PATHS['sonel_exe_path']
            )

            def ejecutar_con_gui(archivo_pqm_inner):
                nonlocal csv_path_generado, proceso_exitoso, error_message
                fallos_suaves = 0
                MAX_FALLOS = 2

                try:
                    # --- FASE 1: Vista inicial ---
                    self.gui_logger.info("--- FASE 1: VISTA INICIAL (GUI) ---")
                    extractor_inicial = GuiAnalisisInicial(
                        archivo_pqm_inner,
                        self.PATHS['sonel_exe_path'],
                        self.coordinates
                    )

                    if not extractor_inicial.conectar():
                        error_message = "Error conectando vista inicial GUI"
                        return False
                    if not extractor_inicial.navegar_configuracion():
                        error_message = "Error navegando configuración GUI"
                        return False
                    if not extractor_inicial.ejecutar_analisis():
                        error_message = "Error ejecutando análisis GUI"
                        return False

                    # --- FASE 2: Configuración ---
                    self.gui_logger.info("--- FASE 2: VISTA CONFIGURACIÓN (GUI) ---")
                    extractor_config = GuiConfiguracion(self.coordinates)
                    app_ref = extractor_inicial.get_app_reference()

                    if not extractor_config.conectar(app_ref):
                        error_message = "Error conectando vista configuración GUI"
                        return False

                    extraction_methods = [
                        ("extraer_configuracion_principal_mediciones_gui", extractor_config.extraer_configuracion_principal_mediciones_gui, 1),
                        ("configurar_radiobutton_gui", extractor_config.configurar_radiobutton_gui, 1),
                        ("configurar_checkboxes_gui", extractor_config.configurar_checkboxes_gui, 1),
                        ("extraer_tabla_mediciones_gui", extractor_config.extraer_tabla_mediciones_gui, 1),
                        ("extraer_informes_graficos_gui", extractor_config.extraer_informes_graficos_gui, 1),
                    ]

                    for method_name, method, delay in extraction_methods:
                        time.sleep(delay)
                        if not method():
                            fallos_suaves += 1
                            self.gui_logger.warning(f"⚠️ Falló {method_name}, continuando")
                            if fallos_suaves > MAX_FALLOS:
                                error_message = f"Se superó el límite de fallos permitidos ({fallos_suaves})."
                                return False

                    # --- FASE 3: Guardar CSV ---
                    self.gui_logger.info("--- FASE 3: GUARDADO Y VERIFICACIÓN CSV (GUI) ---")
                    try:
                        csv_path_generado, proceso_exitoso = extractor_principal.csv_generator.generate_and_verify_csv(
                            archivo_pqm_inner, extractor_config
                        )
                        if not proceso_exitoso:
                            error_message = "No se pudo verificar la creación del archivo CSV"
                    except Exception as e:
                        error_message = f"Error crítico en fase de guardado: {e}"
                        proceso_exitoso = False

                    return proceso_exitoso

                except Exception as e:
                    error_message = f"Error en procesamiento GUI: {e}"
                    self.gui_logger.error(traceback.format_exc())
                    proceso_exitoso = False
                    return False

            extractor_principal.ejecutar_extraccion_archivo = ejecutar_con_gui
            proceso_exitoso = extractor_principal.ejecutar_extraccion_archivo(archivo_pqm)

        except Exception as e:
            error_message = f"Error crítico en procesamiento GUI: {e}"
            self.gui_logger.error(traceback.format_exc())
            proceso_exitoso = False

        finally:
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            self.registrar_archivo_procesado(
                file_path=archivo_pqm,
                resultado_exitoso=proceso_exitoso,
                csv_path=csv_path_generado,
                processing_time=processing_time,
                error_message=error_message,
                additional_info={
                    "extraccion": "completa",
                    "herramienta": "gui",
                    "tipo_archivo": "sonel_pqm"
                }
            )

        return proceso_exitoso

    def ejecutar_extraccion_archivos_con_errores(self):
        """
        Ejecuta el flujo de extracción GUI solo para archivos que tienen errores previos
        Reutiliza completamente la lógica de procesamiento del extractor principal
        
        Returns:
            dict: Resultados del procesamiento
        """
        self.process_start_time = datetime.now()
        
        try:
            # Verificar si hay coordenadas disponibles
            if not self.coordinates:
                self.gui_logger.error("❌ No hay coordenadas disponibles para extracción GUI")
                return {"procesados_exitosos": 0, "procesados_fallidos": 0, "saltados": 0, 
                    "csvs_verificados": 0, "detalles": [], "modo": "recuperacion_errores_gui"}
            
            # Obtener archivos con errores
            archivos_con_errores = self.get_archivos_con_errores()
            
            if not archivos_con_errores:
                self.gui_logger.info("✅ No hay archivos con errores que requieran reprocesamiento GUI")
                return {"procesados_exitosos": 0, "procesados_fallidos": 0, "saltados": 0,
                    "csvs_verificados": 0, "detalles": [], "modo": "recuperacion_errores_gui"}
            
            self.total_files_attempted = len(archivos_con_errores)
            self.total_size_bytes = self._calculate_total_size(archivos_con_errores)
            
            self.gui_logger.info(f"🔄 Archivos con errores a reprocesar: {len(archivos_con_errores)}")

            extractor_principal = SonelExtractorCompleto(
                input_dir=self.PATHS['input_dir'],
                output_dir=self.PATHS['output_dir'], 
                ruta_exe=self.PATHS['sonel_exe_path']
            )
            
            # CONFIGURAR LISTA DE ARCHIVOS PENDIENTES (solo los que tienen errores)
            archivos_pendientes = archivos_con_errores
            
            # SIMULAR ESTRUCTURA DE ARCHIVOS YA PROCESADOS PARA FORZAR REPROCESAMIENTO
            # Temporalmente marcar como no procesados para que se ejecuten
            original_is_processed = extractor_principal.ya_ha_sido_procesado
            def force_reprocess(file_path):
                return False  # Forzar que todos los archivos con errores se reprocesen
            extractor_principal.ya_ha_sido_procesado = force_reprocess
            
            # INYECTAR MÉTODO GUI EN EL EXTRACTOR PRINCIPAL
            def ejecutar_con_gui_wrapper(archivo_pqm):
                return self.ejecutar_extraccion_archivo_gui(archivo_pqm)
            
            # Guardar método original y reemplazar temporalmente
            metodo_original = extractor_principal.ejecutar_extraccion_archivo
            extractor_principal.ejecutar_extraccion_archivo = ejecutar_con_gui_wrapper
            
            # EJECUTAR CON LÓGICA CENTRALIZADA DEL EXTRACTOR PRINCIPAL
            # Configurar archivos pendientes manualmente
            resultados_globales = {
                "procesados_exitosos": 0,
                "procesados_fallidos": 0, 
                "saltados": 0,
                "csvs_verificados": 0,
                "detalles": [],
                "modo": "recuperacion_errores_gui"
            }
            
            # Procesar cada archivo usando la lógica del extractor principal
            for i, archivo in enumerate(archivos_pendientes, 1):
                nombre_archivo = os.path.basename(archivo)
                self.gui_logger.info(f"\n{'='*60}")
                self.gui_logger.info(f"🔧 Reprocesando archivo {i}/{len(archivos_pendientes)}: {nombre_archivo}")
                self.gui_logger.info(f"{'='*60}")
                
                try:
                    # EJECUTAR CON LÓGICA CENTRALIZADA (incluye registro automático)
                    resultado = extractor_principal.ejecutar_extraccion_archivo(archivo)
                    
                    if resultado is True:
                        resultados_globales["procesados_exitosos"] += 1
                        resultados_globales["csvs_verificados"] += 1
                        resultados_globales["detalles"].append({
                            "archivo": nombre_archivo,
                            "estado": "recuperado_exitoso",
                            "csv_verificado": True
                        })
                        
                        # CIERRE SUAVE
                        try:
                            time.sleep(2)
                            self.close_sonel_analysis_force()
                        except Exception as e:
                            self.gui_logger.warning(f"⚠️ Error en limpieza post-éxito: {e}")
                    else:
                        resultados_globales["procesados_fallidos"] += 1
                        resultados_globales["detalles"].append({
                            "archivo": nombre_archivo,
                            "estado": "fallo_recuperacion",
                            "csv_verificado": False
                        })
                        
                        # CIERRE FORZOSO
                        try:
                            self.close_sonel_analysis_force()
                        except Exception as e:
                            self.gui_logger.warning(f"⚠️ Error en cierre forzoso: {e}")
                            
                except Exception as e:
                    self.gui_logger.error(f"❌ Error reprocesando archivo {nombre_archivo}: {e}")
                    resultados_globales["procesados_fallidos"] += 1
                    resultados_globales["detalles"].append({
                        "archivo": nombre_archivo,
                        "estado": "error_excepcion_gui",
                        "csv_verificado": False,
                        "error": str(e)
                    })
                    
                    try:
                        self.close_sonel_analysis_force()
                    except Exception as cleanup_error:
                        self.gui_logger.warning(f"⚠️ Error en limpieza tras excepción: {cleanup_error}")

                # Pausa entre archivos
                if i < len(archivos_pendientes):
                    self.gui_logger.info("⏳ Pausa entre archivos")
                    time.sleep(4)
            
            # Restaurar método original
            extractor_principal.ejecutar_extraccion_archivo = metodo_original
            extractor_principal.ya_ha_sido_procesado = original_is_processed
            
            # Resumen final
            self._log_final_summary_gui(resultados_globales, archivos_con_errores)

            # MODIFICACIÓN: Generar y guardar resumen CSV actualizado
            if resultados_globales["procesados_exitosos"] > 0:
                summary = self._generate_extraction_summary(resultados_globales, archivos_con_errores)
                self._log_extraction_summary_gui(summary)

                # Generar resumen CSV para GUI (acumulativo)
                csv_summary = self.get_csv_summary_for_gui()
                resultados_globales["csv_summary"] = csv_summary

                # Guardar resumen actualizado
                output_file = self.save_csv_summary_to_file()
                if output_file:
                    self.gui_logger.info(f"📄 Resumen CSV actualizado guardado en: {output_file}")

            # Limpieza final
            self.gui_logger.info("🧹 Limpieza final de procesos Sonel Analysis")
            try:
                self.close_sonel_analysis_force()
            except Exception as e:
                self.gui_logger.warning(f"⚠️ Error en limpieza final: {e}")

            return resultados_globales
            
        except Exception as e:
            self.gui_logger.error(f"❌ Error crítico en extracción GUI: {e}")
            self.gui_logger.error(traceback.format_exc())
            
            return {
                "procesados_exitosos": 0,
                "procesados_fallidos": 0, 
                "saltados": 0,
                "csvs_verificados": 0,
                "detalles": [],
                "modo": "recuperacion_errores_gui",
                "error_critico": True,
                "mensaje_error": str(e)
            }

    def _calculate_total_size(self, archivos_pqm):
        """Calcula el tamaño total de todos los archivos"""
        total_size = 0
        for archivo in archivos_pqm:
            try:
                if os.path.exists(archivo):
                    total_size += os.path.getsize(archivo)
            except Exception as e:
                self.gui_logger.warning(f"⚠️ Error calculando tamaño de {archivo}: {e}")
        return total_size
    
    def _log_extraction_summary_gui(self, summary):
        """Log del resumen de extracción estructurado específico para GUI"""
        self.gui_logger.info("\n" + "="*80)
        self.gui_logger.info("📊 RESUMEN ESTRUCTURADO DE RECUPERACIÓN GUI")
        self.gui_logger.info("="*80)
        self.gui_logger.info(f"📁 Archivos Recuperados: {summary['processed_files']} / {summary['total_files']}")
        self.gui_logger.info(f"⚠️ Advertencias: {summary['warnings']}")
        self.gui_logger.info(f"❌ Errores: {summary['errors']}")
        self.gui_logger.info(f"📄 CSVs Generados: {summary['csv_files_generated']}")
        self.gui_logger.info(f"⏱️ Tiempo Recuperación: {summary['execution_time']}")
        self.gui_logger.info(f"💾 Tamaño Procesado: {summary['total_size']}")
        
        # Calcular tasa de recuperación
        if summary['total_files'] > 0:
            recovery_rate = (summary['csv_files_generated'] / summary['total_files']) * 100
            self.gui_logger.info(f"📈 Tasa de recuperación: {recovery_rate:.1f}%")
        
        self.gui_logger.info("="*80)

    def _log_final_summary_gui(self, resultados_globales, archivos_con_errores):
        """Log del resumen final específico para GUI"""
        self.gui_logger.info("\n" + "="*80)
        self.gui_logger.info("📊 RESUMEN FINAL DE RECUPERACIÓN GUI")
        self.gui_logger.info(f"✅ Archivos recuperados exitosamente: {resultados_globales['procesados_exitosos']}")
        self.gui_logger.info(f"📄 CSVs verificados: {resultados_globales['csvs_verificados']}")
        self.gui_logger.info(f"❌ Fallos en recuperación: {resultados_globales['procesados_fallidos']}")
        self.gui_logger.info(f"📁 Total archivos con errores: {len(archivos_con_errores)}")
        
        # Calcular tasa de recuperación
        total_procesados = resultados_globales['procesados_exitosos'] + resultados_globales['procesados_fallidos']
        if total_procesados > 0:
            tasa_recuperacion = (resultados_globales['procesados_exitosos'] / total_procesados) * 100
            self.gui_logger.info(f"📈 Tasa de recuperación: {tasa_recuperacion:.1f}%")
        
        self.gui_logger.info("="*80)

    def get_extraction_summary_for_gui(self):
        """Método público para obtener el resumen desde el controlador (reutilizando lógica del pywin_extractor)"""
        # Si hay un proceso en curso y se ha calculado el resumen
        if hasattr(self, '_last_extraction_summary'):
            return self._last_extraction_summary
        
        # Si no, generar un resumen basado en el estado actual
        archivos_pqm = self.get_pqm_files()
        
        # Obtener estadísticas de archivos procesados
        stats = self.obtener_estadisticas_procesados()
        
        # Cargar datos detallados de procesamiento
        processed_data = self.file_tracker._load_processed_files_data()
        
        # Contar archivos por estado
        procesados_exitosos = 0
        procesados_fallidos = 0
        csvs_verificados = 0
        
        for archivo_path in archivos_pqm:
            file_path_normalized = os.path.abspath(archivo_path)
            if file_path_normalized in processed_data:
                processed_info = processed_data[file_path_normalized]
                status = processed_info.get('status', '')
                csv_output = processed_info.get('csv_output', {})
                csv_verified = csv_output.get('verified', False)
                
                if status == "exitoso":
                    procesados_exitosos += 1
                    if csv_verified:
                        csvs_verificados += 1
                else:
                    procesados_fallidos += 1
        
        # Archivos saltados son los que no están en procesados
        saltados = len(archivos_pqm) - (procesados_exitosos + procesados_fallidos)
        
        resultados_actuales = {
            "procesados_exitosos": procesados_exitosos,
            "procesados_fallidos": procesados_fallidos,
            "saltados": saltados,
            "csvs_verificados": csvs_verificados,
            "detalles": []
        }
        
        return self._generate_extraction_summary(resultados_actuales, archivos_pqm)

    def _generate_extraction_summary(self, resultados_globales, archivos_pqm):
        """Genera el resumen estructurado para la GUI (reutilizando lógica del pywin_extractor)"""
        
        # Calcular totales
        total_files = len(archivos_pqm)
        processed_files = resultados_globales.get('procesados_exitosos', 0)
        warnings = 0  # Archivos procesados pero con advertencias CSV no verificado
        errors = resultados_globales.get('procesados_fallidos', 0)
        csv_files_generated = resultados_globales.get('csvs_verificados', 0)
        
        # Calcular advertencias basadas en archivos procesados vs CSV verificados
        if processed_files > csv_files_generated:
            warnings = processed_files - csv_files_generated
        
        # Calcular tiempo de ejecución
        if self.process_start_time:
            execution_time = self._format_execution_time_gui(self.process_start_time)
        else:
            execution_time = "0:00"
        
        # Formatear tamaño total
        from core.utils.csv_summary import CSVSummaryUtils
        total_size = CSVSummaryUtils._format_file_size(self.total_size_bytes)
        
        # Generar detalles por archivo
        files_detail = self._generate_files_detail(archivos_pqm, resultados_globales)
        
        summary = {
            "processed_files": processed_files,
            "total_files": total_files,
            "warnings": warnings,
            "errors": errors,
            "csv_files_generated": csv_files_generated,
            "execution_time": execution_time,
            "total_size": total_size,
            "files_detail": files_detail
        }
        
        return summary

    def _format_execution_time_gui(self, start_time, end_time=None):
        """Formatea el tiempo de ejecución (reutilizando lógica del pywin_extractor)"""
        if end_time is None:
            end_time = datetime.now()
        
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"0:{total_seconds:02d}"
        else:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"

    def _generate_files_detail(self, archivos_pqm, resultados_globales):
        """Genera detalles por archivo para la tabla de la GUI (reutilizando lógica del pywin_extractor)"""
        files_detail = []
        processed_data = self.file_tracker._load_processed_files_data()
        
        from core.utils.csv_summary import CSVSummaryUtils
        
        for index, archivo_pqm in enumerate(archivos_pqm, 1):
            file_name = os.path.basename(archivo_pqm)
            file_stem = Path(archivo_pqm).stem
            
            # Obtener tamaño del archivo
            try:
                file_size_bytes = os.path.getsize(archivo_pqm) if os.path.exists(archivo_pqm) else 0
                file_size_str = CSVSummaryUtils._format_file_size(file_size_bytes)
            except:
                file_size_str = "0 MB"
            
            # Normalizar ruta para búsqueda
            file_path_normalized = os.path.abspath(archivo_pqm)
            
            # Obtener información del procesamiento
            processed_info = processed_data.get(file_path_normalized, {})
            
            if file_path_normalized in processed_data:
                status = processed_info.get('status', '')
                csv_output = processed_info.get('csv_output', {})
                csv_verified = csv_output.get('verified', False)
                processing_time = processed_info.get('processing_time_seconds', 0)
                
                # Determinar estado y mensaje
                if status == "exitoso" and csv_verified:
                    status_display = "✅ Procesado"
                    csv_output_name = csv_output.get('filename', f"{file_stem}.csv")
                    message = "Procesado correctamente"
                elif status == "exitoso" and not csv_verified:
                    status_display = "⚠️ Advertencia"
                    csv_output_name = "CSV no verificado"
                    message = "Procesado pero CSV no verificado"
                else:
                    status_display = "❌ Error"
                    csv_output_name = "No generado"
                    error_msg = processed_info.get('error_message', 'Error desconocido')
                    message = f"Error: {error_msg}"
                
                # Formatear tiempo de procesamiento
                if processing_time > 0:
                    if processing_time < 60:
                        duration_str = f"0:{int(processing_time):02d}"
                    else:
                        minutes = int(processing_time // 60)
                        seconds = int(processing_time % 60)
                        duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "0:00"
            else:
                # Archivo no procesado
                status_display = "⏳ Pendiente"
                csv_output_name = f"{file_stem}.csv"
                message = "Archivo pendiente de procesamiento"
                duration_str = "0:00"
            
            files_detail.append({
                "index": index,
                "file_name": file_name,
                "status": status_display,
                "duration": duration_str,
                "size": file_size_str,
                "csv_output": csv_output_name,
                "message": message
            })
        
        return files_detail

    def get_csv_summary_for_gui(self):
        """Genera un resumen completo para la GUI de CSV basado en archivos procesados (reutilizando lógica del pywin_extractor)"""
        try:
            # Obtener lista de archivos .pqm702 disponibles
            archivos_pqm = self.get_pqm_files()
            total_files = len(archivos_pqm)
            
            if total_files == 0:
                from core.utils.csv_summary import CSVSummaryUtils
                return CSVSummaryUtils._get_empty_csv_summary()
            
            # Cargar datos de procesamiento desde JSON
            processed_data = self.file_tracker._load_processed_files_data()
            
            # Inicializar contadores
            processed_files = 0
            errors = 0
            warnings = 0
            csv_files_generated = 0
            total_size_bytes = 0
            execution_times = []
            files_details = []
            
            # Procesar cada archivo
            for archivo_pqm in archivos_pqm:
                file_detail = self._process_file_for_summary(archivo_pqm, processed_data)
                
                # Actualizar contadores según el estado
                if file_detail['processed']:
                    processed_files += 1
                    if file_detail['status_type'] == 'success':
                        csv_files_generated += 1
                    elif file_detail['status_type'] == 'error':
                        errors += 1
                    elif file_detail['status_type'] == 'warning':
                        warnings += 1
                
                # Acumular tamaño y tiempo
                total_size_bytes += file_detail['size_bytes']
                if file_detail['execution_time_seconds'] > 0:
                    execution_times.append(file_detail['execution_time_seconds'])
                
                files_details.append(file_detail)
            
            # Calcular métricas derivadas
            from core.utils.csv_summary import CSVSummaryUtils
            total_execution_time = sum(execution_times) if execution_times else 0
            success_rate = (csv_files_generated / total_files * 100) if total_files > 0 else 0
            avg_speed = CSVSummaryUtils._calculate_average_speed(csv_files_generated, total_execution_time)
            
            # Formatear tiempo total
            execution_time_str = CSVSummaryUtils._format_execution_time(total_execution_time)
            
            # Formatear tamaño total
            total_size_str = CSVSummaryUtils._format_file_size(total_size_bytes)
            
            # Calcular total de registros estimado (basado en archivos exitosos)
            total_records = csv_files_generated * 3278  # Estimación promedio por archivo
            
            return {
                "processed_files": processed_files,
                "total_files": total_files,
                "errors": errors,
                "warnings": warnings,
                "csv_files_generated": csv_files_generated,
                "execution_time": execution_time_str,
                "avg_speed": avg_speed,
                "total_size": total_size_str,
                "success_rate": success_rate,
                "total_records": total_records,
                "files": files_details
            }
            
        except Exception as e:
            self.gui_logger.error(f"❌ Error generando resumen CSV para GUI: {e}")
            from core.utils.csv_summary import CSVSummaryUtils
            return CSVSummaryUtils._get_empty_csv_summary()

    def _process_file_for_summary(self, archivo_pqm, processed_data):
        """Procesa un archivo individual para el resumen con la nueva estructura (reutilizando lógica del pywin_extractor)"""
        file_name = os.path.basename(archivo_pqm)
        file_stem = Path(archivo_pqm).stem
        
        # Verificar si existe físicamente
        file_exists = os.path.exists(archivo_pqm)
        file_size_bytes = os.path.getsize(archivo_pqm) if file_exists else 0
        
        # Normalizar ruta para búsqueda
        file_path_normalized = os.path.abspath(archivo_pqm)
        
        # Obtener información del procesamiento usando la nueva estructura
        processed_info = processed_data.get(file_path_normalized, {})
        
        # Determinar estado y mensaje
        if file_path_normalized in processed_data:
            processed = True
            status = processed_info.get('status', '')
            csv_output = processed_info.get('csv_output', {})
            csv_verified = csv_output.get('verified', False)
            
            # Determinar estado visual y tipo según la nueva estructura
            if status == "exitoso" and csv_verified:
                status_display = "✅ Exitoso"
                status_type = "success"
                message = "Procesado correctamente"
            elif status == "exitoso" and not csv_verified:
                status_display = "⚠️ Advertencia"
                status_type = "warning"
                message = "Procesado pero CSV no verificado"
            else:
                status_display = "❌ Error"
                status_type = "error"
                error_msg = processed_info.get('error_message', 'Error desconocido')
                message = f"Error en procesamiento: {error_msg}"
        else:
            processed = False
            status_display = "⏳ Pendiente"
            status_type = "pending"
            message = "Archivo pendiente de procesamiento"
        
        # Generar nombre del CSV esperado
        csv_output_info = processed_info.get('csv_output', {})
        csv_filename = csv_output_info.get('filename', f"{file_stem}.csv")
        
        # Obtener tiempo de ejecución real o estimado
        execution_time_seconds = processed_info.get('processing_time_seconds', 0)
        if execution_time_seconds <= 0:
            from core.utils.csv_summary import CSVSummaryUtils
            execution_time_seconds = CSVSummaryUtils._estimate_execution_time(file_size_bytes)
        
        from core.utils.csv_summary import CSVSummaryUtils
        execution_time_str = CSVSummaryUtils._format_execution_time(execution_time_seconds)
        
        return {
            "filename": file_name,
            "status": status_display,
            "status_type": status_type,
            "records": execution_time_str,  # La GUI espera esto en la columna "Tiempo"
            "size": CSVSummaryUtils._format_file_size(file_size_bytes),
            "filename_csv": csv_filename,
            "message": message,
            "processed": processed,
            "size_bytes": file_size_bytes,
            "execution_time_seconds": execution_time_seconds
        }

    def save_csv_summary_to_file(self, output_file=None, include_files_detail=True):
        """
        Guarda un resumen del procesamiento CSV en un archivo JSON (reutilizando lógica del pywin_extractor).
        MODIFICACIÓN: Para GUI extractor, actualiza información acumulativa en lugar de sobrescribir.
        """
        try:
            # Definir archivo de salida por defecto
            if output_file is None:
                data_dir = self.config['PATHS']['data_dir']
                output_file = os.path.join(data_dir, "resumen_csv.json")

            # Obtener resumen de CSV actual
            csv_summary = self.get_csv_summary_for_gui()

            # MODIFICACIÓN: Para GUI extractor, cargar datos existentes y actualizar de forma acumulativa
            existing_summary_data = None
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_summary_data = json.load(f)
                    self.gui_logger.info("📄 Cargando resumen existente para actualización acumulativa")
                except Exception as e:
                    self.gui_logger.warning(f"⚠️ Error cargando resumen existente: {e}")
                    existing_summary_data = None

            # Construir estructura de salida
            summary_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat() + 'Z',
                    "etl_version": "1.0",
                    "config_file": getattr(self, 'config_file', 'config.ini'),
                    "extractor_type": "pygui_extractor"  # Identificar que fue actualizado por GUI
                },
                "csv_summary": {
                    "processed_files": csv_summary.get("processed_files"),
                    "total_files": csv_summary.get("total_files"),
                    "errors": csv_summary.get("errors"),
                    "warnings": csv_summary.get("warnings"),
                    "csv_files_generated": csv_summary.get("csv_files_generated"),
                    "execution_time": csv_summary.get("execution_time"),
                    "avg_speed": csv_summary.get("avg_speed"),
                    "total_size": csv_summary.get("total_size"),
                    "success_rate": csv_summary.get("success_rate"),
                    "total_records": csv_summary.get("total_records")
                },
                "files_processed": []
            }

            # MODIFICACIÓN: Si existe un resumen anterior y es del pywin_extractor, preservar metadatos
            if existing_summary_data and existing_summary_data.get("metadata", {}).get("extractor_type") != "pygui_extractor":
                summary_data["metadata"]["original_extractor"] = "pywin_extractor"
                summary_data["metadata"]["updated_by"] = "pygui_extractor"
                
                # Log de la actualización acumulativa
                old_csv_summary = existing_summary_data.get("csv_summary", {})
                old_processed = old_csv_summary.get("processed_files", 0)
                old_csv_generated = old_csv_summary.get("csv_files_generated", 0)
                old_errors = old_csv_summary.get("errors", 0)
                
                new_processed = csv_summary.get("processed_files", 0)
                new_csv_generated = csv_summary.get("csv_files_generated", 0)
                new_errors = csv_summary.get("errors", 0)
                
                self.gui_logger.info("🔄 ACTUALIZACIÓN ACUMULATIVA DETECTADA:")
                self.gui_logger.info(f"   📊 Procesados: {old_processed} → {new_processed} (Δ{new_processed - old_processed})")
                self.gui_logger.info(f"   📄 CSVs generados: {old_csv_generated} → {new_csv_generated} (Δ{new_csv_generated - old_csv_generated})")
                self.gui_logger.info(f"   ❌ Errores: {old_errors} → {new_errors} (Δ{new_errors - old_errors})")

            # Incluir detalle de archivos si se solicita
            if include_files_detail:
                summary_data["files_processed"] = csv_summary.get("files", [])

            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Guardar archivo JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)

            self.gui_logger.info(f"Resumen CSV actualizado y guardado en: {output_file}")
            self.gui_logger.info(f"Tamaño del archivo: {os.path.getsize(output_file)} bytes")

            return output_file

        except Exception as e:
            self.gui_logger.error(f"Error guardando resumen CSV: {e}")
            self.gui_logger.error(traceback.format_exc())
            return None