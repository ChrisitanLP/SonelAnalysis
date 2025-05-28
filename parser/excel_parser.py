#sonel_extractor/parser/excel_parser.py
import re
import pandas as pd
from config.logger import logger
from utils.validators import validate_voltage_columns

class ExcelParser:
    """Clase para procesar archivos Excel con datos de voltaje"""

    @staticmethod
    def parse(file_path):
        """
        Procesa un archivo Excel con diferentes estructuras posibles
        
        Args:
            file_path: Ruta al archivo Excel
            
        Returns:
            DataFrame con los datos o None si hay errores
        """
        try:
            # Intentar leer directamente con detección de encabezados
            logger.info(f"Intentando leer archivo Excel: {file_path}")
            df = pd.read_excel(file_path)
            
            # Verificar si las primeras filas contienen datos numéricos en lugar de encabezados
            if df.shape[1] > 0 and all(isinstance(col, (int, float)) for col in df.columns):
                logger.info("Se ha detectado que las columnas son numéricas. Intentando con header=None")
                # Posible archivo sin encabezados o con encabezados en la primera fila
                df = pd.read_excel(file_path, header=None)
                # Intentar usar primera fila como encabezados
                df.columns = df.iloc[0].astype(str)
                df = df.iloc[1:].reset_index(drop=True)
                
            # Convertir todos los nombres de columnas a string para evitar problemas
            df.columns = df.columns.astype(str)
            
            # Imprimir las columnas para debug
            logger.info(f"Columnas encontradas: {list(df.columns)}")
            
            valid, column_map = validate_voltage_columns(df)
            if valid:
                logger.info(f"Datos extraídos correctamente de {file_path}")
                return df
            
            # Si no funciona, probar métodos alternativos
            df = ExcelParser._try_alternative_methods(file_path)
            if df is not None:
                return df
                
        except Exception as e:
            logger.error(f"Error al procesar archivo Excel {file_path}: {e}")
        
        logger.error(f"No se pudo extraer datos del archivo Excel: {file_path}")
        return None
    
    @staticmethod
    def _try_alternative_methods(file_path):
        """
        Intenta métodos alternativos para extraer datos de Excel
        
        Args:
            file_path: Ruta al archivo Excel
            
        Returns:
            DataFrame con los datos o None si hay errores
        """
        try:
            # Intentar diferentes hojas
            xl = pd.ExcelFile(file_path)
            for sheet_name in xl.sheet_names:
                logger.info(f"Intentando leer hoja: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df.columns = df.columns.astype(str)  # Convertir a string
                valid, _ = validate_voltage_columns(df)
                if valid:
                    logger.info(f"Datos extraídos correctamente de la hoja '{sheet_name}' de {file_path}")
                    return df
            
            # Detectar encabezados buscando filas con strings que coincidan con patrones de fechas/voltajes
            for skip_rows in range(1, 20):  # Intentar saltando hasta 20 filas
                try:
                    logger.info(f"Intentando leer Excel saltando {skip_rows} filas")
                    df = pd.read_excel(file_path, skiprows=skip_rows)
                    df.columns = df.columns.astype(str)  # Convertir a string
                    
                    # Revisamos si alguna columna se parece a una fecha/hora
                    date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}'
                    date_cols = [col for col in df.iloc[0].astype(str) if re.search(date_pattern, col)]
                    
                    # Si encontramos fechas en la primera fila, podría ser que las columnas sean la fila anterior
                    if date_cols:
                        logger.info(f"Posibles datos de fecha encontrados en la fila {skip_rows+1}")
                        # Intentar usar esta fila como datos y la anterior como encabezados
                        df_headers = pd.read_excel(file_path, skiprows=skip_rows-1, nrows=1)
                        df_data = pd.read_excel(file_path, skiprows=skip_rows)
                        if not df_headers.empty and not df_data.empty:
                            df_data.columns = df_headers.iloc[0].astype(str)
                            df = df_data
                    
                    # Imprimir las columnas para debug
                    logger.info(f"Columnas encontradas con skiprows={skip_rows}: {list(df.columns)}")
                    
                    valid, column_map = validate_voltage_columns(df)
                    if valid:
                        logger.info(f"Datos extraídos correctamente saltando {skip_rows} filas de {file_path}")
                        return df
                except Exception as e:
                    logger.debug(f"Error al intentar con skiprows={skip_rows}: {e}")
                    continue
                    
            # Si llegamos aquí, intentemos un enfoque más específico para este archivo
            try:
                # Leer las primeras filas para inspección
                preview = pd.read_excel(file_path, nrows=10)
                preview_str = preview.astype(str)
                
                # Buscar filas que contengan palabras clave como "Fecha", "Hora", "U1", "U2"
                for i, row in preview_str.iterrows():
                    row_values = " ".join(row.values)
                    logger.info(f"Fila {i+1}: {row_values[:100]}...")  # Mostrar primeros 100 caracteres
                    
                    if any(re.search(r'(?i)fecha|hora|u\d+|v\d+', val) for val in row.values):
                        logger.info(f"Posible fila de encabezados encontrada en la fila {i+1}")
                        # Intentar con esta fila como encabezado
                        df = pd.read_excel(file_path, header=i)
                        df.columns = df.columns.astype(str)
                        
                        # Imprimir las columnas para debug
                        logger.info(f"Columnas encontradas con header={i}: {list(df.columns)}")
                        
                        valid, column_map = validate_voltage_columns(df)
                        if valid:
                            return df
            except Exception as e:
                logger.debug(f"Error durante el análisis específico del archivo: {e}")
                
            return None
                
        except Exception as e:
            logger.error(f"Error en métodos alternativos para Excel: {e}")
            return None