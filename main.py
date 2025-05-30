#sonel_extractor/main.py
import sys
import os
import argparse
from config.logger import logger
from config.settings import load_config
from sonel_etl import SonelETL
from database.connection import DatabaseConnection

def parse_arguments():
    """
    Parsea los argumentos de línea de comandos
   
    Returns:
        args: Objeto con los argumentos parseados
    """
    parser = argparse.ArgumentParser(description='Extractor de datos de Sonel Analysis')
    parser.add_argument(
        '--method',
        choices=['file', 'gui'],
        default='file',
        help='Método de extracción de datos (file o gui). El modo "file" procesa automáticamente todos los archivos del directorio.'
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
   
    return parser.parse_args()

def main():
    """Función principal"""
    logger.info("🚀 === Iniciando extracción de datos de Sonel Analysis ===")
   
    # Parsear argumentos
    args = parse_arguments()
   
    # Cargar configuración
    config = load_config(args.config)
   
    try:
        # Inicializar conexión a base de datos
        db_connection = DatabaseConnection(config)
        if not db_connection.connect():
            logger.error("No se pudo establecer conexión con la base de datos. Abortando.")
            return 1
           
        # Inicializar el ETL
        etl = SonelETL(config_file=args.config, db_connection=db_connection)
        logger.info("🔄 Proceso ETL inicializado")
       
        # Determinar modo de operación y ejecutar el ETL
        directory = args.dir if args.dir else None
        file_path = args.file if args.file else None
       
        # En modo file sin especificar archivo individual, se procesarán todos los archivos automáticamente
        logger.info("🧪 Ejecutando extracción y transformación de datos...")
        success = etl.run(extraction_method=args.method, directory=directory, file_path=file_path)
       
        if success:
            logger.info("🎉 Proceso ejecutado exitosamente")
            exit_code = 0
        else:
            logger.warning("⚠️ El proceso se completó con errores")
            exit_code = 1
           
    except Exception as e:
        logger.error(f"🔥 Error no controlado durante la ejecución: {e}")
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