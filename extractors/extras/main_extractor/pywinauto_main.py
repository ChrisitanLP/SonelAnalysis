import sys
import os
import time
from pathlib import Path

# Agregar el directorio del proyecto al path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from config.settings import get_config, create_directories, get_full_config
from config.logger import logger
from extractors.extras.main_extractor.pywin_extractor import PywinautoExtractor 

def main():
    """Función principal"""
    try:
        # Obtener configuración
        config = get_full_config()
        
        # Verificar que existe el directorio de archivos .pqm702
        input_dir = config['PATHS']['input_dir']
        if not os.path.exists(input_dir):
            print(f"❌ Error: No existe el directorio de entrada: {input_dir}")
            print(f"   Por favor, crea el directorio y coloca los archivos .pqm702 ahí")
            return
        
        # Verificar archivos .pqm702
        pqm_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pqm702')]
        if not pqm_files:
            print(f"❌ No se encontraron archivos .pqm702 en: {input_dir}")
            input("\nPresiona Enter para salir...")
            return
        
        print(f"📋 Encontrados {len(pqm_files)} archivos .pqm702:")
        for i, file in enumerate(pqm_files, 1):
            print(f"   {i}. {file}")
        
        # Verificar que el ejecutable de Sonel existe
        sonel_exe = config['PATHS']['sonel_exe_path']
        if not os.path.exists(sonel_exe):
            print(f"❌ Error: No se encuentra el ejecutable de Sonel Analysis: {sonel_exe}")
            print(f"   Por favor, verifica la ruta en la configuración")
            input("\nPresiona Enter para salir...")
            return
        
        # Mostrar información del sistema
        print(f"\n📊 INFORMACIÓN DEL SISTEMA:")
        print(f"   • Directorio de entrada: {input_dir}")
        print(f"   • Directorio de salida: {config['PATHS']['export_dir']}")
        print(f"   • Archivos a procesar: {len(pqm_files)}")
        
        # Confirmar ejecución
        print("\n⚠️  IMPORTANTE:")
        print("   • Asegúrate de que la resolución de pantalla sea 1920x1080")
        print("   • No muevas el mouse durante la ejecución")
        print("   • El proceso puede tomar varios minutos")
        
        # Opción de modo debug
        debug_mode = input("\n¿Activar modo debug? (capturas de pantalla y logs detallados) (s/N): ").lower().strip()
        if debug_mode in ['s', 'si', 'sí', 'y', 'yes']:
            os.environ['DEBUG_MODE'] = 'True'
            print("🔍 Modo debug activado")
        
        confirm = input("\n¿Continuar con la extracción? (s/N): ").lower().strip()
        if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
            print("⛔ Operación cancelada por el usuario")
            return
        
        # Crear extractor
        extractor = PywinautoExtractor(config, pqm_files)
        
        # Ejecutar extracción
        start_time = time.time()
        
        results = extractor.extract()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if results and len(results) > 0:
            print(f"✅ Extracción completada exitosamente")
            print(f"📊 Archivos procesados: {len(results)}")
            print(f"⏱️  Tiempo total: {elapsed_time:.2f} segundos")
            print(f"📈 Promedio por archivo: {elapsed_time/len(results):.2f} segundos")
            
            # Mostrar archivos CSV generados
            csv_dir = config['PATHS']['export_dir']
            print(f"📄 Archivos CSV generados en {csv_dir}:")
            
            total_size = 0
            for result in results:
                if os.path.exists(result):
                    file_size = os.path.getsize(result)
                    total_size += file_size
                    print(f"   ✅ {os.path.basename(result)} ({file_size:,} bytes)")
                else:
                    print(f"   ❌ {os.path.basename(result)} (archivo no encontrado)")
            
        else:
            print("❌ La extracción falló")
            print("   Revisa los logs para más detalles")
            
            # Mostrar posibles causas del fallo
            print("\n🔍 POSIBLES CAUSAS DEL FALLO:")
            print("   • El ejecutable de Sonel Analysis no se encontró o no se pudo abrir")
            print("   • Las coordenadas de la GUI no coinciden con tu resolución de pantalla")
            print("   • Sonel Analysis no respondió en el tiempo esperado")
            print("   • Los archivos .pqm702 están corruptos o no son compatibles")
            print("   • Interferencia del usuario durante el proceso")
            
            # Sugerir soluciones
            print("\n💡 SUGERENCIAS:")
            print("   • Ejecuta el programa con modo debug activado")
            print("   • Verifica que la resolución sea 1920x1080")
            print("   • Asegúrate de que Sonel Analysis funcione manualmente")
            print("   • Revisa los logs en la carpeta 'logs/'")
        
        print("\n🏁 Proceso terminado")
        
    except KeyboardInterrupt:
        print("\n\n⛔ Proceso interrumpido por el usuario")
        logger.info("Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        logger.error(f"Error inesperado en main: {e}", exc_info=True)
    finally:
        print("\n" + "="*60)
        print("Presiona Enter para salir...")
        input()

def process_single_file(file_path):
    """
    Procesa un solo archivo .pqm702
    
    Args:
        file_path: Ruta al archivo .pqm702
    """
    try:
        config = get_config()
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            print(f"❌ Archivo no encontrado: {file_path}")
            return False
        
        # Verificar que el ejecutable de Sonel existe
        sonel_exe = config['PATHS']['sonel_exe_path']
        if not os.path.exists(sonel_exe):
            print(f"❌ Error: No se encuentra el ejecutable de Sonel Analysis: {sonel_exe}")
            return False
        
        print(f"🔍 Procesando archivo individual: {file_path}")
        print(f"📊 Tamaño del archivo: {os.path.getsize(file_path):,} bytes")
        
        # Opción de modo debug para archivo individual
        debug_mode = input("\n¿Activar modo debug? (s/N): ").lower().strip()
        if debug_mode in ['s', 'si', 'sí', 'y', 'yes']:
            os.environ['DEBUG_MODE'] = 'True'
            print("🔍 Modo debug activado")
        
        extractor = PywinautoExtractor(config)
        
        start_time = time.time()
        result = extractor.extract_single_file(file_path)
        end_time = time.time()
        
        if result:
            print(f"✅ Archivo procesado exitosamente en {end_time - start_time:.2f} segundos")
            print(f"📄 CSV generado: {result}")
            if os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f"📦 Tamaño del CSV: {file_size:,} bytes")
            return True
        else:
            print(f"❌ Error procesando archivo: {file_path}")
            print("\n🔍 POSIBLES CAUSAS:")
            print("   • El archivo .pqm702 está corrupto o no es compatible")
            print("   • Sonel Analysis no pudo procesar el archivo")
            print("   • Error en la automatización de la GUI")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Error procesando archivo individual {file_path}: {e}", exc_info=True)
        return False

def show_help():
    """Muestra la ayuda del programa"""
    
    print("USO:")
    print("  python main_extractor.py                    # Procesar todos los archivos")
    print("  python main_extractor.py archivo.pqm702    # Procesar un solo archivo")
    print("  python main_extractor.py --help            # Mostrar esta ayuda")
    print("\nREQUISITOS:")
    print("  • Resolución de pantalla: 1920x1080")
    print("  • Sonel Analysis instalado y funcional")
    print("  • Archivos .pqm702 en la carpeta 'archivos_pqm/'")
    print("\nARCHIVOS DE CONFIGURACIÓN:")
    print("  • config/settings.py - Configuración principal")
    print("  • logs/ - Carpeta de logs")
    print("  • csv_generados/ - Carpeta de salida")
    print("\nMODO DEBUG:")
    print("  • Activa capturas de pantalla paso a paso")
    print("  • Genera logs detallados de cada acción")
    print("  • Útil para diagnosticar problemas")

if __name__ == "__main__":
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h', 'help']:
            show_help()
            sys.exit(0)
        elif arg.lower().endswith('.pqm702'):
            # Modo archivo único
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                create_directories()
                success = process_single_file(file_path)
                sys.exit(0 if success else 1)
            else:
                print(f"❌ Archivo no encontrado: {file_path}")
                sys.exit(1)
        else:
            print(f"❌ Argumento no válido: {arg}")
            print("Usa --help para ver las opciones disponibles")
            sys.exit(1)
    else:
        # Modo procesamiento masivo
        main()