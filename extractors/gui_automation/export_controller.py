import os
import time
import pyautogui
from pathlib import Path
from config.logger import logger
from config.settings import get_coordinates, get_delays
from utils.gui_helpers import GUIHelpers
from utils.file_helpers import FileHelpers


class ExportController:
    """
    Controlador para configuración de mediciones y exportación de datos desde Sonel Analysis
    """
    
    def __init__(self, config):
        self.config = config
        self.coordinates = get_coordinates()
        self.delays = get_delays()
        self.export_dir = config['PATHS'].get('export_dir', 'D:/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_csv')
        self.debug_mode = config.get('debug_mode', False)
        
        # Asegurar que el directorio de exportación existe
        FileHelpers.ensure_directory_exists(self.export_dir)

    def configure_measurements_and_export(self, pqm_file_path):
        """
        Navega en la GUI de Sonel para seleccionar configuraciones específicas y exportar los datos
        
        Args:
            pqm_file_path: Ruta del archivo .pqm original para generar nombre del CSV
            
        Returns:
            str: Ruta del archivo CSV exportado o None si hay error
        """
        try:
            # Generar nombre del archivo CSV basado en el archivo .pqm
            csv_base_name = FileHelpers.generate_csv_filename(
                pqm_file_path, 
                cleanup_enabled=self.config.get('FILES', {}).get('filename_cleanup', True)
            )
            
            csv_filename = f"{csv_base_name}.csv"
            csv_full_path = os.path.join(self.export_dir, csv_filename)
            
            logger.info(f"🔧 Configurando mediciones para: {os.path.basename(pqm_file_path)}")
            GUIHelpers.debug_log(f"Archivo de destino: {csv_full_path}", self.debug_mode)
            
            # Paso 1: Navegación por menús principales
            if not self._navigate_to_measurements():
                logger.error("❌ Falló navegación a mediciones")
                return None
            
            # Paso 2: Configurar selecciones específicas
            if not self._configure_measurement_selections():
                logger.error("❌ Falló configuración de selecciones")
                return None
                
            # Paso 3: Ejecutar exportación
            if not self._execute_export(csv_full_path):
                logger.error("❌ Falló exportación")
                return None
            
            # Paso 4: Verificar archivo exportado
            if self._verify_exported_file(csv_full_path):
                logger.info(f"✅ Exportación exitosa: {csv_filename}")
                return csv_full_path
            else:
                logger.error(f"❌ No se pudo verificar archivo exportado: {csv_filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error durante configuración y exportación: {e}")
            return None

    def _navigate_to_measurements(self):
        """
        Navega a través de los menús principales hasta llegar a mediciones
        
        Returns:
            bool: True si la navegación es exitosa
        """
        try:
            GUIHelpers.debug_log("Iniciando navegación a mediciones", self.debug_mode)
            
            # Secuencia de navegación principal
            navigation_steps = [
                (self.coordinates['config_1'], "Config 1", self.delays['after_menu']),
                (self.coordinates['analisis_datos'], "Análisis de Datos", self.delays['after_menu']),
                (self.coordinates['mediciones'], "Mediciones", self.delays['after_menu'])
            ]
            
            for coords, description, delay in navigation_steps:
                if not GUIHelpers.safe_click(
                    coords[0], coords[1], 
                    description, 
                    delay_after=delay, 
                    debug_mode=self.debug_mode
                ):
                    logger.error(f"❌ Falló paso de navegación: {description}")
                    return False
                    
                logger.info(f"✅ Navegación completada: {description}")
            
            GUIHelpers.debug_log("Navegación a mediciones completada", self.debug_mode)
            return True
            
        except Exception as e:
            logger.error(f"Error navegando a mediciones: {e}")
            return False

    def _configure_measurement_selections(self):
        """
        Configura las selecciones específicas de mediciones
        
        Returns:
            bool: True si la configuración es exitosa
        """
        try:
            GUIHelpers.debug_log("Configurando selecciones de mediciones", self.debug_mode)
            
            # Configuraciones específicas de mediciones
            selection_steps = [
                (self.coordinates['check_usuario'], "Checkbox usuario", self.delays['between_clicks']),
            ]
            
            for coords, description, delay in selection_steps:
                if not GUIHelpers.safe_click(
                    coords[0], coords[1], 
                    description, 
                    delay_after=delay,
                    debug_mode=self.debug_mode
                ):
                    logger.error(f"❌ Falló configuración: {description}")
                    return False
                    
                logger.info(f"✅ Configuración aplicada: {description}")
            
            # Confirmar selección haciendo clic en la esquina de la tabla
            if not GUIHelpers.safe_click(
                self.coordinates['tabla_esquina'][0], 
                self.coordinates['tabla_esquina'][1], 
                "Confirmar selección tabla",
                delay_after=self.delays['before_export'],
                debug_mode=self.debug_mode
            ):
                logger.error("❌ Falló confirmación de selección")
                return False
            
            logger.info("✅ Selecciones de mediciones configuradas")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando selecciones: {e}")
            return False

    def _execute_export(self, csv_full_path):
        """
        Ejecuta el proceso de exportación a CSV
        
        Args:
            csv_full_path: Ruta completa donde guardar el archivo CSV
            
        Returns:
            bool: True si la exportación se ejecuta correctamente
        """
        try:
            GUIHelpers.debug_log("Iniciando proceso de exportación", self.debug_mode)
            
            # Navegar a menú de exportación
            export_navigation = [
                (self.coordinates['informes'], "Menú Informes", self.delays['after_menu']),
                (self.coordinates['exportar_csv'], "Exportar CSV", self.delays['after_menu'])
            ]
            
            for coords, description, delay in export_navigation:
                if not GUIHelpers.safe_click(
                    coords[0], coords[1], 
                    description, 
                    delay_after=delay,
                    debug_mode=self.debug_mode
                ):
                    logger.error(f"❌ Falló navegación de exportación: {description}")
                    return False
                    
                logger.info(f"✅ Navegación exportación: {description}")
            
            # Configurar nombre del archivo en el diálogo de guardado
            if not self._configure_export_filename(csv_full_path):
                logger.error("❌ Falló configuración del nombre de archivo")
                return False
            
            logger.info("✅ Proceso de exportación ejecutado")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando exportación: {e}")
            return False

    def _configure_export_filename(self, csv_full_path):
        """
        Configura el nombre del archivo en el diálogo de exportación
        
        Args:
            csv_full_path: Ruta completa del archivo a guardar
            
        Returns:
            bool: True si se configura correctamente el nombre
        """
        try:
            GUIHelpers.debug_log(f"Configurando nombre de archivo: {csv_full_path}", self.debug_mode)
            
            # Hacer clic en el campo de nombre de archivo
            if not GUIHelpers.safe_click(
                self.coordinates['dialogo_nombre'][0], 
                self.coordinates['dialogo_nombre'][1], 
                "Campo nombre archivo", 
                delay_after=self.delays['file_naming'],
                debug_mode=self.debug_mode
            ):
                logger.error("❌ No se pudo acceder al campo de nombre")
                return False
            
            # Escribir la ruta completa del archivo
            if not GUIHelpers.write_text_safely(
                csv_full_path,
                clear_first=True,
                delay_after=0.5
            ):
                logger.error("❌ No se pudo escribir el nombre del archivo")
                return False
            
            logger.info(f"💾 Configurado nombre de archivo: {os.path.basename(csv_full_path)}")
            
            # Confirmar guardado
            if not GUIHelpers.send_hotkey('enter', delay_after=self.delays['after_export']):
                logger.error("❌ No se pudo confirmar el guardado")
                return False
            
            logger.info("✅ Nombre de archivo configurado y confirmado")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando nombre de archivo: {e}")
            return False

    def _verify_exported_file(self, csv_full_path, max_attempts=8, min_file_size=100):
        """
        Verifica que el archivo haya sido exportado correctamente
        
        Args:
            csv_full_path: Ruta completa del archivo a verificar
            max_attempts: Número máximo de intentos de verificación
            min_file_size: Tamaño mínimo esperado del archivo en bytes
            
        Returns:
            bool: True si el archivo se exportó correctamente
        """
        try:
            GUIHelpers.debug_log(f"Verificando archivo exportado: {csv_full_path}", self.debug_mode)
            
            verification_attempts = 0
            
            while verification_attempts < max_attempts:
                # Verificar si el archivo existe
                file_exists, validation_message = FileHelpers.validate_file_exists(
                    csv_full_path, 
                    min_size_bytes=min_file_size
                )
                
                if file_exists:
                    file_size_str = FileHelpers.get_file_size_formatted(csv_full_path)
                    logger.info(f"✅ Archivo verificado: {os.path.basename(csv_full_path)} ({file_size_str})")
                    return True
                else:
                    GUIHelpers.debug_log(
                        f"Verificación {verification_attempts + 1}/{max_attempts}: {validation_message}", 
                        self.debug_mode
                    )
                
                verification_attempts += 1
                time.sleep(self.delays['file_verification'])
            
            logger.error(f"❌ No se pudo verificar archivo después de {max_attempts} intentos: {csv_full_path}")
            return False
            
        except Exception as e:
            logger.error(f"Error verificando archivo exportado: {e}")
            return False

    def export_single_measurement(self, pqm_file_path, measurement_config=None):
        """
        Exporta una medición específica con configuración personalizada
        
        Args:
            pqm_file_path: Ruta del archivo .pqm original
            measurement_config: Configuración específica de medición (opcional)
            
        Returns:
            str: Ruta del archivo CSV exportado o None si hay error
        """
        try:
            logger.info(f"🎯 Exportación específica para: {os.path.basename(pqm_file_path)}")
            
            # Si se proporciona configuración específica, aplicarla
            if measurement_config:
                GUIHelpers.debug_log(f"Aplicando configuración específica: {measurement_config}", self.debug_mode)
                # Aquí se pueden agregar configuraciones específicas en el futuro
            
            # Usar el método principal de configuración y exportación
            return self.configure_measurements_and_export(pqm_file_path)
            
        except Exception as e:
            logger.error(f"Error en exportación específica: {e}")
            return None

    def batch_export_measurements(self, pqm_files_list):
        """
        Exporta múltiples mediciones en lote
        
        Args:
            pqm_files_list: Lista de rutas de archivos .pqm
            
        Returns:
            list: Lista de rutas de archivos CSV exportados exitosamente
        """
        try:
            logger.info(f"📦 Iniciando exportación en lote para {len(pqm_files_list)} archivos")
            
            exported_files = []
            failed_exports = []
            
            for i, pqm_file in enumerate(pqm_files_list, 1):
                logger.info(f"📁 Procesando archivo {i}/{len(pqm_files_list)}: {os.path.basename(pqm_file)}")
                
                csv_path = self.configure_measurements_and_export(pqm_file)
                
                if csv_path:
                    exported_files.append(csv_path)
                    logger.info(f"✅ Exportado {i}/{len(pqm_files_list)}")
                else:
                    failed_exports.append(pqm_file)
                    logger.error(f"❌ Falló exportación {i}/{len(pqm_files_list)}")
                
                # Pausa entre archivos si no es el último
                if i < len(pqm_files_list):
                    GUIHelpers.stabilization_pause(
                        self.delays.get('between_files', 2),
                        file_number=i,
                        total_files=len(pqm_files_list)
                    )
            
            # Resumen final
            logger.info(f"📊 Exportación en lote completada:")
            logger.info(f"   ✅ Exitosos: {len(exported_files)}")
            logger.info(f"   ❌ Fallidos: {len(failed_exports)}")
            
            if failed_exports:
                logger.warning("❌ Archivos que fallaron:")
                for failed_file in failed_exports:
                    logger.warning(f"   - {os.path.basename(failed_file)}")
            
            return exported_files
            
        except Exception as e:
            logger.error(f"Error en exportación en lote: {e}")
            return exported_files if 'exported_files' in locals() else []

    def get_export_statistics(self):
        """
        Obtiene estadísticas del directorio de exportación
        
        Returns:
            dict: Estadísticas de archivos exportados
        """
        try:
            csv_files = FileHelpers.get_files_by_extension(self.export_dir, '.csv', sort_files=True)
            
            total_size = 0
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    total_size += os.path.getsize(csv_file)
            
            stats = {
                'total_files': len(csv_files),
                'total_size_bytes': total_size,
                'total_size_formatted': f"{total_size:,} bytes",
                'export_directory': self.export_dir,
                'recent_files': [os.path.basename(f) for f in csv_files[-5:]]  # Últimos 5
            }
            
            GUIHelpers.debug_log(f"Estadísticas de exportación: {stats}", self.debug_mode)
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de exportación: {e}")
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_formatted': '0 bytes',
                'export_directory': self.export_dir,
                'recent_files': [],
                'error': str(e)
            }