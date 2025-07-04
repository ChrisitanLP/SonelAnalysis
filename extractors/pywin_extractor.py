import os
import re
import json
import time
import psutil
import logging
import traceback
import pyautogui
import pyperclip
from time import sleep
from pathlib import Path
from datetime import datetime
from pywinauto.mouse import move
from pywinauto import Application
from config.logger import get_logger
from pywinauto.keyboard import send_keys
from pyautogui import click, moveTo, position
from pywinauto import Desktop, mouse, findwindows
from pynput.mouse import Button, Listener as MouseListener
from pywinauto.controls.uia_controls import EditWrapper, ButtonWrapper

# Imports de los nuevos módulos
from extractors.pyautowin_extractor.w_analysis import SonelAnalisisInicial
from extractors.pyautowin_extractor.w_configuration import SonelConfiguracion

from config.settings import get_full_config, create_directories, PATHS, LOGGING_CONFIG, GUI_DELAYS

class SonelExtractorCompleto:
    """Coordinador principal que maneja ambas clases con procesamiento dinámico"""
    
    def __init__(self, input_dir=None, output_dir=None, ruta_exe=None):
        # Configuración de rutas
        config = get_full_config()

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
        
        # Archivo de seguimiento de procesados
        self.processed_files_json = os.path.join(
            self.PATHS['process_file_dir'],
            'procesados.json'
        )

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

    def _verify_file_creation(self, csv_path, max_attempts=5):
        """
        Verifica la creación del archivo CSV
        
        Args:
            csv_path: Ruta del archivo a verificar
            max_attempts: Número máximo de intentos de verificación
            
        Returns:
            bool: True si el archivo fue creado exitosamente
        """
        verification_attempts = 0
        
        self.pywinauto_logger.info(f"🔍 Iniciando verificación de archivo: {os.path.basename(csv_path)}")
        
        while verification_attempts < max_attempts:
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                if file_size > 100:  # Archivo debe tener contenido mínimo
                    self.pywinauto_logger.info(f"✅ Archivo verificado exitosamente: {os.path.basename(csv_path)} ({file_size} bytes)")
                    return True
                else:
                    self.pywinauto_logger.warning(f"⚠️ Archivo existe pero muy pequeño ({file_size} bytes)")
            
            verification_attempts += 1
            time.sleep(self.delays['file_verification'])
            self.pywinauto_logger.info(f"🔄 Verificación {verification_attempts}/{max_attempts} - Buscando: {os.path.basename(csv_path)}")
        
        self.pywinauto_logger.error(f"❌ Archivo no pudo ser verificado después de {max_attempts} intentos: {os.path.basename(csv_path)}")
        return False

    def _get_expected_csv_name(self, archivo_pqm):
        """
        Genera el nombre esperado del archivo CSV basado en el archivo PQM original
        
        Args:
            archivo_pqm: Ruta del archivo .pqm702
            
        Returns:
            str: Nombre completo esperado del archivo CSV
        """
        # Obtener el nombre completo del archivo sin extensión
        file_stem = Path(archivo_pqm).stem
        # Crear nombre CSV con sufijo _procesado
        csv_name = f"{file_stem}.csv"
        return os.path.join(self.PATHS['output_dir'], csv_name)

    def _find_generated_csv(self, expected_csv_path, archivo_pqm):
        """
        Busca el archivo CSV generado, considerando posibles variaciones en el nombre
        
        Args:
            expected_csv_path: Ruta esperada del archivo CSV
            archivo_pqm: Archivo PQM original para extraer información
            
        Returns:
            str|None: Ruta del archivo CSV encontrado o None si no se encuentra
        """
        # Primero verificar si existe con el nombre esperado
        if os.path.exists(expected_csv_path):
            return expected_csv_path
        
        # Extraer información del archivo original
        original_name = os.path.basename(archivo_pqm)
        file_stem = Path(archivo_pqm).stem
        
        # Buscar posibles variaciones del nombre
        possible_names = [
            f"{file_stem}.csv",
            f"{file_stem}_procesado.csv",
        ]
        
        # Si el nombre tiene números al inicio, buscar también solo con esos números
        import re
        match = re.match(r'^(\d+)', file_stem)
        if match:
            number_prefix = match.group(1)
            possible_names.extend([
                f"{number_prefix}.csv",
                f"{number_prefix}_procesado.csv"
            ])
        
        # Buscar en el directorio de salida
        for possible_name in possible_names:
            possible_path = os.path.join(self.PATHS['output_dir'], possible_name)
            if os.path.exists(possible_path):
                self.pywinauto_logger.info(f"📂 Archivo CSV encontrado con nombre alternativo: {possible_name}")
                return possible_path
        
        # Buscar cualquier archivo CSV creado recientemente
        try:
            csv_files = [f for f in os.listdir(self.PATHS['output_dir']) if f.endswith('.csv')]
            if csv_files:
                # Ordenar por fecha de modificación (más reciente primero)
                csv_files_with_time = []
                for csv_file in csv_files:
                    csv_path = os.path.join(self.PATHS['output_dir'], csv_file)
                    mtime = os.path.getmtime(csv_path)
                    csv_files_with_time.append((csv_file, mtime, csv_path))
                
                csv_files_with_time.sort(key=lambda x: x[1], reverse=True)
                
                # Verificar si el archivo más reciente fue creado en los últimos 5 minutos
                if csv_files_with_time:
                    most_recent = csv_files_with_time[0]
                    time_diff = time.time() - most_recent[1]
                    
                    if time_diff < 300:  # 5 minutos
                        self.pywinauto_logger.info(f"📂 Posible archivo CSV encontrado (creado recientemente): {most_recent[0]}")
                        return most_recent[2]
        
        except Exception as e:
            self.pywinauto_logger.warning(f"⚠️ Error buscando archivos CSV alternativos: {e}")
        
        return None

    def get_pqm_files(self):
        """
        Obtiene lista de archivos .pqm702 en el directorio de entrada
        
        Returns:
            Lista de rutas de archivos .pqm702
        """
        try:
            if not os.path.exists(self.PATHS['input_dir']):
                self.pywinauto_logger.error(f"❌ Directorio de entrada no existe: {self.PATHS['input_dir']}")
                return []
            
            pqm_files = []
            for file in os.listdir(self.PATHS['input_dir']):
                if file.lower().endswith('.pqm702'):
                    ruta_normalizada = os.path.join(self.PATHS['input_dir'], file).replace("\\", "/")
                    pqm_files.append(ruta_normalizada)
            
            # Ordenar archivos para procesamiento consistente
            pqm_files.sort()
            
            self.pywinauto_logger.info(f"📋 Encontrados {len(pqm_files)} archivos .pqm702 en {self.PATHS['input_dir']}")
            for i, file in enumerate(pqm_files, 1):
                self.pywinauto_logger.info(f"   {i}. {os.path.basename(file)}")
            
            return pqm_files
            
        except Exception as e:
            self.pywinauto_logger.error(f"Error obteniendo archivos .pqm702: {e}")
            return []

    def obtener_estadisticas_procesados(self):
        """
        Obtiene estadísticas de archivos procesados
        
        Returns:
            dict: Estadísticas de procesamiento
        """
        try:
            if not os.path.exists(self.processed_files_json):
                return {"total": 0, "archivos": []}
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            return {
                "total": len(processed_data),
                "archivos": list(processed_data.keys()),
                "ultimo_procesado": max(
                    processed_data.values(), 
                    key=lambda x: x.get('fecha', ''), 
                    default={}
                ).get('fecha', 'N/A') if processed_data else 'N/A'
            }
            
        except Exception as e:
            self.pywinauto_logger.error(f"Error obteniendo estadísticas: {e}")
            return {"total": 0, "archivos": [], "error": str(e)}

    def ya_ha_sido_procesado(self, file_path):
        """
        Verifica si un archivo ya ha sido procesado anteriormente
        
        Args:
            file_path (str): Ruta completa del archivo a verificar
            
        Returns:
            bool: True si ya fue procesado, False si no
        """
        try:
            # Obtener nombre base del archivo sin ruta
            file_name = os.path.basename(file_path)
            
            # Verificar si existe el archivo JSON
            if not os.path.exists(self.processed_files_json):
                return False
            
            # Leer archivo JSON
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            # Verificar si el archivo está registrado
            if file_name in processed_data:
                entry = processed_data[file_name]

                # Verificar si fue exitoso
                if entry.get("exitoso", False):
                    self.pywinauto_logger.info(f"⏭️  Saltando {file_name} (ya procesado exitosamente)")
                    return True
                else:
                    self.pywinauto_logger.info(f"🔁 Reintentando procesamiento de {file_name} (procesamiento anterior fallido)")
                    return False
            else:
                return False
            
        except json.JSONDecodeError as e:
            self.pywinauto_logger.warning(f"Error leyendo JSON de procesados: {e}")
            return False
        except Exception as e:
            self.pywinauto_logger.error(f"Error verificando archivo procesado {file_path}: {e}")
            return False

    def registrar_archivo_procesado(self, file_path, resultado_exitoso=True, csv_path=None):
        """
        Registra un archivo como procesado exitosamente
        
        Args:
            file_path (str): Ruta completa del archivo procesado
            resultado_exitoso (bool): Si el procesamiento fue exitoso
            csv_path (str): Ruta del archivo CSV generado (opcional)
        """
        try:
            # Obtener información del archivo
            file_name = os.path.basename(file_path)
            file_stem = Path(file_path).stem
            file_ext = Path(file_path).suffix.lstrip('.')
            
            # Cargar datos existentes o crear estructura vacía
            processed_data = {}
            if os.path.exists(self.processed_files_json):
                try:
                    with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                        processed_data = json.load(f)
                except json.JSONDecodeError:
                    self.pywinauto_logger.warning("Archivo JSON corrupto, creando uno nuevo")
                    processed_data = {}
            
            # Crear registro del archivo procesado
            registro = {
                "nombre": file_stem,
                "extension": file_ext,
                "fecha": datetime.now().isoformat(),
                "exitoso": resultado_exitoso
            }
            
            # Agregar información del CSV si está disponible
            if csv_path and os.path.exists(csv_path):
                registro["csv_generado"] = os.path.basename(csv_path)
                registro["csv_size"] = os.path.getsize(csv_path)
                registro["csv_verificado"] = True
            else:
                registro["csv_verificado"] = False
            
            # Agregar registro del archivo procesado
            processed_data[file_name] = registro
            
            # Guardar archivo JSON actualizado
            os.makedirs(os.path.dirname(self.processed_files_json), exist_ok=True)
            
            with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)
            
            status = "✅" if resultado_exitoso else "❌"
            csv_info = f" (CSV: {os.path.basename(csv_path)})" if csv_path else ""
            self.pywinauto_logger.info(f"📝 Registrado {status}: {file_name}{csv_info}")
            
        except Exception as e:
            self.pywinauto_logger.error(f"Error registrando archivo procesado {file_path}: {e}")

    def ejecutar_extraccion_archivo(self, archivo_pqm):
        """Ejecuta el flujo completo para un archivo específico"""
        nombre_archivo = os.path.basename(archivo_pqm)
        csv_path_generado = None
        proceso_exitoso = False  # Variable para controlar el estado real del proceso
        
        try:
            self.pywinauto_logger.info(f"\n🎯 Procesando: {nombre_archivo}")
            
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
            
            # FASE 2: Vista configuración
            self.pywinauto_logger.info("--- FASE 2: VISTA CONFIGURACIÓN ---")
            extractor_config = SonelConfiguracion()
            app_ref = extractor_inicial.get_app_reference()
            
            if not extractor_config.conectar(app_ref):
                self.pywinauto_logger.error("❌ Error conectando vista configuración")
                return False
            
            # Ejecutar extracciones en configuración - MANEJO DE ERRORES MEJORADO
            try:
                time.sleep(1)
                if not extractor_config.extraer_navegacion_lateral():
                    self.pywinauto_logger.warning("⚠️ Falló extracción navegación lateral, continuando...")
                    # NO retornar False aquí, solo advertir
                
                time.sleep(1)
                if not extractor_config.configurar_filtros_datos():
                    self.pywinauto_logger.warning("⚠️ Falló configuración filtros, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(2)
                if not extractor_config.extraer_configuracion_principal_mediciones():
                    self.pywinauto_logger.warning("⚠️ Falló extracción configuración principal, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(2)
                if not extractor_config.extraer_componentes_arbol_mediciones():
                    self.pywinauto_logger.warning("⚠️ Falló extracción árbol mediciones, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(1)
                if not extractor_config.extraer_tabla_mediciones():
                    self.pywinauto_logger.warning("⚠️ Falló extracción tabla mediciones, continuando...")
                    # NO retornar False aquí, solo advertir

                time.sleep(2)
                if not extractor_config.extraer_informes_graficos():
                    self.pywinauto_logger.warning("⚠️ Falló extracción informes gráficos, continuando...")
                    # NO retornar False aquí, solo advertir

            except Exception as e:
                self.pywinauto_logger.warning(f"⚠️ Error en fase de extracción, pero continuando: {e}")
                # NO retornar False, continuar con el guardado

            # FASE 3: Guardar y verificar archivo CSV - ESTA ES LA FASE CRÍTICA
            self.pywinauto_logger.info("--- FASE 3: GUARDADO Y VERIFICACIÓN CSV ---")
            
            try:
                # Generar nombre esperado del CSV
                expected_csv_path = self._get_expected_csv_name(archivo_pqm)
                self.pywinauto_logger.info(f"📄 Archivo CSV esperado: {os.path.basename(expected_csv_path)}")
                
                # Guardar archivo CSV - MODIFICACIÓN AQUÍ para pasar el parámetro
                time.sleep(1)
                save_result = extractor_config.guardar_archivo_csv(expected_csv_path)
                
                # Si el guardado falló, aún intentar verificar
                if not save_result:
                    self.pywinauto_logger.warning("⚠️ Comando de guardado retornó False, pero verificando archivo...")
                
                # Esperar un poco para que se complete la escritura
                time.sleep(3)

                # Buscar el archivo CSV con nombres alternativos
                self.pywinauto_logger.info(f"🔍 Iniciando verificación de archivo")
                found_csv = self._find_generated_csv(expected_csv_path, archivo_pqm)
                
                if found_csv and self._verify_file_creation(found_csv):
                    csv_path_generado = found_csv
                    proceso_exitoso = True  # ÉXITO confirmado por archivo alternativo
                    self.pywinauto_logger.info(f"✅ CSV encontrado y verificado: {os.path.basename(found_csv)}")
                
                    time.sleep(2)
                else:
                    self.pywinauto_logger.error("❌ No se pudo verificar la creación del archivo CSV")
                    proceso_exitoso = False
                        
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
            self.pywinauto_logger.error(f"❌ Error general procesando {nombre_archivo}: {e}")
            proceso_exitoso = False
            return False
        finally:
            # Siempre registrar el resultado, incluyendo información del CSV si se generó
            self.registrar_archivo_procesado(archivo_pqm, proceso_exitoso, csv_path_generado)
    
    def close_sonel_analysis_force(self):
        """
        Cierra todos los procesos relacionados con Sonel Analysis de forma forzada.
        """
        sonel_keywords = ['SonelAnalysis.exe', 'sonelanalysis.exe']
        closed = 0

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                if any(keyword in proc_name for keyword in sonel_keywords):
                    proc.kill()
                    self.pywinauto_logger.info(f"💀 Proceso Sonel terminado: {proc.info['name']} (PID: {proc.info['pid']})")
                    closed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if closed == 0:
            self.pywinauto_logger.info("✅ No se encontraron procesos de Sonel para cerrar.")
        else:
            self.pywinauto_logger.info(f"✅ Se cerraron {closed} procesos de Sonel.")

    def ejecutar_extraccion_completa_dinamica(self):
        """Ejecuta el flujo completo para todos los archivos no procesados"""
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
                return None
            
            # Filtrar archivos ya procesados
            archivos_pendientes = [
                archivo for archivo in archivos_pqm 
                if not self.ya_ha_sido_procesado(archivo)
            ]
            
            if not archivos_pendientes:
                self.pywinauto_logger.info("✅ Todos los archivos ya han sido procesados")
                return {"procesados": 0, "saltados": len(archivos_pqm)}
            
            self.pywinauto_logger.info(f"🔄 Archivos pendientes de procesar: {len(archivos_pendientes)}")
            
            # Procesar cada archivo
            resultados_globales = {
                "procesados_exitosos": 0,
                "procesados_fallidos": 0,
                "saltados": len(archivos_pqm) - len(archivos_pendientes),
                "csvs_verificados": 0,
                "detalles": []
            }
            
            for i, archivo in enumerate(archivos_pendientes, 1):
                nombre_archivo = os.path.basename(archivo)
                self.pywinauto_logger.info(f"\n{'='*60}")
                self.pywinauto_logger.info(f"📁 Procesando archivo {i}/{len(archivos_pendientes)}: {nombre_archivo}")
                self.pywinauto_logger.info(f"{'='*60}")
                
                # EJECUTAR PROCESAMIENTO
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

                # Pausa entre archivos para estabilidad
                if i < len(archivos_pendientes):
                    self.pywinauto_logger.info("⏳ Pausa entre archivos...")
                    time.sleep(4)
            
            # Resumen final
            self.pywinauto_logger.info("\n" + "="*80)
            self.pywinauto_logger.info("📊 RESUMEN FINAL DE PROCESAMIENTO")
            self.pywinauto_logger.info(f"✅ Procesados exitosamente: {resultados_globales['procesados_exitosos']}")
            self.pywinauto_logger.info(f"📄 CSVs verificados: {resultados_globales['csvs_verificados']}")
            self.pywinauto_logger.info(f"❌ Procesados con error: {resultados_globales['procesados_fallidos']}")
            self.pywinauto_logger.info(f"⏭️  Saltados (ya procesados): {resultados_globales['saltados']}")
            self.pywinauto_logger.info(f"📁 Total de archivos: {len(archivos_pqm)}")
            self.pywinauto_logger.info("="*80)

            # Limpieza final
            self.pywinauto_logger.info("🧹 Limpieza final de procesos Sonel Analysis...")
            try:
                self.close_sonel_analysis_force()
            except Exception as e:
                self.pywinauto_logger.warning(f"⚠️ Error en limpieza final: {e}")
            
            return resultados_globales
            
        except Exception as e:
            self.pywinauto_logger.error(f"❌ Error en extracción completa dinámica: {e}")
            return None