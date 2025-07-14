#sonel_extractor/parsers/csv_parser.py
import re
import pandas as pd
from config.logger import logger
from config.settings import SUPPORTED_ENCODINGS
from core.utils.validators import validate_voltage_columns

class CSVParser:
    """Clase para procesar archivos CSV con datos de voltaje"""

    @staticmethod
    def parse(file_path):
        """
        Procesa un archivo CSV con diferentes estructuras posibles
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            DataFrame con los datos o None si hay errores
        """
        try:
            # Intentar leer directamente con detección automática
            logger.info(f"Intentando leer archivo CSV: {file_path}")
            
            # Probar diferentes combinaciones de separador y encoding
            for sep in [';', ',', '\t', '|']:
                for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'iso-8859-1', 'cp1252', 'utf-16', 'utf-16le', 'utf-16be', 'windows-1252', 'iso-8859-15']:
                    try:
                        df = pd.read_csv(file_path, sep=sep, encoding=encoding)
                        
                        # Verificar si las primeras filas contienen datos numéricos en lugar de encabezados
                        if df.shape[1] > 0 and all(isinstance(col, (int, float)) for col in df.columns):
                            logger.info("Se ha detectado que las columnas son numéricas. Intentando con header=None")
                            # Posible archivo sin encabezados o con encabezados en la primera fila
                            df = pd.read_csv(file_path, sep=sep, encoding=encoding, header=None)
                            # Intentar usar primera fila como encabezados
                            if not df.empty:
                                df.columns = df.iloc[0].astype(str)
                                df = df.iloc[1:].reset_index(drop=True)
                        
                        # Convertir todos los nombres de columnas a string para evitar problemas
                        df.columns = df.columns.astype(str)
                        
                        # Imprimir las columnas para debug
                        logger.info(f"Columnas encontradas con sep='{sep}', encoding='{encoding}': {list(df.columns)}")
                        
                        valid, column_map = validate_voltage_columns(df)
                        if valid:
                            logger.info(f"Datos extraídos correctamente de {file_path}")
                            return df
                            
                    except Exception as e:
                        logger.debug(f"Error con sep='{sep}', encoding='{encoding}': {e}")
                        continue
            
            # Si no funciona, probar métodos alternativos
            df = CSVParser._try_alternative_methods(file_path)
            if df is not None:
                return df
                
        except Exception as e:
            logger.error(f"Error al procesar archivo CSV {file_path}: {e}")
        
        logger.error(f"No se pudo extraer datos del archivo CSV: {file_path}")
        return None
    
    @staticmethod
    def _try_alternative_methods(file_path):
        """
        Intenta métodos alternativos para extraer datos de CSV
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            DataFrame con los datos o None si hay errores
        """
        try:
            # Detectar encabezados buscando filas con strings que coincidan con patrones de fechas/voltajes
            for sep in [';', ',', '\t', '|']:
                for encoding in SUPPORTED_ENCODINGS:
                    try:
                        # Intentar diferentes números de filas a saltar
                        for skip_rows in range(1, 20):  # Intentar saltando hasta 20 filas
                            try:
                                logger.info(f"Intentando leer CSV saltando {skip_rows} filas con sep='{sep}', encoding='{encoding}'")
                                df = pd.read_csv(file_path, sep=sep, encoding=encoding, skiprows=skip_rows)
                                
                                if df.empty:
                                    continue
                                    
                                df.columns = df.columns.astype(str)  # Convertir a string
                                
                                # Revisamos si alguna columna se parece a una fecha/hora
                                date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{1,2}-\d{1,2}|\d{1,2}:\d{1,2}:\d{1,2}'
                                if not df.empty:
                                    first_row_str = df.iloc[0].astype(str)
                                    date_cols = [col for col in first_row_str if re.search(date_pattern, col)]
                                    
                                    # Si encontramos fechas en la primera fila, podría ser que las columnas sean la fila anterior
                                    if date_cols and skip_rows > 0:
                                        logger.info(f"Posibles datos de fecha encontrados en la fila {skip_rows+1}")
                                        # Intentar usar esta fila como datos y la anterior como encabezados
                                        try:
                                            df_headers = pd.read_csv(file_path, sep=sep, encoding=encoding, 
                                                                   skiprows=skip_rows-1, nrows=1)
                                            df_data = pd.read_csv(file_path, sep=sep, encoding=encoding, 
                                                                skiprows=skip_rows)
                                            if not df_headers.empty and not df_data.empty:
                                                df_data.columns = df_headers.iloc[0].astype(str)
                                                df = df_data
                                        except Exception as e:
                                            logger.debug(f"Error al intentar recomponer encabezados: {e}")
                                
                                # Imprimir las columnas para debug
                                logger.info(f"Columnas encontradas con skiprows={skip_rows}: {list(df.columns)}")
                                
                                valid, column_map = validate_voltage_columns(df)
                                if valid:
                                    logger.info(f"Datos extraídos correctamente saltando {skip_rows} filas de {file_path}")
                                    return df
                                    
                            except Exception as e:
                                logger.debug(f"Error al intentar con skiprows={skip_rows}, sep='{sep}', encoding='{encoding}': {e}")
                                continue
                                
                    except Exception as e:
                        logger.debug(f"Error con sep='{sep}', encoding='{encoding}' en métodos alternativos: {e}")
                        continue
            
            # Si llegamos aquí, intentemos un enfoque más específico para este archivo
            df = CSVParser._specific_file_analysis(file_path)
            if df is not None:
                return df
                
            return None
                
        except Exception as e:
            logger.error(f"Error en métodos alternativos para CSV: {e}")
            return None
    
    @staticmethod
    def _specific_file_analysis(file_path):
        """
        Análisis específico del archivo CSV para casos complejos
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            DataFrame con los datos o None si hay errores
        """
        try:
            for sep in [';', ',', '\t', '|']:
                for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'utf-16']:
                    try:
                        # Leer las primeras filas para inspección
                        preview = pd.read_csv(file_path, sep=sep, encoding=encoding, nrows=20)
                        
                        if preview.empty:
                            continue
                            
                        preview_str = preview.astype(str)
                        
                        # Buscar filas que contengan palabras clave como "Fecha", "Hora", "U1", "U2"
                        for i, row in preview_str.iterrows():
                            row_values = " ".join(row.values)
                            logger.info(f"Fila {i+1}: {row_values[:100]}...")  # Mostrar primeros 100 caracteres
                            
                            # Buscar patrones de encabezados más amplios
                            header_patterns = [
                                r'(?i)fecha|hora|u\d+|v\d+|volt|tens',
                                r'(?i)time|date|voltage|current',
                                r'(?i)timestamp|datetime|phase',
                                r'L\d+|N\d+|R\d+|S\d+|T\d+'  # Patrones de fases eléctricas
                            ]
                            
                            if any(any(re.search(pattern, val) for val in row.values) for pattern in header_patterns):
                                logger.info(f"Posible fila de encabezados encontrada en la fila {i+1}")
                                # Intentar con esta fila como encabezado
                                try:
                                    if i == 0:
                                        df = pd.read_csv(file_path, sep=sep, encoding=encoding)
                                    else:
                                        df = pd.read_csv(file_path, sep=sep, encoding=encoding, skiprows=i)
                                    
                                    if df.empty:
                                        continue
                                        
                                    df.columns = df.columns.astype(str)
                                    
                                    # Imprimir las columnas para debug
                                    logger.info(f"Columnas encontradas con header en fila {i+1}: {list(df.columns)}")
                                    
                                    valid, column_map = validate_voltage_columns(df)
                                    if valid:
                                        logger.info(f"Datos extraídos correctamente usando fila {i+1} como encabezado")
                                        return df
                                        
                                except Exception as e:
                                    logger.debug(f"Error al usar fila {i+1} como encabezado: {e}")
                                    continue
                                    
                    except Exception as e:
                        logger.debug(f"Error durante el análisis específico con sep='{sep}', encoding='{encoding}': {e}")
                        continue
            
            # Último intento: buscar estructura de datos analizando el contenido línea por línea
            return CSVParser._line_by_line_analysis(file_path)
                
        except Exception as e:
            logger.debug(f"Error durante el análisis específico del archivo: {e}")
            return None
    
    @staticmethod
    def _line_by_line_analysis(file_path):
        """
        Análisis línea por línea para encontrar la estructura correcta
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            DataFrame con los datos o None si hay errores
        """
        try:
            for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'utf-16']:
                try:
                    # Leer las líneas del archivo
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    
                    if not lines:
                        continue
                    
                    # Analizar cada línea para encontrar separadores y patrones
                    for sep in [';', ',', '\t', '|']:
                        # Buscar línea con posibles encabezados de columnas
                        data_start_line = 0
                        max_columns = 0
                        
                        for i, line in enumerate(lines[:30]):  # Revisar primeras 30 líneas
                            line = line.strip()
                            if not line:
                                continue
                                
                            # Contar columnas en esta línea
                            columns_count = len(line.split(sep))
                            
                            # Buscar líneas que podrían contener encabezados relacionados con tiempo y voltaje
                            header_patterns = [
                                r'(?i)(fecha|time|hora|date|tiempo).*(u\s*l|v\s*l|volt|tens)',
                                r'(?i)(timestamp|datetime).*(phase|voltage)',
                                r'(?i)u\d+.*v\d+|L\d+.*N\d+'
                            ]
                            
                            if any(re.search(pattern, line) for pattern in header_patterns):
                                data_start_line = i
                                logger.info(f"Posible línea de encabezados encontrada en línea {i+1}: {line[:100]}...")
                                break
                            
                            # También considerar la línea con más columnas como posible encabezado
                            if columns_count > max_columns and columns_count >= 3:  # Al menos 3 columnas
                                max_columns = columns_count
                                if data_start_line == 0:  # Solo si no hemos encontrado un encabezado específico
                                    data_start_line = i
                        
                        # Si encontramos un posible inicio de datos, intentar leer desde ahí
                        if data_start_line >= 0:
                            try:
                                logger.info(f"Intentando leer desde línea {data_start_line+1} con sep='{sep}', encoding='{encoding}'")
                                
                                if data_start_line == 0:
                                    df = pd.read_csv(file_path, sep=sep, encoding=encoding)
                                else:
                                    df = pd.read_csv(file_path, sep=sep, encoding=encoding, skiprows=data_start_line)
                                
                                if df.empty:
                                    continue
                                    
                                df.columns = df.columns.astype(str)
                                
                                # Imprimir las columnas para debug
                                logger.info(f"Columnas encontradas desde línea {data_start_line+1}: {list(df.columns)}")
                                
                                valid, column_map = validate_voltage_columns(df)
                                if valid:
                                    logger.info(f"Datos extraídos correctamente desde la línea {data_start_line+1} de {file_path}")
                                    return df
                                    
                            except Exception as e:
                                logger.debug(f"Error al leer desde línea {data_start_line+1}: {e}")
                                continue
                                
                except Exception as e:
                    logger.debug(f"Error con encoding '{encoding}' en análisis línea por línea: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error en análisis línea por línea: {e}")
            return None