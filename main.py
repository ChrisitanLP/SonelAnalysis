"""
Main script para ejecutar el extractor completo de Sonel Analysis

Este script inicializa y ejecuta el procesamiento dinámico de archivos .pqm702
utilizando la clase SonelExtractorCompleto del módulo pysonel_extractor.

Autor: Generado para procesamiento automático de archivos Sonel
Fecha: 2025
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
from etl.sonel_etl import SonelETL
from config.logger import get_logger
from database.connection import DatabaseConnection

# Importar la clase principal del extractor
from extractors.pywin_extractor import SonelExtractorCompleto
from config.settings import get_full_config, validate_configuration, validate_screen_resolution ,PATHS, LOGGING_CONFIG, load_config, create_directories

class UnifiedSonelProcessor:
    """
    Procesador unificado que maneja tanto la extracción PYWIN como el procesamiento ETL
    """

    def __init__(self, config_file: str = None):
        """
        Inicializa el procesador unificado
        
        Args:
            config_file: Ruta al archivo de configuración (opcional)
            debug_mode: Modo debug para logging adicional
        """
        self.config_file = config_file
        self.win_config = get_full_config()
        self.etl_config = load_config(config_file)

        self.rutas = self.configurar_rutas()

        self.unified_logger = get_logger("unifiedsonel", f"{__name__}_unifiedsonel")
        self.unified_logger.setLevel(getattr(logging, self.win_config['LOGGING']['level']))

        self.unified_logger.info("="*80)
        self.unified_logger.info("🚀 EXTRACTOR UNIFICADO (SONEL - ETL)")
        self.unified_logger.info("="*80)

    def configurar_rutas(self):
        """
        Configura las rutas por defecto del sistema.
        Personaliza estas rutas según tu configuración específica.
        
        Returns:
            dict: Diccionario con las rutas configuradas
        """

        rutas = {
            "input_directory": self.win_config['PATHS']['input_dir'],
            "register_file": self.win_config['PATHS']['input_dir'],
            "output_directory": self.win_config['PATHS']['export_dir'], 
            "sonel_exe_path": self.win_config['PATHS']['sonel_exe_path']
        }
        
        return rutas

    def _load_etl_config(self):
        """
        Carga la configuración ETL desde archivo
        
        Returns:
            dict: Configuración ETL
        """
        try:
            return self.win_config
        except Exception as e:
            self.unified_logger.error(f"❌ Error cargando configuración ETL: {e}")
            return None
        
    def validate_environment(self):
        """
        Valida que el entorno esté configurado correctamente
        
        Returns:
            bool: True si el entorno es válido
        """
        self.unified_logger.info("🔍 Validando entorno de ejecución...")
        
        # Validar configuración general
        if not validate_configuration():
            self.unified_logger.error("❌ Configuración general inválida")
            return False
        
        # Validar resolución de pantalla para GUI
        try:
            validate_screen_resolution()
        except Exception as e:
            self.unified_logger.error(f"❌ Error en resolución de pantalla: {e}")
            return False
        
        # Crear directorio de salida si no existe
        os.makedirs(self.rutas["output_directory"], exist_ok=True)
        
        self.unified_logger.info("✅ Entorno validado correctamente")
        return True

    def verificar_requisitos(self):
        """
        Verifica que existan los directorios y archivos necesarios.
        
        Args:
            rutas (dict): Diccionario con las rutas a verificar
            
        Returns:
            bool: True si todos los requisitos están cumplidos
        """
        self.unified_logger.info("🔍 Verificando requisitos del sistema...")

        if not validate_configuration():
            return False
        
        # Crear directorio de salida si no existe
        os.makedirs(self.rutas["output_directory"], exist_ok=True)
        
        self.unified_logger.info("✅ Todos los requisitos están cumplidos")
        return True


    def mostrar_configuracion(self):
        """
        Muestra la configuración actual del sistema.
        
        Args:
            rutas (dict): Diccionario con las rutas configuradas
        """
        self.unified_logger.info("\n" + "="*60)
        self.unified_logger.info("⚙️  CONFIGURACIÓN DEL EXTRACTOR SONEL")
        self.unified_logger.info("="*60)
        self.unified_logger.info(f"📁 Directorio de entrada: {self.rutas['input_directory']}")
        self.unified_logger.info(f"📁 Directorio de salida:  {self.rutas['output_directory']}")
        self.unified_logger.info(f"🔧 Ejecutable Sonel:      {self.rutas['sonel_exe_path']}")
        self.unified_logger.info("="*60)

    def run_pywinauto_extraction(self):
        """
        Ejecuta la extracción GUI usando pywinauto
        
        Returns:
            tuple: (success: bool, extracted_files: int)
        """
        self.unified_logger.info("🚀 === INICIANDO EXTRACCIÓN PYWIN ===")
        
        try:
            # Verificar requisitos
            if not self.verificar_requisitos():
                self.unified_logger.error("❌ No se pueden cumplir los requisitos del sistema")
                return False, 0
            
            # Crear instancia del extractor con procesamiento dinámico
            self.unified_logger.info("🔧 Inicializando extractor...")
            extractor = SonelExtractorCompleto(
                input_dir=self.rutas["input_directory"],
                output_dir=self.rutas["output_directory"], 
                ruta_exe=self.rutas["sonel_exe_path"]
            )
            
            # Ejecutar procesamiento completo dinámico
            self.unified_logger.info("🎯 Iniciando procesamiento completo...")
            resultados = extractor.ejecutar_extraccion_completa_dinamica()
            
            # Verificar si se obtuvieron resultados válidos
            if resultados is None:
                self.unified_logger.error("❌ El extractor devolvió None - procesamiento fallido")
                return False, 0
            
            # Verificar que el diccionario tenga la estructura esperada
            if not isinstance(resultados, dict):
                self.unified_logger.error(f"❌ El extractor devolvió tipo inválido: {type(resultados)}")
                return False, 0
            
            # Verificar claves requeridas con valores por defecto
            claves_requeridas = ['procesados_exitosos', 'procesados_fallidos', 'saltados', 'csvs_verificados']
            for clave in claves_requeridas:
                if clave not in resultados:
                    self.unified_logger.warning(f"⚠️ Clave faltante en resultados: {clave}, usando valor por defecto 0")
                    resultados[clave] = 0
            
            # Asegurar que 'detalles' exista
            if 'detalles' not in resultados:
                resultados['detalles'] = []
            
            # Mostrar resumen
            self.mostrar_resumen_pywinauto(resultados)
            
            # ✅ LÓGICA MEJORADA: Considerar éxito cuando todos los archivos están procesados
            archivos_exitosos = resultados.get('procesados_exitosos', 0)
            archivos_saltados = resultados.get('saltados', 0)
            archivos_fallidos = resultados.get('procesados_fallidos', 0)
            
            # Caso 1: Se procesaron archivos nuevos exitosamente
            if archivos_exitosos > 0:
                self.unified_logger.info(f"✅ Extracción PYWIN exitosa: {archivos_exitosos} archivos procesados")
                return True, archivos_exitosos
            
            # Caso 2: Todos los archivos ya estaban procesados (saltados)
            elif archivos_saltados > 0 and archivos_fallidos == 0:
                self.unified_logger.info(f"✅ Extracción PYWIN exitosa: Todos los archivos ya han sido procesados ({archivos_saltados} saltados)")
                return True, 0  # Éxito pero 0 archivos nuevos
            
            # Caso 3: No hay archivos para procesar
            elif archivos_saltados == 0 and archivos_exitosos == 0 and archivos_fallidos == 0:
                self.unified_logger.info("ℹ️ No se encontraron archivos para procesar")
                return True, 0  # Consideramos esto como éxito
            
            # Caso 4: Hubo fallos en el procesamiento
            else:
                self.unified_logger.warning(f"⚠️ Extracción PYWIN completada con {archivos_fallidos} fallos")
                return False, archivos_exitosos
            
        except Exception as e:
            self.unified_logger.error(f"❌ Error durante extracción PYWIN: {e}")
            import traceback
            self.unified_logger.error(traceback.format_exc())
            return False, 0
        
    def run_etl_processing(self, force_reprocess: bool = False):
        """
        Ejecuta el procesamiento ETL de los archivos CSV
        
        Args:
            force_reprocess: Si True, reprocesa todos los archivos ignorando el registro
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """

        self.unified_logger.info("🚀 === INICIANDO PROCESAMIENTO ETL ===")
        
        db_connection = None
        etl = None
        
        try:
            # Inicializar conexión a base de datos
            db_connection = DatabaseConnection(self.etl_config)
            if not db_connection.connect():
                self.unified_logger.error("❌ No se pudo establecer conexión con la base de datos")
                return False
            
            self.unified_logger.info("✅ Conexión a base de datos establecida")
            
            # Inicializar ETL
            etl = SonelETL(
                config_file=self.config_file,
                db_connection=db_connection
            )
            
            # Directorio donde están los CSV (mismo que export_dir de GUI)
            csv_directory = self.rutas["output_directory"]
            
            self.unified_logger.info(f"📂 Procesando archivos CSV desde: {csv_directory}")
            
            # Ejecutar procesamiento ETL
            success = etl.run(
                extraction_method='file',
                directory=csv_directory,
                force_reprocess=force_reprocess
            )
            
            if success:
                self.unified_logger.info("✅ Procesamiento ETL completado exitosamente")
                return True
            else:
                self.unified_logger.warning("⚠️ El procesamiento ETL se completó con advertencias")
                return True  # Consideramos las advertencias como éxito parcial
                
        except Exception as e:
            self.unified_logger.error(f"❌ Error durante procesamiento ETL: {e}")
            import traceback
            self.unified_logger.error(traceback.format_exc())
            return False
            
        finally:
            # Limpieza de recursos
            if etl:
                etl.close()
            if db_connection:
                db_connection.close()
            self.unified_logger.info("🧹 Recursos liberados correctamente")

    def run_complete_workflow(self, force_reprocess: bool = False, 
                        skip_gui: bool = False, skip_etl: bool = False):
        """
        Ejecuta el flujo completo: extracción GUI + procesamiento ETL
        
        Args:
            force_reprocess: Fuerza el reprocesamiento en ETL
            skip_gui: Omite la extracción GUI
            skip_etl: Omite el procesamiento ETL
            
        Returns:
            bool: True si el flujo completo fue exitoso
        """
        self.unified_logger.info("🎯 === INICIANDO FLUJO COMPLETO SONEL ===")
        start_time = time.time()
        
        # Validar entorno
        if not self.validate_environment():
            self.unified_logger.error("❌ Validación de entorno fallida")
            return False
        
        gui_success = True
        extracted_files = 0
        
        # Paso 1: Extracción GUI (opcional)
        if not skip_gui:
            gui_success, extracted_files = self.run_pywinauto_extraction()
            if not gui_success:
                self.unified_logger.warning("⚠️ Extracción PYWINAUTO falló, continuando con ETL...")
        else:
            self.unified_logger.info("⏭️ Extracción PYWINAUTO omitida por configuración")
        
        # Paso 2: Procesamiento ETL (opcional)
        etl_success = True
        if not skip_etl:
            etl_success = self.run_etl_processing(force_reprocess)
        else:
            self.unified_logger.info("⏭️ Procesamiento ETL omitido por configuración")
        
        # Resumen final
        end_time = time.time()
        total_time = end_time - start_time
        
        self.unified_logger.info("🏁 === RESUMEN DEL FLUJO COMPLETO ===")
        self.unified_logger.info(f"⏱️ Tiempo total de ejecución: {total_time:.2f} segundos")
        
        # ✅ MENSAJE MEJORADO: Más claro sobre el estado
        if gui_success and extracted_files > 0:
            self.unified_logger.info(f"🔄 Extracción PYWIN: ✅ Exitosa - {extracted_files} archivos nuevos procesados")
        elif gui_success and extracted_files == 0 and not skip_gui:
            self.unified_logger.info("🔄 Extracción PYWIN: ✅ Exitosa - Todos los archivos ya procesados")
        elif not gui_success and not skip_gui:
            self.unified_logger.info("🔄 Extracción PYWIN: ❌ Falló")
        else:
            self.unified_logger.info("🔄 Extracción PYWIN: ⏭️ Omitida")
        
        self.unified_logger.info(f"📊 Archivos extraídos: {extracted_files}")
        self.unified_logger.info(f"💾 Procesamiento ETL: {'✅ Exitoso' if etl_success else '❌ Falló'}")
        
        overall_success = (gui_success or skip_gui) and (etl_success or skip_etl)
        self.unified_logger.info(f"🎯 Resultado general: {'✅ ÉXITO' if overall_success else '❌ FALLO'}")
        
        return overall_success

    def mostrar_resumen_pywinauto(self, resultados):
        """
        Muestra el resumen final del procesamiento con validación robusta.
        
        Args:
            resultados (dict): Resultados del procesamiento
        """
        try:
            # Validar que resultados no sea None
            if resultados is None:
                self.unified_logger.error("❌ Error en el procesamiento general - resultados nulos")
                return
            
            # Validar que sea un diccionario
            if not isinstance(resultados, dict):
                self.unified_logger.error(f"❌ Error en el procesamiento general - tipo inválido: {type(resultados)}")
                return
            
            # Obtener valores con valores por defecto seguros
            procesados_exitosos = resultados.get('procesados_exitosos', 0)
            procesados_fallidos = resultados.get('procesados_fallidos', 0)
            saltados = resultados.get('saltados', 0)
            csvs_verificados = resultados.get('csvs_verificados', 0)
            detalles = resultados.get('detalles', [])
            
            # ✅ LÓGICA MEJORADA: Mensaje de estado más claro
            if procesados_exitosos > 0:
                estado_mensaje = "✅ PROCESAMIENTO EXITOSO"
            elif saltados > 0 and procesados_fallidos == 0:
                estado_mensaje = "✅ PROCESAMIENTO COMPLETO - TODOS LOS ARCHIVOS YA PROCESADOS"
            elif procesados_fallidos > 0:
                estado_mensaje = "⚠️ PROCESAMIENTO COMPLETADO CON ERRORES"
            else:
                estado_mensaje = "ℹ️ NO SE ENCONTRARON ARCHIVOS PARA PROCESAR"
            
            # Mostrar resumen principal
            self.unified_logger.info("\n" + "="*50)
            self.unified_logger.info(estado_mensaje)
            self.unified_logger.info("="*50)
            self.unified_logger.info(f"📊 Exitosos:        {procesados_exitosos}")
            self.unified_logger.info(f"📄 CSVs verificados: {csvs_verificados}")
            self.unified_logger.info(f"❌ Fallidos:        {procesados_fallidos}")
            self.unified_logger.info(f"⏭️  Saltados:        {saltados}")
            self.unified_logger.info("="*50)
            
            # Mostrar detalles si están disponibles
            if detalles and len(detalles) > 0:
                self.unified_logger.info("\n📋 DETALLES POR ARCHIVO:")
                self.unified_logger.info("-" * 30)
                for detalle in detalles:
                    if isinstance(detalle, dict):
                        archivo = detalle.get('archivo', 'Desconocido')
                        estado = detalle.get('estado', 'desconocido')
                        csv_verificado = detalle.get('csv_verificado', False)
                        
                        estado_icon = "✅" if estado == 'exitoso' else "❌"
                        csv_icon = "📄" if csv_verificado else "📋"
                        self.unified_logger.info(f"{estado_icon} {csv_icon} {archivo}")
                    else:
                        self.unified_logger.warning(f"⚠️ Detalle inválido: {detalle}")
            
            # Mostrar información adicional si hay claves extra
            claves_extra = set(resultados.keys()) - {
                'procesados_exitosos', 'procesados_fallidos', 'saltados', 
                'csvs_verificados', 'detalles'
            }
            if claves_extra:
                self.unified_logger.info(f"\n📌 Información adicional: {dict((k, resultados[k]) for k in claves_extra)}")
                
        except Exception as e:
            self.unified_logger.error(f"❌ Error mostrando resumen: {e}")
            # Mostrar información básica de respaldo
            self.unified_logger.info("\n" + "="*50)
            self.unified_logger.info("⚠️ RESUMEN CON ERRORES")
            self.unified_logger.info("="*50)
            self.unified_logger.info(f"Resultados recibidos: {resultados}")
            self.unified_logger.info("="*50)

def parse_arguments():
    """
    Parsea los argumentos de línea de comandos
    
    Returns:
        argparse.Namespace: Argumentos parseados
    """

    parser = argparse.ArgumentParser(
        description="Procesador unificado Sonel Analysis - Extracción GUI + ETL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Ejemplos de uso:
            python main_unified.py                    # Flujo completo (GUI + ETL)
            python main_unified.py --skip-gui         # Solo ETL
            python main_unified.py --skip-etl         # Solo extracción GUI
            python main_unified.py --debug            # Flujo completo con modo debug
            python main_unified.py --force            # Fuerza reprocesamiento en ETL
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.ini',
        help='Ruta al archivo de configuración ETL (opcional)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Activar modo debug'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Forzar reprocesamiento en ETL'
    )
    
    parser.add_argument(
        '--skip-gui',
        action='store_true',
        help='Omitir extracción PYWIN'
    )
    
    parser.add_argument(
        '--skip-etl',
        action='store_true',
        help='Omitir procesamiento ETL'
    )
    
    return parser.parse_args()

def main():
    """
    Función principal que ejecuta todo el flujo del extractor unificado.
    """
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Crear directorios necesarios
        create_directories()
        
        # Mostrar información inicial
        print("🚀 === PROCESADOR UNIFICADO SONEL ANALYSIS ===")
        print(f"📁 Archivo de configuración: {args.config or 'Por defecto'}")
        print(f"🔍 Modo debug: {'Activado' if args.debug else 'Desactivado'}")
        print(f"🔄 Forzar reprocesamiento: {'Sí' if args.force else 'No'}")
        
        if args.skip_gui and args.skip_etl:
            print("❌ No se puede omitir tanto PYWIN como ETL. Debe ejecutarse al menos una parte.")
            return 1
        
        # Mostrar advertencias importantes si se ejecuta GUI
        if not args.skip_gui:
            print("\n⚠️ IMPORTANTE PARA EXTRACCIÓN PYWIN:")
            print("   • Asegúrate de que la resolución de pantalla sea 1920x1080")
            print("   • No muevas el mouse durante la extracción PYWIN")
            print("   • El proceso puede tomar varios minutos")
        
        # Inicializar procesador
        processor = UnifiedSonelProcessor(
            config_file=args.config
        )
        
        # Mostrar configuración
        processor.mostrar_configuracion()
        
        # Ejecutar flujo completo
        success = processor.run_complete_workflow(
            force_reprocess=args.force,
            skip_gui=args.skip_gui,
            skip_etl=args.skip_etl
        )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⛔ Proceso interrumpido por el usuario")
        return 130
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de que todos los módulos estén disponibles")
        return 1
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        print(traceback.format_exc())
        return 2
    finally:
        print("🔚 Finalizando procesador unificado")


if __name__ == "__main__":
    exit_code = main()
    
    # Pausa final para ver resultados (solo en modo interactivo)
    if sys.stdin.isatty():
        input("\nPresiona Enter para salir...")
    
    sys.exit(exit_code)