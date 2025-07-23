import os
import time
import re
from pathlib import Path

class CSVGenerator:
    """Maneja la generación y verificación de archivos CSV"""
    
    def __init__(self, paths, delays, logger):
        self.PATHS = paths
        self.delays = delays
        self.logger = logger
    
    def generate_and_verify_csv(self, archivo_pqm, extractor_config):
        """
        Genera y verifica el archivo CSV
        
        Args:
            archivo_pqm: Ruta del archivo PQM original
            extractor_config: Instancia del extractor de configuración
            
        Returns:
            tuple: (csv_path_generado, proceso_exitoso)
        """
        csv_path_generado = None
        proceso_exitoso = False
        
        try:
            # Generar nombre esperado del CSV
            expected_csv_path = self._get_expected_csv_name(archivo_pqm)
            self.logger.info(f"📄 Archivo CSV esperado: {os.path.basename(expected_csv_path)}")
            
            # Guardar archivo CSV
            time.sleep(1)
            save_result = extractor_config.guardar_archivo_csv(expected_csv_path)
            
            # Si el guardado falló, aún intentar verificar
            if not save_result:
                self.logger.warning("⚠️ Comando de guardado retornó False, pero verificando archivo")
            
            # Esperar un poco para que se complete la escritura
            time.sleep(3)

            # Buscar el archivo CSV con nombres alternativos
            self.logger.info(f"🔍 Iniciando verificación de archivo")
            found_csv = self._find_generated_csv(expected_csv_path, archivo_pqm)
            
            if found_csv and self._verify_file_creation(found_csv):
                csv_path_generado = found_csv
                proceso_exitoso = True
                self.logger.info(f"✅ CSV encontrado y verificado: {os.path.basename(found_csv)}")
                time.sleep(2)
            else:
                self.logger.error("❌ No se pudo verificar la creación del archivo CSV")
                proceso_exitoso = False
                
        except Exception as e:
            self.logger.error(f"❌ Error crítico en generación de CSV: {e}")
            proceso_exitoso = False
        
        return csv_path_generado, proceso_exitoso
    
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
        
        self.logger.info(f"🔍 Iniciando verificación de archivo: {os.path.basename(csv_path)}")
        
        while verification_attempts < max_attempts:
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                if file_size > 100:  # Archivo debe tener contenido mínimo
                    self.logger.info(f"✅ Archivo verificado exitosamente: {os.path.basename(csv_path)} ({file_size} bytes)")
                    return True
                else:
                    self.logger.warning(f"⚠️ Archivo existe pero muy pequeño ({file_size} bytes)")
            
            verification_attempts += 1
            time.sleep(self.delays['file_verification'])
            self.logger.info(f"🔄 Verificación {verification_attempts}/{max_attempts} - Buscando: {os.path.basename(csv_path)}")
        
        self.logger.error(f"❌ Archivo no pudo ser verificado después de {max_attempts} intentos: {os.path.basename(csv_path)}")
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
                self.logger.info(f"📂 Archivo CSV encontrado con nombre alternativo: {possible_name}")
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
                        self.logger.info(f"📂 Posible archivo CSV encontrado (creado recientemente): {most_recent[0]}")
                        return most_recent[2]
        
        except Exception as e:
            self.logger.warning(f"⚠️ Error buscando archivos CSV alternativos: {e}")
        
        return None