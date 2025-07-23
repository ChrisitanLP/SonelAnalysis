import os
import json
from pathlib import Path
from datetime import datetime

class FileTracker:
    """Maneja el seguimiento y registro de archivos procesados"""
    
    def __init__(self, paths, logger):
        self.PATHS = paths
        self.logger = logger
        self.processed_files_json = os.path.join(
            self.PATHS['process_file_dir'],
            'procesados.json'
        )
    
    def get_processing_statistics(self):
        """
        Obtiene estadísticas de archivos procesados con la nueva estructura
        
        Returns:
            dict: Estadísticas de procesamiento
        """
        try:
            if not os.path.exists(self.processed_files_json):
                return {"total": 0, "archivos": []}
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            # Obtener la sección 'files' de la nueva estructura
            files_info = processed_data.get("files", {})
            
            # Extraer solo los nombres de archivo para compatibilidad
            archivos_procesados = []
            for file_path, file_info in files_info.items():
                filename = file_info.get("filename", os.path.basename(file_path))
                archivos_procesados.append(filename)
            
            # Encontrar el último procesado
            ultimo_procesado = "N/A"
            if files_info:
                latest_entry = max(
                    files_info.values(), 
                    key=lambda x: x.get('processing_completed', ''), 
                    default={}
                )
                ultimo_procesado = latest_entry.get('processing_completed', 'N/A')
            
            return {
                "total": len(files_info),
                "archivos": archivos_procesados,
                "ultimo_procesado": ultimo_procesado
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {"total": 0, "archivos": [], "error": str(e)}

    def is_already_processed(self, file_path):
        """
        Verifica si un archivo ya ha sido procesado anteriormente usando la nueva estructura JSON.

        Args:
            file_path (str): Ruta completa del archivo a verificar

        Returns:
            bool: True si ya fue procesado exitosamente, False si debe reintentarse
        """
        try:
            # Verificar si existe el archivo JSON
            if not os.path.exists(self.processed_files_json):
                return False

            # Leer archivo JSON
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)

            # Validar que existe la sección 'files' en la nueva estructura
            files_info = processed_data.get("files", {})
            if not files_info:
                return False

            # Normalizar la ruta del archivo para comparación
            file_path_normalized = os.path.abspath(file_path)

            # Verificar si el archivo está en el registro usando su ruta completa
            entry = files_info.get(file_path_normalized)
            if entry:
                status = entry.get("status", "")
                csv_verified = entry.get("csv_output", {}).get("verified", False)

                if status == "exitoso" and csv_verified:
                    self.logger.info(f"⏭️  Saltando {os.path.basename(file_path)} (ya procesado exitosamente)")
                    return True
                else:
                    self.logger.info(f"🔁 Reintentando procesamiento de {os.path.basename(file_path)} (procesamiento anterior fallido o incompleto)")
                    return False

            return False

        except json.JSONDecodeError as e:
            self.logger.warning(f"Error leyendo JSON de procesados: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error verificando archivo procesado {file_path}: {e}")
            return False

    def register_processed_file(self, file_path, resultado_exitoso=True, csv_path=None, processing_time=None, error_message=None, additional_info=None):
        """
        Registra un archivo como procesado con información detallada y robusta
        
        Args:
            file_path (str): Ruta completa del archivo procesado
            resultado_exitoso (bool): Si el procesamiento fue exitoso
            csv_path (str): Ruta del archivo CSV generado (opcional)
            processing_time (float): Tiempo de procesamiento en segundos (opcional)
            error_message (str): Mensaje de error si el procesamiento falló (opcional)
            additional_info (dict): Información adicional del procesamiento (opcional)
        """
        # Capturar tiempo de finalización si no se proporciona
        if processing_time is None:
            processing_time = 0
        
        try:
            # Obtener información del archivo
            file_name = os.path.basename(file_path)
            file_stem = Path(file_path).stem
            file_ext = Path(file_path).suffix.lstrip('.')
            file_key = os.path.abspath(file_path)
            
            # Cargar datos existentes o crear estructura vacía
            processed_data = {}
            if os.path.exists(self.processed_files_json):
                try:
                    with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                        processed_data = json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning("Archivo JSON corrupto, creando uno nuevo")
                    processed_data = {}
            
            # Asegurar estructura del registro
            if "version" not in processed_data:
                processed_data["version"] = "1.0"
                processed_data["created"] = datetime.now().isoformat()
            
            if "files" not in processed_data:
                processed_data["files"] = {}
            
            # Obtener información detallada del archivo
            from .file_manager import FileManager
            file_manager = FileManager(self.PATHS, self.logger)
            file_info = file_manager.get_file_info(file_path)
            
            # Crear registro del archivo procesado con información extendida
            registro = {
                "filename": file_name,
                "file_stem": file_stem,
                "extension": file_ext,
                "status": "exitoso" if resultado_exitoso else "con_errores",
                "processing_completed": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "file_info": file_info,
                "attempts": processed_data.get("files", {}).get(file_key, {}).get("attempts", 0) + 1,
                "error_message": error_message if not resultado_exitoso else None
            }
            
            # Agregar información del CSV si está disponible
            if csv_path and os.path.exists(csv_path):
                csv_info = file_manager.get_file_info(csv_path)
                registro["csv_output"] = {
                    "filename": os.path.basename(csv_path),
                    "path": csv_path,
                    "size_bytes": csv_info.get("size", 0),
                    "created": csv_info.get("modified", datetime.now().isoformat()),
                    "verified": True
                }
            else:
                registro["csv_output"] = {
                    "verified": False,
                    "error": "CSV no generado o no encontrado"
                }
            
            # Agregar información adicional si está disponible
            if additional_info:
                registro["additional_info"] = additional_info
            
            # Agregar registro del archivo procesado usando la ruta absoluta como clave
            processed_data["files"][file_key] = registro
            processed_data["last_updated"] = datetime.now().isoformat()
            
            # Guardar archivo JSON actualizado
            os.makedirs(os.path.dirname(self.processed_files_json), exist_ok=True)
            
            with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            # Log mejorado con más información
            status = "✅" if resultado_exitoso else "❌"
            time_info = f" | {processing_time:.2f}s" if processing_time > 0 else ""
            csv_info = f" (CSV: {os.path.basename(csv_path)})" if csv_path and os.path.exists(csv_path) else ""
            
            if resultado_exitoso:
                self.logger.info(f"✅ Procesamiento exitoso registrado: {file_name}{time_info}{csv_info}")
            else:
                self.logger.error(f"❌ Error de procesamiento registrado: {file_name}{time_info} - {error_message}")
            
        except Exception as e:
            self.logger.error(f"❌ Error crítico registrando archivo procesado {file_path}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _load_processed_files_data(self):
        """
        Carga los datos de archivos procesados desde JSON con la nueva estructura
        
        Returns:
            dict: Datos de archivos procesados
        """
        try:
            if not os.path.exists(self.processed_files_json):
                return {}
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Devolver solo la sección 'files' de la nueva estructura
            return data.get("files", {})
        except Exception as e:
            self.logger.warning(f"⚠️ Error cargando datos procesados: {e}")
            return {}