import os

class FileManager:
    """Maneja las operaciones de archivos y directorios"""
    
    SUPPORTED_EXTENSIONS = ['.pqm702', '.pqm710', '.pqm711', '.pqm712']

    def __init__(self, paths, logger):
        self.PATHS = paths
        self.logger = logger
    
    def get_pqm_files(self):
        """
        Obtiene lista de archivos PQM con extensiones soportadas en el directorio de entrada
        
        Extensiones soportadas: .pqm702, .pqm710, .pqm711, .pqm712
       
        Returns:
            Lista de rutas de archivos PQM soportados
        """
        try:
            if not os.path.exists(self.PATHS['input_dir']):
                self.logger.error(f"❌ Directorio de entrada no existe: {self.PATHS['input_dir']}")
                return []
           
            pqm_files = []
            files_by_extension = {ext: 0 for ext in self.SUPPORTED_EXTENSIONS}
            
            for file in os.listdir(self.PATHS['input_dir']):
                file_lower = file.lower()
                for ext in self.SUPPORTED_EXTENSIONS:
                    if file_lower.endswith(ext):
                        ruta_normalizada = os.path.join(self.PATHS['input_dir'], file).replace("\\", "/")
                        pqm_files.append(ruta_normalizada)
                        files_by_extension[ext] += 1
                        break
           
            # Ordenar archivos para procesamiento consistente
            pqm_files.sort()
           
            # Log detallado por tipo de extensión
            total_files = len(pqm_files)
            self.logger.info(f"📋 Encontrados {total_files} archivos PQM en {self.PATHS['input_dir']}")
            
            for ext, count in files_by_extension.items():
                if count > 0:
                    self.logger.info(f"   - {ext}: {count} archivo(s)")
            
            # Mostrar lista de archivos si no son demasiados
            if total_files <= 20:
                for i, file in enumerate(pqm_files, 1):
                    file_name = os.path.basename(file)
                    file_ext = self._get_file_extension(file_name)
                    self.logger.info(f"   {i}. {file_name} ({file_ext})")
            elif total_files > 20:
                self.logger.info(f"   (Lista completa de {total_files} archivos disponible para procesamiento)")
           
            return pqm_files
           
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo archivos PQM: {e}")
            return []
    
    def _get_file_extension(self, filename):
        """
        Obtiene la extensión de archivo PQM del nombre de archivo
        
        Args:
            filename (str): Nombre del archivo
            
        Returns:
            str: Extensión encontrada o 'unknown' si no coincide
        """
        filename_lower = filename.lower()
        for ext in self.SUPPORTED_EXTENSIONS:
            if filename_lower.endswith(ext):
                return ext
        return 'unknown'
    
    def is_supported_pqm_file(self, file_path):
        """
        Verifica si un archivo tiene una extensión PQM soportada
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            bool: True si es un archivo PQM soportado
        """
        if not file_path:
            return False
            
        filename = os.path.basename(file_path).lower()
        return any(filename.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)

    def get_file_info(self, file_path):
        """
        Obtiene información detallada de un archivo incluyendo tipo de extensión PQM
       
        Args:
            file_path (str): Ruta al archivo
           
        Returns:
            dict: Información del archivo incluyendo tipo PQM
        """
        import hashlib
        from datetime import datetime
       
        try:
            if not os.path.exists(file_path):
                return {}
               
            stat = os.stat(file_path)
           
            # Calcular hash MD5 del archivo
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            # Información adicional sobre tipo de archivo PQM
            file_name = os.path.basename(file_path)
            pqm_extension = self._get_file_extension(file_name)
            is_supported = self.is_supported_pqm_file(file_path)
           
            return {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "hash": hash_md5.hexdigest(),
                "full_path": os.path.abspath(file_path),
                "pqm_extension": pqm_extension,
                "is_supported_pqm": is_supported,
                "file_type": "PQM" if is_supported else "UNKNOWN"
            }
        except (OSError, IOError) as e:
            self.logger.error(f"❌ Error al obtener información de {file_path}: {e}")
            return {}