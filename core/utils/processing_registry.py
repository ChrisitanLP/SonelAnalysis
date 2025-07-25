# core/utils/processing_registry.py
import os
import json
import hashlib
from enum import Enum
from datetime import datetime
from config.logger import logger
from typing import Dict, List, Tuple

class ProcessingStatus(Enum):
    """Estados posibles de procesamiento de archivos"""
    PENDING = "pendiente"
    SUCCESS = "exitoso"
    ERROR = "con_errores"
    SKIPPED = "omitido"
    PROCESSING = "processing"

class ProcessingRegistry:
    """Gestor del registro de archivos procesados"""
    
    def __init__(self, registry_file: str = "registro_procesamiento.json"):
        """
        Inicializa el registro de procesamiento
        
        Args:
            registry_file: Nombre del archivo de registro
        """
        self.registry_file = registry_file
        self.registry_data = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """
        Carga el registro desde el archivo JSON
        
        Returns:
            dict: Datos del registro
        """
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"📋 Registro de procesamiento cargado: {len(data.get('files', {}))} archivos registrados")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"⚠️ Error al cargar registro, creando uno nuevo: {e}")
        
        # Crear estructura inicial
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "files": {}
        }
    
    def _save_registry(self):
        """Guarda el registro en el archivo JSON"""
        try:
            self.registry_data["last_updated"] = datetime.now().isoformat()
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registry_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 Registro guardado en {self.registry_file}")
        except IOError as e:
            logger.error(f"❌ Error al guardar registro: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        Calcula el hash MD5 de un archivo para detectar cambios
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            str: Hash MD5 del archivo
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError as e:
            logger.error(f"❌ Error al calcular hash de {file_path}: {e}")
            return ""
    
    def _get_file_info(self, file_path: str) -> Dict:
        """
        Obtiene información detallada de un archivo
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            dict: Información del archivo
        """
        try:
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "hash": self._get_file_hash(file_path)
            }
        except OSError as e:
            logger.error(f"❌ Error al obtener información de {file_path}: {e}")
            return {}
    
    def should_process_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Determina si un archivo debe ser procesado
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            tuple: (debe_procesar, razon)
        """
        file_key = os.path.abspath(file_path)
        
        # Si el archivo no existe en el registro, debe procesarse
        if file_key not in self.registry_data["files"]:
            return True, "archivo_nuevo"
        
        file_record = self.registry_data["files"][file_key]
        
        # Si el estado anterior fue error, permitir reprocesamiento
        if file_record.get("status") == ProcessingStatus.ERROR.value:
            return True, "reprocesar_error"
            
        # Si el estado fue exitoso, verificar si el archivo cambió
        if file_record.get("status") == ProcessingStatus.SUCCESS.value:
            current_info = self._get_file_info(file_path)
            
            # Si no se puede obtener info del archivo, mejor procesarlo
            if not current_info:
                return True, "info_no_disponible"
            
            # Comparar hash para detectar cambios
            stored_hash = file_record.get("file_info", {}).get("hash", "")
            current_hash = current_info.get("hash", "")
            
            if stored_hash != current_hash:
                return True, "archivo_modificado"
            
            # Si también queremos verificar fecha de modificación como backup
            stored_modified = file_record.get("file_info", {}).get("modified", "")
            current_modified = current_info.get("modified", "")
            
            if stored_modified != current_modified:
                return True, "fecha_modificada"
            
            # El archivo no ha cambiado y fue procesado exitosamente
            return False, "ya_procesado"
        
        # Para cualquier otro estado, procesar por seguridad
        return True, "estado_desconocido"
    
    def register_processing_start(self, file_path: str, client_code: str = None):
        """
        Registra el inicio del procesamiento de un archivo
        
        Args:
            file_path: Ruta al archivo
            client_code: Código del cliente (opcional)
        """
        file_key = os.path.abspath(file_path)
        file_info = self._get_file_info(file_path)
        
        self.registry_data["files"][file_key] = {
            "filename": os.path.basename(file_path),
            "client_code": client_code,
            "status": ProcessingStatus.PENDING.value,
            "processing_started": datetime.now().isoformat(),
            "processing_completed": None,
            "file_info": file_info,
            "error_message": None,
            "attempts": self.registry_data["files"].get(file_key, {}).get("attempts", 0) + 1
        }
        
        self._save_registry()
        logger.info(f"📝 Iniciando procesamiento registrado: {os.path.basename(file_path)}")
    
    def register_processing_success(self, file_path: str, additional_info: Dict = None):
        """
        Registra el procesamiento exitoso de un archivo
        
        Args:
            file_path: Ruta al archivo
            additional_info: Información adicional (opcional)
        """
        file_key = os.path.abspath(file_path)
        
        if file_key in self.registry_data["files"]:
            self.registry_data["files"][file_key].update({
                "status": ProcessingStatus.SUCCESS.value,
                "processing_completed": datetime.now().isoformat(),
                "error_message": None
            })
            
            # 🔄 MEJORA: Guardar additional_info de manera estructurada
            if additional_info:
                self.registry_data["files"][file_key]["additional_info"] = additional_info
            
            self._save_registry()
            
            # 🔄 MEJORA: Log mejorado con información de tiempo y registros
            rows = additional_info.get("rows_processed", 0) if additional_info else 0
            time_taken = additional_info.get("processing_time_seconds", 0) if additional_info else 0
            logger.info(f"✅ Procesamiento exitoso registrado: {os.path.basename(file_path)} | {rows} registros | {time_taken:.2f}s")

    def register_processing_error(self, file_path: str, error_message: str, additional_info: Dict = None):
        """
        Registra un error en el procesamiento de un archivo
        
        Args:
            file_path: Ruta al archivo
            error_message: Mensaje de error
            additional_info: Información adicional del procesamiento (opcional)
        """
        file_key = os.path.abspath(file_path)
        
        if file_key in self.registry_data["files"]:
            self.registry_data["files"][file_key].update({
                "status": ProcessingStatus.ERROR.value,
                "processing_completed": datetime.now().isoformat(),
                "error_message": error_message
            })
            
            # 🔄 MEJORA: Guardar additional_info incluso en caso de error
            if additional_info:
                self.registry_data["files"][file_key]["additional_info"] = additional_info
            
            self._save_registry()
            
            # 🔄 MEJORA: Log con información de tiempo si está disponible
            time_taken = additional_info.get("processing_time_seconds", 0) if additional_info else 0
            time_info = f" | {time_taken:.2f}s" if time_taken > 0 else ""
            logger.error(f"❌ Error de procesamiento registrado: {os.path.basename(file_path)}{time_info} - {error_message}")

    def register_processing_skipped(self, file_path: str, reason: str):
        """
        Registra que un archivo fue omitido
        
        Args:
            file_path: Ruta al archivo
            reason: Razón por la cual fue omitido
        """
        file_key = os.path.abspath(file_path)
        
        # Solo actualizar si ya existe en el registro
        if file_key in self.registry_data["files"]:
            self.registry_data["files"][file_key]["last_checked"] = datetime.now().isoformat()
            self.registry_data["files"][file_key]["skip_reason"] = reason
            self._save_registry()
        
        logger.info(f"⏭️ Archivo omitido: {os.path.basename(file_path)} - {reason}")
    
    def is_file_registered_with_status(self, file_path: str, status: ProcessingStatus) -> bool:
        """
        Verifica si un archivo está registrado con un estado específico
        
        Args:
            file_path: Ruta al archivo
            status: Estado a verificar
            
        Returns:
            bool: True si el archivo está registrado con ese estado
        """
        file_key = os.path.abspath(file_path)
        
        if file_key not in self.registry_data.get("files", {}):
            return False
        
        file_data = self.registry_data["files"][file_key]
        return file_data.get("status") == status.value

    def get_processing_stats(self) -> Dict:
        """
        Obtiene estadísticas del procesamiento
        
        Returns:
            dict: Estadísticas de procesamiento
        """
        files = self.registry_data.get("files", {})
        stats = {
            "total_files": len(files),
            "successful": 0,
            "errors": 0,
            "pending": 0,
            "skipped": 0
        }
        
        for file_data in files.values():
            status = file_data.get("status", "")
            if status == ProcessingStatus.SUCCESS.value:
                stats["successful"] += 1
            elif status == ProcessingStatus.ERROR.value:
                stats["errors"] += 1
            elif status == ProcessingStatus.PENDING.value:
                stats["pending"] += 1
            elif status == ProcessingStatus.SKIPPED.value:
                stats["skipped"] += 1
        
        return stats
    
    def get_files_by_status(self, status: ProcessingStatus) -> List[str]:
        """
        Obtiene archivos por estado
        
        Args:
            status: Estado a filtrar
            
        Returns:
            list: Lista de rutas de archivos con el estado especificado
        """
        files = []
        for file_path, file_data in self.registry_data.get("files", {}).items():
            if file_data.get("status") == status.value:
                files.append(file_path)
        return files
    
    def cleanup_missing_files(self) -> int:
        """
        Limpia del registro archivos que ya no existen
        
        Returns:
            int: Número de archivos eliminados del registro
        """
        files_to_remove = []
        
        for file_path in self.registry_data.get("files", {}):
            if not os.path.exists(file_path):
                files_to_remove.append(file_path)
        
        for file_path in files_to_remove:
            del self.registry_data["files"][file_path]
            logger.info(f"🗑️ Archivo eliminado del registro (no existe): {os.path.basename(file_path)}")
        
        if files_to_remove:
            self._save_registry()
        
        return len(files_to_remove)
    
    def print_status_report(self):
        """Imprime un reporte del estado del registro"""
        stats = self.get_processing_stats()
        
        logger.info("📊 === REPORTE DE ESTADO DEL REGISTRO ===")
        logger.info(f"Total de archivos: {stats['total_files']}")
        logger.info(f"Procesados exitosamente: {stats['successful']}")
        logger.info(f"Con errores: {stats['errors']}")
        logger.info(f"Pendientes: {stats['pending']}")
        logger.info(f"Omitidos: {stats['skipped']}")
        
        # Mostrar archivos con errores si los hay
        error_files = self.get_files_by_status(ProcessingStatus.ERROR)
        if error_files:
            logger.info("❌ Archivos con errores:")
            for file_path in error_files[:5]:  # Mostrar solo los primeros 5
                file_data = self.registry_data["files"][file_path]
                error_msg = file_data.get("error_message", "Sin mensaje")
                logger.info(f"  - {os.path.basename(file_path)}: {error_msg}")
            
            if len(error_files) > 5:
                logger.info(f"  ... y {len(error_files) - 5} archivos más con errores")

    def register_batch_processing_time(self, total_time_seconds: float, start_time: datetime, end_time: datetime):
        """
        Registra el tiempo total de procesamiento del batch
        
        Args:
            total_time_seconds: Tiempo total en segundos
            start_time: Tiempo de inicio del batch
            end_time: Tiempo de finalización del batch
        """
        self.registry_data["batch_processing"] = {
            "total_time_seconds": total_time_seconds,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "recorded_at": datetime.now().isoformat()
        }
        
        self._save_registry()
        logger.info(f"⏱️ Tiempo total de batch registrado: {total_time_seconds:.2f} segundos")

    def get_batch_processing_time(self) -> float:
        """
        Obtiene el tiempo total de procesamiento del batch
        
        Returns:
            float: Tiempo total en segundos, o 0 si no está disponible
        """
        batch_data = self.registry_data.get("batch_processing", {})
        return batch_data.get("total_time_seconds", 0)

    def get_batch_processing_info(self) -> Dict:
        """
        Obtiene información completa del procesamiento del batch
        
        Returns:
            dict: Información del batch o diccionario vacío si no está disponible
        """
        return self.registry_data.get("batch_processing", {})