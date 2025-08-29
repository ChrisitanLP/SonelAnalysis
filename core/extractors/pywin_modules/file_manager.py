import os

class FileManager:
    """Maneja las operaciones de archivos y directorios"""
    
    def __init__(self, paths, logger):
        self.PATHS = paths
        self.logger = logger
    
    def get_pqm_files(self):
        """
        Obtiene lista de archivos .pqm702 en el directorio de entrada
        
        Returns:
            Lista de rutas de archivos .pqm702
        """
        try:
            if not os.path.exists(self.PATHS['input_dir']):
                self.logger.error(f"❌ Directorio de entrada no existe: {self.PATHS['input_dir']}")
                return []
            
            pqm_files = []
            for file in os.listdir(self.PATHS['input_dir']):
                if file.lower().endswith('.pqm702'):
                    ruta_normalizada = os.path.join(self.PATHS['input_dir'], file).replace("\\", "/")
                    pqm_files.append(ruta_normalizada)
            
            # Ordenar archivos para procesamiento consistente
            pqm_files.sort()
            
            self.logger.info(f"📋 Encontrados {len(pqm_files)} archivos .pqm702 en {self.PATHS['input_dir']}")
            for i, file in enumerate(pqm_files, 1):
                self.logger.info(f"   {i}. {os.path.basename(file)}")
            
            return pqm_files
            
        except Exception as e:
            self.logger.error(f"Error obteniendo archivos .pqm702: {e}")
            return []
    
    def get_file_info(self, file_path):
        """
        Obtiene información detallada de un archivo
        
        Args:
            file_path (str): Ruta al archivo
            
        Returns:
            dict: Información del archivo
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
            
            return {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "hash": hash_md5.hexdigest(),
                "full_path": os.path.abspath(file_path)
            }
        except (OSError, IOError) as e:
            self.logger.error(f"❌ Error al obtener información de {file_path}: {e}")
            return {}