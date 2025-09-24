import os
import time
import re
from pathlib import Path
from datetime import datetime

class CSVGenerator:
    """Maneja la generación y verificación de archivos CSV"""
    
    def __init__(self, paths, delays, logger):
        self.PATHS = paths
        self.delays = delays
        self.logger = logger
        self.filename_counter = {}
    
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
            
            # Guardar archivo CSV
            time.sleep(1)
            save_result = extractor_config.guardar_archivo_csv(expected_csv_path)
            
            # Si el guardado falló, aún intentar verificar
            if not save_result:
                self.logger.warning("⚠️ Comando de guardado retornó False, pero verificando archivo")
            
            # Esperar un poco para que se complete la escritura
            time.sleep(3)

            # Buscar el archivo CSV con nombres alternativos
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
        
        self.logger.error(f"❌ Archivo no pudo ser verificado después de {max_attempts} intentos: {os.path.basename(csv_path)}")
        return False

    def _get_expected_csv_name(self, archivo_pqm):
        """
        Genera el nombre esperado del archivo CSV basado en el archivo PQM original
        MODIFICADO: Ahora agrega numeración incremental si detecta archivos duplicados
        
        Args:
            archivo_pqm: Ruta del archivo .pqm702
            
        Returns:
            str: Nombre completo esperado del archivo CSV con numeración si es necesario
        """
        from pathlib import Path
        
        # Obtener el nombre completo del archivo sin extensión
        file_stem = Path(archivo_pqm).stem
        
        # NUEVA LÓGICA: Verificar si ya existe un archivo con este nombre base
        base_csv_name = f"{file_stem}.csv"
        base_csv_path = os.path.join(self.PATHS['output_dir'], base_csv_name)
        
        # Obtener información del directorio fuente para contexto
        source_directory = os.path.basename(os.path.dirname(archivo_pqm))
        
        final_csv_name = self._aplicar_numeracion_esperada(base_csv_name, file_stem)
        final_csv_path = os.path.join(self.PATHS['output_dir'], final_csv_name)
        
        self.logger.info(f"📄 CSV esperado: {final_csv_name} (directorio: {source_directory})")
        
        if final_csv_name != base_csv_name:
            self.logger.info(f"   🔄 Numeración aplicada para evitar conflictos")
        
        return final_csv_path

    def _aplicar_numeracion_esperada(self, nombre_csv, file_stem):
        """
        Aplica la misma lógica de numeración que usará el executor.
        
        Args:
            nombre_csv (str): Nombre base del CSV
            file_stem (str): Nombre del archivo sin extensión
            
        Returns:
            str: Nombre del CSV con numeración si es necesario
        """
        base_csv_path = os.path.join(self.PATHS['output_dir'], nombre_csv)
        
        # Si no existe, usar el nombre original
        if not os.path.exists(base_csv_path):
            return nombre_csv
        
        # Buscar el siguiente número disponible (misma lógica que executor)
        contador = 1
        max_intentos = 500
        
        while contador <= max_intentos:
            nombre_numerado = f"{contador}_{file_stem}.csv"
            ruta_numerada = os.path.join(self.PATHS['output_dir'], nombre_numerado)
            
            if not os.path.exists(ruta_numerada):
                return nombre_numerado
            
            contador += 1
        
        # Fallback con timestamp si es necesario
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{file_stem}.csv"


    def _find_generated_csv(self, expected_csv_path, archivo_pqm):
        """
        Busca el archivo CSV generado, considerando posibles variaciones en el nombre
        MODIFICADO: Mejorado para manejar archivos con numeración incremental
        
        Args:
            expected_csv_path: Ruta esperada del archivo CSV
            archivo_pqm: Archivo PQM original para extraer información
            
        Returns:
            str|None: Ruta del archivo CSV encontrado o None si no se encuentra
        """
        import re
        
        # Primero verificar si existe con el nombre esperado
        if os.path.exists(expected_csv_path):
            return expected_csv_path
        
        # Extraer información del archivo original
        original_name = os.path.basename(archivo_pqm)
        file_stem = Path(archivo_pqm).stem
        source_directory = os.path.basename(os.path.dirname(archivo_pqm))
        
        # NUEVA LÓGICA: Buscar archivos con numeración incremental
        possible_names = [
            f"{file_stem}.csv",
            f"{file_stem}_procesado.csv",
        ]
        
        # Agregar posibles nombres con numeración
        for i in range(1, 11):  # Buscar hasta 10 variaciones numeradas
            possible_names.extend([
                f"{i}. {file_stem}.csv",
                f"{i}_{file_stem}.csv",
                f"({i}) {file_stem}.csv"
            ])
        
        # Si el nombre tiene números al inicio, buscar también solo con esos números
        match = re.match(r'^(\d+)', file_stem)
        if match:
            number_prefix = match.group(1)
            possible_names.extend([
                f"{number_prefix}.csv",
                f"{number_prefix}_procesado.csv"
            ])
            # Agregar variaciones numeradas del prefijo
            for i in range(1, 6):
                possible_names.extend([
                    f"{i}. {number_prefix}.csv",
                    f"{i}_{number_prefix}.csv"
                ])
        
        # Buscar en el directorio de salida
        for possible_name in possible_names:
            possible_path = os.path.join(self.PATHS['output_dir'], possible_name)
            if os.path.exists(possible_path):
                self.logger.info(f"📂 Archivo CSV encontrado con nombre alternativo: {possible_name}")
                return possible_path
        
        # Buscar cualquier archivo CSV creado recientemente con patrón similar
        try:
            csv_files = [f for f in os.listdir(self.PATHS['output_dir']) if f.endswith('.csv')]
            if csv_files:
                # Filtrar archivos que contengan parte del nombre original
                file_stem_clean = re.sub(r'[^\w\s]', '', file_stem).lower()
                matching_files = []
                
                for csv_file in csv_files:
                    csv_file_clean = re.sub(r'[^\w\s]', '', csv_file).lower()
                    # Buscar coincidencias parciales
                    if any(word in csv_file_clean for word in file_stem_clean.split() if len(word) > 3):
                        csv_path = os.path.join(self.PATHS['output_dir'], csv_file)
                        mtime = os.path.getmtime(csv_path)
                        matching_files.append((csv_file, mtime, csv_path))
                
                if matching_files:
                    # Ordenar por fecha de modificación (más reciente primero)
                    matching_files.sort(key=lambda x: x[1], reverse=True)
                    
                    # Verificar si el archivo más reciente fue creado en los últimos 5 minutos
                    most_recent = matching_files[0]
                    time_diff = time.time() - most_recent[1]
                    
                    if time_diff < 300:  # 5 minutos
                        self.logger.info(f"📂 Posible archivo CSV encontrado por similitud: {most_recent[0]}")
                        return most_recent[2]
        
        except Exception as e:
            self.logger.warning(f"⚠️ Error buscando archivos CSV alternativos: {e}")
        
        return None