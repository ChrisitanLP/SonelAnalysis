# NUEVO ARCHIVO: core/utils/coordinates_utils.py

import json
import os
from config.logger import logger

class CoordinatesUtils:
    """Utilidades para manejo de coordenadas de elementos de interfaz"""
    
    @staticmethod
    def load_coordinates(coordinates_file_path):
        """
        Carga coordenadas desde un archivo JSON
        
        Args:
            coordinates_file_path: Ruta al archivo JSON
            
        Returns:
            dict: Coordenadas cargadas o diccionario vacío si hay error
        """
        try:
            if not os.path.exists(coordinates_file_path):
                logger.warning(f"⚠️ Archivo de coordenadas no encontrado: {coordinates_file_path}")
                return {}
            
            with open(coordinates_file_path, 'r', encoding='utf-8') as f:
                coordinates = json.load(f)
            
            logger.info(f"✅ Coordenadas cargadas: {len(coordinates)} elementos desde {coordinates_file_path}")
            return coordinates
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando JSON de coordenadas: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Error cargando coordenadas: {e}")
            return {}
    
    @staticmethod
    def save_coordinates(coordinates_data, coordinates_file_path):
        """
        Guarda coordenadas en un archivo JSON
        
        Args:
            coordinates_data: Diccionario con coordenadas
            coordinates_file_path: Ruta del archivo de destino
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(coordinates_file_path), exist_ok=True)
            
            with open(coordinates_file_path, 'w', encoding='utf-8') as f:
                json.dump(coordinates_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"✅ Coordenadas guardadas: {len(coordinates_data)} elementos en {coordinates_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando coordenadas: {e}")
            return False
    
    @staticmethod
    def validate_coordinates_structure(coordinates_data):
        """
        Valida la estructura básica de las coordenadas
        
        Args:
            coordinates_data: Diccionario con coordenadas
            
        Returns:
            tuple: (bool, list) - (es_valido, errores_encontrados)
        """
        errors = []
        
        if not isinstance(coordinates_data, dict):
            errors.append("Las coordenadas deben ser un diccionario")
            return False, errors
        
        for key, coord_info in coordinates_data.items():
            if not isinstance(coord_info, dict):
                errors.append(f"Coordenada '{key}': debe ser un diccionario")
                continue
            
            # Validar campos obligatorios
            required_fields = ['x', 'y']
            for field in required_fields:
                if field not in coord_info:
                    errors.append(f"Coordenada '{key}': falta campo obligatorio '{field}'")
                elif not isinstance(coord_info[field], (int, float)):
                    errors.append(f"Coordenada '{key}': campo '{field}' debe ser numérico")
            
            # Validar campos opcionales
            if 'rect' in coord_info:
                rect = coord_info['rect']
                if isinstance(rect, dict):
                    rect_fields = ['left', 'top', 'right', 'bottom']
                    for rect_field in rect_fields:
                        if rect_field in rect and not isinstance(rect[rect_field], (int, float)):
                            errors.append(f"Coordenada '{key}': rect.{rect_field} debe ser numérico")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def get_coordinate_center(coord_info):
        """
        Obtiene el centro de una coordenada
        
        Args:
            coord_info: Información de coordenada con 'x', 'y' o 'rect'
            
        Returns:
            tuple: (x, y) del centro
        """
        if 'x' in coord_info and 'y' in coord_info:
            return coord_info['x'], coord_info['y']
        elif 'rect' in coord_info:
            rect = coord_info['rect']
            center_x = (rect['left'] + rect['right']) // 2
            center_y = (rect['top'] + rect['bottom']) // 2
            return center_x, center_y
        else:
            raise ValueError("Coordenada no válida: falta 'x','y' o 'rect'")
    
    @staticmethod
    def merge_coordinates(base_coords, new_coords):
        """
        Combina dos conjuntos de coordenadas, dando prioridad a las nuevas
        
        Args:
            base_coords: Coordenadas base
            new_coords: Coordenadas nuevas (tienen prioridad)
            
        Returns:
            dict: Coordenadas combinadas
        """
        merged = base_coords.copy()
        merged.update(new_coords)
        return merged
    
    @staticmethod
    def filter_coordinates_by_keys(coordinates_data, keys_to_keep):
        """
        Filtra coordenadas manteniendo solo las claves especificadas
        
        Args:
            coordinates_data: Diccionario con todas las coordenadas
            keys_to_keep: Lista de claves a mantener
            
        Returns:
            dict: Coordenadas filtradas
        """
        return {key: coordinates_data[key] for key in keys_to_keep if key in coordinates_data}
    
    @staticmethod
    def get_coordinates_summary(coordinates_data):
        """
        Genera un resumen de las coordenadas disponibles
        
        Args:
            coordinates_data: Diccionario con coordenadas
            
        Returns:
            dict: Resumen con estadísticas
        """
        if not coordinates_data:
            return {
                "total_elements": 0,
                "elements_with_text": 0,
                "elements_with_rect": 0,
                "element_types": {}
            }
        
        elements_with_text = sum(1 for coord in coordinates_data.values() 
                               if isinstance(coord, dict) and coord.get('texto', '').strip())
        
        elements_with_rect = sum(1 for coord in coordinates_data.values() 
                               if isinstance(coord, dict) and 'rect' in coord)
        
        # Categorizar por prefijo del nombre
        element_types = {}
        for key in coordinates_data.keys():
            prefix = key.split('_')[0] if '_' in key else 'Other'
            element_types[prefix] = element_types.get(prefix, 0) + 1
        
        return {
            "total_elements": len(coordinates_data),
            "elements_with_text": elements_with_text,
            "elements_with_rect": elements_with_rect,
            "element_types": element_types
        }