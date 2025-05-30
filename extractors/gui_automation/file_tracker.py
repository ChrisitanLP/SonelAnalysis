import os
import re
import json
import datetime
from pathlib import Path
from config.logger import logger
from utils.gui_helpers import GUIHelpers

class FileTracker:
    def __init__(self, parent_extractor):
        """
        Inicializa el rastreador de archivos
        
        Args:
            parent_extractor: Referencia al extractor GUI principal
        """
        self.parent = parent_extractor
        self.config = parent_extractor.config
        self.export_dir = parent_extractor.export_dir
        self.input_dir = parent_extractor.input_dir
        self.debug_mode = parent_extractor.debug_mode
        
        self.processed_files_json = os.path.join(
            self.export_dir,
            'procesados.json'
        )

    def ya_ha_sido_procesado(self, file_path):
        """
        Verifica si un archivo ya ha sido procesado anteriormente
        
        Args:
            file_path (str): Ruta completa del archivo a verificar
            
        Returns:
            bool: True si ya fue procesado, False si no
        """
        try:
            # Obtener nombre base del archivo sin ruta
            file_name = os.path.basename(file_path)
            
            # Verificar si existe el archivo JSON
            if not os.path.exists(self.processed_files_json):
                GUIHelpers.debug_log(self.debug_mode, f"Archivo de registro no existe: {self.processed_files_json}")
                return False
            
            # Leer archivo JSON
            with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            
            # Verificar si el archivo está registrado
            is_processed = file_name in processed_data
            
            if is_processed:
                fecha_procesamiento = processed_data[file_name].get('fecha', 'Fecha desconocida')
                GUIHelpers.debug_log(self.debug_mode, f"Archivo ya procesado: {file_name} (fecha: {fecha_procesamiento})")
            else:
                GUIHelpers.debug_log(self.debug_mode, f"Archivo NO procesado anteriormente: {file_name}")
                
            return is_processed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Error leyendo JSON de procesados: {e}")
            return False
        except Exception as e:
            logger.error(f"Error verificando archivo procesado {file_path}: {e}")
            return False

    def registrar_archivo_procesado(self, file_path):
        """
        Registra un archivo como procesado exitosamente
        
        Args:
            file_path (str): Ruta completa del archivo procesado
        """
        try:
            # Obtener información del archivo
            file_name = os.path.basename(file_path)
            file_stem = Path(file_path).stem
            file_ext = Path(file_path).suffix.lstrip('.')
            
            # Cargar datos existentes o crear estructura vacía
            processed_data = {}
            if os.path.exists(self.processed_files_json):
                try:
                    with open(self.processed_files_json, 'r', encoding='utf-8') as f:
                        processed_data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Archivo JSON corrupto, creando uno nuevo")
                    processed_data = {}
            
            # Agregar registro del archivo procesado
            processed_data[file_name] = {
                "nombre": file_stem,
                "extension": file_ext,
                "fecha": datetime.datetime.now().isoformat()
            }
            
            # Guardar archivo JSON actualizado
            os.makedirs(os.path.dirname(self.processed_files_json), exist_ok=True)
            
            with open(self.processed_files_json, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)
            
            GUIHelpers.debug_log(self.debug_mode, f"Archivo registrado como procesado: {file_name}")
            logger.info(f"📝 Registrado: {file_name}")
            
        except Exception as e:
            logger.error(f"Error registrando archivo procesado {file_path}: {e}")

    def obtener_estadisticas_procesados(self):
        """
        Obtiene estadísticas de archivos procesados
        
        Returns:
            dict: Estadísticas de procesamiento
        """
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

    def get_pqm_files(self):
        """
        Obtiene lista de archivos .pqm702 en el directorio de entrada
        
        Returns:
            Lista de rutas de archivos .pqm702
        """
        try:
            if not os.path.exists(self.input_dir):
                logger.error(f"❌ Directorio de entrada no existe: {self.input_dir}")
                return []
            
            pqm_files = []
            for file in os.listdir(self.input_dir):
                if file.lower().endswith('.pqm702'):
                    pqm_files.append(os.path.join(self.input_dir, file))
            
            # Ordenar archivos para procesamiento consistente
            pqm_files.sort()
            
            logger.info(f"📋 Encontrados {len(pqm_files)} archivos .pqm702 en {self.input_dir}")
            for i, file in enumerate(pqm_files, 1):
                logger.info(f"   {i}. {os.path.basename(file)}")
            
            return pqm_files
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos .pqm702: {e}")
            return []
        
    def generate_csv_filename(self, pqm_file_path):
        """
        ✅ Genera el nombre del archivo CSV basado en el archivo .pqm702
        
        Args:
            pqm_file_path: Ruta del archivo .pqm702 original
            
        Returns:
            str: Nombre del archivo CSV (sin extensión)
        """
        try:
            base_name = Path(pqm_file_path).stem

            # Limpiar caracteres especiales si está habilitado
            if self.config.get('FILES', {}).get('filename_cleanup', False):
                # Permitir letras con tilde, eñes, guiones, guiones bajos y espacios
                clean_name = re.sub(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ\-]", '', base_name, flags=re.UNICODE)
                clean_name = clean_name.strip()
                if clean_name:
                    base_name = clean_name

            GUIHelpers.debug_log(f"Nombre CSV generado: {base_name}.csv")
            return base_name

        except Exception as e:
            logger.error(f"Error generando nombre CSV: {e}")
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"export_{timestamp}"