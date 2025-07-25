import os
import json
import time
import psutil
import logging
import traceback
from pathlib import Path
from datetime import datetime
from config.logger import get_logger
from core.utils.csv_summary import CSVSummaryUtils
from config.settings import get_full_config, create_directories, load_config, PATHS

# Imports de los nuevos módulos
from core.extractors.pyautowin_extractor.w_analysis import SonelAnalisisInicial
from core.extractors.pyautowin_extractor.w_configuration import SonelConfiguracion

# Imports de los módulos modularizados
from .pywin_modules.file_manager import FileManager
from .pywin_modules.file_tracker import FileTracker
from .pywin_modules.process_manager import ProcessManager
from .pywin_modules.csv_generator import CSVGenerator

class SonelExtractorCompleto:
    """Coordinador principal que maneja ambas clases con procesamiento dinámico"""
    
    def __init__(self, input_dir=None, output_dir=None, ruta_exe=None):
        # Configuración de rutas
        config = get_full_config()
        config_file = 'config.ini'
        self.config = load_config(config_file)

        # Configuración de paths por defecto
        self.PATHS = {
            'input_dir': input_dir or config['PATHS']['input_dir'],
            'output_dir': output_dir or config['PATHS']['export_dir'],
            'export_dir': output_dir or config['PATHS']['export_dir'],
            'sonel_exe_path': ruta_exe or config['PATHS']['sonel_exe_path'],
            'temp_dir': config['PATHS']['temp_dir'],
            'process_file_dir': Path(input_dir or config['PATHS']['input_dir']).resolve()
        }
        
        # Configuración de delays para verificación
        self.delays = {
            'file_verification': config['GUI']['delays']['file_verification'],
            'ui_response': config['GUI']['delays']['ui_response'],
            'between_files': config['GUI']['delays']['between_files']
        }
        
        # Crear directorios usando función centralizada
        create_directories()

        # Crear directorios si no existen
        os.makedirs(self.PATHS['output_dir'], exist_ok=True)
        os.makedirs(self.PATHS['process_file_dir'], exist_ok=True)
        os.makedirs(self.PATHS['temp_dir'], exist_ok=True)
    
        # ✅ Logger específico para pywinauto (para usar en clases hijas)
        self.pywinauto_logger = get_logger("pywinauto", f"{__name__}_pywinauto")
        
        # Configurar nivel de logging
        self.pywinauto_logger.setLevel(getattr(logging, config['LOGGING']['level']))
        
        self.pywinauto_logger.info("="*80)
        self.pywinauto_logger.info("🚀 EXTRACTOR COMPLETO SONEL ANALYSIS - INICIO")
        self.pywinauto_logger.info(f"📁 Directorio entrada: {self.PATHS['input_dir']}")
        self.pywinauto_logger.info(f"📁 Directorio salida: {self.PATHS['output_dir']}")
        self.pywinauto_logger.info("="*80)
        
        # ✅ Log de configuración de loggers
        self.pywinauto_logger.info("📊 Sistema de logging configurado:")
        self.pywinauto_logger.info(f"   - Logger pywinauto: {self.pywinauto_logger.name}")

        # Inicializar módulos
        self._init_modules()

    def _init_modules(self):
        """Inicializa los módulos modularizados"""
        self.file_manager = FileManager(self.PATHS, self.pywinauto_logger)
        self.file_tracker = FileTracker(self.PATHS, self.pywinauto_logger)
        self.process_manager = ProcessManager(self.pywinauto_logger)
        self.csv_generator = CSVGenerator(self.PATHS, self.delays, self.pywinauto_logger)

    def get_pqm_files(self):
        """Obtiene lista de archivos .pqm702 en el directorio de entrada"""
        return self.file_manager.get_pqm_files()

    def obtener_estadisticas_procesados(self):
        """Obtiene estadísticas de archivos procesados con la nueva estructura"""
        return self.file_tracker.get_processing_statistics()

    def ya_ha_sido_procesado(self, file_path):
        """Verifica si un archivo ya ha sido procesado anteriormente"""
        return self.file_tracker.is_already_processed(file_path)

    def registrar_archivo_procesado(self, file_path, resultado_exitoso=True, csv_path=None, 
                                  processing_time=None, error_message=None, additional_info=None):
        """Registra un archivo como procesado con información detallada"""
        return self.file_tracker.register_processed_file(
            file_path, resultado_exitoso, csv_path, processing_time, error_message, additional_info
        )

    def close_sonel_analysis_force(self):
        """Cierra todos los procesos relacionados con Sonel Analysis de forma forzada"""
        return self.process_manager.close_sonel_analysis_force()

    def ejecutar_extraccion_archivo(self, archivo_pqm):
        """Ejecuta el flujo completo para un archivo específico"""
        nombre_archivo = os.path.basename(archivo_pqm)
        csv_path_generado = None
        proceso_exitoso = False
        error_message = None
        start_time = datetime.now()

        fallos_suaves = 0
        MAX_FALLOS = 2
        
        try:
            self.pywinauto_logger.info(f"\n🎯 Procesando: {nombre_archivo}")
            
            try:
                # FASE 1: Vista inicial
                self.pywinauto_logger.info("--- FASE 1: VISTA INICIAL ---")
                extractor_inicial = SonelAnalisisInicial(archivo_pqm, self.PATHS['sonel_exe_path'])
                
                if not extractor_inicial.conectar():
                    self.pywinauto_logger.error("❌ Error conectando vista inicial")
                    return False
                
                if not extractor_inicial.navegar_configuracion():
                    self.pywinauto_logger.error("❌ Error navegando configuración")
                    return False
                
                if not extractor_inicial.ejecutar_analisis():
                    self.pywinauto_logger.error("❌ Error ejecutando análisis")
                    return False
                
            except Exception as e:
                self.pywinauto_logger.warning(f"⚠️ Error en fase inicial, pero continuando: {e}")
                self.pywinauto_logger.error(traceback.format_exc())
                proceso_exitoso = False
                error_message = str(e)
                return False

            # Ejecutar extracciones en configuración - MANEJO DE ERRORES MEJORADO
            try:
                # FASE 2: Vista configuración
                self.pywinauto_logger.info("--- FASE 2: VISTA CONFIGURACIÓN ---")
                extractor_config = SonelConfiguracion()
                app_ref = extractor_inicial.get_app_reference()
                
                if not extractor_config.conectar(app_ref):
                    self.pywinauto_logger.error("❌ Error conectando vista configuración")
                    return False

                # Ejecutar extracciones con manejo de fallos suaves
                extraction_methods = [
                    ("extraer_navegacion_lateral", extractor_config.extraer_navegacion_lateral, 1),
                    ("configurar_radiobutton", extractor_config.configurar_radiobutton, 1),
                    ("configurar_chechkboxes", extractor_config.configurar_chechkboxes, 1),
                    ("extraer_configuracion_principal_mediciones", extractor_config.extraer_configuracion_principal_mediciones, 1),
                    ("extraer_componentes_arbol_mediciones", extractor_config.extraer_componentes_arbol_mediciones, 1),
                    ("extraer_tabla_mediciones", extractor_config.extraer_tabla_mediciones, 1),
                    ("extraer_informes_graficos", extractor_config.extraer_informes_graficos, 1),
                ]

                for method_name, method, delay in extraction_methods:
                    time.sleep(delay)
                    if not method():
                        fallos_suaves += 1
                        self.pywinauto_logger.warning(f"⚠️ Falló {method_name}, continuando")
                        if fallos_suaves > MAX_FALLOS:
                            raise RuntimeError(f"Se superó el límite de fallos permitidos ({fallos_suaves}).")

            except Exception as e:
                self.pywinauto_logger.warning(f"⚠️ Error en fase de extracción, pero continuando: {e}")
                self.pywinauto_logger.error(traceback.format_exc())
                proceso_exitoso = False
                error_message = str(e)
                return False

            # FASE 3: Guardar y verificar archivo CSV - ESTA ES LA FASE CRÍTICA
            self.pywinauto_logger.info("--- FASE 3: GUARDADO Y VERIFICACIÓN CSV ---")
            
            try:
                # Usar el módulo CSV Generator
                csv_path_generado, proceso_exitoso = self.csv_generator.generate_and_verify_csv(
                    archivo_pqm, extractor_config
                )
                
                if not proceso_exitoso:
                    self.pywinauto_logger.error("❌ No se pudo verificar la creación del archivo CSV")
                        
            except Exception as e:
                self.pywinauto_logger.error(f"❌ Error crítico en fase de guardado: {e}")
                proceso_exitoso = False

            # Log del resultado final
            if proceso_exitoso:
                self.pywinauto_logger.info(f"✅ Procesamiento exitoso: {nombre_archivo}")
            else:
                self.pywinauto_logger.error(f"❌ Procesamiento falló: {nombre_archivo} - No se generó CSV válido")
            
            return proceso_exitoso
        
        except Exception as e:
            error_message = f"❌ Error crítico en procesamiento: {e}"
            self.pywinauto_logger.error(error_message)
            self.pywinauto_logger.error(traceback.format_exc())
            proceso_exitoso = False
            return False
        finally:
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            additional_info = {
                "extraccion": "completa",
                "herramienta": "pywinauto",
                "tipo_archivo": "sonel_pqm"
            }

            # Siempre registrar el resultado, incluyendo información del CSV si se generó
            self.registrar_archivo_procesado(
                file_path=archivo_pqm,
                resultado_exitoso=proceso_exitoso,
                csv_path=csv_path_generado,
                processing_time=processing_time,
                error_message=error_message,
                additional_info=additional_info
            )

    def ejecutar_extraccion_completa_dinamica(self):
        """Ejecuta el flujo completo para todos los archivos no procesados"""
        # Inicializar estructura de resultados por defecto
        resultados_globales = {
            "procesados_exitosos": 0,
            "procesados_fallidos": 0,
            "saltados": 0,
            "csvs_verificados": 0,
            "detalles": []
        }
        
        try:
            # Obtener estadísticas iniciales
            stats = self.obtener_estadisticas_procesados()
            self.pywinauto_logger.info(f"📊 Archivos ya procesados: {stats['total']}")
            if stats['total'] > 0:
                self.pywinauto_logger.info(f"📅 Último procesado: {stats['ultimo_procesado']}")
            
            # Obtener lista de archivos
            archivos_pqm = self.get_pqm_files()
            if not archivos_pqm:
                self.pywinauto_logger.warning("⚠️  No se encontraron archivos .pqm702 para procesar")
                return resultados_globales
            
            # Filtrar archivos ya procesados
            archivos_pendientes = [
                archivo for archivo in archivos_pqm 
                if not self.ya_ha_sido_procesado(archivo)
            ]
            
            # Actualizar saltados
            resultados_globales["saltados"] = len(archivos_pqm) - len(archivos_pendientes)
            
            if not archivos_pendientes:
                self.pywinauto_logger.info("✅ Todos los archivos ya han sido procesados")
                return resultados_globales
            
            self.pywinauto_logger.info(f"🔄 Archivos pendientes de procesar: {len(archivos_pendientes)}")
            
            # Procesar cada archivo
            for i, archivo in enumerate(archivos_pendientes, 1):
                nombre_archivo = os.path.basename(archivo)
                self.pywinauto_logger.info(f"\n{'='*60}")
                self.pywinauto_logger.info(f"📁 Procesando archivo {i}/{len(archivos_pendientes)}: {nombre_archivo}")
                self.pywinauto_logger.info(f"{'='*60}")
                
                # EJECUTAR PROCESAMIENTO
                try:
                    resultado = self.ejecutar_extraccion_archivo(archivo)
                    
                    # EVALUAR RESULTADO Y ACTUAR EN CONSECUENCIA
                    if resultado is True:
                        # ÉXITO - No forzar cierre
                        resultados_globales["procesados_exitosos"] += 1
                        resultados_globales["csvs_verificados"] += 1
                        resultados_globales["detalles"].append({
                            "archivo": nombre_archivo,
                            "estado": "exitoso",
                            "csv_verificado": True
                        })
                        self.pywinauto_logger.info(f"✅ Archivo procesado exitosamente: {nombre_archivo}")
                        
                        # CIERRE SUAVE - Solo cerrar procesos, no forzar
                        try:
                            time.sleep(2)  # Dar tiempo para que termine correctamente
                            self.close_sonel_analysis_force()  # Limpieza preventiva
                        except Exception as e:
                            self.pywinauto_logger.warning(f"⚠️ Error en limpieza post-éxito: {e}")
                    
                    else:
                        # FALLO - Aquí sí forzar cierre
                        resultados_globales["procesados_fallidos"] += 1
                        resultados_globales["detalles"].append({
                            "archivo": nombre_archivo,
                            "estado": "fallido",
                            "csv_verificado": False
                        })
                        self.pywinauto_logger.error(f"❌ Archivo procesado con error: {nombre_archivo}")
                        
                        # CIERRE FORZOSO por error
                        try:
                            self.close_sonel_analysis_force()
                        except Exception as e:
                            self.pywinauto_logger.warning(f"⚠️ Error en cierre forzoso: {e}")
                            
                except Exception as e:
                    # Error en procesamiento individual
                    self.pywinauto_logger.error(f"❌ Error procesando archivo {nombre_archivo}: {e}")
                    resultados_globales["procesados_fallidos"] += 1
                    resultados_globales["detalles"].append({
                        "archivo": nombre_archivo,
                        "estado": "error_excepcion",
                        "csv_verificado": False,
                        "error": str(e)
                    })
                    
                    # Limpieza tras error
                    try:
                        self.close_sonel_analysis_force()
                    except Exception as cleanup_error:
                        self.pywinauto_logger.warning(f"⚠️ Error en limpieza tras excepción: {cleanup_error}")

                # Pausa entre archivos para estabilidad
                if i < len(archivos_pendientes):
                    self.pywinauto_logger.info("⏳ Pausa entre archivos")
                    time.sleep(4)
            
            # Resumen final mejorado con más detalles
            self._log_final_summary(resultados_globales, archivos_pqm)

            # Limpieza final
            self.pywinauto_logger.info("🧹 Limpieza final de procesos Sonel Analysis")
            try:
                self.close_sonel_analysis_force()
            except Exception as e:
                self.pywinauto_logger.warning(f"⚠️ Error en limpieza final: {e}")

            # Generar resumen CSV para GUI
            csv_summary = self.get_csv_summary_for_gui()
            resultados_globales["csv_summary"] = csv_summary

            output_file = self.save_csv_summary_to_file()
            if output_file:
                print(f"Resumen guardado en: {output_file}")

            return resultados_globales
            
        except Exception as e:
            self.pywinauto_logger.error(f"❌ Error crítico en extracción completa dinámica: {e}")
            import traceback
            self.pywinauto_logger.error(traceback.format_exc())
            
            # Devolver estructura con información de error
            resultados_globales.update({
                "error_critico": True,
                "mensaje_error": str(e)
            })
            return resultados_globales

    def _log_final_summary(self, resultados_globales, archivos_pqm):
        """Log del resumen final con información detallada"""
        self.pywinauto_logger.info("\n" + "="*80)
        self.pywinauto_logger.info("📊 RESUMEN FINAL DE PROCESAMIENTO")
        self.pywinauto_logger.info(f"✅ Procesados exitosamente: {resultados_globales['procesados_exitosos']}")
        self.pywinauto_logger.info(f"📄 CSVs verificados: {resultados_globales['csvs_verificados']}")
        self.pywinauto_logger.info(f"❌ Procesados con error: {resultados_globales['procesados_fallidos']}")
        self.pywinauto_logger.info(f"⏭️  Saltados (ya procesados): {resultados_globales['saltados']}")
        self.pywinauto_logger.info(f"📁 Total de archivos: {len(archivos_pqm)}")
        
        # Calcular tasa de éxito
        total_procesados = resultados_globales['procesados_exitosos'] + resultados_globales['procesados_fallidos']
        if total_procesados > 0:
            tasa_exito = (resultados_globales['procesados_exitosos'] / total_procesados) * 100
            self.pywinauto_logger.info(f"📈 Tasa de éxito: {tasa_exito:.1f}%")
        
        # Detalles por archivo si hay errores
        if resultados_globales['procesados_fallidos'] > 0:
            self.pywinauto_logger.info("📋 Archivos con errores:")
            for detalle in resultados_globales['detalles']:
                if detalle['estado'] != 'exitoso':
                    archivo = detalle['archivo']
                    estado = detalle['estado']
                    error = detalle.get('error', '')
                    self.pywinauto_logger.info(f"   ❌ {archivo}: {estado} {error}")
        
        self.pywinauto_logger.info("="*80)
        
    def get_csv_summary_for_gui(self):
        """Genera un resumen completo para la GUI de CSV basado en archivos procesados"""
        try:
            # Obtener lista de archivos .pqm702 disponibles
            archivos_pqm = self.get_pqm_files()
            total_files = len(archivos_pqm)
            
            if total_files == 0:
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
            self.pywinauto_logger.error(f"❌ Error generando resumen CSV para GUI: {e}")
            return CSVSummaryUtils._get_empty_csv_summary()

    def _process_file_for_summary(self, archivo_pqm, processed_data):
        """Procesa un archivo individual para el resumen con la nueva estructura"""
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
            execution_time_seconds = CSVSummaryUtils._estimate_execution_time(file_size_bytes)
        
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
        Guarda un resumen del procesamiento CSV en un archivo JSON.
        Se apoya en get_csv_summary_for_gui para obtener los datos.
        """
        try:
            # Definir archivo de salida por defecto
            if output_file is None:
                data_dir = self.config['PATHS']['data_dir']
                output_file = os.path.join(data_dir, "resumen_csv.json")

            # Obtener resumen de CSV
            csv_summary = self.get_csv_summary_for_gui()

            # Construir estructura de salida
            summary_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat() + 'Z',
                    "etl_version": "1.0",
                    "config_file": getattr(self, 'config_file', 'config.ini')
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

            # Incluir detalle de archivos si se solicita
            if include_files_detail:
                summary_data["files_processed"] = csv_summary.get("files", [])

            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Guardar archivo JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)

            self.pywinauto_logger.info(f"Resumen CSV guardado en: {output_file}")
            self.pywinauto_logger.info(f"Tamaño del archivo: {os.path.getsize(output_file)} bytes")

            return output_file

        except Exception as e:
            self.pywinauto_logger.error(f"Error guardando resumen CSV: {e}")
            import traceback
            self.pywinauto_logger.error(traceback.format_exc())
            return None