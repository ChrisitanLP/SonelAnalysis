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

    # Log de las columnas originales para debug
    logger.debug("Columnas originales encontradas:")
    for i, col in enumerate(df.columns):
        logger.debug(f"  [{i}]: '{col}' (len: {len(col)})")

    # Mapeo de nombres de columnas estándar a nombres encontrados
    column_mapping = {}

    # Procesar patrones en orden específico para evitar conflictos
    ordered_patterns = [
        'time', 'date', 'time_utc', 'utc_zone',  # Campos de tiempo
        'u_l1', 'u_l2', 'u_l3', 'u_l12',        # Voltajes
        'i_l1', 'i_l2',                          # Corrientes
        'p_l1', 'p_l2', 'p_l3', 'p_e',          # Potencia activa
        'q1_l1', 'q1_l2', 'q1_e',               # Potencia reactiva
        'sn_l1', 'sn_l2', 'sn_e',               # Potencia aparente compleja (procesar antes que S)
        's_l1', 's_l2', 's_e'                   # Potencia aparente (procesar después)
    ]

    for std_name in ordered_patterns:
        if std_name in COLUMN_PATTERNS:
            pattern = COLUMN_PATTERNS[std_name]
            
            # Buscar todas las columnas que coinciden con el patrón
            matched = []
            for col in df.columns:
                try:
                    if re.search(pattern, col):
                        matched.append(col)
                        logger.debug(f"Patrón '{std_name}' coincide con columna: '{col}'")
                except re.error as e:
                    logger.warning(f"Error en regex para patrón '{std_name}': {e}")
                    continue
            
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
    
    # Manejar compatibilidad con time_utc5 y variaciones UTC (mapear a time_utc si existe)
    if 'time_utc' not in column_mapping:
        # Buscar usando patrones más amplios para compatibilidad con diferentes zonas UTC
        time_utc_patterns = [
            r'(?i)(time|tiempo)\s*\(utc[+-]?\d+\)',  # UTC con cualquier número
            r'(?i)(time|tiempo).*utc.*[+-]?\d*'       # Patrón más flexible
        ]
        
        for pattern in time_utc_patterns:
            matched = [col for col in df.columns if re.search(pattern, col)]
            if matched:
                column_mapping['time_utc'] = matched[0]
                logger.debug(f"Columna time_utc mapeada desde patrón UTC genérico: {matched[0]}")
                break

    # Log del mapeo final para debug
    for key, value in column_mapping.items():
        logger.info(f"  {key} -> {value}")

    # Verificar columnas requeridas mínimas (tiempo y al menos algunos valores eléctricos)
    # Flexibilizar los requerimientos para manejar mejor archivos con diferentes estructuras
    essential_patterns = {
        'time_found': any(key in column_mapping for key in ['time', 'date', 'time_utc']),
        'voltage_found': any(key in column_mapping for key in ['u_l1', 'u_l2', 'u_l3']),
        'current_found': any(key in column_mapping for key in ['i_l1', 'i_l2']),
        'power_found': any(key in column_mapping for key in ['p_l1', 'p_l2', 'p_l3', 'p_e'])
    }
    
    # Requerir al menos tiempo y alguna medida eléctrica (voltaje, corriente o potencia)
    if (essential_patterns['time_found'] and 
        (essential_patterns['voltage_found'] or essential_patterns['current_found'] or essential_patterns['power_found'])):
        
        found_types = [k for k, v in essential_patterns.items() if v]
        logger.info(f"Se encontraron las medidas esenciales: {found_types}")
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
    El código es la última cadena de dígitos del nombre del archivo (entre 2 y 10 dígitos).
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
        
        # Método principal: buscar la última cadena de dígitos (entre 2 y 10 dígitos)
        # al final del nombre del archivo (antes de posible espacio en blanco al final)
        pattern = r'(\d{2,10})\s*$'
        match = re.search(pattern, name_without_ext)
        
        if match:
            code = match.group(1)
            logger.info(f"Código de cliente extraído correctamente: {code}")
            return code
        
        # Segundo método: buscar la última cadena de dígitos consecutivos en cualquier parte del nombre
        # Encontrar todas las cadenas de 2-10 dígitos y tomar la última
        pattern = r'(\d{2,10})'
        matches = re.findall(pattern, name_without_ext)
        
        if matches:
            # Tomar la última cadena encontrada
            code = matches[-1]
            logger.info(f"Código de cliente extraído del nombre (último grupo): {code}")
            return code
        
        # Tercer método: Si hay al menos 2 dígitos en total, tomar los últimos
        all_digits = ''.join(char for char in name_without_ext if char.isdigit())
        if len(all_digits) >= 2:
            # Tomar hasta 10 dígitos de los últimos dígitos disponibles
            code = all_digits[-min(10, len(all_digits)):]
            if len(code) >= 2:  # Asegurar que tenga al menos 2 dígitos
                logger.info(f"Código numérico extraído (últimos dígitos): {code}")
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
        
        # Validar que tenga al menos 2 caracteres antes de la extensión
        if len(name) < 2:
            logger.warning(f"El archivo {file_name} tiene un nombre demasiado corto para extraer un código válido")
            return False
        
        # Método principal: Buscar al menos una cadena de 2-10 dígitos consecutivos en el nombre
        pattern = r'\d{2,10}'
        if re.search(pattern, name):
            logger.info(f"Nombre de archivo válido: {file_name} - contiene un código válido")
            return True
            
        # Verificar si hay al menos 2 dígitos en total en el nombre
        digits_count = sum(1 for char in name if char.isdigit())
        if digits_count >= 2:
            logger.info(f"Nombre de archivo aceptable: {file_name} - contiene al menos 2 dígitos")
            return True
        
        # Si no hay suficientes dígitos, el archivo no es válido para nuestro proceso
        logger.warning(f"El archivo {file_name} no contiene suficientes dígitos (mínimo 2) para extraer un código")
        # En el nuevo sistema, siempre consideramos los archivos válidos, ya que generaremos un código único si es necesario
        return True
        
    except Exception as e:
        logger.error(f"Error al validar nombre de archivo {file_path}: {e}")
        return True  # En caso de error, consideramos válido y generaremos un código único

def has_valid_client_code(file_path):
    """
    Determina si un archivo tiene un código de cliente válido que puede ser extraído.
    Esta función es más estricta que validate_file_name, ya que verifica específicamente
    si se puede extraer un código de cliente de 2-10 dígitos.
    
    Args:
        file_path: Ruta al archivo a validar
        
    Returns:
        bool: True si se puede extraer un código de cliente válido
    """
    try:
        file_name = os.path.basename(file_path)
        name, _ = os.path.splitext(file_name)
        
        # Buscar un patrón de 2-10 dígitos consecutivos
        pattern = r'\d{2,10}'
        if re.search(pattern, name):
            return True
            
        # Si no hay dígitos consecutivos suficientes, verificar si hay al menos 2 dígitos en total
        digits_count = sum(1 for char in name if char.isdigit())
        if digits_count >= 2:
            return True
            
        # En el nuevo sistema, siempre consideramos que tiene código válido, ya que generaremos uno si es necesario
        return True
        
    except Exception as e:
        logger.error(f"Error al verificar código de cliente en {file_path}: {e}")
        return True
        