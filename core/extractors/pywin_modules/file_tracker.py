import os
import json
from pathlib import Path
from datetime import datetime

class FileTracker:
    """Maneja el seguimiento y registro de archivos procesados"""
    
    def __init__(self, paths, logger):
        self.PATHS = paths
        self.logger = logger
        export_dir = self.PATHS.get('export_dir', self.PATHS.get('export_dir'))
        if not export_dir:
            export_dir = self.PATHS.get('reprocess_dir', self.PATHS.get('reprocess_dir'))
        
        os.makedirs(export_dir, exist_ok=True)  
        self.processed_files_json = os.path.join(export_dir, 'procesados_global.json')

    def _generate_file_key(self, file_path):
        """
        Genera clave única basada SOLO en el contenido del archivo para evitar duplicados globales
        
        Args:
            file_path (str): Ruta completa del archivo
            
        Returns:
            str: Clave única para identificar el archivo globalmente basada en contenido
        """
        import hashlib
        
        # Usar solo el nombre del archivo como identificador principal
        filename = os.path.basename(file_path)
        
        # Generar hash basado en CONTENIDO del archivo, no en metadatos del sistema
        try:
            if os.path.exists(file_path):
                # Leer una muestra del contenido del archivo para generar hash único
                with open(file_path, 'rb') as f:
                    # Leer los primeros 8KB del archivo para generar fingerprint
                    content_sample = f.read(8192)
                    
                    # Si el archivo es muy pequeño, leer todo
                    if len(content_sample) < 8192:
                        f.seek(0)
                        content_sample = f.read()
                    
                    # También leer los últimos 1KB si el archivo es grande
                    file_size = f.seek(0, 2)  # Ir al final para obtener tamaño
                    if file_size > 8192:
                        f.seek(-min(1024, file_size), 2)  # Leer últimos 1KB
                        content_sample += f.read()
                    
                    # Generar hash del contenido muestreado
                    content_hash = hashlib.md5(content_sample).hexdigest()[:12]
                    
                    # Incluir el tamaño del archivo como validación adicional
                    size_hash = hashlib.md5(str(file_size).encode()).hexdigest()[:4]
                    
                    return f"{filename}_{content_hash}_{size_hash}"
            else:
                # Si el archivo no existe, usar solo el nombre (esto es un fallback)
                self.logger.warning(f"Archivo no existe para generar clave: {file_path}")
                return filename
                
        except Exception as e:
            self.logger.warning(f"No se pudo generar hash de contenido para {filename}: {e}")
            # Fallback: usar solo el nombre del archivo
            return filename
    
    def get_processing_statistics(self):
        """
        Obtiene estadísticas de archivos procesados con la nueva estructura
        """
        try:
            if not os.path.exists(self.processed_files_json):
                self.logger.info(f"📄 Archivo de registro no existe aún: {self.processed_files_json}")
                return {"total": 0, "archivos": []}
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            # Obtener la sección 'files' con la nueva estructura
            files_info = processed_data.get("files", {})
            
            if not files_info:
                self.logger.info("📊 No hay archivos procesados registrados")
                return {"total": 0, "archivos": []}
            
            # Extraer nombres de archivo para compatibilidad
            archivos_procesados = []
            for file_key, file_info in files_info.items():
                filename = file_info.get("filename", file_key.split('_')[0] if '_' in file_key else file_key)
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
            
            # Log de estadísticas para debugging
            self.logger.info(f"📊 Estadísticas cargadas - Total: {len(files_info)}, Último: {ultimo_procesado}")
            
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

            # nueva clave basada en contenido del archivo
            file_key = self._generate_file_key(file_path)

            # Verificar TODAS las claves existentes para detectar duplicados por nombre
            filename = os.path.basename(file_path)
            
            # Buscar si ya existe un archivo con el mismo nombre (independiente de la clave)
            existing_entries = []
            for existing_key, entry in files_info.items():
                if entry.get("filename") == filename:
                    existing_entries.append((existing_key, entry))
            
            # Mostrar información de duplicados encontrados
            if len(existing_entries) > 1:
                self.logger.info(f"🔍 Archivo '{filename}' encontrado en {len(existing_entries)} registros:")
                for key, entry in existing_entries:
                    status = entry.get("status", "")
                    paths = entry.get("source_paths", [])
                    self.logger.info(f"   - Clave: {key}, Estado: {status}, Rutas: {len(paths)}")

            # Verificar si el archivo está en el registro usando la nueva clave
            entry = files_info.get(file_key)
            if entry:
                status = entry.get("status", "")
                csv_verified = entry.get("csv_output", {}).get("verified", False)
                source_paths = entry.get("source_paths", [])

                if status == "exitoso" and csv_verified:
                    self.logger.info(f"⏭️ Saltando {filename} (ya procesado exitosamente)")
                    self.logger.info(f"   🔑 Clave: {file_key}")
                    self.logger.info(f"   📁 Rutas conocidas: {len(source_paths)}")
                    if len(source_paths) > 0:
                        self.logger.info(f"   📍 Primera ruta: {source_paths[0]}")
                    return True
                else:
                    self.logger.info(f"🔁 Reintentando procesamiento de {filename}")
                    self.logger.info(f"   🔑 Clave: {file_key}")
                    self.logger.info(f"   ⚠️ Razón: Estado='{status}', CSV_verificado={csv_verified}")
                    return False
            else:
                # Verificar si existe con otra clave (archivo movido o copiado)
                for existing_key, existing_entry in existing_entries:
                    if existing_key != file_key:  # Es una clave diferente
                        status = existing_entry.get("status", "")
                        csv_verified = existing_entry.get("csv_output", {}).get("verified", False)
                        
                        if status == "exitoso" and csv_verified:
                            self.logger.info(f"⏭️ Saltando {filename} (ya procesado con otra clave)")
                            self.logger.info(f"   🔑 Clave actual: {file_key}")
                            self.logger.info(f"   🔑 Clave existente: {existing_key}")
                            self.logger.info(f"   📝 El archivo será registrado con la nueva clave pero no reprocesado")
                            
                            # Registrar la nueva ruta en el archivo existente
                            self._update_source_paths(existing_key, file_path, files_info, processed_data)
                            return True

            return False

        except json.JSONDecodeError as e:
            self.logger.warning(f"Error leyendo JSON de procesados: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error verificando archivo procesado {file_path}: {e}")
            return False

    def _update_source_paths(self, existing_key, new_file_path, files_info, processed_data):
        """
        Actualiza las rutas de origen de un archivo ya procesado
        
        Args:
            existing_key (str): Clave del archivo existente en el registro
            new_file_path (str): Nueva ruta encontrada para el archivo
            files_info (dict): Información de archivos procesados
            processed_data (dict): Datos completos del procesamiento
        """
        try:
            existing_entry = files_info[existing_key]
            source_paths = existing_entry.get("source_paths", [])
            new_path_normalized = os.path.abspath(new_file_path)
            
            # Agregar nueva ruta si no existe
            if new_path_normalized not in source_paths:
                source_paths.append(new_path_normalized)
                existing_entry["source_paths"] = source_paths
                existing_entry["last_seen_path"] = new_path_normalized
                existing_entry["last_updated"] = datetime.now().isoformat()
                
                # Guardar cambios
                with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, indent=2, ensure_ascii=False)
                
                filename = os.path.basename(new_file_path)
                self.logger.info(f"✅ Ruta actualizada para {filename}")
                self.logger.info(f"   📁 Nueva ruta registrada: {new_path_normalized}")
                self.logger.info(f"   📊 Total rutas conocidas: {len(source_paths)}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error actualizando rutas de origen: {e}")

    def register_processed_file(self, file_path, resultado_exitoso=True, csv_path=None, processing_time=None, error_message=None, additional_info=None):
        """
        Registra un archivo como procesado con información detallada y robusta.
        Evita duplicados verificando por nombre de archivo.
        
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
            
            # nueva clave global basada en contenido
            file_key = self._generate_file_key(file_path)
            
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
                processed_data["version"] = "1.2"  # Nueva versión
                processed_data["created"] = datetime.now().isoformat()
            
            if "files" not in processed_data:
                processed_data["files"] = {}
            
            files_info = processed_data["files"]
            
            # Verificar si ya existe un registro del mismo archivo con otra clave
            existing_entries = []
            for existing_key, entry in files_info.items():
                if entry.get("filename") == file_name and existing_key != file_key:
                    existing_entries.append((existing_key, entry))
            
            # Si existe con otra clave, consolidar información
            if existing_entries:
                self.logger.info(f"🔄 Consolidando registro existente para {file_name}")
                
                # Tomar el primer registro existente como base
                base_key, base_entry = existing_entries[0]
                
                # Actualizar rutas de origen
                existing_paths = base_entry.get("source_paths", [])
                file_path_normalized = os.path.abspath(file_path)
                
                if file_path_normalized not in existing_paths:
                    existing_paths.append(file_path_normalized)
                
                # Actualizar información con los nuevos datos si el procesamiento fue exitoso
                if resultado_exitoso:
                    base_entry.update({
                        "status": "exitoso",
                        "processing_completed": datetime.now().isoformat(),
                        "processing_time_seconds": processing_time,
                        "source_paths": existing_paths,
                        "current_source_path": file_path_normalized,
                        "attempts": base_entry.get("attempts", 0) + 1,
                        "error_message": None,
                        "last_updated": datetime.now().isoformat()
                    })
                    
                    # Actualizar información del CSV
                    if csv_path and os.path.exists(csv_path):
                        try:
                            csv_info = self._get_file_info_basic(csv_path)
                            base_entry["csv_output"] = {
                                "filename": os.path.basename(csv_path),
                                "path": csv_path,
                                "size_bytes": csv_info.get("size", 0),
                                "created": csv_info.get("modified", datetime.now().isoformat()),
                                "verified": True
                            }
                        except Exception as e:
                            self.logger.warning(f"Error obteniendo info de CSV {csv_path}: {e}")
                            base_entry["csv_output"] = {
                                "filename": os.path.basename(csv_path) if csv_path else "error.csv",
                                "verified": False,
                                "error": f"Error obteniendo información: {e}"
                            }
                
                # Agregar información adicional si está disponible
                if additional_info:
                    base_entry["additional_info"] = additional_info
                
                # Actualizar timestamp
                processed_data["last_updated"] = datetime.now().isoformat()
                
                # Eliminar registros duplicados y mantener solo el consolidado
                for dup_key, _ in existing_entries[1:]:  # Eliminar duplicados adicionales
                    if dup_key in files_info:
                        del files_info[dup_key]
                        self.logger.info(f"🗑️ Eliminado registro duplicado con clave: {dup_key}")
                
                self.logger.info(f"✅ Registro consolidado para {file_name} con clave: {base_key}")
                
            else:
                # Proceder normalmente
                try:
                    file_info = self._get_file_info_basic(file_path)
                except Exception as e:
                    self.logger.warning(f"Error obteniendo info de archivo {file_name}: {e}")
                    file_info = {"size": 0, "modified": datetime.now().isoformat()}
                
                # Crear nuevo registro
                registro = {
                    "filename": file_name,
                    "file_stem": file_stem,
                    "extension": file_ext,
                    "status": "exitoso" if resultado_exitoso else "con_errores",
                    "processing_completed": datetime.now().isoformat(),
                    "processing_time_seconds": processing_time,
                    "file_info": file_info,
                    "attempts": 1,
                    "error_message": error_message if not resultado_exitoso else None,
                    "source_paths": [os.path.abspath(file_path)],
                    "current_source_path": os.path.abspath(file_path)
                }
                
                # Agregar información del CSV si está disponible
                if csv_path and os.path.exists(csv_path):
                    try:
                        csv_info = self._get_file_info_basic(csv_path)
                        registro["csv_output"] = {
                            "filename": os.path.basename(csv_path),
                            "path": csv_path,
                            "size_bytes": csv_info.get("size", 0),
                            "created": csv_info.get("modified", datetime.now().isoformat()),
                            "verified": True
                        }
                    except Exception as e:
                        self.logger.warning(f"Error obteniendo info de CSV {csv_path}: {e}")
                        registro["csv_output"] = {
                            "filename": os.path.basename(csv_path) if csv_path else "error.csv",
                            "verified": False,
                            "error": f"Error obteniendo información: {e}"
                        }
                else:
                    registro["csv_output"] = {
                        "verified": False,
                        "error": "CSV no generado o no encontrado"
                    }
                
                # Agregar información adicional si está disponible
                if additional_info:
                    registro["additional_info"] = additional_info
                
                # nueva clave global basada en contenido
                files_info[file_key] = registro
                processed_data["last_updated"] = datetime.now().isoformat()
            
            # Guardar archivo JSON actualizado
            os.makedirs(os.path.dirname(self.processed_files_json), exist_ok=True)
            
            with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            # Log mejorado con más información
            time_info = f" | {processing_time:.2f}s" if processing_time > 0 else ""
            csv_info = f" (CSV: {os.path.basename(csv_path)})" if csv_path and os.path.exists(csv_path) else ""
            
            if resultado_exitoso:
                self.logger.info(f"✅ Procesamiento exitoso registrado: {file_name}{time_info}{csv_info} [Clave: {file_key}]")
            else:
                self.logger.error(f"❌ Error de procesamiento registrado: {file_name}{time_info} - {error_message} [Clave: {file_key}]")
            
            # Log de confirmación de guardado
            self.logger.debug(f"📄 Registro actualizado en: {self.processed_files_json}")
            
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
                self.logger.debug(f"📄 Archivo de registro no existe: {self.processed_files_json}")
                return {}
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            files_data = data.get("files", {})
            self.logger.debug(f"📊 Cargados {len(files_data)} registros de archivos procesados")
            
            # Devolver solo la sección 'files' de la nueva estructura
            return files_data
        except Exception as e:
            self.logger.warning(f"⚠️ Error cargando datos procesados: {e}")
            return {}
        
    def _get_file_info_basic(self, file_path):
        """
        Obtiene información básica del archivo sin depender de FileManager
        """
        try:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                return {
                    "size": stat_info.st_size,
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat() if hasattr(stat_info, 'st_ctime') else None
                }
            else:
                return {"size": 0, "modified": datetime.now().isoformat()}
        except Exception as e:
            return {"size": 0, "modified": datetime.now().isoformat(), "error": str(e)}
