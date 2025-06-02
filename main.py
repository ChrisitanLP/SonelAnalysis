#sonel_extractor/main.py
import sys
import os
import argparse
from config.logger import logger
from config.settings import load_config
from etl.sonel_etl import SonelETL
from database.connection import DatabaseConnection

def parse_arguments():
    """
    Parsea los argumentos de línea de comandos
   
    Returns:
        args: Objeto con los argumentos parseados
    """
    parser = argparse.ArgumentParser(description='Extractor de datos de Sonel Analysis con control de procesamiento')
    parser.add_argument(
        '--method',
        choices=['file', 'gui'],
        default='file',
        help='Método de extracción de datos (file o gui). El modo "file" procesa automáticamente archivos nuevos o modificados.'
    )
    parser.add_argument(
        '--config',
        default='config.ini',
        help='Ruta al archivo de configuración'
    )
    parser.add_argument(
        '--dir',
        type=str,
        help='Directorio con archivos a procesar (sobrescribe config)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Archivo específico a procesar'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Fuerza el reprocesamiento de todos los archivos, ignorando el registro'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Muestra el estado del registro de procesamiento y sale'
    )
    parser.add_argument(
        '--reset',
        type=str,
        help='Reinicia el estado de procesamiento de un archivo específico'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Limpia archivos inexistentes del registro'
    )
    parser.add_argument(
        '--registry',
        type=str,
        help='Ruta personalizada al archivo de registro (por defecto: data/registro_procesamiento.json)'
    )
   
    return parser.parse_args()

def show_processing_status(etl):
    """
    Muestra el estado del registro de procesamiento
    
    Args:
        etl: Instancia del ETL
    """
    logger.info("📊 === ESTADO DEL REGISTRO DE PROCESAMIENTO ===")
    
    report = etl.get_processing_report()
    stats = report["statistics"]
    
    print(f"\n📈 ESTADÍSTICAS GENERALES:")
    print(f"  Total de archivos registrados: {stats['total_files']}")
    print(f"  Procesados exitosamente: {stats['successful']}")
    print(f"  Con errores: {stats['errors']}")
    print(f"  Pendientes: {stats['pending']}")
    
    if stats['errors'] > 0:
        print(f"\n❌ ARCHIVOS CON ERRORES:")
        for error_file in report["error_files"]:
            print(f"  - {error_file['file']}: {error_file['error'][:80]}...")
    
    if stats['pending'] > 0:
        print(f"\n⏳ ARCHIVOS PENDIENTES:")
        for pending_file in report["pending_files"]:
            print(f"  - {pending_file}")
    
    print(f"\n📄 Archivo de registro: {report['registry_file']}")

def main():
    """Función principal"""
    logger.info("🚀 === Iniciando extracción de datos de Sonel Analysis ===")
   
    # Parsear argumentos
    args = parse_arguments()
   
    # Cargar configuración
    config = load_config(args.config)
   
    try:
        # Inicializar ETL (incluso para operaciones de solo estado)
        etl = SonelETL(config_file=args.config, registry_file=args.registry)
        
        # Manejar operaciones especiales
        if args.status:
            show_processing_status(etl)
            return 0
        
        if args.reset:
            if os.path.exists(args.reset):
                etl.reset_file_processing(args.reset)
                logger.info(f"✅ Estado reiniciado para: {args.reset}")
            else:
                logger.error(f"❌ Archivo no encontrado: {args.reset}")
                return 1
            return 0
        
        if args.cleanup:
            file_extractor = etl.FileExtractor(config, etl.registry_file)
            cleaned = file_extractor.cleanup_registry()
            logger.info(f"🧹 Limpieza completada: {cleaned} archivos eliminados del registro")
            return 0
        
        # Inicializar conexión a base de datos para procesamiento
        db_connection = DatabaseConnection(config)
        if not db_connection.connect():
            logger.error("No se pudo establecer conexión con la base de datos. Abortando.")
            return 1
        
        # Actualizar la conexión en el ETL
        etl.db_connection = db_connection
        logger.info("🔄 Proceso ETL inicializado")
       
        # Determinar modo de operación y ejecutar el ETL
        directory = args.dir if args.dir else None
        file_path = args.file if args.file else None
        force_reprocess = args.force
        
        if force_reprocess:
            logger.info("🔄 Modo de reprocesamiento forzado activado")
        
        # Ejecutar el procesamiento
        logger.info("🧪 Ejecutando extracción y transformación de datos...")
        success = etl.run(
            extraction_method=args.method, 
            directory=directory, 
            file_path=file_path,
            force_reprocess=force_reprocess
        )
       
        if success:
            logger.info("🎉 Proceso ejecutado exitosamente")
            exit_code = 0
        else:
            logger.warning("⚠️ El proceso se completó con errores")
            exit_code = 1
           
    except KeyboardInterrupt:
        logger.info("⏹️ Proceso interrumpido por el usuario")
        exit_code = 130
    except Exception as e:
        logger.error(f"🔥 Error no controlado durante la ejecución: {e}")
        import traceback
        logger.error(traceback.format_exc())
        exit_code = 2
    finally:
        if 'etl' in locals():
            etl.close()
        if 'db_connection' in locals():
            db_connection.close()
       
    logger.info("✅ === Proceso de extracción finalizado ===")
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)