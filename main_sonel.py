#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main script para ejecutar el extractor completo de Sonel Analysis

Este script inicializa y ejecuta el procesamiento dinámico de archivos .pqm702
utilizando la clase SonelExtractorCompleto del módulo pysonel_extractor.

Autor: Generado para procesamiento automático de archivos Sonel
Fecha: 2025
"""

import os
import sys
from pathlib import Path

# Importar la clase principal del extractor
from extractors.pywin_extractor import SonelExtractorCompleto
from config.settings import get_full_config, validate_configuration, validate_screen_resolution ,PATHS, LOGGING_CONFIG



def configurar_rutas():
    """
    Configura las rutas por defecto del sistema.
    Personaliza estas rutas según tu configuración específica.
    
    Returns:
        dict: Diccionario con las rutas configuradas
    """

    config = get_full_config()
    
    rutas = {
        "input_directory": config['PATHS']['input_dir'],
        "register_file": config['PATHS']['input_dir'],
        "output_directory": config['PATHS']['export_dir'], 
        "sonel_exe_path": config['PATHS']['sonel_exe_path']
    }
    
    return rutas


def verificar_requisitos(rutas):
    """
    Verifica que existan los directorios y archivos necesarios.
    
    Args:
        rutas (dict): Diccionario con las rutas a verificar
        
    Returns:
        bool: True si todos los requisitos están cumplidos
    """
    print("🔍 Verificando requisitos del sistema...")

    if not validate_configuration():
        return False
    
    # Crear directorio de salida si no existe
    os.makedirs(rutas["output_directory"], exist_ok=True)
    
    print("✅ Todos los requisitos están cumplidos")
    return True


def mostrar_configuracion(rutas):
    """
    Muestra la configuración actual del sistema.
    
    Args:
        rutas (dict): Diccionario con las rutas configuradas
    """
    print("\n" + "="*60)
    print("⚙️  CONFIGURACIÓN DEL EXTRACTOR SONEL")
    print("="*60)
    print(f"📁 Directorio de entrada: {rutas['input_directory']}")
    print(f"📁 Directorio de salida:  {rutas['output_directory']}")
    print(f"🔧 Ejecutable Sonel:      {rutas['sonel_exe_path']}")
    print("="*60)


def mostrar_resumen_final(resultados):
    """
    Muestra el resumen final del procesamiento.
    
    Args:
        resultados (dict): Resultados del procesamiento
    """
    if not resultados:
        print("❌ Error en el procesamiento general")
        return
    
    print("\n" + "="*50)
    print("✅ PROCESAMIENTO COMPLETADO")
    print("="*50)
    print(f"📊 Exitosos:        {resultados['procesados_exitosos']}")
    print(f"📄 CSVs verificados: {resultados['csvs_verificados']}")
    print(f"❌ Fallidos:        {resultados['procesados_fallidos']}")
    print(f"⏭️  Saltados:        {resultados['saltados']}")
    print("="*50)
    
    # Mostrar detalles si están disponibles
    if 'detalles' in resultados and resultados['detalles']:
        print("\n📋 DETALLES POR ARCHIVO:")
        print("-" * 30)
        for detalle in resultados['detalles']:
            estado_icon = "✅" if detalle['estado'] == 'exitoso' else "❌"
            csv_icon = "📄" if detalle.get('csv_verificado', False) else "📋"
            print(f"{estado_icon} {csv_icon} {detalle['archivo']}")


def main():
    """
    Función principal que ejecuta todo el flujo del extractor.
    """
    try:
        print("🚀 INICIANDO EXTRACTOR SONEL ANALYSIS")
        print("="*60)

        # Validar configuración antes de proceder
        validate_screen_resolution()
        
        # Configurar rutas
        rutas = configurar_rutas()
        
        # Mostrar configuración
        mostrar_configuracion(rutas)
        
        # Verificar requisitos
        if not verificar_requisitos(rutas):
            print("❌ No se pueden cumplir los requisitos del sistema")
            sys.exit(1)
        
        # Crear instancia del extractor con procesamiento dinámico
        print("\n🔧 Inicializando extractor...")
        extractor = SonelExtractorCompleto(
            input_dir=rutas["input_directory"],
            output_dir=rutas["output_directory"], 
            ruta_exe=rutas["sonel_exe_path"]
        )
        
        # Ejecutar procesamiento completo dinámico
        print("\n🎯 Iniciando procesamiento completo...")
        resultados = extractor.ejecutar_extraccion_completa_dinamica()
        
        # Mostrar resumen final
        mostrar_resumen_final(resultados)
        
    except KeyboardInterrupt:
        print("\n⚠️  Procesamiento interrumpido por el usuario")
        sys.exit(1)
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de que el módulo 'pysonel_extractor' esté disponible")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()