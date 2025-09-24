import os
import json
import time
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
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
            'export_dir': config['PATHS']['export_dir'],
            'sonel_exe_path': ruta_exe or config['PATHS']['sonel_exe_path'],
            'reprocess_dir': config['PATHS']['export_dir'],
            'process_file_dir': Path(input_dir or config['PATHS']['input_dir']).resolve(),
            'coordinates_file': coordinates_file or os.path.join(config['PATHS']['output_dir'], 'component_positions.json')
        }
        
        # Configuración de delays para verificación (reutilizando)
        self.delays = {
            'file_verification': config['GUI']['delays']['file_verification'],
            'ui_response': config['GUI']['delays']['ui_response'],
            'between_files': config['GUI']['delays']['between_files']
        }

        self.archivos_reprocesados_sesion = {}
        self.session_start_time = datetime.now()
        
        # Crear directorios usando función centralizada
        create_directories()
        os.makedirs(self.PATHS['output_dir'], exist_ok=True)
        os.makedirs(self.PATHS['export_dir'], exist_ok=True)
        os.makedirs(self.PATHS['process_file_dir'], exist_ok=True)
    
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
        pqm_files = self.file_manager.get_pqm_files()
        
        if pqm_files:
            # Analizar duplicados por directorio
            duplicate_analysis = self.file_manager.check_duplicate_filenames_across_directories(pqm_files)
            
            self.gui_logger.info("📊 Análisis de duplicados por directorio:")
            self.gui_logger.info(f"   📁 Total de archivos: {duplicate_analysis['total_files']}")
            self.gui_logger.info(f"   📋 Nombres únicos: {duplicate_analysis['unique_filenames']}")
            self.gui_logger.info(f"   🔄 Nombres duplicados: {duplicate_analysis['duplicate_filenames']}")
            
            if duplicate_analysis['duplicate_filenames'] > 0:
                self.gui_logger.info("   ✅ Cada archivo será procesado independientemente por directorio")
                self.gui_logger.info("   📝 Los CSVs tendrán numeración incremental para evitar conflictos")
        
        return pqm_files

    def obtener_estadisticas_procesados(self):
        """Obtiene estadísticas de archivos procesados"""
        return self.file_tracker.get_processing_statistics()

    def ya_ha_sido_procesado(self, file_path):
        """Verifica si un archivo ya ha sido procesado anteriormente"""
        file_name = os.path.basename(file_path)
        file_path_normalized = os.path.abspath(file_path)

        # Verificar con la clave única existente (lógica actual)
        if self.file_tracker.is_already_processed(file_path):
            self.gui_logger.info(f"📌 Archivo '{file_name}' detectado como procesado por CLAVE única.")
            return True

        # Verificar si el archivo ya está registrado en source_paths de algún registro
        if os.path.exists(self.file_tracker.processed_files_json):
            with open(self.file_tracker.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            for entry in processed_data.get("files", {}).values():
                if entry.get("filename") == file_name:
                    if file_path_normalized in entry.get("source_paths", []):
                        self.gui_logger.info(f"📌 Archivo '{file_name}' detectado como procesado por RUTA en source_paths: {file_path_normalized}")
                        return True  # Ya procesado en este directorio

        # Si no está ni por clave ni por ruta
        return False

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
        Obtiene lista de archivos que han sido procesados con errores o advertencias.
        Maneja archivos desde múltiples directorios usando las rutas exactas del registro.
        
        Returns:
            list: Lista de rutas completas de archivos con errores
        """
        try:
            processed_data = self.file_tracker._load_processed_files_data()
            archivos_con_errores = []
            
            if not processed_data:
                self.gui_logger.info("📋 No hay archivos procesados registrados")
                return []
            
            for file_key, file_info in processed_data.items():
                filename = file_info.get('filename', '')
                status = file_info.get('status', '')
                csv_output = file_info.get('csv_output', {})
                csv_verified = csv_output.get('verified', False)
                source_paths = file_info.get('source_paths', [])
                current_source_path = file_info.get('current_source_path', '')
                
                # Solo considerar archivos con errores reales
                # No incluir archivos exitosos con CSV verificado
                has_errors = (status != "exitoso") or (status == "exitoso" and not csv_verified)
                
                if has_errors:
                    # Intentar encontrar el archivo usando las rutas registradas
                    archivo_encontrado = None
                    
                    # Prioridad 1: current_source_path (última ruta conocida)
                    if current_source_path and os.path.exists(current_source_path):
                        archivo_encontrado = current_source_path
                        self.gui_logger.debug(f"📍 Archivo encontrado en ruta actual: {current_source_path}")
                    
                    # Prioridad 2: buscar en todas las source_paths
                    if not archivo_encontrado:
                        for path in source_paths:
                            if os.path.exists(path):
                                archivo_encontrado = path
                                self.gui_logger.debug(f"📍 Archivo encontrado en ruta alternativa: {path}")
                                break
                    
                    # Prioridad 3: buscar en directorio de entrada por defecto
                    if not archivo_encontrado:
                        default_path = os.path.join(self.PATHS['input_dir'], filename)
                        if os.path.exists(default_path):
                            archivo_encontrado = default_path
                            self.gui_logger.debug(f"📍 Archivo encontrado en directorio por defecto: {default_path}")
                    
                    # Si se encontró el archivo, agregarlo a la lista
                    if archivo_encontrado:
                        archivos_con_errores.append(archivo_encontrado)
                        self.gui_logger.info(f"   ⚠️ {filename} -> {archivo_encontrado}")
                    else:
                        self.gui_logger.warning(f"   🔍 Archivo no encontrado: {filename}")
                        self.gui_logger.warning(f"       Rutas buscadas: {source_paths}")
            
            # Log mejorado para mostrar diferencia entre archivos con errores vs exitosos
            total_procesados = len(processed_data)
            exitosos_verificados = sum(1 for f in processed_data.values() 
                                    if f.get('status') == 'exitoso' and f.get('csv_output', {}).get('verified', False))
            
            self.gui_logger.info(f"📋 Total archivos procesados: {total_procesados}")
            self.gui_logger.info(f"✅ Archivos exitosos verificados: {exitosos_verificados}")
            self.gui_logger.info(f"⚠️ Archivos con errores encontrados: {len(archivos_con_errores)}")
            
            return archivos_con_errores
            
        except Exception as e:
            self.gui_logger.error(f"❌ Error obteniendo archivos con errores: {e}")
            return []

    def ejecutar_extraccion_archivo_gui(self, archivo_pqm):
        """
        MODIFICADO: Registra específicamente archivos reprocesados en esta sesión
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
            # Marcar inicio de reprocesamiento
            self.archivos_reprocesados_sesion[archivo_pqm] = {
                'filename': nombre_archivo,
                'start_time': start_time,
                'status': 'processing'
            }

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
            
            # Actualizar registro de reprocesamiento
            if archivo_pqm in self.archivos_reprocesados_sesion:
                self.archivos_reprocesados_sesion[archivo_pqm].update({
                    'end_time': end_time,
                    'processing_time_seconds': processing_time,
                    'status': 'success' if proceso_exitoso else 'error',
                    'csv_generated': proceso_exitoso and csv_path_generado is not None,
                    'csv_path': csv_path_generado,
                    'error_message': error_message
                })

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
                    time.sleep(4)
            
            # Restaurar método original
            extractor_principal.ejecutar_extraccion_archivo = metodo_original
            extractor_principal.ya_ha_sido_procesado = original_is_processed
            
            # Resumen final
            self._log_final_summary_gui(resultados_globales, archivos_con_errores)

            # Generar y guardar resumen CSV actualizado
            if resultados_globales["procesados_exitosos"] > 0:
                summary = self._generate_extraction_summary(resultados_globales, archivos_con_errores)
                self._log_extraction_summary_gui(summary)

                # Generar resumen CSV para GUI (acumulativo)
                csv_summary = self.get_csv_summary_for_gui(summary)
                resultados_globales["csv_summary"] = csv_summary

                # Guardar resumen actualizado
                output_file = self.save_csv_summary_to_file(summary)
                if output_file:
                    self.gui_logger.info(f"📄 Resumen CSV actualizado guardado en: {output_file}")

            # Limpieza final
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
        self.gui_logger.info(f"📁 Total archivos con errores: {resultados_globales['procesados_fallidos']}")
        
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
        """
        CORREGIDO: Genera el resumen estructurado preservando la información real del directorio origen
        """
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
        total_size = CSVSummaryUtils._format_file_size(self.total_size_bytes)
        
        # Generar detalles preservando directorio origen real**
        files_detail = self._generate_files_detail_with_real_directories(archivos_pqm, resultados_globales)
        
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
    
    def _generate_files_detail_with_real_directories(self, archivos_pqm, resultados_globales):
        """
        CORREGIDO: Genera detalles por archivo preservando el directorio real de origen
        """
        files_detail = []
        processed_data = self.file_tracker._load_processed_files_data()
        
        for index, archivo_pqm in enumerate(archivos_pqm, 1):
            file_name = os.path.basename(archivo_pqm)
            file_stem = Path(archivo_pqm).stem
            
            # Obtener directorio origen REAL del archivo actual**
            real_source_directory = os.path.basename(os.path.dirname(os.path.abspath(archivo_pqm)))
            
            # Obtener tamaño del archivo
            try:
                file_size_bytes = os.path.getsize(archivo_pqm) if os.path.exists(archivo_pqm) else 0
                file_size_str = CSVSummaryUtils._format_file_size(file_size_bytes)
            except:
                file_size_str = "0 MB"
            
            # Buscar información de procesamiento usando current_source_path**
            processed_info = None
            file_path_normalized = os.path.abspath(archivo_pqm)
            
            # Buscar por ruta exacta primero
            if file_path_normalized in processed_data:
                processed_info = processed_data[file_path_normalized]
            else:
                # Buscar por current_source_path o source_paths
                for key, data in processed_data.items():
                    current_path = data.get('current_source_path', '')
                    source_paths = data.get('source_paths', [])
                    
                    if (current_path and os.path.abspath(current_path) == file_path_normalized) or \
                    (file_path_normalized in [os.path.abspath(p) for p in source_paths]):
                        processed_info = data
                        break
            
            if processed_info:
                status = processed_info.get('status', '')
                csv_output = processed_info.get('csv_output', {})
                csv_verified = csv_output.get('verified', False)
                processing_time = processed_info.get('processing_time_seconds', 0)
                
                # Preservar directorio origen registrado o usar el real**
                # current_source_path > source_paths > directorio actual
                registered_source_path = processed_info.get('current_source_path', '')
                if registered_source_path:
                    registered_directory = os.path.basename(os.path.dirname(registered_source_path))
                else:
                    source_paths = processed_info.get('source_paths', [])
                    if source_paths:
                        registered_directory = os.path.basename(os.path.dirname(source_paths[0]))
                    else:
                        registered_directory = real_source_directory
                
                # Determinar estado y mensaje
                if status == "exitoso" and csv_verified:
                    status_display = "✅ Procesado"
                    csv_output_name = csv_output.get('filename', f"{file_stem}.csv")
                    message = f"Procesado correctamente (Dir origen: {registered_directory})"
                elif status == "exitoso" and not csv_verified:
                    status_display = "⚠️ Advertencia"
                    csv_output_name = "CSV no verificado"
                    message = f"Procesado pero CSV no verificado (Dir origen: {registered_directory})"
                else:
                    status_display = "❌ Error"
                    csv_output_name = "No generado"
                    error_msg = processed_info.get('error_message', 'Error desconocido')
                    message = f"Error: {error_msg} (Dir origen: {registered_directory})"
                
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
                message = f"Archivo pendiente de procesamiento (Dir: {real_source_directory})"
                duration_str = "0:00"
                registered_directory = real_source_directory
            
            files_detail.append({
                "index": index,
                "filename": file_name,
                "status": status_display,
                "records": duration_str,
                "size": file_size_str,
                "filename_csv": csv_output_name,
                "message": message,
                "source_directory": registered_directory,  # Usar directorio real**
                "processed": file_path_normalized in processed_data or processed_info is not None,
                "size_bytes": file_size_bytes if 'file_size_bytes' in locals() else 0,
                "execution_time_seconds": processing_time if 'processing_time' in locals() else 0
            })
        
        return files_detail

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

    def get_csv_summary_for_gui(self, summary):
        """
        CORREGIDO: Actualiza automáticamente archivos reprocesados en el resumen
        """
        try:
            # Obtener archivos con errores (base para reprocesamiento)
            archivos_pqm = self.get_archivos_con_errores()
            total_files = len(archivos_pqm)
            
            if total_files == 0:
                return CSVSummaryUtils._get_empty_csv_summary()

            # Cargar datos de procesamiento
            processed_data = self.file_tracker._load_processed_files_data()
            
            # Inicializar contadores
            processed_files = 0
            errors = 0
            warnings = 0
            csv_files_generated = 0
            total_size_bytes = 0
            execution_times = []
            files_details = []
            
            # Contadores para reprocesamiento
            reprocessed_count = 0
            errors_corrected = 0
            new_csvs_generated = 0

            # Procesar cada archivo
            for archivo_pqm in archivos_pqm:
                file_detail = self._process_file_for_summary_with_real_directory(archivo_pqm, processed_data)
                
                # Verificar si fue reprocesado exitosamente en esta sesión
                if archivo_pqm in self.archivos_reprocesados_sesion:
                    reprocess_info = self.archivos_reprocesados_sesion[archivo_pqm]
                    
                    if reprocess_info.get('status') == 'success' and reprocess_info.get('csv_generated', False):
                        # Actualizar archivo con información de reprocesamiento
                        original_status_type = file_detail.get('status_type', 'error')
                        
                        file_detail.update({
                            'status': "✅ Exitoso (.pqm702)",
                            'status_type': 'success',
                            'message': f"Reprocesado correctamente (Origen: {file_detail.get('source_directory', 'directorio_desconocido')})",
                            'execution_time_seconds': reprocess_info.get('processing_time_seconds', 0),
                            'records': self._format_execution_time_from_seconds(reprocess_info.get('processing_time_seconds', 0)),
                            'filename_csv': f"{Path(file_detail['filename']).stem}.csv",
                            'processed': True,
                            'reprocessed_in_session': True,
                            'original_status': original_status_type
                        })
                        
                        # Actualizar contadores
                        reprocessed_count += 1
                        new_csvs_generated += 1
                        
                        if original_status_type == 'error':
                            errors_corrected += 1

            # Calcular métricas finales
            total_execution_time = sum(execution_times) if execution_times else 0
            success_rate = (csv_files_generated / total_files * 100) if total_files > 0 else 0
            avg_speed = CSVSummaryUtils._calculate_average_speed(csv_files_generated, total_execution_time)
            execution_time_str = CSVSummaryUtils._format_execution_time(total_execution_time)
            total_size_str = CSVSummaryUtils._format_file_size(total_size_bytes)
            total_records = csv_files_generated * 3278

            # Log de reprocesamiento
            if summary['total_files'] > 0:
                self.gui_logger.info(f"🔄 Resumen de reprocesamiento:")
                self.gui_logger.info(f"   Archivos reprocesados: {summary['total_files']}")
                self.gui_logger.info(f"   Errores corregidos: {summary['processed_files']}")
                self.gui_logger.info(f"   Nuevos CSVs: {summary['csv_files_generated']}")
                self.gui_logger.info(f"   Errores restantes: {summary['errors']}")

            return {
                "processed_files": processed_files,
                "total_files": total_files,
                "errors": summary['errors'],  # Ya actualizado
                "warnings": warnings,
                "csv_files_generated": total_files + summary['csv_files_generated'],  # Ya actualizado
                "execution_time": execution_time_str,  # Ya actualizado
                "avg_speed": avg_speed,
                "total_size": total_size_str + summary['total_size'],
                "success_rate": success_rate,  # Ya actualizado
                "total_records": total_records,
                "files": files_details,
                # Información de reprocesamiento
                "reprocessing_info": {
                    "reprocessed_files": reprocessed_count,
                    "errors_corrected": errors_corrected,
                    "new_csvs_generated": new_csvs_generated
                }
            }
            
        except Exception as e:
            self.gui_logger.error(f"❌ Error generando resumen CSV para GUI: {e}")
            return CSVSummaryUtils._get_empty_csv_summary()

    def _format_execution_time_from_seconds(self, seconds):
        """
        Formatea segundos a formato MM:SS
        """
        if seconds <= 0:
            return "0:00"
        
        if seconds < 60:
            return f"0:{int(seconds):02d}"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}:{remaining_seconds:02d}"

    def _process_file_for_summary(self, archivo_pqm, processed_data):
        """
        Procesa un archivo individual para el resumen.
        Corrige la identificación de archivos procesados usando solo file_stem.
        """
        file_name = os.path.basename(archivo_pqm)
        file_stem = Path(archivo_pqm).stem

        # Verificar si existe físicamente
        file_exists = os.path.exists(archivo_pqm)
        file_size_bytes = os.path.getsize(archivo_pqm) if file_exists else 0

        # Buscar info de procesamiento por file_stem
        processed_info = None
        for key, data in processed_data.items():
            if data.get("file_stem") == file_stem:
                processed_info = data
                break

        if processed_info:
            processed = True
            status = processed_info.get('status', '')
            csv_output = processed_info.get('csv_output', {})
            csv_verified = csv_output.get('verified', False)

            if status == "exitoso" and csv_verified:
                status_display = "✅ Exitoso"
                status_type = "success"
                message = "Procesado correctamente"
                
                # Confirmar existencia real del CSV
                csv_path = csv_output.get('path', '')
                if not csv_path or not os.path.exists(csv_path):
                    status_display = "⚠️ Advertencia"
                    status_type = "warning"
                    message = "Procesado pero CSV no encontrado en disco"
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
            # Solo archivos realmente no procesados
            processed = False
            status_display = "⏳ Pendiente"
            status_type = "pending"
            message = "Archivo pendiente de procesamiento"

        # Nombre del CSV esperado
        csv_filename = csv_output.get('filename', f"{file_stem}.csv") if processed_info else f"{file_stem}.csv"

        # Tiempo de ejecución
        execution_time_seconds = processed_info.get('processing_time_seconds', 0) if processed_info else 0
        if execution_time_seconds <= 0:
            execution_time_seconds = CSVSummaryUtils._estimate_execution_time(file_size_bytes)

        execution_time_str = CSVSummaryUtils._format_execution_time(execution_time_seconds)

        return {
            "filename": file_name,
            "status": status_display,
            "status_type": status_type,
            "records": execution_time_str,
            "size": CSVSummaryUtils._format_file_size(file_size_bytes),
            "filename_csv": csv_filename,
            "message": message,
            "processed": processed,
            "size_bytes": file_size_bytes,
            "execution_time_seconds": execution_time_seconds
        }
    
    def _process_file_for_summary_with_real_directory(self, archivo_pqm, processed_data):
        """
        CORREGIDO: Procesa archivo preservando directorio origen real y 
        marcando correctamente archivos reprocesados
        """
        file_name = os.path.basename(archivo_pqm)
        file_stem = Path(archivo_pqm).stem

        # Obtener directorio origen REAL**
        real_source_directory = os.path.basename(os.path.dirname(os.path.abspath(archivo_pqm)))

        # Verificar si existe físicamente
        file_exists = os.path.exists(archivo_pqm)
        file_size_bytes = os.path.getsize(archivo_pqm) if file_exists else 0

        # Buscar info de procesamiento preservando información origen**
        processed_info = None
        file_path_normalized = os.path.abspath(archivo_pqm)

        # Buscar información de procesamiento usando múltiples criterios
        for key, data in processed_data.items():
            # Criterio 1: Ruta exacta
            if key == file_path_normalized:
                processed_info = data
                break
            
            # Criterio 2: current_source_path
            current_path = data.get('current_source_path', '')
            if current_path and os.path.abspath(current_path) == file_path_normalized:
                processed_info = data
                break
            
            # Criterio 3: source_paths
            source_paths = data.get('source_paths', [])
            if file_path_normalized in [os.path.abspath(p) for p in source_paths]:
                processed_info = data
                break

        if processed_info:
            processed = True
            status = processed_info.get('status', '')
            csv_output = processed_info.get('csv_output', {})
            csv_verified = csv_output.get('verified', False)

            # **PRESERVAR directorio origen registrado si existe**
            registered_source_path = processed_info.get('current_source_path', '')
            if registered_source_path:
                source_directory = os.path.basename(os.path.dirname(registered_source_path))
            else:
                source_paths = processed_info.get('source_paths', [])
                if source_paths:
                    source_directory = os.path.basename(os.path.dirname(source_paths[0]))
                else:
                    source_directory = real_source_directory

            # Determinar estado basado en procesamiento real**
            if status == "exitoso" and csv_verified:
                status_display = "✅ Exitoso"
                status_type = "success"
                message = f"Procesado correctamente (Origen: {source_directory})"
            elif status == "exitoso" and not csv_verified:
                status_display = "⚠️ Advertencia"
                status_type = "warning"
                message = f"Procesado pero CSV no verificado (Origen: {source_directory})"
            else:
                status_display = "❌ Error"
                status_type = "error"
                error_msg = processed_info.get('error_message', 'Error desconocido')
                message = f"Error: {error_msg} (Origen: {source_directory})"
        else:
            # Archivo no procesado
            processed = False
            status_display = "⏳ Pendiente"
            status_type = "pending"
            message = f"Archivo pendiente de procesamiento"
            source_directory = real_source_directory

        # Nombre del CSV esperado
        csv_filename = csv_output.get('filename', f"{file_stem}.csv") if processed_info else f"{file_stem}.csv"

        # Tiempo de ejecución
        execution_time_seconds = processed_info.get('processing_time_seconds', 0) if processed_info else 0
        if execution_time_seconds <= 0:
            execution_time_seconds = CSVSummaryUtils._estimate_execution_time(file_size_bytes)

        execution_time_str = CSVSummaryUtils._format_execution_time(execution_time_seconds)

        return {
            "filename": file_name,
            "status": status_display,
            "status_type": status_type,
            "records": execution_time_str,
            "size": CSVSummaryUtils._format_file_size(file_size_bytes),
            "filename_csv": csv_filename,
            "message": message,
            "processed": processed,
            "size_bytes": file_size_bytes,
            "execution_time_seconds": execution_time_seconds,
            "source_directory": source_directory,
            "reprocessed_in_recovery": processed and status == "exitoso"  # Marcar reprocesados**
        }

    def save_csv_summary_to_file(self, summary, output_file=None, include_files_detail=True):
        """
        CORREGIDO: Actualiza correctamente archivos reprocesados y métricas globales
        """
        try:
            # Definir archivo de salida
            if output_file is None:
                export_dir = self.PATHS.get('export_dir')
                if not export_dir:
                    export_dir = self.PATHS.get('export_dir', os.path.join(os.getcwd(), 'export'))
                
                os.makedirs(export_dir, exist_ok=True)
                output_file = os.path.join(export_dir, "resumen_csv.json")

            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Obtener resumen actual (ya incluye archivos reprocesados actualizados)
            csv_summary_actual = self.get_csv_summary_for_gui(summary)
            
            if not csv_summary_actual:
                self.gui_logger.warning("⚠️ No se pudo generar el resumen CSV")
                return None

            # Cargar datos existentes
            existing_data = {}
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    self.gui_logger.info(f"📊 Cargando datos existentes desde: {output_file}")
                except Exception as e:
                    self.gui_logger.warning(f"⚠️ Error cargando datos existentes: {e}")
                    existing_data = {}

            # Obtener información de reprocesamiento
            reprocessed_files_count = summary['total_files']
            errors_corrected = summary['processed_files']
            new_csvs_generated = summary['csv_files_generated']

            # Consolidar archivos con lógica de actualización inteligente
            consolidated_files = {}
            
            # 1. Cargar archivos existentes
            existing_files = existing_data.get("files_processed", [])
            for file_data in existing_files:
                if isinstance(file_data, dict) and 'filename' in file_data:
                    filename = file_data['filename']
                    source_dir = file_data.get('source_directory', 'directorio_desconocido')
                    file_key = f"{filename}_{source_dir}"
                    consolidated_files[file_key] = file_data

            # 2. Actualizar con archivos del resumen actual
            for full_path, session_data in self.archivos_reprocesados_sesion.items():
                if isinstance(session_data, dict) and 'filename' in session_data:
                    filename = session_data['filename']
                    
                    # Extraer directorio desde la ruta completa
                    source_dir = os.path.basename(os.path.normpath(os.path.dirname(full_path)))
                    file_key = f"{filename}_{source_dir}"
                    
                    if file_key in consolidated_files:
                        # Archivo existente - actualizar con datos de sesión
                        existing_file = consolidated_files[file_key]
                        
                        # Determinar status y message basados en la sesión
                        if session_data.get('status') == 'success':
                            status = '✅ Exitoso (.pqm702)'
                            status_type = 'success'
                            message = f"Reprocesado correctamente (Origen: {source_dir})"
                        else:
                            status = '❌ Error'
                            status_type = 'error' 
                            message = session_data.get('error_message', f"Error en reprocesamiento (Origen: {source_dir})")
                        
                        # Actualizar archivo existente con datos de sesión
                        consolidated_files[file_key] = {
                            'filename': filename,
                            'source_directory': source_dir,
                            'pqm_type': existing_file.get('pqm_type', '.pqm702'),
                            'size_bytes': existing_file.get('size_bytes', 0),
                            'size': existing_file.get('size', '0 MB'),
                            'status': status,
                            'status_type': status_type,
                            'message': message,
                            'processing_date': datetime.now().isoformat(),
                            'execution_time_seconds': session_data.get('processing_time_seconds', existing_file.get('execution_time_seconds', 0)),
                            'records': existing_file.get('records', '0:00'),
                            'filename_csv': session_data.get('csv_path', existing_file.get('filename_csv', f"{Path(filename).stem}.csv")) if session_data.get('csv_path') else existing_file.get('filename_csv', f"{Path(filename).stem}.csv"),
                            'processed': True,
                            'reprocessed_in_recovery': True,
                            'original_status': existing_file.get('status_type', 'error'),
                            'recovery_successful': session_data.get('status') == 'success',
                            'same_name_other_dirs': existing_file.get('same_name_other_dirs', 0)
                        }
                    else:
                        
                        # Determinar status y message basados en la sesión  
                        if session_data.get('status') == 'success':
                            status = '✅ Exitoso (.pqm702)'
                            status_type = 'success'
                            message = f"Procesado correctamente (Origen: {source_dir})"
                        else:
                            status = '❌ Error'
                            status_type = 'error'
                            message = session_data.get('error_message', f"Error en procesamiento (Origen: {source_dir})")
                        
                        consolidated_files[file_key] = {
                            'filename': filename,
                            'source_directory': source_dir,
                            'pqm_type': '.pqm702',
                            'size_bytes': 0,
                            'size': '0 MB', 
                            'status': status,
                            'status_type': status_type,
                            'message': message,
                            'processing_date': datetime.now().isoformat(),
                            'execution_time_seconds': session_data.get('processing_time_seconds', 0),
                            'records': '0:00',
                            'filename_csv': session_data.get('csv_path', f"{Path(filename).stem}.csv") if session_data.get('csv_path') else f"{Path(filename).stem}.csv",
                            'processed': True,
                            'reprocessed_in_recovery': True,
                            'original_status': 'new',
                            'recovery_successful': session_data.get('status') == 'success',
                            'same_name_other_dirs': 0
                        }

            # Recalcular métricas globales basadas en archivos consolidados
            total_files = len(consolidated_files)
            processed_files = sum(1 for f in consolidated_files.values() if f.get('processed', False))
            warnings = sum(1 for f in consolidated_files.values() if f.get('status_type') == 'warning')
            current_csv_files_generated = sum(1 for f in consolidated_files.values() if f.get('status_type') == 'success')
            
            # Tiempos y tamaños actualizados
            total_execution_time = sum(f.get('execution_time_seconds', 0) for f in consolidated_files.values())
            total_size_bytes = sum(f.get('size_bytes', 0) for f in consolidated_files.values())
            
            # Formatear métricas
            execution_time_str = CSVSummaryUtils._format_execution_time(total_execution_time)
            total_size_str = CSVSummaryUtils._format_file_size(total_size_bytes)
            success_rate = (summary['csv_files_generated'] / summary['total_files'] * 100) if total_files > 0 else 0
            avg_speed = CSVSummaryUtils._calculate_average_speed(current_csv_files_generated, total_execution_time)
            total_records = current_csv_files_generated * 3278

            # Información de directorios
            unique_directories = list(set(f.get('source_directory', '') for f in consolidated_files.values()))
            
            summary_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "etl_version": "1.2.2",
                    "config_file": getattr(self, 'config_file', 'config.ini'),
                    "registry_file": self.file_tracker.processed_files_json,
                    "extractor_type": "pygui_extractor",
                    "operation_mode": "error_recovery_consolidation",
                    "consolidation_info": {
                        "total_directories_processed": len(unique_directories),
                        "directories_list": unique_directories,
                        "last_consolidation": datetime.now().isoformat(),
                        "reprocessed_files_count": reprocessed_files_count,
                        "recovered_files_count": reprocessed_files_count,  # Mismo valor para coherencia
                        "recovery_session_files": reprocessed_files_count,
                        "errors_corrected": errors_corrected,
                        "new_csvs_generated": new_csvs_generated
                    }
                },
                "csv_summary": {
                    "processed_files": processed_files,
                    "total_files": total_files,
                    "errors": summary['errors'],  # Actualizado correctamente
                    "warnings": warnings,
                    "csv_files_generated": current_csv_files_generated,  # Actualizado correctamente
                    "execution_time": execution_time_str,  # Actualizado correctamente
                    "avg_speed": avg_speed,
                    "total_size": total_size_str + summary['total_size'],
                    "success_rate": success_rate,  # Actualizado correctamente
                    "total_records": total_records
                },
                "files_processed": list(consolidated_files.values()) if include_files_detail else []
            }

            # Guardar archivo
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)

            # Log mejorado
            self.gui_logger.info(f"✅ Resumen CSV actualizado guardado en: {output_file}")
            self.gui_logger.info(f"📊 Archivos consolidados: {total_files} de {len(unique_directories)} directorios")
            
            if reprocessed_files_count > 0:
                self.gui_logger.info(f"🔄 Archivos reprocesados en sesión: {reprocessed_files_count}")
                self.gui_logger.info(f"✅ Archivos recuperados exitosamente: {reprocessed_files_count}")
                self.gui_logger.info(f"🔧 Errores corregidos: {summary['processed_files']}")
                self.gui_logger.info(f"📄 Nuevos CSVs generados: {summary['csv_files_generated']}")
                
            self.gui_logger.info(f"📈 Tasa de éxito final: {success_rate:.1f}%")
            self.gui_logger.info(f"❌ Errores restantes: {summary['errors']}")
            self.gui_logger.info(f"📄 CSVs totales: {summary['csv_files_generated']}")
            
            return output_file

        except Exception as e:
            self.gui_logger.error(f"❌ Error crítico guardando resumen CSV: {e}")
            self.gui_logger.error(traceback.format_exc())
            return None