import os
import json
import datetime
from pathlib import Path
from config.logger import logger
from utils.gui_helpers import GUIHelpers


class FileTracker:
    def __init__(self, config):
        self.config = config
        self.export_dir = config['PATHS'].get('export_dir', 
                                            'D:/Universidad/8vo Semestre/Practicas/Sonel/data/archivos_csv')
        
        self.processed_files_json = os.path.join(
            self.export_dir,
            'procesados.json'
        )
        
        self.debug_mode = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        
        os.makedirs(os.path.dirname(self.processed_files_json), exist_ok=True)

    def ya_ha_sido_procesado(self, file_path):
        try:
            file_name = os.path.basename(file_path)
            
            if not os.path.exists(self.processed_files_json):
                GUIHelpers.debug_log(f"Archivo de registro no existe: {self.processed_files_json}", self.debug_mode)
                return False
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            is_processed = file_name in processed_data
            
            if is_processed:
                fecha_procesamiento = processed_data[file_name].get('fecha', 'Fecha desconocida')
                GUIHelpers.debug_log(f"Archivo ya procesado: {file_name} (fecha: {fecha_procesamiento})", self.debug_mode)
            else:
                GUIHelpers.debug_log(f"Archivo NO procesado anteriormente: {file_name}", self.debug_mode)
                
            return is_processed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Error leyendo JSON de procesados: {e}")
            return False
        except Exception as e:
            logger.error(f"Error verificando archivo procesado {file_path}: {e}")
            return False

    def registrar_archivo_procesado(self, file_path):
        try:
            file_name = os.path.basename(file_path)
            file_stem = Path(file_path).stem
            file_ext = Path(file_path).suffix.lstrip('.')
            
            processed_data = {}
            if os.path.exists(self.processed_files_json):
                try:
                    with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                        processed_data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Archivo JSON corrupto, creando uno nuevo")
                    processed_data = {}
            
            processed_data[file_name] = {
                "nombre": file_stem,
                "extension": file_ext,
                "fecha": datetime.datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.processed_files_json), exist_ok=True)
            
            with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)
            
            GUIHelpers.debug_log(f"Archivo registrado como procesado: {file_name}", self.debug_mode)
            logger.info(f"📝 Registrado: {file_name}")
            
        except Exception as e:
            logger.error(f"Error registrando archivo procesado {file_path}: {e}")

    def obtener_estadisticas_procesados(self):
        try:
            if not os.path.exists(self.processed_files_json):
                return {"total": 0, "archivos": []}
            
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            return {
                "total": len(processed_data),
                "archivos": list(processed_data.keys()),
                "ultimo_procesado": max(
                    processed_data.values(), 
                    key=lambda x: x.get('fecha', ''), 
                    default={}
                ).get('fecha', 'N/A') if processed_data else 'N/A'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"total": 0, "archivos": [], "error": str(e)}

    def limpiar_registros_procesados(self):
        try:
            if os.path.exists(self.processed_files_json):
                os.remove(self.processed_files_json)
                logger.info("🧹 Registros de archivos procesados limpiados")
                return True
            return False
        except Exception as e:
            logger.error(f"Error limpiando registros: {e}")
            return False