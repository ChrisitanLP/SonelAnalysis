#sonel_extractor/utils/validators.py
import re
import os
import time
import hashlib
from config.logger import logger
from config.settings import COLUMN_PATTERNS

def validate_voltage_columns(df):
    """
    Verifica que el DataFrame contenga las columnas necesarias o similares
    Args:
        df: DataFrame a validar

    Returns:
        tuple: (bool, dict) - Validez del dataframe y mapeo de columnas encontradas
    """
    # Convertir todos los nombres de columnas a string para evitar errores con enteros
    df.columns = df.columns.astype(str)

    # Mapeo de nombres de columnas estándar a nombres encontrados
    column_mapping = {}

    # Procesar patrones en orden específico para evitar conflictos
    ordered_patterns = [
        'time', 'date', 'time_utc5',  # NUEVOS CAMPOS AGREGADOS
        'u_l1', 'u_l2', 'u_l3', 'u_l12',
        'i_l1', 'i_l2', 
        'p_l1', 'p_l2', 'p_l3', 'p_e',
        'q1_l1', 'q1_l2', 'q1_e',
        'sn_l1', 'sn_l2', 'sn_e',  # Procesar Sn antes que S
        's_l1', 's_l2', 's_e'      # Procesar S después
    ]

    for std_name in ordered_patterns:
        if std_name in COLUMN_PATTERNS:
            pattern = COLUMN_PATTERNS[std_name]
            # Buscar todas las columnas que coinciden con el patrón
            matched = [col for col in df.columns if re.search(pattern, col)]
            
            if matched:
                # Para potencia aparente S, asegurarnos de no tomar columnas Sn
                if std_name in ['s_l1', 's_l2', 's_e']:
                    # Filtrar columnas que contengan "Sn" (potencia aparente compleja)
                    filtered_matches = []
                    for col in matched:
                        # Verificar que no sea una columna ya asignada a Sn
                        if not any(col == column_mapping.get(sn_key) for sn_key in ['sn_l1', 'sn_l2', 'sn_e']):
                            # Verificar que no contenga "Sn" explícitamente
                            if not re.search(r'(?i)sn\s', col):
                                filtered_matches.append(col)
                    
                    if filtered_matches:
                        column_mapping[std_name] = filtered_matches[0]
                        logger.debug(f"Columna {std_name} mapeada a: {filtered_matches[0]} (filtrada de Sn)")
                    else:
                        logger.debug(f"No se encontró columna válida para {std_name} después del filtrado")
                else:
                    column_mapping[std_name] = matched[0]
                    logger.debug(f"Columna {std_name} mapeada a: {matched[0]}")
            else:
                logger.debug(f"No se encontró columna que coincida con patrón {std_name}: {pattern}")

    # Log del mapeo final para debug
    logger.info("Mapeo final de columnas:")
    for key, value in column_mapping.items():
        logger.info(f"  {key} -> {value}")

    # Verificar columnas requeridas mínimas (tiempo y al menos dos voltajes)
    required_minimum = ['time', 'u_l1', 'u_l2', 'p_l1', 'p_l2']
    if all(req in column_mapping for req in required_minimum):
        logger.info(f"Se encontraron las columnas mínimas requeridas: {[column_mapping[req] for req in required_minimum]}")
        return True, column_mapping

    # Si no se encuentran las columnas mínimas, devolver False
    return False, column_mapping

def find_column(df, pattern):
    """
    Encuentra una columna que coincida con el patrón regex
    Args:
        df: DataFrame donde buscar
        pattern: Patrón regex para buscar

    Returns:
        str: Nombre de la columna encontrada o None
    """
    matches = [col for col in df.columns if re.search(pattern, col)]
    return matches[0] if matches else None

def generate_unique_code():
    """
    Genera un código único de 10 dígitos basado en timestamp actual y un componente aleatorio
    
    Returns:
        str: Código único de 10 dígitos
    """
    # Usar timestamp para garantizar unicidad entre ejecuciones cercanas
    timestamp = time.time()
    # Combinar con un componente aleatorio
    unique_str = f"{timestamp}_{os.urandom(8).hex()}"
    # Generar hash para obtener un valor distribuido
    hash_obj = hashlib.md5(unique_str.encode())
    # Convertir a un número de 10 dígitos
    hash_int = int(hash_obj.hexdigest(), 16) % 10**10
    # Formatear a 10 dígitos con ceros a la izquierda
    return f"{hash_int:010d}"

def extract_client_code(file_path):
    """
    Extrae el código del cliente del nombre del archivo.
    El código siempre son los últimos 10 dígitos del nombre del archivo.
    Si no se puede extraer, genera un código numérico único basado en el hash del nombre.
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        str: Código de cliente extraído o un código generado único
    """
    try:
        if file_path is None:
            logger.error("Se intentó extraer código de un archivo None")
            return generate_unique_code()
            
        logger.debug(f"Extrayendo código del archivo: {file_path}")

        # Obtener solo el nombre del archivo sin ruta ni extensión
        file_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(file_name)[0]
        
        # Método principal: buscar exactamente 10 dígitos consecutivos
        # al final del nombre del archivo (antes de posible espacio en blanco al final)
        pattern = r'(\d{10})\s*$'
        match = re.search(pattern, name_without_ext)
        
        if match:
            code = match.group(1)
            logger.info(f"Código de cliente extraído correctamente: {code}")
            return code
        
        # Segundo método: buscar 10 dígitos consecutivos en cualquier parte del nombre
        pattern = r'(\d{10})'
        match = re.search(pattern, name_without_ext)
        
        if match:
            code = match.group(1)
            logger.info(f"Código de cliente extraído del nombre (método 2): {code}")
            return code
        
        # Tercer método: Extraer los últimos 10 dígitos si hay al menos 10 dígitos en total
        all_digits = ''.join(char for char in name_without_ext if char.isdigit())
        if len(all_digits) >= 10:
            code = all_digits[-10:]
            logger.info(f"Código numérico extraído (últimos 10 dígitos): {code}")
            return code
        
        # Si no hay suficientes dígitos, generar un código automático único basado en hash
        # del nombre del archivo para mantener consistencia entre ejecuciones
        hash_obj = hashlib.md5(file_name.encode())
        # Extraemos un número de 10 dígitos del hash (usando los primeros 10 dígitos del valor decimal del hash)
        hash_int = int(hash_obj.hexdigest(), 16) % 10**10
        auto_code = f"{hash_int:010d}"  # Formateamos a 10 dígitos con ceros a la izquierda
        
        logger.info(f"Generado código único automático para {file_name}: {auto_code}")
        return auto_code
        
    except Exception as e:
        logger.error(f"Error al extraer código del cliente del archivo {file_path}: {e}")
        
        # En caso de error, generamos un código único completamente aleatorio
        auto_code = generate_unique_code()
        logger.warning(f"Generado código de emergencia tras error: {auto_code}")
        return auto_code

def validate_file_name(file_path):
    """
    Valida que el nombre del archivo tenga el formato esperado para poder extraer
    un código de cliente válido.
    
    Args:
        file_path: Ruta al archivo a validar
        
    Returns:
        bool: True si el nombre del archivo es válido y contiene un código de cliente extraíble
    """
    try:
        file_name = os.path.basename(file_path)
        name, ext = os.path.splitext(file_name)
        
        # Validar que tenga al menos 10 caracteres antes de la extensión
        if len(name) < 10:
            logger.warning(f"El archivo {file_name} tiene un nombre demasiado corto para extraer un código válido")
            return False
        
        # Método principal: Buscar exactamente 10 dígitos consecutivos en el nombre
        pattern = r'\d{10}'
        if re.search(pattern, name):
            logger.info(f"Nombre de archivo válido: {file_name} - contiene un código de 10 dígitos")
            return True
            
        # Verificar si hay al menos 10 dígitos en total en el nombre
        digits_count = sum(1 for char in name if char.isdigit())
        if digits_count >= 10:
            logger.info(f"Nombre de archivo aceptable: {file_name} - contiene al menos 10 dígitos")
            return True
        
        # Si no hay suficientes dígitos, el archivo no es válido para nuestro proceso
        logger.warning(f"El archivo {file_name} no contiene suficientes dígitos (mínimo 10) para extraer un código")
        # En el nuevo sistema, siempre consideramos los archivos válidos, ya que generaremos un código único si es necesario
        return True
        
    except Exception as e:
        logger.error(f"Error al validar nombre de archivo {file_path}: {e}")
        return True  # En caso de error, consideramos válido y generaremos un código único

def has_valid_client_code(file_path):
    """
    Determina si un archivo tiene un código de cliente válido que puede ser extraído.
    Esta función es más estricta que validate_file_name, ya que verifica específicamente
    si se puede extraer un código de cliente de 10 dígitos.
    
    Args:
        file_path: Ruta al archivo a validar
        
    Returns:
        bool: True si se puede extraer un código de cliente válido
    """
    try:
        file_name = os.path.basename(file_path)
        name, _ = os.path.splitext(file_name)
        
        # Buscar un patrón de 10 dígitos consecutivos
        pattern = r'\d{10}'
        if re.search(pattern, name):
            return True
            
        # Si no hay 10 dígitos consecutivos, verificar si hay al menos 10 dígitos en total
        digits_count = sum(1 for char in name if char.isdigit())
        if digits_count >= 10:
            return True
            
        # En el nuevo sistema, siempre consideramos que tiene código válido, ya que generaremos uno si es necesario
        return True
        
    except Exception as e:
        logger.error(f"Error al verificar código de cliente en {file_path}: {e}")
        return True  # En caso de error, consideramos válido y generaremos un código único
        