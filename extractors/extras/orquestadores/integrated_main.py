#!/usr/bin/env python3
import sys
import os
import time
import argparse
from pathlib import Path
from typing import Optional, Tuple

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Imports para extracción GUI
from config.settings import create_directories, get_full_config
from config.logger import logger
from extractors.pygui_extractor import GUIExtractor

# Imports para ETL
from config.settings import load_config
from etl.sonel_etl import SonelETL
from database.connection import DatabaseConnection


class UnifiedSonelProcessor:
    """
    Procesador unificado que maneja tanto la extracción GUI como el procesamiento ETL
    """
    
    def __init__(self, config_file: str = 'config.ini', debug_mode: bool = False):
        """
        Inicializa el procesador unificado
        
        Args:
            config_file: Archivo de configuración
            debug_mode: Activar modo debug para capturas y logs detallados
        """
        self.config_file = config_file
        self.debug_mode = debug_mode
        
        # Configurar modo debug si está activado
        if debug_mode:
            os.environ['DEBUG_MODE'] = 'True'
            logger.info("🔍 Modo debug activado")
        
        # Cargar configuraciones para ambos módulos
        try:
            self.gui_config = get_full_config()
            self.etl_config = load_config(config_file)
            logger.info("✅ Configuraciones cargadas correctamente")
        except Exception as e:
            logger.error(f"❌ Error cargando configuraciones: {e}")
            raise
    
    def validate_environment(self) -> bool:
        """
        Valida que el entorno esté correctamente configurado
        
        Returns:
            bool: True si el entorno es válido
        """
        logger.info("🔍 Validando entorno de ejecución...")
        
        # Validar directorio de entrada para archivos .pqm702
        input_dir = self.gui_config['PATHS']['input_dir']
        if not os.path.exists(input_dir):
            logger.warning(f"⚠️ Directorio de entrada no existe: {input_dir}")
            logger.info("💡 Creando directorio de entrada...")
            try:
                os.makedirs(input_dir, exist_ok=True)
                logger.info(f"✅ Directorio creado: {input_dir}")
            except Exception as e:
                logger.error(f"❌ No se pudo crear el directorio: {e}")
                return False
        
        # Validar ejecutable de Sonel
        sonel_exe = self.gui_config['PATHS']['sonel_exe_path']
        if not os.path.exists(sonel_exe):
            logger.error(f"❌ Ejecutable de Sonel Analysis no encontrado: {sonel_exe}")
            return False
        
        # Validar directorio de exportación/CSV
        export_dir = self.gui_config['PATHS']['export_dir']
        if not os.path.exists(export_dir):
            logger.info(f"📁 Creando directorio de exportación: {export_dir}")
            try:
                os.makedirs(export_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"❌ No se pudo crear directorio de exportación: {e}")
                return False
        
        logger.info("✅ Entorno validado correctamente")
        return True
    
    def run_gui_extraction(self) -> Tuple[bool, int]:
        """
        Ejecuta la extracción GUI de archivos desde Sonel Analysis
        
        Returns:
            Tuple[bool, int]: (éxito, número de archivos procesados)
        """
        logger.info("🚀 === INICIANDO EXTRACCIÓN GUI ===")
        
        try:
            # Verificar archivos .pqm702 disponibles
            input_dir = self.gui_config['PATHS']['input_dir']
            pqm_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pqm702')]
            
            if not pqm_files:
                logger.info(f"ℹ️ No se encontraron archivos .pqm702 en: {input_dir}")
                logger.info("⏭️ Saltando extracción GUI - no hay archivos para procesar")
                return True, 0
            
            logger.info(f"📋 Encontrados {len(pqm_files)} archivos .pqm702:")
            for i, file in enumerate(pqm_files, 1):
                logger.info(f"   {i}. {file}")
            
            # Crear extractor y ejecutar
            extractor = GUIExtractor(self.gui_config)
            
            start_time = time.time()
            results = extractor.extract()
            end_time = time.time()
            
            if results and len(results) > 0:
                elapsed_time = end_time - start_time
                logger.info(f"✅ Extracción GUI completada exitosamente")
                logger.info(f"📊 Archivos procesados: {len(results)}")
                logger.info(f"⏱️ Tiempo total: {elapsed_time:.2f} segundos")
                logger.info(f"📈 Promedio por archivo: {elapsed_time/len(results):.2f} segundos")
                
                # Mostrar archivos CSV generados
                csv_dir = self.gui_config['PATHS']['export_dir']
                logger.info(f"📄 Archivos CSV generados en {csv_dir}:")
                
                for result in results:
                    if os.path.exists(result):
                        file_size = os.path.getsize(result)
                        logger.info(f"   ✅ {os.path.basename(result)} ({file_size:,} bytes)")
                    else:
                        logger.warning(f"   ⚠️ {os.path.basename(result)} (archivo no encontrado)")
                
                return True, len(results)
            else:
                logger.warning("⚠️ La extracción GUI no generó resultados")
                logger.info("💡 Posibles causas:")
                logger.info("   • Los archivos .pqm702 ya fueron procesados anteriormente")
                logger.info("   • Error en la automatización de Sonel Analysis")
                logger.info("   • Archivos .pqm702 corruptos o incompatibles")
                return True, 0  # No es un error crítico, continuar con ETL
                
        except Exception as e:
            logger.error(f"❌ Error durante extracción GUI: {e}")
            logger.error("🔍 El proceso ETL continuará independientemente")
            import traceback
            logger.error(traceback.format_exc())
            return False, 0
    
    def run_etl_processing(self, force_reprocess: bool = False) -> bool:
        """
        Ejecuta el procesamiento ETL de los archivos CSV
        
        Args:
            force_reprocess: Si True, reprocesa todos los archivos ignorando el registro
            
        Returns:
            bool: True si el procesamiento fue exitoso
        """
        logger.info("🚀 === INICIANDO PROCESAMIENTO ETL ===")
        
        db_connection = None
        etl = None
        
        try:
            # Inicializar conexión a base de datos
            db_connection = DatabaseConnection(self.etl_config)
            if not db_connection.connect():
                logger.error("❌ No se pudo establecer conexión con la base de datos")
                return False
            
            logger.info("✅ Conexión a base de datos establecida")
            
            # Inicializar ETL
            etl = SonelETL(
                config_file=self.config_file,
                db_connection=db_connection
            )
            
            # Directorio donde están los CSV (mismo que export_dir de GUI)
            csv_directory = self.gui_config['PATHS']['export_dir']
            
            logger.info(f"📂 Procesando archivos CSV desde: {csv_directory}")
            
            # Ejecutar procesamiento ETL
            success = etl.run(
                extraction_method='file',
                directory=csv_directory,
                force_reprocess=force_reprocess
            )
            
            if success:
                logger.info("✅ Procesamiento ETL completado exitosamente")
                return True
            else:
                logger.warning("⚠️ El procesamiento ETL se completó con advertencias")
                return True  # Consideramos las advertencias como éxito parcial
                
        except Exception as e:
            logger.error(f"❌ Error durante procesamiento ETL: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
        finally:
            # Limpieza de recursos
            if etl:
                etl.close()
            if db_connection:
                db_connection.close()
            logger.info("🧹 Recursos liberados correctamente")
    
    def run_complete_workflow(self, force_reprocess: bool = False, 
                            skip_gui: bool = False, skip_etl: bool = False) -> bool:
        """
        Ejecuta el flujo completo: extracción GUI + procesamiento ETL
        
        Args:
            force_reprocess: Fuerza el reprocesamiento en ETL
            skip_gui: Omite la extracción GUI
            skip_etl: Omite el procesamiento ETL
            
        Returns:
            bool: True si el flujo completo fue exitoso
        """
        logger.info("🎯 === INICIANDO FLUJO COMPLETO SONEL ===")
        start_time = time.time()
        
        # Validar entorno
        if not self.validate_environment():
            logger.error("❌ Validación de entorno fallida")
            return False
        
        gui_success = True
        extracted_files = 0
        
        # Paso 1: Extracción GUI (opcional)
        if not skip_gui:
            gui_success, extracted_files = self.run_gui_extraction()
            if not gui_success:
                logger.warning("⚠️ Extracción GUI falló, continuando con ETL...")
        else:
            logger.info("⏭️ Extracción GUI omitida por configuración")
        
        # Paso 2: Procesamiento ETL (opcional)
        etl_success = True
        if not skip_etl:
            etl_success = self.run_etl_processing(force_reprocess)
        else:
            logger.info("⏭️ Procesamiento ETL omitido por configuración")
        
        # Resumen final
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info("🏁 === RESUMEN DEL FLUJO COMPLETO ===")
        logger.info(f"⏱️ Tiempo total de ejecución: {total_time:.2f} segundos")
        logger.info(f"🔄 Extracción GUI: {'✅ Exitosa' if gui_success else '❌ Falló'}")
        logger.info(f"📊 Archivos extraídos: {extracted_files}")
        logger.info(f"💾 Procesamiento ETL: {'✅ Exitoso' if etl_success else '❌ Falló'}")
        
        overall_success = (gui_success or skip_gui) and (etl_success or skip_etl)
        logger.info(f"🎯 Resultado general: {'✅ ÉXITO' if overall_success else '❌ FALLO'}")
        
        return overall_success


def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Procesador unificado de Sonel Analysis: Extracción GUI + ETL',
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
        '--config',
        default='config.ini',
        help='Archivo de configuración (por defecto: config.ini)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activa modo debug (capturas de pantalla y logs detallados)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Fuerza el reprocesamiento de todos los archivos en ETL'
    )
    
    parser.add_argument(
        '--skip-gui',
        action='store_true',
        help='Omite la extracción GUI, solo ejecuta ETL'
    )
    
    parser.add_argument(
        '--skip-etl',
        action='store_true',
        help='Omite el procesamiento ETL, solo ejecuta extracción GUI'
    )
    
    return parser.parse_args()


def main():
    """Función principal"""
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        # Crear directorios necesarios
        create_directories()
        
        # Mostrar información inicial
        logger.info("🚀 === PROCESADOR UNIFICADO SONEL ANALYSIS ===")
        logger.info(f"📁 Archivo de configuración: {args.config}")
        logger.info(f"🔍 Modo debug: {'Activado' if args.debug else 'Desactivado'}")
        logger.info(f"🔄 Forzar reprocesamiento: {'Sí' if args.force else 'No'}")
        
        if args.skip_gui and args.skip_etl:
            logger.error("❌ No se puede omitir tanto GUI como ETL. Debe ejecutarse al menos una parte.")
            return 1
        
        # Mostrar advertencias importantes si se ejecuta GUI
        if not args.skip_gui:
            logger.info("\n⚠️ IMPORTANTE PARA EXTRACCIÓN GUI:")
            logger.info("   • Asegúrate de que la resolución de pantalla sea 1920x1080")
            logger.info("   • No muevas el mouse durante la extracción GUI")
            logger.info("   • El proceso puede tomar varios minutos")
        
        # Inicializar procesador
        processor = UnifiedSonelProcessor(
            config_file=args.config,
            debug_mode=args.debug
        )
        
        # Ejecutar flujo completo
        success = processor.run_complete_workflow(
            force_reprocess=args.force,
            skip_gui=args.skip_gui,
            skip_etl=args.skip_etl
        )
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n⛔ Proceso interrumpido por el usuario")
        return 130
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 2
    finally:
        logger.info("🔚 Finalizando procesador unificado")


if __name__ == "__main__":
    exit_code = main()
    
    # Pausa final para ver resultados (solo en modo interactivo)
    if sys.stdin.isatty():
        input("\nPresiona Enter para salir...")
    
    sys.exit(exit_code)