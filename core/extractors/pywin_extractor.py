import os
import json
import time
import psutil
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
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
            'output_dir': output_dir or config['PATHS']['output_dir'],
            'export_dir': config['PATHS']['export_dir'],
            'sonel_exe_path': ruta_exe or config['PATHS']['sonel_exe_path'],
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

        self.process_start_time = None
        self.total_files_attempted = 0
        self.total_size_bytes = 0

        # Inicializar módulos
        self._init_modules()

    def _init_modules(self):
        """Inicializa los módulos modularizados"""
        self.file_manager = FileManager(self.PATHS, self.pywinauto_logger)
        self.file_tracker = FileTracker(self.PATHS, self.pywinauto_logger)
        self.process_manager = ProcessManager(self.pywinauto_logger)
        self.csv_generator = CSVGenerator(self.PATHS, self.delays, self.pywinauto_logger)

    def get_pqm_files(self):
        """
        Obtiene lista de archivos .pqm702 en el directorio de entrada
        MODIFICADO: Incluye análisis de duplicados por directorio
        """
        pqm_files = self.file_manager.get_pqm_files()
        
        if pqm_files:
            # NUEVO: Analizar duplicados por directorio
            duplicate_analysis = self.file_manager.check_duplicate_filenames_across_directories(pqm_files)
            
            self.pywinauto_logger.info("📊 Análisis de duplicados por directorio:")
            self.pywinauto_logger.info(f"   📁 Total de archivos: {duplicate_analysis['total_files']}")
            self.pywinauto_logger.info(f"   📋 Nombres únicos: {duplicate_analysis['unique_filenames']}")
            self.pywinauto_logger.info(f"   🔄 Nombres duplicados: {duplicate_analysis['duplicate_filenames']}")
            
            if duplicate_analysis['duplicate_filenames'] > 0:
                self.pywinauto_logger.info("   ✅ Cada archivo será procesado independientemente por directorio")
                self.pywinauto_logger.info("   📝 Los CSVs tendrán numeración incremental para evitar conflictos")
        
        return pqm_files

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
            # Verificar que el archivo es compatible
            if not self.file_manager.is_supported_pqm_file(archivo_pqm):
                extension = self.file_manager._get_file_extension(nombre_archivo)
                error_message = f"Extensión no soportada: {extension}"
                self.pywinauto_logger.error(f"❌ {error_message}")
                return False
            
            # Obtener información del archivo para logging
            file_info = self.file_manager.get_file_info(archivo_pqm)
            pqm_type = file_info.get('pqm_extension', 'unknown')
            
            self.pywinauto_logger.info(f"\n🎯 Procesando: {nombre_archivo} (Tipo: {pqm_type})")
            
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

            # Log del resultado final con tipo de archivo
            if proceso_exitoso:
                self.pywinauto_logger.info(f"✅ Procesamiento exitoso: {nombre_archivo} ({pqm_type})")
            else:
                self.pywinauto_logger.error(f"❌ Procesamiento falló: {nombre_archivo} ({pqm_type}) - No se generó CSV válido")
            
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

            # Incluir información del tipo de archivo en additional_info
            file_info = self.file_manager.get_file_info(archivo_pqm)
            additional_info = {
                "extraccion": "completa",
                "herramienta": "pywinauto",
                "tipo_archivo": "sonel_pqm",
                "pqm_extension": file_info.get('pqm_extension', 'unknown'),
                "file_type": file_info.get('file_type', 'UNKNOWN')
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
        self.process_start_time = datetime.now()

        # Inicializar estructura de resultados por defecto
        resultados_globales = {
            "procesados_exitosos": 0,
            "procesados_fallidos": 0,
            "saltados": 0,
            "csvs_verificados": 0,
            "detalles": [],
            "tipos_archivo": {}  # Nuevo: contador por tipo de extensión
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
                self.pywinauto_logger.warning("⚠️ No se encontraron archivos PQM para procesar")
                # ✅ ASEGURAR: Generar resumen incluso sin archivos
                summary = self._generate_extraction_summary(resultados_globales, archivos_pqm)
                self._log_extraction_summary(summary)
                
                # ✅ NUEVO: Intentar generar archivo de resumen incluso sin procesamiento
                try:
                    output_file = self.save_csv_summary_to_file()
                    if output_file:
                        self.pywinauto_logger.info(f"📄 Resumen básico guardado en: {output_file}")
                except Exception as summary_error:
                    self.pywinauto_logger.warning(f"⚠️ Error generando resumen básico: {summary_error}")
                
                return resultados_globales
            
            self.total_files_attempted = len(archivos_pqm)
            self.total_size_bytes = self._calculate_total_size(archivos_pqm)
            
            # Analizar tipos de archivos encontrados
            tipos_encontrados = {}
            for archivo in archivos_pqm:
                file_info = self.file_manager.get_file_info(archivo)
                pqm_ext = file_info.get('pqm_extension', 'unknown')
                tipos_encontrados[pqm_ext] = tipos_encontrados.get(pqm_ext, 0) + 1
            
            resultados_globales["tipos_archivo"] = tipos_encontrados
            
            # Log de tipos encontrados
            self.pywinauto_logger.info("📋 Tipos de archivo PQM encontrados:")
            for tipo, cantidad in tipos_encontrados.items():
                self.pywinauto_logger.info(f"   - {tipo}: {cantidad} archivo(s)")
            
            # Filtrar archivos ya procesados
            archivos_pendientes = [
                archivo for archivo in archivos_pqm 
                if not self.ya_ha_sido_procesado(archivo)
            ]
            
            # Actualizar saltados
            resultados_globales["saltados"] = len(archivos_pqm) - len(archivos_pendientes)
            
            if not archivos_pendientes:
                self.pywinauto_logger.info("✅ Todos los archivos ya han sido procesados")
                summary = self._generate_extraction_summary(resultados_globales, archivos_pqm)
                self._log_extraction_summary(summary)
                
                # ✅ ASEGURAR: Generar resumen con archivos ya procesados
                output_file = self.save_csv_summary_to_file()
                if output_file:
                    self.pywinauto_logger.info(f"📄 Resumen actualizado guardado en: {output_file}")
                
                return resultados_globales
            
            self.pywinauto_logger.info(f"🔄 Archivos pendientes de procesar: {len(archivos_pendientes)}")
            
            # Procesar cada archivo
            for i, archivo in enumerate(archivos_pendientes, 1):
                nombre_archivo = os.path.basename(archivo)
                file_info = self.file_manager.get_file_info(archivo)
                pqm_type = file_info.get('pqm_extension', 'unknown')
                
                self.pywinauto_logger.info(f"\n{'='*60}")
                self.pywinauto_logger.info(f"📁 Procesando archivo {i}/{len(archivos_pendientes)}: {nombre_archivo} ({pqm_type})")
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
                            "csv_verificado": True,
                            "tipo_pqm": pqm_type
                        })
                        self.pywinauto_logger.info(f"✅ Archivo procesado exitosamente: {nombre_archivo} ({pqm_type})")
                        
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
                            "csv_verificado": False,
                            "tipo_pqm": pqm_type
                        })
                        self.pywinauto_logger.error(f"❌ Archivo procesado con error: {nombre_archivo} ({pqm_type})")
                        
                        # CIERRE FORZOSO por error
                        try:
                            self.close_sonel_analysis_force()
                        except Exception as e:
                            self.pywinauto_logger.warning(f"⚠️ Error en cierre forzoso: {e}")
                            
                except Exception as e:
                    # Error en procesamiento individual
                    self.pywinauto_logger.error(f"❌ Error procesando archivo {nombre_archivo} ({pqm_type}): {e}")
                    resultados_globales["procesados_fallidos"] += 1
                    resultados_globales["detalles"].append({
                        "archivo": nombre_archivo,
                        "estado": "error_excepcion",
                        "csv_verificado": False,
                        "error": str(e),
                        "tipo_pqm": pqm_type
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
            
            # [RESTO DEL CÓDIGO PERMANECE IGUAL...]
            # Resumen final mejorado con más detalles
            self._log_final_summary(resultados_globales, archivos_pqm)

            summary = self._generate_extraction_summary(resultados_globales, archivos_pqm)
            self._log_extraction_summary(summary)

            # Limpieza final
            self.pywinauto_logger.info("🧹 Limpieza final de procesos Sonel Analysis")
            try:
                self.close_sonel_analysis_force()
            except Exception as e:
                self.pywinauto_logger.warning(f"⚠️ Error en limpieza final: {e}")

            # ✅ CRÍTICO: Generar resumen CSV para GUI - SIEMPRE
            try:
                csv_summary = self.get_csv_summary_for_gui()
                resultados_globales["csv_summary"] = csv_summary
                
                # ✅ ASEGURAR: Guardar archivo de resumen
                output_file = self.save_csv_summary_to_file()
                if output_file:
                    self.pywinauto_logger.info(f"✅ Resumen final guardado exitosamente en: {output_file}")
                    resultados_globales["resumen_archivo"] = output_file
                else:
                    self.pywinauto_logger.error("❌ No se pudo guardar el archivo de resumen")
                    
            except Exception as resumen_error:
                self.pywinauto_logger.error(f"❌ Error crítico generando resumen final: {resumen_error}")
                import traceback
                self.pywinauto_logger.error(traceback.format_exc())

            return resultados_globales
            
        except Exception as e:
            self.pywinauto_logger.error(f"❌ Error crítico en extracción completa dinámica: {e}")
            self.pywinauto_logger.error(traceback.format_exc())

            summary = self._generate_extraction_summary(resultados_globales, archivos_pqm if 'archivos_pqm' in locals() else [])
            self._log_extraction_summary(summary)
            
            # ✅ ASEGURAR: Generar resumen incluso en caso de error crítico
            try:
                output_file = self.save_csv_summary_to_file()
                if output_file:
                    self.pywinauto_logger.info(f"📄 Resumen de error guardado en: {output_file}")
                    resultados_globales["resumen_archivo"] = output_file
            except Exception as error_summary:
                self.pywinauto_logger.error(f"❌ Error guardando resumen de error: {error_summary}")
            
            # Devolver estructura con información de error
            resultados_globales.update({
                "error_critico": True,
                "mensaje_error": str(e)
            })
            return resultados_globales
        
    def _log_extraction_summary(self, summary):
        """Log del resumen de extracción estructurado"""
        self.pywinauto_logger.info("\n" + "="*80)
        self.pywinauto_logger.info("📊 RESUMEN ESTRUCTURADO DE EXTRACCIÓN CSV")
        self.pywinauto_logger.info("="*80)
        self.pywinauto_logger.info(f"📁 Archivos Procesados: {summary['processed_files']} / {summary['total_files']}")
        self.pywinauto_logger.info(f"⚠️ Advertencias: {summary['warnings']}")
        self.pywinauto_logger.info(f"❌ Errores: {summary['errors']}")
        self.pywinauto_logger.info(f"📄 CSVs Generados: {summary['csv_files_generated']}")
        self.pywinauto_logger.info(f"⏱️ Tiempo Extracción: {summary['execution_time']}")
        self.pywinauto_logger.info(f"💾 Tamaño Procesado: {summary['total_size']}")
        
        # Calcular tasa de éxito
        if summary['total_files'] > 0:
            success_rate = (summary['csv_files_generated'] / summary['total_files']) * 100
            self.pywinauto_logger.info(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        # Mostrar detalles de archivos si hay errores o advertencias
        if summary['errors'] > 0 or summary['warnings'] > 0:
            self.pywinauto_logger.info("\n📋 Detalles por archivo:")
            for file_detail in summary['files_detail']:
                if "Error" in file_detail['status'] or "Advertencia" in file_detail['status']:
                    self.pywinauto_logger.info(f"   {file_detail['status']} {file_detail['file_name']}: {file_detail['message']}")
        
        self.pywinauto_logger.info("="*80)
        
    def _generate_extraction_summary(self, resultados_globales, archivos_pqm):
        """Genera el resumen estructurado para la GUI"""
        
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
            execution_time = self._format_execution_time_win(self.process_start_time)
        else:
            execution_time = "0:00"
        
        # Formatear tamaño total
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

    def _format_execution_time_win(self, start_time, end_time=None):
        """Formatea el tiempo de ejecución"""
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
        """Genera detalles por archivo para la tabla de la GUI incluyendo tipo PQM"""
        files_detail = []
        processed_data = self.file_tracker._load_processed_files_data()
        
        for index, archivo_pqm in enumerate(archivos_pqm, 1):
            file_name = os.path.basename(archivo_pqm)
            file_stem = Path(archivo_pqm).stem
            
            # Obtener información del archivo incluyendo tipo PQM
            file_info = self.file_manager.get_file_info(archivo_pqm)
            pqm_type = file_info.get('pqm_extension', 'unknown')
            
            # Obtener tamaño del archivo
            try:
                file_size_bytes = os.path.getsize(archivo_pqm) if os.path.exists(archivo_pqm) else 0
                file_size_str = CSVSummaryUtils._format_file_size(file_size_bytes)
            except:
                file_size_str = "0 MB"
            
            # Usar nueva clave global en lugar de ruta absoluta
            file_key = self.file_tracker._generate_file_key(archivo_pqm)
            
            # Obtener información del procesamiento usando la nueva clave
            processed_info = processed_data.get(file_key, {})
            
            if file_key in processed_data:
                status = processed_info.get('status', '')
                csv_output = processed_info.get('csv_output', {})
                csv_verified = csv_output.get('verified', False)
                processing_time = processed_info.get('processing_time_seconds', 0)
                
                # Determinar estado y mensaje
                if status == "exitoso" and csv_verified:
                    status_display = f"✅ Procesado ({pqm_type})"
                    csv_output_name = csv_output.get('filename', f"{file_stem}.csv")
                    message = f"Procesado correctamente - Tipo: {pqm_type}"
                    
                    # Mostrar información adicional de ubicaciones múltiples
                    source_paths = processed_info.get('source_paths', [])
                    if len(source_paths) > 1:
                        message += f" (Visto en {len(source_paths)} ubicaciones)"
                        
                elif status == "exitoso" and not csv_verified:
                    status_display = f"⚠️ Advertencia ({pqm_type})"
                    csv_output_name = "CSV no verificado"
                    message = f"Procesado pero CSV no verificado - Tipo: {pqm_type}"
                else:
                    status_display = f"❌ Error ({pqm_type})"
                    csv_output_name = "No generado"
                    error_msg = processed_info.get('error_message', 'Error desconocido')
                    message = f"Error: {error_msg} - Tipo: {pqm_type}"
                
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
                status_display = f"⏳ Pendiente ({pqm_type})"
                csv_output_name = f"{file_stem}.csv"
                message = f"Archivo pendiente de procesamiento - Tipo: {pqm_type}"
                duration_str = "0:00"
            
            files_detail.append({
                "index": index,
                "file_name": file_name,
                "status": status_display,
                "duration": duration_str,
                "size": file_size_str,
                "csv_output": csv_output_name,
                "message": message,
                "pqm_type": pqm_type  # Nuevo campo para tipo PQM
            })
        
        return files_detail

    def _calculate_total_size(self, archivos_pqm):
        """Calcula el tamaño total de todos los archivos"""
        total_size = 0
        for archivo in archivos_pqm:
            try:
                if os.path.exists(archivo):
                    total_size += os.path.getsize(archivo)
            except Exception as e:
                self.pywinauto_logger.warning(f"⚠️ Error calculando tamaño de {archivo}: {e}")
        return total_size

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
        """
        Genera un resumen completo para la GUI de CSV basado en archivos procesados
        MODIFICADO: Solo incluye archivos que fueron realmente procesados en la ejecución actual
        """
        try:
            # Obtener lista de archivos .pqm702 disponibles
            archivos_pqm = self.get_pqm_files()
            total_files = len(archivos_pqm)
            
            if total_files == 0:
                self.pywinauto_logger.info("📄 No hay archivos PQM para procesar")
                return CSVSummaryUtils._get_empty_csv_summary()
            
            # ✅ CORREGIDO: Cargar datos de procesamiento desde JSON usando nueva estructura
            processed_data = self.file_tracker._load_processed_files_data()
            
            if not processed_data:
                self.pywinauto_logger.info("📊 No hay datos de procesamiento registrados aún")
                return CSVSummaryUtils._get_empty_csv_summary()
            
            # Inicializar contadores
            processed_files = 0
            errors = 0
            warnings = 0
            csv_files_generated = 0
            total_size_bytes = 0
            execution_times = []
            files_details = []
            
            # NUEVA LÓGICA: Solo procesar archivos que NO fueron saltados
            archivos_realmente_procesados = []
            for archivo_pqm in archivos_pqm:
                file_key = self.file_tracker._generate_file_key(archivo_pqm)
                
                # Verificar si el archivo existe en el registro Y fue procesado recientemente
                if file_key in processed_data:
                    entry = processed_data[file_key]
                    processing_date = entry.get("processing_completed", "")
                    
                    # Solo incluir archivos procesados en la sesión actual (últimas 24 horas como margen)
                    if processing_date:
                        try:
                            processing_datetime = datetime.fromisoformat(processing_date.replace('Z', '+00:00'))
                            current_session_start = self.process_start_time or (datetime.now() - timedelta(days=45))
                            
                            if processing_datetime >= current_session_start:
                                archivos_realmente_procesados.append(archivo_pqm)
                                self.pywinauto_logger.debug(f"📊 Incluido en resumen: {os.path.basename(archivo_pqm)} (procesado: {processing_date})")
                            else:
                                self.pywinauto_logger.debug(f"⏭️ Excluido del resumen: {os.path.basename(archivo_pqm)} (procesado previamente: {processing_date})")
                        except ValueError:
                            # Si hay error parseando la fecha, incluir por seguridad
                            archivos_realmente_procesados.append(archivo_pqm)
                            self.pywinauto_logger.warning(f"⚠️ Error parseando fecha para {os.path.basename(archivo_pqm)}, incluido por seguridad")
                else:
                    # Si no está en el registro, significa que es nuevo y debe ser incluido
                    archivos_realmente_procesados.append(archivo_pqm)
                    self.pywinauto_logger.debug(f"📋 Archivo nuevo incluido: {os.path.basename(archivo_pqm)}")
            
            self.pywinauto_logger.info(f"📊 Archivos para resumen CSV: {len(archivos_realmente_procesados)}/{len(archivos_pqm)} (excluidos {len(archivos_pqm) - len(archivos_realmente_procesados)} ya procesados)")
            
            # ✅ CORREGIDO: Procesar solo archivos que fueron realmente procesados
            for archivo_pqm in archivos_realmente_procesados:
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
            
            # Usar el total de archivos realmente procesados para las métricas
            total_files_for_metrics = len(archivos_realmente_procesados)
            
            # Calcular métricas derivadas
            total_execution_time = sum(execution_times) if execution_times else 0
            success_rate = (csv_files_generated / total_files_for_metrics * 100) if total_files_for_metrics > 0 else 0
            avg_speed = CSVSummaryUtils._calculate_average_speed(csv_files_generated, total_execution_time)
            
            # Formatear tiempo total
            execution_time_str = CSVSummaryUtils._format_execution_time(total_execution_time)
            
            # Formatear tamaño total
            total_size_str = CSVSummaryUtils._format_file_size(total_size_bytes)
            
            # Calcular total de registros estimado (basado en archivos exitosos)
            total_records = csv_files_generated * 3278  # Estimación promedio por archivo
            
            # ✅ NUEVO: Log de resumen generado para debugging
            self.pywinauto_logger.info(f"📊 Resumen CSV generado - Procesados: {processed_files}/{total_files_for_metrics}, CSVs: {csv_files_generated}, Errores: {errors}, Advertencias: {warnings}")
            
            return {
                "processed_files": processed_files,
                "total_files": total_files_for_metrics,
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
            import traceback
            self.pywinauto_logger.error(traceback.format_exc())
            return CSVSummaryUtils._get_empty_csv_summary()
        
    def get_extraction_summary_for_gui(self):
        """Método público para obtener el resumen desde el controlador"""
        # Si hay un proceso en curso y se ha calculado el resumen
        if hasattr(self, '_last_extraction_summary'):
            return self._last_extraction_summary
        
        # Si no, generar un resumen basado en el estado actual
        archivos_pqm = self.get_pqm_files()
        
        # Obtener estadísticas de archivos procesados
        stats = self.obtener_estadisticas_procesados()
        
        # Cargar datos detallados de procesamiento con nueva estructura
        processed_data = self.file_tracker._load_processed_files_data()
        
        # Contar archivos por estado usando las nuevas claves
        procesados_exitosos = 0
        procesados_fallidos = 0
        csvs_verificados = 0
        
        for archivo_path in archivos_pqm:
            # Usar nueva clave global en lugar de ruta absoluta
            file_key = self.file_tracker._generate_file_key(archivo_path)
            
            if file_key in processed_data:
                processed_info = processed_data[file_key]
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

    def _process_file_for_summary(self, archivo_pqm, processed_data):
        """
        Procesa un archivo individual para el resumen con información de tipo PQM
        CORREGIDO: Mejorado para detectar correctamente archivos procesados con numeración incremental
        """
        file_name = os.path.basename(archivo_pqm)
        file_stem = Path(archivo_pqm).stem
        source_directory = os.path.basename(os.path.dirname(archivo_pqm))
        
        # Obtener información del archivo incluyendo tipo PQM
        file_info = self.file_manager.get_file_info(archivo_pqm)
        pqm_type = file_info.get('pqm_extension', 'unknown')
        
        # Verificar si existe físicamente
        file_exists = os.path.exists(archivo_pqm)
        file_size_bytes = os.path.getsize(archivo_pqm) if file_exists else 0
        
        # Usar la nueva función de generación de claves globales que incluye directorio
        file_key = self.file_tracker._generate_file_key(archivo_pqm)
        
        # NUEVA LÓGICA: Buscar información de otros archivos con el mismo nombre en diferentes directorios
        same_name_different_dirs = []
        matching_entries = []  # NUEVO: Para archivos que corresponden al mismo archivo
        
        for key, info in processed_data.items():
            if info.get('filename') == file_name:
                if key != file_key:
                    other_dir = "desconocido"
                    if info.get('source_paths'):
                        other_dir = os.path.basename(os.path.dirname(info['source_paths'][0]))
                    if other_dir != source_directory:
                        same_name_different_dirs.append((key, info, other_dir))
                    else:
                        # CRÍTICO: Archivo con mismo nombre y directorio (posible match exacto)
                        matching_entries.append((key, info))
        
        # CORRECCIÓN PRINCIPAL: Verificar si existe un registro que corresponda a este archivo
        processed_info = None
        actual_key = file_key
        
        # 1. Buscar por clave exacta
        if file_key in processed_data:
            processed_info = processed_data[file_key]
            actual_key = file_key
        
        # 2. NUEVO: Buscar por archivos que puedan corresponder al mismo archivo físico
        elif matching_entries:
            # Verificar si algún archivo de matching_entries corresponde al mismo archivo físico
            for match_key, match_info in matching_entries:
                source_paths = match_info.get('source_paths', [])
                current_path = os.path.abspath(archivo_pqm)
                
                # Verificar si la ruta actual está en las rutas conocidas
                for known_path in source_paths:
                    if os.path.abspath(known_path) == current_path:
                        processed_info = match_info
                        actual_key = match_key
                        self.pywinauto_logger.debug(f"🎯 Archivo encontrado por ruta física: {file_name}")
                        break
                
                if processed_info:
                    break
        
        # 3. NUEVO: Buscar archivos procesados exitosamente del mismo nombre en otros directorios
        #    y verificar si generaron un CSV que coincida con este archivo
        elif same_name_different_dirs:
            for other_key, other_info, other_dir in same_name_different_dirs:
                if (other_info.get('status') == 'exitoso' and 
                    other_info.get('csv_output', {}).get('verified', False)):
                    
                    # Verificar si el CSV generado corresponde a este archivo
                    csv_filename = other_info.get('csv_output', {}).get('filename', '')
                    if csv_filename and self._csv_corresponds_to_file(csv_filename, file_stem):
                        processed_info = other_info.copy()  # Copiar la información
                        actual_key = other_key
                        
                        # MODIFICAR: Actualizar información específica para este directorio
                        processed_info['message_modifier'] = f"procesado_desde_otro_directorio:{other_dir}"
                        
                        self.pywinauto_logger.info(f"📂 Archivo {file_name} en '{source_directory}' corresponde a procesamiento exitoso en '{other_dir}'")
                        break
        
        # Determinar estado y mensaje
        if processed_info:
            processed = True
            status = processed_info.get('status', '')
            csv_output = processed_info.get('csv_output', {})
            csv_verified = csv_output.get('verified', False)
            
            # CORRECCIÓN CRÍTICA: Usar tiempo real del procesamiento
            execution_time_seconds = processed_info.get('processing_time_seconds', 0)
            
            # NUEVA LÓGICA: Verificar físicamente el CSV numerado si es necesario
            csv_filename = csv_output.get('filename', f"{file_stem}.csv")
            
            # Verificar físicamente si existe el CSV (incluyendo versiones numeradas)
            csv_exists_physically = self._verify_csv_exists_physically(file_stem, csv_filename)
            
            # CORRECCIÓN: Determinar estado correcto
            is_from_other_directory = 'message_modifier' in processed_info
            
            if status == "exitoso" and (csv_verified or csv_exists_physically):
                status_display = f"✅ Exitoso ({pqm_type})"
                status_type = "success"
                
                if is_from_other_directory:
                    other_dir = processed_info['message_modifier'].split(':')[1]
                    message = f"Procesado correctamente - Directorio actual: {source_directory}, Procesado desde: {other_dir}, Tipo: {pqm_type}"
                else:
                    message = f"Procesado correctamente - Directorio: {source_directory}, Tipo: {pqm_type}"
                
                # Si el CSV fue verificado físicamente pero no marcado como verified, actualizar
                if not csv_verified and csv_exists_physically:
                    message += " (CSV verificado físicamente)"
                    self.pywinauto_logger.info(f"🔧 CSV verificado físicamente para {file_name}: {csv_filename}")
                    
            elif status == "exitoso" and not csv_verified and not csv_exists_physically:
                status_display = f"⚠️ Advertencia ({pqm_type})"
                status_type = "warning"
                message = f"Procesado pero CSV no verificado - Directorio: {source_directory}, Tipo: {pqm_type}"
            else:
                status_display = f"❌ Error ({pqm_type})"
                status_type = "error"
                error_msg = processed_info.get('error_message', 'Error desconocido')
                message = f"Error: {error_msg} - Directorio: {source_directory}, Tipo: {pqm_type}"
            
            # NUEVA INFORMACIÓN: Mostrar información sobre archivos con mismo nombre en otros directorios
            if same_name_different_dirs and not is_from_other_directory:
                other_dirs = [other_dir for _, _, other_dir in same_name_different_dirs]
                message += f" (También procesado en: {', '.join(other_dirs)})"
                
        else:
            # Archivo no procesado
            processed = False
            status_display = f"⏳ Pendiente ({pqm_type})"
            status_type = "pending"
            message = f"Archivo pendiente - Directorio: {source_directory}, Tipo: {pqm_type}"
            
            # CORRECCIÓN: Usar estimación basada en tamaño para archivos pendientes
            execution_time_seconds = CSVSummaryUtils._estimate_execution_time(file_size_bytes)
            
            # Mostrar si existe en otros directorios
            if same_name_different_dirs:
                processed_dirs = []
                for _, info, other_dir in same_name_different_dirs:
                    if info.get('status') == 'exitoso':
                        processed_dirs.append(other_dir)
                if processed_dirs:
                    message += f" (Ya procesado en: {', '.join(processed_dirs)})"
        
        # CORRECCIÓN: Mejorar detección del nombre CSV esperado con numeración
        if processed_info:
            csv_filename = self._get_actual_csv_filename(file_stem, processed_info)
        else:
            csv_filename = f"{file_stem}.csv"
        
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
            "pqm_type": pqm_type,
            "source_directory": source_directory,
            "same_name_other_dirs": len(same_name_different_dirs)
        }
    
    def _verify_csv_exists_physically(self, file_stem, reported_csv_filename):
        """
        Verifica físicamente si existe un archivo CSV para el archivo dado, 
        incluyendo versiones con numeración incremental.
        
        Args:
            file_stem (str): Nombre base del archivo sin extensión
            reported_csv_filename (str): Nombre del CSV reportado en el registro
            
        Returns:
            bool: True si se encuentra físicamente el archivo CSV
        """
        try:
            output_dir = self.PATHS['output_dir']
            
            # 1. Verificar el nombre reportado directamente
            reported_path = os.path.join(output_dir, reported_csv_filename)
            if os.path.exists(reported_path):
                self.pywinauto_logger.debug(f"CSV encontrado con nombre reportado: {reported_csv_filename}")
                return True
            
            # 2. Verificar nombre base sin numeración
            base_csv_name = f"{file_stem}.csv"
            base_path = os.path.join(output_dir, base_csv_name)
            if os.path.exists(base_path):
                self.pywinauto_logger.debug(f"CSV encontrado con nombre base: {base_csv_name}")
                return True
            
            # 3. Buscar versiones con numeración incremental (formato usado por el sistema)
            numbered_patterns = [
                f"{file_stem}.csv",  # Original
                f"*_{file_stem}.csv",  # Patrón numérico: 1_nombre.csv, 2_nombre.csv, etc.
            ]
            
            import glob
            for pattern in numbered_patterns:
                pattern_path = os.path.join(output_dir, pattern)
                matching_files = glob.glob(pattern_path)
                if matching_files:
                    found_file = os.path.basename(matching_files[0])
                    self.pywinauto_logger.debug(f"CSV encontrado con patrón numerado: {found_file}")
                    return True
            
            # 4. Búsqueda manual en el directorio por si los patrones fallan
            try:
                for filename in os.listdir(output_dir):
                    if filename.endswith('.csv'):
                        # Verificar si el nombre contiene el file_stem
                        if file_stem in filename:
                            # Verificar patrones específicos de numeración
                            import re
                            
                            # Patrón: número_nombre.csv
                            if re.match(rf'^\d+_{re.escape(file_stem)}\.csv$', filename):
                                self.pywinauto_logger.debug(f"CSV encontrado con numeración manual: {filename}")
                                return True
                            
                            # Patrón: nombre.csv (exacto)
                            if filename == f"{file_stem}.csv":
                                self.pywinauto_logger.debug(f"CSV encontrado exacto: {filename}")
                                return True
            
            except OSError as e:
                self.pywinauto_logger.warning(f"Error listando directorio {output_dir}: {e}")
            
            return False
            
        except Exception as e:
            self.pywinauto_logger.warning(f"Error verificando existencia física de CSV para {file_stem}: {e}")
            return False

    def _get_actual_csv_filename(self, file_stem, processed_info):
        """
        Obtiene el nombre real del archivo CSV, priorizando el que existe físicamente.
        
        Args:
            file_stem (str): Nombre base del archivo sin extensión
            processed_info (dict): Información del procesamiento del archivo
            
        Returns:
            str: Nombre real del archivo CSV
        """
        try:
            # 1. Intentar usar el nombre registrado
            csv_output = processed_info.get('csv_output', {})
            registered_filename = csv_output.get('filename', f"{file_stem}.csv")
            
            # 2. Verificar si el nombre registrado existe físicamente
            output_dir = self.PATHS['output_dir']
            registered_path = os.path.join(output_dir, registered_filename)
            
            if os.path.exists(registered_path):
                return registered_filename
            
            # 3. Buscar versiones numeradas existentes
            import glob
            import re
            
            # Patrón para archivos numerados
            numbered_pattern = os.path.join(output_dir, f"*_{file_stem}.csv")
            numbered_files = glob.glob(numbered_pattern)
            
            if numbered_files:
                # Tomar el primer archivo encontrado y extraer solo el nombre
                found_file = os.path.basename(numbered_files[0])
                self.pywinauto_logger.debug(f"CSV numerado encontrado para {file_stem}: {found_file}")
                return found_file
            
            # 4. Buscar archivo base
            base_filename = f"{file_stem}.csv"
            base_path = os.path.join(output_dir, base_filename)
            
            if os.path.exists(base_path):
                return base_filename
            
            # 5. Búsqueda manual más exhaustiva
            try:
                for filename in os.listdir(output_dir):
                    if filename.endswith('.csv') and file_stem in filename:
                        # Verificar patrones comunes
                        if re.match(rf'^\d+_{re.escape(file_stem)}\.csv$', filename):
                            self.pywinauto_logger.debug(f"CSV encontrado manualmente: {filename}")
                            return filename
            except OSError:
                pass
            
            # 6. Fallback: usar nombre registrado o base
            return registered_filename if registered_filename != f"{file_stem}.csv" else f"{file_stem}.csv"
            
        except Exception as e:
            self.pywinauto_logger.warning(f"Error obteniendo nombre real del CSV para {file_stem}: {e}")
            return f"{file_stem}.csv"

    def _csv_corresponds_to_file(self, csv_filename, file_stem):
        """
        Verifica si un archivo CSV corresponde a un archivo PQM dado, 
        considerando numeración incremental.
        
        Args:
            csv_filename (str): Nombre del archivo CSV
            file_stem (str): Nombre base del archivo PQM sin extensión
            
        Returns:
            bool: True si el CSV corresponde al archivo
        """
        import re
        
        # Remover extensión del CSV
        csv_stem = csv_filename.replace('.csv', '')
        
        # 1. Verificación exacta (sin numeración)
        if csv_stem == file_stem:
            return True
        
        # 2. Verificar patrón de numeración: "número_nombre"
        pattern_numbered = rf'^(\d+)_{re.escape(file_stem)}$'
        if re.match(pattern_numbered, csv_stem):
            return True
        
        # 3. Verificar patrón con espacios: "número. nombre"
        pattern_spaced = rf'^(\d+)\.\s*{re.escape(file_stem)}$'
        if re.match(pattern_spaced, csv_stem):
            return True
        
        # 4. Verificar patrón con paréntesis: "(número) nombre"
        pattern_parenthesis = rf'^\((\d+)\)\s*{re.escape(file_stem)}$'
        if re.match(pattern_parenthesis, csv_stem):
            return True
        
        # 5. Verificación por contenido de nombre (para casos especiales)
        # Normalizar nombres removiendo caracteres especiales para comparación
        csv_normalized = re.sub(r'[^\w\s]', '', csv_stem).lower()
        file_normalized = re.sub(r'[^\w\s]', '', file_stem).lower()
        
        # Si el nombre normalizado del archivo está contenido en el CSV
        if file_normalized in csv_normalized and len(file_normalized) > 5:
            return True
        
        return False

    def save_csv_summary_to_file(self, output_file=None, include_files_detail=True):
        """
        Guarda un resumen del procesamiento CSV en un archivo JSON de forma consolidada.
        MODIFICADO: Solo incluye archivos procesados en la ejecución actual, no archivos saltados
        """
        try:
            # Definir archivo de salida usando export_dir correctamente
            if output_file is None:
                export_dir = self.PATHS.get('export_dir')
                if not export_dir:
                    export_dir = self.PATHS.get('export_dir', os.path.join(os.getcwd(), 'export'))
                
                os.makedirs(export_dir, exist_ok=True)
                output_file = os.path.join(export_dir, "resumen_csv.json")

            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # ✅ CAMBIO CRÍTICO: Usar el resumen filtrado que ya excluye archivos saltados
            csv_summary_actual = self.get_csv_summary_for_gui()
            
            if not csv_summary_actual:
                self.pywinauto_logger.warning("⚠️ No se pudo generar el resumen CSV")
                return None

            # **NUEVA LÓGICA MEJORADA: Cargar datos existentes si el archivo ya existe**
            existing_data = {}
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    self.pywinauto_logger.info(f"📊 Cargando datos existentes desde: {output_file}")
                except Exception as e:
                    self.pywinauto_logger.warning(f"⚠️ Error cargando datos existentes: {e}. Creando archivo nuevo.")
                    existing_data = {}

            # **NUEVA LÓGICA: Consolidar SOLO archivos procesados en la ejecución actual**
            consolidated_files = {}
            
            # 1. Cargar archivos existentes (de ejecuciones anteriores)
            existing_files = existing_data.get("files_processed", [])
            for file_data in existing_files:
                if isinstance(file_data, dict) and 'filename' in file_data:
                    filename = file_data['filename']
                    source_dir = file_data.get('source_directory', 'directorio_desconocido')
                    processing_date = file_data.get('processing_date', '')
                    
                    # NUEVA CLAVE: filename + directorio + fecha para evitar duplicados reales
                    file_key = f"{filename}#{source_dir}#{processing_date[:10] if processing_date else 'unknown'}"
                    
                    # Verificar si este archivo fue procesado en la sesión actual
                    current_session_start = self.process_start_time or (datetime.now() - timedelta(hours=24))
                    
                    should_keep_existing = True
                    if processing_date:
                        try:
                            processing_datetime = datetime.fromisoformat(processing_date.replace('Z', '+00:00'))
                            # Si fue procesado en la sesión actual, será reemplazado por los datos nuevos
                            if processing_datetime >= current_session_start:
                                should_keep_existing = False
                                self.pywinauto_logger.debug(f"🔄 Archivo será actualizado: {filename} (procesado en sesión actual)")
                        except ValueError:
                            pass  # Mantener archivo si hay error parseando fecha
                    
                    if should_keep_existing:
                        consolidated_files[file_key] = file_data
                        self.pywinauto_logger.debug(f"📋 Archivo mantenido de sesión anterior: {filename}")

            # 2. Agregar/actualizar SOLO archivos del procesamiento actual (excluye saltados)
            current_input_dir = os.path.basename(self.PATHS.get('input_dir', 'directorio_actual'))
            current_files = csv_summary_actual.get("files", [])  # Ya filtrado por get_csv_summary_for_gui()
            current_date = datetime.now().isoformat()
            
            self.pywinauto_logger.info(f"📊 Archivos de sesión actual para consolidar: {len(current_files)}")
            
            for file_data in current_files:
                if isinstance(file_data, dict) and 'filename' in file_data:
                    filename = file_data['filename']
                    # Agregar información del directorio de origen
                    file_data['source_directory'] = current_input_dir
                    file_data['processing_date'] = current_date
                    
                    # NUEVA CLAVE con información más específica
                    file_key = f"{filename}#{current_input_dir}#{current_date[:10]}"
                    
                    # Agregar archivo procesado en sesión actual
                    consolidated_files[file_key] = file_data
                    self.pywinauto_logger.debug(f"📝 Archivo de sesión actual consolidado: {filename}")

            # **NUEVA LÓGICA: Calcular métricas consolidadas correctamente**
            total_files = len(consolidated_files)
            processed_files = sum(1 for f in consolidated_files.values() if f.get('processed', False))
            errors = sum(1 for f in consolidated_files.values() if f.get('status_type') == 'error')
            warnings = sum(1 for f in consolidated_files.values() if f.get('status_type') == 'warning')
            csv_files_generated = sum(1 for f in consolidated_files.values() if f.get('status_type') == 'success')
            
            # Calcular tiempo total y tamaño total
            total_execution_time = sum(f.get('execution_time_seconds', 0) for f in consolidated_files.values())
            total_size_bytes = sum(f.get('size_bytes', 0) for f in consolidated_files.values())
            
            # Formatear métricas
            execution_time_str = self._format_execution_time_win(
                datetime.now() - timedelta(seconds=total_execution_time)
            ) if total_execution_time > 0 else "0:00"
            
            total_size_str = CSVSummaryUtils._format_file_size(total_size_bytes)
            success_rate = (csv_files_generated / total_files * 100) if total_files > 0 else 0
            avg_speed = CSVSummaryUtils._calculate_average_speed(csv_files_generated, total_execution_time)
            total_records = csv_files_generated * 3278  # Estimación promedio por archivo

            # NUEVA ESTRUCTURA: Información de consolidación mejorada
            unique_directories = list(set(f.get('source_directory', '') for f in consolidated_files.values()))
            unique_filenames = list(set(f.get('filename', '') for f in consolidated_files.values()))
            
            # Detectar archivos con el mismo nombre en diferentes directorios
            filename_directory_map = {}
            for file_data in consolidated_files.values():
                filename = file_data.get('filename', '')
                source_dir = file_data.get('source_directory', '')
                if filename not in filename_directory_map:
                    filename_directory_map[filename] = []
                filename_directory_map[filename].append(source_dir)
            
            # Contar archivos duplicados (mismo nombre, diferentes directorios)
            duplicate_files = {name: dirs for name, dirs in filename_directory_map.items() if len(dirs) > 1}

            summary_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "etl_version": "1.3",  # Actualizar versión por cambios de directorio
                    "config_file": getattr(self, 'config_file', 'config.ini'),
                    "registry_file": self.file_tracker.processed_files_json,
                    "consolidation_info": {
                        "total_directories_processed": len(unique_directories),
                        "unique_filenames": len(unique_filenames),
                        "total_file_directory_combinations": len(consolidated_files),
                        "duplicate_files_across_directories": len(duplicate_files),
                        "current_directory": current_input_dir,
                        "last_consolidation": datetime.now().isoformat(),
                        "directories_processed": unique_directories,
                        "duplicate_files_detail": {
                            name: dirs for name, dirs in list(duplicate_files.items())[:5]  # Primeros 5
                        } if duplicate_files else {}
                    }
                },
                "csv_summary": {
                    "processed_files": processed_files,
                    "total_files": total_files,
                    "errors": errors,
                    "warnings": warnings,
                    "csv_files_generated": csv_files_generated,
                    "execution_time": execution_time_str,
                    "avg_speed": avg_speed,
                    "total_size": total_size_str,
                    "success_rate": success_rate,
                    "total_records": total_records
                },
                "files_processed": list(consolidated_files.values()) if include_files_detail else []
            }

            # Guardar archivo JSON consolidado
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2, ensure_ascii=False)
            except Exception as write_error:
                self.pywinauto_logger.error(f"❌ Error escribiendo archivo JSON: {write_error}")
                return None

            # Verificar que el archivo se creó correctamente
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                self.pywinauto_logger.info(f"✅ Resumen CSV consolidado guardado en: {output_file}")
                self.pywinauto_logger.info(f"📄 Tamaño del archivo: {file_size} bytes")
                self.pywinauto_logger.info(f"📊 Archivos consolidados: {total_files} combinaciones archivo-directorio")
                self.pywinauto_logger.info(f"📁 Directorios procesados: {len(unique_directories)}")
                self.pywinauto_logger.info(f"📋 Nombres únicos: {len(unique_filenames)}")
                
                if duplicate_files:
                    self.pywinauto_logger.info(f"🔄 Archivos duplicados en diferentes directorios: {len(duplicate_files)}")
                    for filename, directories in list(duplicate_files.items())[:3]:  # Mostrar solo 3
                        self.pywinauto_logger.info(f"   📂 '{filename}' en: {', '.join(directories)}")
                
                # Log específico sobre exclusiones
                total_archivos_disponibles = len(self.get_pqm_files()) if hasattr(self, 'get_pqm_files') else 0
                archivos_excluidos = total_archivos_disponibles - len(current_files)
                if archivos_excluidos > 0:
                    self.pywinauto_logger.info(f"⏭️ Archivos excluidos del resumen (ya procesados): {archivos_excluidos}")
                
                # Validar contenido del archivo
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        verification_data = json.load(f)
                        files_count = len(verification_data.get("files_processed", []))
                        directories_count = verification_data.get("metadata", {}).get("consolidation_info", {}).get("total_directories_processed", 0)
                        self.pywinauto_logger.info(f"📊 Archivo verificado - {files_count} archivos de {directories_count} directorios")
                except Exception as verify_error:
                    self.pywinauto_logger.warning(f"⚠️ Error verificando archivo guardado: {verify_error}")
                
                return output_file
            else:
                self.pywinauto_logger.error(f"❌ El archivo no se creó correctamente: {output_file}")
                return None

        except Exception as e:
            self.pywinauto_logger.error(f"❌ Error crítico guardando resumen CSV consolidado: {e}")
            import traceback
            self.pywinauto_logger.error(traceback.format_exc())
            return None