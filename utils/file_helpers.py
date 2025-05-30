import os
import datetime
from pathlib import Path
from config.logger import logger


class FileHelpers:
    @staticmethod
    def generate_csv_filename(pqm_file_path, cleanup_enabled=True):
        try:
            base_name = Path(pqm_file_path).stem
            
            if cleanup_enabled:
                clean_name = "".join(c for c in base_name if c.isalnum() or c in ('-', '_', ' '))
                clean_name = clean_name.strip()
                if clean_name:
                    base_name = clean_name
            
            return base_name
            
        except Exception as e:
            logger.error(f"Error generando nombre CSV: {e}")
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"export_{timestamp}"

    @staticmethod
    def ensure_directory_exists(directory_path):
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creando directorio {directory_path}: {e}")
            return False

    @staticmethod
    def get_file_size_formatted(file_path):
        try:
            if os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                return f"{size_bytes:,} bytes"
            return "0 bytes"
        except Exception:
            return "Unknown size"

    @staticmethod
    def validate_file_exists(file_path, min_size_bytes=0):
        try:
            if not os.path.exists(file_path):
                return False, f"Archivo no encontrado: {file_path}"
            
            if min_size_bytes > 0:
                size = os.path.getsize(file_path)
                if size < min_size_bytes:
                    return False, f"Archivo muy pequeño ({size} bytes, mínimo {min_size_bytes})"
            
            return True, "Archivo válido"
            
        except Exception as e:
            return False, f"Error validando archivo: {e}"

    @staticmethod
    def get_files_by_extension(directory, extension, sort_files=True):
        try:
            if not os.path.exists(directory):
                logger.error(f"Directorio no existe: {directory}")
                return []
            
            files = []
            for file in os.listdir(directory):
                if file.lower().endswith(extension.lower()):
                    files.append(os.path.join(directory, file))
            
            if sort_files:
                files.sort()
            
            return files
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos {extension} de {directory}: {e}")
            return []